from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from app.leagues.services import LeagueService
from app.matches.services import MatchService
from app.player_match_stats.services import PlayerMatchStatsService
from app.players.services import PlayerService
from app.teams.services import TeamService

templates = Jinja2Templates(directory="templates")


class UtilsView(BaseView):
    @expose("/utils", methods=["GET", "POST"])
    async def utils(self, request: Request):
        if request.method == "POST":
            form = await request.form()
            action = form.get("action")
            league_id = form.get("league_id")
            match_id = form.get("match_id")

            if action == "add_league":
                return await self.add_league(request, league_id)
            elif action == "add_teams":
                return await self.add_teams(request, league_id)
            elif action == "add_players":
                return await self.add_players(request, league_id)
            elif action == "add_matches":
                return await self.add_matches(request, league_id)
            elif action == "add_all":
                return await self.add_all(request, league_id)
            elif action == "add_empty_stats_for_match":
                return await self.add_empty_stats_for_match(request, match_id)
            elif action == "add_empty_stats_for_all_matches":
                return await self.add_empty_stats_for_all_matches(request)
            elif action == "sync_all_players":
                return await self.sync_all_players(request)
            elif action == "sync_players_for_team":
                team_id = form.get("team_id")
                return await self.sync_players_for_team(request, team_id)
            elif action == "translate_all_players":
                return await self.translate_all_players(request)
            elif action == "translate_player_by_id":
                player_id = form.get("player_id")
                return await self.translate_player_by_id(request, player_id)
            elif action == "translate_all_teams":
                return await self.translate_all_teams(request)
            elif action == "translate_team_by_id":
                team_id = form.get("team_id_translate")
                return await self.translate_team_by_id(request, team_id)

        return templates.TemplateResponse("utils.html", {"request": request})

    async def add_league(self, request: Request, league_id: str):
        try:
            await LeagueService.add_league(int(league_id))
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def add_teams(self, request: Request, league_id: str):
        try:
            await TeamService.add_teams(int(league_id))
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def add_players(self, request: Request, league_id: str):
        try:
            await PlayerService.add_players_for_league(int(league_id))
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def add_matches(self, request: Request, league_id: str):
        try:
            await MatchService.add_matches_for_league(int(league_id))
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def add_all(self, request: Request, league_id: str):
        try:
            await LeagueService.add_league(int(league_id))
            await TeamService.add_teams(int(league_id))
            await PlayerService.add_players_for_league(int(league_id))
            await MatchService.add_matches_for_league(int(league_id))
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def add_empty_stats_for_match(self, request: Request, match_id: str):
        try:
            await PlayerMatchStatsService.add_empty_stats_for_match(
                int(match_id)
            )
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def add_empty_stats_for_all_matches(self, request: Request):
        try:
            await PlayerMatchStatsService.add_empty_stats_for_all_matches()
            return RedirectResponse(
                request.url_for("admin:utils"), status_code=302
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def sync_all_players(self, request: Request):
        try:
            result = await PlayerService.sync_all_players()
            success_message = f"Синхронизация завершена: добавлено {result['added']}, обновлено {result['updated']}"
            return templates.TemplateResponse(
                "utils.html", {"request": request, "success": success_message}
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def sync_players_for_team(self, request: Request, team_id: str):
        try:
            result = await PlayerService.sync_players_for_team(int(team_id))
            success_message = f"Синхронизация игроков команды '{result['team_name']}' завершена: добавлено {result['added']}, обновлено {result['updated']}"
            if result.get('message'):
                success_message += f". {result['message']}"
            return templates.TemplateResponse(
                "utils.html", {"request": request, "success": success_message}
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def translate_all_players(self, request: Request):
        try:
            result = await PlayerService.translate_all_players_names()
            success_message = f"Перевод имен всех игроков завершен: переведено {result['translated']} из {result['total']}"
            return templates.TemplateResponse(
                "utils.html", {"request": request, "success": success_message}
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def translate_player_by_id(self, request: Request, player_id: str):
        try:
            result = await PlayerService.translate_player_name_by_id(int(player_id))
            success_message = f"Имя игрока переведено: {result['original_name']} -> {result['translated_name']}"
            return templates.TemplateResponse(
                "utils.html", {"request": request, "success": success_message}
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def translate_all_teams(self, request: Request):
        try:
            result = await TeamService.translate_all_teams_names()
            success_message = f"Перевод названий всех команд завершен: переведено {result['translated']} из {result['total']}"
            return templates.TemplateResponse(
                "utils.html", {"request": request, "success": success_message}
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    async def translate_team_by_id(self, request: Request, team_id: str):
        try:
            result = await TeamService.translate_team_name_by_id(int(team_id))
            success_message = f"Название команды переведено: {result['original_name']} -> {result['translated_name']}"
            return templates.TemplateResponse(
                "utils.html", {"request": request, "success": success_message}
            )
        except Exception as e:
            return templates.TemplateResponse(
                "utils.html", {"request": request, "error": str(e)}
            )

    def is_visible(self, request: Request) -> bool:
        return True
