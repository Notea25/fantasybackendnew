from datetime import datetime

import httpx
from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.base_service import BaseService
from app.config import settings
from app.database import async_session_maker
from app.exceptions import ExternalAPIErrorException, FailedOperationException
from app.matches.models import Match
from app.utils.external_api import external_api


class MatchService(BaseService):
    model=Match

    @staticmethod
    async def find_matches_by_team(team_id: int) -> list[Match]:
        async with async_session_maker() as session:
            query = (
                select(Match)
                .where(or_(
                    Match.home_team_id == team_id,
                    Match.away_team_id == team_id
                ))
                .options(
                    selectinload(Match.home_team),
                    selectinload(Match.away_team),
                    selectinload(Match.league)
                )
            )
            result = await session.execute(query)
            matches = result.scalars().all()
            return matches

    @staticmethod
    async def add_matches(league_id: int):
        try:
            matches_data = await external_api.fetch_matches(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"External API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch matches data: {e}")

        try:
            async with async_session_maker() as session:
                for match_data in matches_data:
                    match = Match(**match_data)
                    session.add(match)
                await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add matches to database: {e}")

    @classmethod
    async def add_matches_for_league(cls, league_id: int):
        try:
            matches_data = await external_api.fetch_matches(league_id, settings.EXTERNAL_API_SEASON)
        except httpx.HTTPStatusError:
            raise ExternalAPIErrorException()
        except Exception:
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            for match_data in matches_data:
                try:
                    fixture = match_data["fixture"]
                    teams = match_data["teams"]
                    goals = match_data["goals"]

                    match = cls.model(
                        id=fixture["id"],
                        date=datetime.fromisoformat(fixture["date"].replace('Z', '+00:00')),
                        status=fixture["status"]["long"],
                        duration=fixture["status"].get("elapsed"),
                        league_id=league_id,
                        home_team_id=teams["home"]["id"],
                        away_team_id=teams["away"]["id"],
                        home_team_score=goals["home"],
                        away_team_score=goals["away"],
                        home_team_penalties=match_data["score"].get("penalty", {}).get("home") if match_data[
                            "score"].get("penalty") else None,
                        away_team_penalties=match_data["score"].get("penalty", {}).get("away") if match_data[
                            "score"].get("penalty") else None
                    )
                    session.add(match)
                except Exception as e:
                    await session.rollback()
                    raise FailedOperationException(msg=f"Failed to add match: {e}")

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to commit matches: {e}")

    @classmethod
    async def find_filtered(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()