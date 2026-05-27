"""Fix swap requests stuck on PENDING_INITIATOR_FEE before owner approval."""
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE swap_requests
        SET status = 'PENDING_OWNER_APPROVAL'
        WHERE status = 'PENDING_INITIATOR_FEE'
          AND (initiator_paystack_ref IS NULL OR TRIM(initiator_paystack_ref) = '')
          AND initiator_fee_paid IS NOT TRUE
          AND hub_id IS NULL
        """
    )


def downgrade():
    pass
