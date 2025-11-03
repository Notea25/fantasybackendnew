from pydantic import BaseModel

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
    shots_total: int | None = None
    shots_on: int | None = None
    passes_total: int | None = None
    passes_key: int | None = None
    passes_accuracy: int | None = None
    tackles_total: int | None = None
    tackles_blocks: int | None = None
    tackles_interceptions: int | None = None
    duels_total: int | None = None
    duels_won: int | None = None
    dribbles_attempts: int | None = None
    dribbles_success: int | None = None
    dribbles_past: int | None = None
    fouls_drawn: int | None = None
    fouls_committed: int | None = None
    penalty_won: int | None = None
    penalty_committed: int | None = None
    penalty_scored: int | None = None
    penalty_missed: int | None = None
    penalty_saved: int | None = None
    substitutes_in: int | None = None
    substitutes_out: int | None = None
    substitutes_bench: int | None = None
    player_name: str | None = None
    league_name: str | None = None
    team_name: str | None = None

    class Config:
        from_attributes = True
