"""Add listing add-on service fields."""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "listings",
        sa.Column(
            "wish_finding",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "budget_negotiation",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "listings",
        sa.Column("budget_amount", sa.Float(), nullable=True),
    )
    op.add_column(
        "listings",
        sa.Column(
            "collection_assistance",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("listings", "collection_assistance")
    op.drop_column("listings", "budget_amount")
    op.drop_column("listings", "budget_negotiation")
    op.drop_column("listings", "wish_finding")
