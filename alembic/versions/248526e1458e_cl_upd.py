"""cl upd

Revision ID: 248526e1458e
Revises: ae601446e73b
Create Date: 2026-01-13 00:11:14.472198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '248526e1458e'
down_revision: Union[str, Sequence[str], None] = 'ae601446e73b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('custom_leagues', sa.Column('prize', sa.String(), nullable=True))
    op.add_column('custom_leagues', sa.Column('logo', sa.String(), nullable=True))
    op.add_column('custom_leagues', sa.Column('winner_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'custom_leagues', 'squads', ['winner_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'custom_leagues', type_='foreignkey')
    op.drop_column('custom_leagues', 'winner_id')
    op.drop_column('custom_leagues', 'logo')
    op.drop_column('custom_leagues', 'prize')