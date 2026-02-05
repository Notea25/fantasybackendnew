"""add name_rus to teams

Revision ID: dd44ee55ff66
Revises: cc33dd44ee55
Create Date: 2026-02-05 17:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd44ee55ff66'
down_revision: Union[str, Sequence[str], None] = 'cc33dd44ee55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add name_rus column to teams table."""
    op.add_column('teams', sa.Column('name_rus', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove name_rus column from teams table."""
    op.drop_column('teams', 'name_rus')
