"""remove_updated_at_from_referral_transactions

Revision ID: 7ee6feb1b026
Revises: add_referral_system
Create Date: 2024-04-14 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ee6feb1b026'
down_revision: Union[str, None] = 'add_referral_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove updated_at column from referral_transactions
    op.drop_column('referral_transactions', 'updated_at')


def downgrade() -> None:
    # Add updated_at column back to referral_transactions
    op.add_column('referral_transactions', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
