"""add_referrer_id_to_users

Revision ID: a1b2c3d4e5f7
Revises: f4a5b6c7d8e9
Create Date: 2026-02-01 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f4a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add referrer_id column to users table."""
    # Add referrer_id column (foreign key to users.id, nullable)
    op.add_column('users', 
        sa.Column('referrer_id', sa.BigInteger(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_users_referrer_id',  # constraint name
        'users',  # source table
        'users',  # referenced table
        ['referrer_id'],  # source column
        ['id'],  # referenced column
        ondelete='SET NULL'  # if referrer is deleted, set to NULL
    )
    
    # Add index for better query performance
    op.create_index(
        'ix_users_referrer_id',
        'users',
        ['referrer_id']
    )


def downgrade() -> None:
    """Remove referrer_id column from users table."""
    # Drop index
    op.drop_index('ix_users_referrer_id', table_name='users')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_users_referrer_id', 'users', type_='foreignkey')
    
    # Drop column
    op.drop_column('users', 'referrer_id')
