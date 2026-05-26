"""
Listing categories aligned with swap-pro add-belonging UI (add_belonging.dart).

Item categories are used on listing.category; incoming categories may appear in wishlist items.
"""

from typing import FrozenSet, List, Tuple

# Rows mirror Figma layout in AddBelongingPage._itemCategoryRows (order preserved for API clients).
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


def is_valid_item_category(value: str) -> bool:
    return value in LISTING_ITEM_CATEGORIES_SET


def is_valid_incoming_category(value: str) -> bool:
    return value in LISTING_INCOMING_CATEGORIES_SET


def is_valid_listing_category(value: str) -> bool:
    """True for item or incoming (wishlist) categories."""
    return value in ALL_LISTING_CATEGORIES_SET


def format_allowed_item_categories() -> str:
    return ", ".join(LISTING_ITEM_CATEGORIES)


def format_allowed_incoming_categories() -> str:
    return ", ".join(LISTING_INCOMING_CATEGORIES)
