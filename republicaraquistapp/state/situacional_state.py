# republicaraquistapp/state/situacional_state.py
"""
situacional_state.py
--------------------
Estado reactivo para el análisis situacional (Splits, RISP, Clutch),
LOB Tracker (Dejados en Base) y Enfrentamientos BvP (Bateador vs Lanzador).
"""

from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.styles.theme import (
    ACCENT_GOLD,
    LEONES_RED,
    TEXT_PRIMARY,
    CARD_BG
)
from core.teams import get_team_logo, get_team_name, LVBP_TEAMS
from core.situational import (
    fetch_season_situational_data,
    compute_all_situational_splits,
    compute_bvp_summary,
    compute_lob_analytics,
    summarize_slash_line,
    LEONES_TEAM_ID
)


def build_ops_by_situation_chart(splits_df: pd.DataFrame) -> go.Figure:
    """Construye el gráfico de barras horizontal comparativo de OPS por situación."""
    fig = go.Figure()
    if splits_df.empty:
        fig.update_layout(
            title="<b>Comparativa de OPS (Sin Datos)</b>",
            template="plotly_dark",
            paper_bgcolor="rgba(13, 21, 43, 0.95)",
            plot_bgcolor="rgba(13, 21, 43, 0.95)",
            height=380
        )
        return fig

    chart_df = splits_df.copy()
    chart_df["OPS_num"] = chart_df["OPS"].astype(float)
    # Invertir para que la primera situación quede arriba
    chart_df = chart_df.iloc[::-1]

    # Paleta dinámica según nivel de OPS
    colors = [
        "#10b981" if v >= 0.850 else ("#FDB827" if v >= 0.700 else "#ef4444")
        for v in chart_df["OPS_num"]
    ]

    fig.add_trace(go.Bar(
        y=chart_df["Situación"],
        x=chart_df["OPS_num"],
        orientation="h",
        marker_color=colors,
        text=chart_df["OPS_num"].apply(lambda v: f".{int(v*1000):03d}" if v < 1.0 else f"{v:.3f}"),
        textposition="outside",
        textfont=dict(color="#FFFFFF", size=11),
        hovertemplate="<b>%{y}</b><br>OPS: <b>%{x:.3f}</b><extra></extra>"
    ))

    fig.add_vline(
        x=0.700,
        line_dash="dash",
        line_color="rgba(255, 255, 255, 0.4)",
        annotation_text="Promedio (.700)",
        annotation_font=dict(color="#94a3b8", size=10)
    )

    fig.update_layout(
        title=dict(
            text="<b>📊 Comparativa de OPS por Contexto Situacional</b>",
            font=dict(size=14, color="#FFFFFF")
        ),
        xaxis_title="OPS (On-Base Plus Slugging)",
        yaxis_title="",
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.08)",
            color="#94a3b8",
            range=[0, max(1.1, chart_df["OPS_num"].max() * 1.15)]
        ),
        yaxis=dict(color="#FFFFFF"),
        template="plotly_dark",
        paper_bgcolor="rgba(13, 21, 43, 0.95)",
        plot_bgcolor="rgba(13, 21, 43, 0.95)",
        height=400,
        margin=dict(l=15, r=25, t=45, b=35),
        showlegend=False
    )
    return fig


def build_top_risp_lob_chart(df_lob_players: pd.DataFrame) -> go.Figure:
    """Construye el gráfico de barras con los bateadores con más corredores en RISP dejados en base."""
    fig = go.Figure()
    if df_lob_players.empty:
        fig.update_layout(
            title="<b>RISP LOB por Bateador (Sin Datos)</b>",
            template="plotly_dark",
            paper_bgcolor="rgba(13, 21, 43, 0.95)",
            plot_bgcolor="rgba(13, 21, 43, 0.95)",
            height=360
        )
        return fig

    top_lob = df_lob_players.head(10).iloc[::-1]
    fig.add_trace(go.Bar(
        y=top_lob["Bateador"],
        x=top_lob["Total RISP LOB"],
        orientation="h",
        marker_color="#ef4444",
        text=top_lob["Total RISP LOB"],
        textposition="outside",
        textfont=dict(color="#FFFFFF", size=11),
        hovertemplate="<b>%{y}</b><br>RISP LOB: <b>%{x}</b> corredores<extra></extra>"
    ))
    fig.update_layout(
        title=dict(
            text="<b>🛑 Top Bateadores con Más RISP LOB</b>",
            font=dict(size=14, color="#FFFFFF")
        ),
        xaxis_title="Corredores Dejados en Posición Anotadora",
        yaxis_title="",
        xaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", color="#94a3b8"),
        yaxis=dict(color="#FFFFFF"),
        template="plotly_dark",
        paper_bgcolor="rgba(13, 21, 43, 0.95)",
        plot_bgcolor="rgba(13, 21, 43, 0.95)",
        height=360,
        margin=dict(l=15, r=25, t=45, b=35),
        showlegend=False
    )
    return fig


class SituationalState(AppState):
    """Estado reactivo para el módulo situacional, LOB tracker y BvP."""

    # Pestaña activa: "splits", "lob", "bvp"
    active_tab: str = "splits"

    # Selector de Bateador para Splits
    batter_options: List[str] = ["🌟 Toda la Ofensiva de Leones"]
    selected_batter: str = "🌟 Toda la Ofensiva de Leones"

    # KPIs Situacionales
    kpi_pa: str = "0"
    kpi_avg: str = ".000"
    kpi_risp_avg: str = ".000"
    kpi_risp_avg_delta: str = "+.000"
    kpi_risp_ops: str = ".000"
    kpi_risp_ops_delta: str = "+.000"
    kpi_clutch_avg: str = ".000"
    kpi_clutch_avg_delta: str = "+.000"
    kpi_rbi: str = "0"

    # Tabla de Splits Situacionales y Gráfico
    splits_table_data: List[Dict[str, Any]] = []
    ops_chart_figure: go.Figure = go.Figure()

    # LOB Tracker (Dejados en Base)
    lob_total_ending: int = 0
    lob_risp_ending: int = 0
    lob_risp_mid: int = 0
    lob_risp_total: int = 0
    lob_players_data: List[Dict[str, Any]] = []
    lob_chart_figure: go.Figure = go.Figure()

    # Matriz BvP
    bvp_batter_options: List[str] = []
    selected_bvp_batter: str = ""
    rival_team_options: List[str] = ["Todos los Rivales"]
    selected_rival_team: str = "Todos los Rivales"
    bvp_table_data: List[Dict[str, Any]] = []

    def on_load_situacional(self):
        """Carga inicial del módulo situacional para la temporada seleccionada."""
        self.is_loading = True
        self.loading_text = "Procesando apariciones al plato y analítica situacional..."
        try:
            df_pa = fetch_season_situational_data(self.selected_season, team_id=LEONES_TEAM_ID)
            if df_pa.empty:
                self.batter_options = ["🌟 Toda la Ofensiva de Leones"]
                self.splits_table_data = []
                self.bvp_table_data = []
                return

            leones_pa = df_pa[df_pa["is_batter_leones"] == True].copy()
            
            # Poblar lista de bateadores
            batters_count = leones_pa["batter_name"].value_counts()
            b_opts = ["🌟 Toda la Ofensiva de Leones"] + [f"{name} ({c} PA)" for name, c in batters_count.items()]
            self.batter_options = b_opts
            self.selected_batter = "🌟 Toda la Ofensiva de Leones"

            # 1. Calcular Splits para toda la ofensiva
            self.calculate_splits_for_target(leones_pa)

            # 2. Calcular LOB Tracker
            team_lob, df_lob_p = compute_lob_analytics(leones_pa)
            self.lob_total_ending = int(team_lob.get("total_lob_ending", 0))
            self.lob_risp_ending = int(team_lob.get("total_risp_lob_ending", 0))
            self.lob_risp_mid = int(team_lob.get("total_risp_lob_mid", 0))
            self.lob_risp_total = int(team_lob.get("total_risp_lob", 0))
            
            lob_list = []
            if not df_lob_p.empty:
                for _, r in df_lob_p.iterrows():
                    lob_list.append({
                        "batter": str(r["Bateador"]),
                        "pa": int(r["PA"]),
                        "risp_pa": int(r["PA en RISP"]),
                        "rbi": int(r["RBI"]),
                        "risp_avg": str(r["AVG en RISP"]),
                        "lob_ending": int(r["LOB al Terminar Inning"]),
                        "risp_lob_ending": int(r["RISP LOB al Terminar Inning"]),
                        "risp_lob_mid": int(r["RISP LOB Dentro de Inning"]),
                        "total_risp_lob": int(r["Total RISP LOB"]),
                    })
            self.lob_players_data = lob_list
            self.lob_chart_figure = build_top_risp_lob_chart(df_lob_p)

            # 3. Configurar BvP
            u_batters = sorted(leones_pa["batter_name"].unique().tolist())
            self.bvp_batter_options = u_batters
            if u_batters:
                self.selected_bvp_batter = u_batters[0]
                self.load_bvp_data(df_pa)

        except Exception as e:
            self.has_error = True
            self.error_title = "Error en Análisis Situacional"
            self.error_message = f"No se pudieron calcular los splits: {str(e)}"
        finally:
            self.is_loading = False

    def set_active_tab(self, tab: str):
        """Cambia de pestaña entre Splits, LOB Tracker y BvP."""
        self.active_tab = tab

    def set_selected_batter(self, batter_display: str):
        """Manejador al cambiar de bateador para splits situacionales."""
        self.selected_batter = batter_display
        df_pa = fetch_season_situational_data(self.selected_season, team_id=LEONES_TEAM_ID)
        leones_pa = df_pa[df_pa["is_batter_leones"] == True].copy()

        if batter_display == "🌟 Toda la Ofensiva de Leones":
            df_target = leones_pa
        else:
            # Extraer nombre antes de " (X PA)"
            b_name = batter_display.split(" (")[0]
            df_target = leones_pa[leones_pa["batter_name"] == b_name]

        self.calculate_splits_for_target(df_target)

    def calculate_splits_for_target(self, df_target: pd.DataFrame):
        """Calcula la tabla de splits y actualiza los KPIs para el bateador o colectivo seleccionado."""
        splits_df = compute_all_situational_splits(df_target)
        
        # Actualizar datos de tabla
        table_rows = []
        if not splits_df.empty:
            for _, r in splits_df.iterrows():
                table_rows.append({
                    "sit": str(r["Situación"]),
                    "pa": int(r["PA"]),
                    "ab": int(r["AB"]),
                    "h": int(r["H"]),
                    "h2b": int(r["2B"]),
                    "h3b": int(r["3B"]),
                    "hr": int(r["HR"]),
                    "bb": int(r["BB"]),
                    "so": int(r["SO"]),
                    "rbi": int(r["RBI"]),
                    "avg": str(r["AVG"]),
                    "obp": str(r["OBP"]),
                    "slg": str(r["SLG"]),
                    "ops": str(r["OPS"]),
                })
        self.splits_table_data = table_rows
        self.ops_chart_figure = build_ops_by_situation_chart(splits_df)

        # Actualizar KPIs
        m_all = summarize_slash_line(df_target)
        risp_df = df_target[df_target["is_risp"] == True]
        m_risp = summarize_slash_line(risp_df)
        outs2_risp = df_target[df_target["is_2_outs_risp"] == True]
        m_clutch = summarize_slash_line(outs2_risp)

        self.kpi_pa = str(m_all["PA"])
        self.kpi_avg = str(m_all["AVG"])
        self.kpi_risp_avg = str(m_risp["AVG"])
        diff_avg = m_risp["AVG_num"] - m_all["AVG_num"]
        self.kpi_risp_avg_delta = f"{diff_avg:+.3f}" if m_all["AB"] > 0 else "+.000"

        self.kpi_risp_ops = str(m_risp["OPS"])
        diff_ops = m_risp["OPS_num"] - m_all["OPS_num"]
        self.kpi_risp_ops_delta = f"{diff_ops:+.3f}" if m_all["AB"] > 0 else "+.000"

        self.kpi_clutch_avg = str(m_clutch["AVG"])
        diff_clutch = m_clutch["AVG_num"] - m_all["AVG_num"]
        self.kpi_clutch_avg_delta = f"{diff_clutch:+.3f}" if m_all["AB"] > 0 else "+.000"

        self.kpi_rbi = str(m_all["RBI"])

    def set_bvp_batter(self, batter_name: str):
        """Manejador para cambio de bateador en la matriz BvP."""
        self.selected_bvp_batter = batter_name
        df_pa = fetch_season_situational_data(self.selected_season, team_id=LEONES_TEAM_ID)
        self.load_bvp_data(df_pa)

    def set_rival_team(self, team_name: str):
        """Manejador para filtrar la tabla BvP por equipo rival."""
        self.selected_rival_team = team_name
        df_pa = fetch_season_situational_data(self.selected_season, team_id=LEONES_TEAM_ID)
        self.load_bvp_data(df_pa)

    def load_bvp_data(self, df_pa: pd.DataFrame):
        """Genera el resumen BvP para el bateador seleccionado y aplica el filtro de equipo rival."""
        if df_pa.empty or not self.selected_bvp_batter:
            self.bvp_table_data = []
            return

        leones_b = df_pa[df_pa["batter_name"] == self.selected_bvp_batter]
        if leones_b.empty:
            self.bvp_table_data = []
            return

        b_id = int(leones_b["batter_id"].iloc[0])
        bvp_df = compute_bvp_summary(df_pa, batter_id=b_id)
        if bvp_df.empty:
            self.bvp_table_data = []
            return

        # Actualizar opciones de rivales
        rivals = ["Todos los Rivales"] + sorted(list(bvp_df["Equipo Rival"].unique()))
        self.rival_team_options = rivals

        if self.selected_rival_team != "Todos los Rivales":
            bvp_df = bvp_df[bvp_df["Equipo Rival"] == self.selected_rival_team]

        rows = []
        for _, r in bvp_df.iterrows():
            opp_team = str(r["Equipo Rival"])
            rows.append({
                "logo": get_team_logo(opp_team, size=72),
                "pitcher": str(r["Lanzador Rival"]),
                "opp_team": opp_team,
                "pa": int(r["PA"]),
                "ab": int(r["AB"]),
                "h": int(r["H"]),
                "h2b": int(r["2B"]),
                "h3b": int(r["3B"]),
                "hr": int(r["HR"]),
                "bb": int(r["BB"]),
                "so": int(r["SO"]),
                "rbi": int(r["RBI"]),
                "avg": str(r["AVG"]),
                "obp": str(r["OBP"]),
                "slg": str(r["SLG"]),
                "ops": str(r["OPS"]),
            })
        self.bvp_table_data = rows
