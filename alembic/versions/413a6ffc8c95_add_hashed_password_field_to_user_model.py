"""Add hashed_password field to User model

Revision ID: 413a6ffc8c95
Revises: 
Create Date: 2025-04-13 03:25:17.958429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '413a6ffc8c95'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pi_user_id', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('role', sa.Enum('ADMIN', 'USER', name='userrole'), nullable=True),
    sa.Column('balance', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_pi_user_id'), 'users', ['pi_user_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('prediction_markets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.Column('resolution_time', sa.DateTime(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'CLOSED', 'SETTLED', 'CANCELLED', name='marketstatus'), nullable=True),
    sa.Column('total_pool', sa.Float(), nullable=True),
    sa.Column('yes_pool', sa.Float(), nullable=True),
    sa.Column('no_pool', sa.Float(), nullable=True),
    sa.Column('correct_outcome', sa.String(), nullable=True),
    sa.Column('creator_fee_percentage', sa.Float(), nullable=True),
    sa.Column('platform_fee_percentage', sa.Float(), nullable=True),
    sa.Column('market_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_markets_id'), 'prediction_markets', ['id'], unique=False)
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('DEPOSIT', 'WITHDRAWAL', 'PREDICTION', 'WINNINGS', 'REFUND', 'FEE', name='transactiontype'), nullable=True),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('tx_hash', sa.String(), nullable=True),
    sa.Column('reference_id', sa.String(), nullable=True),
    sa.Column('transaction_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_table('predictions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('market_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('predicted_outcome', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'WON', 'LOST', 'CANCELLED', name='predictionstatus'), nullable=True),
    sa.Column('potential_winnings', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['market_id'], ['prediction_markets.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'], unique=False)
    op.create_table('rewards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('prediction_id', sa.Integer(), nullable=False),
    sa.Column('market_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=20, scale=6), nullable=False),
    sa.Column('original_prediction_amount', sa.Numeric(precision=20, scale=6), nullable=False),
    sa.Column('reward_multiplier', sa.Float(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PROCESSED', 'FAILED', 'CANCELLED', name='rewardstatus'), nullable=False),
    sa.Column('transaction_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('reward_metadata', sa.JSON(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['market_id'], ['prediction_markets.id'], ),
    sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rewards_id'), 'rewards', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_rewards_id'), table_name='rewards')
    op.drop_table('rewards')
    op.drop_index(op.f('ix_predictions_id'), table_name='predictions')
    op.drop_table('predictions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_prediction_markets_id'), table_name='prediction_markets')
    op.drop_table('prediction_markets')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_pi_user_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
