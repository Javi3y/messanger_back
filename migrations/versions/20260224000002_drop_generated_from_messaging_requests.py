"""drop generated from messaging_requests

Revision ID: 20260224000002
Revises: 20260204000001
Create Date: 2026-02-24 00:00:02.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260224000002"
down_revision: Union[str, Sequence[str], None] = "20260204000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("messaging_requests", "generated")


def downgrade() -> None:
    op.add_column(
        "messaging_requests",
        sa.Column("generated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
