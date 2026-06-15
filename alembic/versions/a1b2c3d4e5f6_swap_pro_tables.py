"""Swap Pro domain tables and user extensions."""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "070198b14d42"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("role", sa.String(length=20), server_default="USER", nullable=False))
    op.add_column("users", sa.Column("credit_balance", sa.Float(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("strikes", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("longitude", sa.Float(), nullable=True))

    op.create_table(
        "hubs",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("operating_hours", sa.JSON(), nullable=True),
        sa.Column("meeting_slots", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("condition", sa.String(length=50), nullable=False),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.Column("estimated_value", sa.Float(), nullable=False),
        sa.Column("wishlist", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("renewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listings_user_id", "listings", ["user_id"])
    op.create_index("ix_listings_category", "listings", ["category"])

    op.create_table(
        "swap_requests",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("initiator_id", sa.String(length=20), nullable=False),
        sa.Column("owner_id", sa.String(length=20), nullable=False),
        sa.Column("initiator_listing_id", sa.String(length=20), nullable=False),
        sa.Column("owner_listing_id", sa.String(length=20), nullable=False),
        sa.Column("initiator_fee_paid", sa.Boolean(), nullable=True),
        sa.Column("owner_fee_paid", sa.Boolean(), nullable=True),
        sa.Column("initiator_fee_amount", sa.Float(), nullable=True),
        sa.Column("owner_fee_amount", sa.Float(), nullable=True),
        sa.Column("difference_value", sa.Float(), nullable=True),
        sa.Column("initiator_value_higher", sa.Boolean(), nullable=True),
        sa.Column("cash_difference", sa.Float(), nullable=True),
        sa.Column("credit_to_add", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("initiator_paystack_ref", sa.String(length=100), nullable=True),
        sa.Column("owner_paystack_ref", sa.String(length=100), nullable=True),
        sa.Column("hub_id", sa.String(length=20), nullable=True),
        sa.Column("meeting_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["initiator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["initiator_listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["owner_listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["hub_id"], ["hubs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_swap_requests_initiator_id", "swap_requests", ["initiator_id"])
    op.create_index("ix_swap_requests_owner_id", "swap_requests", ["owner_id"])

    op.create_table(
        "swaps",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("swap_request_id", sa.String(length=20), nullable=False),
        sa.Column("hub_id", sa.String(length=20), nullable=False),
        sa.Column("meeting_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("initiator_attended", sa.Boolean(), nullable=True),
        sa.Column("owner_attended", sa.Boolean(), nullable=True),
        sa.Column("difference_settled", sa.Boolean(), nullable=True),
        sa.Column("difference_payment_method", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["swap_request_id"], ["swap_requests.id"]),
        sa.ForeignKeyConstraint(["hub_id"], ["hubs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("swap_request_id"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=30), nullable=False),
        sa.Column("swap_request_id", sa.String(length=20), nullable=True),
        sa.Column("swap_id", sa.String(length=20), nullable=True),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("paystack_reference", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["swap_request_id"], ["swap_requests.id"]),
        sa.ForeignKeyConstraint(["swap_id"], ["swaps.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paystack_reference"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("swap_id", sa.String(length=20), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["swap_id"], ["swaps.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_credit_transactions_user_id", "credit_transactions", ["user_id"])


def downgrade():
    op.drop_index("ix_credit_transactions_user_id", table_name="credit_transactions")
    op.drop_table("credit_transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("swaps")
    op.drop_index("ix_swap_requests_owner_id", table_name="swap_requests")
    op.drop_index("ix_swap_requests_initiator_id", table_name="swap_requests")
    op.drop_table("swap_requests")
    op.drop_index("ix_listings_category", table_name="listings")
    op.drop_index("ix_listings_user_id", table_name="listings")
    op.drop_table("listings")
    op.drop_table("hubs")
    op.drop_column("users", "longitude")
    op.drop_column("users", "latitude")
    op.drop_column("users", "strikes")
    op.drop_column("users", "credit_balance")
    op.drop_column("users", "role")
