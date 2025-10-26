from app.base_service import BaseService
from app.teams.models import Team


class SquadService(BaseService):
    model = Team
