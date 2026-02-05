import logging

import httpx
from sqlalchemy.future import select
from deep_translator import GoogleTranslator

from app.database import async_session_maker
from app.teams.models import Team
from app.utils.base_service import BaseService
from app.utils.exceptions import (
    ExternalAPIErrorException,
    FailedOperationException,
)
from app.utils.external_api import external_api

logger = logging.getLogger(__name__)


class TeamService(BaseService):
    model = Team

    @classmethod
    async def add_teams(cls, league_id: int):
        try:
            teams_data = await external_api.fetch_teams(league_id)
            logger.debug(f"Received {len(teams_data)} teams from API")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching teams for league {league_id}: {e}")
            raise ExternalAPIErrorException()
        except Exception as e:
            logger.error(f"Unexpected error fetching teams for league {league_id}: {e}")
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            for team_response in teams_data:
                try:
                    team_data = team_response.get("team", {})
                    if not team_data:
                        logger.warning(f"Team data is missing in response: {team_response}")
                        continue

                    stmt = select(Team).where(Team.id == team_data["id"])
                    result = await session.execute(stmt)
                    existing_team = result.scalar_one_or_none()
                    if existing_team:
                        logger.debug(
                            f"Team {team_data['id']} already exists, skipping..."
                        )
                        continue

                    team = cls.model(
                        id=team_data["id"],
                        name=team_data["name"],
                        logo=team_data.get("logo"),
                        league_id=league_id,
                    )
                    session.add(team)
                    logger.debug(
                        f"Added team: {team_data['name']} (ID: {team_data['id']})"
                    )
                except KeyError as e:
                    logger.error(f"Missing key in team data: {e}")
                    await session.rollback()
                    raise FailedOperationException(
                        msg=f"Missing key in team data: {e}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing team {team_data.get('id', 'unknown')}: {e}"
                    )
                    await session.rollback()
                    raise FailedOperationException(
                        msg=f"Error processing team: {e}"
                    )

            try:
                await session.commit()
                logger.debug("Teams committed to DB successfully")
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Failed to commit teams for league {league_id}: {e}"
                )
                raise FailedOperationException(msg=f"Failed to commit teams: {e}")

    @classmethod
    async def translate_all_teams_names(cls):
        """Переводит названия всех команд на русский и сохраняет в name_rus"""
        translator = GoogleTranslator(source='auto', target='ru')
        
        async with async_session_maker() as session:
            # Получаем все команды
            stmt = select(Team)
            result = await session.execute(stmt)
            teams = result.scalars().all()
            
            logger.info(f"Found {len(teams)} teams to translate")
            
            translated_count = 0
            
            for team in teams:
                try:
                    # Переводим название команды
                    translated_name = translator.translate(team.name)
                    team.name_rus = translated_name
                    translated_count += 1
                    
                    if translated_count % 10 == 0:
                        logger.info(f"Translated {translated_count}/{len(teams)} teams")
                except Exception as e:
                    logger.error(f"Failed to translate team {team.id} ({team.name}): {e}")
                    continue
            
            await session.commit()
            logger.info(f"Translation completed: {translated_count} teams translated")
            return {"translated": translated_count, "total": len(teams)}

    @classmethod
    async def translate_team_name_by_id(cls, team_id: int):
        """Переводит название конкретной команды на русский по её ID"""
        translator = GoogleTranslator(source='auto', target='ru')
        
        async with async_session_maker() as session:
            stmt = select(Team).where(Team.id == team_id)
            result = await session.execute(stmt)
            team = result.scalar_one_or_none()
            
            if not team:
                from app.utils.exceptions import ResourceNotFoundException
                raise ResourceNotFoundException(detail=f"Team with id {team_id} not found")
            
            try:
                translated_name = translator.translate(team.name)
                team.name_rus = translated_name
                await session.commit()
                
                logger.info(f"Translated team {team_id}: {team.name} -> {translated_name}")
                return {
                    "team_id": team_id,
                    "original_name": team.name,
                    "translated_name": translated_name
                }
            except Exception as e:
                logger.error(f"Failed to translate team {team_id} ({team.name}): {e}")
                await session.rollback()
                raise FailedOperationException(msg=f"Failed to translate team name: {e}")
