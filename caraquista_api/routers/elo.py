from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from caraquista_api.schemas import MonteCarloSimulationResponse, MonteCarloTeamResult, TeamEloRating
from core.supabase_client import get_standings, init_supabase
from core.elo import simulate_monte_carlo_projections, BASE_ELO
from core.teams import LVBP_TEAMS, LVBP_ABBR, get_team_abbr

router = APIRouter(prefix="/api/v1/elo", tags=["ELO & Monte Carlo"])

@router.get("/ratings", response_model=List[TeamEloRating])
def get_elo_ratings(season: int = Query(2025, description="Año de inicio de la temporada")):
    """Retorna los ratings ELO de los 8 equipos LVBP basados en standings y diferencial."""
    try:
        standings_df = get_standings(season=season, phase="regular")
        if standings_df.empty:
            raise HTTPException(status_code=404, detail="No hay datos de standings para la temporada")

        ratings = []
        for _, row in standings_df.iterrows():
            tid = int(row["team_id"])
            pct = float(row.get("pct", 0.5))
            run_diff = float(row.get("run_diff", 0))
            elo = round(1500 + (pct - 0.5) * 400 + run_diff * 1.2, 1)

            ratings.append(
                TeamEloRating(
                    team_id=tid,
                    team_name=row["team_name"],
                    abbreviation=get_team_abbr(tid),
                    elo_rating=elo,
                    rank=0,
                )
            )

        ratings.sort(key=lambda x: x.elo_rating, reverse=True)
        for idx, r in enumerate(ratings):
            r.rank = idx + 1

        return ratings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando ELO: {str(e)}")

@router.get("/monte-carlo", response_model=MonteCarloSimulationResponse)
def get_monte_carlo_projections(
    season: int = Query(2025, description="Año de inicio de la temporada"),
    iterations: int = Query(5000, ge=100, le=10000, description="Número de iteraciones de simulación"),
):
    """
    Ejecuta simulaciones probabilísticas Monte Carlo (hasta 10,000 iteraciones)
    para proyectar probabilidades de avance a Round Robin, Gran Final y Campeonato.
    """
    try:
        standings_df = get_standings(season=season, phase="regular")
        if standings_df.empty:
            raise HTTPException(status_code=404, detail="No hay datos de standings para la temporada")

        # Construir diccionario ELO
        elo_dict: Dict[int, float] = {}
        for _, row in standings_df.iterrows():
            tid = int(row["team_id"])
            pct = float(row.get("pct", 0.5))
            run_diff = float(row.get("run_diff", 0))
            elo_dict[tid] = 1500.0 + (pct - 0.5) * 400.0 + run_diff * 1.2

        sim_results = simulate_monte_carlo_projections(
            standings_df=standings_df,
            elo_dict=elo_dict,
            n_simulations=iterations,
            simulate_from_scratch=False,
        )

        df_proj = sim_results["projections"]
        probabilities: List[MonteCarloTeamResult] = []

        for _, row in df_proj.iterrows():
            tid = int(row["team_id"])
            probabilities.append(
                MonteCarloTeamResult(
                    team_id=tid,
                    team_name=str(row["team_name"]),
                    abbreviation=get_team_abbr(tid),
                    round_robin_pct=round(float(row.get("rr_prob", 0.0)), 4),
                    final_pct=round(float(row.get("final_prob", 0.0)), 4),
                    champion_pct=round(float(row.get("champ_prob", 0.0)), 4),
                )
            )

        return MonteCarloSimulationResponse(
            season=season,
            iterations=iterations,
            probabilities=probabilities,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación Monte Carlo: {str(e)}")
