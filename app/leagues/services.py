import logging
from datetime import timedelta
from typing import Optional, List

from sqlalchemy import func, select as sql_select
from sqlalchemy.orm import selectinload
from app.leagues.models import League
from app.database import async_session_maker
from app.squads.models import Squad
from app.tours.services import TourService
from app.utils.external_api import external_api
from app.utils.base_service import BaseService
from app.utils.exceptions import (
    ExternalAPIErrorException,
    AlreadyExistsException,
    FailedOperationException,
)
import httpx

logger = logging.getLogger(__name__)

class LeagueService(BaseService):
    model = League

    @classmethod
    async def add_league(cls, league_id: int) -> League:
        try:
            logger.debug(f"Fetching league {league_id} from external API")
            league_data = await external_api.fetch_league(league_id)
            logger.debug(f"League data received: {league_data}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching league {league_id}: {e}")
            raise ExternalAPIErrorException()
        except ValueError as e:
            logger.error(f"League {league_id} not found: {e}")
            raise ExternalAPIErrorException(msg=str(e))
        except Exception as e:
            logger.error(f"Unexpected error fetching league {league_id}: {e}")
            raise ExternalAPIErrorException()

        async with async_session_maker() as session:
            stmt = sql_select(League).where(League.id == league_id)
            result = await session.execute(stmt)
            existing_league = result.scalar_one_or_none()
            if existing_league:
                logger.warning(f"League {league_id} already exists")
                raise AlreadyExistsException()

            try:
                league_info = league_data["league"]
                country_info = league_data["country"]

                league = cls.model(
                    id=league_info["id"],
                    name=league_info["name"],
                    logo=league_info["logo"],
                    country=country_info["name"],
                )
                session.add(league)
                await session.commit()
                await session.refresh(league)
                logger.info(f"League {league_id} added successfully")
                return league
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add league {league_id}: {e}")
                raise FailedOperationException(msg=f"Failed to add league: {e}")

    @classmethod
    async def find_one_or_none_main_page(
            cls, league_id: int, user_id: int
    ) -> Optional[League]:
        async with async_session_maker() as session:
            league_query = sql_select(cls.model).where(cls.model.id == league_id)
            league_res = await session.execute(league_query)
            league = league_res.scalar_one_or_none()
            if not league:
                return None

            squads_count_query = sql_select(func.count()).select_from(Squad).where(Squad.league_id == league_id)
            squads_count_res = await session.execute(squads_count_query)
            league.all_squads_quantity = squads_count_res.scalar()

            user_squad_query = (
                sql_select(Squad)
                .where(Squad.league_id == league_id, Squad.user_id == user_id)
                .options(
                    selectinload(Squad.current_main_players),
                    selectinload(Squad.current_bench_players)
                )
            )
            user_squad_res = await session.execute(user_squad_query)
            user_squad = user_squad_res.unique().scalar_one_or_none()

            if user_squad:
                all_squads_query = (
                    sql_select(Squad)
                    .where(Squad.league_id == league_id)
                    .order_by(Squad.points.desc())
                    .options(
                        selectinload(Squad.current_main_players),
                        selectinload(Squad.current_bench_players)
                    )
                )
                all_squads_res = await session.execute(all_squads_query)
                all_squads = all_squads_res.unique().scalars().all()

                league.your_place = next(
                    (i + 1 for i, squad in enumerate(all_squads) if squad.id == user_squad.id),
                    None,
                )
            else:
                league.your_place = None

            league.deadline = await TourService.get_deadline_for_next_tour(league_id)

            return league