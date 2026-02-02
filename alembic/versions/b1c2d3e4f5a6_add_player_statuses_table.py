"""add player statuses table

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f7
Create Date: 2026-02-02 21:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create player_statuses table
    op.create_table(
        'player_statuses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('status_type', sa.String(), nullable=False),
        sa.Column('tour_start', sa.Integer(), nullable=False),
        sa.Column('tour_end', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_player_statuses_player_id', 'player_statuses', ['player_id'])
    op.create_index('ix_player_tours', 'player_statuses', ['player_id', 'tour_start', 'tour_end'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_player_tours', table_name='player_statuses')
    op.drop_index('ix_player_statuses_player_id', table_name='player_statuses')
    
    # Drop table
    op.drop_table('player_statuses')