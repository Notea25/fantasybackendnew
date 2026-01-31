from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class SquadReadSchema(BaseModel):
    """Squad metadata only - state moved to SquadTour"""
    id: int
    name: str
    user_id: int
    username: str
    league_id: int
    fav_team_id: int

    model_config = ConfigDict(from_attributes=True)


class SquadCreateSchema(BaseModel):
    name: str
    league_id: int
    fav_team_id: int
    captain_id: int
    vice_captain_id: int
    main_player_ids: list[int]
    bench_player_ids: list[int]


class SquadUpdatePlayersSchema(BaseModel):
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None
    # Для обновления/замены игроков поля могут быть частичными,
    # поэтому делаем списки опциональными.
    main_player_ids: Optional[list[int]] = None
    bench_player_ids: Optional[list[int]] = None




class SquadUpdateResponseSchema(BaseModel):
    status: str
    message: str
    squad: SquadReadSchema




class SquadRenameSchema(BaseModel):
    id: int
    name: str
    user_id: int
    league_id: int
    fav_team_id: int

    model_config = ConfigDict(from_attributes=True)




