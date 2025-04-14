"""add_avatar_field_to_users

Revision ID: e799fa3d5ee6
Revises: 9a675ef3c9f8
Create Date: 2024-04-14 01:45:32.263386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e799fa3d5ee6'
down_revision: Union[str, None] = '9a675ef3c9f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add avatar_url column to users table
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove avatar_url column from users table
    op.drop_column('users', 'avatar_url')
