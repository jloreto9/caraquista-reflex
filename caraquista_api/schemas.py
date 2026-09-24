from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "republicaraquista-api"
    version: str = "1.0.0"

class TeamEloRating(BaseModel):
    team_id: int
    team_name: str
    abbreviation: str
    elo_rating: float
    rank: int

class MonteCarloTeamResult(BaseModel):
    team_id: int
    team_name: str
    abbreviation: str
    round_robin_pct: float = Field(description="Probabilidad de avanzar al Round Robin (0.0 a 1.0)")
    final_pct: float = Field(description="Probabilidad de avanzar a la Serie Final (0.0 a 1.0)")
    champion_pct: float = Field(description="Probabilidad de ser Campeón (0.0 a 1.0)")

class MonteCarloSimulationResponse(BaseModel):
    season: int
    iterations: int
    probabilities: List[MonteCarloTeamResult]

class WpaPlayRecord(BaseModel):
    inning: int
    half: str
    outs: int
    score_home: int
    score_away: int
    description: str
    home_win_exp: float
    leverage_index: float
    wpa_home: float

class WpaGameResponse(BaseModel):
    game_pk: int
    season: int
    home_team: str
    away_team: str
    home_final_score: int
    away_final_score: int
    total_plays: int
    plays: List[WpaPlayRecord]
