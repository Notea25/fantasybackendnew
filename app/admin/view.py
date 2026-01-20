import logging

from sqladmin import ModelView
from sqlalchemy import update, delete
from sqlalchemy.orm import joinedload

from app.boosts.models import Boost
from app.custom_leagues.club_league.models import ClubLeague
from app.custom_leagues.commercial_league.models import CommercialLeague, commercial_league_squads
from app.custom_leagues.user_league.models import UserLeague
from app.leagues.models import League
from app.matches.models import Match
from app.player_match_stats.models import PlayerMatchStats
from app.players.models import Player
from app.squads.models import Squad, SquadTour
from app.teams.models import Team
from app.tours.models import Tour, TourMatchAssociation
from app.users.models import User


logger = logging.getLogger(__name__)


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.photo_url,
        User.emblem_url,
    ]
    column_searchable_list = ["username"]
    can_delete = False
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class LeagueAdmin(ModelView, model=League):
    column_list = [
        League.id,
        League.name,
        League.logo,
        League.sport,
    ]
    column_searchable_list = ["name"]
    name = "League"
    name_plural = "Leagues"
    icon = "fa-solid fa-trophy"


class MatchAdmin(ModelView, model=Match):
    column_list = [
        Match.id,
        Match.date,
        Match.status,
        Match.duration,
        Match.league_id,
        Match.home_team,
        Match.away_team,
        Match.home_team_score,
        Match.away_team_score,
        Match.home_team_penalties,
        Match.away_team_penalties,
    ]
    column_searchable_list = ["home_team", "away_team"]
    column_labels = {
        "home_team": "Home Team",
        "away_team": "Away Team",
        "home_team_penalties": "Home Team Penalties",
        "away_team_penalties": "Away Team Penalties",
    }
    page_size = 20

    def format(self, attr, value):
        if attr in ("home_team", "away_team") and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Match"
    name_plural = "Matches"
    icon = "fa-solid fa-futbol"


class PlayerAdmin(ModelView, model=Player):
    column_list = [
        Player.id,
        Player.name,
        Player.age,
        Player.number,
        Player.position,
        Player.photo,
        Player.team_id,
        Player.market_value,
        Player.sport,
        Player.league_id,
    ]
    column_searchable_list = ["name", "position"]

    def format(self, attr, value):
        if attr == "team_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Player"
    name_plural = "Players"
    icon = "fa-solid fa-person-running"


class SquadAdmin(ModelView, model=Squad):
    column_list = [
        Squad.id,
        Squad.name,
        Squad.user_id,
        Squad.fav_team_id,
        Squad.budget,
        Squad.replacements,
        Squad.league_id,
        Squad.points,
        Squad.current_tour_id,
    ]

    form_columns = [
        Squad.name,
        Squad.user_id,
        Squad.fav_team_id,
        Squad.budget,
        Squad.replacements,
        Squad.league_id,
        Squad.points,
        Squad.current_tour_id,
    ]

    column_searchable_list = ["name"]
    column_labels = {
        "user_id": "User",
        "fav_team_id": "Favorite Team",
        "league_id": "League",
        "current_tour_id": "Current Tour",
    }
    column_details_exclude_list = [
        "current_main_players",
        "current_bench_players",
        "tour_history",
        "used_boosts",
    ]

    def format(self, attr, value):
        if attr == "user_id" and value is not None:
            return value.username
        if attr == "fav_team_id" and value is not None:
            return value.name
        if attr == "league_id" and value is not None:
            return value.name
        if attr == "current_tour_id" and value is not None:
            return f"Tour {value.number}"
        return super().format(attr, value)

    async def on_model_delete(self, model, request):
        # Перед удалением сквада чистим все ссылки на него, которые могут
        # нарушить ограничения внешних ключей.
        from app.database import async_session_maker

        async with async_session_maker() as session:
            # 1) winner_id в коммерческих лигах
            await session.execute(
                update(CommercialLeague)
                .where(CommercialLeague.winner_id == model.id)
                .values(winner_id=None)
            )
            # 2) связи сквада с коммерческими лигами
            await session.execute(
                delete(commercial_league_squads)
                .where(commercial_league_squads.c.squad_id == model.id)
            )
            # 3) все бусты этого сквада
            await session.execute(
                delete(Boost)
                .where(Boost.squad_id == model.id)
            )
            await session.commit()

        logger.debug(f"Удаление команды: {model.id}")
        return await super().on_model_delete(model, request)

    async def after_model_delete(self, model, request):
        logger.debug(f"После удаления команды: {model.id}")
        return await super().after_model_delete(model, request)

    name = "Squad"
    name_plural = "Squads"
    icon = "fa-solid fa-people-group"


class SquadTourAdmin(ModelView, model=SquadTour):
    column_list = [
        SquadTour.id,
        SquadTour.squad_id,
        SquadTour.tour_id,
        SquadTour.is_current,
        SquadTour.used_boost,
        SquadTour.points,
        SquadTour.points,
    ]
    column_labels = {
        "squad_id": "Squad",
        "tour_id": "Tour",
    }

    def format(self, attr, value):
        if attr == "squad_id" and value is not None:
            return value.name
        if attr == "tour_id" and value is not None:
            return f"Tour {value.number}"
        return super().format(attr, value)

    name = "Squad Tour"
    name_plural = "Squad Tours"
    icon = "fa-solid fa-calendar"


class BoostAdmin(ModelView, model=Boost):
    column_list = [
        Boost.id,
        Boost.squad_id,
        Boost.tour_id,
        Boost.type,
        Boost.used_at,
    ]
    column_labels = {
        "squad_id": "Squad",
        "tour_id": "Tour",
    }

    def format(self, attr, value):
        if attr == "squad_id" and value is not None:
            return value.name
        if attr == "tour_id" and value is not None:
            return f"Tour {value.number}"
        return super().format(attr, value)

    name = "Boost"
    name_plural = "Boosts"
    icon = "fa-solid fa-bolt"


class TeamAdmin(ModelView, model=Team):
    column_list = [
        Team.id,
        Team.name,
        Team.league_id,
    ]
    column_searchable_list = ["name"]

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Team"
    name_plural = "Teams"
    icon = "fa-solid fa-people-line"


class PlayerMatchStatsAdmin(ModelView, model=PlayerMatchStats):
    column_list = [
        PlayerMatchStats.id,
        PlayerMatchStats.player_id,
        PlayerMatchStats.match_id,
        PlayerMatchStats.team_id,
        PlayerMatchStats.league_id,
        PlayerMatchStats.position,
        PlayerMatchStats.goals_total,
        PlayerMatchStats.assists,
        PlayerMatchStats.yellow_cards,
        PlayerMatchStats.red_cards,
        PlayerMatchStats.minutes_played,
        PlayerMatchStats.points,
    ]
    column_searchable_list = ["player_id"]

    def format(self, attr, value):
        if attr == "player_id" and value is not None:
            return value.name
        if attr == "team_id" and value is not None:
            return value.name
        if attr == "league_id" and value is not None:
            return value.name
        if attr == "match_id" and value is not None:
            return f"Match {value.id}"
        return super().format(attr, value)

    name = "Player Match Stats"
    name_plural = "Player Match Stats"
    icon = "fa-solid fa-chart-simple"


class TourAdmin(ModelView, model=Tour):
    column_list = [
        Tour.id,
        Tour.number,
        Tour.league_id,
    ]
    column_searchable_list = ["number"]
    column_labels = {
        "matches": "Matches",
    }

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Tour"
    name_plural = "Tours"
    icon = "fa-solid fa-calendar"


class UserLeagueAdmin(ModelView, model=UserLeague):
    column_list = [
        UserLeague.id,
        UserLeague.name,
        UserLeague.league_id,
        UserLeague.creator_id,
        UserLeague.tours,
        UserLeague.squads,
    ]
    column_searchable_list = ["name"]
    column_labels = {
        "league_id": "League",
        "creator_id": "Creator",
        "tours": "Tours",
        "squads": "Squads",
    }

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        if attr == "creator_id" and value is not None:
            return value.username
        if attr == "tours" and value:
            return ", ".join(tour.name for tour in value)
        if attr == "squads" and value:
            return ", ".join(squad.name for squad in value)
        return super().format(attr, value)

    name = "User League"
    name_plural = "User Leagues"
    icon = "fa-solid fa-user"


class CommercialLeagueAdmin(ModelView, model=CommercialLeague):
    column_list = [
        CommercialLeague.id,
        CommercialLeague.name,
        CommercialLeague.league_id,
        CommercialLeague.prize,
        CommercialLeague.logo,
        CommercialLeague.winner_id,
        CommercialLeague.registration_start,
        CommercialLeague.registration_end,
    ]
    column_searchable_list = ["name"]
    column_labels = {
        "league_id": "League",
        "winner_id": "Winner Squad",
    }

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        if attr == "winner_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Commercial League"
    name_plural = "Commercial Leagues"
    icon = "fa-solid fa-money-bill"

    def get_query(self):
        return self.session.query(self.model)

    def get_one(self, ident):
        return (
            self.session.query(self.model)
            .filter(self.model.id == ident)
            .first()
        )



class ClubLeagueAdmin(ModelView, model=ClubLeague):
    column_list = [
        ClubLeague.id,
        ClubLeague.name,
        ClubLeague.league_id,
        ClubLeague.team_id,
    ]
    column_searchable_list = ["name"]
    column_labels = {
        "league_id": "League",
        "team_id": "Team",
    }

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        if attr == "team_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Club League"
    name_plural = "Club Leagues"
    icon = "fa-solid fa-trophy"

    def get_query(self):
        return self.session.query(self.model).options(
            joinedload(ClubLeague.league), joinedload(ClubLeague.team)
        )

    def get_one(self, ident):
        return self.get_query().filter(self.model.id == ident).one()


class TourMatchesAdmin(ModelView, model=TourMatchAssociation):
    name = "Tour Matches"
    name_plural = "Tour Matches"
    icon = "fa-solid fa-link"

    column_list = [
        TourMatchAssociation.tour_id,
        TourMatchAssociation.match_id,
    ]

    column_labels = {
        "tour_id": "Tour ID",
        "match_id": "Match ID",
    }

    def format(self, attr, value):
        if attr == "tour_id" and value is not None:
            return f"Tour {value}"
        if attr == "match_id" and value is not None:
            return f"Match {value}"
        return super().format(attr, value)