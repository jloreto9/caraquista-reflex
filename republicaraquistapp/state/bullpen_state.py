# republicaraquistapp/state/bullpen_state.py
"""
bullpen_state.py
----------------
Estado reactivo para el análisis de corredores heredados del bullpen (IR / IRS)
y el seguimiento de órdenes al bate 1-9 y combinaciones de alineaciones titulares (Lineups).
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
from core.bullpen_lineups import (
    fetch_season_bullpen_and_lineups,
    compute_bullpen_inherited_stats,
    LEONES_TEAM_ID
)


def build_bullpen_ir_chart(df_irs_summary: pd.DataFrame) -> go.Figure:
    """Construye el gráfico de barras agrupadas de IR vs IRS por relevista."""
    fig = go.Figure()
    if df_irs_summary.empty:
        fig.update_layout(
            title="<b>Corredores Heredados por Relevista (Sin Datos)</b>",
            template="plotly_dark",
            paper_bgcolor="rgba(13, 21, 43, 0.95)",
            plot_bgcolor="rgba(13, 21, 43, 0.95)",
            height=360
        )
        return fig

    top_relievers = df_irs_summary.head(10)
    fig.add_trace(go.Bar(
        x=top_relievers["Lanzador Relevista"],
        y=top_relievers["Corredores Heredados (IR)"],
        name="Heredados (IR)",
        marker_color="#3b82f6",
        text=top_relievers["Corredores Heredados (IR)"],
        textposition="outside",
        textfont=dict(color="#FFFFFF", size=10)
    ))
    fig.add_trace(go.Bar(
        x=top_relievers["Lanzador Relevista"],
        y=top_relievers["Heredados Anotados (IRS)"],
        name="Anotaron (IRS)",
        marker_color="#ef4444",
        text=top_relievers["Heredados Anotados (IRS)"],
        textposition="outside",
        textfont=dict(color="#FFFFFF", size=10)
    ))

    fig.update_layout(
        barmode="group",
        title=dict(
            text="<b>📊 Comparativa: Heredados (IR) vs. Anotaron (IRS)</b>",
            font=dict(size=14, color="#FFFFFF")
        ),
        xaxis_title="",
        yaxis_title="Cantidad de Corredores",
        xaxis=dict(color="#FFFFFF", tickangle=-25),
        yaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", color="#94a3b8"),
        template="plotly_dark",
        paper_bgcolor="rgba(13, 21, 43, 0.95)",
        plot_bgcolor="rgba(13, 21, 43, 0.95)",
        height=380,
        margin=dict(l=15, r=15, t=45, b=65),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#e2e8f0"))
    )
    return fig


def build_lineup_heatmap_chart(df_starters: pd.DataFrame) -> go.Figure:
    """Construye la matriz de calor (Heatmap) de titularidades del 1ro al 9no bate."""
    fig = go.Figure()
    if df_starters.empty:
        fig.update_layout(
            title="<b>Matriz de Titularidades (Sin Datos)</b>",
            template="plotly_dark",
            paper_bgcolor="rgba(13, 21, 43, 0.95)",
            plot_bgcolor="rgba(13, 21, 43, 0.95)",
            height=450
        )
        return fig

    pivot = df_starters.pivot_table(index="Jugador", columns="Turno_Num", aggfunc="size", fill_value=0)
    ordered_cols = [i for i in range(1, 10) if i in pivot.columns]
    col_labels = [f"{i}º Bate" for i in ordered_cols]

    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by="Total", ascending=False)
    top_players = pivot.head(15).iloc[::-1]  # Invertir para visualización top-down

    z_values = top_players[ordered_cols].values
    y_labels = top_players.index.tolist()

    fig = px.imshow(
        z_values,
        x=col_labels,
        y=y_labels,
        color_continuous_scale="Blues",
        text_auto=True,
        labels=dict(x="Turno al Bate", y="Jugador", color="Juegos Titular")
    )
    fig.update_layout(
        title=dict(
            text="<b>📊 Distribución de Titularidades en el Orden al Bate (1ro al 9no)</b>",
            font=dict(size=14, color="#FFFFFF")
        ),
        xaxis_title="Turno en el Orden al Bate",
        yaxis_title="",
        xaxis=dict(color="#FFFFFF"),
        yaxis=dict(color="#FFFFFF"),
        template="plotly_dark",
        paper_bgcolor="rgba(13, 21, 43, 0.95)",
        plot_bgcolor="rgba(13, 21, 43, 0.95)",
        height=480,
        margin=dict(l=15, r=15, t=45, b=35),
        coloraxis_showscale=False
    )
    return fig


class BullpenState(AppState):
    """Estado reactivo para el análisis de Bullpen (IR/IRS) y Lineups 1-9."""

    # Pestaña activa principal: "bullpen" o "lineups"
    active_tab: str = "bullpen"

    # ── Módulo Bullpen (IR / IRS) ───────────────────────────────────────────
    kpi_tot_ir: int = 0
    kpi_tot_irs: int = 0
    kpi_irs_pct: str = "0.0%"
    kpi_best_reliever: str = "N/A"
    kpi_best_reliever_sub: str = "0% IRS"

    relievers_table_data: List[Dict[str, Any]] = []
    bullpen_chart_figure: go.Figure = go.Figure()
    detailed_inherited_logs: List[Dict[str, Any]] = []

    # ── Módulo Lineups & Órdenes al Bate ────────────────────────────────────
    lineup_subtab: str = "card"  # "card", "frequent", "heatmap", "player"

    lineup_kpi_total_games: int = 0
    lineup_kpi_total_players: int = 0
    lineup_kpi_top_starter: str = "N/A"
    lineup_kpi_top_starter_jj: str = "0 JJ"
    lineup_kpi_top_cleanup: str = "N/A"
    lineup_kpi_top_cleanup_jj: str = "0 JJ"

    # Tarjeta de Juego (Dugout Scorecard)
    game_lineup_options: List[str] = []
    selected_game_lineup_label: str = ""
    selected_game_card_title: str = "Alineación Titular"
    selected_game_card_date: str = ""
    selected_game_card_score: str = ""
    selected_game_card_result: str = ""
    selected_game_card_won: bool = True
    selected_game_opp_name: str = "Rival"
    selected_game_opp_logo: str = ""
    selected_game_starters: List[Dict[str, Any]] = []

    # Alineaciones Más Frecuentes
    top_frequent_lineups: List[Dict[str, Any]] = []

    # Matriz de Calor
    lineup_heatmap_figure: go.Figure = go.Figure()

    # Análisis por Jugador Titular
    player_lineup_options: List[str] = []
    selected_player_lineup: str = ""
    player_impact_games: int = 0
    player_impact_record: str = "0 - 0"
    player_impact_pct: str = ".000"
    player_order_breakdown: List[Dict[str, Any]] = []

    def on_load_bullpen(self):
        """Carga inicial de datos de bullpen y lineups."""
        self.is_loading = True
        self.loading_text = "Calculando efectividad de relevistas y combinaciones de lineups..."
        try:
            df_bp, lineups_data = fetch_season_bullpen_and_lineups(
                self.selected_season,
                team_id=LEONES_TEAM_ID,
                cache_version="v2_with_scores"
            )

            # 1. Procesar Bullpen
            if not df_bp.empty:
                df_irs = compute_bullpen_inherited_stats(df_bp)
                tot_ir = int(df_bp["inherited_runners"].sum())
                tot_irs = int(df_bp["inherited_scored"].sum())
                irs_pct = round(tot_irs / tot_ir * 100, 1) if tot_ir > 0 else 0.0

                self.kpi_tot_ir = tot_ir
                self.kpi_tot_irs = tot_irs
                self.kpi_irs_pct = f"{irs_pct}%"

                # Mejor relevista con >= 5 IR
                rel_q = df_irs[df_irs["Corredores Heredados (IR)"] >= 5].sort_values(
                    by=["% Anotados (IRS%)", "Corredores Heredados (IR)"],
                    ascending=[True, False]
                )
                if not rel_q.empty:
                    b_rel = rel_q.iloc[0]
                    self.kpi_best_reliever = str(b_rel["Lanzador Relevista"])
                    self.kpi_best_reliever_sub = f"{b_rel['% Anotados (IRS%)']}% IRS ({int(b_rel['Heredados Anotados (IRS)'])}/{int(b_rel['Corredores Heredados (IR)'])} anotaron)"
                else:
                    self.kpi_best_reliever = "N/A"
                    self.kpi_best_reliever_sub = "Sin calificados (mín. 5 IR)"

                # Tabla de Relevistas
                r_rows = []
                for _, r in df_irs.iterrows():
                    r_rows.append({
                        "pitcher": str(r["Lanzador Relevista"]),
                        "appearances": int(r["Juegos con Herencia"]),
                        "ir": int(r["Corredores Heredados (IR)"]),
                        "irs": int(r["Heredados Anotados (IRS)"]),
                        "irs_pct": f"{float(r['% Anotados (IRS%)']):.1f}%",
                    })
                self.relievers_table_data = r_rows
                self.bullpen_chart_figure = build_bullpen_ir_chart(df_irs)

                # Log Detallado
                log_rows = []
                for _, r in df_bp.head(50).iterrows():
                    log_rows.append({
                        "date": str(r.get("game_date", "")),
                        "opp": str(r.get("opposing_team", "")),
                        "inning": f"Inn {r.get('inning', 1)}",
                        "pitcher": str(r.get("pitcher_name", "")),
                        "ir": int(r.get("inherited_runners", 0)),
                        "irs": int(r.get("inherited_scored", 0)),
                    })
                self.detailed_inherited_logs = log_rows

            # 2. Procesar Lineups
            if lineups_data:
                self.process_lineups_dataset(lineups_data)

        except Exception as e:
            self.has_error = True
            self.error_title = "Error en Módulo Bullpen"
            self.error_message = f"No se pudieron procesar los datos de bullpen: {str(e)}"
        finally:
            self.is_loading = False

    def set_active_tab(self, tab_name: str):
        """Cambia entre la vista de Bullpen y la de Lineups."""
        self.active_tab = tab_name

    def set_lineup_subtab(self, subtab_name: str):
        """Cambia entre las sub-vistas del tracker de alineaciones."""
        self.lineup_subtab = subtab_name

    def process_lineups_dataset(self, lineups_data: list):
        """Procesa y estructura los registros de alineaciones de toda la temporada."""
        lineup_records = []
        starters_flat = []

        pos_full_map = {
            "1B": "Primera Base", "2B": "Segunda Base", "3B": "Tercera Base",
            "SS": "Campocorto", "LF": "Jardín Izquierdo", "CF": "Jardín Central",
            "RF": "Jardín Derecho", "C": "Receptor", "DH": "Bateador Designado"
        }

        for item in lineups_data:
            g_date = item["game_date"]
            opp = item["opposing_team"]
            won = item["leones_won"]
            score_leo = item.get("leones_score", 0)
            score_opp = item.get("opposing_score", 0)
            score_str = item.get("score_str", f"{score_leo}-{score_opp}")
            full_score = item.get("full_score_str", f"Leones {score_leo} - {score_opp} {opp}")
            starters = item.get("starters", [])

            # Agregar nombre completo y color de badge a cada titular
            formatted_starters = []
            for s in starters:
                ord_num = s["order"]
                b_col = "#3b82f6" if ord_num <= 3 else ("#f59e0b" if ord_num == 4 else "#8b5cf6")
                formatted_starters.append({
                    "order": ord_num,
                    "order_str": f"#{ord_num}",
                    "player_name": s["player_name"],
                    "position": s["position"],
                    "position_full": f"{s['position']} • {pos_full_map.get(s['position'], s['position'])}",
                    "badge_color": b_col
                })

            game_entry = {
                "game_pk": item["game_pk"],
                "game_date": g_date,
                "opposing_team": opp,
                "won": 1 if won else 0,
                "score_str": score_str,
                "full_score_str": full_score,
                "result_str": "VICTORIA" if won else "DERROTA",
                "starters": formatted_starters
            }
            lineup_records.append(game_entry)

            for s in starters:
                starters_flat.append({
                    "Jugador": s["player_name"],
                    "Turno_Num": s["order"],
                    "Turno": f"{s['order']}º Bate",
                    "Posicion": s["position"],
                    "game_date": g_date,
                    "opposing_team": opp,
                    "Marcador": score_str,
                    "won": 1 if won else 0,
                    "lost": 0 if won else 1
                })

        df_starters = pd.DataFrame(starters_flat)
        df_games_lu = pd.DataFrame(lineup_records)

        self.lineup_kpi_total_games = len(df_games_lu)
        self.lineup_kpi_total_players = df_starters["Jugador"].nunique()

        top_titular = df_starters["Jugador"].value_counts().index[0]
        top_titular_jj = df_starters["Jugador"].value_counts().iloc[0]
        self.lineup_kpi_top_starter = str(top_titular)
        self.lineup_kpi_top_starter_jj = f"{top_titular_jj} JJ"

        cleanups = df_starters[df_starters["Turno_Num"] == 4]["Jugador"].value_counts()
        if not cleanups.empty:
            self.lineup_kpi_top_cleanup = str(cleanups.index[0])
            self.lineup_kpi_top_cleanup_jj = f"{cleanups.iloc[0]} titularidades"
        else:
            self.lineup_kpi_top_cleanup = "N/A"
            self.lineup_kpi_top_cleanup_jj = "0"

        # 1. Opciones para el selector de tarjetas de juego
        g_opts = []
        for g in lineup_records:
            sym = "✅ Victoria" if g["won"] == 1 else "❌ Derrota"
            lbl = f"📅 {g['game_date']} | vs {g['opposing_team']} ({sym} {g['score_str']})"
            g_opts.append(lbl)

        self.game_lineup_options = g_opts
        if g_opts:
            self.selected_game_lineup_label = g_opts[0]
            self.update_selected_game_card(lineup_records[0])

        # 2. Agrupación de alineaciones más frecuentes
        lineup_groups = {}
        for g in lineup_records:
            starters = g["starters"]
            key = tuple((s["order"], s["player_name"], s["position"]) for s in sorted(starters, key=lambda x: x["order"]))
            if key not in lineup_groups:
                lineup_groups[key] = {
                    "games_count": 0,
                    "wins": 0,
                    "losses": 0,
                    "starters": sorted(starters, key=lambda x: x["order"])
                }
            is_w = (g["won"] == 1)
            lineup_groups[key]["games_count"] += 1
            if is_w:
                lineup_groups[key]["wins"] += 1
            else:
                lineup_groups[key]["losses"] += 1

        sorted_lu = sorted(lineup_groups.values(), key=lambda x: (x["games_count"], x["wins"]), reverse=True)
        top_list = []
        for idx, item in enumerate(sorted_lu[:10], 1):
            pct = item["wins"] / item["games_count"] if item["games_count"] > 0 else 0
            s_preview = ", ".join([f"{s['order']}. {s['player_name']}" for s in item["starters"][:4]]) + "..."
            top_list.append({
                "rank_str": f"Alineación #{idx}",
                "summary": f"{item['games_count']} JJ • {item['wins']}V - {item['losses']}D (.{int(pct*1000):03d} PCT)",
                "preview": s_preview,
                "starters": item["starters"],
            })
        self.top_frequent_lineups = top_list

        # 3. Matriz de Calor
        self.lineup_heatmap_figure = build_lineup_heatmap_chart(df_starters)

        # 4. Jugadores disponibles para análisis individual
        p_list = sorted(df_starters["Jugador"].unique().tolist())
        self.player_lineup_options = p_list
        if p_list:
            self.selected_player_lineup = p_list[0]
            self.update_player_impact(p_list[0], df_starters)

    def set_selected_game_lineup(self, label: str):
        """Manejador para cambio de juego en la tarjeta de alineación."""
        self.selected_game_lineup_label = label
        df_bp, lineups_data = fetch_season_bullpen_and_lineups(
            self.selected_season,
            team_id=LEONES_TEAM_ID,
            cache_version="v2_with_scores"
        )
        if not lineups_data:
            return

        for item in lineups_data:
            g_date = item["game_date"]
            opp = item["opposing_team"]
            won = item["leones_won"]
            score_leo = item.get("leones_score", 0)
            score_opp = item.get("opposing_score", 0)
            score_str = item.get("score_str", f"{score_leo}-{score_opp}")
            sym = "✅ Victoria" if won else "❌ Derrota"
            lbl = f"📅 {g_date} | vs {opp} ({sym} {score_str})"
            if lbl == label:
                self.update_selected_game_card({
                    "game_date": g_date,
                    "opposing_team": opp,
                    "won": 1 if won else 0,
                    "score_str": score_str,
                    "full_score_str": item.get("full_score_str", f"Leones {score_leo} - {score_opp} {opp}"),
                    "result_str": "VICTORIA" if won else "DERROTA",
                    "starters": item.get("starters", [])
                })
                break

    def update_selected_game_card(self, g: dict):
        """Actualiza los datos reactivos de la tarjeta Dugout."""
        pos_full_map = {
            "1B": "Primera Base", "2B": "Segunda Base", "3B": "Tercera Base",
            "SS": "Campocorto", "LF": "Jardín Izquierdo", "CF": "Jardín Central",
            "RF": "Jardín Derecho", "C": "Receptor", "DH": "Bateador Designado"
        }
        self.selected_game_card_title = f"Alineación Titular vs {g.get('opposing_team', 'Rival')}"
        self.selected_game_card_date = g.get("game_date", "")
        self.selected_game_card_score = g.get("full_score_str", "")
        self.selected_game_card_result = g.get("result_str", "")
        self.selected_game_card_won = (g.get("won") == 1)
        self.selected_game_opp_name = g.get("opposing_team", "Rival")
        self.selected_game_opp_logo = get_team_logo(g.get("opposing_team", ""), size=144)

        raw_starters = g.get("starters", [])
        formatted = []
        for s in raw_starters:
            ord_num = s["order"] if isinstance(s, dict) and "order" in s else 1
            p_name = s["player_name"] if isinstance(s, dict) and "player_name" in s else ""
            pos = s["position"] if isinstance(s, dict) and "position" in s else ""
            b_col = "#3b82f6" if ord_num <= 3 else ("#f59e0b" if ord_num == 4 else "#8b5cf6")
            formatted.append({
                "order": ord_num,
                "order_str": f"#{ord_num}",
                "player_name": p_name,
                "position": pos,
                "position_full": f"{pos} • {pos_full_map.get(pos, pos)}",
                "badge_color": b_col
            })
        self.selected_game_starters = formatted

    def set_selected_player_lineup(self, player_name: str):
        """Manejador para cambio de jugador en la pestaña de impacto individual."""
        self.selected_player_lineup = player_name
        df_bp, lineups_data = fetch_season_bullpen_and_lineups(
            self.selected_season,
            team_id=LEONES_TEAM_ID,
            cache_version="v2_with_scores"
        )
        if not lineups_data:
            return

        starters_flat = []
        for item in lineups_data:
            g_date = item["game_date"]
            opp = item["opposing_team"]
            won = item["leones_won"]
            score_leo = item.get("leones_score", 0)
            score_opp = item.get("opposing_score", 0)
            score_str = item.get("score_str", f"{score_leo}-{score_opp}")
            for s in item.get("starters", []):
                starters_flat.append({
                    "Jugador": s["player_name"],
                    "Turno_Num": s["order"],
                    "Turno": f"{s['order']}º Bate",
                    "Posicion": s["position"],
                    "game_date": g_date,
                    "opposing_team": opp,
                    "Marcador": score_str,
                    "won": 1 if won else 0,
                    "lost": 0 if won else 1
                })
        self.update_player_impact(player_name, pd.DataFrame(starters_flat))

    def update_player_impact(self, player_name: str, df_starters: pd.DataFrame):
        """Calcula el récord y desglose por turno para el jugador seleccionado."""
        if df_starters.empty:
            return

        df_p = df_starters[df_starters["Jugador"] == player_name]
        if df_p.empty:
            self.player_impact_games = 0
            self.player_impact_record = "0 - 0"
            self.player_impact_pct = ".000"
            self.player_order_breakdown = []
            return

        tot_g = len(df_p)
        w = int(df_p["won"].sum())
        l = int(df_p["lost"].sum())
        pct = (w / tot_g) if tot_g > 0 else 0

        self.player_impact_games = tot_g
        self.player_impact_record = f"{w} - {l}"
        self.player_impact_pct = f".{int(pct*1000):03d}"

        breakdown = df_p.groupby("Turno").agg(
            Titularidades=("won", "count"),
            Victorias=("won", "sum"),
            Derrotas=("lost", "sum")
        ).reset_index().sort_values(by="Titularidades", ascending=False)

        b_list = []
        for _, r in breakdown.iterrows():
            t_w = int(r["Victorias"])
            t_cnt = int(r["Titularidades"])
            t_pct = (t_w / t_cnt) if t_cnt > 0 else 0
            b_list.append({
                "slot": str(r["Turno"]),
                "starts": t_cnt,
                "wins": t_w,
                "losses": int(r["Derrotas"]),
                "pct": f".{int(t_pct*1000):03d}"
            })
        self.player_order_breakdown = b_list
