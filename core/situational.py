from typing import Any, Dict, List, Optional, Tuple
from core.cache import cache_ttl
# utils/situational.py
import requests
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

LEONES_TEAM_ID = 695

def parse_game_plate_appearances(game_pk: int) -> list[dict]:
    """Extrae todas las apariciones al plato con contexto situacional exacto previo a la jugada."""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    try:
        res = requests.get(url, timeout=20)
        if res.status_code != 200:
            return []
        data = res.json()
        
        plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])
        game_date = data.get("gameData", {}).get("datetime", {}).get("originalDate", "")
        home_team = data.get("gameData", {}).get("teams", {}).get("home", {}).get("name", "Home")
        away_team = data.get("gameData", {}).get("teams", {}).get("away", {}).get("name", "Away")
        home_id = data.get("gameData", {}).get("teams", {}).get("home", {}).get("id")
        away_id = data.get("gameData", {}).get("teams", {}).get("away", {}).get("id")
        
        records = []
        
        # Rastrear el estado exacto de bases y outs a lo largo de cada medio inning
        curr_inn = None
        curr_half = None
        curr_runners = {"1B": False, "2B": False, "3B": False}
        curr_outs = 0
        
        for play in plays:
            about = play.get("about", {})
            inning = about.get("inning", 1)
            half = about.get("halfInning", "top")
            
            # Reiniciar estado en cada cambio de medio inning
            if (inning != curr_inn) or (half != curr_half):
                curr_inn = inning
                curr_half = half
                curr_runners = {"1B": False, "2B": False, "3B": False}
                curr_outs = 0
                
            # Outs antes de la jugada (primer lanzamiento del turno o estado acumulado del inning)
            outs_before = play.get("playEvents", [{}])[0].get("count", {}).get("outs", curr_outs) if play.get("playEvents") else curr_outs
            if not isinstance(outs_before, (int, float)):
                outs_before = curr_outs
            outs_before = int(outs_before)
            
            # Estado de corredores antes de la jugada
            runner_1b = bool(curr_runners["1B"])
            runner_2b = bool(curr_runners["2B"])
            runner_3b = bool(curr_runners["3B"])
            
            is_bases_empty = (not runner_1b and not runner_2b and not runner_3b)
            is_men_on = (runner_1b or runner_2b or runner_3b)
            is_risp = (runner_2b or runner_3b)
            is_bases_loaded = (runner_1b and runner_2b and runner_3b)
            is_2_outs = (outs_before == 2)
            is_2_outs_risp = (is_2_outs and is_risp)
            
            matchup = play.get("matchup", {})
            batter = matchup.get("batter", {})
            pitcher = matchup.get("pitcher", {})
            bat_side = matchup.get("batSide", {}).get("code", "R")
            pitch_hand = matchup.get("pitchHand", {}).get("code", "R")
            
            batter_team_id = away_id if half == "top" else home_id
            pitcher_team_id = home_id if half == "top" else away_id
            opposing_team_name = home_team if half == "top" else away_team
            
            result = play.get("result", {})
            event = result.get("event", "Out")
            rbi = int(result.get("rbi", 0))
            desc = result.get("description", "")
            
            # Segmento de entradas
            if inning <= 3:
                inning_bucket = "Inicios (1-3)"
            elif inning <= 6:
                inning_bucket = "Medio (4-6)"
            else:
                inning_bucket = "Finales/Clutch (7-9+)"
                
            # Clasificación del resultado del turno
            is_hit = event in ["Single", "Double", "Triple", "Home Run"]
            is_single = (event == "Single")
            is_double = (event == "Double")
            is_triple = (event == "Triple")
            is_hr = (event == "Home Run")
            is_walk = event in ["Walk", "Intent Walk"]
            is_strikeout = event in ["Strikeout", "Strikeout Looking"]
            is_sac_fly = event in ["Sac Fly", "Sac Fly Double Play"]
            is_sac_bunt = (event == "Sac Bunt")
            is_sac = (is_sac_fly or is_sac_bunt)
            is_hbp = (event == "Hit By Pitch")
            
            # Turno Oficial (AB) descuenta BB, HBP, Sacrificios e Interferencias
            is_ab = not (is_walk or is_hbp or is_sac or "Interference" in event)
            is_pa = True
            
            records.append({
                "game_pk": game_pk,
                "game_date": game_date,
                "home_team": home_team,
                "away_team": away_team,
                "inning": inning,
                "half": half,
                "inning_bucket": inning_bucket,
                "batter_id": batter.get("id"),
                "batter_name": batter.get("fullName", "Desconocido"),
                "batter_team_id": batter_team_id,
                "is_batter_leones": (batter_team_id == LEONES_TEAM_ID),
                "bat_side": bat_side,
                "pitcher_id": pitcher.get("id"),
                "pitcher_name": pitcher.get("fullName", "Desconocido"),
                "pitcher_team_id": pitcher_team_id,
                "is_pitcher_leones": (pitcher_team_id == LEONES_TEAM_ID),
                "opposing_team": opposing_team_name,
                "pitch_hand": pitch_hand,
                "event": event,
                "rbi": rbi,
                "description": desc,
                "outs": outs_before,
                "is_2_outs": is_2_outs,
                "runner_1b": runner_1b,
                "runner_2b": runner_2b,
                "runner_3b": runner_3b,
                "is_bases_empty": is_bases_empty,
                "is_men_on": is_men_on,
                "is_risp": is_risp,
                "is_bases_loaded": is_bases_loaded,
                "is_2_outs_risp": is_2_outs_risp,
                "is_pa": is_pa,
                "is_ab": is_ab,
                "is_hit": is_hit,
                "is_single": is_single,
                "is_double": is_double,
                "is_triple": is_triple,
                "is_hr": is_hr,
                "is_walk": is_walk,
                "is_strikeout": is_strikeout,
                "is_sac": is_sac,
                "is_sac_fly": is_sac_fly,
                "is_sac_bunt": is_sac_bunt,
                "is_hbp": is_hbp
            })
            
            # Actualizar estado de corredores y outs posteriores a la jugada
            curr_runners["1B"] = bool(matchup.get("postOnFirst"))
            curr_runners["2B"] = bool(matchup.get("postOnSecond"))
            curr_runners["3B"] = bool(matchup.get("postOnThird"))
            curr_outs = play.get("count", {}).get("outs", curr_outs)
            if not isinstance(curr_outs, int):
                curr_outs = outs_before
                
        return records
    except Exception:
        return []


@cache_ttl(ttl_seconds=600)
def fetch_season_situational_data(season: int, team_id: int = LEONES_TEAM_ID, cache_version: str = "v3_exact_state_tracking") -> pd.DataFrame:
    """Descarga todas las apariciones al plato de la temporada para análisis situacional."""
    sched_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=17&leagueId=135&season={season}&teamId={team_id}"
    try:
        res = requests.get(sched_url, timeout=30)
        if res.status_code != 200:
            return pd.DataFrame()
        sched_data = res.json()
    except Exception:
        return pd.DataFrame()
        
    game_pks = []
    for d in sched_data.get("dates", []):
        for g in d.get("games", []):
            if g.get("status", {}).get("detailedState") in ["Final", "Completed Early", "Game Over"]:
                game_pks.append(g["gamePk"])
                
    if not game_pks:
        return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(parse_game_plate_appearances, game_pks))
        
    all_records = [item for sublist in results for item in sublist]
    if not all_records:
        return pd.DataFrame()
        
    return pd.DataFrame(all_records)


def summarize_slash_line(df: pd.DataFrame) -> dict:
    """Calcula la línea estadística clásica (PA, AB, H, 2B, 3B, HR, BB, SO, RBI, AVG, OBP, SLG, OPS)."""
    if df.empty:
        return {
            "PA": 0, "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0,
            "BB": 0, "SO": 0, "RBI": 0, "AVG": ".000", "OBP": ".000", "SLG": ".000", "OPS": ".000"
        }
        
    pa = int(df["is_pa"].sum())
    ab = int(df["is_ab"].sum())
    h = int(df["is_hit"].sum())
    h2b = int(df["is_double"].sum())
    h3b = int(df["is_triple"].sum())
    hr = int(df["is_hr"].sum())
    h1b = h - (h2b + h3b + hr)
    bb = int(df["is_walk"].sum())
    so = int(df["is_strikeout"].sum())
    rbi = int(df["rbi"].sum())
    hbp = int(df["is_hbp"].sum())
    sac = int(df["is_sac"].sum())
    
    avg_num = (h / ab) if ab > 0 else 0.0
    obp_num = ((h + bb + hbp) / (ab + bb + hbp + sac)) if (ab + bb + hbp + sac) > 0 else 0.0
    tb = (h1b + 2 * h2b + 3 * h3b + 4 * hr)
    slg_num = (tb / ab) if ab > 0 else 0.0
    ops_num = obp_num + slg_num
    
    return {
        "PA": pa, "AB": ab, "H": h, "2B": h2b, "3B": h3b, "HR": hr,
        "BB": bb, "SO": so, "RBI": rbi,
        "AVG_num": avg_num, "OBP_num": obp_num, "SLG_num": slg_num, "OPS_num": ops_num,
        "AVG": f"{avg_num:.3f}".replace("0.", "."),
        "OBP": f"{obp_num:.3f}".replace("0.", "."),
        "SLG": f"{slg_num:.3f}".replace("0.", "."),
        "OPS": f"{ops_num:.3f}".replace("0.", ".")
    }


def compute_all_situational_splits(df_subject: pd.DataFrame) -> pd.DataFrame:
    """Calcula y compara los splits situacionales clave."""
    splits = [
        ("Total General", df_subject),
        ("Bases Limpias", df_subject[df_subject["is_bases_empty"] == True]),
        ("Hombres en Base", df_subject[df_subject["is_men_on"] == True]),
        ("Posición Anotadora (RISP)", df_subject[df_subject["is_risp"] == True]),
        ("RISP con 2 Outs (Clutch)", df_subject[df_subject["is_2_outs_risp"] == True]),
        ("Bases Llenas", df_subject[df_subject["is_bases_loaded"] == True]),
        ("Con 2 Outs (Cualquier base)", df_subject[df_subject["is_2_outs"] == True]),
        ("vs Lanzadores Derechos (RHP)", df_subject[df_subject["pitch_hand"] == "R"]),
        ("vs Lanzadores Zurdos (LHP)", df_subject[df_subject["pitch_hand"] == "L"]),
        ("Entradas Tempranas (1-3)", df_subject[df_subject["inning_bucket"] == "Inicios (1-3)"]),
        ("Entradas Medias (4-6)", df_subject[df_subject["inning_bucket"] == "Medio (4-6)"]),
        ("Entradas Tardías (7-9+)", df_subject[df_subject["inning_bucket"] == "Finales/Clutch (7-9+)"])
    ]
    
    rows = []
    for name, sub in splits:
        if not sub.empty:
            st_dict = summarize_slash_line(sub)
            st_dict["Situación"] = name
            rows.append(st_dict)
            
    if not rows:
        return pd.DataFrame()
        
    res_df = pd.DataFrame(rows)
    cols = ["Situación", "PA", "AB", "H", "2B", "3B", "HR", "BB", "SO", "RBI", "AVG", "OBP", "SLG", "OPS"]
    return res_df[cols]


def compute_bvp_summary(df_pas: pd.DataFrame, batter_id: int = None, pitcher_id: int = None) -> pd.DataFrame:
    """Calcula la tabla de enfrentamientos cara a cara BvP."""
    if batter_id:
        sub = df_pas[df_pas["batter_id"] == batter_id]
        group_col = "pitcher_name"
        label_col = "Lanzador Rival"
    elif pitcher_id:
        sub = df_pas[df_pas["pitcher_id"] == pitcher_id]
        group_col = "batter_name"
        label_col = "Bateador Rival"
    else:
        return pd.DataFrame()
        
    rows = []
    for rival, group in sub.groupby(group_col):
        st_dict = summarize_slash_line(group)
        st_dict[label_col] = rival
        st_dict["Equipo Rival"] = group["opposing_team"].iloc[0] if "opposing_team" in group else ""
        rows.append(st_dict)
        
    if not rows:
        return pd.DataFrame()
        
    res_df = pd.DataFrame(rows).sort_values("PA", ascending=False)
    cols = [label_col, "Equipo Rival", "PA", "AB", "H", "2B", "3B", "HR", "BB", "SO", "RBI", "AVG", "OBP", "SLG", "OPS"]
    return res_df[cols]


class LobResult(tuple):
    """Tupla de 2 elementos (team_totals, df_players) compatible con unpacking e indexación por clave."""
    def __new__(cls, summary, players_df):
        return super().__new__(cls, (summary, players_df))

    @property
    def summary(self):
        return self[0]

    @property
    def players_df(self):
        return self[1]

    def __getitem__(self, item):
        if item in ("summary", 0):
            return super().__getitem__(0)
        elif item in ("players_df", 1):
            return super().__getitem__(1)
        if isinstance(self[0], dict) and item in self[0]:
            return self[0][item]
        raise KeyError(item)

    def __contains__(self, item):
        return item in ("summary", "players_df", 0, 1) or (isinstance(self[0], dict) and item in self[0])

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default


def compute_lob_analytics(df_team_pa: Any) -> LobResult:
    """
    Calcula métricas analíticas de Dejados en Base (LOB) para el equipo y por bateador:
    1. LOB al terminar inning (3er out con corredores en base).
    2. RISP LOB al terminar inning (3er out con corredores en 2da o 3ra base).
    3. RISP LOB dentro de inning (0 o 1 out con corredores en 2da o 3ra base donde no se remolcó carrera).
    4. Total General de Oportunidades RISP LOB.
    """
    empty_summary = {
        "total_pa": 0,
        "total_lob_ending": 0,
        "total_risp_lob_ending": 0,
        "total_risp_lob_mid": 0,
        "total_risp_lob": 0,
        "lob_by_team": 0,
        "inning_risp_lob_by_team": 0,
    }
    empty_df = pd.DataFrame(columns=[
        "Bateador", "PA", "PA en RISP", "RBI", "AVG en RISP",
        "LOB al Terminar Inning", "RISP LOB al Terminar Inning",
        "RISP LOB Dentro de Inning", "Total RISP LOB"
    ])

    if df_team_pa is None:
        return LobResult(empty_summary, empty_df)

    if isinstance(df_team_pa, list):
        if len(df_team_pa) == 0:
            return LobResult(empty_summary, empty_df)
        records = []
        for it in df_team_pa:
            if isinstance(it, dict):
                if "about" in it or "matchup" in it or "result" in it:
                    batter = it.get("matchup", {}).get("batter", {}).get("fullName") or "Desconocido"
                    event = (it.get("result", {}).get("event") or "").lower()
                    rbi = it.get("result", {}).get("rbi", 0) or 0
                    records.append({
                        "batter_name": batter,
                        "runner_1b": False,
                        "runner_2b": False,
                        "runner_3b": False,
                        "is_hit": any(h in event for h in ["single", "double", "triple", "home"]),
                        "is_walk": "walk" in event,
                        "is_hbp": "hit by pitch" in event,
                        "is_ab": True,
                        "is_2_outs": False,
                        "is_risp": False,
                        "rbi": rbi,
                    })
                else:
                    records.append(it)
        df = pd.DataFrame(records)
    elif isinstance(df_team_pa, pd.DataFrame):
        if df_team_pa.empty:
            return LobResult(empty_summary, empty_df)
        df = df_team_pa.copy()
    else:
        return LobResult(empty_summary, empty_df)

    if df.empty:
        return LobResult(empty_summary, empty_df)

    for col, dval in [
        ("runner_1b", False), ("runner_2b", False), ("runner_3b", False),
        ("is_hit", False), ("is_walk", False), ("is_hbp", False),
        ("is_ab", True), ("is_2_outs", False), ("is_risp", False),
        ("rbi", 0), ("batter_name", "Desconocido")
    ]:
        if col not in df.columns:
            df[col] = dval
        else:
            df[col] = df[col].fillna(dval)

    # Corredores en base y en posición anotadora previos a la jugada
    df["runners_on_base"] = df["runner_1b"].astype(int) + df["runner_2b"].astype(int) + df["runner_3b"].astype(int)
    df["runners_in_risp"] = df["runner_2b"].astype(int) + df["runner_3b"].astype(int)
    
    # Out registrado en la jugada
    is_out_event = ~df["is_hit"].astype(bool) & ~df["is_walk"].astype(bool) & ~df["is_hbp"].astype(bool)
    df["is_out"] = is_out_event
    
    # 1. LOB al terminar inning (2 outs antes de la jugada y resultado es out)
    df["is_inning_ending_out"] = df["is_2_outs"].astype(bool) & df["is_out"]
    df["lob_inning_ending"] = np.where(df["is_inning_ending_out"], df["runners_on_base"], 0)
    df["risp_lob_inning_ending"] = np.where(df["is_inning_ending_out"], df["runners_in_risp"], 0)
    
    # 2. RISP LOB dentro de inning (0 o 1 out con hombres en RISP, resultado es out y 0 RBI)
    df["is_mid_inning_risp_out"] = (~df["is_2_outs"].astype(bool)) & df["is_risp"].astype(bool) & df["is_out"] & (df["rbi"].fillna(0) == 0)
    df["risp_lob_mid_inning"] = np.where(df["is_mid_inning_risp_out"], df["runners_in_risp"], 0)
    
    # Total RISP LOB combinado
    df["risp_lob_total"] = df["risp_lob_inning_ending"] + df["risp_lob_mid_inning"]
    
    # Resumen por jugador
    player_summary = []
    for b_name, group in df.groupby("batter_name"):
        pa_count = len(group)
        if pa_count < 1:
            continue
        tot_lob_ending = int(group["lob_inning_ending"].sum())
        risp_lob_end = int(group["risp_lob_inning_ending"].sum())
        risp_lob_mid = int(group["risp_lob_mid_inning"].sum())
        risp_lob_tot = int(group["risp_lob_total"].sum())
        
        risp_sub = group[group["is_risp"].astype(bool) == True]
        risp_opps = len(risp_sub)
        risp_hits = len(risp_sub[risp_sub["is_hit"].astype(bool) == True])
        risp_ab = len(risp_sub[risp_sub["is_ab"].astype(bool) == True])
        risp_avg = (risp_hits / risp_ab) if risp_ab > 0 else 0.0
        rbi = int(group["rbi"].sum())
        
        player_summary.append({
            "Bateador": str(b_name),
            "PA": pa_count,
            "PA en RISP": risp_opps,
            "RBI": rbi,
            "AVG en RISP": f".{int(risp_avg*1000):03d}",
            "LOB al Terminar Inning": tot_lob_ending,
            "RISP LOB al Terminar Inning": risp_lob_end,
            "RISP LOB Dentro de Inning": risp_lob_mid,
            "Total RISP LOB": risp_lob_tot,
        })
        
    if player_summary:
        df_players = pd.DataFrame(player_summary).sort_values("Total RISP LOB", ascending=False).reset_index(drop=True)
    else:
        df_players = empty_df
    
    # Totales del equipo
    team_totals = {
        "total_pa": len(df),
        "total_lob_ending": int(df["lob_inning_ending"].sum()),
        "total_risp_lob_ending": int(df["risp_lob_inning_ending"].sum()),
        "total_risp_lob_mid": int(df["risp_lob_mid_inning"].sum()),
        "total_risp_lob": int(df["risp_lob_total"].sum()),
        "lob_by_team": int(df["lob_inning_ending"].sum()),
        "inning_risp_lob_by_team": int(df["risp_lob_mid_inning"].sum()),
    }
    
    return LobResult(team_totals, df_players)
