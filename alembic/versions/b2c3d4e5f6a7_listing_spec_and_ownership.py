"""Add listing primary image, item specs, and ownership documents flag."""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "listings",
        sa.Column("primary_image_url", sa.String(length=500), nullable=True),
    )
    op.add_column("listings", sa.Column("serial_number", sa.String(length=100), nullable=True))
    op.add_column("listings", sa.Column("build_version", sa.String(length=100), nullable=True))
    op.add_column(
        "listings",
        sa.Column(
            "ownership_documents_available",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    # Backfill primary image from first gallery image for existing rows
    op.execute(
        """
        UPDATE listings
        SET primary_image_url = COALESCE(
            (image_urls::jsonb ->> 0),
            ''
        )
        WHERE primary_image_url IS NULL
        """
    )
    op.alter_column("listings", "primary_image_url", nullable=False)


def downgrade():
    op.drop_column("listings", "ownership_documents_available")
    op.drop_column("listings", "build_version")
    op.drop_column("listings", "serial_number")
    op.drop_column("listings", "primary_image_url")
