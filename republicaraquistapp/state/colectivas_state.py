# republicaraquistapp/state/colectivas_state.py
"""
colectivas_state.py
-------------------
Estado reactivo para la vista de Estadísticas Colectivas (/colectivas).
Cubre:
1. Bateo Colectivo (8 equipos de la LVBP: AVG, OBP, SLG, OPS, HR, R, H, 2B, 3B, RBI, BB, SO, BR, LOB, BABIP).
2. Pitcheo Colectivo (8 equipos de la LVBP: ERA, WHIP, SV, HLD, BS, IP, H, R, CL, BB, SO, HR, K/9, BB/9, K/BB, BAA).
3. Fildeo Colectivo (8 equipos de la LVBP: E, FPCT, DP, TP, PB, CS, SB, CS%, RF/9).
4. Gráficos interactivos comparativos horizontales en Plotly (rx.plotly) con selector de métricas.
5. Soporte para todas las fases del torneo (Temporada Regular, Round Robin, Serie Final, Comodín, Todas).
"""

from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from core.supabase_client import (
    get_collective_team_stats,
    get_available_seasons,
    get_current_season,
)
from core.teams import get_team_logo, get_team_abbr, get_team_name, LVBP_TEAMS
from republicaraquistapp.state.base_state import AppState


class ColectivasState(AppState):
    """Estado reactivo para estadísticas colectivas de los 8 equipos LVBP."""

    # ── Pestaña Activa ──────────────────────────────────────────────────────────
    active_tab: str = "bateo"  # "bateo", "pitcheo", "fildeo"

    # ── Fase del Torneo ────────────────────────────────────────────────────────
    selected_phase: str = "R"  # "R", "L", "F", "D", "all"
    selected_phase_name: str = "Temporada Regular"
    phase_options: List[str] = [
        "Temporada Regular",
        "Todos Contra Todos (Round Robin)",
        "Serie Final",
        "Serie Comodín (Wild Card)",
        "Todas las Fases",
    ]
    phase_map: Dict[str, str] = {
        "Temporada Regular": "R",
        "Todos Contra Todos (Round Robin)": "L",
        "Serie Final": "F",
        "Serie Comodín (Wild Card)": "D",
        "Todas las Fases": "all",
    }

    # ── Métricas Seleccionadas para Gráficos ────────────────────────────────────
    selected_batting_metric: str = "ops"
    selected_pitching_metric: str = "era"
    selected_fielding_metric: str = "fielding"

    # ── Listas de Datos Procesadas ─────────────────────────────────────────────
    collective_batting_data: List[Dict[str, Any]] = []
    collective_pitching_data: List[Dict[str, Any]] = []
    collective_fielding_data: List[Dict[str, Any]] = []

    # ── Tarjetas de Líderes Colectivos ─────────────────────────────────────────
    batting_kpis: Dict[str, Any] = {
        "avg_val": ".000", "avg_team": "-",
        "ops_val": ".000", "ops_team": "-",
        "hr_val": "0", "hr_team": "-",
        "r_val": "0", "r_team": "-",
    }
    pitching_kpis: Dict[str, Any] = {
        "era_val": "0.00", "era_team": "-",
        "whip_val": "0.00", "whip_team": "-",
        "so_val": "0", "so_team": "-",
        "sv_val": "0", "sv_team": "-",
    }
    fielding_kpis: Dict[str, Any] = {
        "fpct_val": "1.000", "fpct_team": "-",
        "e_val": "0", "e_team": "-",
        "dp_val": "0", "dp_team": "-",
        "cs_pct_val": ".000", "cs_pct_team": "-",
    }

    # ── Handler Principal on_load ───────────────────────────────────────────────
    def on_load(self):
        """Carga inicial de estadísticas colectivas."""
        self.is_loading = True
        self.has_error = False
        try:
            self.load_collective_stats()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error al Cargar Estadísticas Colectivas"
            self.error_message = str(e)
        finally:
            self.is_loading = False

    # ── Carga y Formateo de Estadísticas Colectivas ─────────────────────────────
    def load_collective_stats(self):
        """Consulta datos colectivos de bateo, pitcheo y fildeo para los 8 equipos."""
        season = self.selected_season
        phase = self.selected_phase

        # 1. BATEO COLECTIVO
        df_bat = get_collective_team_stats(season=season, phase=phase, group="hitting")
        if df_bat is not None and not df_bat.empty:
            bat_list = []
            for _, row in df_bat.iterrows():
                t_id = int(row.get("team_id", 0))
                t_name = str(row.get("team_name", "Equipo"))
                logo = get_team_logo(t_id if t_id > 0 else t_name, size=72)
                abbr = get_team_abbr(t_id if t_id > 0 else t_name)
                is_leones = (t_id == 695 or "Leones" in t_name)

                gp = int(row.get("gamesPlayed", 0))
                pa = int(row.get("plateAppearances", 0))
                ab = int(row.get("atBats", 0))
                r = int(row.get("runs", 0))
                h = int(row.get("hits", 0))
                d2 = int(row.get("doubles", 0))
                d3 = int(row.get("triples", 0))
                hr = int(row.get("homeRuns", 0))
                rbi = int(row.get("rbi", 0))
                bb = int(row.get("baseOnBalls", 0))
                so = int(row.get("strikeOuts", 0))
                sb = int(row.get("stolenBases", 0))
                cs = int(row.get("caughtStealing", 0))
                lob = int(row.get("leftOnBase", 0))

                avg = float(row.get("avg", 0.0))
                obp = float(row.get("obp", 0.0))
                slg = float(row.get("slg", 0.0))
                ops = float(row.get("ops", 0.0))
                babip = float(row.get("babip", 0.0))

                bat_list.append({
                    "team_id": t_id,
                    "team_name": t_name,
                    "team_abbr": abbr,
                    "logo": logo,
                    "is_leones": is_leones,
                    "games": gp,
                    "pa": pa,
                    "ab": ab,
                    "r": r,
                    "h": h,
                    "doubles": d2,
                    "triples": d3,
                    "hr": hr,
                    "rbi": rbi,
                    "bb": bb,
                    "so": so,
                    "sb": sb,
                    "cs": cs,
                    "lob": lob,
                    "avg": avg,
                    "avg_str": f"{avg:.3f}".replace("0.", "."),
                    "obp": obp,
                    "obp_str": f"{obp:.3f}".replace("0.", "."),
                    "slg": slg,
                    "slg_str": f"{slg:.3f}".replace("0.", "."),
                    "ops": ops,
                    "ops_str": f"{ops:.3f}",
                    "babip": babip,
                    "babip_str": f"{babip:.3f}".replace("0.", "."),
                })

            # Ordenar por OPS descendente
            self.collective_batting_data = sorted(bat_list, key=lambda x: x["ops"], reverse=True)

            # Extraer Líderes
            if bat_list:
                l_avg = max(bat_list, key=lambda x: x["avg"])
                l_ops = max(bat_list, key=lambda x: x["ops"])
                l_hr = max(bat_list, key=lambda x: x["hr"])
                l_r = max(bat_list, key=lambda x: x["r"])
                self.batting_kpis = {
                    "avg_val": l_avg["avg_str"], "avg_team": l_avg["team_name"],
                    "ops_val": l_ops["ops_str"], "ops_team": l_ops["team_name"],
                    "hr_val": f"{l_hr['hr']} HR", "hr_team": l_hr["team_name"],
                    "r_val": f"{l_r['r']} CA", "r_team": l_r["team_name"],
                }
        else:
            self.collective_batting_data = []

        # 2. PITCHEO COLECTIVO
        df_pit = get_collective_team_stats(season=season, phase=phase, group="pitching")
        if df_pit is not None and not df_pit.empty:
            pit_list = []
            for _, row in df_pit.iterrows():
                t_id = int(row.get("team_id", 0))
                t_name = str(row.get("team_name", "Equipo"))
                logo = get_team_logo(t_id if t_id > 0 else t_name, size=72)
                abbr = get_team_abbr(t_id if t_id > 0 else t_name)
                is_leones = (t_id == 695 or "Leones" in t_name)

                gp = int(row.get("gamesPlayed", 0))
                w = int(row.get("wins", 0))
                l = int(row.get("losses", 0))
                sv = int(row.get("saves", 0))
                hld = int(row.get("holds", 0))
                bs = int(row.get("blownSaves", 0))
                ip = float(row.get("inningsPitched", 0.0))
                h = int(row.get("hits", 0))
                r = int(row.get("runs", 0))
                er = int(row.get("earnedRuns", 0))
                bb = int(row.get("baseOnBalls", 0))
                so = int(row.get("strikeOuts", 0))
                hr = int(row.get("homeRuns", 0))

                era = float(row.get("era", 0.0))
                whip = float(row.get("whip", 0.0))
                k9 = float(row.get("strikeoutsPer9Inn", 0.0))
                bb9 = float(row.get("walksPer9Inn", 0.0))
                k_bb = float(row.get("strikeoutWalkRatio", 0.0))
                baa = float(row.get("avg", 0.0))

                pit_list.append({
                    "team_id": t_id,
                    "team_name": t_name,
                    "team_abbr": abbr,
                    "logo": logo,
                    "is_leones": is_leones,
                    "games": gp,
                    "wins": w,
                    "losses": l,
                    "sv": sv,
                    "holds": hld,
                    "blown_saves": bs,
                    "ip": ip,
                    "ip_str": f"{ip:.1f}",
                    "h": h,
                    "r": r,
                    "er": er,
                    "bb": bb,
                    "so": so,
                    "hr": hr,
                    "era": era,
                    "era_str": f"{era:.2f}",
                    "whip": whip,
                    "whip_str": f"{whip:.2f}",
                    "k9": k9,
                    "k9_str": f"{k9:.2f}",
                    "bb9": bb9,
                    "bb9_str": f"{bb9:.2f}",
                    "k_bb": k_bb,
                    "k_bb_str": f"{k_bb:.2f}",
                    "baa": baa,
                    "baa_str": f"{baa:.3f}".replace("0.", "."),
                })

            # Ordenar por ERA ascendente (menor es mejor)
            self.collective_pitching_data = sorted(pit_list, key=lambda x: x["era"], reverse=False)

            if pit_list:
                l_era = min(pit_list, key=lambda x: x["era"])
                l_whip = min(pit_list, key=lambda x: x["whip"])
                l_so = max(pit_list, key=lambda x: x["so"])
                l_sv = max(pit_list, key=lambda x: x["sv"])
                self.pitching_kpis = {
                    "era_val": l_era["era_str"], "era_team": l_era["team_name"],
                    "whip_val": l_whip["whip_str"], "whip_team": l_whip["team_name"],
                    "so_val": f"{l_so['so']} K", "so_team": l_so["team_name"],
                    "sv_val": f"{l_sv['sv']} SV", "sv_team": l_sv["team_name"],
                }
        else:
            self.collective_pitching_data = []

        # 3. FILDEO COLECTIVO
        df_fld = get_collective_team_stats(season=season, phase=phase, group="fielding")
        if df_fld is not None and not df_fld.empty:
            fld_list = []
            for _, row in df_fld.iterrows():
                t_id = int(row.get("team_id", 0))
                t_name = str(row.get("team_name", "Equipo"))
                logo = get_team_logo(t_id if t_id > 0 else t_name, size=72)
                abbr = get_team_abbr(t_id if t_id > 0 else t_name)
                is_leones = (t_id == 695 or "Leones" in t_name)

                gp = int(row.get("gamesPlayed", 0))
                inn = str(row.get("innings", "0.0"))
                po = int(row.get("putOuts", 0))
                a = int(row.get("assists", 0))
                e = int(row.get("errors", 0))
                tc = int(row.get("chances", 0))
                dp = int(row.get("doublePlays", 0))
                tp = int(row.get("triplePlays", 0))
                pb = int(row.get("passedBall", 0))
                cs = int(row.get("caughtStealing", 0))
                sb = int(row.get("stolenBases", 0))

                fpct = float(row.get("fielding", 0.0))
                cs_pct = float(row.get("caughtStealingPercentage", 0.0))
                rf9 = float(row.get("rangeFactorPer9Inn", 0.0))

                fld_list.append({
                    "team_id": t_id,
                    "team_name": t_name,
                    "team_abbr": abbr,
                    "logo": logo,
                    "is_leones": is_leones,
                    "games": gp,
                    "innings": inn,
                    "po": po,
                    "a": a,
                    "e": e,
                    "tc": tc,
                    "dp": dp,
                    "tp": tp,
                    "pb": pb,
                    "cs": cs,
                    "sb": sb,
                    "fpct": fpct,
                    "fpct_str": f"{fpct:.3f}".replace("0.", "."),
                    "cs_pct": cs_pct,
                    "cs_pct_str": f"{cs_pct:.3f}".replace("0.", "."),
                    "rf9": rf9,
                    "rf9_str": f"{rf9:.2f}",
                })

            # Ordenar por FPCT descendente
            self.collective_fielding_data = sorted(fld_list, key=lambda x: x["fpct"], reverse=True)

            if fld_list:
                l_fpct = max(fld_list, key=lambda x: x["fpct"])
                l_e = min(fld_list, key=lambda x: x["e"])
                l_dp = max(fld_list, key=lambda x: x["dp"])
                l_cs = max(fld_list, key=lambda x: x["cs_pct"])
                self.fielding_kpis = {
                    "fpct_val": l_fpct["fpct_str"], "fpct_team": l_fpct["team_name"],
                    "e_val": f"{l_e['e']} E", "e_team": l_e["team_name"],
                    "dp_val": f"{l_dp['dp']} DP", "dp_team": l_dp["team_name"],
                    "cs_pct_val": l_cs["cs_pct_str"], "cs_pct_team": l_cs["team_name"],
                }
        else:
            self.collective_fielding_data = []

    # ── Handlers de Fase y Pestañas ─────────────────────────────────────────────
    def set_active_tab(self, tab: str):
        self.active_tab = tab

    def set_phase_by_name(self, phase_name: str):
        self.selected_phase_name = phase_name
        self.selected_phase = self.phase_map.get(phase_name, "R")
        self.load_collective_stats()

    def set_batting_metric(self, metric: str):
        self.selected_batting_metric = metric

    def set_pitching_metric(self, metric: str):
        self.selected_pitching_metric = metric

    def set_fielding_metric(self, metric: str):
        self.selected_fielding_metric = metric

    # ── Gráficos Plotly (@rx.var) ──────────────────────────────────────────────
    @rx.var
    def batting_bar_chart(self) -> go.Figure:
        """Gráfico horizontal comparativo de métricas ofensivas por equipo."""
        fig = go.Figure()
        if not self.collective_batting_data:
            fig.update_layout(template="plotly_dark", height=380)
            return fig

        m_key = self.selected_batting_metric
        # Ordenar ascendente para que el más alto quede arriba en el eje Y
        sorted_data = sorted(self.collective_batting_data, key=lambda x: x.get(m_key, 0), reverse=False)

        names = [d["team_name"] for d in sorted_data]
        values = [d.get(m_key, 0) for d in sorted_data]
        colors = ["#FDB827" if d["is_leones"] else "#38BDF8" for d in sorted_data]

        text_labels = []
        for v in values:
            if isinstance(v, float):
                text_labels.append(f"{v:.3f}")
            else:
                text_labels.append(str(v))

        fig.add_trace(go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
            text=text_labels,
            textposition="auto",
        ))

        labels_map = {
            "ops": "OPS (On-base Plus Slugging)",
            "avg": "AVG (Promedio de Bateo)",
            "obp": "OBP (Porcentaje de Embasado)",
            "slg": "SLG (Slugging)",
            "hr": "Jonrones (HR)",
            "r": "Carreras Anotadas (CA)",
            "h": "Hits Conectados (H)",
            "bb": "Boletos Recibidos (BB)",
            "sb": "Bases Robadas (SB)",
            "lob": "Dejados en Base (LOB)",
        }
        title_label = labels_map.get(m_key, m_key.upper())

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text=f"Comparativa Colectiva: {title_label}", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title=title_label, gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            margin=dict(l=140, r=40, t=45, b=45),
            height=380,
        )
        return fig

    @rx.var
    def pitching_bar_chart(self) -> go.Figure:
        """Gráfico horizontal comparativo de pitcheo por equipo."""
        fig = go.Figure()
        if not self.collective_pitching_data:
            fig.update_layout(template="plotly_dark", height=380)
            return fig

        m_key = self.selected_pitching_metric
        # Para ERA, WHIP, BAA, BB, menor es mejor -> orden descendente para que el menor quede arriba
        lower_is_better = m_key in ["era", "whip", "baa", "bb", "bb9"]
        sorted_data = sorted(self.collective_pitching_data, key=lambda x: x.get(m_key, 0), reverse=lower_is_better)

        names = [d["team_name"] for d in sorted_data]
        values = [d.get(m_key, 0) for d in sorted_data]
        colors = ["#FDB827" if d["is_leones"] else "#CE1141" for d in sorted_data]

        text_labels = []
        for v in values:
            if isinstance(v, float):
                text_labels.append(f"{v:.2f}")
            else:
                text_labels.append(str(v))

        fig.add_trace(go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
            text=text_labels,
            textposition="auto",
        ))

        labels_map_p = {
            "era": "Efectividad (ERA)",
            "whip": "Tráfico (WHIP)",
            "so": "Ponches Totales (K)",
            "k9": "Ponches por 9 Entradas (K/9)",
            "bb": "Boletos Permitidos (BB)",
            "k_bb": "Relación K/BB",
            "sv": "Juegos Salvados (SV)",
            "baa": "Promedio Bateo Rival (BAA)",
        }
        title_label_p = labels_map_p.get(m_key, m_key.upper())

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text=f"Comparativa Colectiva: {title_label_p}", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title=title_label_p, gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            margin=dict(l=140, r=40, t=45, b=45),
            height=380,
        )
        return fig

    @rx.var
    def fielding_bar_chart(self) -> go.Figure:
        """Gráfico horizontal comparativo de fildeo por equipo."""
        fig = go.Figure()
        if not self.collective_fielding_data:
            fig.update_layout(template="plotly_dark", height=380)
            return fig

        m_key = self.selected_fielding_metric
        lower_is_better = (m_key == "e")
        sorted_data = sorted(self.collective_fielding_data, key=lambda x: x.get(m_key, 0), reverse=lower_is_better)

        names = [d["team_name"] for d in sorted_data]
        values = [d.get(m_key, 0) for d in sorted_data]
        colors = ["#FDB827" if d["is_leones"] else "#10B981" for d in sorted_data]

        text_labels = []
        for v in values:
            if isinstance(v, float):
                text_labels.append(f"{v:.3f}")
            else:
                text_labels.append(str(v))

        fig.add_trace(go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
            text=text_labels,
            textposition="auto",
        ))

        labels_map_f = {
            "fpct": "Porcentaje de Fildeo (FPCT)",
            "e": "Errores Cometidos (E)",
            "dp": "Doble Matanzas (DP)",
            "a": "Asistencias (A)",
            "po": "Outs Realizados (PO)",
            "tc": "Total de Lances (TC)",
            "cs_pct": "Porcentaje de Captura de Receptores (CS%)",
        }
        title_label_f = labels_map_f.get(m_key, m_key.upper())

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text=f"Comparativa Colectiva: {title_label_f}", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title=title_label_f, gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            margin=dict(l=140, r=40, t=45, b=45),
            height=380,
        )
        return fig
