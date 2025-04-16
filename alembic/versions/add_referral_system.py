"""add referral system

Revision ID: add_referral_system
Revises: add_firstname_lastname_fields
Create Date: 2024-04-14 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_referral_system'
down_revision: Union[str, None] = 'add_firstname_lastname_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add referral columns to users table
    op.add_column('users', sa.Column('referral_code', sa.String(), nullable=True))
    op.add_column('users', sa.Column('referral_earnings', sa.Float(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('referred_by_id', sa.Integer(), nullable=True))
    
    # Create indexes for referral_code
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
    
    # Add foreign key for referred_by_id
    op.create_foreign_key('fk_users_referred_by_id', 'users', 'users', ['referred_by_id'], ['id'])
    
    # Create referral_transactions table
    op.create_table('referral_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('referred_user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referral_transactions_id'), 'referral_transactions', ['id'], unique=False)


def downgrade() -> None:
    # Drop referral_transactions table
    op.drop_index(op.f('ix_referral_transactions_id'), table_name='referral_transactions')
    op.drop_table('referral_transactions')
    
    # Drop referral columns from users table
    op.drop_constraint('fk_users_referred_by_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_column('users', 'referred_by_id')
    op.drop_column('users', 'referral_earnings')
    op.drop_column('users', 'referral_code') 