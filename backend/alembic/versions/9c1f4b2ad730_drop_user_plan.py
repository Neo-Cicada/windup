"""drop the user plan column

The academy is free while it is being built, so there is no paid tier to record.
The column comes back with the billing flow, if there ever is one.

Revision ID: 9c1f4b2ad730
Revises: 2711da7f5aad
Create Date: 2026-07-26 10:12:04.118233
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '9c1f4b2ad730'
down_revision: str | None = '2711da7f5aad'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column('users', 'plan')


def downgrade() -> None:
    op.add_column(
        'users',
        sa.Column('plan', sa.String(length=16), nullable=False, server_default='free'),
    )
    op.alter_column('users', 'plan', server_default=None)
