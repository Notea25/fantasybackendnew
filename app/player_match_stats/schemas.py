from pydantic import BaseModel

class PlayerMatchStats(BaseModel):
    id: int
    player_id: int
    match_id: int
    league_id: int
    team_id: int
    position: str
    minutes_played: int
    is_substitute: bool
    yellow_cards: int
    yellow_red_cards: int
    red_cards: int
    goals_total: int
    assists: int
    goals_conceded: int
    saves: int
    penalty_saved: int
    penalty_missed: int
    points: float

    class Config:
        from_attributes = True

class PlayerTotalStats(BaseModel):
    player_name: str
    position: str
    league_name: str
    team_name: str
    total_minutes_played: int
    total_matches: int
    total_yellow_cards: int
    total_yellow_red_cards: int
    total_red_cards: int
    total_goals: int
    total_assists: int
    total_goals_conceded: int
    total_saves: int
    total_penalty_saved: int
    total_penalty_missed: int
    total_points: float
    clean_sheets: int

    class Config:
        from_attributes = True