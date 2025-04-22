"""remove updated_at from referral_transactions

Revision ID: 7ee6feb1b026
Revises: add_referral_system
Create Date: 2024-04-14 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7ee6feb1b026'
down_revision: Union[str, None] = 'add_referral_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Check if column exists before trying to drop it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    has_column = False
    for column in inspector.get_columns('referral_transactions'):
        if column['name'] == 'updated_at':
            has_column = True
            break
    
    if has_column:
        op.drop_column('referral_transactions', 'updated_at')

def downgrade() -> None:
    # Add the column back if it doesn't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    has_column = False
    for column in inspector.get_columns('referral_transactions'):
        if column['name'] == 'updated_at':
            has_column = True
            break
    
    if not has_column:
        op.add_column('referral_transactions', sa.Column('updated_at', sa.DateTime(), nullable=True))
