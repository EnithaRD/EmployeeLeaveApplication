"""add medical_certificates table

Revision ID: d4f8a1c2b3e4
Revises:
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4f8a1c2b3e4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medical_certificates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leave_application_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["leave_application_id"],
            ["leave_applications.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("leave_application_id", name="uq_medical_certificates_leave_application_id"),
        sa.UniqueConstraint("stored_filename", name="uq_medical_certificates_stored_filename"),
    )
    op.create_index(
        op.f("ix_medical_certificates_id"),
        "medical_certificates",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_medical_certificates_id"), table_name="medical_certificates")
    op.drop_table("medical_certificates")
