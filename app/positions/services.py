from app.base_service import BaseService
from app.clubs.models import Club


class ClubService(BaseService):
    model = Club