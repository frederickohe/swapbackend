"""Remap legacy listing categories onto the new domain set."""

from alembic import op


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None

# Must stay in sync with LEGACY_ITEM_CATEGORY_MAP in listing_categories.py
_LEGACY_TO_CANONICAL = (
    ("Electronics", "Phones"),
    ("Home & Kitchen", "Services"),
    ("kids", "Games"),
    ("Books", "Services"),
    ("Fashion", "Services"),
    ("Sports", "Games"),
    ("Tools", "Services"),
    ("Fitness", "Services"),
    ("Beauty Products", "Services"),
    ("Vehicles", "Cars"),
    ("Vehicle Parts", "Cars"),
    ("Personal Care", "Services"),
    ("Media", "Games"),
    ("Video Games", "Games"),
)


def upgrade():
    for legacy, canonical in _LEGACY_TO_CANONICAL:
        # Escape single quotes for SQL literals.
        legacy_sql = legacy.replace("'", "''")
        canonical_sql = canonical.replace("'", "''")
        op.execute(
            f"UPDATE listings SET category = '{canonical_sql}' "
            f"WHERE category = '{legacy_sql}'"
        )


def downgrade():
    # Ambiguous reverse mapping (many legacy labels share one canonical).
    # Leave categories on the new domain set.
    pass
