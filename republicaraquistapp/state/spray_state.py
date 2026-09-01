# republicaraquistapp/state/spray_state.py
"""
spray_state.py
--------------
Estado reactivo para los Spray Charts espaciales en diamante con modelo BIS de dureza
y la visualización de la Zona de Strike 3x3 con métricas de disciplina en el plato.
"""

from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.styles.theme import (
    ACCENT_GOLD,
    LEONES_RED,
    TEXT_PRIMARY,
    CARD_BG
)
from core.spray_chart import (
    fetch_season_batted_balls,
    create_spray_chart_figure,
    generate_spray_chart_figure,
    calculate_spray_stats,
    LEONES_TEAM_ID
)
from core.strike_zone import (
    fetch_season_pitches,
    create_strike_zone_figure,
    generate_strike_zone_figure,
    calculate_discipline_metrics
)


class SprayState(AppState):
    """Estado reactivo para Spray Charts y Zona de Strike 3x3."""

    # Vista activa: "spray" o "strike_zone"
    active_view: str = "spray"

    # ── Spray Charts ────────────────────────────────────────────────────────
    spray_player_options: List[str] = ["🌟 Toda la Ofensiva de Leones"]
    selected_spray_player: str = "🌟 Toda la Ofensiva de Leones"
    spray_color_mode: str = "event"  # "event", "trajectory", "hardness"

    # KPIs de Spray
    spray_total_batted: int = 0
    spray_total_hits: int = 0
    spray_babip: str = ".000"
    spray_pct_pull: str = "0.0%"
    spray_pct_center: str = "0.0%"
    spray_pct_oppo: str = "0.0%"
    spray_pct_gb: str = "0.0%"
    spray_pct_fb: str = "0.0%"
    spray_pct_ld: str = "0.0%"
    spray_pct_pu: str = "0.0%"
    spray_pct_hard: str = "0.0%"
    spray_pct_medium: str = "0.0%"
    spray_pct_soft: str = "0.0%"

    # Figura Plotly Spray Chart
    spray_chart_figure: go.Figure = go.Figure()

    # ── Strike Zone 3x3 ─────────────────────────────────────────────────────
    sz_perspective: str = "Bateadores de Leones"  # "Bateadores de Leones" o "Lanzadores de Leones"
    sz_player_options: List[str] = ["🌟 Todo el Equipo"]
    selected_sz_player: str = "🌟 Todo el Equipo"

    # KPIs de Disciplina
    sz_total_pitches: int = 0
    sz_csw_pct: str = "0.0%"
    sz_whiff_pct: str = "0.0%"
    sz_o_swing_pct: str = "0.0%"
    sz_z_swing_pct: str = "0.0%"
    sz_z_contact_pct: str = "0.0%"
    sz_swstr_pct: str = "0.0%"

    # Figura Plotly Strike Zone
    strike_zone_figure: go.Figure = go.Figure()

    def on_load_spray(self):
        """Carga inicial de Spray Charts y Zona de Strike."""
        self.is_loading = True
        self.loading_text = "Descargando coordenadas espaciales y lanzamientos..."
        try:
            self.load_spray_data()
            self.load_strike_zone_data()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error en Spray Charts"
            self.error_message = f"No se pudieron cargar los datos espaciales: {str(e)}"
        finally:
            self.is_loading = False

    def set_active_view(self, view_name: str):
        """Cambia entre Spray Charts y Zona de Strike 3x3."""
        self.active_view = view_name

    def load_spray_data(self):
        """Carga y procesa datos de batazos para el Spray Chart."""
        df_batted = fetch_season_batted_balls(self.selected_season, team_id=LEONES_TEAM_ID)
        if df_batted.empty:
            self.spray_player_options = ["🌟 Toda la Ofensiva de Leones"]
            self.spray_chart_figure = generate_spray_chart_figure(pd.DataFrame(), "Sin datos")
            return

        leones_batted = df_batted[df_batted["is_leones"] == True].copy()
        p_counts = leones_batted["batter_name"].value_counts()
        opts = ["🌟 Toda la Ofensiva de Leones"] + [f"{name} ({c} batazos)" for name, c in p_counts.items()]
        self.spray_player_options = opts

        self.update_spray_figure(df_batted)

    def set_selected_spray_player(self, player_display: str):
        """Manejador para cambio de jugador en el Spray Chart."""
        self.selected_spray_player = player_display
        df_batted = fetch_season_batted_balls(self.selected_season, team_id=LEONES_TEAM_ID)
        self.update_spray_figure(df_batted)

    def set_spray_color_mode(self, mode: str):
        """Manejador para cambiar la paleta de colores del Spray Chart."""
        self.spray_color_mode = mode
        df_batted = fetch_season_batted_balls(self.selected_season, team_id=LEONES_TEAM_ID)
        self.update_spray_figure(df_batted)

    def update_spray_figure(self, df_batted: pd.DataFrame):
        """Filtra y recalcula la figura de Spray Chart y sus métricas."""
        if df_batted.empty:
            return

        leones_b = df_batted[df_batted["is_leones"] == True].copy()
        if self.selected_spray_player == "🌟 Toda la Ofensiva de Leones":
            df_target = leones_b
            p_title = "Leones del Caracas (Ofensiva Completa)"
        else:
            p_name = self.selected_spray_player.split(" (")[0]
            df_target = leones_b[leones_b["batter_name"] == p_name]
            p_title = p_name

        # Recalcular métricas
        stats = calculate_spray_stats(df_target)
        self.spray_total_batted = stats["total_batted"]
        self.spray_total_hits = stats["total_hits"]
        self.spray_babip = f".{int(stats['babip']*1000):03d}" if stats["babip"] < 1.0 else f"{stats['babip']:.3f}"
        self.spray_pct_pull = f"{stats['pct_pull']}%"
        self.spray_pct_center = f"{stats['pct_center']}%"
        self.spray_pct_oppo = f"{stats['pct_oppo']}%"
        self.spray_pct_gb = f"{stats['pct_gb']}%"
        self.spray_pct_fb = f"{stats['pct_fb']}%"
        self.spray_pct_ld = f"{stats['pct_ld']}%"
        self.spray_pct_pu = f"{stats['pct_pu']}%"
        self.spray_pct_hard = f"{stats['pct_hard']}%"
        self.spray_pct_medium = f"{stats['pct_medium']}%"
        self.spray_pct_soft = f"{stats['pct_soft']}%"

        # Generar Figura
        self.spray_chart_figure = generate_spray_chart_figure(
            df_target,
            player_name=p_title,
            color_mode=self.spray_color_mode
        )

    def load_strike_zone_data(self):
        """Carga y procesa datos de lanzamientos para la Zona de Strike 3x3."""
        df_pitches = fetch_season_pitches(self.selected_season, team_id=LEONES_TEAM_ID, cache_version="v3_at_bats_opponents")
        if df_pitches.empty:
            self.sz_player_options = ["🌟 Todo el Equipo"]
            self.strike_zone_figure = generate_strike_zone_figure(pd.DataFrame(), "Sin datos")
            return

        is_batting = (self.sz_perspective == "Bateadores de Leones")
        df_pool = df_pitches[df_pitches["is_batter_leones"] == True] if is_batting else df_pitches[df_pitches["is_pitcher_leones"] == True]
        col_name = "batter_name" if is_batting else "pitcher_name"
        
        p_counts = df_pool[col_name].value_counts()
        opts = ["🌟 Todo el Equipo"] + [f"{name} ({c} pitcheos)" for name, c in p_counts.items()]
        self.sz_player_options = opts
        self.selected_sz_player = "🌟 Todo el Equipo"

        self.update_strike_zone_figure(df_pitches)

    def set_sz_perspective(self, perspective: str):
        """Cambia entre perspectiva de Bateo o Pitcheo para la Zona de Strike."""
        self.sz_perspective = perspective
        df_pitches = fetch_season_pitches(self.selected_season, team_id=LEONES_TEAM_ID, cache_version="v3_at_bats_opponents")
        if df_pitches.empty:
            return

        is_batting = (perspective == "Bateadores de Leones")
        df_pool = df_pitches[df_pitches["is_batter_leones"] == True] if is_batting else df_pitches[df_pitches["is_pitcher_leones"] == True]
        col_name = "batter_name" if is_batting else "pitcher_name"
        
        p_counts = df_pool[col_name].value_counts()
        self.sz_player_options = ["🌟 Todo el Equipo"] + [f"{name} ({c} pitcheos)" for name, c in p_counts.items()]
        self.selected_sz_player = "🌟 Todo el Equipo"

        self.update_strike_zone_figure(df_pitches)

    def set_selected_sz_player(self, player_display: str):
        """Manejador para cambio de jugador en la Zona de Strike."""
        self.selected_sz_player = player_display
        df_pitches = fetch_season_pitches(self.selected_season, team_id=LEONES_TEAM_ID, cache_version="v3_at_bats_opponents")
        self.update_strike_zone_figure(df_pitches)

    def update_strike_zone_figure(self, df_pitches: pd.DataFrame):
        """Filtra y recalcula la figura de Zona de Strike y métricas de disciplina."""
        if df_pitches.empty:
            return

        is_batting = (self.sz_perspective == "Bateadores de Leones")
        df_pool = df_pitches[df_pitches["is_batter_leones"] == True] if is_batting else df_pitches[df_pitches["is_pitcher_leones"] == True]
        col_name = "batter_name" if is_batting else "pitcher_name"

        if self.selected_sz_player == "🌟 Todo el Equipo":
            df_target = df_pool
            p_title = "Leones del Caracas (Ofensiva)" if is_batting else "Leones del Caracas (Pitcheo)"
        else:
            p_name = self.selected_sz_player.split(" (")[0]
            df_target = df_pool[df_pool[col_name] == p_name]
            p_title = p_name

        # Recalcular métricas de disciplina
        disc = calculate_discipline_metrics(df_target)
        self.sz_total_pitches = disc["total_pitches"]
        self.sz_csw_pct = f"{disc['csw_pct']}%"
        self.sz_whiff_pct = f"{disc['whiff_pct']}%"
        self.sz_o_swing_pct = f"{disc['o_swing_pct']}%"
        self.sz_z_swing_pct = f"{disc['z_swing_pct']}%"
        self.sz_z_contact_pct = f"{disc['z_contact_pct']}%"
        self.sz_swstr_pct = f"{disc['swstr_pct']}%"

        # Generar Figura
        self.strike_zone_figure = generate_strike_zone_figure(df_target, player_name=p_title)
