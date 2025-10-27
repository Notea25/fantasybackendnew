from sqladmin import ModelView
from app.users.models import User
from app.leagues.models import League
from app.matches.models import Match
from app.players.models import Player
from app.squads.models import Squad
from app.teams.models import Team
from app.player_match_stats.models import PlayerMatchStats

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
        Match.home_team_id,
        Match.away_team_id,
        Match.home_team_score,
        Match.away_team_score,
        Match.home_team_penalties,
        Match.away_team_penalties,
    ]
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

class PlayerMatchStatsAdmin(ModelView, model=PlayerMatchStats):
    column_list = [
        PlayerMatchStats.id,
        PlayerMatchStats.player_id,
        PlayerMatchStats.match_id,
        PlayerMatchStats.league_id,
        PlayerMatchStats.team_id,
        PlayerMatchStats.position,
        PlayerMatchStats.minutes_played,
        PlayerMatchStats.is_substitute,
        PlayerMatchStats.yellow_cards,
        PlayerMatchStats.yellow_red_cards,
        PlayerMatchStats.red_cards,
        PlayerMatchStats.goals_total,
        PlayerMatchStats.assists,
        PlayerMatchStats.goals_conceded,
        PlayerMatchStats.saves,
        PlayerMatchStats.penalty_saved,
        PlayerMatchStats.penalty_missed,
        PlayerMatchStats.points,
    ]
    name = "Player Match Stats"
    name_plural = "Player Match Stats"
    icon = "fa-solid fa-chart-simple"
