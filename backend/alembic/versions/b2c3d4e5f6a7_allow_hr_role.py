"""allow HR in users.role check constraint

Revision ID: b2c3d4e5f6a7
Revises: e5f6a7b8c9d0
Create Date: 2026-08-19 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("users_role_check", "users", type_="check")
    op.create_check_constraint(
        "users_role_check",
        "users",
        "role IN ('EMPLOYEE', 'MANAGER', 'HR', 'ADMIN')",
    )


def downgrade() -> None:
    op.drop_constraint("users_role_check", "users", type_="check")
    op.create_check_constraint(
        "users_role_check",
        "users",
        "role IN ('EMPLOYEE', 'MANAGER', 'ADMIN')",
    )
