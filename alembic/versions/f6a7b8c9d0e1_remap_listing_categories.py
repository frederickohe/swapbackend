"""Restore domain labels onto the original listing category set.

Previously this revision remapped Electronics/Fashion/… → Phones/Services/….
That direction is no longer desired; upgrade only remaps the short-lived
domain labels back onto the restored categories.
"""

from alembic import op


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None

# Domain labels → restored item categories (best-effort; many→one was irreversible).
_DOMAIN_TO_RESTORED = (
    ("Cryptos", "Electronics"),
    ("Services", "Fashion"),
    ("Phones", "Electronics"),
    ("Laptops", "Electronics"),
    ("Cars", "Vehicles"),
    ("Games", "Video Games"),
)


def upgrade():
    for domain, restored in _DOMAIN_TO_RESTORED:
        domain_sql = domain.replace("'", "''")
        restored_sql = restored.replace("'", "''")
        op.execute(
            f"UPDATE listings SET category = '{restored_sql}' "
            f"WHERE category = '{domain_sql}'"
        )


def downgrade():
    # Ambiguous; leave restored labels in place.
    pass
