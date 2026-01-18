"""club custom league

Revision ID: ae601446e73b
Revises: db232a153de1
Create Date: 2026-01-11 18:30:51.338526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ae601446e73b'
down_revision: Union[str, Sequence[str], None] = 'db232a153de1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('custom_leagues', sa.Column('team_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'custom_leagues', 'teams', ['team_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'custom_leagues', type_='foreignkey')
    op.drop_column('custom_leagues', 'team_id')