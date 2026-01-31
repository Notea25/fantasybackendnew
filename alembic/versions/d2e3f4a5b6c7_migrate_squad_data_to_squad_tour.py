"""Migrate squad data to squad_tour

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-01-31 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Copy budget and replacements from squads to squad_tours
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE squad_tours st
        SET budget = s.budget, 
            replacements = s.replacements
        FROM squads s
        WHERE st.squad_id = s.id
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # No downgrade needed - data remains in squads table
    pass
