"""add cascade delete constraints

Revision ID: bb22cc33dd44
Revises: aa11bb22cc33
Create Date: 2026-02-04 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb22cc33dd44'
down_revision: Union[str, Sequence[str], None] = 'aa11bb22cc33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CASCADE constraints to foreign keys."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing foreign key constraints
    if 'players' in inspector.get_table_names():
        fks = inspector.get_foreign_keys('players')
        
        # Drop and recreate players.team_id with CASCADE
        for fk in fks:
            if 'team_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'players', type_='foreignkey')
                op.create_foreign_key(
                    'fk_players_team_id',
                    'players',
                    'teams',
                    ['team_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
            elif 'league_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'players', type_='foreignkey')
                op.create_foreign_key(
                    'fk_players_league_id',
                    'players',
                    'leagues',
                    ['league_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
    
    # Drop and recreate matches foreign keys with CASCADE
    if 'matches' in inspector.get_table_names():
        fks = inspector.get_foreign_keys('matches')
        
        for fk in fks:
            if 'league_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'matches', type_='foreignkey')
                op.create_foreign_key(
                    'fk_matches_league_id',
                    'matches',
                    'leagues',
                    ['league_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
            elif 'home_team_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'matches', type_='foreignkey')
                op.create_foreign_key(
                    'fk_matches_home_team_id',
                    'matches',
                    'teams',
                    ['home_team_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
            elif 'away_team_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'matches', type_='foreignkey')
                op.create_foreign_key(
                    'fk_matches_away_team_id',
                    'matches',
                    'teams',
                    ['away_team_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
    
    # Drop and recreate teams.league_id with CASCADE
    if 'teams' in inspector.get_table_names():
        fks = inspector.get_foreign_keys('teams')
        
        for fk in fks:
            if 'league_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'teams', type_='foreignkey')
                op.create_foreign_key(
                    'fk_teams_league_id',
                    'teams',
                    'leagues',
                    ['league_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
    
    # Drop and recreate player_match_stats foreign keys with CASCADE
    if 'player_match_stats' in inspector.get_table_names():
        fks = inspector.get_foreign_keys('player_match_stats')
        
        for fk in fks:
            if 'player_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'player_match_stats', type_='foreignkey')
                op.create_foreign_key(
                    'fk_player_match_stats_player_id',
                    'player_match_stats',
                    'players',
                    ['player_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
            elif 'match_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'player_match_stats', type_='foreignkey')
                op.create_foreign_key(
                    'fk_player_match_stats_match_id',
                    'player_match_stats',
                    'matches',
                    ['match_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
    
    # Drop and recreate squads.league_id with CASCADE
    if 'squads' in inspector.get_table_names():
        fks = inspector.get_foreign_keys('squads')
        
        for fk in fks:
            if 'league_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'squads', type_='foreignkey')
                op.create_foreign_key(
                    'fk_squads_league_id',
                    'squads',
                    'leagues',
                    ['league_id'],
                    ['id'],
                    ondelete='CASCADE'
                )
    
    # Drop and recreate tours.league_id with CASCADE
    if 'tours' in inspector.get_table_names():
        fks = inspector.get_foreign_keys('tours')
        
        for fk in fks:
            if 'league_id' in fk['constrained_columns']:
                op.drop_constraint(fk['name'], 'tours', type_='foreignkey')
                op.create_foreign_key(
                    'fk_tours_league_id',
                    'tours',
                    'leagues',
                    ['league_id'],
                    ['id'],
                    ondelete='CASCADE'
                )


def downgrade() -> None:
    """Remove CASCADE constraints from foreign keys."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Restore players foreign keys without CASCADE
    if 'players' in inspector.get_table_names():
        op.drop_constraint('fk_players_team_id', 'players', type_='foreignkey')
        op.create_foreign_key(None, 'players', 'teams', ['team_id'], ['id'])
        
        op.drop_constraint('fk_players_league_id', 'players', type_='foreignkey')
        op.create_foreign_key(None, 'players', 'leagues', ['league_id'], ['id'])
    
    # Restore matches foreign keys without CASCADE
    if 'matches' in inspector.get_table_names():
        op.drop_constraint('fk_matches_league_id', 'matches', type_='foreignkey')
        op.create_foreign_key(None, 'matches', 'leagues', ['league_id'], ['id'])
        
        op.drop_constraint('fk_matches_home_team_id', 'matches', type_='foreignkey')
        op.create_foreign_key(None, 'matches', 'teams', ['home_team_id'], ['id'])
        
        op.drop_constraint('fk_matches_away_team_id', 'matches', type_='foreignkey')
        op.create_foreign_key(None, 'matches', 'teams', ['away_team_id'], ['id'])
    
    # Restore teams foreign key without CASCADE
    if 'teams' in inspector.get_table_names():
        op.drop_constraint('fk_teams_league_id', 'teams', type_='foreignkey')
        op.create_foreign_key(None, 'teams', 'leagues', ['league_id'], ['id'])
    
    # Restore player_match_stats foreign keys without CASCADE
    if 'player_match_stats' in inspector.get_table_names():
        op.drop_constraint('fk_player_match_stats_player_id', 'player_match_stats', type_='foreignkey')
        op.create_foreign_key(None, 'player_match_stats', 'players', ['player_id'], ['id'])
        
        op.drop_constraint('fk_player_match_stats_match_id', 'player_match_stats', type_='foreignkey')
        op.create_foreign_key(None, 'player_match_stats', 'matches', ['match_id'], ['id'])
    
    # Restore squads foreign key without CASCADE
    if 'squads' in inspector.get_table_names():
        op.drop_constraint('fk_squads_league_id', 'squads', type_='foreignkey')
        op.create_foreign_key(None, 'squads', 'leagues', ['league_id'], ['id'])
    
    # Restore tours foreign key without CASCADE
    if 'tours' in inspector.get_table_names():
        op.drop_constraint('fk_tours_league_id', 'tours', type_='foreignkey')
        op.create_foreign_key(None, 'tours', 'leagues', ['league_id'], ['id'])
