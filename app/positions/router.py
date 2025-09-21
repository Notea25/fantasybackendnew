from fastapi import APIRouter

from app.clubs.schemas import ClubRead
from app.clubs.services import ClubService

router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.get("/all")
async def list_clubs() -> list[ClubRead]:
    return await ClubService.find_all()


@router.get("/{club_id}")
async def get_club(club_id: int) -> list[ClubRead]:
    return await ClubService.find_one_or_none(club_id=club_id)


@router.get("/by_competition")
async def get_clubs_by_competition(competition_id: str) -> list[ClubRead]:
    return await ClubService.find_filtered(competition_id=competition_id)