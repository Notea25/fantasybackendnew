from app.base_service import BaseService
from app.players.models import Player


class PlayerService(BaseService):
    model = Player
