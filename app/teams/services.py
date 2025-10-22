from app.base_service import BaseService
from app.teams.models import Team


class TeamService(BaseService):
    model = Team
