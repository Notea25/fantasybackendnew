"""update empty usernames

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-02-03 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update all users with empty username to use their telegram ID
    op.execute("""
        UPDATE users 
        SET username = 'user_' || id::text 
        WHERE username = '' OR username IS NULL
    """)


def downgrade() -> None:
    # Cannot reliably downgrade - we don't know which usernames were originally empty
    pass
