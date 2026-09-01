# republicaraquistapp/state/wpa_state.py
"""
wpa_state.py
------------
Estado reactivo para el módulo de Win Expectancy (WE), Win Probability Added (WPA)
y Leverage Index (LI) de los Leones del Caracas en Reflex.
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
    CARD_BG,
    NAVY_PRIMARY
)
from core.supabase_client import init_supabase
from core.teams import get_team_name, get_team_logo
from core.wpa_engine import (
    process_game_wpa_advanced,
    calculate_player_game_wpa,
    get_season_wpa_leaderboard,
    format_base_state,
    TEAM_ID
)


def build_wp_evolution_chart(df_wpa: pd.DataFrame, matchup_title: str) -> go.Figure:
    """Construye la curva interactiva de Win Expectancy optimizada para Reflex."""
    fig = go.Figure()
    
    if df_wpa.empty:
        fig.update_layout(
            title="<b>Curva de Probabilidad de Victoria (Sin Datos)</b>",
            template="plotly_dark",
            paper_bgcolor="rgba(13, 21, 43, 0.95)",
            plot_bgcolor="rgba(13, 21, 43, 0.95)",
            height=450
        )
        return fig

    df_plot = df_wpa.copy()
    df_plot["play_number"] = range(1, len(df_plot) + 1)

    initial_row = pd.DataFrame([{
        "play_number": 0,
        "wp_after": 0.50,
        "inning": 1,
        "halfInning": "top",
        "score_str": "0-0",
        "batter": "Inicio del juego",
        "pitcher": "Abridor",
        "eventType": "Play Ball",
        "base_icons": "◇ ◇ ◇",
        "outs_before": 0,
        "li": 1.0,
        "wpa": 0.0
    }])
    df_plot = pd.concat([initial_row, df_plot], ignore_index=True)

    # 1. Área de ventaja Leones (> 50%)
    fig.add_trace(go.Scatter(
        x=df_plot["play_number"],
        y=df_plot["wp_after"].where(df_plot["wp_after"] >= 0.5, 0.5),
        fill="tonexty",
        fillcolor="rgba(253, 184, 39, 0.22)",
        line=dict(width=0),
        name="Ventaja Leones",
        showlegend=True,
        hoverinfo="skip"
    ))

    # 2. Línea neutral 50%
    fig.add_trace(go.Scatter(
        x=df_plot["play_number"],
        y=[0.5] * len(df_plot),
        mode="lines",
        line=dict(color="rgba(150, 150, 150, 0.5)", width=1.5, dash="dash"),
        name="Empate (50%)",
        showlegend=False,
        hoverinfo="skip"
    ))

    # 3. Área de ventaja Rival (< 50%)
    fig.add_trace(go.Scatter(
        x=df_plot["play_number"],
        y=df_plot["wp_after"].where(df_plot["wp_after"] < 0.5, 0.5),
        fill="tonexty",
        fillcolor="rgba(206, 17, 65, 0.20)",
        line=dict(width=0),
        name="Ventaja Rival",
        showlegend=True,
        hoverinfo="skip"
    ))

    # 4. Línea principal de Win Probability
    custom_text = [
        f"<b>Jugada #{r['play_number']}</b> ({'▲' if r['halfInning']=='top' else '▼'}Inn {r['inning']})<br>"
        f"⚾ <b>{r['batter']}</b> vs {r['pitcher']}<br>"
        f"📌 Evento: <b>{r['eventType']}</b><br>"
        f"🏃 Bases: {r.get('base_icons', '◇ ◇ ◇')} | Outs: {r.get('outs_before', 0)}<br>"
        f"🔢 Marcador: <b>{r['score_str']}</b><br>"
        f"📈 WP: <b>{r['wp_after']:.1%}</b> (WPA: <b>{r['wpa']:+.3f}</b>)<br>"
        f"⚡ Apalancamiento (LI): <b>{r['li']:.2f}x</b>"
        for _, r in df_plot.iterrows()
    ]

    fig.add_trace(go.Scatter(
        x=df_plot["play_number"],
        y=df_plot["wp_after"],
        mode="lines",
        name="Win Probability (Leones)",
        line=dict(color="#FDB827", width=3.5),
        hovertext=custom_text,
        hoverinfo="text"
    ))

    # 5. Puntos de alto impacto positivo (+WPA >= 0.08)
    top_pos = df_wpa[df_wpa["wpa"] >= 0.08]
    if not top_pos.empty:
        fig.add_trace(go.Scatter(
            x=top_pos["atbat_index"] + 1,
            y=top_pos["wp_after"],
            mode="markers",
            marker=dict(color="#10b981", size=10, symbol="triangle-up", line=dict(color="white", width=1.5)),
            name="Impacto Positivo (+WPA)",
            hoverinfo="skip"
        ))

    # 6. Puntos de alto impacto negativo (-WPA <= -0.08)
    top_neg = df_wpa[df_wpa["wpa"] <= -0.08]
    if not top_neg.empty:
        fig.add_trace(go.Scatter(
            x=top_neg["atbat_index"] + 1,
            y=top_neg["wp_after"],
            mode="markers",
            marker=dict(color="#ef4444", size=10, symbol="triangle-down", line=dict(color="white", width=1.5)),
            name="Impacto Negativo (-WPA)",
            hoverinfo="skip"
        ))

    final_wp = df_plot.iloc[-1]["wp_after"] if not df_plot.empty else 0.5
    res_str = "VICTORIA LEONES" if final_wp >= 0.5 else "DERROTA LEONES"
    res_color = "#10b981" if final_wp >= 0.5 else "#ef4444"

    fig.update_layout(
        title=dict(
            text=f"<b>Curva de Probabilidad de Victoria (Win Probability)</b><br><sub>{matchup_title}</sub>",
            font=dict(size=16, color="#FFFFFF"),
            x=0.04
        ),
        xaxis_title="Secuencia de Jugadas (Play-by-Play)",
        yaxis_title="Probabilidad de Ganar (Leones)",
        yaxis=dict(
            tickformat=".0%",
            range=[-0.02, 1.02],
            tickvals=[0, 0.25, 0.5, 0.75, 1.0],
            gridcolor="rgba(255, 255, 255, 0.1)",
            zerolinecolor="rgba(255, 255, 255, 0.2)",
            color="#94a3b8"
        ),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.1)",
            color="#94a3b8"
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(13, 21, 43, 0.95)",
        plot_bgcolor="rgba(13, 21, 43, 0.95)",
        height=460,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#e2e8f0")),
        hovermode="closest",
        margin=dict(l=20, r=20, t=60, b=40),
        annotations=[
            dict(
                x=0.98, y=0.95,
                xref="paper", yref="paper",
                text=f"<b>{res_str}</b>",
                showarrow=False,
                font=dict(size=12, color=res_color),
                bgcolor="rgba(7, 11, 25, 0.85)",
                bordercolor=res_color,
                borderwidth=1.5,
                borderpad=4
            )
        ]
    )
    return fig


def build_wpa_by_inning_chart(df_wpa: pd.DataFrame) -> go.Figure:
    """Construye el gráfico de barras de WPA neto acumulado por inning."""
    fig = go.Figure()
    if df_wpa.empty:
        fig.update_layout(
            title="<b>WPA por Inning (Sin Datos)</b>",
            template="plotly_dark",
            paper_bgcolor="rgba(13, 21, 43, 0.95)",
            plot_bgcolor="rgba(13, 21, 43, 0.95)",
            height=320
        )
        return fig

    wpa_by_inn = df_wpa.groupby("inning")["wpa"].sum().reset_index()
    colors = ["#FDB827" if x > 0 else "#CE1141" for x in wpa_by_inn["wpa"]]

    fig.add_trace(go.Bar(
        x=wpa_by_inn["inning"],
        y=wpa_by_inn["wpa"],
        marker_color=colors,
        text=wpa_by_inn["wpa"].apply(lambda x: f"{x:+.3f}"),
        textposition="outside",
        textfont=dict(size=11, color="#FFFFFF"),
        hovertemplate="Inning %{x}<br>WPA Neto: <b>%{y:+.3f}</b><extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="solid", line_color="rgba(255, 255, 255, 0.3)", line_width=1)
    fig.update_layout(
        title=dict(text="<b>WPA Neto Acumulado por Inning</b>", font=dict(size=14, color="#FFFFFF")),
        xaxis_title="Inning",
        yaxis_title="WPA Neto",
        xaxis=dict(tickmode="linear", tick0=1, dtick=1, gridcolor="rgba(255, 255, 255, 0.08)", color="#94a3b8"),
        yaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", color="#94a3b8"),
        template="plotly_dark",
        paper_bgcolor="rgba(13, 21, 43, 0.95)",
        plot_bgcolor="rgba(13, 21, 43, 0.95)",
        height=320,
        margin=dict(l=20, r=20, t=50, b=35),
        showlegend=False
    )
    return fig


class WpaState(AppState):
    """Estado reactivo para análisis de WPA, Apalancamiento y Win Expectancy."""

    # Pestaña activa: "juego" o "temporada"
    active_tab: str = "juego"

    # Juegos disponibles para selección
    game_options: List[Dict[str, Any]] = []
    game_labels: List[str] = []
    selected_game_label: str = ""
    selected_game_pk: int = 0
    matchup_title: str = ""

    # KPIs de Juego
    game_result_badge: str = "N/A"
    game_result_color: str = "gray"
    game_score_str: str = "0 - 0"
    game_max_li: str = "1.00x"
    game_top_hero: str = "N/A"
    game_top_hero_wpa: str = "+.000"
    game_top_villain: str = "N/A"
    game_top_villain_wpa: str = "-.000"

    # Tablas de Jugadas y Rendimiento por Jugador en el Juego
    pivotal_plays: List[Dict[str, Any]] = []
    player_game_wpa: List[Dict[str, Any]] = []

    # Gráficos Plotly
    we_chart_figure: go.Figure = go.Figure()
    inning_wpa_figure: go.Figure = go.Figure()

    # Métricas de Temporada Completa
    season_total_games: int = 0
    season_total_plays: int = 0
    season_batters: List[Dict[str, Any]] = []
    season_pitchers: List[Dict[str, Any]] = []
    season_top_positive_plays: List[Dict[str, Any]] = []
    season_top_negative_plays: List[Dict[str, Any]] = []

    def on_load_wpa(self):
        """Carga inicial del módulo WPA para la temporada seleccionada."""
        self.is_loading = True
        self.loading_text = "Calculando modelos de Win Expectancy y WPA..."
        try:
            self.load_games_list()
            self.load_season_leaderboards()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error en Módulo WPA"
            self.error_message = f"No se pudieron cargar los datos de WPA: {str(e)}"
        finally:
            self.is_loading = False

    def load_games_list(self):
        """Carga la lista de juegos de Leones en la temporada y selecciona el más reciente."""
        supabase = init_supabase()
        response = supabase.table("games") \
            .select("*") \
            .eq("season", self.selected_season) \
            .in_("status", ["Final", "Completed", "Completed Early", "Game Over"]) \
            .or_(f"home_team_id.eq.{TEAM_ID},away_team_id.eq.{TEAM_ID}") \
            .order("game_date", desc=True) \
            .execute()

        games = response.data or []
        opts = []
        for g in games:
            is_home = (g.get("home_team_id") == TEAM_ID)
            opp_name = g.get("away_team_name") if is_home else g.get("home_team_name")
            if not opp_name:
                opp_id = g.get("away_team_id") if is_home else g.get("home_team_id")
                opp_name = get_team_name(opp_id) if opp_id else "Rival"

            h_score = g.get("home_score", 0)
            a_score = g.get("away_score", 0)
            leo_score = h_score if is_home else a_score
            opp_score = a_score if is_home else h_score
            won = (leo_score > opp_score)
            res_sym = "✅ Victoria" if won else "❌ Derrota"
            score_txt = f"{leo_score}-{opp_score}"
            
            label = f"📅 {g.get('game_date', '')} | vs {opp_name} ({res_sym} {score_txt})"
            opts.append({
                "label": label,
                "game_pk": g.get("id"),
                "opp_name": opp_name,
                "date": g.get("game_date", ""),
                "won": won,
                "score_str": score_txt,
                "is_home": is_home,
                "leo_score": leo_score,
                "opp_score": opp_score,
            })

        self.game_options = opts
        self.game_labels = [o["label"] for o in opts]
        if opts:
            self.selected_game_label = opts[0]["label"]
            self.selected_game_pk = int(opts[0]["game_pk"])
            self.load_selected_game_wpa()
        else:
            self.we_chart_figure = build_wp_evolution_chart(pd.DataFrame(), "Sin juegos")
            self.inning_wpa_figure = build_wpa_by_inning_chart(pd.DataFrame())

    def set_selected_game(self, game_label: str):
        """Manejador para cambio de juego en el selector."""
        self.selected_game_label = game_label
        for item in self.game_options:
            if item["label"] == game_label:
                self.selected_game_pk = int(item["game_pk"])
                break
        self.load_selected_game_wpa()

    def set_active_tab(self, tab_name: str):
        """Cambia la pestaña activa entre juego individual y líderes de temporada."""
        self.active_tab = tab_name

    def load_selected_game_wpa(self):
        """Procesa el juego seleccionado y actualiza figuras y tablas reactivas."""
        if not self.selected_game_pk:
            return

        df_wpa, is_home, err = process_game_wpa_advanced(self.selected_game_pk)
        if err or df_wpa.empty:
            self.pivotal_plays = []
            self.player_game_wpa = []
            self.we_chart_figure = build_wp_evolution_chart(pd.DataFrame(), "Error al cargar")
            self.inning_wpa_figure = build_wpa_by_inning_chart(pd.DataFrame())
            return

        # Metadatos y título del juego
        curr_opt = next((x for x in self.game_options if x["game_pk"] == self.selected_game_pk), None)
        opp_name = curr_opt["opp_name"] if curr_opt else "Rival"
        g_date = curr_opt["date"] if curr_opt else ""
        won = curr_opt["won"] if curr_opt else (df_wpa.iloc[-1]["wp_after"] >= 0.5)

        self.matchup_title = f"Leones del Caracas vs. {opp_name} • {g_date}"
        self.game_score_str = curr_opt["score_str"] if curr_opt else f"{df_wpa.iloc[-1]['score_str']}"
        self.game_result_badge = "VICTORIA" if won else "DERROTA"
        self.game_result_color = "green" if won else "red"

        # Máximo apalancamiento registrado
        max_li_val = df_wpa["li"].max() if not df_wpa.empty else 1.0
        self.game_max_li = f"{max_li_val:.2f}x"

        # Jugadas Pivote (Top 5 positivas y Top 5 negativas)
        top_pos = df_wpa.nlargest(5, "wpa").copy()
        top_neg = df_wpa.nsmallest(5, "wpa").copy()
        pivotal_combined = pd.concat([top_pos, top_neg]).drop_duplicates(subset=["atbat_index"]).sort_values("atbat_index")

        pivotal_list = []
        for _, r in pivotal_combined.iterrows():
            wpa_v = float(r["wpa"])
            pivotal_list.append({
                "inning_str": f"{'▲' if r['halfInning']=='top' else '▼'} {r['inning']}",
                "outs_str": f"{r['outs_before']} Outs",
                "bases": r.get("base_icons", "◇ ◇ ◇"),
                "batter": str(r["batter"]),
                "pitcher": str(r["pitcher"]),
                "event": str(r["eventType"]),
                "desc": str(r.get("description", "")),
                "score": str(r["score_str"]),
                "wpa_str": f"{wpa_v:+.3f}",
                "wpa_color": "green" if wpa_v > 0 else "red",
                "li_str": f"{float(r['li']):.2f}x",
            })
        self.pivotal_plays = pivotal_list

        # Héroe y Villano del partido
        best_play = df_wpa.loc[df_wpa["wpa"].idxmax()] if not df_wpa.empty else None
        worst_play = df_wpa.loc[df_wpa["wpa"].idxmin()] if not df_wpa.empty else None

        if best_play is not None:
            self.game_top_hero = f"{best_play['batter']} ({best_play['eventType']})"
            self.game_top_hero_wpa = f"{float(best_play['wpa']):+.3f}"
        if worst_play is not None:
            self.game_top_villain = f"{worst_play['pitcher'] if worst_play['leones_batting'] else worst_play['batter']} ({worst_play['eventType']})"
            self.game_top_villain_wpa = f"{float(worst_play['wpa']):+.3f}"

        # Resumen de Rendimiento WPA / LI / Clutch por Jugador
        df_players = calculate_player_game_wpa(df_wpa)
        player_list = []
        if not df_players.empty:
            for _, p in df_players.iterrows():
                wpa_tot = float(p.get("WPA_total", 0))
                wpa_li_tot = float(p.get("WPA_LI_total", 0))
                clutch_val = float(p.get("Clutch", 0))
                player_list.append({
                    "player": str(p["player"]),
                    "wpa": f"{wpa_tot:+.3f}",
                    "wpa_color": "green" if wpa_tot > 0 else ("red" if wpa_tot < 0 else "gray"),
                    "wpa_li": f"{wpa_li_tot:+.3f}",
                    "clutch": f"{clutch_val:+.3f}",
                    "clutch_color": "green" if clutch_val > 0 else ("red" if clutch_val < 0 else "gray"),
                })
        self.player_game_wpa = player_list

        # Construir Gráficos Plotly
        self.we_chart_figure = build_wp_evolution_chart(df_wpa, self.matchup_title)
        self.inning_wpa_figure = build_wpa_by_inning_chart(df_wpa)

    def load_season_leaderboards(self):
        """Calcula rankings acumulados de WPA y jugadas históricas de la temporada."""
        data = get_season_wpa_leaderboard(self.selected_season)
        if not data:
            self.season_total_games = 0
            self.season_total_plays = 0
            self.season_batters = []
            self.season_pitchers = []
            self.season_top_positive_plays = []
            self.season_top_negative_plays = []
            return

        self.season_total_games = data.get("total_games", 0)
        self.season_total_plays = data.get("total_plays", 0)

        # 1. Bateadores
        batters_df = data.get("batters", pd.DataFrame())
        bat_list = []
        if not batters_df.empty:
            for _, r in batters_df.head(15).iterrows():
                wpa_v = float(r["WPA"])
                clutch_v = float(r["Clutch"])
                bat_list.append({
                    "player": str(r["batter"]),
                    "jj": int(r["JJ"]),
                    "pa": int(r["PA"]),
                    "wpa": f"{wpa_v:+.3f}",
                    "wpa_color": "green" if wpa_v > 0 else "red",
                    "wpa_li": f"{float(r['WPA_LI']):+.3f}",
                    "li_avg": f"{float(r['LI_avg']):.2f}",
                    "high_li_pa": int(r["High_LI_PA"]),
                    "clutch": f"{clutch_v:+.3f}",
                    "clutch_color": "green" if clutch_v > 0 else "red",
                })
        self.season_batters = bat_list

        # 2. Lanzadores
        pitchers_df = data.get("pitchers", pd.DataFrame())
        pit_list = []
        if not pitchers_df.empty:
            for _, r in pitchers_df.head(15).iterrows():
                wpa_v = float(r["WPA"])
                clutch_v = float(r["Clutch"])
                pit_list.append({
                    "player": str(r["pitcher"]),
                    "jj": int(r["JJ"]),
                    "bf": int(r["BF"]),
                    "wpa": f"{wpa_v:+.3f}",
                    "wpa_color": "green" if wpa_v > 0 else "red",
                    "wpa_li": f"{float(r['WPA_LI']):+.3f}",
                    "li_avg": f"{float(r['LI_avg']):.2f}",
                    "high_li_bf": int(r["High_LI_BF"]),
                    "clutch": f"{clutch_v:+.3f}",
                    "clutch_color": "green" if clutch_v > 0 else "red",
                })
        self.season_pitchers = pit_list

        # 3. Top Jugadas Positivas
        top_pos_df = data.get("top_positive_plays", pd.DataFrame())
        pos_list = []
        if not top_pos_df.empty:
            for _, r in top_pos_df.iterrows():
                pos_list.append({
                    "date": str(r.get("game_date", "")),
                    "inn": f"{'▲' if r['halfInning']=='top' else '▼'} {r['inning']}",
                    "batter": str(r["batter"]),
                    "pitcher": str(r["pitcher"]),
                    "event": str(r["eventType"]),
                    "desc": str(r.get("description", "")),
                    "wpa": f"{float(r['wpa']):+.3f}",
                    "li": f"{float(r['li']):.2f}x"
                })
        self.season_top_positive_plays = pos_list

        # 4. Top Jugadas Negativas
        top_neg_df = data.get("top_negative_plays", pd.DataFrame())
        neg_list = []
        if not top_neg_df.empty:
            for _, r in top_neg_df.iterrows():
                neg_list.append({
                    "date": str(r.get("game_date", "")),
                    "inn": f"{'▲' if r['halfInning']=='top' else '▼'} {r['inning']}",
                    "batter": str(r["batter"]),
                    "pitcher": str(r["pitcher"]),
                    "event": str(r["eventType"]),
                    "desc": str(r.get("description", "")),
                    "wpa": f"{float(r['wpa']):+.3f}",
                    "li": f"{float(r['li']):.2f}x"
                })
        self.season_top_negative_plays = neg_list
