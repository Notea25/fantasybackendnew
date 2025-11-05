import logging
from datetime import datetime

import httpx
from fastapi import HTTPException
from sqlalchemy import select, or_, exc
from sqlalchemy.orm import selectinload

from app.matches.schemas import MatchCreateSchema
from app.utils.base_service import BaseService
from app.config import settings
from app.database import async_session_maker
from app.utils.exceptions import ExternalAPIErrorException, FailedOperationException
from app.matches.models import Match
from app.utils.external_api import external_api


logger = logging.getLogger(__name__)

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
            logger.debug(f"Fetching matches for league {league_id} from external API")
            matches_data = await external_api.fetch_matches(league_id)
            logger.debug(f"Matches data received: {len(matches_data)} matches")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching matches for league {league_id}: {e}")
            raise ExternalAPIErrorException()
        except ValueError as e:
            logger.error(f"No matches found for league {league_id}: {e}")
            raise ExternalAPIErrorException(msg=str(e))
        except Exception as e:
            logger.error(f"Unexpected error fetching matches for league {league_id}: {e}")
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            for match_data in matches_data:
                try:
                    fixture = match_data.get("fixture", {})
                    teams = match_data.get("teams", {})
                    goals = match_data.get("goals", {})
                    score = match_data.get("score", {})
                    if not fixture or not teams or not goals:
                        logger.warning(f"Missing required data in match: {match_data}")
                        continue

                    match_schema = MatchCreateSchema(
                        id=fixture.get("id"),
                        date=datetime.fromisoformat(fixture["date"].replace('Z', '+00:00')),
                        status=fixture.get("status", {}).get("long", "Not Started"),
                        duration=fixture.get("status", {}).get("elapsed"),
                        league_id=league_id,
                        home_team_id=teams.get("home", {}).get("id"),
                        away_team_id=teams.get("away", {}).get("id"),
                        home_team_score=goals.get("home"),
                        away_team_score=goals.get("away"),
                        home_team_penalties=score.get("penalty", {}).get("home") if score.get("penalty") else None,
                        away_team_penalties=score.get("penalty", {}).get("away") if score.get("penalty") else None
                    )

                    match_dict = match_schema.model_dump(exclude_none=True)

                    stmt = select(cls.model).where(cls.model.id == match_dict["id"])
                    result = await session.execute(stmt)
                    existing_match = result.scalar_one_or_none()

                    if not existing_match:
                        match = cls.model(**match_dict)
                        session.add(match)
                        logger.debug(f"Added match {match.id} to session")
                    else:
                        logger.debug(f"Match {match_dict['id']} already exists, skipping")
                except KeyError as e:
                    logger.error(f"Missing key in match data: {e}")
                    await session.rollback()
                    raise FailedOperationException(msg=f"Missing key in match data: {e}")
                except Exception as e:
                    logger.error(f"Error processing match: {e}")
                    await session.rollback()
                    raise FailedOperationException(msg=f"Error processing match: {e}")

            try:
                await session.commit()
                logger.info(f"Successfully committed matches for league {league_id}")
            except exc.SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Failed to commit matches for league {league_id}: {e}")
                raise FailedOperationException(msg=f"Failed to commit matches: {e}")

    @classmethod
    async def find_filtered(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()