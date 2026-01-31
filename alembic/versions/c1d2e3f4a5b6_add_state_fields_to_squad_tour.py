"""Add state fields to squad_tour

Revision ID: c1d2e3f4a5b6
Revises: b4e8f9c0d2a3
Create Date: 2026-01-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b4e8f9c0d2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add state fields to squad_tours table
    op.add_column('squad_tours', sa.Column('budget', sa.Integer(), nullable=False, server_default='100000'))
    op.add_column('squad_tours', sa.Column('replacements', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('squad_tours', sa.Column('is_finalized', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('squad_tours', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove state fields from squad_tours table
    op.drop_column('squad_tours', 'created_at')
    op.drop_column('squad_tours', 'is_finalized')
    op.drop_column('squad_tours', 'replacements')
    op.drop_column('squad_tours', 'budget')
