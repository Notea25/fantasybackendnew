from pydantic import BaseModel, field_validator

class PlayerStatsCreateSchema(BaseModel):
    player_id: int
    league_id: int
    team_id: int
    season: int
    appearances: int | None = None
    lineups: int | None = None
    minutes_played: int | None = None
    position: str | None = None
    goals_total: int | None = None
    assists: int | None = None
    yellow_cards: int | None = None
    yellow_red_cards: int | None = None
    red_cards: int | None = None
    penalty_scored: int | None = None
    penalty_missed: int | None = None
    penalty_saved: int | None = None
    points: int | None = None

    @field_validator('position', mode='before')
    def set_default_position(cls, value):
        return value if value else "Unknown"

    @field_validator('minutes_played', 'appearances', 'lineups', 'goals_total', 'assists',
                     'yellow_cards', 'yellow_red_cards', 'red_cards', 'penalty_scored',
                     'penalty_missed', 'penalty_saved', mode='before')
    def set_default_zero(cls, value):
        return value if value is not None else 0

class PlayerStats(BaseModel):
    id: int
    player_id: int
    league_id: int
    team_id: int
    season: int
    appearances: int | None = None
    lineups: int | None = None
    minutes_played: int | None = None
    position: str | None = None
    goals_total: int | None = None
    assists: int | None = None
    yellow_cards: int | None = None
    yellow_red_cards: int | None = None
    red_cards: int | None = None
    penalty_scored: int | None = None
    penalty_missed: int | None = None
    penalty_saved: int | None = None
    points: int | None = None
    player_name: str | None = None
    league_name: str | None = None
    team_name: str | None = None

    class Config:
        from_attributes = True
