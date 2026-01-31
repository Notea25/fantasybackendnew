"""Add next_tour_penalty_points to squad

Revision ID: b4e8f9c0d2a3
Revises: a3f7b8c9d1e2
Create Date: 2026-01-31 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4e8f9c0d2a3'
down_revision: Union[str, Sequence[str], None] = 'a3f7b8c9d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add next_tour_penalty_points to squads table
    op.add_column('squads', sa.Column('next_tour_penalty_points', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove next_tour_penalty_points from squads table
    op.drop_column('squads', 'next_tour_penalty_points')
