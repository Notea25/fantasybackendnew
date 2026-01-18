from pydantic import BaseModel, field_validator

class PlayerMatchStatsCreateSchema(BaseModel):
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

    @field_validator('position', mode='before')
    def set_default_position(cls, value):
        return value if value else "Unknown"

    @field_validator('minutes_played', 'goals_total', 'assists', 'yellow_cards', 'red_cards', mode='before')
    def set_default_zero(cls, value):
        return value if value is not None else 0

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