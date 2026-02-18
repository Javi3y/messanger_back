"""outbox events

Revision ID: 20260204000001
Revises: ca7232639906
Create Date: 2026-02-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260204000001"
down_revision: Union[str, Sequence[str], None] = "ca7232639906"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "attempts", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("dedup_key", sa.String(length=255), nullable=True),
        sa.Column("aggregate_type", sa.String(length=50), nullable=True),
        sa.Column("aggregate_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outbox_events_id"), "outbox_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_outbox_events_event_type"),
        "outbox_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_events_available_at"),
        "outbox_events",
        ["available_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_events_processed_at"),
        "outbox_events",
        ["processed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_events_dedup_key"), "outbox_events", ["dedup_key"], unique=False
    )
    op.create_index(
        op.f("ix_outbox_events_aggregate_type"),
        "outbox_events",
        ["aggregate_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_events_aggregate_id"),
        "outbox_events",
        ["aggregate_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_events_created_at"),
        "outbox_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_outbox_events_created_at"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_aggregate_id"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_aggregate_type"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_dedup_key"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_processed_at"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_available_at"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_event_type"), table_name="outbox_events")
    op.drop_index(op.f("ix_outbox_events_id"), table_name="outbox_events")
    op.drop_table("outbox_events")
