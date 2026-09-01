import os
from supabase import create_client, Client
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Dict, Optional, Any
from dotenv import load_dotenv
from core.cache import cache_ttl

load_dotenv()

# Inicializar cliente de Supabase
@cache_ttl(ttl_seconds=3600)
def init_supabase() -> Client:
    """Inicializa y retorna el cliente de Supabase"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar definidos en las variables de entorno o archivo .env")
    return create_client(url, key)

def get_current_season():
    """Retorna la temporada actual basada en la fecha (Oct-Dic: año actual, Ene-Sep: año anterior)"""
    now = datetime.now()
    month = now.month
    year = now.year

    # La temporada LVBP 2025-2026 se almacena como 2025 (año de inicio)
    if month >= 10:
        return year
    else:
        return year - 1

@cache_ttl(ttl_seconds=600)
def get_available_seasons():
    """Obtiene todas las temporadas disponibles en la base de datos"""
    supabase = init_supabase()

    try:
        response = supabase.table('games') \
            .select('season') \
            .execute()

        if response.data:
            seasons = list(set([g['season'] for g in response.data if g.get('season')]))
            if seasons:
                return sorted(seasons, reverse=True)
    except:
        pass

    return [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]

@cache_ttl(ttl_seconds=600)  # Cache por 10 minutos
def get_standings(season=None, phase='regular'):
    """Calcula standings desde la tabla games - Solo equipos LVBP filtrados por fase"""
    if season is None:
        season = get_current_season()
    
    supabase = init_supabase()
    
    # IDs de los equipos LVBP
    LVBP_TEAM_IDS = [692, 693, 694, 695, 696, 697, 698, 699]
    
    # Mapeo de fase a códigos de game_type
    PHASE_TYPE_MAP = {
        'regular': ['R'],
        'round_robin': ['L'],
        'wildcard_playin': ['D'],
        'final': ['F'],
        'all': ['R', 'L', 'D', 'F']
    }
    game_types = PHASE_TYPE_MAP.get(phase, ['R'])
    
    # Calcular desde games según la fase seleccionada
    try:
        games_response = supabase.table('games') \
            .select('*') \
            .eq('season', season) \
            .in_('status', ['Final', 'Completed', 'Completed Early']) \
            .in_('game_type', game_types) \
            .execute()
        
        if not games_response.data:
            return pd.DataFrame()
        
        games_df = pd.DataFrame(games_response.data)
        games_df = games_df.sort_values('game_date')
        
        # Filtrar solo juegos de equipos LVBP
        games_df = games_df[
            (games_df['home_team_id'].isin(LVBP_TEAM_IDS)) | 
            (games_df['away_team_id'].isin(LVBP_TEAM_IDS))
        ]
        
        # Obtener información de equipos
        teams_response = supabase.table('teams') \
            .select('*') \
            .in_('id', LVBP_TEAM_IDS) \
            .execute()
        
        if not teams_response.data:
            return pd.DataFrame()
        
        teams_df = pd.DataFrame(teams_response.data)
        
        # Calcular standings
        standings_data = []
        
        for team in teams_df.itertuples():
            # Filtrar juegos del equipo
            team_games = games_df[
                (games_df['home_team_id'] == team.id) | 
                (games_df['away_team_id'] == team.id)
            ]
            
            if len(team_games) == 0:
                continue
            
            wins = 0
            losses = 0
            runs_for = 0
            runs_against = 0
            home_wins = 0
            home_losses = 0
            away_wins = 0
            away_losses = 0
            last_10 = []
            
            # Ordenar juegos por fecha para calcular rachas
            team_games_sorted = team_games.sort_values('game_date')
            
            for _, game in team_games_sorted.iterrows():
                if game['home_team_id'] == team.id:
                    # Juego de local
                    runs_for += game['home_score'] or 0
                    runs_against += game['away_score'] or 0
                    
                    if game['home_score'] > game['away_score']:
                        wins += 1
                        home_wins += 1
                        last_10.append('W')
                    else:
                        losses += 1
                        home_losses += 1
                        last_10.append('L')
                else:
                    # Juego de visitante
                    runs_for += game['away_score'] or 0
                    runs_against += game['home_score'] or 0
                    
                    if game['away_score'] > game['home_score']:
                        wins += 1
                        away_wins += 1
                        last_10.append('W')
                    else:
                        losses += 1
                        away_losses += 1
                        last_10.append('L')
            
            # Calcular estadísticas
            games_played = wins + losses
            pct = wins / games_played if games_played > 0 else 0
            
            # Últimos 10 juegos
            last_10 = last_10[-10:] if len(last_10) >= 10 else last_10
            last_10_wins = last_10.count('W')
            last_10_losses = last_10.count('L')
            last_10_record = f"{last_10_wins}-{last_10_losses}"
            
            # Racha actual
            if last_10:
                current_streak = 1
                streak_type = last_10[-1]
                for i in range(len(last_10)-2, -1, -1):
                    if last_10[i] == streak_type:
                        current_streak += 1
                    else:
                        break
                streak = f"{streak_type}{current_streak}"
            else:
                streak = "-"
            
            standings_data.append({
                'team_id': team.id,
                'team_name': team.name,
                'team_abbreviation': team.abbreviation if hasattr(team, 'abbreviation') else '',
                'wins': wins,
                'losses': losses,
                'pct': pct,
                'games_back': 0,  # Se calculará después
                'runs_for': runs_for,
                'runs_against': runs_against,
                'run_diff': runs_for - runs_against,
                'home_record': f"{home_wins}-{home_losses}",
                'away_record': f"{away_wins}-{away_losses}",
                'last_10': last_10_record,
                'streak': streak
            })
        
        if not standings_data:
            return pd.DataFrame()
        
        # Crear DataFrame y ordenar por PCT
        standings_df = pd.DataFrame(standings_data).sort_values('pct', ascending=False)
        
        # Calcular games back
        if not standings_df.empty:
            leader_wins = standings_df.iloc[0]['wins']
            leader_losses = standings_df.iloc[0]['losses']
            
            standings_df['games_back'] = standings_df.apply(
                lambda x: ((leader_wins - x['wins']) + (x['losses'] - leader_losses)) / 2,
                axis=1
            )
        
        return standings_df
        
    except Exception as e:
        st.error(f"Error calculando standings: {str(e)}")
        return pd.DataFrame()

def parse_single_game_advanced(game):
    """Procesa un juego individual consultando el feed de MLB Stats API."""
    game_pk = game["id"]
    is_home = (game["home_team_id"] == 695)
    leones_score = game["home_score"] if is_home else game["away_score"]
    opp_score = game["away_score"] if is_home else game["home_score"]
    won = leones_score > opp_score
    game_date = game["game_date"]
    
    # 1. De noche: >= 19:00 hora local venezolana (VET = UTC-4)
    is_night = True
    if game.get("game_datetime"):
        try:
            dt = datetime.fromisoformat(game["game_datetime"].replace("Z", "+00:00"))
            vet_dt = dt - timedelta(hours=4)
            is_night = (vet_dt.hour >= 19)
        except Exception:
            pass
            
    # 2. Consultar feed live
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            feed = r.json()
            live_data = feed.get("liveData", {})
            linescore = live_data.get("linescore", {})
            boxscore = live_data.get("boxscore", {})
            decisions = live_data.get("decisions", {})
            
            # Innings totales (Extrainnings > 9)
            total_innings = len(linescore.get("innings", []))
            is_extra = (total_innings > 9)
            
            # Marcador al 7mo inning (acumulado tras los primeros 6 innings)
            runs_leo_6 = 0
            runs_opp_6 = 0
            for inn in linescore.get("innings", [])[:6]:
                runs_leo_6 += inn.get("home" if is_home else "away", {}).get("runs", 0)
                runs_opp_6 += inn.get("away" if is_home else "home", {}).get("runs", 0)
                
            led_after_6 = (runs_leo_6 > runs_opp_6)
            trailed_after_6 = (runs_leo_6 < runs_opp_6)
            
            # Decisiones de pitcheo (Abridor vs Relevistas)
            winner_id = decisions.get("winner", {}).get("id")
            loser_id = decisions.get("loser", {}).get("id")
            save_id = decisions.get("save", {}).get("id")
            
            leones_box = boxscore.get("teams", {}).get("home" if is_home else "away", {})
            leones_pitchers = leones_box.get("pitchers", [])
            leones_starter_id = leones_pitchers[0] if leones_pitchers else None
            leones_relievers = leones_pitchers[1:] if len(leones_pitchers) > 1 else []
            
            starter_win = (won and winner_id == leones_starter_id)
            starter_loss = ((not won) and loser_id == leones_starter_id)
            reliever_win = (won and winner_id in leones_relievers)
            reliever_loss = ((not won) and loser_id in leones_relievers)
            has_save = (save_id in leones_pitchers)
            
            # Terreneadas: Leones siendo local gana en la baja del 9no (o entradas extras)
            all_plays = live_data.get("plays", {}).get("allPlays", [])
            last_play = all_plays[-1] if all_plays else {}
            about = last_play.get("about", {})
            last_play_half = about.get("halfInning")
            last_play_inning = about.get("inning", 1)
            is_walkoff_play = about.get("isWalkOff", False)
            
            is_terreneada = bool(is_home and won and ((last_play_half == "bottom" and last_play_inning >= 9) or is_walkoff_play))
            
            return {
                "game_pk": game_pk,
                "game_date": game_date,
                "won": won,
                "is_home": is_home,
                "is_night": is_night,
                "is_extra": is_extra,
                "shutout": won and (opp_score == 0),
                "one_run": abs(leones_score - opp_score) == 1,
                "led_after_6": led_after_6,
                "trailed_after_6": trailed_after_6,
                "starter_win": starter_win,
                "starter_loss": starter_loss,
                "reliever_win": reliever_win,
                "reliever_loss": reliever_loss,
                "has_save": has_save,
                "terreneada": is_terreneada
            }
    except Exception:
        pass
        
    return {
        "game_pk": game_pk,
        "game_date": game_date,
        "won": won,
        "is_home": is_home,
        "is_night": is_night,
        "is_extra": False,
        "shutout": won and (opp_score == 0),
        "one_run": abs(leones_score - opp_score) == 1,
        "led_after_6": False,
        "trailed_after_6": False,
        "starter_win": False,
        "starter_loss": False,
        "reliever_win": False,
        "reliever_loss": False,
        "has_save": False,
        "terreneada": False
    }


@cache_ttl(ttl_seconds=600)
def get_leones_advanced_stats(season=None, cache_version="v4_terreneadas_fixed"):
    """Calcula estadísticas avanzadas de los Leones del Caracas con precisión de MLB Stats API"""
    if season is None:
        season = get_current_season()
    
    supabase = init_supabase()
    
    try:
        games_response = supabase.table('games') \
            .select('*') \
            .eq('season', season) \
            .in_('status', ['Final', 'Completed', 'Completed Early', 'Game Over']) \
            .or_('home_team_id.eq.695,away_team_id.eq.695') \
            .eq('game_type', 'R') \
            .order('game_date', desc=False) \
            .execute()
        
        if not games_response.data:
            return {}
        
        games = games_response.data
        total_games = len(games)
        
        with ThreadPoolExecutor(max_workers=12) as executor:
            parsed = list(executor.map(parse_single_game_advanced, games))
            
        parsed_clean = [p for p in parsed if p]
        
        wins = sum(1 for p in parsed_clean if p["won"])
        losses = total_games - wins
        
        home_wins = sum(1 for p in parsed_clean if p["is_home"] and p["won"])
        home_losses = sum(1 for p in parsed_clean if p["is_home"] and not p["won"])
        away_wins = sum(1 for p in parsed_clean if (not p["is_home"]) and p["won"])
        away_losses = sum(1 for p in parsed_clean if (not p["is_home"]) and not p["won"])
        
        night_wins = sum(1 for p in parsed_clean if p["is_night"] and p["won"])
        night_losses = sum(1 for p in parsed_clean if p["is_night"] and not p["won"])
        
        shutouts = sum(1 for p in parsed_clean if p["shutout"])
        
        extra_wins = sum(1 for p in parsed_clean if p["is_extra"] and p["won"])
        extra_losses = sum(1 for p in parsed_clean if p["is_extra"] and not p["won"])
        
        one_run_wins = sum(1 for p in parsed_clean if p["one_run"] and p["won"])
        one_run_losses = sum(1 for p in parsed_clean if p["one_run"] and not p["won"])
        
        # Remontadas: Ganados llegando perdiendo al 7mo
        remontados = sum(1 for p in parsed_clean if p["trailed_after_6"] and p["won"])
        
        # Arriba: Récord llegando ganando al 7mo
        arriba_wins = sum(1 for p in parsed_clean if p["led_after_6"] and p["won"])
        arriba_losses = sum(1 for p in parsed_clean if p["led_after_6"] and not p["won"])
        
        # Terreneadas (Walk-off wins)
        terreneadas = sum(1 for p in parsed_clean if p.get("terreneada", False))
        
        # Decisiones de pitcheo
        starter_wins = sum(1 for p in parsed_clean if p["starter_win"])
        starter_losses = sum(1 for p in parsed_clean if p["starter_loss"])
        reliever_wins = sum(1 for p in parsed_clean if p["reliever_win"])
        reliever_losses = sum(1 for p in parsed_clean if p["reliever_loss"])
        
        saves = sum(1 for p in parsed_clean if p["has_save"])
        
        # Por mes
        oct_wins = oct_losses = nov_wins = nov_losses = dec_wins = dec_losses = 0
        for p in parsed_clean:
            try:
                m = pd.to_datetime(p["game_date"]).month
                if m == 10:
                    if p["won"]: oct_wins += 1
                    else: oct_losses += 1
                elif m == 11:
                    if p["won"]: nov_wins += 1
                    else: nov_losses += 1
                elif m == 12:
                    if p["won"]: dec_wins += 1
                    else: dec_losses += 1
            except Exception:
                pass
                
        # Por día de semana (0=Lunes, 1=Martes, ..., 6=Domingo)
        days_records = {i: {"w": 0, "l": 0} for i in range(7)}
        for p in parsed_clean:
            try:
                wd = pd.to_datetime(p["game_date"]).weekday()
                if p["won"]:
                    days_records[wd]["w"] += 1
                else:
                    days_records[wd]["l"] += 1
            except Exception:
                pass
                
        # Últimos 10
        last_10 = sorted(parsed_clean, key=lambda x: x["game_date"], reverse=True)[:10]
        l10_wins = sum(1 for p in last_10 if p["won"])
        l10_losses = len(last_10) - l10_wins
        
        # Racha
        chronological = sorted(parsed_clean, key=lambda x: x["game_date"])
        if chronological:
            last_res = chronological[-1]["won"]
            stk_count = 0
            for p in reversed(chronological):
                if p["won"] == last_res:
                    stk_count += 1
                else:
                    break
            streak = f"{stk_count} {'W' if last_res else 'L'}"
        else:
            streak = "N/A"
            
        return {
            'total_games': total_games,
            'record': f"{wins}-{losses}",
            'home_record': f"{home_wins}-{home_losses}",
            'away_record': f"{away_wins}-{away_losses}",
            'night_record': f"{night_wins}-{night_losses}",
            'shutouts': f"{shutouts}",
            'streak': streak,
            'extra_inning': f"{extra_wins}-{extra_losses}",
            'last_10': f"{l10_wins}-{l10_losses}",
            'one_run': f"{one_run_wins}-{one_run_losses}",
            'remontados': f"{remontados}",
            'up': f"{arriba_wins}-{arriba_losses}",
            'terreneadas': f"{terreneadas}",
            'starters': f"{starter_wins}-{starter_losses}",
            'relievers': f"{reliever_wins}-{reliever_losses}",
            'saves': f"{saves}",
            'oct': f"{oct_wins}G-{oct_losses}P",
            'nov': f"{nov_wins}G-{nov_losses}P",
            'dec': f"{dec_wins}G-{dec_losses}P",
            'lunes': f"{days_records[0]['w']}G-{days_records[0]['l']}P",
            'martes': f"{days_records[1]['w']}G-{days_records[1]['l']}P",
            'miercoles': f"{days_records[2]['w']}G-{days_records[2]['l']}P",
            'jueves': f"{days_records[3]['w']}G-{days_records[3]['l']}P",
            'viernes': f"{days_records[4]['w']}G-{days_records[4]['l']}P",
            'sabado': f"{days_records[5]['w']}G-{days_records[5]['l']}P",
            'domingo': f"{days_records[6]['w']}G-{days_records[6]['l']}P"
        }
    except Exception as e:
        st.error(f"Error calculando estadísticas avanzadas: {str(e)}")
        return {}
   
@cache_ttl(ttl_seconds=600)
def get_recent_games(team_id=695, limit=10, season=None):
    """Obtiene los últimos juegos del equipo"""
    supabase = init_supabase()
    
    try:
        query = supabase.table('games') \
            .select('*, home_team:teams!games_home_team_id_fkey(name, abbreviation), away_team:teams!games_away_team_id_fkey(name, abbreviation)') \
            .or_(f'home_team_id.eq.{team_id},away_team_id.eq.{team_id}') \
            .eq('status', 'Final')
            
        if season is not None:
            query = query.eq('season', season)
            
        response = query.order('game_date', desc=True).limit(limit).execute()
        
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        return pd.DataFrame()

@cache_ttl(ttl_seconds=600)
def get_batting_stats(team_id=695, limit=50, season=None):
    """Obtiene estadísticas de bateo agregadas por jugador"""
    supabase = init_supabase()

    if season is None:
        season = get_current_season()

    try:
        # Obtener todos los registros de bateo del equipo para la temporada
        response = supabase.table('batting_stats') \
            .select('*, players!inner(full_name), games!inner(season)') \
            .eq('team_id', team_id) \
            .eq('games.season', season) \
            .execute()

        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)

        # Extraer nombre del jugador
        df['player_name'] = df['players'].apply(
            lambda x: x.get('full_name', 'N/A') if isinstance(x, dict) else 'N/A'
        )

        # Agrupar por jugador y sumar estadísticas (incluir todas las columnas disponibles)
        agg_dict = {
            'ab': 'sum',
            'r': 'sum',
            'h': 'sum',
            'doubles': 'sum',
            'triples': 'sum',
            'hr': 'sum',
            'rbi': 'sum',
            'bb': 'sum',
            'so': 'sum',
            'sb': 'sum'
        }

        # Agregar columnas adicionales si existen
        if 'cs' in df.columns:
            agg_dict['cs'] = 'sum'
        if 'hbp' in df.columns:
            agg_dict['hbp'] = 'sum'
        if 'sf' in df.columns:
            agg_dict['sf'] = 'sum'
        if 'sh' in df.columns:
            agg_dict['sh'] = 'sum'

        grouped = df.groupby(['player_id', 'player_name']).agg(agg_dict).reset_index()

        # Calcular estadísticas derivadas con fórmula estándar de OBP
        hbp_col = grouped['hbp'] if 'hbp' in grouped.columns else 0
        sf_col = grouped['sf'] if 'sf' in grouped.columns else 0
        obp_den = grouped['ab'] + grouped['bb'] + hbp_col + sf_col

        grouped['avg'] = np.where(grouped['ab'] > 0, (grouped['h'] / grouped['ab']), 0.0).round(3)
        grouped['obp'] = np.where(obp_den > 0, ((grouped['h'] + grouped['bb'] + hbp_col) / obp_den), 0.0).round(3)
        grouped['slg'] = np.where(grouped['ab'] > 0, ((grouped['h'] + grouped['doubles'] + 2*grouped['triples'] + 3*grouped['hr']) / grouped['ab']), 0.0).round(3)
        grouped['ops'] = (grouped['obp'] + grouped['slg']).round(3)

        # Crear columna 'players' con el formato esperado
        grouped['players'] = grouped.apply(
            lambda row: {'full_name': row['player_name']}, axis=1
        )

        return grouped.sort_values('ops', ascending=False).head(limit)

    except Exception as e:
        print(f"Error obteniendo estadísticas de bateo: {str(e)}")
        return pd.DataFrame()

@cache_ttl(ttl_seconds=600)
def get_pitching_stats(team_id=695, limit=50, season=None):
    """Obtiene estadísticas de pitcheo agregadas por jugador"""
    supabase = init_supabase()

    if season is None:
        season = get_current_season()

    try:
        # Obtener todos los registros de pitcheo del equipo para la temporada
        response = supabase.table('pitching_stats') \
            .select('*, players!inner(full_name), games!inner(season)') \
            .eq('team_id', team_id) \
            .eq('games.season', season) \
            .execute()

        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)

        # Extraer nombre del jugador
        df['player_name'] = df['players'].apply(
            lambda x: x.get('full_name', 'N/A') if isinstance(x, dict) else 'N/A'
        )

        # Contar juegos (apariciones)
        df['g_count'] = 1

        # Agrupar por jugador y sumar estadísticas (incluir todas las columnas disponibles)
        agg_dict = {
            'ip_decimal': 'sum',
            'h': 'sum',
            'r': 'sum',
            'er': 'sum',
            'bb': 'sum',
            'so': 'sum',
            'hr': 'sum',
            'g_count': 'sum'
        }

        # Agregar columnas adicionales si existen
        if 'hbp' in df.columns:
            agg_dict['hbp'] = 'sum'
        if 'wp' in df.columns:
            agg_dict['wp'] = 'sum'
        if 'bk' in df.columns:
            agg_dict['bk'] = 'sum'

        grouped = df.groupby(['player_id', 'player_name']).agg(agg_dict).reset_index()

        # Renombrar columnas
        grouped = grouped.rename(columns={
            'ip_decimal': 'ip',
            'g_count': 'g'
        })

        # Calcular estadísticas derivadas con protección ante IP=0
        grouped['era'] = np.where(grouped['ip'] > 0, ((grouped['er'] * 9) / grouped['ip']), 0.0).round(2)
        grouped['whip'] = np.where(grouped['ip'] > 0, ((grouped['h'] + grouped['bb']) / grouped['ip']), 0.0).round(2)

        # Estas estadísticas no están disponibles en el boxscore individual
        # Las inicializamos en 0 por ahora
        grouped['w'] = 0
        grouped['l'] = 0
        grouped['sv'] = 0
        grouped['gs'] = 0

        # Crear columna 'players' con el formato esperado
        grouped['players'] = grouped.apply(
            lambda row: {'full_name': row['player_name']}, axis=1
        )

        return grouped.sort_values('ip', ascending=False).head(limit)

    except Exception as e:
        print(f"Error obteniendo estadísticas de pitcheo: {str(e)}")
        return pd.DataFrame()

def calculate_batting_stats(df):
    """Calcula estadísticas de bateo agregadas con fórmula estándar de OBP"""
    if df.empty:
        return df
    
    agg_dict = {
        'ab': 'sum',
        'r': 'sum',
        'h': 'sum',
        'doubles': 'sum',
        'triples': 'sum',
        'hr': 'sum',
        'rbi': 'sum',
        'bb': 'sum',
        'so': 'sum',
        'sb': 'sum'
    }
    if 'hbp' in df.columns:
        agg_dict['hbp'] = 'sum'
    if 'sf' in df.columns:
        agg_dict['sf'] = 'sum'
    if 'sh' in df.columns:
        agg_dict['sh'] = 'sum'
    if 'cs' in df.columns:
        agg_dict['cs'] = 'sum'

    grouped = df.groupby('player_id').agg(agg_dict).reset_index()
    
    # Calcular promedios
    hbp_col = grouped['hbp'] if 'hbp' in grouped.columns else 0
    sf_col = grouped['sf'] if 'sf' in grouped.columns else 0
    obp_den = grouped['ab'] + grouped['bb'] + hbp_col + sf_col

    grouped['avg'] = np.where(grouped['ab'] > 0, (grouped['h'] / grouped['ab']), 0.0).round(3)
    grouped['obp'] = np.where(obp_den > 0, ((grouped['h'] + grouped['bb'] + hbp_col) / obp_den), 0.0).round(3)
    grouped['slg'] = np.where(grouped['ab'] > 0, ((grouped['h'] + grouped['doubles'] + 2*grouped['triples'] + 3*grouped['hr']) / grouped['ab']), 0.0).round(3)
    grouped['ops'] = (grouped['obp'] + grouped['slg']).round(3)
    
    return grouped.sort_values('avg', ascending=False)


@cache_ttl(ttl_seconds=1800)
def get_weekly_records(season=None, team_id=695, phase='regular') -> pd.DataFrame:
    """
    Calcula el desglose de rendimiento semana a semana (lunes a domingo ISO)
    para el equipo en la temporada y fase seleccionada.
    """
    if season is None:
        season = get_current_season()
        
    supabase = init_supabase()
    
    PHASE_TYPE_MAP = {
        'regular': ['R'],
        'round_robin': ['L'],
        'wildcard_playin': ['D'],
        'final': ['F'],
        'all': ['R', 'L', 'D', 'F']
    }
    game_types = PHASE_TYPE_MAP.get(phase, ['R'])
    
    try:
        res = supabase.table('games') \
            .select('*') \
            .eq('season', season) \
            .in_('status', ['Final', 'Completed', 'Completed Early', 'Game Over']) \
            .in_('game_type', game_types) \
            .or_(f'home_team_id.eq.{team_id},away_team_id.eq.{team_id}') \
            .order('game_date', desc=False) \
            .execute()
            
        games = res.data or []
        if not games:
            return pd.DataFrame()
            
        parsed = []
        for g in games:
            is_home = (g["home_team_id"] == team_id)
            team_score = g["home_score"] if is_home else g["away_score"]
            opp_score = g["away_score"] if is_home else g["home_score"]
            won = (team_score > opp_score)
            g_date = pd.to_datetime(g["game_date"]).date()
            
            # Semanas ISO: lunes (0) a domingo (6)
            monday = g_date - timedelta(days=g_date.weekday())
            sunday = monday + timedelta(days=6)
            
            parsed.append({
                "game_pk": g["id"],
                "game_date": g_date,
                "monday": monday,
                "sunday": sunday,
                "won": won,
                "runs_for": team_score or 0,
                "runs_against": opp_score or 0
            })
            
        df = pd.DataFrame(parsed)
        weeks = df[["monday", "sunday"]].drop_duplicates().sort_values("monday").reset_index(drop=True)
        weeks["week_num"] = range(1, len(weeks) + 1)
        
        df = pd.merge(df, weeks, on=["monday", "sunday"])
        
        weekly_summary = []
        for (wn, mon, sun), group in df.groupby(["week_num", "monday", "sunday"], sort=True):
            w = sum(group["won"])
            l = len(group) - w
            pct = w / len(group) if len(group) > 0 else 0
            rf = sum(group["runs_for"])
            ra = sum(group["runs_against"])
            diff = rf - ra
            
            dates_label = f"{mon.strftime('%d/%m')} - {sun.strftime('%d/%m')}"
            week_label = f"Semana {wn} ({dates_label})"
            
            weekly_summary.append({
                "Semana": week_label,
                "semana": week_label,
                "Juegos": len(group),
                "juegos": len(group),
                "G": w,
                "w": w,
                "P": l,
                "l": l,
                "PCT": f".{int(pct*1000):03d}",
                "pct": f".{int(pct*1000):03d}",
                "CF": rf,
                "cf": rf,
                "CP": ra,
                "cp": ra,
                "DIF": f"{diff:+d}" if diff != 0 else "0",
                "dif": f"{diff:+d}" if diff != 0 else "0",
                "Récord": f"{w}G-{l}P",
                "record": f"{w}G-{l}P"
            })
            
        return pd.DataFrame(weekly_summary)
    except Exception as e:
        print(f"Error obteniendo récord semanal: {e}")
        return pd.DataFrame()


@cache_ttl(ttl_seconds=1800)
def get_collective_team_stats(season=None, phase='R', group=None) -> Any:
    """
    Descarga estadísticas colectivas de los 8 equipos de la LVBP vía MLB Stats API.
    Soporta group='hitting' (Bateo), 'pitching' (Pitcheo), 'fielding' (Fildeo) o None/'all'
    (que retorna un diccionario con {'batting': df_bat, 'pitching': df_pitch, 'fielding': df_field}).
    """
    if season is None:
        season = get_current_season()
        
    def _fetch_group(grp: str) -> pd.DataFrame:
        url = f"https://statsapi.mlb.com/api/v1/teams/stats?season={season}&sportIds=17&leagueIds=135&group={grp}&stats=season&gameType={phase}"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                return pd.DataFrame()
            data = r.json()
            stats_list = data.get("stats", [])
            if not stats_list:
                return pd.DataFrame()
            splits = stats_list[0].get("splits", [])
            if not splits:
                return pd.DataFrame()
                
            rows = []
            for s in splits:
                team_info = s.get("team", {})
                tid = team_info.get("id")
                tname = team_info.get("name", "Equipo")
                stat = s.get("stat", {})
                row = {"team_id": tid, "team_name": tname}
                row.update(stat)
                rows.append(row)
                
            return pd.DataFrame(rows)
        except Exception as e:
            print(f"Error obteniendo estadísticas colectivas ({grp}): {e}")
            return pd.DataFrame()

    if group in ['hitting', 'batting']:
        return _fetch_group('hitting')
    elif group == 'pitching':
        return _fetch_group('pitching')
    elif group == 'fielding':
        return _fetch_group('fielding')
    else:
        # group is None or 'all': fetch all three
        df_bat = _fetch_group('hitting')
        df_pitch = _fetch_group('pitching')
        df_field = _fetch_group('fielding')
        return {
            'batting': df_bat,
            'pitching': df_pitch,
            'fielding': df_field
        }


@cache_ttl(ttl_seconds=1800)
def get_individual_fielding_stats(season=None, team_id=None, phase='R') -> pd.DataFrame:
    """
    Descarga estadísticas individuales de fildeo (defensa) vía MLB Stats API.
    Si team_id está presente, filtra por ese equipo (ej: 695 para Leones).
    Retorna DataFrame completo de métricas defensivas para fildeadores y receptores.
    """
    if season is None:
        season = get_current_season()
        
    url = f"https://statsapi.mlb.com/api/v1/stats?stats=season&group=fielding&season={season}&sportId=17&leagueId=135&playerPool=all&gameType={phase}&limit=1000"
    if team_id:
        url += f"&teamId={team_id}"
        
    try:
        r = requests.get(url, timeout=25)
        if r.status_code != 200:
            return pd.DataFrame()
        data = r.json()
        stats_list = data.get("stats", [])
        if not stats_list:
            return pd.DataFrame()
        splits = stats_list[0].get("splits", [])
        if not splits:
            return pd.DataFrame()
            
        rows = []
        for s in splits:
            player_info = s.get("player", {})
            team_info = s.get("team", {})
            pos_info = s.get("position", {})
            stat = s.get("stat", {})
            
            p_id = player_info.get("id")
            p_name = player_info.get("fullName", "Desconocido")
            t_id = team_info.get("id")
            t_name = team_info.get("name", "")
            pos_abbr = pos_info.get("abbreviation", "UT")
            
            def _to_int(val, default=0):
                try:
                    return int(val) if val is not None and str(val).strip() != '' else default
                except (ValueError, TypeError):
                    return default

            def _to_float(val, default=0.0):
                try:
                    return float(val) if val is not None and str(val).strip() != '' else default
                except (ValueError, TypeError):
                    return default

            po = _to_int(stat.get("putOuts", 0))
            a = _to_int(stat.get("assists", 0))
            e = _to_int(stat.get("errors", 0))
            tc = _to_int(stat.get("chances", 0))
            fpct = _to_float(stat.get("fielding", 0.0))
            dp = _to_int(stat.get("doublePlays", 0))
            tp = _to_int(stat.get("triplePlays", 0))
            rf9 = _to_float(stat.get("rangeFactorPer9Inn", 0.0))
            cs = _to_int(stat.get("caughtStealing", 0))
            sb = _to_int(stat.get("stolenBases", 0))
            cs_pct = _to_float(stat.get("caughtStealingPercentage", 0.0))
            pb = _to_int(stat.get("passedBall", 0))
            te = _to_int(stat.get("throwingErrors", 0))

            row = {
                "player_id": p_id,
                "player_name": p_name,
                "team_id": t_id,
                "team_name": t_name,
                "position": pos_abbr,
                "games": _to_int(stat.get("gamesPlayed", 0)),
                "games_started": _to_int(stat.get("gamesStarted", 0)),
                "innings": str(stat.get("innings", "0.0")),
                "putouts": po,
                "po": po,
                "assists": a,
                "a": a,
                "errors": e,
                "e": e,
                "chances": tc,
                "tc": tc,
                "fielding_pct": fpct,
                "fpct": fpct,
                "double_plays": dp,
                "dp": dp,
                "triple_plays": tp,
                "tp": tp,
                "range_factor_per_9": rf9,
                "rf9": rf9,
                "caught_stealing": cs,
                "cs": cs,
                "stolen_bases": sb,
                "sb": sb,
                "caught_stealing_pct": cs_pct,
                "cs_pct": cs_pct,
                "passed_balls": pb,
                "pb": pb,
                "throwing_errors": te
            }
            rows.append(row)
            
        df = pd.DataFrame(rows)
        return df
    except Exception as e:
        print(f"Error obteniendo estadísticas defensivas individuales: {e}")
        return pd.DataFrame()















