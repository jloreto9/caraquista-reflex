from fastapi import APIRouter, HTTPException, Path
from typing import List
from caraquista_api.schemas import WpaGameResponse, WpaPlayRecord
from core.wpa_engine import process_game_wpa_advanced

router = APIRouter(prefix="/api/v1/wpa", tags=["Win Expectancy & WPA"])

@router.get("/game/{game_pk}", response_model=WpaGameResponse)
def get_game_wpa(game_pk: int = Path(..., description="MLB Stats API game_pk")):
    """
    Retorna la curva de Win Expectancy jugada por jugada, apalancamiento (Leverage Index)
    y Win Probability Added (WPA) utilizando la matriz Tango RE24.
    """
    try:
        df, leones_is_home, error_msg = process_game_wpa_advanced(game_pk)
        if error_msg or df.empty:
            raise HTTPException(status_code=404, detail=error_msg or "No se encontraron jugadas para el partido")

        plays: List[WpaPlayRecord] = []
        for _, row in df.iterrows():
            plays.append(
                WpaPlayRecord(
                    inning=int(row.get("inning", 1)),
                    half=str(row.get("half", "top")),
                    outs=int(row.get("outs_before", 0)),
                    score_home=int(row.get("home_score", 0)),
                    score_away=int(row.get("away_score", 0)),
                    description=str(row.get("description", "")),
                    home_win_exp=round(float(row.get("home_win_exp_after", 0.5)), 4),
                    leverage_index=round(float(row.get("leverage_index", 1.0)), 2),
                    wpa_home=round(float(row.get("wpa_home", 0.0)), 4),
                )
            )

        home_final = int(df.iloc[-1]["home_score"]) if not df.empty else 0
        away_final = int(df.iloc[-1]["away_score"]) if not df.empty else 0

        return WpaGameResponse(
            game_pk=game_pk,
            season=2025,
            home_team=str(df.iloc[0].get("home_team", "Local")) if not df.empty else "Local",
            away_team=str(df.iloc[0].get("away_team", "Visitante")) if not df.empty else "Visitante",
            home_final_score=home_final,
            away_final_score=away_final,
            total_plays=len(plays),
            plays=plays,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando WPA del juego: {str(e)}")
