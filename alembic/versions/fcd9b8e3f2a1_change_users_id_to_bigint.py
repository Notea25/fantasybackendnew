"""change_users_id_to_bigint

Revision ID: fcd9b8e3f2a1
Revises: f1a4c9d8e3ab
Create Date: 2026-01-30 22:50:16.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcd9b8e3f2a1'
down_revision: Union[str, Sequence[str], None] = 'f1a4c9d8e3ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Change users.id from INTEGER to BIGINT."""
    # Change users.id to BIGINT
    op.alter_column('users', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)
    
    # Change squads.user_id to BIGINT (foreign key to users.id)
    op.alter_column('squads', 'user_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)
    
    # Change custom_leagues.creator_id to BIGINT (foreign key to users.id)
    op.alter_column('custom_leagues', 'creator_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema - Revert users.id back to INTEGER."""
    # Revert custom_leagues.creator_id to INTEGER
    op.alter_column('custom_leagues', 'creator_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    
    # Revert squads.user_id to INTEGER
    op.alter_column('squads', 'user_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    
    # Revert users.id to INTEGER
    op.alter_column('users', 'id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
