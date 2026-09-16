# republicaraquistapp/state/pitching_state.py
"""
pitching_state.py
-----------------
Estado reactivo para la vista de Pitching Summary (/pitching).
Gestiona:
1. Búsqueda universal de lanzadores (MLB/MiLB/LVBP).
2. Selección de temporada y salidas (Game Logs).
3. Bifurcación reactiva: Pestaña MLB/MiLB (Statcast) vs Pestaña Leones del Caracas (LVBP).
4. Cómputo de tablas y figuras Plotly de alto contraste (Movimiento, Strike Zone, Carga y Splits).
5. Descarga de tarjeta gráfica en PNG de alta resolución (2400x1350 px a 300 DPI).
"""

import base64
from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd
import plotly.graph_objects as go

from core.pitching_engine import (
    search_pitchers,
    get_pitcher_game_logs,
    get_game_pitch_data,
    get_statcast_pitcher_df,
    get_pitcher_bio_data,
)
from core.pitching_card import (
    build_pitching_summary_card,
    build_nestico_pitching_summary,
    build_lvbp_matplotlib_summary,
    PITCH_COLORS,
    _get_pitch_color,
)
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    ACCENT_GOLD,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_DIM,
)


def _plotly_layout_base(title: str = "") -> dict:
    """Configuración base oscura para figuras Plotly consistente con el tema."""
    return dict(
        title=dict(
            text=title,
            font=dict(color=ACCENT_GOLD, size=14, family="Inter, sans-serif"),
            x=0.03,
            y=0.96,
        ),
        paper_bgcolor="rgba(13, 21, 43, 0.6)",
        plot_bgcolor="rgba(7, 11, 25, 0.8)",
        margin=dict(l=35, r=25, t=35, b=30),
        font=dict(color=TEXT_PRIMARY, size=11, family="Inter, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(color=TEXT_MUTED, size=10),
        ),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.07)",
            zerolinecolor="rgba(253, 184, 39, 0.4)",
            tickfont=dict(color=TEXT_MUTED, size=10),
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.07)",
            zerolinecolor="rgba(253, 184, 39, 0.4)",
            tickfont=dict(color=TEXT_MUTED, size=10),
        ),
    )


class PitchingState(AppState):
    """Estado reactivo de la página Pitching Summary."""

    # ── Buscador ────────────────────────────────────────────────────────────
    search_query: str = ""
    search_results: List[Dict[str, Any]] = []
    is_searching: bool = False

    # ── Selección de Lanzador ────────────────────────────────────────────────
    selected_pitcher: Dict[str, Any] = {}
    has_pitcher_selected: bool = False
    has_caracas_history: bool = False

    # ── Filtros y Configuración ─────────────────────────────────────────────
    active_branch: str = "mlb"  # "mlb" o "lvbp"
    pitcher_season: str = "2024"
    available_seasons: List[str] = ["2025", "2024", "2023", "2022"]
    game_logs: List[Dict[str, Any]] = []
    game_log_options: List[str] = []
    selected_game_label: str = ""
    selected_game_pk: int = 0
    is_loading_data: bool = False
    is_generating_card: bool = False

    # ── Modos Temporales y Tarjeta Matplotlib ──────────────────────────────
    time_mode: str = "game"  # "game", "season", "range"
    range_start_date: str = "2024-04-01"
    range_end_date: str = "2024-06-30"
    rendered_image_url: str = ""
    raw_card_bytes: bytes = b""

    # ── Datos Procesados del Juego ──────────────────────────────────────────
    pitch_analysis: Dict[str, Any] = {}
    statcast_table: List[Dict[str, Any]] = []
    pbp_table: List[Dict[str, Any]] = []
    pbp_kpis: Dict[str, Any] = {}
    current_game_summary: Dict[str, Any] = {}

    # ── Figuras Plotly Interactivas ─────────────────────────────────────────
    fig_movement: go.Figure = go.Figure()
    fig_strike_zone: go.Figure = go.Figure()
    fig_workload: go.Figure = go.Figure()
    fig_leverage: go.Figure = go.Figure()
    fig_splits: go.Figure = go.Figure()

    # ── Manejadores del Buscador ────────────────────────────────────────────

    def set_search_query(self, query: str):
        """Actualiza el texto de búsqueda y dispara búsqueda si tiene >= 2 caracteres."""
        self.search_query = query
        if len(query.strip()) >= 2:
            self.perform_search()
        else:
            self.search_results = []

    def perform_search(self):
        """Ejecuta la búsqueda de lanzadores en MLB Stats API."""
        if not self.search_query or len(self.search_query.strip()) < 2:
            self.search_results = []
            return
        self.is_searching = True
        try:
            self.search_results = search_pitchers(self.search_query)
        finally:
            self.is_searching = False

    def select_pitcher_by_id(self, pitcher_id: int):
        """Selecciona un lanzador, extrae su historial y carga sus juegos."""
        found = None
        for p in self.search_results:
            if p.get("id") == pitcher_id:
                found = p
                break
        if not found:
            # Buscar individualmente
            res = search_pitchers(str(pitcher_id))
            if res:
                found = res[0]

        if not found:
            return

        self.selected_pitcher = found
        self.has_pitcher_selected = True
        self.has_caracas_history = bool(found.get("has_caracas_history", False))

        # Por defecto abrir la pestaña MLB a menos que sea exclusivo de LVBP
        if not self.has_caracas_history:
            self.active_branch = "mlb"
        elif self.active_branch not in ("mlb", "lvbp"):
            self.active_branch = "lvbp"

        self.search_results = []
        self.search_query = ""
        self.load_pitcher_games()

    def clear_selection(self):
        """Regresa al estado inicial con buscador centrado."""
        self.has_pitcher_selected = False
        self.selected_pitcher = {}
        self.game_logs = []
        self.game_log_options = []
        self.selected_game_label = ""
        self.selected_game_pk = 0
        self.pitch_analysis = {}
        self.statcast_table = []
        self.pbp_table = []
        self.pbp_kpis = {}
        self.current_game_summary = {}
        self.search_query = ""
        self.search_results = []
        self.rendered_image_url = ""
        self.raw_card_bytes = b""
        self.time_mode = "game"

    # ── Manejadores de Salidas, Ramas y Modos Temporales ────────────────────

    def set_active_branch(self, branch: str):
        """Cambia entre la rama MLB/MiLB (Statcast) y Leones del Caracas (LVBP)."""
        if branch == "lvbp" and not self.has_caracas_history:
            return
        self.active_branch = branch
        self.load_pitcher_games()

    def set_pitcher_season(self, season_val: str):
        """Cambia la temporada seleccionada y recarga salidas."""
        self.pitcher_season = str(season_val)
        self.range_start_date = f"{self.pitcher_season}-04-01"
        self.range_end_date = f"{self.pitcher_season}-06-30"
        self.load_pitcher_games()

    def set_time_mode(self, mode: str):
        """Cambia el modo temporal: 'game' (Salida), 'season' (Temporada) o 'range' (Rango)."""
        self.time_mode = mode
        if mode == "game" and self.selected_game_pk:
            self.load_game_data()
        else:
            self.generate_card()

    def set_range_start_date(self, val: str):
        """Actualiza la fecha de inicio para el modo rango."""
        self.range_start_date = val

    def set_range_end_date(self, val: str):
        """Actualiza la fecha de fin para el modo rango."""
        self.range_end_date = val

    def set_selected_game_by_label(self, label: str):
        """Selecciona un juego según la etiqueta elegida en el selector."""
        self.selected_game_label = label
        for i, opt in enumerate(self.game_log_options):
            if opt == label and i < len(self.game_logs):
                self.selected_game_pk = self.game_logs[i].get("game_pk", 0)
                self.current_game_summary = self.game_logs[i]
                self.load_game_data()
                break

    def select_game(self, game_pk_str: str):
        """Selecciona un juego específico y recarga su analítica."""
        try:
            self.selected_game_pk = int(game_pk_str)
            for g in self.game_logs:
                if g.get("game_pk") == self.selected_game_pk:
                    self.current_game_summary = g
                    break
            self.load_game_data()
        except (ValueError, TypeError):
            pass

    def load_pitcher_games(self):
        """Descarga la lista de salidas del lanzador para la temporada y rama activa."""
        if not self.selected_pitcher:
            return
        self.is_loading_data = True
        try:
            p_id = self.selected_pitcher.get("id")
            is_lvbp = (self.active_branch == "lvbp")
            try:
                s_int = int(self.pitcher_season)
            except (ValueError, TypeError):
                s_int = 2024
            logs = get_pitcher_game_logs(p_id, s_int, is_lvbp=is_lvbp)
            self.game_logs = logs

            opts = [
                f"{g.get('date', '')} vs {g.get('opponent', '')} ({g.get('ip', 0)} IP, {g.get('so', 0)} K)"
                for g in logs
            ]
            self.game_log_options = opts

            if logs and opts:
                self.selected_game_pk = logs[0].get("game_pk", 0)
                self.current_game_summary = logs[0]
                self.selected_game_label = opts[0]
                self.load_game_data()
            else:
                self.selected_game_pk = 0
                self.current_game_summary = {}
                self.selected_game_label = ""
                self.pitch_analysis = {}
                self.statcast_table = []
                self.pbp_table = []
                self.pbp_kpis = {}
                self._reset_figures()
                self.generate_card()
        finally:
            self.is_loading_data = False

    def load_game_data(self):
        """Descarga y computa la analítica y figuras del juego seleccionado."""
        if not self.selected_game_pk or not self.selected_pitcher:
            return

        self.is_loading_data = True
        try:
            p_id = self.selected_pitcher.get("id")
            is_lvbp = (self.active_branch == "lvbp")
            analysis = get_game_pitch_data(self.selected_game_pk, p_id, is_lvbp=is_lvbp)
            self.pitch_analysis = analysis
            self.statcast_table = analysis.get("statcast_table", [])
            self.pbp_table = analysis.get("pbp_table", [])
            self.pbp_kpis = analysis.get("pbp_kpis", {})

            # Construir figuras interactivas
            pitches = analysis.get("pitches", [])
            has_sc = analysis.get("has_statcast", False) and not is_lvbp

            if has_sc:
                self.fig_movement = self._build_movement_figure(pitches)
                self.fig_strike_zone = self._build_strike_zone_figure(pitches)
            else:
                self.fig_movement = go.Figure()
                self.fig_strike_zone = go.Figure()

            # Figuras para ambas ramas (Carga, LI, Splits)
            self.fig_workload = self._build_workload_figure(analysis.get("innings_workload", []))
            self.fig_leverage = self._build_leverage_figure(analysis.get("innings_workload", []))
            self.fig_splits = self._build_splits_figure(analysis.get("splits_platoon", {}))
        finally:
            self.is_loading_data = False
            self.generate_card()

    # ── Constructores de Figuras Plotly ─────────────────────────────────────

    def _reset_figures(self):
        self.fig_movement = go.Figure()
        self.fig_strike_zone = go.Figure()
        self.fig_workload = go.Figure()
        self.fig_leverage = go.Figure()
        self.fig_splits = go.Figure()

    def _build_movement_figure(self, pitches: List[Dict[str, Any]]) -> go.Figure:
        """Construye el gráfico cartesiano de movimiento de pitcheos (IVB vs HB)."""
        fig = go.Figure()
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for p in pitches:
            if p.get("hb") is not None and p.get("ivb") is not None:
                by_type.setdefault(p.get("pitch_name", "Desconocido"), []).append(p)

        for p_name, p_list in by_type.items():
            rgb = _get_pitch_color(p_name)
            hex_color = f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

            fig.add_trace(go.Scatter(
                x=[p["hb"] for p in p_list],
                y=[p["ivb"] for p in p_list],
                mode="markers",
                name=p_name,
                marker=dict(
                    size=9,
                    color=hex_color,
                    line=dict(width=1, color="rgba(255,255,255,0.8)"),
                    opacity=0.85,
                ),
                text=[f"{p_name}<br>Velo: {p.get('speed')} mph<br>IVB: {p.get('ivb')}\"<br>HB: {p.get('hb')}\"" for p in p_list],
                hoverinfo="text",
            ))

        layout = _plotly_layout_base("Movimiento de Pitcheos (IVB vs HB en pulgadas)")
        layout["xaxis"]["title"] = "Quiebre Horizontal (HB) [in]  ← Guante | Brazo →"
        layout["yaxis"]["title"] = "Quiebre Vertical Inducido (IVB) [in]"
        layout["xaxis"]["range"] = [-25, 25]
        layout["yaxis"]["range"] = [-25, 25]

        # Cuadrantes
        layout["shapes"] = [
            dict(type="line", x0=-25, x1=25, y0=0, y1=0, line=dict(color="rgba(253,184,39,0.3)", width=1, dash="dash")),
            dict(type="line", x0=0, x1=0, y0=-25, y1=25, line=dict(color="rgba(253,184,39,0.3)", width=1, dash="dash")),
        ]
        fig.update_layout(layout)
        return fig

    def _build_strike_zone_figure(self, pitches: List[Dict[str, Any]]) -> go.Figure:
        """Construye el gráfico de localización en la zona de strike."""
        fig = go.Figure()
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for p in pitches:
            if p.get("plate_x") is not None and p.get("plate_z") is not None:
                by_type.setdefault(p.get("pitch_name", "Desconocido"), []).append(p)

        for p_name, p_list in by_type.items():
            rgb = _get_pitch_color(p_name)
            hex_color = f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

            fig.add_trace(go.Scatter(
                x=[p["plate_x"] for p in p_list],
                y=[p["plate_z"] for p in p_list],
                mode="markers",
                name=p_name,
                marker=dict(
                    size=9,
                    color=hex_color,
                    line=dict(width=1.5, color="rgba(253,184,39,0.9)" if any(p.get("is_whiff") for p in p_list) else "rgba(255,255,255,0.7)"),
                    symbol=["cross" if p.get("is_whiff") else "circle" for p in p_list],
                ),
                text=[f"{p_name}<br>Resultado: {p.get('result')}<br>Velo: {p.get('speed')} mph" for p in p_list],
                hoverinfo="text",
            ))

        layout = _plotly_layout_base("Localización en Zona de Strike")
        layout["xaxis"]["title"] = "Coordenada X (ft) [Centro = 0.0]"
        layout["yaxis"]["title"] = "Altura Z (ft)"
        layout["xaxis"]["range"] = [-2.0, 2.0]
        layout["yaxis"]["range"] = [0.5, 4.5]

        # Caja de la zona de strike (ancho ~1.42 ft, alto 1.5 a 3.5 ft)
        layout["shapes"] = [
            dict(
                type="rect",
                x0=-0.85, x1=0.85, y0=1.5, y1=3.5,
                line=dict(color="#3B82F6", width=2.5),
                fillcolor="rgba(59, 130, 246, 0.08)",
            )
        ]
        fig.update_layout(layout)
        return fig

    def _build_workload_figure(self, workload: List[Dict[str, Any]]) -> go.Figure:
        """Construye el gráfico de barras de lanzamientos por entrada."""
        fig = go.Figure()
        if not workload:
            return fig

        inns = [f"Inning {w['inning']}" for w in workload]
        strikes = [w["strikes"] for w in workload]
        balls = [w["pitches"] - w["strikes"] for w in workload]

        fig.add_trace(go.Bar(
            name="Strikes",
            x=inns,
            y=strikes,
            marker_color="#FDB827",
        ))
        fig.add_trace(go.Bar(
            name="Bolas",
            x=inns,
            y=balls,
            marker_color="rgba(80, 100, 140, 0.8)",
        ))

        layout = _plotly_layout_base("Lanzamientos por Entrada (Carga de Trabajo)")
        layout["barmode"] = "stack"
        layout["yaxis"]["title"] = "Total Pitcheos"
        fig.update_layout(layout)
        return fig

    def _build_leverage_figure(self, workload: List[Dict[str, Any]]) -> go.Figure:
        """Construye el gráfico de apalancamiento (Leverage Index) por entrada."""
        fig = go.Figure()
        if not workload:
            return fig

        inns = [f"Inning {w['inning']}" for w in workload]
        lis = [w.get("avg_li", 1.0) for w in workload]

        colors = ["#EF4444" if li >= 1.5 else ("#FDB827" if li >= 0.9 else "#3B82F6") for li in lis]

        fig.add_trace(go.Bar(
            name="Leverage Index",
            x=inns,
            y=lis,
            marker_color=colors,
            text=[f"LI: {li:.2f}" for li in lis],
            textposition="auto",
        ))

        layout = _plotly_layout_base("Apalancamiento de Entrada (Leverage Index RE24)")
        layout["yaxis"]["title"] = "Índice de Apalancamiento (LI)"
        layout["yaxis"]["range"] = [0, max(max(lis, default=1.5) + 0.5, 2.5)]

        # Líneas de referencia
        layout["shapes"] = [
            dict(type="line", x0=-0.5, x1=len(inns)-0.5, y0=1.0, y1=1.0, line=dict(color="rgba(255,255,255,0.4)", width=1, dash="dash")),
            dict(type="line", x0=-0.5, x1=len(inns)-0.5, y0=1.5, y1=1.5, line=dict(color="rgba(239,68,68,0.6)", width=1.5, dash="dot")),
        ]
        fig.update_layout(layout)
        return fig

    def _build_splits_figure(self, splits: Dict[str, Any]) -> go.Figure:
        """Construye el gráfico de barras comparativo vs LHB y RHB."""
        fig = go.Figure()
        lhb = splits.get("vs_lhb", {})
        rhb = splits.get("vs_rhb", {})

        categories = ["CSW %", "Whiff %", "Strike %"]
        lhb_vals = [
            float(lhb.get("csw_pct", "0.0%").replace("%", "")),
            float(lhb.get("whiff_pct", "0.0%").replace("%", "")),
            float(lhb.get("strike_pct", "0.0%").replace("%", "")),
        ]
        rhb_vals = [
            float(rhb.get("csw_pct", "0.0%").replace("%", "")),
            float(rhb.get("whiff_pct", "0.0%").replace("%", "")),
            float(rhb.get("strike_pct", "0.0%").replace("%", "")),
        ]

        fig.add_trace(go.Bar(name="vs Zurdos (LHB)", x=categories, y=lhb_vals, marker_color="#3B82F6"))
        fig.add_trace(go.Bar(name="vs Derechos (RHB)", x=categories, y=rhb_vals, marker_color="#FDB827"))

        layout = _plotly_layout_base("Efectividad Situacional (Platoon Splits LHB vs RHB)")
        layout["barmode"] = "group"
        layout["yaxis"]["title"] = "Porcentaje (%)"
        fig.update_layout(layout)
        return fig

    # ── Generación y Descarga de Tarjeta HD en Matplotlib ────────────────────

    def generate_card(self):
        """Genera la tarjeta Matplotlib de Pitching Summary en memoria."""
        if not self.selected_pitcher:
            return

        self.is_generating_card = True
        try:
            p_id = self.selected_pitcher.get("id")
            try:
                s_int = int(self.pitcher_season)
            except (ValueError, TypeError):
                s_int = 2024

            is_lvbp = (self.active_branch == "lvbp")

            if is_lvbp:
                raw_bytes = build_lvbp_matplotlib_summary(
                    pitcher_info=self.selected_pitcher,
                    game_summary=self.current_game_summary,
                    analysis=self.pitch_analysis,
                    season=s_int,
                    dpi=160,
                )
            else:
                pitcher_info = dict(self.selected_pitcher)
                if not pitcher_info.get("age") or not pitcher_info.get("height"):
                    try:
                        bio = get_pitcher_bio_data(p_id)
                        pitcher_info.update(bio)
                        self.selected_pitcher = pitcher_info
                    except Exception:
                        pass

                game_date = self.current_game_summary.get("date")
                df_sc = get_statcast_pitcher_df(
                    pitcher_id=p_id,
                    season=s_int,
                    mode=self.time_mode,
                    game_pk=self.selected_game_pk if self.time_mode == "game" else None,
                    game_date=game_date if self.time_mode == "game" else None,
                    start_date=self.range_start_date if self.time_mode == "range" else None,
                    end_date=self.range_end_date if self.time_mode == "range" else None,
                )

                raw_bytes = build_nestico_pitching_summary(
                    df=df_sc,
                    pitcher_info=pitcher_info,
                    mode=self.time_mode,
                    season=s_int,
                    start_date=self.range_start_date,
                    end_date=self.range_end_date,
                    game_summary=self.current_game_summary,
                    dpi=160,
                )

            self.raw_card_bytes = raw_bytes
            b64 = base64.b64encode(raw_bytes).decode("utf-8")
            self.rendered_image_url = f"data:image/png;base64,{b64}"
        finally:
            self.is_generating_card = False

    def download_pitching_card(self):
        """Descarga la tarjeta gráfica oficial en PNG de alta resolución."""
        if not self.selected_pitcher:
            return
        if not self.raw_card_bytes:
            self.generate_card()
        if not self.raw_card_bytes:
            return

        safe_name = "".join(c for c in self.selected_pitcher.get("name", "Pitcher") if c.isalnum() or c == "_").strip()
        is_lvbp = (self.active_branch == "lvbp")
        league_tag = "LVBP" if is_lvbp else "MLB"

        if is_lvbp or self.time_mode == "game":
            date_safe = str(self.current_game_summary.get("date", "game")).replace("-", "")
            filename = f"PitchingSummary_{safe_name}_{league_tag}_{date_safe}.png"
        elif self.time_mode == "season":
            filename = f"PitchingSummary_{safe_name}_{league_tag}_Temporada_{self.pitcher_season}.png"
        else:
            s_safe = str(self.range_start_date).replace("-", "")
            e_safe = str(self.range_end_date).replace("-", "")
            filename = f"PitchingSummary_{safe_name}_{league_tag}_Rango_{s_safe}_{e_safe}.png"

        return rx.download(data=self.raw_card_bytes, filename=filename, mime_type="image/png")

    # ── Lifecycle on_load ───────────────────────────────────────────────────

    def on_load(self):
        """Manejador inicial al navegar a la página /pitching."""
        # Si ya hay un lanzador seleccionado, no resetear
        if self.has_pitcher_selected:
            return

        # Comprobar si viene un pitcher_id por query params (ej: /pitching?pitcher_id=544150)
        p_id = self.router.page.params.get("pitcher_id")
        if p_id:
            try:
                self.select_pitcher_by_id(int(p_id))
                return
            except (ValueError, TypeError):
                pass

        # Comprobar si viene un pitcher_name por query params (ej: /pitching?pitcher_name=Erick+Leal)
        p_name = self.router.page.params.get("pitcher_name")
        if p_name:
            self.search_query = p_name
            self.perform_search()
            if self.search_results:
                self.select_pitcher_by_id(self.search_results[0]["id"])
