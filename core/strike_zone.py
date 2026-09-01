# core/strike_zone.py
"""
Motor Sabermétrico de Visualización de Zona de Strike 3x3 y Métricas Avanzadas
de Disciplina en el Plato (O-Swing%, Z-Swing%, Z-Contact%, Whiff%, CSW%, SwStr%).
"""
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Dict, Optional, Any
from core.cache import cache_ttl

LEONES_TEAM_ID = 695

CALL_TRANSLATIONS = {
    "Ball": "Bola",
    "Ball In Dirt": "Bola en tierra",
    "Called Strike": "Strike cantado",
    "Swinging Strike": "Swing y abanicado (Whiff)",
    "Swinging Strike (Blocked)": "Swing abanicado (Bloqueado)",
    "Foul": "Foul",
    "Foul Tip": "Foul Tip (Abanicado)",
    "Foul Bunt": "Foul de toque",
    "Missed Bunt": "Toque fallido (Whiff)",
    "In play, out(s)": "En juego (Out)",
    "In play, no out": "En juego (Hit/Safe)",
    "In play, run(s)": "En juego (Carrera anotada)",
    "Hit By Pitch": "Golpeado por lanzamiento",
    "Automatic Ball": "Bola automática",
    "Automatic Strike": "Strike automático"
}

CALL_COLORS = {
    "Whiff": "#e74c3c",          # Rojo brillante
    "Called Strike": "#f39c12",  # Ámbar / Naranja
    "Foul": "#3498db",           # Azul
    "In Play": "#2ecc71",        # Verde
    "Ball": "rgba(149, 165, 166, 0.6)", # Gris suave
    "Other": "#9b59b6"
}


def convert_pitch_coordinates(x_raw: float, y_raw: float, sz_top: float = 3.4, sz_bot: float = 1.5) -> Tuple[float, float]:
    """
    Convierte coordenadas de pitch Gameday a pies centrados en home plate.
    Calibración empírica exacta:
    - Centro horizontal del plato: x0 = 110.0 (ancho de zona 17 in = 1.417 ft -> 35 unidades)
    - Altura vertical: top de zona y=136, bottom de zona y=176 (40 unidades)
    Retorna (x_ft, z_ft).
    """
    if x_raw is None or y_raw is None:
        return 0.0, 2.5
    
    top = float(sz_top) if sz_top and not np.isnan(sz_top) else 3.4
    bot = float(sz_bot) if sz_bot and not np.isnan(sz_bot) else 1.5
    
    # 35 unidades en Gameday ~ ancho del home plate (17 in = 1.417 ft)
    x_ft = (float(x_raw) - 110.0) * (1.417 / 35.0)
    
    # 40 unidades de altura en Gameday ~ altura de zona (y=136 top, y=176 bot)
    z_ft = bot + (top - bot) * ((176.0 - float(y_raw)) / 40.0)
    
    return round(x_ft, 2), round(z_ft, 2)


def classify_pitch_event(call_desc: str) -> Dict[str, Any]:
    """Clasifica el pitcheo en indicadores sabermétricos de disciplina."""
    desc = str(call_desc)
    
    is_whiff = desc in ["Swinging Strike", "Swinging Strike (Blocked)", "Foul Tip", "Missed Bunt"]
    is_foul = desc in ["Foul", "Foul Bunt"]
    is_in_play = desc.startswith("In play")
    is_called_strike = desc == "Called Strike"
    is_ball = desc.startswith("Ball") or desc in ["Hit By Pitch", "Automatic Ball"]
    
    is_swing = is_whiff or is_foul or is_in_play
    is_contact = is_foul or is_in_play
    is_strike = is_called_strike or is_swing
    
    if is_whiff:
        group = "Whiff"
    elif is_called_strike:
        group = "Called Strike"
    elif is_foul:
        group = "Foul"
    elif is_in_play:
        group = "In Play"
    elif is_ball:
        group = "Ball"
    else:
        group = "Other"
        
    return {
        "call_group": group,
        "is_swing": is_swing,
        "is_whiff": is_whiff,
        "is_contact": is_contact,
        "is_called_strike": is_called_strike,
        "is_ball": is_ball,
        "is_strike": is_strike
    }


def fetch_single_game_pitches(game_pk: int) -> List[Dict[str, Any]]:
    """Descarga y estructura todos los pitcheos de un juego."""
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
        for play in plays:
            matchup = play.get("matchup", {})
            batter = matchup.get("batter", {})
            pitcher = matchup.get("pitcher", {})
            bat_side = matchup.get("batSide", {}).get("code", "R")
            pitch_hand = matchup.get("pitchHand", {}).get("code", "R")
            
            about = play.get("about", {})
            inning = about.get("inning", 1)
            half = about.get("halfInning", "top")
            at_bat_index = play.get("atBatIndex", about.get("atBatIndex", 0))
            result = play.get("result", {})
            play_event = result.get("event", "En juego")
            play_desc = result.get("description", "")
            
            batter_team_id = away_id if half == "top" else home_id
            pitcher_team_id = home_id if half == "top" else away_id
            
            for ev in play.get("playEvents", []):
                if ev.get("isPitch"):
                    pitch_number = ev.get("pitchNumber", 1)
                    details = ev.get("details", {})
                    call_desc = details.get("description", "")
                    pitch_type = details.get("type", {}).get("description", "Sin dato")
                    
                    pdata = ev.get("pitchData", {})
                    coords = pdata.get("coordinates", {})
                    x_raw = coords.get("x")
                    y_raw = coords.get("y")
                    
                    sz_top = pdata.get("strikeZoneTop", 3.4)
                    sz_bot = pdata.get("strikeZoneBottom", 1.5)
                    
                    if x_raw is not None and y_raw is not None:
                        x_ft, z_ft = convert_pitch_coordinates(x_raw, y_raw, sz_top, sz_bot)
                        
                        # Definición de en zona: |x| <= 0.83 ft (~10 in de centro), sz_bot <= z <= sz_top
                        in_zone = (abs(x_ft) <= 0.83) and (sz_bot <= z_ft <= sz_top)
                        
                        # Clasificación de zona 1 a 9 o fuera
                        zone_num = "Fuera"
                        if in_zone:
                            # Tercio horizontal
                            if x_ft < -0.28:
                                col = 0
                            elif x_ft > 0.28:
                                col = 2
                            else:
                                col = 1
                            # Tercio vertical
                            z_range = sz_top - sz_bot
                            if z_ft > sz_bot + 2 * z_range / 3:
                                row = 0  # Alta
                            elif z_ft < sz_bot + z_range / 3:
                                row = 2  # Baja
                            else:
                                row = 1  # Media
                            zone_num = str(row * 3 + col + 1)
                            
                        flags = classify_pitch_event(call_desc)
                        
                        count = ev.get("count", {})
                        balls = count.get("balls", 0)
                        strikes = count.get("strikes", 0)
                        
                        batter_name = batter.get("fullName", "Desconocido")
                        pitcher_name = pitcher.get("fullName", "Desconocido")
                        is_batter_leones = (batter_team_id == LEONES_TEAM_ID)
                        opponent_name = pitcher_name if is_batter_leones else batter_name
                        
                        records.append({
                            "game_pk": game_pk,
                            "game_date": game_date,
                            "home_team": home_team,
                            "away_team": away_team,
                            "at_bat_index": at_bat_index,
                            "pitch_number": pitch_number,
                            "play_event": play_event,
                            "play_desc": play_desc,
                            "inning": inning,
                            "half": half,
                            "batter_id": batter.get("id"),
                            "batter_name": batter_name,
                            "batter_team_id": batter_team_id,
                            "is_batter_leones": is_batter_leones,
                            "bat_side": bat_side,
                            "pitcher_id": pitcher.get("id"),
                            "pitcher_name": pitcher_name,
                            "pitcher_team_id": pitcher_team_id,
                            "is_pitcher_leones": (pitcher_team_id == LEONES_TEAM_ID),
                            "opponent_name": opponent_name,
                            "pitch_hand": pitch_hand,
                            "pitch_type": pitch_type,
                            "call_desc": call_desc,
                            "call_es": CALL_TRANSLATIONS.get(call_desc, call_desc),
                            "call_group": flags["call_group"],
                            "is_swing": flags["is_swing"],
                            "is_whiff": flags["is_whiff"],
                            "is_contact": flags["is_contact"],
                            "is_called_strike": flags["is_called_strike"],
                            "is_ball": flags["is_ball"],
                            "is_strike": flags["is_strike"],
                            "in_zone": in_zone,
                            "zone_num": zone_num,
                            "balls": balls,
                            "strikes": strikes,
                            "count_str": f"{balls}-{strikes}",
                            "x_ft": x_ft,
                            "z_ft": z_ft,
                            "sz_top": round(sz_top, 2),
                            "sz_bot": round(sz_bot, 2)
                        })
        return records
    except Exception:
        return []


@cache_ttl(ttl_seconds=1800)
def fetch_season_pitches(season: int, team_id: int = LEONES_TEAM_ID, cache_version: str = "v3_at_bats_opponents") -> pd.DataFrame:
    """Descarga todos los lanzamientos de la temporada con multithreading."""
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
        results = list(executor.map(fetch_single_game_pitches, game_pks))
        
    all_records = [item for sublist in results for item in sublist]
    if not all_records:
        return pd.DataFrame()
        
    return pd.DataFrame(all_records)


def calculate_discipline_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula todas las métricas avanzadas de disciplina en el plato."""
    if df.empty:
        return {
            "total_pitches": 0, "zone_pct": 0.0, "swing_pct": 0.0,
            "o_swing_pct": 0.0, "z_swing_pct": 0.0, "contact_pct": 0.0,
            "z_contact_pct": 0.0, "o_contact_pct": 0.0, "whiff_pct": 0.0,
            "swstr_pct": 0.0, "csw_pct": 0.0
        }
        
    n = len(df)
    in_zone_col = "in_zone" if "in_zone" in df.columns else ("is_in_zone" if "is_in_zone" in df.columns else None)
    if in_zone_col:
        in_zone_df = df[df[in_zone_col] == True]
        out_zone_df = df[df[in_zone_col] == False]
    elif "x_ft" in df.columns and "z_ft" in df.columns:
        in_zone_mask = (df["x_ft"].abs() <= 0.85) & (df["z_ft"] >= 1.5) & (df["z_ft"] <= 3.5)
        in_zone_df = df[in_zone_mask]
        out_zone_df = df[~in_zone_mask]
    else:
        in_zone_df = pd.DataFrame()
        out_zone_df = pd.DataFrame()
        
    n_in_zone = len(in_zone_df)
    n_out_zone = len(out_zone_df)
    
    is_swing_col = "is_swing" if "is_swing" in df.columns else ("swing" if "swing" in df.columns else None)
    swings = df[df[is_swing_col] == True] if is_swing_col else pd.DataFrame()
    n_swings = len(swings)
    
    is_whiff_col = "is_whiff" if "is_whiff" in df.columns else ("whiff" if "whiff" in df.columns else None)
    whiffs = df[df[is_whiff_col] == True] if is_whiff_col else pd.DataFrame()
    n_whiffs = len(whiffs)
    
    is_cs_col = "is_called_strike" if "is_called_strike" in df.columns else ("called_strike" if "called_strike" in df.columns else None)
    called_strikes = df[df[is_cs_col] == True] if is_cs_col else pd.DataFrame()
    n_called_strikes = len(called_strikes)
    
    # O-Swing: Swings fuera de zona / Pitcheos fuera de zona
    o_swings = out_zone_df[out_zone_df[is_swing_col] == True] if is_swing_col and not out_zone_df.empty else pd.DataFrame()
    o_swing_pct = (len(o_swings) / n_out_zone * 100) if n_out_zone > 0 else 0.0
    
    # Z-Swing: Swings en zona / Pitcheos en zona
    z_swings = in_zone_df[in_zone_df[is_swing_col] == True] if is_swing_col and not in_zone_df.empty else pd.DataFrame()
    z_swing_pct = (len(z_swings) / n_in_zone * 100) if n_in_zone > 0 else 0.0
    
    # Contact%: Contactos / Swings
    is_contact_col = "is_contact" if "is_contact" in df.columns else ("contact" if "contact" in df.columns else None)
    contacts = df[df[is_contact_col] == True] if is_contact_col else pd.DataFrame()
    contact_pct = (len(contacts) / n_swings * 100) if n_swings > 0 else 0.0
    
    # Z-Contact%: Contacto en zona / Swings en zona
    z_contacts = in_zone_df[in_zone_df[is_contact_col] == True] if is_contact_col and not in_zone_df.empty else pd.DataFrame()
    z_contact_pct = (len(z_contacts) / len(z_swings) * 100) if len(z_swings) > 0 else 0.0
    
    # O-Contact%: Contacto fuera de zona / Swings fuera de zona
    o_contacts = out_zone_df[out_zone_df[is_contact_col] == True] if is_contact_col and not out_zone_df.empty else pd.DataFrame()
    o_contact_pct = (len(o_contacts) / len(o_swings) * 100) if len(o_swings) > 0 else 0.0
    
    # Whiff%: Whiffs / Swings
    whiff_pct = (n_whiffs / n_swings * 100) if n_swings > 0 else 0.0
    
    # SwStr%: Whiffs / Pitcheos totales
    swstr_pct = (n_whiffs / n * 100) if n > 0 else 0.0
    
    # CSW%: (Called Strikes + Whiffs) / Pitcheos totales
    csw_pct = ((n_called_strikes + n_whiffs) / n * 100) if n > 0 else 0.0
    
    # Zone%: Pitcheos en zona / Pitcheos totales
    zone_pct = (n_in_zone / n * 100) if n > 0 else 0.0
    
    # Swing%: Swings / Pitcheos totales
    swing_pct = (n_swings / n * 100) if n > 0 else 0.0
    
    return {
        "total_pitches": n,
        "zone_pct": round(zone_pct, 1),
        "swing_pct": round(swing_pct, 1),
        "o_swing_pct": round(o_swing_pct, 1),
        "z_swing_pct": round(z_swing_pct, 1),
        "contact_pct": round(contact_pct, 1),
        "z_contact_pct": round(z_contact_pct, 1),
        "o_contact_pct": round(o_contact_pct, 1),
        "whiff_pct": round(whiff_pct, 1),
        "swstr_pct": round(swstr_pct, 1),
        "csw_pct": round(csw_pct, 1)
    }


def create_strike_zone_figure(
    df: pd.DataFrame,
    title_player: str = "Leones del Caracas",
    rol_view: str = "Bateadores de Leones",
    show_sequence_numbers: bool = False
) -> go.Figure:
    """Genera la figura de Zona de Strike con cuadrícula 3x3 y lanzamientos con detalle de rival y turno."""
    fig = go.Figure()
    
    # Dimensiones estándar de zona en pies
    x_min, x_max = -0.83, 0.83
    z_min, z_max = 1.5, 3.4
    
    # 1. Zona de Sombra Exterior (Shadow Zone)
    fig.add_shape(
        type="rect",
        x0=x_min - 0.28, x1=x_max + 0.28,
        y0=z_min - 0.28, y1=z_max + 0.28,
        line=dict(color="rgba(148, 163, 184, 0.3)", width=1, dash="dash"),
        fillcolor="rgba(30, 41, 59, 0.3)",
        layer="below"
    )
    
    # 2. Caja de Strike Zone Oficial (Solid White)
    fig.add_shape(
        type="rect",
        x0=x_min, x1=x_max,
        y0=z_min, y1=z_max,
        line=dict(color="#ffffff", width=2.5),
        fillcolor="rgba(15, 23, 42, 0.4)",
        layer="below"
    )
    
    # 3. Líneas de Cuadrícula 3x3
    dx = (x_max - x_min) / 3.0
    dz = (z_max - z_min) / 3.0
    
    # Verticales internas
    fig.add_shape(type="line", x0=x_min + dx, x1=x_min + dx, y0=z_min, y1=z_max, line=dict(color="rgba(255, 255, 255, 0.35)", width=1, dash="dot"))
    fig.add_shape(type="line", x0=x_min + 2*dx, x1=x_min + 2*dx, y0=z_min, y1=z_max, line=dict(color="rgba(255, 255, 255, 0.35)", width=1, dash="dot"))
    
    # Horizontales internas
    fig.add_shape(type="line", x0=x_min, x1=x_max, y0=z_min + dz, y1=z_min + dz, line=dict(color="rgba(255, 255, 255, 0.35)", width=1, dash="dot"))
    fig.add_shape(type="line", x0=x_min, x1=x_max, y0=z_min + 2*dz, y1=z_min + 2*dz, line=dict(color="rgba(255, 255, 255, 0.35)", width=1, dash="dot"))
    
    # 4. Pentágono de Home Plate (al fondo z = 0.5 ft)
    plate_x = [-0.71, 0.71, 0.71, 0, -0.71, -0.71]
    plate_z = [0.8, 0.8, 0.6, 0.3, 0.6, 0.8]
    fig.add_trace(go.Scatter(
        x=plate_x,
        y=plate_z,
        fill="toself",
        fillcolor="rgba(255, 255, 255, 0.8)",
        line=dict(color="#ffffff", width=1.5),
        hoverinfo="skip",
        showlegend=False,
        name="Home Plate"
    ))
    
    if df.empty:
        fig.update_layout(
            title=dict(text=f"Zona de Strike: {title_player} (Sin datos)", font=dict(size=18)),
            template="plotly_dark",
            height=620
        )
        return fig
        
    # Preparar campos seguros
    play_events = df["play_event"] if "play_event" in df.columns else pd.Series([""] * len(df))
    pitch_nums = df["pitch_number"] if "pitch_number" in df.columns else pd.Series([1] * len(df))
    
    # Preparar Customdata para hover
    customdata = np.stack((
        df["batter_name"],
        df["pitcher_name"],
        df["call_es"],
        df["count_str"],
        df["inning"],
        df["game_date"],
        df["pitch_type"],
        df["x_ft"],
        df["z_ft"],
        play_events,
        pitch_nums
    ), axis=-1)
    
    if rol_view == "Bateadores de Leones":
        hovertemplate = (
            "<b>🦁 Bateador:</b> %{customdata[0]}<br>"
            "<b>⚾ Lanzador que lanzaba:</b> %{customdata[1]}<br>"
            "<b>🎯 Turno:</b> Inning %{customdata[4]} (%{customdata[9]}) | <b>Pitcheo #:</b> %{customdata[10]}<br>"
            "<b>Resultado:</b> %{customdata[2]}<br>"
            "<b>Cuenta:</b> %{customdata[3]}<br>"
            "<b>Fecha:</b> %{customdata[5]}<br>"
            "<b>Tipo Pitcheo:</b> %{customdata[6]}<br>"
            "<b>Ubicación:</b> X=%{customdata[7]} ft, Z=%{customdata[8]} ft"
            "<extra></extra>"
        )
    else:
        hovertemplate = (
            "<b>🦁 Lanzador:</b> %{customdata[1]}<br>"
            "<b>🏏 Bateador contrario:</b> %{customdata[0]}<br>"
            "<b>🎯 Enfrentamiento:</b> Inning %{customdata[4]} (%{customdata[9]}) | <b>Pitcheo #:</b> %{customdata[10]}<br>"
            "<b>Resultado:</b> %{customdata[2]}<br>"
            "<b>Cuenta:</b> %{customdata[3]}<br>"
            "<b>Fecha:</b> %{customdata[5]}<br>"
            "<b>Tipo Pitcheo:</b> %{customdata[6]}<br>"
            "<b>Ubicación:</b> X=%{customdata[7]} ft, Z=%{customdata[8]} ft"
            "<extra></extra>"
        )
    
    # Trazar puntos agrupados por llamada
    groups = [
        ("Whiff", "Swing y Abanicado (Whiff)", "#e74c3c", 11, "circle"),
        ("Called Strike", "Strike Cantado", "#f39c12", 10, "diamond"),
        ("In Play", "En Juego (Contacto)", "#2ecc71", 10, "square"),
        ("Foul", "Foul", "#3498db", 9, "triangle-up"),
        ("Ball", "Bola", "rgba(148, 163, 184, 0.65)", 8, "circle-open")
    ]
    
    is_single_turn = (show_sequence_numbers or len(df) <= 12)
    
    for group_key, label, color, size, symbol in groups:
        sub_df = df[df["call_group"] == group_key]
        if not sub_df.empty:
            sub_customdata = customdata[df["call_group"] == group_key]
            
            trace_kwargs = dict(
                x=sub_df["x_ft"],
                y=sub_df["z_ft"],
                name=f"{label} ({len(sub_df)})",
                marker=dict(
                    size=size if not is_single_turn else size + 4,
                    color=color,
                    symbol=symbol,
                    line=dict(width=1.2, color="#ffffff" if group_key != "Ball" else "rgba(255,255,255,0.3)")
                ),
                customdata=sub_customdata,
                hovertemplate=hovertemplate
            )
            
            if is_single_turn and "pitch_number" in sub_df.columns:
                trace_kwargs["mode"] = "markers+text"
                trace_kwargs["text"] = sub_df["pitch_number"].astype(str)
                trace_kwargs["textposition"] = "middle center"
                trace_kwargs["textfont"] = dict(color="#ffffff", size=10, family="Arial Black")
            else:
                trace_kwargs["mode"] = "markers"
                
            fig.add_trace(go.Scatter(**trace_kwargs))
            
    fig.update_layout(
        title=dict(
            text=f"🎯 Localización de Pitcheos: {title_player} ({len(df)} lanzamientos)",
            font=dict(size=17, color="#ffffff"),
            x=0.05
        ),
        xaxis=dict(
            range=[-2.0, 2.0],
            showgrid=False,
            zeroline=False,
            showticklabels=True,
            title="Lado del Plato (Pies)",
            fixedrange=True
        ),
        yaxis=dict(
            range=[0.0, 4.5],
            showgrid=False,
            zeroline=False,
            showticklabels=True,
            title="Altura sobre el Suelo (Pies)",
            fixedrange=True
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.95)",
        plot_bgcolor="rgba(15, 23, 42, 0.95)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        height=620,
        margin=dict(l=20, r=20, t=50, b=60)
    )
    
    return fig


def generate_strike_zone_figure(df_pitches: pd.DataFrame, player_name: str = "Leones del Caracas") -> go.Figure:
    """Alias para compatibilidad con la interfaz generate_strike_zone_figure."""
    return create_strike_zone_figure(df_pitches, title_player=player_name)
