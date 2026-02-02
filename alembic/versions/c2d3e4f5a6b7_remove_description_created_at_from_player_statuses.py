"""remove description and created_at from player_statuses

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-02-02 21:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop description and created_at columns from player_statuses
    op.drop_column('player_statuses', 'description')
    op.drop_column('player_statuses', 'created_at')


def downgrade() -> None:
    # Re-add description and created_at columns
    op.add_column(
        'player_statuses',
        sa.Column('description', sa.String(), nullable=True)
    )
    op.add_column(
        'player_statuses',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )