from core.cache import cache_ttl
# utils/bullpen_lineups.py
import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

LEONES_TEAM_ID = 695

def parse_game_bullpen_and_lineups(game_pk: int) -> dict:
    """Extrae datos de corredores heredados del bullpen y alineaciones del juego."""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    try:
        res = requests.get(url, timeout=20)
        if res.status_code != 200:
            return {"bullpen": [], "lineups": [], "order_stats": []}
        data = res.json()
        
        live = data.get("liveData", {})
        plays = live.get("plays", {}).get("allPlays", [])
        box = live.get("boxscore", {})
        game_date = data.get("gameData", {}).get("datetime", {}).get("originalDate", "")
        home_team = data.get("gameData", {}).get("teams", {}).get("home", {}).get("name", "Home")
        away_team = data.get("gameData", {}).get("teams", {}).get("away", {}).get("name", "Away")
        home_id = data.get("gameData", {}).get("teams", {}).get("home", {}).get("id")
        away_id = data.get("gameData", {}).get("teams", {}).get("away", {}).get("id")
        
        # 1. Extraer Lineup de Leones y resultado del juego
        # Determinar si Leones ganó
        linescore = live.get("linescore", {})
        teams_ls = linescore.get("teams", {})
        home_runs = teams_ls.get("home", {}).get("runs", 0)
        away_runs = teams_ls.get("away", {}).get("runs", 0)
        
        is_leones_home = (home_id == LEONES_TEAM_ID)
        leones_won = (home_runs > away_runs) if is_leones_home else (away_runs > home_runs)
        leones_score = home_runs if is_leones_home else away_runs
        opposing_score = away_runs if is_leones_home else home_runs
        opp_name = away_team if is_leones_home else home_team
        
        # Lineup inicial de Leones desde boxscore
        leones_side = "home" if is_leones_home else "away"
        leones_players = box.get("teams", {}).get(leones_side, {}).get("players", {})
        
        starting_lineup = []
        for p_id, p_info in leones_players.items():
            bat_order = p_info.get("battingOrder")
            if bat_order and str(bat_order).endswith("00"):  # Titulares tienen orden tipo "100", "200", ..., "900"
                order_num = int(str(bat_order)[0])
                starting_lineup.append({
                    "order": order_num,
                    "player_id": p_info.get("person", {}).get("id"),
                    "player_name": p_info.get("person", {}).get("fullName", "Desconocido"),
                    "position": p_info.get("position", {}).get("abbreviation", "")
                })
        starting_lineup.sort(key=lambda x: x["order"])
        
        lineup_str = " | ".join([f"{item['order']}. {item['player_name']} ({item['position']})" for item in starting_lineup])
        
        lineup_entry = {
            "game_pk": game_pk,
            "game_date": game_date,
            "home_team": home_team,
            "away_team": away_team,
            "opposing_team": opp_name,
            "is_home": is_leones_home,
            "leones_score": leones_score,
            "opposing_score": opposing_score,
            "score_str": f"{leones_score}-{opposing_score}",
            "full_score_str": f"Leones {leones_score} - {opposing_score} {opp_name}",
            "leones_won": leones_won,
            "lineup_summary": lineup_str,
            "starters": starting_lineup
        }
        
        # 2. Bullpen Inherited Runners Tracking
        # Rastreamos cada cambio de lanzador
        bullpen_entries = []
        current_pitcher_id = None
        current_half = None
        current_inning = None
        inherited_runners_tracked = []
        
        for p_idx, play in enumerate(plays):
            about = play.get("about", {})
            inning = about.get("inning", 1)
            half = about.get("halfInning", "top")
            
            # Solo nos interesan los lanzadores de Leones
            pitcher_team_id = home_id if half == "top" else away_id
            is_pitcher_leones = (pitcher_team_id == LEONES_TEAM_ID)
            
            matchup = play.get("matchup", {})
            pitcher = matchup.get("pitcher", {})
            pitcher_id = pitcher.get("id")
            pitcher_name = pitcher.get("fullName", "Desconocido")
            
            if (half != current_half) or (inning != current_inning):
                current_half = half
                current_inning = inning
                current_pitcher_id = pitcher_id
                inherited_runners_tracked = []
            elif pitcher_id != current_pitcher_id:
                # Cambio de lanzador a mitad de inning
                old_pitcher = current_pitcher_id
                current_pitcher_id = pitcher_id
                
                # Identificar cuántos corredores habían en base en el momento del cambio
                runners = play.get("runners", [])
                base_runners = [r for r in runners if r.get("movement", {}).get("originBase") in ["1B", "2B", "3B"]]
                ir_count = len(base_runners)
                
                if is_pitcher_leones and ir_count > 0:
                    # Rastrear si alguno de estos corredores anota en las jugadas siguientes de este medio inning
                    irs_count = 0
                    for follow_play in plays[p_idx:]:
                        if follow_play.get("about", {}).get("inning") != inning or follow_play.get("about", {}).get("halfInning") != half:
                            break
                        for r in follow_play.get("runners", []):
                            if r.get("movement", {}).get("isOut") == False and r.get("movement", {}).get("end") == "score":
                                if r.get("details", {}).get("runner", {}).get("id") in [br.get("details", {}).get("runner", {}).get("id") for br in base_runners]:
                                    irs_count += 1
                                    
                    bullpen_entries.append({
                        "game_pk": game_pk,
                        "game_date": game_date,
                        "opposing_team": away_team if is_leones_home else home_team,
                        "inning": inning,
                        "pitcher_id": pitcher_id,
                        "pitcher_name": pitcher_name,
                        "inherited_runners": ir_count,
                        "inherited_scored": min(irs_count, ir_count)
                    })
                    
        return {
            "bullpen": bullpen_entries,
            "lineup": lineup_entry
        }
    except Exception:
        return {"bullpen": [], "lineup": None}


@cache_ttl(ttl_seconds=600)
def fetch_season_bullpen_and_lineups(season: int, team_id: int = LEONES_TEAM_ID, cache_version: str = "v2_with_scores") -> tuple[pd.DataFrame, list]:
    """Descarga datos de bullpen y lineups de toda la temporada."""
    sched_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=17&leagueId=135&season={season}&teamId={team_id}"
    try:
        res = requests.get(sched_url, timeout=30)
        if res.status_code != 200:
            return pd.DataFrame(), []
        sched_data = res.json()
    except Exception:
        return pd.DataFrame(), []
        
    game_pks = []
    for d in sched_data.get("dates", []):
        for g in d.get("games", []):
            if g.get("status", {}).get("detailedState") in ["Final", "Completed Early", "Game Over"]:
                game_pks.append(g["gamePk"])
                
    if not game_pks:
        return pd.DataFrame(), []
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(parse_game_bullpen_and_lineups, game_pks))
        
    bullpen_all = [item for r in results for item in r.get("bullpen", [])]
    lineups_all = [r.get("lineup") for r in results if r.get("lineup")]
    
    df_bullpen = pd.DataFrame(bullpen_all) if bullpen_all else pd.DataFrame()
    return df_bullpen, lineups_all


def compute_bullpen_inherited_stats(df_bullpen: pd.DataFrame) -> pd.DataFrame:
    """Calcula la tabla de corredores heredados por lanzador del bullpen."""
    if df_bullpen.empty:
        return pd.DataFrame()
        
    agg = df_bullpen.groupby("pitcher_name").agg(
        Apariciones_Herencia=("inherited_runners", "count"),
        Total_IR=("inherited_runners", "sum"),
        Total_IRS=("inherited_scored", "sum")
    ).reset_index()
    
    agg["Tasa_IRS_pct"] = (agg["Total_IRS"] / agg["Total_IR"] * 100).round(1)
    agg = agg.sort_values(by=["Total_IR", "Tasa_IRS_pct"], ascending=[False, True])
    
    rename_cols = {
        "pitcher_name": "Lanzador Relevista",
        "Apariciones_Herencia": "Juegos con Herencia",
        "Total_IR": "Corredores Heredados (IR)",
        "Total_IRS": "Heredados Anotados (IRS)",
        "Tasa_IRS_pct": "% Anotados (IRS%)"
    }
    return agg.rename(columns=rename_cols)
