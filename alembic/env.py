from logging.config import fileConfig
from os.path import abspath, dirname
from sqlalchemy import engine_from_config, pool

from alembic import context

import sys
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from app.config import settings
from app.database import Base

from app.admin.models import Admin
from app.leagues.models import League
from app.teams.models import Team
from app.matches.models import Match
from app.players.models import Player
from app.player_match_stats.models import PlayerMatchStats
from app.squads.models import Squad
from app.boosts.models import Boost
from app.users.models import User
from app.tours.models import Tour
from app.custom_leagues.models import CustomLeague

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    f"{settings.DATABASE_URL}?async_fallback=True"
)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            process_revision_directives=process_revision_directives
        )

        with context.begin_transaction():
            context.run_migrations()

def process_revision_directives(context, revision, directives):
    """Process custom revision directives."""
    if getattr(context.config.cmd_opts, 'autogenerate', False):
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
