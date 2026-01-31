# Deployment Guide: Penalty Points System

## Overview
This guide covers deployment of the penalty points system implementation. The system tracks penalties when users exceed their free transfer limit (2 transfers per tour).

## Backend Deployment

### 1. Verify Migration Chain
```bash
cd C:\Users\val2\projects\sporttg
alembic current
# Expected: fcd9b8e3f2a1 (bigint users)
```

### 2. Apply Database Migration
```bash
# Apply penalty_points migration
alembic upgrade head

# Verify migration applied
alembic current
# Expected: a3f7b8c9d1e2 (add penalty_points to squads and squad_tours)
```

### 3. Restart Backend Service
```bash
# If using Docker Compose
docker-compose restart sp_app

# Or if running manually
# Stop current process (Ctrl+C)
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify Backend Changes
Test the following endpoints:
- `GET /api/squads/my_squads` - Should include `penalty_points` field
- `GET /api/squads/leaderboard/{tour_id}` - Should include `penalty_points` in entries
- `POST /api/squads/{squad_id}/replace_players` - Should apply penalties when transfers > 2

## Frontend Deployment

### 1. Build Frontend
```bash
cd C:\Users\val2\projects\tele-mini-sparkle
npm run build
```

### 2. Deploy Build
Copy the `dist/` directory to your production server or hosting service.

### 3. Verify Frontend Changes
Check that the following pages display penalty points:
- `/league` - Main leaderboard and club leaderboard
- `/tournament-table` - Full tournament table
- `/view-team?id={squad_id}` - Team details page
- `/view-user-league?id={league_id}` - User league pages
- `/view-com-league?id={league_id}` - Commercial league pages
- Tour history component

## Key Features Implemented

### Backend
- ✅ Database schema: `penalty_points` added to `squads` and `squad_tours` tables
- ✅ Transfer penalty logic: 4 points per paid transfer (when transfers > 2)
- ✅ All endpoints return `penalty_points`
- ✅ Leaderboards sort by net points (`total_points - penalty_points`)
- ✅ Admin panel supports editing penalty points
- ✅ Squad creation fixed: always creates for next tour

### Frontend
- ✅ Type definitions updated: All API interfaces include `penalty_points`
- ✅ UI component: `PointsDisplay` for compact/detailed display
- ✅ All leaderboard pages show penalty points
- ✅ Team view page shows penalty breakdown
- ✅ Tour history shows penalties per tour

## Testing Checklist

### Backend Tests
- [ ] Create a squad (should initialize with `penalty_points=0`)
- [ ] Make 2 transfers (should be free, no penalties)
- [ ] Make 3rd transfer (should add 4 penalty points)
- [ ] Make 4th transfer (should add another 4 penalty points, total 8)
- [ ] Check leaderboard (should sort by `total_points - penalty_points`)
- [ ] Check squad tour snapshots (should include penalty_points)

### Frontend Tests
- [ ] View leaderboard on `/league` (shows penalty info)
- [ ] View team details (shows penalty breakdown)
- [ ] View tournament table (includes penalty data)
- [ ] View tour history (shows penalties per tour)
- [ ] Check all custom league pages (user/commercial leagues)

## Rollback Procedure

If issues occur, rollback the migration:

```bash
cd C:\Users\val2\projects\sporttg
alembic downgrade -1
docker-compose restart sp_app
```

This will remove the `penalty_points` columns from the database.

## Monitoring

After deployment, monitor:
- Database performance (new columns should not impact queries significantly)
- API response times (penalty calculation is minimal overhead)
- User feedback on penalty display

## Notes

- Default free transfers: **2 per tour**
- Penalty rate: **4 points per paid transfer**
- Penalty calculation: `paid_transfers = max(0, transfer_count - available_replacements)`
- Squad creation: Always for **next tour** (not current)
- Penalties accumulate in `Squad.penalty_points` and sync to `SquadTour.penalty_points`
- Net points displayed: `points - penalty_points`

## Documentation

Full implementation details:
- `PENALTY_POINTS_IMPLEMENTATION.md` - Backend implementation
- `FRONTEND_PENALTY_POINTS_GUIDE.md` - Frontend integration guide
- `SQUAD_CREATION_LOGIC_FIX.md` - Squad creation bug fix

## Support

For issues or questions, refer to the implementation documentation files or contact the development team.
