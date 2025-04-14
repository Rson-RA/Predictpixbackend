"""make_pi_user_id_nullable

Revision ID: 9a675ef3c9f8
Revises: 7501e07ff86a
Create Date: 2025-04-14 01:19:32.263386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a675ef3c9f8'
down_revision: Union[str, None] = '7501e07ff86a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make pi_user_id column nullable
    op.alter_column('users', 'pi_user_id',
               existing_type=sa.String(),
               nullable=True)


def downgrade() -> None:
    # Make pi_user_id column non-nullable again
    op.alter_column('users', 'pi_user_id',
               existing_type=sa.String(),
               nullable=False)
