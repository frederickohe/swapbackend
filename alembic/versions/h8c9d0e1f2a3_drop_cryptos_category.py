"""Move any remaining Cryptos listings onto Electronics.

The app no longer offers a cryptocurrency category.
"""
from alembic import op


revision = "h8c9d0e1f2a3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE listings SET category = 'Electronics' WHERE category = 'Cryptos'"
    )
    # Wishlist entries are JSON objects: {"category": "...", "description": "..."}.
    op.execute(
        """
        UPDATE listings
        SET wishlist = replace(wishlist::text, '"category": "Cryptos"', '"category": "Electronics"')::json
        WHERE wishlist::text LIKE '%"category": "Cryptos"%'
        """
    )


def downgrade():
    # Cryptocurrency is no longer a supported category.
    pass
