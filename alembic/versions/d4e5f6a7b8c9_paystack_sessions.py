"""Paystack checkout sessions for Flutter SDK."""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "paystack_sessions",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("access_code", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("gateway_response", sa.String(length=200), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transaction_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )
    op.create_index("ix_paystack_sessions_user_id", "paystack_sessions", ["user_id"])
    op.create_index("ix_paystack_sessions_reference", "paystack_sessions", ["reference"])


def downgrade():
    op.drop_index("ix_paystack_sessions_reference", table_name="paystack_sessions")
    op.drop_index("ix_paystack_sessions_user_id", table_name="paystack_sessions")
    op.drop_table("paystack_sessions")
