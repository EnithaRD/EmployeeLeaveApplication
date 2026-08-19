"""add approval_routing_rules table and leave_applications approval columns

Revision ID: a1b2c3d4e5f6
Revises: d4f8a1c2b3e4
Create Date: 2026-08-19 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d4f8a1c2b3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_routing_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leave_type_id", sa.Integer(), nullable=False),
        sa.Column("approval_chain", sa.String(length=100), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["leave_type_id"],
            ["leave_types.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("leave_type_id", name="uq_approval_routing_rules_leave_type_id"),
    )
    op.create_index(
        op.f("ix_approval_routing_rules_id"),
        "approval_routing_rules",
        ["id"],
        unique=False,
    )

    op.add_column(
        "leave_applications",
        sa.Column("approval_chain", sa.String(length=100), server_default="MANAGER", nullable=False),
    )
    op.add_column(
        "leave_applications",
        sa.Column("approval_stage", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("leave_applications", "approval_stage")
    op.drop_column("leave_applications", "approval_chain")
    op.drop_index(op.f("ix_approval_routing_rules_id"), table_name="approval_routing_rules")
    op.drop_table("approval_routing_rules")
