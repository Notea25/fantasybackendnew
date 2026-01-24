# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **fantasy sports platform** built with FastAPI, SQLAlchemy (async), and PostgreSQL. Users create squads of players, compete in leagues (user-created, commercial, or club leagues), and earn points based on player performance in real matches. The system integrates with an external sports data API and includes an admin panel (SQLAdmin).

## Key Commands

### Local Development (Windows/PowerShell)
```powershell
# Install dependencies (using Poetry)
poetry install

# Create admin user (run once after database setup)
python create_admin.py

# Run database migrations
poetry run alembic upgrade head

# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Run development server
poetry run uvicorn app.main:app --reload --port 8000
```

### Docker Development
```powershell
# Start all services (PostgreSQL, FastAPI app, nginx)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f app

# Rebuild after dependency changes
docker-compose build
```

## Architecture

### Core Domain Models

The application follows a **domain-driven structure** with these primary entities:

1. **League** - Real-world sports leagues (e.g., Premier League)
2. **Team** - Real clubs in a league
3. **Player** - Athletes with market values and statistics
4. **Match** - Games between two teams
5. **Tour** - A round/gameweek in a league containing multiple matches
6. **Squad** - User's fantasy team (11 main + 4 bench players)
7. **User** - Platform users who create squads
8. **PlayerMatchStats** - Performance data for players in matches

### Custom Leagues System

The platform supports three types of **custom leagues** where squads compete:

- **UserLeague** - Private leagues created by users
- **CommercialLeague** - Sponsored/official leagues
- **ClubLeague** - Leagues for specific club fans

All three share the same base League model but have separate tables with many-to-many relationships to squads and tours.

### Squad System Architecture

**Critical constraint**: Each squad operates within a single base league (e.g., Premier League) and can join multiple custom leagues.

- **Squad composition**: Exactly 11 main players + 4 bench players
- **Budget constraint**: Total player cost must not exceed squad budget (default 100,000)
- **Club rule**: Maximum 3 players from the same club
- **Captain system**: Captain and vice-captain earn bonus points
- **SquadTour**: Snapshot of a squad's lineup/points for each gameweek

### Boosts System

Squads can use special boosts during tours to multiply points or provide other advantages. Each boost is tracked with `type`, `squad_id`, `tour_id`, and `used_at` timestamp.

### Database Patterns

- **Async SQLAlchemy** with `async_sessionmaker` and `AsyncSession`
- **Association tables** for many-to-many relationships (e.g., `squad_players_association`, `tour_matches_association`)
- **Relationship cascades** on `SquadTour` (`ondelete="CASCADE"`)
- All models inherit from `Base(AsyncAttrs, DeclarativeBase)`

### API Structure

Each domain module follows this pattern:
```
app/{domain}/
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas for validation
├── router.py      # FastAPI route definitions
└── services.py    # Business logic layer
```

All routers are registered in `app/main.py` with `/api` prefix.

### Admin Panel

- **SQLAdmin** integration at `/admin` endpoint
- Custom authentication backend (`AdminAuth`) using JWT
- Admin views for all major entities
- Special `UtilsView` for bulk data operations

### External API Integration

The platform fetches sports data from an external API:
- Configuration in `app/config.py`: `EXTERNAL_API_BASE_URL`, `EXTERNAL_API_KEY`, `EXTERNAL_API_SEASON`
- Utilities in `app/utils/router.py` for batch importing leagues, teams, players, and matches
- Use `/api/utils/add_all?league_id=116` to populate data for a league

### Middleware & Security

- **SessionMiddleware** for admin authentication (uses `SECRET_KEY` from config)
- **CORS middleware** conditionally enabled when `MODE=DEVFRONT` (for React frontend)
- **JWT-based authentication** for admin panel

## Environment Configuration

Required environment variables (defined in `.env`):
- `DATABASE_URL` - Async PostgreSQL connection string
- `SECRET_KEY` - Session encryption key
- `ALGORITHM` - JWT algorithm (default: HS256)
- `TELEGRAM_BOT_TOKEN` - For Telegram bot integration
- `EXTERNAL_API_BASE_URL` - Sports data API endpoint
- `EXTERNAL_API_KEY` - API authentication
- `EXTERNAL_API_SEASON` - Target season (default: 2025)
- `MODE` - Runtime mode (e.g., DEVFRONT for frontend dev)
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` - Admin credentials

Celery/Redis variables are present but currently unused (commented out in `docker-compose.yaml`).

## Important Implementation Notes

### When Adding New Models
1. Import in `alembic/env.py` to ensure migrations detect changes
2. Add corresponding SQLAdmin view in `app/admin/view.py`
3. Register view in `app/main.py`
4. Follow the existing service layer pattern for business logic

### Squad Modifications
- Always validate using `Squad.validate_players()` before updates
- Use `Squad.count_different_players()` to enforce replacement limits
- Update `Squad.points` by calling `Squad.calculate_points(session)`
- Create `SquadTour` snapshots when a tour starts

### Working with Tours
- Tours automatically calculate `start_date`, `end_date`, and `deadline` properties based on associated matches
- Use `tour_matches_association` table to link matches to tours
- Maintain `is_current` flag on `SquadTour` to track active gameweek

### Database Migrations
- Alembic is configured to use async connection string with `?async_fallback=True`
- Migrations auto-detect model changes via `--autogenerate`
- Custom `process_revision_directives` prevents empty migrations

## Docker Setup

The application runs in a multi-container environment:
- **db**: PostgreSQL 15 with health checks
- **app**: FastAPI server (auto-migrates on startup via `alembic upgrade head`)
- **nginx**: Reverse proxy on port 80
- **redis/celery**: Commented out but ready for background task implementation

Volume `postgresdata` persists database across container restarts.
