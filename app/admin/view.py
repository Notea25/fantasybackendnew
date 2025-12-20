from sqladmin import ModelView
from sqlalchemy.orm import selectinload

from app.users.models import User
from app.leagues.models import League
from app.matches.models import Match
from app.players.models import Player
from app.squads.models import Squad
from app.teams.models import Team
from app.player_stats.models import PlayerStats
from app.tours.models import Tour

class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.photo_url,
        User.emblem_url,
    ]
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
        Match.home_team_penalties,  # Исправлено название атрибута
        Match.away_team_penalties,
    ]

    column_labels = {
        'home_team': 'Home Team',
        'away_team': 'Away Team',
        'home_team_penalties': 'Home Team Penalties',
        'away_team_penalties': 'Away Team Penalties',
    }

    def format(self, attr, value):
        if attr in ('home_team', 'away_team') and value is not None:
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
    name = "Player"
    name_plural = "Players"
    icon = "fa-solid fa-person-running"

class SquadAdmin(ModelView, model=Squad):
    column_list = [
        Squad.id,
        Squad.name,
        Squad.user_id,
        Squad.budget,
        Squad.replacements,
        Squad.league_id,
    ]
    name = "Squad"
    name_plural = "Squads"
    icon = "fa-solid fa-people-group"

class TeamAdmin(ModelView, model=Team):
    column_list = [
        Team.id,
        Team.name,
        Team.league_id,
    ]
    name = "Team"
    name_plural = "Teams"
    icon = "fa-solid fa-people-line"

class PlayerStatsAdmin(ModelView, model=PlayerStats):
    column_list = [
        PlayerStats.id,
        PlayerStats.player_id,
        PlayerStats.league_id,
        PlayerStats.team_id,
        PlayerStats.season,
        PlayerStats.appearances,
        PlayerStats.lineups,
        PlayerStats.minutes_played,
        PlayerStats.position,
        PlayerStats.goals_total,
        PlayerStats.assists,
        PlayerStats.yellow_cards,
        PlayerStats.yellow_red_cards,
        PlayerStats.red_cards,
        PlayerStats.points,
    ]
    name = "Player Stats"
    name_plural = "Player Stats"
    icon = "fa-solid fa-chart-simple"


class TourAdmin(ModelView, model=Tour):
    column_list = [
        Tour.id,
        Tour.number,
        Tour.league_id,
        Tour.matches,
    ]

    column_labels = {
        'matches': 'Matches',
    }

    name = "Tour"
    name_plural = "Tours"
    icon = "fa-solid fa-calendar"