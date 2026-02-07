import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import exc, or_, select
from sqlalchemy.orm import selectinload

from app.utils.timezone import now_msk

from app.database import async_session_maker
from app.matches.models import Match
from app.matches.schemas import MatchCreateSchema
from app.utils.base_service import BaseService
from app.utils.exceptions import (
    ExternalAPIErrorException,
    FailedOperationException,
)
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

    # @classmethod
    # async def add_matches_for_league(cls, league_id: int):
    #     try:
    #         logger.debug(f"Fetching matches for league {league_id} from external API")
    #         matches_data = await external_api.fetch_matches(league_id)
    #         logger.debug(f"Matches data received: {len(matches_data)} matches")
    #     except httpx.HTTPStatusError as e:
    #         logger.error(f"HTTP error fetching matches for league {league_id}: {e}")
    #         raise ExternalAPIErrorException()
    #     except ValueError as e:
    #         logger.error(f"No matches found for league {league_id}: {e}")
    #         raise ExternalAPIErrorException(msg=str(e))
    #     except Exception as e:
    #         logger.error(f"Unexpected error fetching matches for league {league_id}: {e}")
    #         raise ExternalAPIErrorException()
    #
    #     async with async_session_maker() as session:
    #         for match_data in matches_data:
    #             try:
    #                 fixture = match_data.get("fixture", {})
    #                 teams = match_data.get("teams", {})
    #                 goals = match_data.get("goals", {})
    #                 score = match_data.get("score", {})
    #                 if not fixture or not teams or not goals:
    #                     logger.warning(f"Missing required data in match: {match_data}")
    #                     continue
    #
    #                 match_schema = MatchCreateSchema(
    #                     id=fixture.get("id"),
    #                     date=datetime.fromisoformat(fixture["date"].replace('Z', '+00:00')),
    #                     status=fixture.get("status", {}).get("long", "Not Started"),
    #                     duration=fixture.get("status", {}).get("elapsed"),
    #                     league_id=league_id,
    #                     home_team_id=teams.get("home", {}).get("id"),
    #                     away_team_id=teams.get("away", {}).get("id"),
    #                     home_team_score=goals.get("home"),
    #                     away_team_score=goals.get("away"),
    #                     home_team_penalties=score.get("penalty", {}).get("home") if score.get("penalty") else None,
    #                     away_team_penalties=score.get("penalty", {}).get("away") if score.get("penalty") else None
    #                 )
    #
    #                 match_dict = match_schema.model_dump(exclude_none=True)
    #
    #                 stmt = select(cls.model).where(cls.model.id == match_dict["id"])
    #                 result = await session.execute(stmt)
    #                 existing_match = result.scalar_one_or_none()
    #
    #                 if not existing_match:
    #                     match = cls.model(**match_dict)
    #                     session.add(match)
    #                     logger.debug(f"Added match {match.id} to session")
    #                 else:
    #                     logger.debug(f"Match {match_dict['id']} already exists, skipping")
    #             except KeyError as e:
    #                 logger.error(f"Missing key in match data: {e}")
    #                 await session.rollback()
    #                 raise FailedOperationException(msg=f"Missing key in match data: {e}")
    #             except Exception as e:
    #                 logger.error(f"Error processing match: {e}")
    #                 await session.rollback()
    #                 raise FailedOperationException(msg=f"Error processing match: {e}")
    #
    #         try:
    #             await session.commit()
    #             logger.info(f"Successfully committed matches for league {league_id}")
    #         except exc.SQLAlchemyError as e:
    #             await session.rollback()
    #             logger.error(f"Failed to commit matches for league {league_id}: {e}")
    #             raise FailedOperationException(msg=f"Failed to commit matches: {e}")

    @classmethod
    async def find_filtered(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def finalize_match(cls, match_id: int) -> dict:
        """Finalize match and add points to all SquadTours.
        
        Full implementation with captains and boosts:
        1. Marks match as finished (is_finished=True, finished_at=now)
        2. Gets all PlayerMatchStats for this match
        3. For each SquadTour in this tour:
           - For each player in main_players (or bench_players if bench_boost):
             * Get player's points from PlayerMatchStats
             * Apply multipliers:
               - Captain: × 2 (or × 3 if triple_captain)
               - Vice-captain: × 2 if captain got 0 points
             * Add to squad_tour.points
        
        Args:
            match_id: ID of match to finalize
        
        Returns:
            dict with counts of updated SquadTours and total points added
        """
        from app.player_match_stats.models import PlayerMatchStats
        from app.squad_tours.models import SquadTour, squad_tour_players, squad_tour_bench_players
        
        async with async_session_maker() as session:
            # 1. Get match and validate
            match = await session.execute(
                select(Match).where(Match.id == match_id)
            )
            match = match.scalars().first()
            
            if not match:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match {match_id} not found"
                )
            
            if match.is_finished:
                raise HTTPException(
                    status_code=400,
                    detail=f"Match {match_id} is already finished"
                )
            
            if not match.tour_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Match {match_id} has no tour_id assigned"
                )
            
            # 2. Mark match as finished
            match.is_finished = True
            match.finished_at = now_msk()
            
            # 3. Get all PlayerMatchStats for this match as dict
            player_stats_result = await session.execute(
                select(PlayerMatchStats)
                .where(PlayerMatchStats.match_id == match_id)
            )
            player_stats_list = player_stats_result.scalars().all()
            player_points = {ps.player_id: (ps.points or 0) for ps in player_stats_list}
            
            if not player_points:
                logger.warning(f"No PlayerMatchStats found for match {match_id}")
                await session.commit()
                return {
                    "match_id": match_id,
                    "updated_squad_tours": 0,
                    "total_points_added": 0,
                }
            
            # 4. Get all SquadTours for this tour with players loaded
            squad_tours_stmt = (
                select(SquadTour)
                .where(SquadTour.tour_id == match.tour_id)
                .options(
                    selectinload(SquadTour.main_players),
                    selectinload(SquadTour.bench_players)
                )
            )
            result = await session.execute(squad_tours_stmt)
            squad_tours = result.scalars().all()
            
            updated_squad_tours = set()
            total_points_added = 0
            
            # 5. For each SquadTour, calculate and add points
            for squad_tour in squad_tours:
                squad_points = 0
                captain_points = 0
                vice_captain_points = 0
                
                # Determine if bench boost is active
                is_bench_boost = squad_tour.used_boost == "bench_boost"
                is_triple_captain = squad_tour.used_boost == "triple_captain"
                
                # Get captain and vice-captain points
                if squad_tour.captain_id:
                    captain_points = player_points.get(squad_tour.captain_id, 0)
                if squad_tour.vice_captain_id:
                    vice_captain_points = player_points.get(squad_tour.vice_captain_id, 0)
                
                # Process main players
                for player in squad_tour.main_players:
                    player_id = player.id
                    base_points = player_points.get(player_id, 0)
                    
                    if base_points == 0:
                        continue
                    
                    # Apply multipliers
                    if player_id == squad_tour.captain_id:
                        if is_triple_captain:
                            points_to_add = base_points * 3
                            logger.info(
                                f"SquadTour {squad_tour.id}: Captain {player_id} × 3 (Triple Captain) = {points_to_add}"
                            )
                        else:
                            points_to_add = base_points * 2
                            logger.info(
                                f"SquadTour {squad_tour.id}: Captain {player_id} × 2 = {points_to_add}"
                            )
                    elif player_id == squad_tour.vice_captain_id and captain_points == 0:
                        points_to_add = base_points * 2
                        logger.info(
                            f"SquadTour {squad_tour.id}: Vice-captain {player_id} × 2 (captain got 0) = {points_to_add}"
                        )
                    else:
                        points_to_add = base_points
                    
                    squad_points += points_to_add
                
                # Process bench players if bench boost is active
                if is_bench_boost:
                    for player in squad_tour.bench_players:
                        player_id = player.id
                        base_points = player_points.get(player_id, 0)
                        
                        if base_points > 0:
                            squad_points += base_points
                            logger.info(
                                f"SquadTour {squad_tour.id}: Bench player {player_id} = {base_points} (Bench Boost)"
                            )
                
                # Add points to squad_tour if any points were earned
                if squad_points > 0:
                    squad_tour.points = (squad_tour.points or 0) + squad_points
                    updated_squad_tours.add(squad_tour.id)
                    total_points_added += squad_points
                    
                    logger.info(
                        f"SquadTour {squad_tour.id}: Added {squad_points} points from match {match_id}"
                    )
            
            await session.commit()
            
            logger.info(
                f"Match {match_id} finalized. "
                f"Updated {len(updated_squad_tours)} SquadTours, "
                f"added {total_points_added} total points"
            )
            
            return {
                "match_id": match_id,
                "updated_squad_tours": len(updated_squad_tours),
                "total_points_added": total_points_added,
            }
