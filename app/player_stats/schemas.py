from pydantic import BaseModel

class PlayerStats(BaseModel):
    id: int
    player_id: int
    league_id: int
    team_id: int
    season: int
    appearances: int
    lineups: int
    minutes_played: int
    position: str
    goals_total: int
    assists: int
    yellow_cards: int
    yellow_red_cards: int
    red_cards: int
    player_name: str | None = None
    league_name: str | None = None
    team_name: str | None = None

    class Config:
        from_attributes = True
