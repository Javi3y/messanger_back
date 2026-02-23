"""add user_id to files

Revision ID: 20260224000003
Revises: 20260224000002
Create Date: 2026-02-24 00:00:03.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260224000003"
down_revision: Union[str, Sequence[str], None] = "20260224000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("files", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_files_user_id", "files", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_files_user_id_users",
        "files",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_files_user_id_users", "files", type_="foreignkey")
    op.drop_index("ix_files_user_id", table_name="files")
    op.drop_column("files", "user_id")
