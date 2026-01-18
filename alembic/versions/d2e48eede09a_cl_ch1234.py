"""cl ch1234

Revision ID: d2e48eede09a
Revises: 248526e1458e
Create Date: 2026-01-17 12:02:49.216397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd2e48eede09a'
down_revision: Union[str, Sequence[str], None] = '248526e1458e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_leagues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('league_id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('club_leagues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('league_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_league_tours',
    sa.Column('tour_id', sa.Integer(), nullable=False),
    sa.Column('user_league_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ),
    sa.ForeignKeyConstraint(['user_league_id'], ['user_leagues.id'], ),
    sa.PrimaryKeyConstraint('tour_id', 'user_league_id')
    )
    op.create_table('club_league_tours',
    sa.Column('tour_id', sa.Integer(), nullable=False),
    sa.Column('club_league_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['club_league_id'], ['club_leagues.id'], ),
    sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ),
    sa.PrimaryKeyConstraint('tour_id', 'club_league_id')
    )
    op.create_table('club_league_squads',
    sa.Column('squad_id', sa.Integer(), nullable=False),
    sa.Column('club_league_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['club_league_id'], ['club_leagues.id'], ),
    sa.ForeignKeyConstraint(['squad_id'], ['squads.id'], ),
    sa.PrimaryKeyConstraint('squad_id', 'club_league_id')
    )
    op.create_table('commercial_leagues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('league_id', sa.Integer(), nullable=False),
    sa.Column('prize', sa.String(), nullable=True),
    sa.Column('logo', sa.String(), nullable=True),
    sa.Column('winner_id', sa.Integer(), nullable=True),
    sa.Column('registration_start', sa.DateTime(), nullable=True),
    sa.Column('registration_end', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
    sa.ForeignKeyConstraint(['winner_id'], ['squads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_league_squads',
    sa.Column('squad_id', sa.Integer(), nullable=False),
    sa.Column('user_league_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['squad_id'], ['squads.id'], ),
    sa.ForeignKeyConstraint(['user_league_id'], ['user_leagues.id'], ),
    sa.PrimaryKeyConstraint('squad_id', 'user_league_id')
    )
    op.create_table('commercial_league_squads',
    sa.Column('squad_id', sa.Integer(), nullable=False),
    sa.Column('commercial_league_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['commercial_league_id'], ['commercial_leagues.id'], ),
    sa.ForeignKeyConstraint(['squad_id'], ['squads.id'], ),
    sa.PrimaryKeyConstraint('squad_id', 'commercial_league_id')
    )
    op.create_table('commercial_league_tours',
    sa.Column('tour_id', sa.Integer(), nullable=False),
    sa.Column('commercial_league_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['commercial_league_id'], ['commercial_leagues.id'], ),
    sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ),
    sa.PrimaryKeyConstraint('tour_id', 'commercial_league_id')
    )
    op.drop_table('custom_league_squads')
    op.drop_table('custom_league_tours')
    op.drop_table('custom_leagues')

def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('custom_leagues',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('custom_leagues_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('league_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('type', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('is_public', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('invitation_only', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('creator_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('registration_start', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('registration_end', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('team_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('prize', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('logo', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('winner_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], name='custom_leagues_creator_id_fkey'),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], name='custom_leagues_league_id_fkey'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name='custom_leagues_team_id_fkey'),
    sa.ForeignKeyConstraint(['winner_id'], ['squads.id'], name='custom_leagues_winner_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='custom_leagues_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('custom_league_tours',
    sa.Column('custom_league_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('tour_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['custom_league_id'], ['custom_leagues.id'], name=op.f('custom_league_tours_custom_league_id_fkey')),
    sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], name=op.f('custom_league_tours_tour_id_fkey')),
    sa.PrimaryKeyConstraint('custom_league_id', 'tour_id', name=op.f('custom_league_tours_pkey'))
    )
    op.create_table('custom_league_squads',
    sa.Column('custom_league_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('squad_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['custom_league_id'], ['custom_leagues.id'], name=op.f('custom_league_squads_custom_league_id_fkey')),
    sa.ForeignKeyConstraint(['squad_id'], ['squads.id'], name=op.f('custom_league_squads_squad_id_fkey')),
    sa.PrimaryKeyConstraint('custom_league_id', 'squad_id', name=op.f('custom_league_squads_pkey'))
    )
    op.drop_table('commercial_league_tours')
    op.drop_table('commercial_league_squads')
    op.drop_table('user_league_squads')
    op.drop_table('commercial_leagues')
    op.drop_table('club_league_squads')
    op.drop_table('club_league_tours')
    op.drop_table('user_league_tours')
    op.drop_table('club_leagues')
    op.drop_table('user_leagues')