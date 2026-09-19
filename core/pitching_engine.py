# core/pitching_engine.py
"""
pitching_engine.py
------------------
Motor analítico y de ingesta de datos para el Pitching Summary de República Caraquista.
Soporta:
1. Búsqueda universal de lanzadores (MLB, Triple-A, MiLB, LVBP).
2. Detección automática de historial en Leones del Caracas (LVBP).
3. Obtención de Game Logs (aperturas y relevos) para MLB/MiLB y LVBP.
4. Extracción pitcheo a pitcheo vía Baseball Savant Gamefeed y MLB Gameday Live Feed.
5. Cálculo de métricas Statcast completas (IVB, HB, Velo, Spin, CSW%, Whiff%, Zone%)
   y métricas PBP sabermétricas adaptadas para LVBP (Workload, LI, Platoon splits).
6. Persistencia y caché local en .cache/mlb_pbp/ para consultas ultrarrápidas.
"""

import os
import json
import time
import socket
import urllib.parse
import urllib.request
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Timeout global de socket (30s) para evitar bloqueos por bibliotecas de terceros (ej: pybaseball)
socket.setdefaulttimeout(30.0)

from core.cache import cache_ttl
from core.teams import LVBP_TEAMS, get_team_abbr, get_team_name, get_team_logo
from core.wpa_engine import calculate_leverage_index, encode_base_state


CACHE_PBP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".cache",
    "mlb_pbp"
)
os.makedirs(CACHE_PBP_DIR, exist_ok=True)

CACHE_STATCAST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".cache",
    "statcast"
)
os.makedirs(CACHE_STATCAST_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


# ── 1. Búsqueda Universal de Lanzadores y Resolución por ID ───────────────────

@cache_ttl(ttl_seconds=7200)
def _get_caracas_pitcher_ids() -> set:
    """Obtiene los IDs de lanzadores que han lanzado con Leones del Caracas en Supabase o caché."""
    caracas_ids = {
        544150,  # Albert Suárez
        468504,  # Jhoulys Chacín (MLB Person ID)
        518586,  # Jhoulys Chacín (Legacy ID)
        612797,  # Erick Leal
        660508,  # Norwith Gudiño
        600965,  # Ricardo Rodríguez
        642570,  # José Mujica
        542467,  # Yoimer Camacho
        622703,  # Ronald Herrera
        660896,  # Miguel Socolovich
        672851,  # Alfred Gutiérrez
        600526,  # José Torres
        521655,  # Wilmer Font
        660788,  # Jesus Vargas
        622415,  # Anthony Vizcaya
        672578,  # Carlos Hernández
        506693,  # Henderson Álvarez
        640470,  # Adbert Alzolay
        692350,  # Mikell Manzano
    }
    # Intentar cargar de archivos locales .cache/lvbp_season_*.json
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            if f.startswith("lvbp_season_") and f.endswith(".json"):
                try:
                    p = os.path.join(cache_dir, f)
                    with open(p, "r", encoding="utf-8") as fp:
                        s_data = json.load(fp)
                        for br in s_data.get("bullpen_records", []):
                            if br.get("team_id") == 695 and br.get("pitcher_id"):
                                caracas_ids.add(int(br.get("pitcher_id")))
                except Exception:
                    pass
    return caracas_ids


@cache_ttl(ttl_seconds=3600)
def _get_lvbp_pitcher_metadata(pitcher_id: int) -> Dict[str, Any]:
    """Consulta si un lanzador tiene registros en la LVBP (todos los 8 equipos) y retorna su equipo."""
    from core.teams import LVBP_TEAMS, LVBP_ABBR
    caracas_ids = _get_caracas_pitcher_ids()
    is_caracas = pitcher_id in caracas_ids

    # 1. Consultar Supabase
    try:
        from core.supabase_client import init_supabase
        sb = init_supabase()
        res = sb.table('pitching_stats').select('team_id, players(full_name)').eq('player_id', pitcher_id).limit(1).execute()
        if res.data:
            tid = int(res.data[0].get('team_id') or 0)
            p_data = res.data[0].get('players') or {}
            p_name = p_data.get('full_name', '') if isinstance(p_data, dict) else ''
            t_name = LVBP_TEAMS.get(tid, "Equipo LVBP")
            t_abbr = LVBP_ABBR.get(tid, "LVBP")
            return {
                "has_lvbp": True,
                "has_caracas": (tid == 695) or is_caracas,
                "team_id": tid,
                "team_name": t_name,
                "team_abbr": t_abbr,
                "name": p_name,
            }
    except Exception:
        pass

    # 2. Consultar archivos locales en .cache
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            if f.startswith("lvbp_season_") and f.endswith(".json"):
                try:
                    p = os.path.join(cache_dir, f)
                    with open(p, "r", encoding="utf-8") as fp:
                        s_data = json.load(fp)
                        for br in s_data.get("bullpen_records", []):
                            if br.get("pitcher_id") == pitcher_id:
                                tid = int(br.get("team_id") or 0)
                                return {
                                    "has_lvbp": True,
                                    "has_caracas": (tid == 695) or is_caracas,
                                    "team_id": tid,
                                    "team_name": LVBP_TEAMS.get(tid, "Equipo LVBP"),
                                    "team_abbr": LVBP_ABBR.get(tid, "LVBP"),
                                    "name": br.get("pitcher_name", ""),
                                }
                except Exception:
                    pass

    return {
        "has_lvbp": is_caracas,
        "has_caracas": is_caracas,
        "team_id": 695 if is_caracas else 0,
        "team_name": "Leones del Caracas" if is_caracas else "Agente Libre",
        "team_abbr": "CAR" if is_caracas else "MLB",
        "name": "",
    }


@cache_ttl(ttl_seconds=3600)
def get_pitcher_by_id(pitcher_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene el perfil completo de un lanzador por su ID numérico.
    Resuelve vía MLB Stats API people/{id} y enriquece con metadatos de la LVBP.
    """
    if not pitcher_id:
        return None

    lvbp_info = _get_lvbp_pitcher_metadata(pitcher_id)

    name = lvbp_info.get("name") or ""
    pos = "P"
    curr_team = lvbp_info.get("team_name") if lvbp_info.get("has_lvbp") else "Agente Libre"
    throws = "R"
    photo_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current/w_213,q_auto:best/v1/people/{pitcher_id}/headshot/67/current"

    # Consultar endpoint directo de persona en MLB Stats API
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            people = data.get("people", [])
            if people:
                p = people[0]
                name = p.get("fullName", name)
                pos = p.get("primaryPosition", {}).get("abbreviation", "P")
                mlb_team = p.get("currentTeam", {}).get("name")
                if mlb_team:
                    curr_team = mlb_team
                throws = p.get("pitchHand", {}).get("code", "R")
    except Exception:
        pass

    if not name:
        name = f"Lanzador #{pitcher_id}"

    return {
        "id": pitcher_id,
        "name": name,
        "position": pos,
        "team": curr_team,
        "throws": throws,
        "has_lvbp_history": bool(lvbp_info.get("has_lvbp")),
        "has_caracas_history": bool(lvbp_info.get("has_caracas")),
        "lvbp_team_id": lvbp_info.get("team_id", 0),
        "lvbp_team_name": lvbp_info.get("team_name", "LVBP"),
        "lvbp_team_abbr": lvbp_info.get("team_abbr", "LVBP"),
        "photo_url": photo_url,
    }


@cache_ttl(ttl_seconds=3600)
def search_pitchers(query: str) -> List[Dict[str, Any]]:
    """
    Busca lanzadores por nombre o ID numérico en MLB Stats API y cruza con la reserva
    de los 8 equipos de la LVBP y Leones del Caracas.
    """
    if not query or len(query.strip()) < 2:
        return []

    clean_query = query.strip()

    # Si es una búsqueda por ID numérico (ej: "645307"), resolver directamente
    if clean_query.isdigit():
        p_single = get_pitcher_by_id(int(clean_query))
        return [p_single] if p_single else []

    q = urllib.parse.quote(clean_query)
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={q}&sportIds=1,11,12,13,14,16,17"

    results: List[Dict[str, Any]] = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            people = data.get("people", [])
    except Exception:
        people = []

    caracas_ids = _get_caracas_pitcher_ids()

    for p in people:
        pos = p.get("primaryPosition", {}).get("abbreviation", "")
        p_id = p.get("id")
        name = p.get("fullName", "")
        curr_team = p.get("currentTeam", {}).get("name", "Agente Libre")
        throws = p.get("pitchHand", {}).get("code", "R")

        lvbp_info = _get_lvbp_pitcher_metadata(p_id)
        has_lvbp = bool(lvbp_info.get("has_lvbp"))
        has_caracas = bool(lvbp_info.get("has_caracas"))

        if has_lvbp and (not curr_team or curr_team == "Agente Libre"):
            curr_team = lvbp_info.get("team_name", curr_team)

        results.append({
            "id": p_id,
            "name": name,
            "position": pos or "P",
            "team": curr_team,
            "throws": throws,
            "has_lvbp_history": has_lvbp,
            "has_caracas_history": has_caracas,
            "lvbp_team_id": lvbp_info.get("team_id", 0),
            "lvbp_team_name": lvbp_info.get("team_name", "LVBP"),
            "lvbp_team_abbr": lvbp_info.get("team_abbr", "LVBP"),
            "photo_url": f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current/w_213,q_auto:best/v1/people/{p_id}/headshot/67/current",
        })

    # Ordenar: primero lanzadores con historial LVBP, luego lanzadores en general
    results.sort(key=lambda x: (not x["has_lvbp_history"], not x["has_caracas_history"], x["position"] != "P", x["name"]))
    return results[:15]


# ── 2. Obtención de Game Logs (Salidas) ────────────────────────────────────────

@cache_ttl(ttl_seconds=1800)
def get_pitcher_game_logs(pitcher_id: int, season: int, is_lvbp: bool = False, phase: str = "all") -> List[Dict[str, Any]]:
    """
    Obtiene las salidas (Game Logs) del lanzador para la temporada especificada.
    Si is_lvbp es True, busca en juegos de LVBP (con opción de filtrar por fase 'R', 'L', 'F', 'all'); de lo contrario en MLB y MiLB.
    """
    if is_lvbp:
        return _get_lvbp_pitcher_game_logs(pitcher_id, season, phase=phase)

    # MLB y MiLB vía MLB Stats API
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
        f"?stats=gameLog&group=pitching&season={season}&sportIds=1,11,12"
    )
    logs: List[Dict[str, Any]] = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            stats = data.get("stats", [])
            if stats:
                splits = stats[0].get("splits", [])
                for s in splits:
                    game = s.get("game", {})
                    stat = s.get("stat", {})
                    opp = s.get("opponent", {}).get("name", "Rival")
                    date_str = s.get("date", "")
                    gpk = game.get("gamePk", 0)
                    is_start = stat.get("gamesStarted", 0) > 0

                    logs.append({
                        "game_pk": gpk,
                        "date": date_str,
                        "opponent": opp,
                        "is_starter": is_start,
                        "role": "Abridor" if is_start else "Relevista",
                        "ip": stat.get("inningsPitched", "0.0"),
                        "h": stat.get("hits", 0),
                        "r": stat.get("runs", 0),
                        "er": stat.get("earnedRuns", 0),
                        "bb": stat.get("baseOnBalls", 0),
                        "so": stat.get("strikeOuts", 0),
                        "hr": stat.get("homeRuns", 0),
                        "pitches": stat.get("numberOfPitches", 0),
                        "strikes": stat.get("strikes", 0),
                        "era": stat.get("era", "0.00"),
                        "decision": _parse_decision(stat),
                        "league": "MLB" if s.get("sport", {}).get("id") == 1 else "MiLB",
                    })
    except Exception:
        pass

    # Ordenar de más reciente a más antiguo
    logs.sort(key=lambda x: x["date"], reverse=True)
    return logs


def _get_lvbp_pitcher_game_logs(pitcher_id: int, season: int, phase: str = "all") -> List[Dict[str, Any]]:
    """Obtiene salidas de LVBP desde Supabase con fallback a caché local y API oficial MLB."""
    logs: List[Dict[str, Any]] = []

    # Mapa oficial de rol abridor / relevista y datos vía MLB Stats API (sportId=17)
    starter_map: Dict[Any, bool] = {}
    pitches_map: Dict[Any, int] = {}
    strikes_map: Dict[Any, int] = {}
    phase_map: Dict[Any, str] = {}
    splits_fallback: List[Dict[str, Any]] = []
    try:
        api_url = (
            f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
            f"?stats=gameLog&group=pitching&season={season}&sportId=17&gameType=R,F,D,L,W"
        )
        req = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            stats = data.get("stats", [])
            if stats:
                splits_fallback = stats[0].get("splits", [])
                for s in splits_fallback:
                    g_pk = s.get("game", {}).get("gamePk")
                    dt = s.get("date")
                    gt = s.get("gameType") or "R"
                    gs = s.get("stat", {}).get("gamesStarted", 0) > 0
                    p_cnt = int(s.get("stat", {}).get("numberOfPitches", 0) or 0)
                    s_cnt = int(s.get("stat", {}).get("strikes", 0) or 0)
                    if g_pk:
                        starter_map[g_pk] = gs
                        pitches_map[g_pk] = p_cnt
                        strikes_map[g_pk] = s_cnt
                        phase_map[g_pk] = gt
                    if dt:
                        starter_map[dt] = gs
                        pitches_map[dt] = p_cnt
                        strikes_map[dt] = s_cnt
                        phase_map[dt] = gt
    except Exception:
        pass

    # 1. Intentar consultar Supabase
    try:
        from core.supabase_client import init_supabase
        supabase = init_supabase()
        res = supabase.table('pitching_stats') \
            .select('*, games!inner(id, game_date, season, home_team_id, away_team_id, game_type)') \
            .eq('player_id', pitcher_id) \
            .eq('games.season', season) \
            .execute()

        if res.data:
            for row in res.data:
                game = row.get("games", {})
                gid = game.get("id") or row.get("game_id")
                team_id = row.get("team_id")
                opp_id = game.get("away_team_id") if game.get("home_team_id") == team_id else game.get("home_team_id")
                opp_name = get_team_name(opp_id) if opp_id else "Rival"
                ip = row.get("ip_string") or str(row.get("innings_pitched", "0.0"))
                h = int(row.get("h", 0) or 0)
                r = int(row.get("r", 0) or 0)
                er = int(row.get("er", 0) or 0)
                bb = int(row.get("bb", 0) or 0)
                so = int(row.get("so", 0) or 0)

                # Priorizar conteo real de pitcheos del API si Supabase viene en cero/nulo
                pitches = int(row.get("pitches_thrown", 0) or 0)
                if pitches == 0:
                    pitches = pitches_map.get(gid) or pitches_map.get(game.get("game_date", "")) or 0

                strikes = int(row.get("strikes", 0) or 0)
                if strikes == 0:
                    strikes = strikes_map.get(gid) or strikes_map.get(game.get("game_date", "")) or 0

                # Filtrar salidas fantasma (jugador en roster pero que no lanzó ningún inning ni pitcheo)
                if str(ip).strip() in ("0.0", "0", "") and h == 0 and r == 0 and er == 0 and bb == 0 and so == 0 and pitches == 0:
                    continue

                g_date = game.get("game_date", "")
                g_type = game.get("game_type") or phase_map.get(gid) or phase_map.get(g_date) or "R"

                # Filtrar por fase si está especificada
                if phase and phase != "all" and g_type != phase:
                    continue

                if gid in starter_map:
                    is_start = starter_map[gid]
                elif g_date in starter_map:
                    is_start = starter_map[g_date]
                else:
                    is_start = bool(row.get("is_starter", False) or row.get("games_started", 0) > 0)

                logs.append({
                    "game_pk": gid,
                    "date": g_date,
                    "opponent": opp_name,
                    "is_starter": is_start,
                    "role": "Abridor" if is_start else "Relevista",
                    "game_type": g_type,
                    "phase": g_type,
                    "ip": ip,
                    "h": h,
                    "r": r,
                    "er": er,
                    "bb": bb,
                    "so": so,
                    "hr": int(row.get("hr", 0) or 0),
                    "pitches": pitches,
                    "strikes": strikes,
                    "era": str(row.get("era") or "0.00"),
                    "decision": "W" if row.get("wins", 0) > 0 else ("L" if row.get("losses", 0) > 0 else ("SV" if row.get("saves", 0) > 0 else "")),
                    "league": "LVBP",
                })
            if logs:
                logs.sort(key=lambda x: x["date"], reverse=True)
                return logs
    except Exception:
        pass

    # 2. Fallback a caché local .cache/lvbp_season_{season}.json
    cache_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".cache",
        f"lvbp_season_{season}.json"
    )
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fp:
                s_data = json.load(fp)
                p_stats = s_data.get("pitching_stats", [])
                games_map = {g.get("id"): g for g in s_data.get("games", [])}
                teams_map = {t.get("id"): t.get("name") for t in s_data.get("teams", [])}

                for row in p_stats:
                    if row.get("player_id") == pitcher_id:
                        gid = row.get("game_id")
                        game = games_map.get(gid, {})
                        opp_id = game.get("away_team_id") if game.get("home_team_id") == row.get("team_id") else game.get("home_team_id")
                        opp_name = teams_map.get(opp_id, LVBP_TEAMS.get(opp_id, "Rival"))
                        ip = str(row.get("innings_pitched", "0.0"))
                        h = int(row.get("hits", 0) or 0)
                        r = int(row.get("runs", 0) or 0)
                        er = int(row.get("earned_runs", 0) or 0)
                        bb = int(row.get("walks", row.get("base_on_balls", 0)) or 0)
                        so = int(row.get("strikeouts", 0) or 0)
                        pitches = int(row.get("pitches_thrown", row.get("number_of_pitches", 0)) or 0)
                        if pitches == 0:
                            pitches = pitches_map.get(gid) or pitches_map.get(game.get("game_date", "")) or 0

                        strikes = int(row.get("strikes", 0) or 0)
                        if strikes == 0:
                            strikes = strikes_map.get(gid) or strikes_map.get(game.get("game_date", "")) or 0

                        if str(ip).strip() in ("0.0", "0", "") and h == 0 and r == 0 and er == 0 and bb == 0 and so == 0 and pitches == 0:
                            continue

                        g_date = game.get("game_date", "")
                        g_type = game.get("game_type") or phase_map.get(gid) or phase_map.get(g_date) or "R"

                        if phase and phase != "all" and g_type != phase:
                            continue

                        if gid in starter_map:
                            is_start = starter_map[gid]
                        elif g_date in starter_map:
                            is_start = starter_map[g_date]
                        else:
                            is_start = bool(row.get("is_starter", False) or row.get("games_started", 0) > 0)

                        logs.append({
                            "game_pk": gid,
                            "date": g_date,
                            "opponent": opp_name,
                            "is_starter": is_start,
                            "role": "Abridor" if is_start else "Relevista",
                            "game_type": g_type,
                            "phase": g_type,
                            "ip": ip,
                            "h": h,
                            "r": r,
                            "er": er,
                            "bb": bb,
                            "so": so,
                            "hr": int(row.get("home_runs", 0) or 0),
                            "pitches": pitches,
                            "strikes": strikes,
                            "era": str(row.get("era", "0.00")),
                            "decision": "W" if row.get("wins", 0) > 0 else ("L" if row.get("losses", 0) > 0 else ("SV" if row.get("saves", 0) > 0 else "")),
                            "league": "LVBP",
                        })
            if logs:
                logs.sort(key=lambda x: x["date"], reverse=True)
                return logs
        except Exception:
            pass

    # 3. Fallback directo a los splits de MLB Stats API si no hay Supabase ni caché
    if splits_fallback:
        for s in splits_fallback:
            game = s.get("game", {})
            stat = s.get("stat", {})
            opp = s.get("opponent", {}).get("name", "Rival")
            date_str = s.get("date", "")
            gpk = game.get("gamePk", 0)
            g_type = s.get("gameType") or "R"
            if phase and phase != "all" and g_type != phase:
                continue
            is_start = stat.get("gamesStarted", 0) > 0
            logs.append({
                "game_pk": gpk,
                "date": date_str,
                "opponent": opp,
                "is_starter": is_start,
                "role": "Abridor" if is_start else "Relevista",
                "game_type": g_type,
                "phase": g_type,
                "ip": stat.get("inningsPitched", "0.0"),
                "h": stat.get("hits", 0),
                "r": stat.get("runs", 0),
                "er": stat.get("earnedRuns", 0),
                "bb": stat.get("baseOnBalls", 0),
                "so": stat.get("strikeOuts", 0),
                "hr": stat.get("homeRuns", 0),
                "pitches": stat.get("numberOfPitches", 0),
                "strikes": stat.get("strikes", 0),
                "era": stat.get("era", "0.00"),
                "decision": _parse_decision(stat),
                "league": "LVBP",
            })

    logs.sort(key=lambda x: x["date"], reverse=True)
    return logs


def _parse_decision(stat: dict) -> str:
    """Extrae la decisión W, L, SV o HLD de una salida."""
    if stat.get("wins", 0) > 0:
        return "W"
    if stat.get("losses", 0) > 0:
        return "L"
    if stat.get("saves", 0) > 0:
        return "SV"
    if stat.get("holds", 0) > 0:
        return "HLD"
    return ""


# ── 3. Extracción y Parseo de Pitcheos (Savant & Gameday) ──────────────────────

def _fetch_game_payload(game_pk: int, is_lvbp: bool = False) -> Dict[str, Any]:
    """
    Descarga el payload de pitcheos con estrategia escalonada:
    1. Archivo en disco .cache/mlb_pbp/{game_pk}.json.
    2. Si es MLB/MiLB: Baseball Savant gf endpoint.
    3. Fallback: MLB Gameday live feed.
    """
    cache_file = os.path.join(CACHE_PBP_DIR, f"{game_pk}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            pass

    payload: Dict[str, Any] = {}

    if not is_lvbp:
        # Intentar Baseball Savant gf
        savant_url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
        try:
            req = urllib.request.Request(savant_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "team_home" in data or "team_away" in data:
                    payload = {"source": "savant", "data": data}
        except Exception:
            pass

    if not payload:
        # MLB Gameday Feed
        live_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        try:
            req = urllib.request.Request(live_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                payload = {"source": "gameday", "data": data}
        except Exception:
            pass

    # Guardar en disco si se obtuvo información válida
    if payload:
        try:
            with open(cache_file, "w", encoding="utf-8") as fp:
                json.dump(payload, fp)
        except Exception:
            pass

    return payload


@cache_ttl(ttl_seconds=1800)
def get_game_pitch_data(game_pk: int, pitcher_id: int, is_lvbp: bool = False) -> Dict[str, Any]:
    """
    Extrae, limpia y calcula toda la analítica de pitcheos de una salida dada:
    - Métricas Statcast completas (si existen).
    - Métricas Play-by-Play adaptadas (siempre disponibles).
    """
    raw = _fetch_game_payload(game_pk, is_lvbp=is_lvbp)
    if not raw:
        return {"error": f"No se encontraron datos para el juego {game_pk}"}

    source = raw.get("source")
    data = raw.get("data", {})

    parsed_pitches: List[Dict[str, Any]] = []

    if source == "savant":
        parsed_pitches = _parse_savant_pitches(data, pitcher_id)
    else:
        parsed_pitches = _parse_gameday_pitches(data, pitcher_id)

    if not parsed_pitches:
        return {
            "game_pk": game_pk,
            "pitcher_id": pitcher_id,
            "total_pitches": 0,
            "pitches": [],
            "statcast_table": [],
            "pbp_table": [],
            "pbp_kpis": {},
            "innings_workload": [],
            "splits_platoon": {},
            "has_statcast": False,
        }

    # Verificar si hay telemetría Statcast
    has_statcast = any(
        p.get("speed") is not None and p.get("ivb") is not None
        for p in parsed_pitches
    )

    # 1. Tabla Statcast (Repertorio)
    statcast_table = _build_statcast_table(parsed_pitches) if has_statcast else []

    # 2. Tabla PBP Sabermétrica (Destinos de Pitcheos)
    pbp_table, pbp_kpis = _build_pbp_summary(parsed_pitches)

    # 3. Gráficos de Inning Workload & Leverage Index
    innings_workload = _build_inning_workload(parsed_pitches)

    # 4. Splits LHB vs RHB
    splits_platoon = _build_platoon_splits(parsed_pitches)

    # Detectar rol abridor / relevista desde el boxscore oficial
    is_starter = False
    try:
        boxscore = data.get("liveData", {}).get("boxscore", {})
        teams_box = boxscore.get("teams", {})
        home_p = teams_box.get("home", {}).get("pitchers", [])
        away_p = teams_box.get("away", {}).get("pitchers", [])
        if (home_p and home_p[0] == pitcher_id) or (away_p and away_p[0] == pitcher_id):
            is_starter = True
        else:
            for side in ("home", "away"):
                p_obj = teams_box.get(side, {}).get("players", {}).get(f"ID{pitcher_id}", {})
                if p_obj.get("stats", {}).get("pitching", {}).get("gamesStarted", 0) > 0:
                    is_starter = True
                    break
    except Exception:
        pass

    return {
        "game_pk": game_pk,
        "pitcher_id": pitcher_id,
        "is_starter": is_starter,
        "role": "Abridor" if is_starter else "Relevista",
        "total_pitches": len(parsed_pitches),
        "has_statcast": has_statcast,
        "statcast_table": statcast_table,
        "pbp_table": pbp_table,
        "pbp_kpis": pbp_kpis,
        "innings_workload": innings_workload,
        "splits_platoon": splits_platoon,
        "pitches": parsed_pitches,
    }


def _parse_savant_pitches(data: dict, pitcher_id: int) -> List[Dict[str, Any]]:
    """Extrae la lista plana de pitcheos desde el JSON de Baseball Savant."""
    all_raw = data.get("team_home", []) + data.get("team_away", [])
    pitches = []

    for idx, p in enumerate(all_raw):
        p_id = p.get("pitcher") or p.get("pitcher_id")
        if p_id != pitcher_id:
            continue

        p_name = p.get("pitch_name") or p.get("pitch_type") or "Desconocido"
        speed = p.get("start_speed")
        spin = p.get("spin_rate")

        # IVB y HB
        ivb = p.get("inducedBreakZ") or p.get("breakZInducedInches")
        hb = p.get("breakXInches") or p.get("pfxX")
        if hb is not None and abs(hb) < 3.0:
            # Si pfxX viene en pies, convertir a pulgadas
            hb = hb * 12.0

        px = p.get("plate_x") or p.get("px")
        pz = p.get("plate_z") or p.get("pz")
        sz_top = p.get("sz_top") or 3.5
        sz_bot = p.get("sz_bot") or 1.5

        call_name = (p.get("call_name") or p.get("description") or "").lower()
        is_whiff = bool(
            p.get("is_strike_swinging") or
            "swinging_strike" in call_name or
            "missed" in call_name
        )
        is_called = bool("called_strike" in call_name)
        is_foul = bool("foul" in call_name)
        is_in_play = bool(p.get("is_bip_out") or "in play" in call_name or "in_play" in call_name)
        is_ball = bool("ball" in call_name or "blocked" in call_name)

        is_strike = is_called or is_whiff or is_foul or is_in_play
        is_zone = bool(p.get("isInZone") or p.get("savantIsInZone"))

        pitches.append({
            "pitch_number": idx + 1,
            "pitch_name": p_name,
            "pitch_type": p.get("pitch_type") or "UN",
            "speed": round(float(speed), 1) if speed is not None else None,
            "spin": int(spin) if spin is not None else None,
            "ivb": round(float(ivb), 1) if ivb is not None else None,
            "hb": round(float(hb), 1) if hb is not None else None,
            "plate_x": round(float(px), 2) if px is not None else None,
            "plate_z": round(float(pz), 2) if pz is not None else None,
            "sz_top": float(sz_top),
            "sz_bot": float(sz_bot),
            "inning": int(p.get("inning", 1)),
            "stand": p.get("stand", "R"),
            "result": p.get("call_name") or p.get("description") or "Pitcheo",
            "is_whiff": is_whiff,
            "is_called": is_called,
            "is_foul": is_foul,
            "is_in_play": is_in_play,
            "is_ball": is_ball,
            "is_strike": is_strike,
            "is_zone": is_zone,
            "outs": int(p.get("outs", 0)),
            "strikes": int(p.get("pre_strikes", p.get("strikes", 0))),
            "balls": int(p.get("pre_balls", p.get("balls", 0))),
        })

    return pitches


def _parse_gameday_pitches(data: dict, pitcher_id: int) -> List[Dict[str, Any]]:
    """Extrae pitcheos desde el Live Feed oficial de MLB Gameday."""
    plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])
    pitches = []
    p_num = 1

    for play in plays:
        m = play.get("matchup", {})
        if m.get("pitcher", {}).get("id") != pitcher_id:
            continue

        stand = m.get("batSide", {}).get("code", "R")
        about = play.get("about", {})
        inning = about.get("inning", 1)
        is_bottom = about.get("halfInning") == "bottom"

        # Bases y marcador para apalancamiento
        home_score = play.get("result", {}).get("homeScore", 0)
        away_score = play.get("result", {}).get("awayScore", 0)

        events = play.get("playEvents", [])
        for ev in events:
            if not ev.get("isPitch"):
                continue

            pdata = ev.get("pitchData", {})
            det = ev.get("details", {})
            coords = pdata.get("coordinates", {})

            speed = pdata.get("startSpeed")
            spin = pdata.get("spinRate")
            pfx_x = coords.get("pfxX")
            pfx_z = coords.get("pfxZ")

            # Convertir coordenadas Hawk-Eye si están presentes
            ivb = pfx_z * 12.0 if pfx_z is not None else None
            hb = pfx_x * 12.0 if pfx_x is not None else None

            px = coords.get("plateX") or coords.get("x")
            pz = coords.get("plateZ") or coords.get("y")
            sz_top = pdata.get("strikeZoneTop", 3.5)
            sz_bot = pdata.get("strikeZoneBottom", 1.5)

            p_type_desc = det.get("type", {}).get("description") or det.get("type", {}).get("code") or "Pitcheo"
            desc = (det.get("description") or "").lower()

            is_whiff = bool("swinging strike" in desc or "missed" in desc or "whiff" in desc)
            is_called = bool("called strike" in desc)
            is_foul = bool("foul" in desc)
            is_in_play = bool(det.get("isInPlay", False) or "in play" in desc)
            is_ball = bool(det.get("isBall", False) or "ball" in desc)
            is_strike = bool(det.get("isStrike", False) or is_whiff or is_called or is_foul or is_in_play)

            outs = ev.get("count", {}).get("outs", 0)
            balls = ev.get("count", {}).get("balls", 0)
            strikes = ev.get("count", {}).get("strikes", 0)

            # Leverage Index aproximado
            li = calculate_leverage_index(
                inning=inning,
                is_bottom=is_bottom,
                outs=outs,
                base_state=0,
                home_score=home_score,
                away_score=away_score
            )

            pitches.append({
                "pitch_number": p_num,
                "pitch_name": p_type_desc,
                "pitch_type": det.get("type", {}).get("code", "UN"),
                "speed": round(float(speed), 1) if speed is not None else None,
                "spin": int(spin) if spin is not None else None,
                "ivb": round(float(ivb), 1) if ivb is not None else None,
                "hb": round(float(hb), 1) if hb is not None else None,
                "plate_x": round(float(px), 2) if px is not None else None,
                "plate_z": round(float(pz), 2) if pz is not None else None,
                "sz_top": float(sz_top),
                "sz_bot": float(sz_bot),
                "inning": int(inning),
                "stand": stand,
                "result": det.get("description", "Pitcheo"),
                "is_whiff": is_whiff,
                "is_called": is_called,
                "is_foul": is_foul,
                "is_in_play": is_in_play,
                "is_ball": is_ball,
                "is_strike": is_strike,
                "is_zone": bool(px is not None and abs(px) <= 0.85 and sz_bot <= (pz or 0) <= sz_top),
                "outs": outs,
                "strikes": strikes,
                "balls": balls,
                "leverage_index": round(li, 2),
            })
            p_num += 1

    return pitches


# ── 4. Cómputo de Tablas y Métricas ───────────────────────────────────────────

def _build_statcast_table(pitches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Genera la tabla central de repertorio estilo Thomas Nestico."""
    total = len(pitches)
    if total == 0:
        return []

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for p in pitches:
        p_name = p.get("pitch_name", "Desconocido")
        groups.setdefault(p_name, []).append(p)

    table = []
    for p_name, p_list in groups.items():
        cnt = len(p_list)
        pct = (cnt / total) * 100.0

        speeds = [p["speed"] for p in p_list if p.get("speed") is not None]
        spins = [p["spin"] for p in p_list if p.get("spin") is not None]
        ivbs = [p["ivb"] for p in p_list if p.get("ivb") is not None]
        hbs = [p["hb"] for p in p_list if p.get("hb") is not None]

        v_avg = round(sum(speeds) / len(speeds), 1) if speeds else "-"
        v_max = round(max(speeds), 1) if speeds else "-"
        spin_avg = int(sum(spins) / len(spins)) if spins else "-"
        ivb_avg = round(sum(ivbs) / len(ivbs), 1) if ivbs else "-"
        hb_avg = round(sum(hbs) / len(hbs), 1) if hbs else "-"

        # Whiff%: abanicados / total swings
        swings = sum(1 for p in p_list if p.get("is_whiff") or p.get("is_foul") or p.get("is_in_play"))
        whiffs = sum(1 for p in p_list if p.get("is_whiff"))
        whiff_pct = round((whiffs / swings * 100.0), 1) if swings > 0 else 0.0

        # CSW%: (called + whiffs) / total pitches
        csw_cnt = sum(1 for p in p_list if p.get("is_called") or p.get("is_whiff"))
        csw_pct = round((csw_cnt / cnt * 100.0), 1)

        # Zone%: pitcheos en zona / total pitcheos
        zone_cnt = sum(1 for p in p_list if p.get("is_zone"))
        zone_pct = round((zone_cnt / cnt * 100.0), 1)

        table.append({
            "pitch_name": p_name,
            "count": cnt,
            "usage_pct": f"{pct:.1f}%",
            "usage_val": pct,
            "velo_avg": v_avg,
            "velo_max": v_max,
            "spin_avg": spin_avg,
            "ivb": ivb_avg,
            "hb": hb_avg,
            "whiff_pct": f"{whiff_pct:.1f}%",
            "csw_pct": f"{csw_pct:.1f}%",
            "zone_pct": f"{zone_pct:.1f}%",
        })

    # Ordenar por uso descendente
    table.sort(key=lambda x: x["usage_val"], reverse=True)
    return table


def _build_pbp_summary(pitches: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Genera la tabla sabermétrica de destinos de pitcheos y KPIs (CSW%, Whiff%, 1stS%)."""
    total = len(pitches)
    if total == 0:
        return [], {}

    balls = sum(1 for p in pitches if p.get("is_ball"))
    called = sum(1 for p in pitches if p.get("is_called"))
    whiffs = sum(1 for p in pitches if p.get("is_whiff"))
    fouls = sum(1 for p in pitches if p.get("is_foul"))
    in_play = sum(1 for p in pitches if p.get("is_in_play"))

    swings = whiffs + fouls + in_play
    whiff_pct = round((whiffs / swings * 100.0), 1) if swings > 0 else 0.0
    csw_pct = round(((called + whiffs) / total * 100.0), 1)
    strike_pct = round(((total - balls) / total * 100.0), 1)

    # First Pitch Strikes
    first_pitches = [p for p in pitches if p.get("balls") == 0 and p.get("strikes") == 0]
    fp_strikes = sum(1 for p in first_pitches if p.get("is_strike"))
    fp_pct = round((fp_strikes / len(first_pitches) * 100.0), 1) if first_pitches else 0.0

    table = [
        {"destination": "Bolas", "count": balls, "pct": f"{(balls/total)*100:.1f}%"},
        {"destination": "Strikes Cantados", "count": called, "pct": f"{(called/total)*100:.1f}%"},
        {"destination": "Strikes Abanicados (Whiff)", "count": whiffs, "pct": f"{(whiffs/total)*100:.1f}%"},
        {"destination": "Fouls", "count": fouls, "pct": f"{(fouls/total)*100:.1f}%"},
        {"destination": "En Juego (Out / Hit)", "count": in_play, "pct": f"{(in_play/total)*100:.1f}%"},
    ]

    kpis = {
        "total_pitches": total,
        "strikes": total - balls,
        "strike_pct": f"{strike_pct:.1f}%",
        "csw_pct": f"{csw_pct:.1f}%",
        "whiff_pct": f"{whiff_pct:.1f}%",
        "fps_pct": f"{fp_pct:.1f}%",
        "swings": swings,
    }

    return table, kpis


def _build_inning_workload(pitches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calcula la carga por entrada (pitcheos, strikes, LI)."""
    by_inn: Dict[int, List[Dict[str, Any]]] = {}
    for p in pitches:
        inn = p.get("inning", 1)
        by_inn.setdefault(inn, []).append(p)

    workload = []
    for inn in sorted(by_inn.keys()):
        p_list = by_inn[inn]
        total_p = len(p_list)
        strikes = sum(1 for p in p_list if p.get("is_strike"))
        whiffs = sum(1 for p in p_list if p.get("is_whiff"))
        lis = [p.get("leverage_index") for p in p_list if p.get("leverage_index") is not None]
        avg_li = round(sum(lis) / len(lis), 2) if lis else 1.0

        workload.append({
            "inning": inn,
            "pitches": total_p,
            "strikes": strikes,
            "whiffs": whiffs,
            "avg_li": avg_li,
        })
    return workload


def _build_platoon_splits(pitches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula el rendimiento vs bateadores zurdos (LHB) y derechos (RHB)."""
    lhb = [p for p in pitches if p.get("stand") == "L"]
    rhb = [p for p in pitches if p.get("stand") == "R"]

    def _calc_split(p_list):
        tot = len(p_list)
        if tot == 0:
            return {"pitches": 0, "csw_pct": "0.0%", "whiff_pct": "0.0%", "strike_pct": "0.0%"}
        called = sum(1 for p in p_list if p.get("is_called"))
        whiffs = sum(1 for p in p_list if p.get("is_whiff"))
        strikes = sum(1 for p in p_list if p.get("is_strike"))
        swings = sum(1 for p in p_list if p.get("is_whiff") or p.get("is_foul") or p.get("is_in_play"))

        csw = round((called + whiffs) / tot * 100.0, 1)
        whiff = round(whiffs / swings * 100.0, 1) if swings > 0 else 0.0
        strk = round(strikes / tot * 100.0, 1)

        return {
            "pitches": tot,
            "csw_pct": f"{csw:.1f}%",
            "whiff_pct": f"{whiff:.1f}%",
            "strike_pct": f"{strk:.1f}%",
        }

    return {
        "vs_lhb": _calc_split(lhb),
        "vs_rhb": _calc_split(rhb),
    }


# ── 4. Telemetría Completa Statcast & Persistencia Local ──────────────────────

def df_processing(df_pyb: pd.DataFrame) -> pd.DataFrame:
    """Prepara y calcula las banderas de swing, whiff, zona y transforma unidades a pulgadas."""
    if df_pyb is None or df_pyb.empty:
        return pd.DataFrame()
    df = df_pyb.copy()
    swing_code = ['foul_bunt', 'foul', 'hit_into_play', 'swinging_strike', 'foul_tip',
                  'swinging_strike_blocked', 'missed_bunt', 'bunt_foul_tip']
    whiff_code = ['swinging_strike', 'foul_tip', 'swinging_strike_blocked']

    if 'description' in df.columns:
        df['swing'] = df['description'].isin(swing_code)
        df['whiff'] = df['description'].isin(whiff_code)
    else:
        df['swing'] = False
        df['whiff'] = False

    if 'zone' in df.columns:
        df['in_zone'] = df['zone'] < 10
        df['out_zone'] = df['zone'] > 10
        df['chase'] = (~df['in_zone']) & (df['swing'])
    else:
        df['in_zone'] = False
        df['out_zone'] = False
        df['chase'] = False

    # Convertir quiebres de pies a pulgadas (si vienen en pies < 6 ft)
    if 'pfx_z' in df.columns and not df['pfx_z'].dropna().empty:
        if df['pfx_z'].abs().max() < 6:
            df['pfx_z'] = df['pfx_z'] * 12
    if 'pfx_x' in df.columns and not df['pfx_x'].dropna().empty:
        if df['pfx_x'].abs().max() < 6:
            df['pfx_x'] = df['pfx_x'] * 12

    return df


def get_statcast_pitcher_df(
    pitcher_id: int,
    season: int = 2024,
    mode: str = "season",
    game_pk: Optional[int] = None,
    game_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Descarga y consulta lanzamientos Statcast para un lanzador con persistencia local en .parquet.
    Cero ocupación en Supabase.
    """
    import pybaseball as pyb

    season_parquet = os.path.join(CACHE_STATCAST_DIR, f"{pitcher_id}_{season}.parquet")
    df: Optional[pd.DataFrame] = None

    if os.path.exists(season_parquet):
        try:
            df = pd.read_parquet(season_parquet)
        except Exception:
            df = None

    if mode == "season":
        if df is None or df.empty:
            s_start = f"{season}-03-20"
            s_end = f"{season}-11-05"
            try:
                df = pyb.statcast_pitcher(s_start, s_end, pitcher_id)
                if df is not None and not df.empty:
                    df.to_parquet(season_parquet, index=False)
            except Exception:
                df = pd.DataFrame()
        return df_processing(df)

    elif mode == "game":
        # Filtrar de season_parquet si ya está en disco
        if df is not None and not df.empty:
            if game_pk and 'game_pk' in df.columns:
                df_game = df[df['game_pk'] == int(game_pk)]
                if not df_game.empty:
                    return df_processing(df_game)
            if game_date and 'game_date' in df.columns:
                df_game = df[df['game_date'].astype(str) == str(game_date)]
                if not df_game.empty:
                    return df_processing(df_game)

        # Si no estaba en season_parquet, buscar o crear game_parquet
        date_str = str(game_date) if game_date else ""
        game_parquet = os.path.join(CACHE_STATCAST_DIR, f"{pitcher_id}_{date_str}.parquet") if date_str else ""
        if game_parquet and os.path.exists(game_parquet):
            try:
                df_game = pd.read_parquet(game_parquet)
                return df_processing(df_game)
            except Exception:
                pass

        if date_str:
            try:
                df_game = pyb.statcast_pitcher(date_str, date_str, pitcher_id)
                if df_game is not None and not df_game.empty and game_parquet:
                    df_game.to_parquet(game_parquet, index=False)
                return df_processing(df_game)
            except Exception:
                pass
        return pd.DataFrame()

    elif mode == "range":
        s_date = start_date or f"{season}-04-01"
        e_date = end_date or f"{season}-06-30"

        # Si tenemos season_parquet, filtrar directamente
        if df is not None and not df.empty and 'game_date' in df.columns:
            df_range = df[(df['game_date'].astype(str) >= s_date) & (df['game_date'].astype(str) <= e_date)]
            return df_processing(df_range)

        # Si no, buscar range_parquet
        range_parquet = os.path.join(CACHE_STATCAST_DIR, f"{pitcher_id}_{s_date}_{e_date}.parquet")
        if os.path.exists(range_parquet):
            try:
                df_range = pd.read_parquet(range_parquet)
                return df_processing(df_range)
            except Exception:
                pass

        try:
            df_range = pyb.statcast_pitcher(s_date, e_date, pitcher_id)
            if df_range is not None and not df_range.empty:
                df_range.to_parquet(range_parquet, index=False)
            return df_processing(df_range)
        except Exception:
            return pd.DataFrame()

    return pd.DataFrame()


def get_pitcher_bio_data(pitcher_id: int) -> Dict[str, Any]:
    """Obtiene biografía completa y equipo actual del lanzador desde MLB Stats API."""
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={pitcher_id}&hydrate=currentTeam"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            person = data['people'][0]
            team_info = person.get('currentTeam', {})
            return {
                "name": person.get("fullName", "Pitcher"),
                "throws": person.get("pitchHand", {}).get("code", "R"),
                "age": person.get("currentAge", 28),
                "height": person.get("height", "6' 2\""),
                "weight": person.get("weight", 200),
                "team": team_info.get("name", "MLB"),
                "team_abbr": team_info.get("abbreviation", "MLB"),
                "team_id": team_info.get("id", 0),
            }
    except Exception:
        return {
            "name": "Pitcher",
            "throws": "R",
            "age": 28,
            "height": "6' 2\"",
            "weight": 200,
            "team": "MLB",
            "team_abbr": "MLB",
            "team_id": 0,
        }

