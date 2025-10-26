# from sqladmin import ModelView
#
# from app.player_match_stats.models import Club
# from app.leagues.models import Competition
# from app.matches.models import Match
# from app.players.models import Player
# from app.positions.models import Position
# from app.sport_types.models import SportType
# from app.teams.models import Team
# from app.users.models import User
#
#
# class UserAdmin(ModelView, model=User):
#     column_list = "__all__"
#     can_delete = False
#     name = "User"
#     name_plural = "Users"
#     icon = "fa-solid fa-user"
#
#
# class SportTypeAdmin(ModelView, model=SportType):
#     column_list = ["id", "name", "positions"]
#     name = "SportType"
#     name_plural = "SportTypes"
#     icon = "fa-solid fa-football"
#
#
# class ClubAdmin(ModelView, model=Club):
#     column_list = "__all__"
#     name = "Club"
#     name_plural = "Clubs"
#     icon = "fa-solid fa-people-group"
#
#
# class CompetitionAdmin(ModelView, model=Competition):
#     column_list = "__all__"
#     name = "Competition"
#     name_plural = "Competitions"
#     icon = "fa-solid fa-trophy"
#
#
# class MatchAdmin(ModelView, model=Match):
#     column_list = "__all__"
#     name = "Match"
#     name_plural = "Matches"
#     icon = "fa-solid fa-calendar-days"
#
#
# class PlayerAdmin(ModelView, model=Player):
#     column_list = "__all__"
#     name = "Player"
#     name_plural = "Players"
#     icon = "fa-solid fa-person-running"
#
#
# class PositionAdmin(ModelView, model=Position):
#     column_list = ["id", "name", "sport_type"]
#     name = "Position"
#     name_plural = "Positions"
#     icon = "fa-solid fa-location-dot"
#
#
# class TeamAdmin(ModelView, model=Team):
#     column_list = "__all__"
#     name = "Team"
#     name_plural = "Teams"
#     icon = "fa-solid fa-users"
