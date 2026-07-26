"""
Listing categories aligned with swap-pro dashboard / add-belonging UI.

Item categories are used on listing.category; incoming categories may appear in wishlist items.
"""

from typing import Dict, FrozenSet, List, Set, Tuple

# Rows mirror AddBelongingPage / Home category strip order (preserved for API clients).
LISTING_ITEM_CATEGORY_ROWS: Tuple[Tuple[str, ...], ...] = (
    ("Cryptos", "Services", "Phones"),
    ("Laptops", "Cars", "Games"),
)

LISTING_INCOMING_CATEGORY_ROWS: Tuple[Tuple[str, ...], ...] = (
    ("House", "Lands", "Building"),
    ("Software",),
)

# Legacy labels (pre-domain refresh) → current item categories.
LEGACY_ITEM_CATEGORY_MAP: Dict[str, str] = {
    "Electronics": "Phones",
    "Home & Kitchen": "Services",
    "kids": "Games",
    "Books": "Services",
    "Fashion": "Services",
    "Sports": "Games",
    "Tools": "Services",
    "Fitness": "Services",
    "Beauty Products": "Services",
    "Vehicles": "Cars",
    "Vehicle Parts": "Cars",
    "Personal Care": "Services",
    "Media": "Games",
    "Video Games": "Games",
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
    """Map a legacy or current category label onto the canonical item category."""
    trimmed = value.strip()
    if trimmed in LISTING_ITEM_CATEGORIES_SET:
        return trimmed
    return LEGACY_ITEM_CATEGORY_MAP.get(trimmed, trimmed)


def is_valid_item_category(value: str) -> bool:
    trimmed = value.strip()
    return (
        trimmed in LISTING_ITEM_CATEGORIES_SET
        or trimmed in LEGACY_ITEM_CATEGORY_MAP
    )


def is_valid_incoming_category(value: str) -> bool:
    return value in LISTING_INCOMING_CATEGORIES_SET


def is_valid_listing_category(value: str) -> bool:
    """True for item or incoming (wishlist) categories."""
    return is_valid_item_category(value) or is_valid_incoming_category(value)


def category_search_values(category: str) -> List[str]:
    """
    Values that should match a category filter, including legacy labels that
    remap onto the requested category.
    """
    canonical = normalize_item_category(category)
    matches: Set[str] = {canonical, category.strip()}
    for legacy, mapped in LEGACY_ITEM_CATEGORY_MAP.items():
        if mapped == canonical:
            matches.add(legacy)
    return sorted(matches)


def format_allowed_item_categories() -> str:
    return ", ".join(LISTING_ITEM_CATEGORIES)


def format_allowed_incoming_categories() -> str:
    return ", ".join(LISTING_INCOMING_CATEGORIES)
