"""add leave_type_approval_steps, leave_application_steps, leave_application_documents tables

Revision ID: e5f6a7b8c9d0
Revises:
Create Date: 2026-08-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leave_type_approval_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leave_type_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("approver_role", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["leave_type_id"],
            ["leave_types.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("leave_type_id", "step_order", name="uq_leave_type_step_order"),
    )
    op.create_index(
        op.f("ix_leave_type_approval_steps_id"),
        "leave_type_approval_steps",
        ["id"],
        unique=False,
    )

    op.create_table(
        "leave_application_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leave_application_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("approver_role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="WAITING"),
        sa.Column("decided_by", sa.Integer(), nullable=True),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["leave_application_id"],
            ["leave_applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by"],
            ["users.id"],
        ),
    )
    op.create_index(
        op.f("ix_leave_application_steps_id"),
        "leave_application_steps",
        ["id"],
        unique=False,
    )

    op.create_table(
        "leave_application_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leave_application_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["leave_application_id"],
            ["leave_applications.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("leave_application_id", name="uq_leave_application_documents_leave_application_id"),
    )
    op.create_index(
        op.f("ix_leave_application_documents_id"),
        "leave_application_documents",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_leave_application_documents_id"), table_name="leave_application_documents")
    op.drop_table("leave_application_documents")
    op.drop_index(op.f("ix_leave_application_steps_id"), table_name="leave_application_steps")
    op.drop_table("leave_application_steps")
    op.drop_index(op.f("ix_leave_type_approval_steps_id"), table_name="leave_type_approval_steps")
    op.drop_table("leave_type_approval_steps")
