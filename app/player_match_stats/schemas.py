from pydantic import BaseModel, field_validator


class PlayerMatchStats(BaseModel):
    id: int
    player_id: int
    match_id: int
    team_id: int
    league_id: int
    position: str | None = None
    goals_total: int | None = None
    assists: int | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None
    minutes_played: int | None = None
    points: int | None = None
    player_name: str | None = None
    match_date: str | None = None
    team_name: str | None = None
    league_name: str | None = None

    class Config:
        from_attributes = True