"""
Listing categories aligned with swap-pro add-belonging UI (add_belonging.dart).

Item categories are used on listing.category; incoming categories may appear in wishlist items.
"""

from typing import Dict, FrozenSet, List, Set, Tuple

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

# Short-lived domain labels (Cryptos/Services/…) → restored item categories.
# Kept so filters still find rows remapped by f6a7b8c9d0e1 until reverse migrate.
DOMAIN_ITEM_CATEGORY_MAP: Dict[str, str] = {
    "Cryptos": "Electronics",
    "Services": "Fashion",
    "Phones": "Electronics",
    "Laptops": "Electronics",
    "Cars": "Vehicles",
    "Games": "Video Games",
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


def normalize_item_category(value: str) -> str:
    """Map a domain or current category label onto the canonical item category."""
    trimmed = value.strip()
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
    return sorted(matches)


def format_allowed_item_categories() -> str:
    return ", ".join(LISTING_ITEM_CATEGORIES)


def format_allowed_incoming_categories() -> str:
    return ", ".join(LISTING_INCOMING_CATEGORIES)
