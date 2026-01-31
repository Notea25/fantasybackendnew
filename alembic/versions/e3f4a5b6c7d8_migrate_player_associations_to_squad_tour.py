"""Migrate player associations to squad_tour

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-01-31 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, Sequence[str], None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Copy main players associations from squads to squad_tours
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO squad_tour_players (squad_tour_id, player_id)
        SELECT st.id, spa.player_id
        FROM squad_tours st
        JOIN squads s ON st.squad_id = s.id
        JOIN squad_players_association spa ON spa.squad_id = s.id
        ON CONFLICT DO NOTHING
    """))
    
    # Copy bench players associations from squads to squad_tours
    connection.execute(sa.text("""
        INSERT INTO squad_tour_bench_players (squad_tour_id, player_id)
        SELECT st.id, sbpa.player_id
        FROM squad_tours st
        JOIN squads s ON st.squad_id = s.id
        JOIN squad_bench_players_association sbpa ON sbpa.squad_id = s.id
        ON CONFLICT DO NOTHING
    """))
    
    # Copy captain and vice_captain from squads to squad_tours
    connection.execute(sa.text("""
        UPDATE squad_tours st
        SET captain_id = s.captain_id,
            vice_captain_id = s.vice_captain_id
        FROM squads s
        WHERE st.squad_id = s.id
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # No downgrade needed - data remains in squad tables
    pass
