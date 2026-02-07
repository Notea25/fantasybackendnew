import logging
import csv
import io
from typing import Any

from sqladmin import ModelView, expose
from sqlalchemy import update, delete, select, inspect
from sqlalchemy.orm import joinedload
from wtforms import SelectField
from starlette.responses import Response
from starlette.requests import Request

from app.boosts.models import Boost
# ClubLeague removed
from app.custom_leagues.commercial_league.models import (
    CommercialLeague,
    commercial_league_squads,
)
from app.custom_leagues.user_league.models import (
    UserLeague,
    user_league_squads,
    user_league_tours,
)
from app.leagues.models import League
from app.matches.models import Match
from app.player_match_stats.models import PlayerMatchStats
from app.players.models import Player
from app.player_statuses.models import PlayerStatus
from app.squads.models import Squad
from app.squad_tours.models import (
    SquadTour,
    squad_tour_players,
    squad_tour_bench_players,
)
from app.teams.models import Team
from app.tours.models import Tour
from app.users.models import User


logger = logging.getLogger(__name__)


class BaseModelView(ModelView):
    """Base ModelView with fixes for common issues and import functionality."""
    
    can_import = True  # Enable import for all models by default
    def _stmt_by_identifier(self, identifier: str):
        """Override to fix URL parameter parsing issue.
        
        sqladmin has a bug where query string parameters like ?pks=379
        are included in the identifier, causing ValueError when parsing.
        This strips the query string before parsing.
        """
        # Strip query string if present
        if '?' in identifier:
            identifier = identifier.split('?')[0]
        return super()._stmt_by_identifier(identifier)
    
    @expose("/import", methods=["GET", "POST"])
    async def import_view(self, request: Request) -> Response:
        """Handle CSV import for the model."""
        from app.database import async_session_maker
        
        if request.method == "POST":
            form = await request.form()
            file = form.get("file")
            
            if not file or not hasattr(file, "file"):
                return Response(
                    content="No file uploaded",
                    status_code=400,
                    media_type="text/html"
                )
            
            try:
                # Read CSV file
                content = await file.read()
                csv_file = io.StringIO(content.decode('utf-8'))
                reader = csv.DictReader(csv_file)
                
                async with async_session_maker() as session:
                    imported_count = 0
                    updated_count = 0
                    errors = []
                    
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            # Get model's columns
                            mapper = inspect(self.model)
                            
                            # Prepare data for insert/update
                            data = {}
                            for column in mapper.columns:
                                col_name = column.name
                                if col_name in row:
                                    value = row[col_name]
                                    
                                    # Convert empty strings, 'None', 'NULL', etc. to None
                                    if value in ('', 'None', 'NULL', 'null', 'none'):
                                        value = None
                                    
                                    # Type conversion
                                    if value is not None:
                                        python_type = column.type.python_type
                                        if python_type == int:
                                            value = int(value)
                                        elif python_type == float:
                                            value = float(value)
                                        elif python_type == bool:
                                            value = value.lower() in ('true', '1', 'yes')
                                    
                                    data[col_name] = value
                            
                            # Check if record exists (by primary key)
                            pk_columns = [col.name for col in mapper.primary_key]
                            if all(pk in data for pk in pk_columns):
                                # Build filter for primary key
                                pk_filter = {pk: data[pk] for pk in pk_columns}
                                stmt = select(self.model).filter_by(**pk_filter)
                                result = await session.execute(stmt)
                                existing = result.scalar_one_or_none()
                                
                                if existing:
                                    # Update existing record
                                    for key, value in data.items():
                                        if key not in pk_columns:  # Don't update PK
                                            setattr(existing, key, value)
                                    updated_count += 1
                                else:
                                    # Insert new record
                                    new_obj = self.model(**data)
                                    session.add(new_obj)
                                    imported_count += 1
                            else:
                                # Insert new record without PK
                                new_obj = self.model(**data)
                                session.add(new_obj)
                                imported_count += 1
                        
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                            logger.error(f"Error importing row {row_num}: {e}")
                            continue
                    
                    if not errors:
                        await session.commit()
                        message = f"Successfully imported {imported_count} new records and updated {updated_count} existing records."
                        status = "success"
                    else:
                        await session.rollback()
                        message = f"Import failed with {len(errors)} errors: {'; '.join(errors[:5])}"
                        status = "error"
                
                # Redirect back to list view with message
                return Response(
                    content=f'<html><body><script>alert("{message}"); window.location.href="{request.url_for("admin:list", identity=self.identity)}";</script></body></html>',
                    media_type="text/html"
                )
            
            except Exception as e:
                logger.error(f"Import error: {e}")
                return Response(
                    content=f'<html><body><script>alert("Import failed: {str(e)}"); window.location.href="{request.url_for("admin:list", identity=self.identity)}";</script></body></html>',
                    media_type="text/html"
                )
        
        # GET request - show import form
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Import {self.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                .form-group {{ margin: 20px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input[type="file"] {{ width: 100%; padding: 10px; }}
                button {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; font-size: 16px; }}
                button:hover {{ background: #45a049; }}
                .info {{ background: #e7f3fe; padding: 15px; margin: 20px 0; border-left: 4px solid #2196F3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Import {self.name}</h1>
                <div class="info">
                    <p><strong>Instructions:</strong></p>
                    <ul>
                        <li>Export current data first to get the correct CSV format</li>
                        <li>Modify the CSV file with your changes</li>
                        <li>Upload the modified file here</li>
                        <li>Records with existing IDs will be updated</li>
                        <li>Records without IDs will be inserted as new</li>
                    </ul>
                </div>
                <form method="POST" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="file">Choose CSV file:</label>
                        <input type="file" id="file" name="file" accept=".csv" required>
                    </div>
                    <button type="submit">Import</button>
                    <a href="{request.url_for('admin:list', identity=self.identity)}" style="margin-left: 10px;">Cancel</a>
                </form>
            </div>
        </body>
        </html>
        """
        return Response(content=html, media_type="text/html")


class UserAdmin(BaseModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.photo_url,
        User.birth_date,
        User.registration_date,
    ]
    column_searchable_list = ["username"]
    # Allow deleting users from the admin panel.
    can_delete = True
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    async def on_model_delete(self, model, request):
        """Cascade-delete all data related to a user before removing it.

        When a user is deleted we want to remove:
        - all squads belonging to this user and everything bound to those squads
          (boosts, links to commercial leagues, user leagues, club leagues,
          winner references in commercial leagues),
        - all user leagues where this user is the creator, together with their
          tour and squad associations.
        """
        from app.database import async_session_maker

        user_id = model.id

        async with async_session_maker() as session:
            # 1) Find all squads of this user
            result = await session.execute(
                select(Squad.id).where(Squad.user_id == user_id)
            )
            squad_ids = [row[0] for row in result.fetchall()]

            # 1a) Find all squad_tours for these squads (history per tour)
            squad_tour_ids: list[int] = []
            if squad_ids:
                result = await session.execute(
                    select(SquadTour.id).where(SquadTour.squad_id.in_(squad_ids))
                )
                squad_tour_ids = [row[0] for row in result.fetchall()]

            if squad_ids:
                # 1b) winner_id in commercial leagues pointing to these squads -> NULL
                await session.execute(
                    update(CommercialLeague)
                    .where(CommercialLeague.winner_id.in_(squad_ids))
                    .values(winner_id=None)
                )

                # 1c) links in commercial/user/club league association tables
                await session.execute(
                    delete(commercial_league_squads)
                    .where(commercial_league_squads.c.squad_id.in_(squad_ids))
                )
                await session.execute(
                    delete(user_league_squads)
                    .where(user_league_squads.c.squad_id.in_(squad_ids))
                )
                # club_league_squads removed

                # 1d) squad <-> players associations removed in new architecture
                # Players are now stored in SquadTour only, cleaned up in step 1f

                # 1e) all boosts for these squads
                await session.execute(
                    delete(Boost).where(Boost.squad_id.in_(squad_ids))
                )

            # 1f) If there were squad_tours, clean up their player associations and
            #     the squad_tours themselves (defensive in case cascade is not
            #     configured at DB level).
            if squad_tour_ids:
                await session.execute(
                    delete(squad_tour_players)
                    .where(squad_tour_players.c.squad_tour_id.in_(squad_tour_ids))
                )
                await session.execute(
                    delete(squad_tour_bench_players)
                    .where(squad_tour_bench_players.c.squad_tour_id.in_(squad_tour_ids))
                )
                await session.execute(
                    delete(SquadTour).where(SquadTour.id.in_(squad_tour_ids))
                )

            # 1g) finally delete the squads themselves
            if squad_ids:
                await session.execute(
                    delete(Squad).where(Squad.id.in_(squad_ids))
                )

            # 2) Delete user leagues created by this user
            result = await session.execute(
                select(UserLeague.id).where(UserLeague.creator_id == user_id)
            )
            user_league_ids = [row[0] for row in result.fetchall()]

            if user_league_ids:
                # 2a) remove associations with tours and squads
                await session.execute(
                    delete(user_league_tours)
                    .where(user_league_tours.c.user_league_id.in_(user_league_ids))
                )
                await session.execute(
                    delete(user_league_squads)
                    .where(user_league_squads.c.user_league_id.in_(user_league_ids))
                )

                # 2b) delete the user leagues themselves
                await session.execute(
                    delete(UserLeague).where(UserLeague.id.in_(user_league_ids))
                )

            await session.commit()

        logger.debug(f"Удаление пользователя: {model.id}")
        return await super().on_model_delete(model, request)


class LeagueAdmin(BaseModelView, model=League):
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


class MatchAdmin(BaseModelView, model=Match):
    column_list = [
        Match.id,
        Match.date,
        Match.is_finished,
        Match.finished_at,
        Match.duration,
        Match.league_id,
        Match.tour_id,
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
        "tour_id": "Tour",
    }
    page_size = 20

    def format(self, attr, value):
        if attr in ("home_team", "away_team") and value is not None:
            return value.name
        if attr == "tour_id" and value is not None:
            return f"Tour {value.number}"
        return super().format(attr, value)

    name = "Match"
    name_plural = "Matches"
    icon = "fa-solid fa-futbol"


class PlayerAdmin(BaseModelView, model=Player):
    column_list = [
        Player.id,
        Player.name,
        Player.name_rus,
        Player.position,
        Player.photo,
        Player.team_id,
        Player.market_value,
        Player.sport,
        Player.league_id,
    ]
    form_columns = [
        Player.id,
        Player.name,
        Player.name_rus,
        Player.position,
        Player.photo,
        Player.team,
        Player.market_value,
        Player.sport,
        Player.league,
    ]
    form_include_pk = True
    form_ajax_refs = {
        "team": {
            "fields": ("name",),
            "order_by": Team.name,
        },
        "league": {
            "fields": ("name",),
            "order_by": League.name,
        },
    }
    column_searchable_list = ["name", "position"]

    def format(self, attr, value):
        if attr == "team_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Player"
    name_plural = "Players"
    icon = "fa-solid fa-person-running"


class SquadAdmin(BaseModelView, model=Squad):
    # NEW ARCHITECTURE: Squad contains only metadata
    # All state (budget, replacements, players, captain, points) is in SquadTour
    column_list = [
        Squad.id,
        Squad.name,
        Squad.user_id,
        Squad.fav_team_id,
        Squad.league_id,
    ]

    column_searchable_list = ["name"]
    column_labels = {
        "user_id": "User",
        "fav_team_id": "Favorite Team",
        "league_id": "League",
    }
    column_details_exclude_list = [
        "tour_snapshots",
        "used_boosts",
    ]
    
    # AJAX поиск для выбора user, fav_team, league
    form_ajax_refs = {
        "user": {
            "fields": ("username",),
            "order_by": User.username,
        },
        "fav_team": {
            "fields": ("name",),
            "order_by": Team.name,
        },
        "league": {
            "fields": ("name",),
            "order_by": League.name,
        },
    }

    def format(self, attr, value):
        if attr == "user_id" and value is not None:
            return value.username
        if attr == "fav_team_id" and value is not None:
            return value.name
        if attr == "league_id" and value is not None:
            return value.name
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


class SquadTourAdmin(BaseModelView, model=SquadTour):
    # NEW ARCHITECTURE: SquadTour contains all tour-specific state
    column_list = [
        SquadTour.id,
        SquadTour.squad_id,
        SquadTour.tour_id,
        SquadTour.budget,
        SquadTour.replacements,
        SquadTour.captain_id,
        SquadTour.vice_captain_id,
        SquadTour.used_boost,
        SquadTour.points,
        SquadTour.penalty_points,
        SquadTour.is_finalized,
    ]
    column_labels = {
        "squad_id": "Squad",
        "tour_id": "Tour",
        "captain_id": "Captain",
        "vice_captain_id": "Vice Captain",
        "penalty_points": "Penalty Points",
        "is_finalized": "Finalized",
    }
    
    # AJAX поиск для выбора squad, tour
    # captain_id и vice_captain_id — это просто int поля, не relationships
    form_ajax_refs = {
        "squad": {
            "fields": ("name",),
            "order_by": Squad.name,
        },
        "tour": {
            "fields": ("number",),
            "order_by": Tour.number,
        },
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


class BoostAdmin(BaseModelView, model=Boost):
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
    
    # AJAX поиск для выбора squad и tour
    form_ajax_refs = {
        "squad": {
            "fields": ("name",),
            "order_by": Squad.name,
        },
        "tour": {
            "fields": ("number",),
            "order_by": Tour.number,
        },
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


class TeamAdmin(BaseModelView, model=Team):
    column_list = [
        Team.id,
        Team.name,
        Team.name_rus,
        Team.league_id,
    ]
    form_columns = [Team.id, Team.name, Team.name_rus, Team.logo, Team.league]
    form_include_pk = True
    form_ajax_refs = {
        "league": {
            "fields": ("name",),
            "order_by": League.name,
        },
    }
    column_searchable_list = ["name"]
    can_delete = True

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        return super().format(attr, value)

    name = "Team"
    name_plural = "Teams"
    icon = "fa-solid fa-people-line"


class PlayerMatchStatsAdmin(BaseModelView, model=PlayerMatchStats):
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
    page_size = 50
    page_size_options = [25, 50, 100, 200]

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


class TourAdmin(BaseModelView, model=Tour):
    column_list = [
        Tour.id,
        Tour.number,
        Tour.league_id,
        Tour.deadline,
        Tour.is_started,
        Tour.is_finalized,
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


class UserLeagueAdmin(BaseModelView, model=UserLeague):
    async def _get_model_objects(
        self,
        session,
        stmt,
    ):
        """Override to add unique() for eager loaded relationships."""
        result = await session.execute(stmt)
        return result.unique().scalars().all()
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
    column_details_exclude_list = [
        "tours",
        "squads",
    ]
    
    # AJAX поиск для выбора связанных объектов
    form_ajax_refs = {
        "league": {
            "fields": ("name",),
            "order_by": League.name,
        },
        "creator": {
            "fields": ("username",),
            "order_by": User.username,
        },
        "tours": {
            "fields": ("number",),
            "order_by": Tour.number,
        },
        "squads": {
            "fields": ("name",),
            "order_by": Squad.name,
        },
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

    def get_query(self):
        return (
            self.session.query(self.model)
            .options(
                joinedload(UserLeague.league),
                joinedload(UserLeague.creator),
                joinedload(UserLeague.tours),
                joinedload(UserLeague.squads)
            )
            .execution_options(populate_existing=True)
        ).unique()

    def get_one(self, ident):
        return (
            self.get_query()
            .filter(self.model.id == ident)
        ).unique().one()


class CommercialLeagueAdmin(BaseModelView, model=CommercialLeague):
    async def _get_model_objects(
        self,
        session,
        stmt,
    ):
        """Override to add unique() for eager loaded relationships."""
        result = await session.execute(stmt)
        return result.unique().scalars().all()
    column_list = [
        CommercialLeague.id,
        CommercialLeague.name,
        CommercialLeague.league_id,
        CommercialLeague.prize,
        CommercialLeague.winner_id,
        CommercialLeague.registration_start,
        CommercialLeague.registration_end,
        CommercialLeague.tours,
        CommercialLeague.squads,
    ]
    column_searchable_list = ["name"]
    column_labels = {
        "league_id": "League",
        "winner_id": "Winner Squad",
        "tours": "Tours",
        "squads": "Squads",
        "registration_start": "Registration Start",
        "registration_end": "Registration End",
    }
    
    form_columns = [
        CommercialLeague.name,
        CommercialLeague.league_id,
        CommercialLeague.prize,
        CommercialLeague.logo,
        CommercialLeague.winner_id,
        CommercialLeague.registration_start,
        CommercialLeague.registration_end,
        CommercialLeague.tours,
        CommercialLeague.squads,
    ]
    
    # Используем AJAX для загрузки связанных объектов в формах
    form_ajax_refs = {
        "league": {
            "fields": ("name",),
            "order_by": League.name,
        },
        "winner": {
            "fields": ("name",),
            "order_by": Squad.name,
        },
        "tours": {
            "fields": ("number",),
            "order_by": Tour.number,
        },
        "squads": {
            "fields": ("name",),
            "order_by": Squad.name,
        },
    }

    def format(self, attr, value):
        if attr == "league_id" and value is not None:
            return value.name
        if attr == "winner_id" and value is not None:
            return value.name
        if attr == "tours" and value:
            return ", ".join(f"Tour {tour.number}" for tour in value)
        if attr == "squads" and value:
            return ", ".join(squad.name for squad in value)
        return super().format(attr, value)

    name = "Commercial League"
    name_plural = "Commercial Leagues"
    icon = "fa-solid fa-money-bill"

    def get_query(self):
        return (
            self.session.query(self.model)
            .options(
                joinedload(CommercialLeague.tours),
                joinedload(CommercialLeague.squads),
                joinedload(CommercialLeague.winner),
                joinedload(CommercialLeague.league)
            )
            .execution_options(populate_existing=True)
        ).unique()

    def get_one(self, ident):
        return (
            self.session.query(self.model)
            .filter(self.model.id == ident)
            .options(
                joinedload(CommercialLeague.tours),
                joinedload(CommercialLeague.squads),
                joinedload(CommercialLeague.winner),
                joinedload(CommercialLeague.league)
            )
            .execution_options(populate_existing=True)
        ).unique().first()



# ClubLeagueAdmin removed


# TourMatchesAdmin removed


class PlayerStatusAdmin(BaseModelView, model=PlayerStatus):
    column_list = [
        PlayerStatus.id,
        PlayerStatus.player_id,
        PlayerStatus.status_type,
        PlayerStatus.tour_start,
        PlayerStatus.tour_end,
    ]
    column_searchable_list = ["status_type"]
    column_sortable_list = [
        PlayerStatus.id,
        PlayerStatus.player_id,
        PlayerStatus.status_type,
        PlayerStatus.tour_start,
        PlayerStatus.tour_end,
    ]
    column_labels = {
        "player_id": "Player",
        "status_type": "Status Type",
        "tour_start": "Start Tour",
        "tour_end": "End Tour (leave empty for indefinite)",
    }
    column_default_sort = [(PlayerStatus.tour_start, True)]  # Sort by tour_start descending
    page_size = 50
    
    # AJAX search for player selection in forms
    form_ajax_refs = {
        "player": {
            "fields": ("name",),
            "order_by": Player.name,
        },
    }
    
    # Dropdown choices for status_type using form_overrides
    form_overrides = {
        "status_type": SelectField
    }
    
    form_args = {
        "status_type": {
            "choices": [
                ("red_card", "Red Card"),
                ("injured", "Injured"),
                ("left_league", "Left League"),
            ]
        }
    }

    def format(self, attr, value):
        if attr == "player_id" and value is not None:
            return f"{value.name} (ID: {value.id})"
        if attr == "status_type" and value is not None:
            status_labels = {
                "red_card": "Red Card",
                "injured": "Injured",
                "left_league": "Left League",
            }
            return status_labels.get(value, value)
        if attr == "tour_end" and value is None:
            return "Indefinite"
        return super().format(attr, value)

    name = "Player Status"
    name_plural = "Player Statuses"
    icon = "fa-solid fa-heart-pulse"
