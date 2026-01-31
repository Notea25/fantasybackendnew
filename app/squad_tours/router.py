from fastapi import APIRouter

# SquadTour endpoints are currently handled by squads/router.py
# since they are tightly coupled with Squad operations.
# This router is reserved for future SquadTour-specific endpoints if needed.

router = APIRouter(prefix="/squad_tours", tags=["Squad Tours"])
