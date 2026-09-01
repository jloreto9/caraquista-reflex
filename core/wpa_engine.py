# core/wpa_engine.py
from core.cache import cache_ttl
"""
Motor Sabermétrico de Win Expectancy (WE), Win Probability Added (WPA) y Leverage Index (LI)
Basado en modelos estocásticos de 24 estados Base-Out (RE24) y distribuciones de carreras restantes.
"""
import math
import requests
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple, List, Optional, Any

TEAM_ID = 695  # Leones del Caracas

# Matriz Tango RE24 (Run Expectancy por estado Outs x Bases)
# Base states: 0: ---, 1: 1--, 2: -2-, 3: --3, 4: 12-, 5: 1-3, 6: -23, 7: 123
RE24: Dict[Tuple[int, int], float] = {
    # 0 outs
    (0, 0): 0.461, (0, 1): 0.831, (0, 2): 1.068, (0, 3): 1.350,
    (0, 4): 1.373, (0, 5): 1.640, (0, 6): 1.880, (0, 7): 2.192,
    # 1 out
    (1, 0): 0.243, (1, 1): 0.489, (1, 2): 0.644, (1, 3): 0.898,
    (1, 4): 0.884, (1, 5): 1.130, (1, 6): 1.330, (1, 7): 1.492,
    # 2 outs
    (2, 0): 0.095, (2, 1): 0.214, (2, 2): 0.305, (2, 3): 0.353,
    (2, 4): 0.413, (2, 5): 0.471, (2, 6): 0.550, (2, 7): 0.720,
}

AVG_RUNS_PER_INNING = 0.50
VAR_PER_INNING = 1.25


BASE_STATE_MAP = {
    (False, False, False): 0,  # ---
    (True, False, False): 1,   # 1--
    (False, True, False): 2,   # -2-
    (False, False, True): 3,   # --3
    (True, True, False): 4,    # 12-
    (True, False, True): 5,    # 1-3
    (False, True, True): 6,    # -23
    (True, True, True): 7,     # 123
}

BASE_STATE_DIAMONDS = {
    0: ("◇", "◇", "◇"),  # ---
    1: ("◇", "◇", "◆"),  # 1--
    2: ("◇", "◆", "◇"),  # -2-
    3: ("◆", "◇", "◇"),  # --3
    4: ("◇", "◆", "◆"),  # 12-
    5: ("◆", "◇", "◆"),  # 1-3
    6: ("◆", "◆", "◇"),  # -23
    7: ("◆", "◆", "◆"),  # 123
}


def encode_base_state(on_1b: bool, on_2b: bool, on_3b: bool) -> int:
    """Codifica el estado de bases en un entero de 0 a 7 alineado exactamente con la matriz RE24."""
    return BASE_STATE_MAP.get((bool(on_1b), bool(on_2b), bool(on_3b)), 0)


def format_base_state(base_state: int) -> str:
    """Retorna representación visual de las bases (ej: '◆ ◇ ◇') alineada con RE24."""
    b3, b2, b1 = BASE_STATE_DIAMONDS.get(base_state, ("◇", "◇", "◇"))
    return f"{b3} {b2} {b1}"


def calculate_win_expectancy(
    inning: int,
    is_bottom: bool,
    outs: int,
    base_state: int,
    home_score: int,
    away_score: int
) -> float:
    """
    Calcula la probabilidad de victoria (Win Expectancy) del equipo LOCAL (Home).
    Rango de salida: [0.001, 0.999] o 1.0 / 0.0 en finales.
    """
    outs = min(max(int(outs), 0), 2)
    base_state = min(max(int(base_state), 0), 7)
    
    # 1. Reglas de terminación de juego
    if inning >= 9 and is_bottom:
        if home_score > away_score:
            return 1.0  # Walk-off completado
            
    diff = home_score - away_score
    re_curr = RE24.get((outs, base_state), 0.25)
    
    if is_bottom:
        # Batea Home
        rem_home_inn = max(0, 9 - inning)
        exp_home_runs = home_score + re_curr + rem_home_inn * AVG_RUNS_PER_INNING
        rem_away_inn = max(0, 9 - inning)
        exp_away_runs = away_score + rem_away_inn * AVG_RUNS_PER_INNING
        
        # Inning 9 o extra para Home
        if inning >= 9:
            needed = away_score - home_score + 1
            if needed <= 0:
                return 1.0
            
            # Distribución Poisson para carreras en este medio inning
            lam = max(0.05, re_curr)
            if needed == 1:
                p_win_now = 1.0 - math.exp(-lam)
                # Si no anota en este inning (3er out), el juego sigue empatado hacia extrainnings
                return min(0.995, max(0.005, p_win_now + (1.0 - p_win_now) * 0.50))
            else:
                prob_home_walkoff = 1.0 - sum((lam**k * math.exp(-lam)) / math.factorial(k) for k in range(needed))
                p_tie = (lam**(needed-1) * math.exp(-lam)) / math.factorial(needed-1)
                return min(0.995, max(0.005, prob_home_walkoff + p_tie * 0.50))
    else:
        # Batea Away (Top)
        rem_away_inn = max(0, 9 - inning)
        exp_away_runs = away_score + re_curr + rem_away_inn * AVG_RUNS_PER_INNING
        rem_home_inn = max(0, 9 - inning + 1)
        exp_home_runs = home_score + rem_home_inn * AVG_RUNS_PER_INNING
        
        if inning >= 9:
            if diff < 0:
                # Away va ganando en el 9no
                needed = away_score - home_score
                lam = RE24[(0, 0)]
                prob_home_ties = (lam**needed * math.exp(-lam)) / math.factorial(needed)
                prob_home_wins = 1.0 - sum((lam**k * math.exp(-lam)) / math.factorial(k) for k in range(needed + 1))
                # Ajustar por probabilidad de que Away amplíe la ventaja en este turno
                away_extra = re_curr
                we_home = (prob_home_wins + prob_home_ties * 0.50) / (1.0 + away_extra * 0.4)
                return min(0.995, max(0.005, we_home))

    # Inning regular (1 a 8)
    exp_diff = exp_home_runs - exp_away_runs
    total_rem_half = (rem_home_inn if is_bottom else rem_home_inn) + rem_away_inn + (1 if not is_bottom else 0)
    var = max(0.5, total_rem_half * VAR_PER_INNING * 0.5)
    sigma = math.sqrt(var)
    
    z = exp_diff / (sigma * 1.15)
    we = 1.0 / (1.0 + math.exp(-1.702 * z))
    return min(0.999, max(0.001, we))


def calculate_leverage_index(
    inning: int,
    is_bottom: bool,
    outs: int,
    base_state: int,
    home_score: int,
    away_score: int
) -> float:
    """
    Calcula el Leverage Index (LI) de una situación.
    LI = 1.0 es el promedio de apalancamiento en MLB/LVBP.
    LI > 1.5: Alto apalancamiento (High Leverage).
    LI < 0.7: Bajo apalancamiento (Low Leverage).
    """
    base_we = calculate_win_expectancy(inning, is_bottom, outs, base_state, home_score, away_score)
    
    # Evaluar los swings potenciales en la jugada:
    # 1. Out (+1 out)
    if outs < 2:
        we_out = calculate_win_expectancy(inning, is_bottom, outs + 1, base_state, home_score, away_score)
    else:
        # Cambio de medio inning
        if not is_bottom:
            we_out = calculate_win_expectancy(inning, True, 0, 0, home_score, away_score)
        else:
            we_out = calculate_win_expectancy(inning + 1, False, 0, 0, home_score, away_score)
            
    # 2. Hit con carrera (anota 1 carrera)
    if not is_bottom:
        we_run = calculate_win_expectancy(inning, is_bottom, outs, min(7, base_state + 1), home_score, away_score + 1)
    else:
        we_run = calculate_win_expectancy(inning, is_bottom, outs, min(7, base_state + 1), home_score + 1, away_score)
        
    delta_swing = abs(we_run - we_out)
    avg_delta_swing = 0.095  # Swing promedio en el béisbol profesional
    
    li = delta_swing / avg_delta_swing
    return round(float(min(10.0, max(0.05, li))), 2)


def get_leverage_index(
    inning: int,
    half: str,
    outs: int,
    base_state: int,
    score_diff: int
) -> float:
    """
    Función de conveniencia para calcular Leverage Index con formato de half (top/bottom) y diferencial.
    score_diff = home_score - away_score
    """
    is_bottom = str(half).lower() in ["bottom", "bot", "b", "baja", "bottominning"]
    home_score = max(0, score_diff)
    away_score = max(0, -score_diff)
    return calculate_leverage_index(inning, is_bottom, outs, base_state, home_score, away_score)


@cache_ttl(ttl_seconds=600)
def process_game_wpa_advanced(game_pk: int) -> Tuple[pd.DataFrame, bool, Optional[str]]:
    """
    Procesa el feed live de un juego de la MLB Stats API y genera
    el dataset completo de WPA, LI, estados base-out y atribución precisa.
    """
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return pd.DataFrame(), False, f"Error HTTP {response.status_code}"
        feed = response.json()
    except Exception as e:
        return pd.DataFrame(), False, str(e)
        
    try:
        home_id = feed["gameData"]["teams"]["home"]["id"]
        leones_is_home = (home_id == TEAM_ID)
        home_name = feed["gameData"]["teams"]["home"]["name"]
        away_name = feed["gameData"]["teams"]["away"]["name"]
    except Exception as e:
        return pd.DataFrame(), False, f"Error en estructura de equipos: {str(e)}"
        
    all_plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
    if not all_plays:
        return pd.DataFrame(), leones_is_home, "No hay jugadas disponibles en el feed"
        
    wpa_rows = []
    
    # Estado inicial: Inning 1 Top, 0 outs, bases limpias, 0-0
    prev_home_we = calculate_win_expectancy(1, False, 0, 0, 0, 0)
    home_score = 0
    away_score = 0
    
    for idx, play in enumerate(all_plays):
        about = play.get("about", {})
        result = play.get("result", {})
        matchup = play.get("matchup", {})
        count = play.get("count", {})
        
        inning = about.get("inning", 1)
        half = about.get("halfInning", "top")
        is_bottom = (half == "bottom")
        
        # Outs antes de la jugada
        outs_before = count.get("outs", 0)
        
        # Corredores en base antes de la jugada
        on_1b_before = bool(matchup.get("postOnFirst") is not None)
        on_2b_before = bool(matchup.get("postOnSecond") is not None)
        on_3b_before = bool(matchup.get("postOnThird") is not None)
        base_state_before = encode_base_state(on_1b_before, on_2b_before, on_3b_before)
        
        # Carreras anotadas en esta jugada
        runs_in_play = sum(1 for runner in play.get("runners", [])
                           if runner.get("movement", {}).get("end") == "score")
        
        home_score_before = home_score
        away_score_before = away_score
        
        if is_bottom:
            home_score += runs_in_play
        else:
            away_score += runs_in_play
            
        home_score_after = home_score
        away_score_after = away_score
        
        # Outs y bases después de la jugada
        # Si la jugada causó 3 outs o final del inning
        is_last_play_of_half = (about.get("isComplete", False) and (idx + 1 < len(all_plays) and all_plays[idx+1].get("about", {}).get("halfInning") != half))
        
        # Calcular WE Home después de la jugada
        if idx == len(all_plays) - 1:
            # Última jugada del partido
            final_home_won = (home_score > away_score)
            we_home_after = 1.0 if final_home_won else 0.0
            li_play = calculate_leverage_index(inning, is_bottom, min(2, outs_before), base_state_before, home_score_before, away_score_before)
        else:
            next_play = all_plays[idx + 1]
            next_about = next_play.get("about", {})
            next_count = next_play.get("count", {})
            next_matchup = next_play.get("matchup", {})
            
            next_inn = next_about.get("inning", inning)
            next_is_bottom = (next_about.get("halfInning", half) == "bottom")
            next_outs = next_count.get("outs", 0)
            next_on_1b = bool(next_matchup.get("postOnFirst") is not None)
            next_on_2b = bool(next_matchup.get("postOnSecond") is not None)
            next_on_3b = bool(next_matchup.get("postOnThird") is not None)
            next_base_state = encode_base_state(next_on_1b, next_on_2b, next_on_3b)
            
            we_home_after = calculate_win_expectancy(
                next_inn, next_is_bottom, next_outs, next_base_state, home_score_after, away_score_after
            )
            li_play = calculate_leverage_index(
                inning, is_bottom, min(2, outs_before), base_state_before, home_score_before, away_score_before
            )

        # Delta de Win Expectancy desde la perspectiva de Leones
        if leones_is_home:
            we_leones_before = prev_home_we
            we_leones_after = we_home_after
        else:
            we_leones_before = 1.0 - prev_home_we
            we_leones_after = 1.0 - we_home_after
            
        wpa_leones = we_leones_after - we_leones_before
        
        # Perspectiva de marcadores
        leones_score_after = home_score_after if leones_is_home else away_score_after
        opp_score_after = away_score_after if leones_is_home else home_score_after
        
        # Identificar bateador y pitcher
        batter_info = matchup.get("batter", {})
        pitcher_info = matchup.get("pitcher", {})
        
        batter_id = batter_info.get("id")
        batter_name = batter_info.get("fullName", "Desconocido")
        pitcher_id = pitcher_info.get("id")
        pitcher_name = pitcher_info.get("fullName", "Desconocido")
        
        # Determinar si Leones está al bate o a la defensiva
        leones_batting = (is_bottom if leones_is_home else (not is_bottom))
        
        wpa_rows.append({
            "atbat_index": idx,
            "inning": inning,
            "halfInning": half,
            "is_bottom": is_bottom,
            "outs_before": outs_before,
            "base_state_before": base_state_before,
            "base_icons": format_base_state(base_state_before),
            "batter_id": batter_id,
            "batter": batter_name,
            "pitcher_id": pitcher_id,
            "pitcher": pitcher_name,
            "eventType": result.get("event", "Jugada"),
            "description": result.get("description", ""),
            "runs_in_play": runs_in_play,
            "home_score_after": home_score_after,
            "away_score_after": away_score_after,
            "leones_score_after": leones_score_after,
            "opp_score_after": opp_score_after,
            "score_str": f"{leones_score_after}-{opp_score_after}",
            "wp_before": we_leones_before,
            "wp_after": we_leones_after,
            "wpa": wpa_leones,
            "li": li_play,
            "wpa_li": round(wpa_leones / max(0.1, li_play), 4),
            "leones_batting": leones_batting
        })
        
        prev_home_we = we_home_after

    df_res = pd.DataFrame(wpa_rows)
    return df_res, leones_is_home, None


def calculate_player_game_wpa(df_wpa: pd.DataFrame, leones_player_ids: Optional[set] = None) -> pd.DataFrame:
    """
    Calcula WPA, WPA/LI y Clutch por jugador para un partido individual.
    """
    if df_wpa.empty:
        return pd.DataFrame()
        
    # 1. Bateo de Leones (cuando leones_batting == True)
    df_bat = df_wpa[df_wpa["leones_batting"] == True]
    bat_summary = df_bat.groupby(["batter_id", "batter"]).agg(
        wpa_bat=("wpa", "sum"),
        wpa_li_bat=("wpa_li", "sum"),
        li_avg_bat=("li", "mean"),
        pa_count=("atbat_index", "count")
    ).reset_index()
    bat_summary.rename(columns={"batter_id": "player_id", "batter": "player"}, inplace=True)
    
    # 2. Pitcheo de Leones (cuando leones_batting == False)
    df_pit = df_wpa[df_wpa["leones_batting"] == False]
    pit_summary = df_pit.groupby(["pitcher_id", "pitcher"]).agg(
        wpa_pit=("wpa", "sum"),
        wpa_li_pit=("wpa_li", "sum"),
        li_avg_pit=("li", "mean"),
        bf_count=("atbat_index", "count")
    ).reset_index()
    pit_summary.rename(columns={"pitcher_id": "player_id", "pitcher": "player"}, inplace=True)
    
    # Merge bateo y pitcheo
    merged = pd.merge(bat_summary, pit_summary, on=["player_id", "player"], how="outer").fillna(0)
    
    # Filtrar solo jugadores de Leones si se tiene la lista de IDs
    if leones_player_ids:
        merged = merged[merged["player_id"].isin(leones_player_ids)]
        
    merged["WPA_total"] = merged["wpa_bat"] + merged["wpa_pit"]
    merged["WPA_LI_total"] = merged["wpa_li_bat"] + merged["wpa_li_pit"]
    
    # Clutch = WPA - (WPA/LI)
    merged["Clutch"] = merged["WPA_total"] - merged["WPA_LI_total"]
    merged = merged.sort_values("WPA_total", ascending=False).reset_index(drop=True)
    
    return merged


def calculate_wpa_for_game(game_pk: int) -> dict:
    """Calcula el WPA para un juego individual y retorna el DataFrame y metadatos."""
    df_wpa, is_home, err = process_game_wpa_advanced(game_pk)
    return {
        "wpa_df": df_wpa,
        "is_home": is_home,
        "error": err
    }


@cache_ttl(ttl_seconds=600)
def get_season_wpa_leaderboard(season: int = 2025) -> Dict[str, Any]:
    """
    Procesa todos los juegos de la temporada para calcular los rankings acumulados
    de WPA, WPA/LI, Clutch y las mejores jugadas de todo el año.
    """
    from core.supabase_client import init_supabase
        
    supabase = init_supabase()
    games_response = supabase.table('games') \
        .select('*') \
        .eq('season', season) \
        .in_('status', ['Final', 'Completed', 'Completed Early', 'Game Over']) \
        .or_('home_team_id.eq.695,away_team_id.eq.695') \
        .eq('game_type', 'R') \
        .order('game_date', desc=False) \
        .execute()
        
    games = games_response.data or []
    if not games:
        return {}
        
    def fetch_and_process(g):
        df_w, is_h, err = process_game_wpa_advanced(g["id"])
        if not err and not df_w.empty:
            df_w["game_date"] = g["game_date"]
            df_w["game_id"] = g["id"]
            return df_w
        return None
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_and_process, games))
        
    all_plays_list = [r for r in results if r is not None and not r.empty]
    if not all_plays_list:
        return {}
        
    full_season_plays = pd.concat(all_plays_list, ignore_index=True)
    
    # 1. Bateadores de Leones en la temporada
    leo_bat_plays = full_season_plays[full_season_plays["leones_batting"] == True]
    batters_agg = leo_bat_plays.groupby(["batter_id", "batter"]).agg(
        JJ=("game_id", "nunique"),
        PA=("atbat_index", "count"),
        WPA=("wpa", "sum"),
        WPA_LI=("wpa_li", "sum"),
        LI_avg=("li", "mean"),
        High_LI_PA=("li", lambda s: (s >= 1.5).sum())
    ).reset_index()
    batters_agg["Clutch"] = batters_agg["WPA"] - batters_agg["WPA_LI"]
    batters_agg = batters_agg.sort_values("WPA", ascending=False).reset_index(drop=True)
    
    # 2. Lanzadores de Leones en la temporada
    leo_pit_plays = full_season_plays[full_season_plays["leones_batting"] == False]
    pitchers_agg = leo_pit_plays.groupby(["pitcher_id", "pitcher"]).agg(
        JJ=("game_id", "nunique"),
        BF=("atbat_index", "count"),
        WPA=("wpa", "sum"),
        WPA_LI=("wpa_li", "sum"),
        LI_avg=("li", "mean"),
        High_LI_BF=("li", lambda s: (s >= 1.5).sum())
    ).reset_index()
    pitchers_agg["Clutch"] = pitchers_agg["WPA"] - pitchers_agg["WPA_LI"]
    pitchers_agg = pitchers_agg.sort_values("WPA", ascending=False).reset_index(drop=True)
    
    # 3. Top 10 jugadas más decisivas de toda la temporada (Mayor WPA positivo y negativo)
    top_positive_plays = full_season_plays.nlargest(10, "wpa").copy()
    top_negative_plays = full_season_plays.nsmallest(10, "wpa").copy()
    
    return {
        "total_games": len(games),
        "total_plays": len(full_season_plays),
        "batters": batters_agg,
        "pitchers": pitchers_agg,
        "top_positive_plays": top_positive_plays,
        "top_negative_plays": top_negative_plays
    }
