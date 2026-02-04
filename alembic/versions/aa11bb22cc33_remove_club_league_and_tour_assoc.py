"""remove club leagues and tour-match association; add tour_id to matches

Revision ID: aa11bb22cc33
Revises: fcd9b8e3f2a1
Create Date: 2026-02-04 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aa11bb22cc33'
down_revision: Union[str, Sequence[str], None] = ('fcd9b8e3f2a1', 'ae601446e73b', 'a1b2c3d4e5f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1) Add tour_id to matches if not exists
    if 'matches' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('matches')]
        if 'tour_id' not in cols:
            op.add_column('matches', sa.Column('tour_id', sa.Integer(), nullable=True))
            op.create_foreign_key('fk_matches_tour_id', 'matches', 'tours', ['tour_id'], ['id'])

    # 2) Backfill tour_id from association table if present
    if 'tour_matches_association' in inspector.get_table_names():
        op.execute(
            sa.text(
                """
                UPDATE matches m
                SET tour_id = tma.tour_id
                FROM tour_matches_association tma
                WHERE m.id = tma.match_id AND m.tour_id IS NULL
                """
            )
        )

    # 3) Drop association table
    if 'tour_matches_association' in inspector.get_table_names():
        op.drop_table('tour_matches_association')

    # 4) Drop club league related tables if present
    if 'club_league_tours' in inspector.get_table_names():
        op.drop_table('club_league_tours')
    if 'club_league_squads' in inspector.get_table_names():
        op.drop_table('club_league_squads')
    if 'club_leagues' in inspector.get_table_names():
        op.drop_table('club_leagues')


def downgrade() -> None:
    # 1) Recreate club leagues tables (minimal structure)
    op.create_table(
        'club_leagues',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('league_id', sa.Integer(), sa.ForeignKey('leagues.id')),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
    )
    op.create_table(
        'club_league_squads',
        sa.Column('club_league_id', sa.Integer(), sa.ForeignKey('club_leagues.id'), primary_key=True),
        sa.Column('squad_id', sa.Integer(), sa.ForeignKey('squads.id'), primary_key=True),
    )
    op.create_table(
        'club_league_tours',
        sa.Column('club_league_id', sa.Integer(), sa.ForeignKey('club_leagues.id'), primary_key=True),
        sa.Column('tour_id', sa.Integer(), sa.ForeignKey('tours.id'), primary_key=True),
    )

    # 2) Recreate tour_matches_association
    op.create_table(
        'tour_matches_association',
        sa.Column('tour_id', sa.Integer(), sa.ForeignKey('tours.id'), primary_key=True),
        sa.Column('match_id', sa.Integer(), sa.ForeignKey('matches.id'), primary_key=True),
    )
    # Backfill from matches.tour_id
    op.execute(
        sa.text(
            """
            INSERT INTO tour_matches_association (tour_id, match_id)
            SELECT DISTINCT tour_id, id FROM matches WHERE tour_id IS NOT NULL
            """
        )
    )

    # 3) Drop matches.tour_id
    with op.batch_alter_table('matches') as batch_op:
        batch_op.drop_constraint('fk_matches_tour_id', type_='foreignkey')
        batch_op.drop_column('tour_id')
