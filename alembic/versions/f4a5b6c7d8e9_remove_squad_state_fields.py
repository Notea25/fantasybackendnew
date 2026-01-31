"""Remove squad state fields

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-01-31 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, Sequence[str], None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop association tables for squad players
    op.drop_table('squad_bench_players_association')
    op.drop_table('squad_players_association')
    
    # Drop foreign key constraints first
    op.drop_constraint('squads_captain_id_fkey', 'squads', type_='foreignkey')
    op.drop_constraint('squads_vice_captain_id_fkey', 'squads', type_='foreignkey')
    
    # Remove state columns from squads table
    op.drop_column('squads', 'vice_captain_id')
    op.drop_column('squads', 'captain_id')
    op.drop_column('squads', 'next_tour_penalty_points')
    op.drop_column('squads', 'penalty_points')
    op.drop_column('squads', 'points')
    op.drop_column('squads', 'replacements')
    op.drop_column('squads', 'budget')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add columns to squads table
    op.add_column('squads', sa.Column('budget', sa.Integer(), nullable=False, server_default='100000'))
    op.add_column('squads', sa.Column('replacements', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('squads', sa.Column('points', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('squads', sa.Column('penalty_points', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('squads', sa.Column('next_tour_penalty_points', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('squads', sa.Column('captain_id', sa.Integer(), nullable=True))
    op.add_column('squads', sa.Column('vice_captain_id', sa.Integer(), nullable=True))
    
    # Re-create foreign key constraints
    op.create_foreign_key('squads_captain_id_fkey', 'squads', 'players', ['captain_id'], ['id'])
    op.create_foreign_key('squads_vice_captain_id_fkey', 'squads', 'players', ['vice_captain_id'], ['id'])
    
    # Re-create association tables
    op.create_table(
        'squad_players_association',
        sa.Column('squad_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['squad_id'], ['squads.id']),
        sa.ForeignKeyConstraint(['player_id'], ['players.id']),
        sa.PrimaryKeyConstraint('squad_id', 'player_id')
    )
    
    op.create_table(
        'squad_bench_players_association',
        sa.Column('squad_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['squad_id'], ['squads.id']),
        sa.ForeignKeyConstraint(['player_id'], ['players.id']),
        sa.PrimaryKeyConstraint('squad_id', 'player_id')
    )
