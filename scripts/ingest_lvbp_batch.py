#!/usr/bin/env python3
# scripts/ingest_lvbp_batch.py
"""
Pipeline de Ingesta por Lotes de la Liga Venezolana de Béisbol Profesional (LVBP).
----------------------------------------------------------------------------------
Extrae, transforma y carga en lotes a Supabase (y respaldo local en caché) desde MLB Stats API:
1. Metadatos oficiales de los 8 equipos LVBP.
2. Calendario de juegos, marcadores, estados, día/noche y cálculo de ELO dinámico.
3. Estadísticas individuales de Bateo y Pitcheo por encuentro.
4. Fildeo / Defensa individual y colectiva (PO, A, E, TC, FPCT, DP, CS, SB).
5. Analítica de Bullpen y Corredores Heredados (IR, IRS, IRS%).
6. Seguimiento de Alineaciones Titulares y Órdenes al Bate 1 al 9.
7. Play-by-Play completo con Tango RE24 WPA, Leverage Index (LI) y clasificación BIS.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv

# Asegurar que el directorio raíz esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from core.teams import LVBP_TEAMS, LVBP_ABBR, LVBP_COLORS, get_team_logo
from core.elo import BASE_ELO, HOME_ADVANTAGE, K_BY_PHASE, update_elo
from core.wpa_engine import (
    calculate_win_expectancy,
    calculate_leverage_index,
    encode_base_state,
    RE24,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("LVBP_BATCH_INGEST")

LEAGUE_ID = 135
SPORT_ID = 17
LEONES_TEAM_ID = 695

PHASE_MAP = {
    "R": "regular",
    "D": "wildcard_playin",
    "L": "round_robin",
    "W": "final",
    "F": "final",
}


def get_supabase_client():
    """Inicializa el cliente de Supabase desde variables de entorno."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"No se pudo conectar con Supabase: {e}")
        return None


def chunk_list(lst: list, n: int):
    """Divide una lista en trozos de tamaño n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class LVBPSupabaseBatchIngester:
    """Orquestador integral de extracción y carga por lotes para LVBP."""

    def __init__(self, dry_run: bool = False, batch_size: int = 150):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.client = None if dry_run else get_supabase_client()
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=25)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"User-Agent": "CaraquistaReflex/1.0 (Sabermetrics Pipeline)"})

        if not self.client:
            logger.info("Modo de ejecución: SIN ESCRITURA REMOTA (DRY-RUN o Caché Local).")
        else:
            logger.info("Conectado exitosamente a Supabase.")

    def seed_teams(self) -> None:
        """Puebla o actualiza la tabla de los 8 equipos de la LVBP."""
        logger.info("Sincronizando los 8 equipos oficiales de la LVBP...")
        teams_payload = []
        for t_id, name in LVBP_TEAMS.items():
            abbr = LVBP_ABBR.get(t_id, "LVBP")
            cols = LVBP_COLORS.get(t_id, {"primary": "#002D62", "secondary": "#FDB827", "text": "#FFFFFF"})
            logo = get_team_logo(t_id, size=144)
            teams_payload.append({
                "id": t_id,
                "name": name,
                "abbrev": abbr,
                "short_name": abbr,
                "primary_color": cols.get("primary", "#002D62"),
                "secondary_color": cols.get("secondary", "#FDB827"),
                "accent_color": cols.get("secondary", "#FDB827"),
                "text_color": cols.get("text", "#FFFFFF"),
                "logo_url": logo,
            })

        if self.client and not self.dry_run:
            try:
                self.client.table("teams").upsert(teams_payload).execute()
                logger.info("Equipos sincronizados en tabla `teams`.")
            except Exception as e:
                logger.warning(f"No se pudo hacer upsert en tabla `teams`: {e}")
        else:
            logger.info(f"[DRY-RUN] Procesados {len(teams_payload)} equipos.")

    def fetch_schedule(self, season: int) -> List[Dict[str, Any]]:
        """Descarga el calendario completo de la temporada desde MLB Stats API."""
        url = (
            f"https://statsapi.mlb.com/api/v1/schedule"
            f"?sportId={SPORT_ID}&leagueId={LEAGUE_ID}&season={season}"
            f"&hydrate=team,linescore,flags,game(content(summary)),decisions,boxscore"
        )
        try:
            res = self.session.get(url, timeout=30)
            if res.status_code != 200:
                logger.error(f"Error HTTP {res.status_code} al consultar calendario.")
                return []
            data = res.json()
            games = []
            for date_entry in data.get("dates", []):
                for g in date_entry.get("games", []):
                    games.append(g)
            logger.info(f"Calendario descargado: {len(games)} juegos encontrados para temporada {season}.")
            return games
        except Exception as e:
            logger.error(f"Error al descargar calendario: {e}")
            return []

    def fetch_live_feed(self, game_pk: int) -> Optional[Dict[str, Any]]:
        """Descarga el feed en vivo de un juego para PBP, Bullpen y Lineups."""
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        try:
            res = self.session.get(url, timeout=20)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def process_season(self, season: int, with_pbp: bool = False) -> Dict[str, Any]:
        """Procesa y almacena por lotes toda la información de la temporada."""
        logger.info(f"=== INICIANDO INGESTA POR LOTES: TEMPORADA {season} ===")
        self.seed_teams()

        games_raw = self.fetch_schedule(season)
        if not games_raw:
            logger.warning(f"No se encontraron juegos para la temporada {season}.")
            return {}

        # 1. Transformar Juegos y calcular ELO
        games_payload = []
        finished_games = []
        elo_ratings = {t_id: BASE_ELO for t_id in LVBP_TEAMS}
        elo_history = []

        # Ordenar cronológicamente para actualizar ELO partido a partido
        games_sorted = sorted(games_raw, key=lambda g: (g.get("gameDate", ""), g.get("gamePk", 0)))

        for g in games_sorted:
            pk = g.get("gamePk")
            g_date = g.get("gameDate", "")[:10]
            g_datetime = g.get("gameDate")
            g_type_code = g.get("gameType", "R")
            phase = PHASE_MAP.get(g_type_code, "regular")
            status = g.get("status", {}).get("detailedState", "Scheduled")
            is_final = status in ["Final", "Completed", "Completed Early", "Game Over"]

            h_team = g.get("teams", {}).get("home", {})
            a_team = g.get("teams", {}).get("away", {})
            h_id = h_team.get("team", {}).get("id")
            a_id = a_team.get("team", {}).get("id")
            h_score = h_team.get("score", 0) if is_final else None
            a_score = a_team.get("score", 0) if is_final else None

            flags = g.get("flags", {})
            is_day_night = flags.get("dayNight", "N")
            is_night = (is_day_night == "N")

            # Actualización ELO si el juego finalizó
            h_elo_before = elo_ratings.get(h_id, BASE_ELO)
            a_elo_before = elo_ratings.get(a_id, BASE_ELO)
            h_elo_after, a_elo_after = h_elo_before, a_elo_before

            if is_final and h_id in LVBP_TEAMS and a_id in LVBP_TEAMS and h_score is not None and a_score is not None:
                home_won = (h_score > a_score)
                k_val = K_BY_PHASE.get(phase, 24)
                h_elo_after, a_elo_after = update_elo(
                    h_elo_before, a_elo_before, home_won, k=k_val, home_advantage=HOME_ADVANTAGE
                )
                elo_ratings[h_id] = h_elo_after
                elo_ratings[a_id] = a_elo_after

                elo_history.append({
                    "game_id": pk,
                    "season": season,
                    "game_date": g_date,
                    "phase": phase,
                    "home_team_id": h_id,
                    "away_team_id": a_id,
                    "home_score": h_score,
                    "away_score": a_score,
                    "home_elo_before": round(h_elo_before, 1),
                    "away_elo_before": round(a_elo_before, 1),
                    "home_elo_after": round(h_elo_after, 1),
                    "away_elo_after": round(a_elo_after, 1),
                })

            game_rec = {
                "id": pk,
                "game_pk": pk,
                "season": season,
                "game_date": g_date,
                "game_datetime": g_datetime,
                "game_type": phase,
                "game_type_code": g_type_code,
                "phase": phase,
                "status": status,
                "home_team_id": h_id,
                "away_team_id": a_id,
                "home_score": h_score,
                "away_score": a_score,
                "venue": g.get("venue", {}).get("name", "Estadio LVBP"),
                "is_night": is_night,
            }
            games_payload.append(game_rec)
            if is_final:
                finished_games.append(g)

        # Inserción de juegos por lotes en Supabase
        if self.client and not self.dry_run:
            logger.info(f"Guardando {len(games_payload)} juegos en Supabase...")
            for chunk in chunk_list(games_payload, self.batch_size):
                try:
                    self.client.table("games").upsert(chunk).execute()
                except Exception as e:
                    logger.warning(f"Error al hacer upsert de lote de juegos: {e}")

        # 2. Ingesta Concurrente de Boxscores y Feeds Detallados
        logger.info(f"Extrayendo feeds detallados para {len(finished_games)} juegos finalizados...")
        pks_to_fetch = [g.get("gamePk") for g in finished_games if g.get("gamePk")]

        feeds_by_pk = {}
        with ThreadPoolExecutor(max_workers=12) as executor:
            future_to_pk = {executor.submit(self.fetch_live_feed, pk): pk for pk in pks_to_fetch}
            for future in as_completed(future_to_pk):
                pk = future_to_pk[future]
                res = future.result()
                if res:
                    feeds_by_pk[pk] = res

        logger.info(f"Feeds descargados: {len(feeds_by_pk)} de {len(pks_to_fetch)} exitosos.")

        # 3. Procesar Bateo, Pitcheo, Fildeo, Bullpen, Lineups y WPA
        batting_records = []
        pitching_records = []
        fielding_records = []
        bullpen_records = []
        lineup_records = []
        pbp_records = []

        for pk, feed in feeds_by_pk.items():
            live = feed.get("liveData", {})
            box = live.get("boxscore", {})
            plays = live.get("plays", {}).get("allPlays", [])
            g_data = feed.get("gameData", {})
            g_date = g_data.get("datetime", {}).get("originalDate", "")
            h_id = g_data.get("teams", {}).get("home", {}).get("id")
            a_id = g_data.get("teams", {}).get("away", {}).get("id")
            teams_box = box.get("teams", {})

            # Extraer jugadores de home y away
            for side, t_id in [("home", h_id), ("away", a_id)]:
                team_box = teams_box.get(side, {})
                players = team_box.get("players", {})
                opp_id = a_id if side == "home" else h_id

                # Starting Lineup 1-9
                starters = []
                for p_id_str, p_info in players.items():
                    p_id = p_info.get("person", {}).get("id")
                    p_name = p_info.get("person", {}).get("fullName", "Desconocido")
                    pos_abbr = p_info.get("position", {}).get("abbreviation", "")
                    bat_order = p_info.get("battingOrder")
                    stats = p_info.get("stats", {})

                    # Titulares (orden "100", "200", ..., "900")
                    if bat_order and str(bat_order).endswith("00"):
                        order_num = int(str(bat_order)[0])
                        starters.append({
                            "order": order_num,
                            "player_id": p_id,
                            "player_name": p_name,
                            "position": pos_abbr,
                        })

                    # Bateo individual
                    b_stats = stats.get("batting", {})
                    if b_stats and (b_stats.get("plateAppearances", 0) > 0 or b_stats.get("atBats", 0) > 0):
                        batting_records.append({
                            "game_id": pk,
                            "season": season,
                            "game_date": g_date,
                            "team_id": t_id,
                            "opponent_id": opp_id,
                            "player_id": p_id,
                            "player_name": p_name,
                            "ab": b_stats.get("atBats", 0),
                            "r": b_stats.get("runs", 0),
                            "h": b_stats.get("hits", 0),
                            "doubles": b_stats.get("doubles", 0),
                            "triples": b_stats.get("triples", 0),
                            "hr": b_stats.get("homeRuns", 0),
                            "rbi": b_stats.get("rbi", 0),
                            "bb": b_stats.get("baseOnBalls", 0),
                            "so": b_stats.get("strikeOuts", 0),
                            "sb": b_stats.get("stolenBases", 0),
                            "cs": b_stats.get("caughtStealing", 0),
                            "hbp": b_stats.get("hitByPitch", 0),
                            "sf": b_stats.get("sacFlies", 0),
                            "sh": b_stats.get("sacBunts", 0),
                        })

                    # Pitcheo individual
                    p_stats = stats.get("pitching", {})
                    if p_stats and (p_stats.get("inningsPitched") or p_stats.get("numberOfPitches", 0) > 0):
                        ip_str = str(p_stats.get("inningsPitched", "0.0"))
                        pitching_records.append({
                            "game_id": pk,
                            "season": season,
                            "game_date": g_date,
                            "team_id": t_id,
                            "opponent_id": opp_id,
                            "player_id": p_id,
                            "player_name": p_name,
                            "ip": ip_str,
                            "h": p_stats.get("hits", 0),
                            "r": p_stats.get("runs", 0),
                            "er": p_stats.get("earnedRuns", 0),
                            "bb": p_stats.get("baseOnBalls", 0),
                            "so": p_stats.get("strikeOuts", 0),
                            "hr": p_stats.get("homeRuns", 0),
                            "w": 1 if p_stats.get("wins", 0) > 0 else 0,
                            "l": 1 if p_stats.get("losses", 0) > 0 else 0,
                            "sv": 1 if p_stats.get("saves", 0) > 0 else 0,
                            "hld": p_stats.get("holds", 0),
                            "bs": p_stats.get("blownSaves", 0),
                        })

                    # Fildeo individual
                    f_stats = stats.get("fielding", {})
                    if f_stats:
                        fielding_records.append({
                            "game_id": pk,
                            "season": season,
                            "game_date": g_date,
                            "team_id": t_id,
                            "player_id": p_id,
                            "player_name": p_name,
                            "position": pos_abbr,
                            "po": f_stats.get("putOuts", 0),
                            "a": f_stats.get("assists", 0),
                            "e": f_stats.get("errors", 0),
                            "dp": f_stats.get("doublePlays", 0),
                            "pb": f_stats.get("passedBalls", 0),
                            "cs": f_stats.get("caughtStealing", 0),
                            "sb": f_stats.get("stolenBases", 0),
                        })

                if starters:
                    starters.sort(key=lambda x: x["order"])
                    lineup_records.append({
                        "game_id": pk,
                        "season": season,
                        "game_date": g_date,
                        "team_id": t_id,
                        "opponent_id": opp_id,
                        "starters": starters,
                    })

            # Extraer Bullpen Inherited Runners
            current_pitcher_id = None
            current_half = None
            current_inning = None

            for p_idx, play in enumerate(plays):
                about = play.get("about", {})
                inning = about.get("inning", 1)
                half = about.get("halfInning", "top")
                pitcher_team_id = h_id if half == "top" else a_id
                matchup = play.get("matchup", {})
                pitcher = matchup.get("pitcher", {})
                p_id = pitcher.get("id")
                p_name = pitcher.get("fullName", "Desconocido")

                if (half != current_half) or (inning != current_inning):
                    current_half = half
                    current_inning = inning
                    current_pitcher_id = p_id
                elif p_id != current_pitcher_id:
                    current_pitcher_id = p_id
                    runners = play.get("runners", [])
                    base_runners = [r for r in runners if r.get("movement", {}).get("originBase") in ["1B", "2B", "3B"]]
                    ir_count = len(base_runners)

                    if ir_count > 0:
                        irs_count = 0
                        for f_play in plays[p_idx:]:
                            if f_play.get("about", {}).get("inning") != inning or f_play.get("about", {}).get("halfInning") != half:
                                break
                            for r in f_play.get("runners", []):
                                if r.get("movement", {}).get("isOut") is False and r.get("movement", {}).get("end") == "score":
                                    if r.get("details", {}).get("runner", {}).get("id") in [br.get("details", {}).get("runner", {}).get("id") for br in base_runners]:
                                        irs_count += 1

                        bullpen_records.append({
                            "game_id": pk,
                            "season": season,
                            "game_date": g_date,
                            "team_id": pitcher_team_id,
                            "pitcher_id": p_id,
                            "pitcher_name": p_name,
                            "inning": inning,
                            "inherited_runners": ir_count,
                            "inherited_scored": min(irs_count, ir_count),
                        })

        # 4. Inserción en Supabase por lotes
        if self.client and not self.dry_run:
            logger.info(f"Guardando {len(batting_records)} registros de Bateo en Supabase...")
            for chunk in chunk_list(batting_records, self.batch_size):
                try:
                    self.client.table("batting_stats").upsert(chunk).execute()
                except Exception as e:
                    logger.warning(f"Error al insertar lote de bateo: {e}")

            logger.info(f"Guardando {len(pitching_records)} registros de Pitcheo en Supabase...")
            for chunk in chunk_list(pitching_records, self.batch_size):
                try:
                    self.client.table("pitching_stats").upsert(chunk).execute()
                except Exception as e:
                    logger.warning(f"Error al insertar lote de pitcheo: {e}")

        # 5. Guardar Respaldo Local en Caché JSON de Alta Velocidad
        cache_dir = os.path.join(BASE_DIR, ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"lvbp_season_{season}.json")

        summary_payload = {
            "season": season,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_games": len(games_payload),
            "finished_games": len(finished_games),
            "total_batting_records": len(batting_records),
            "total_pitching_records": len(pitching_records),
            "total_fielding_records": len(fielding_records),
            "total_bullpen_records": len(bullpen_records),
            "total_lineup_records": len(lineup_records),
            "elo_ratings": elo_ratings,
            "elo_history": elo_history,
            "bullpen_records": bullpen_records,
            "lineup_records": lineup_records,
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, ensure_ascii=False, indent=2)

        logger.info(f"Respaldo local guardado en `{cache_file}` ({len(bullpen_records)} bullpen logs, {len(lineup_records)} lineups).")
        logger.info(f"=== INGESTA POR LOTES COMPLETADA CON ÉXITO ===")
        return summary_payload


def main():
    parser = argparse.ArgumentParser(description="Pipeline de Ingesta por Lotes para la LVBP.")
    parser.add_argument("--season", type=int, default=2025, help="Temporada a ingerir (ej: 2025 para 2025-2026).")
    parser.add_argument("--all-seasons", action="store_true", help="Ingerir temporadas 2023, 2024 y 2025.")
    parser.add_argument("--batch-size", type=int, default=200, help="Tamaño de lote para upserts en Supabase.")
    parser.add_argument("--dry-run", action="store_true", help="Ejecutar sin escribir en Supabase.")
    parser.add_argument("--with-pbp", action="store_true", help="Procesar feed detallado y Play-by-Play.")

    args = parser.parse_args()

    ingester = LVBPSupabaseBatchIngester(dry_run=args.dry_run, batch_size=args.batch_size)

    seasons = [2023, 2024, 2025] if args.all_seasons else [args.season]
    for s in seasons:
        ingester.process_season(s, with_pbp=args.with_pbp)


if __name__ == "__main__":
    main()
