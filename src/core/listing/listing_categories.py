"""
Listing categories aligned with swap-pro add-belonging UI (add_belonging.dart).

Item categories are used on listing.category; incoming categories may appear in wishlist items.
"""

from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# Rows mirror Figma layout in AddBelongingPage (order preserved for API clients).
LISTING_ITEM_CATEGORY_ROWS: Tuple[Tuple[str, ...], ...] = (
    ("Electronics", "Home & Kitchen", "kids"),
    ("Books", "Fashion", "Sports", "Tools"),
    ("Fitness", "Beauty Products", "Vehicles"),
    ("Vehicle Parts", "Fitness", "Personal Care"),
    ("Media", "Video Games"),
)

LISTING_INCOMING_CATEGORY_ROWS: Tuple[Tuple[str, ...], ...] = (
    ("House", "Lands", "Building"),
    ("Software",),
)

# Retired browse labels → current item categories.
# Cryptos is not offered. It is not a creatable category.
DOMAIN_ITEM_CATEGORY_MAP: Dict[str, str] = {
    "Services": "Fashion",
    "Phones": "Electronics",
    "Laptops": "Electronics",
    "Cars": "Vehicles",
    "Games": "Video Games",
}

# Labels that must never be shown or stored as their own category.
RETIRED_CATEGORY_LABELS: Dict[str, str] = {
    "Cryptos": "Electronics",
}


def _unique_flatten(rows: Tuple[Tuple[str, ...], ...]) -> Tuple[str, ...]:
    seen = set()
    ordered: List[str] = []
    for row in rows:
        for label in row:
            if label not in seen:
                seen.add(label)
                ordered.append(label)
    return tuple(ordered)


LISTING_ITEM_CATEGORIES: Tuple[str, ...] = _unique_flatten(LISTING_ITEM_CATEGORY_ROWS)
LISTING_INCOMING_CATEGORIES: Tuple[str, ...] = _unique_flatten(LISTING_INCOMING_CATEGORY_ROWS)

LISTING_ITEM_CATEGORIES_SET: FrozenSet[str] = frozenset(LISTING_ITEM_CATEGORIES)
LISTING_INCOMING_CATEGORIES_SET: FrozenSet[str] = frozenset(LISTING_INCOMING_CATEGORIES)
ALL_LISTING_CATEGORIES_SET: FrozenSet[str] = (
    LISTING_ITEM_CATEGORIES_SET | LISTING_INCOMING_CATEGORIES_SET
)


def public_item_category(value: Optional[str]) -> Optional[str]:
    """Hide retired labels, including cryptocurrency, from API responses."""
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return trimmed
    return RETIRED_CATEGORY_LABELS.get(trimmed, trimmed)


def normalize_item_category(value: str) -> str:
    """Map a domain or current category label onto the canonical item category."""
    trimmed = value.strip()
    retired = RETIRED_CATEGORY_LABELS.get(trimmed)
    if retired:
        return retired
    if trimmed in LISTING_ITEM_CATEGORIES_SET:
        return trimmed
    return DOMAIN_ITEM_CATEGORY_MAP.get(trimmed, trimmed)


def is_valid_item_category(value: str) -> bool:
    trimmed = value.strip()
    return (
        trimmed in LISTING_ITEM_CATEGORIES_SET
        or trimmed in DOMAIN_ITEM_CATEGORY_MAP
    )


def is_valid_incoming_category(value: str) -> bool:
    return value in LISTING_INCOMING_CATEGORIES_SET


def is_valid_listing_category(value: str) -> bool:
    """True for item or incoming (wishlist) categories."""
    return is_valid_item_category(value) or is_valid_incoming_category(value)


def category_search_values(category: str) -> List[str]:
    """
    Values that should match a category filter, including domain labels that
    remap onto the requested category.
    """
    canonical = normalize_item_category(category)
    matches: Set[str] = {canonical, category.strip()}
    for domain, mapped in DOMAIN_ITEM_CATEGORY_MAP.items():
        if mapped == canonical:
            matches.add(domain)
    for retired, mapped in RETIRED_CATEGORY_LABELS.items():
        if mapped == canonical:
            matches.add(retired)
    return sorted(matches)


def format_allowed_item_categories() -> str:
    return ", ".join(LISTING_ITEM_CATEGORIES)


def format_allowed_incoming_categories() -> str:
    return ", ".join(LISTING_INCOMING_CATEGORIES)
