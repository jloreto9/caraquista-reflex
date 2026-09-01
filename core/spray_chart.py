# core/spray_chart.py
"""
Motor Sabermétrico de Spray Charts espaciales en diamante con modelo determinístico
de dureza BIS (Hard, Medium, Soft) y calibración geométrica de coordenadas MLB Gameday.
"""
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Dict, Optional, Any
from core.cache import cache_ttl

LEONES_TEAM_ID = 695

EVENT_TRANSLATIONS = {
    "Single": "Sencillo (1B)",
    "Double": "Doble (2B)",
    "Triple": "Triple (3B)",
    "Home Run": "Jonrón (HR)",
    "Flyout": "Elevado de out",
    "Groundout": "Rolling de out",
    "Lineout": "Línea de out",
    "Pop Out": "Foul/Pop out",
    "Forceout": "Out forzado",
    "Field Error": "Error de fildeo",
    "Sac Fly": "Elevado de sacrificio",
    "Sac Bunt": "Toque de sacrificio",
    "Fielders Choice": "Selección del fildeador",
    "Fielders Choice Out": "Out en jugada de selección",
    "Double Play": "Doble Play",
    "Grounded Into DP": "Rolling para Doble Play",
    "Sac Fly Double Play": "Sac Fly + DP"
}

EVENT_COLORS = {
    "Single": "#2ecc71",       # Verde
    "Double": "#3498db",       # Azul
    "Triple": "#f39c12",       # Naranja / Oro
    "Home Run": "#e74c3c",     # Rojo
    "Out": "#95a5a6",          # Gris
    "Field Error": "#9b59b6",  # Morado
    "Other": "#bdc3c7"
}

TRAJECTORY_TRANSLATIONS = {
    "ground_ball": "Rolling (GB)",
    "line_drive": "Línea (LD)",
    "fly_ball": "Elevado (FB)",
    "popup": "Pop up (PU)",
    "unknown": "Sin dato"
}

HARDNESS_TRANSLATIONS = {
    "hard": "Fuerte (Hard)",
    "medium": "Medio (Medium)",
    "soft": "Suave (Soft)",
    "unknown": "Sin dato"
}


def transform_coordinates(coord_x: float, coord_y: float) -> Tuple[float, float, float, float]:
    """
    Convierte coordenadas de MLB Gameday (250x250) a pies en el campo de béisbol.
    Home plate en (125, 204.5)
    Retorna: (x_ft, y_ft, distancia_ft, angulo_deg)
    """
    if coord_x is None or coord_y is None:
        return 0.0, 0.0, 0.0, 0.0
    
    # Transformación a pies (escala estándar MLB Gameday ~2.5 ft/unit)
    x_ft = (float(coord_x) - 125.0) * 2.5
    y_ft = (204.5 - float(coord_y)) * 2.5
    
    dist_ft = float(np.sqrt(x_ft**2 + y_ft**2))
    # Ángulo en grados (-45 = línea 3B / LF, 0 = 2B / CF, +45 = línea 1B / RF)
    angle_deg = float(np.degrees(np.arctan2(x_ft, y_ft)))
    
    return x_ft, y_ft, dist_ft, angle_deg


def classify_direction(angle_deg: float, bat_side: str) -> str:
    """
    Clasifica el batazo en Pull, Center u Oppo según la mano del bateador.
    """
    side = str(bat_side).upper() if bat_side else "R"
    if side == "R":
        if angle_deg < -15.0:
            return "Pull (Hacia LF)"
        elif angle_deg > 15.0:
            return "Oppo (Hacia RF)"
        else:
            return "Center (Centro)"
    else:  # Bateador zurdo (L)
        if angle_deg > 15.0:
            return "Pull (Hacia RF)"
        elif angle_deg < -15.0:
            return "Oppo (Hacia LF)"
        else:
            return "Center (Centro)"


def classify_batted_ball_hardness(event: str, trajectory: str, dist_ft: float, raw_hardness: str) -> str:
    """
    Clasifica la dureza del contacto (hard, medium, soft) basada en el modelo sabermétrico BIS.
    Corrige el sesgo de la API de MLB que asigna 'medium' a >90% de los batazos en la LVBP.
    """
    raw = str(raw_hardness).lower() if raw_hardness else "unknown"
    traj = str(trajectory).lower() if trajectory else "unknown"
    ev = str(event) if event else "Out"

    # 1. Extremos indiscutibles de poder
    if ev in ["Home Run", "Triple"]:
        return "hard"
    if ev == "Double" and traj != "popup":
        return "hard"
    if raw == "hard":
        return "hard"

    # 2. Contacto Débil / Suave (Soft)
    if traj in ["popup", "bunt_grounder", "bunt_line_drive", "bunt_popup"] or "Bunt" in ev or "Pop Out" in ev:
        return "soft"
    if raw == "soft":
        return "soft"
    if traj == "fly_ball" and dist_ft < 185:
        return "soft"
    if traj == "ground_ball" and dist_ft < 85 and ev in ["Groundout", "Forceout", "Double Play", "Grounded Into DP", "Fielders Choice", "Fielders Choice Out"]:
        return "soft"

    # 3. Contacto Fuerte (Hard)
    if traj == "line_drive":
        if dist_ft >= 200 or ev in ["Double", "Triple", "Home Run"] or (ev == "Single" and dist_ft >= 150):
            return "hard"
    if traj == "fly_ball" and dist_ft >= 310:
        return "hard"
    if traj == "ground_ball" and dist_ft >= 155:
        return "hard"

    # 4. Contacto Medio (Medium)
    return "medium"


def fetch_single_game_batted_balls(game_pk: int) -> List[Dict[str, Any]]:
    """Extrae todos los batazos en juego de un partido específico."""
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
            
            # Identificar equipo del bateador
            batter_team_id = away_id if half == "top" else home_id
            batter_team_name = away_team if half == "top" else home_team
            opposing_team_name = home_team if half == "top" else away_team
            
            result = play.get("result", {})
            event = result.get("event", "Out")
            desc = result.get("description", "")
            rbi = result.get("rbi", 0)
            
            for ev in play.get("playEvents", []):
                hit = ev.get("hitData")
                if hit and hit.get("coordinates") and "coordX" in hit["coordinates"]:
                    coords = hit["coordinates"]
                    cx = coords.get("coordX")
                    cy = coords.get("coordY")
                    if cx is not None and cy is not None and (cx != 0 or cy != 0):
                        x_ft, y_ft, dist_ft, angle_deg = transform_coordinates(cx, cy)
                        direction = classify_direction(angle_deg, bat_side)
                        
                        is_hit = event in ["Single", "Double", "Triple", "Home Run"]
                        
                        # Agrupación de evento para color
                        if event in ["Single", "Double", "Triple", "Home Run", "Field Error"]:
                            event_group = event
                        else:
                            event_group = "Out"
                            
                        raw_hardness = hit.get("hardness", "medium")
                        calibrated_hardness = classify_batted_ball_hardness(
                            event=event,
                            trajectory=hit.get("trajectory", "unknown"),
                            dist_ft=dist_ft,
                            raw_hardness=raw_hardness
                        )
                            
                        records.append({
                            "game_pk": game_pk,
                            "game_date": game_date,
                            "home_team": home_team,
                            "away_team": away_team,
                            "inning": inning,
                            "half": half,
                            "batter_id": batter.get("id"),
                            "batter_name": batter.get("fullName", "Desconocido"),
                            "batter_team_id": batter_team_id,
                            "batter_team": batter_team_name,
                            "opposing_team": opposing_team_name,
                            "is_leones": (batter_team_id == LEONES_TEAM_ID),
                            "bat_side": bat_side,
                            "pitcher_id": pitcher.get("id"),
                            "pitcher_name": pitcher.get("fullName", "Desconocido"),
                            "pitch_hand": pitch_hand,
                            "event": event,
                            "event_group": event_group,
                            "event_es": EVENT_TRANSLATIONS.get(event, event),
                            "is_hit": is_hit,
                            "description": desc,
                            "rbi": rbi,
                            "coord_x": cx,
                            "coord_y": cy,
                            "x_ft": round(x_ft, 1),
                            "y_ft": round(y_ft, 1),
                            "distance_ft": round(dist_ft, 1),
                            "spray_angle": round(angle_deg, 1),
                            "direction": direction,
                            "trajectory": hit.get("trajectory", "unknown"),
                            "trajectory_es": TRAJECTORY_TRANSLATIONS.get(hit.get("trajectory", "unknown"), "Sin dato"),
                            "hardness": calibrated_hardness,
                            "hardness_es": HARDNESS_TRANSLATIONS.get(calibrated_hardness, "Sin dato"),
                            "launch_speed": hit.get("launchSpeed"),
                            "total_distance": hit.get("totalDistance")
                        })
        return records
    except Exception:
        return []


@cache_ttl(ttl_seconds=1800)
def fetch_season_batted_balls(season: int, team_id: int = LEONES_TEAM_ID) -> pd.DataFrame:
    """
    Descarga y estructura todos los batazos de la temporada para el equipo indicado.
    Utiliza multithreading para máxima velocidad.
    """
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
        
    # Extracción en paralelo con 10 threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_single_game_batted_balls, game_pks))
        
    all_records = [item for sublist in results for item in sublist]
    if not all_records:
        return pd.DataFrame()
        
    df = pd.DataFrame(all_records)
    return df


def build_baseball_field_figure() -> go.Figure:
    """
    Construye el lienzo base del estadio de béisbol con proporciones geométricas exactas.
    """
    fig = go.Figure()
    
    # 1. Barda del outfield (arco de 330 ft en postes a 400 ft en CF)
    theta_wall = np.linspace(-np.pi/4, np.pi/4, 100)
    r_wall = 400 - 70 * (theta_wall / (np.pi/4))**2
    x_wall = r_wall * np.sin(theta_wall)
    y_wall = r_wall * np.cos(theta_wall)
    
    # Barda exterior (polígono de campo verde)
    x_field = [0] + x_wall.tolist() + [0]
    y_field = [0] + y_wall.tolist() + [0]
    
    fig.add_trace(go.Scatter(
        x=x_field,
        y=y_field,
        fill="toself",
        fillcolor="rgba(34, 139, 34, 0.15)",  # Verde césped sutil
        line=dict(color="#1e824c", width=2.5),
        hoverinfo="skip",
        showlegend=False,
        name="Campo"
    ))
    
    # 2. Líneas de foul (LF y RF)
    r_foul = 335
    x_rf = r_foul * np.sin(np.pi/4)
    y_rf = r_foul * np.cos(np.pi/4)
    x_lf = -r_foul * np.sin(np.pi/4)
    y_lf = r_foul * np.cos(np.pi/4)
    
    fig.add_trace(go.Scatter(
        x=[x_lf, 0, x_rf],
        y=[y_lf, 0, y_rf],
        mode="lines",
        line=dict(color="#ffffff", width=2.5),
        hoverinfo="skip",
        showlegend=False,
        name="Líneas de Foul"
    ))
    
    # 3. Arco de tierra del Infield (radio 95 ft centrado en el montículo y=60.5)
    theta_inf = np.linspace(-np.pi/3, np.pi/3, 50)
    x_inf = 95 * np.sin(theta_inf)
    y_inf = 60.5 + 95 * np.cos(theta_inf)
    
    fig.add_trace(go.Scatter(
        x=x_inf,
        y=y_inf,
        mode="lines",
        line=dict(color="rgba(210, 140, 70, 0.4)", width=2, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
        name="Arco Infield"
    ))
    
    # 4. Diamante y bases
    # Home: (0,0), 1B: (63.64, 63.64), 2B: (0, 127.28), 3B: (-63.64, 63.64)
    diamond_x = [0, 63.64, 0, -63.64, 0]
    diamond_y = [0, 63.64, 127.28, 63.64, 0]
    
    fig.add_trace(go.Scatter(
        x=diamond_x,
        y=diamond_y,
        mode="lines+markers",
        line=dict(color="#ffffff", width=2),
        marker=dict(size=[12, 10, 10, 10, 12], color=["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"], symbol=["pentagon", "square", "square", "square", "pentagon"]),
        hoverinfo="skip",
        showlegend=False,
        name="Bases"
    ))
    
    # 5. Montículo de pitcheo (0, 60.5)
    fig.add_trace(go.Scatter(
        x=[0],
        y=[60.5],
        mode="markers",
        marker=dict(size=8, color="#d35400", symbol="circle"),
        hoverinfo="skip",
        showlegend=False,
        name="Montículo"
    ))
    
    # Anotaciones de distancia
    fig.add_annotation(x=0, y=405, text="400 ft", showarrow=False, font=dict(color="#aaaaaa", size=11))
    fig.add_annotation(x=x_lf - 10, y=y_lf + 10, text="330 ft", showarrow=False, font=dict(color="#aaaaaa", size=11))
    fig.add_annotation(x=x_rf + 10, y=y_rf + 10, text="330 ft", showarrow=False, font=dict(color="#aaaaaa", size=11))
    
    return fig


def create_spray_chart_figure(
    df: pd.DataFrame,
    player_name: str = "Leones del Caracas",
    color_mode: str = "event"
) -> go.Figure:
    """
    Genera el Spray Chart interactivo completo con puntos y hover personalizado.
    """
    fig = build_baseball_field_figure()
    
    if df.empty:
        fig.update_layout(
            title=dict(text=f"Spray Chart: {player_name} (Sin datos)", font=dict(size=18)),
            xaxis=dict(range=[-260, 260], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[-20, 440], showgrid=False, zeroline=False, visible=False),
            template="plotly_dark",
            height=650,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        return fig
        
    # Preparar datos para hover
    customdata = np.stack((
        df["batter_name"],
        df["bat_side"],
        df["event_es"],
        df["pitcher_name"],
        df["pitch_hand"],
        df["opposing_team"],
        df["game_date"],
        df["distance_ft"],
        df["trajectory_es"],
        df["hardness_es"],
        df["description"],
        df["inning"]
    ), axis=-1)
    
    hovertemplate = (
        "<b>%{customdata[0]}</b> (Batea: %{customdata[1]})<br>"
        "<b>Resultado:</b> %{customdata[2]}<br>"
        "<b>Lanzador:</b> %{customdata[3]} (%{customdata[4]})<br>"
        "<b>Rival:</b> %{customdata[5]} | <b>Inning:</b> %{customdata[11]}<br>"
        "<b>Fecha:</b> %{customdata[6]}<br>"
        "<b>Distancia:</b> %{customdata[7]} ft<br>"
        "<b>Contacto:</b> %{customdata[8]} | %{customdata[9]}<br>"
        "<i>%{customdata[10]}</i>"
        "<extra></extra>"
    )
    
    # Colorear por evento o por trayectoria
    if color_mode == "event":
        groups = [
            ("Home Run", "Jonrón (HR)", "#e74c3c", 13, "star"),
            ("Triple", "Triple (3B)", "#f39c12", 11, "diamond"),
            ("Double", "Doble (2B)", "#3498db", 10, "square"),
            ("Single", "Sencillo (1B)", "#2ecc71", 9, "circle"),
            ("Field Error", "Error", "#9b59b6", 8, "cross"),
            ("Out", "Out", "rgba(189, 195, 199, 0.75)", 7, "circle-open")
        ]
        
        for event_key, label, color, size, symbol in groups:
            sub_df = df[df["event_group"] == event_key]
            if not sub_df.empty:
                sub_customdata = customdata[df["event_group"] == event_key]
                fig.add_trace(go.Scatter(
                    x=sub_df["x_ft"],
                    y=sub_df["y_ft"],
                    mode="markers",
                    name=f"{label} ({len(sub_df)})",
                    marker=dict(
                        size=size,
                        color=color,
                        symbol=symbol,
                        line=dict(width=1, color="#ffffff" if event_key != "Out" else "rgba(255,255,255,0.4)")
                    ),
                    customdata=sub_customdata,
                    hovertemplate=hovertemplate
                ))
    elif color_mode == "trajectory":
        traj_colors = {
            "line_drive": ("Línea (LD)", "#3498db", "diamond"),
            "fly_ball": ("Elevado (FB)", "#e67e22", "circle"),
            "ground_ball": ("Rolling (GB)", "#2ecc71", "square"),
            "popup": ("Pop up (PU)", "#9b59b6", "triangle-up"),
            "unknown": ("Sin dato", "#95a5a6", "circle")
        }
        for traj_key, (label, color, symbol) in traj_colors.items():
            sub_df = df[df["trajectory"] == traj_key]
            if not sub_df.empty:
                sub_customdata = customdata[df["trajectory"] == traj_key]
                fig.add_trace(go.Scatter(
                    x=sub_df["x_ft"],
                    y=sub_df["y_ft"],
                    mode="markers",
                    name=f"{label} ({len(sub_df)})",
                    marker=dict(size=9, color=color, symbol=symbol, line=dict(width=1, color="#ffffff")),
                    customdata=sub_customdata,
                    hovertemplate=hovertemplate
                ))
    else:  # Color por Dureza
        hard_colors = {
            "hard": ("Fuerte (Hard)", "#e74c3c", "star", 10),
            "medium": ("Medio (Medium)", "#f39c12", "circle", 8),
            "soft": ("Suave (Soft)", "#95a5a6", "triangle-up", 7),
        }
        for hard_key, (label, color, symbol, size) in hard_colors.items():
            sub_df = df[df["hardness"] == hard_key]
            if not sub_df.empty:
                sub_customdata = customdata[df["hardness"] == hard_key]
                fig.add_trace(go.Scatter(
                    x=sub_df["x_ft"],
                    y=sub_df["y_ft"],
                    mode="markers",
                    name=f"{label} ({len(sub_df)})",
                    marker=dict(size=size, color=color, symbol=symbol, line=dict(width=1, color="#ffffff")),
                    customdata=sub_customdata,
                    hovertemplate=hovertemplate
                ))

    # Layout estilizado
    fig.update_layout(
        title=dict(
            text=f"🎯 Spray Chart: {player_name} ({len(df)} batazos)",
            font=dict(size=18, color="#ffffff"),
            x=0.05
        ),
        xaxis=dict(
            range=[-250, 250],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True
        ),
        yaxis=dict(
            range=[-15, 435],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            fixedrange=True
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.95)",
        plot_bgcolor="rgba(15, 23, 42, 0.95)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        height=680,
        margin=dict(l=10, r=10, t=50, b=50)
    )
    
    return fig


def generate_spray_chart_figure(df: pd.DataFrame, player_name: str = "Leones del Caracas", color_mode: str = "event") -> go.Figure:
    """Alias para compatibilidad de interfaz con generate_spray_chart_figure."""
    return create_spray_chart_figure(df, player_name=player_name, color_mode=color_mode)


def calculate_spray_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula agregados y métricas clave de los batazos."""
    if df.empty:
        return {
            "total_batted": 0, "total_hits": 0, "babip": 0.0,
            "pct_pull": 0.0, "pct_center": 0.0, "pct_oppo": 0.0,
            "pct_gb": 0.0, "pct_fb": 0.0, "pct_ld": 0.0, "pct_pu": 0.0,
            "pct_hard": 0.0, "pct_medium": 0.0, "pct_soft": 0.0
        }
        
    n = len(df)
    hits = int(df["is_hit"].sum())
    
    # BABIP sobre pelotas puestas en juego (excluyendo HRs que salen del parque)
    bip_no_hr = df[df["event"] != "Home Run"]
    babip = (df["is_hit"].sum() - (df["event"] == "Home Run").sum()) / len(bip_no_hr) if len(bip_no_hr) > 0 else 0.0
    
    # Direccionales
    pull_count = (df["direction"].str.startswith("Pull")).sum()
    center_count = (df["direction"].str.startswith("Center")).sum()
    oppo_count = (df["direction"].str.startswith("Oppo")).sum()
    
    # Trayectorias
    gb_count = (df["trajectory"] == "ground_ball").sum()
    fb_count = (df["trajectory"] == "fly_ball").sum()
    ld_count = (df["trajectory"] == "line_drive").sum()
    pu_count = (df["trajectory"] == "popup").sum()
    
    # Dureza
    hard_count = (df["hardness"] == "hard").sum()
    med_count = (df["hardness"] == "medium").sum()
    soft_count = (df["hardness"] == "soft").sum()
    
    return {
        "total_batted": n,
        "total_hits": hits,
        "babip": round(babip, 3),
        "pct_pull": round(pull_count / n * 100, 1),
        "pct_center": round(center_count / n * 100, 1),
        "pct_oppo": round(oppo_count / n * 100, 1),
        "pct_gb": round(gb_count / n * 100, 1),
        "pct_fb": round(fb_count / n * 100, 1),
        "pct_ld": round(ld_count / n * 100, 1),
        "pct_pu": round(pu_count / n * 100, 1),
        "pct_hard": round(hard_count / n * 100, 1),
        "pct_medium": round(med_count / n * 100, 1),
        "pct_soft": round(soft_count / n * 100, 1)
    }
