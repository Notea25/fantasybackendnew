from app.base_service import BaseService
from app.leagues.models import League


class LeagueService(BaseService):
    model = League
