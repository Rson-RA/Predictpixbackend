"""add firstname lastname fields

Revision ID: add_firstname_lastname_fields
Revises: 4f3a8b17f4c4
Create Date: 2024-04-14 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_firstname_lastname_fields'
down_revision: Union[str, None] = '4f3a8b17f4c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add firstname and lastname columns to users table
    op.add_column('users', sa.Column('firstname', sa.String(), nullable=True))
    op.add_column('users', sa.Column('lastname', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove firstname and lastname columns from users table
    op.drop_column('users', 'firstname')
    op.drop_column('users', 'lastname') 