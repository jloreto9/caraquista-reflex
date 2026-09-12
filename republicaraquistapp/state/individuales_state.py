# republicaraquistapp/state/individuales_state.py
"""
individuales_state.py
---------------------
Estado reactivo para la vista de Estadísticas Individuales (/individuales).
Cubre:
1. Bateo: Líderes y tabla completa con AVG, OBP, SLG, OPS, ISO, BABIP, wOBA, wRC+.
2. Pitcheo: Líderes y tabla completa con ERA, WHIP, FIP, K/9, BB/9, K/BB, IP, SV.
3. Fildeo / Defensa: Rendimiento defensivo con PO, A, E, TC, FPCT, DP, RF/9, CS, SB, CS%, PB.
4. Comparador Head-to-Head (H2H): Gráfico de radar polar (8 dimensiones sabermétricas,
   percentiles 0-100), tarjetas de perfil con headshots, tabla comparativa categoría por categoría
   y veredicto analítico automatizado.
"""

from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from core.supabase_client import (
    get_batting_stats,
    get_pitching_stats,
    get_individual_fielding_stats,
    get_current_season,
)
from core.teams import get_team_logo, get_team_abbr, get_team_name
from core.matchup_card import build_matchup_image
from republicaraquistapp.state.base_state import AppState



def _safe_int(val, default: int = 0) -> int:
    if val is None or pd.isna(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def _safe_float(val, default: float = 0.0) -> float:
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _safe_str(val, default: str = "-") -> str:
    if val is None:
        return default
    return str(val)


def _find_player(data: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    """Busca un jugador en la lista ya sea por formato 'Nombre (ABBR)' o por 'Nombre'."""
    if not query or not data:
        return None
    for p in data:
        formatted = f"{p.get('player_name', '')} ({p.get('team_abbr', '')})"
        if formatted == query:
            return p
    for p in data:
        if p.get("player_name") == query:
            return p
    for p in data:
        p_name = p.get("player_name", "")
        if p_name and (p_name in query or query.startswith(p_name)):
            return p
    return None


def _shorten_name(name: str) -> str:
    """Abrevia nombres largos a formato 'H. Castro' para badges y celdas compactas."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name


class IndividualesState(AppState):
    """Estado reactivo para estadísticas individuales y comparador sabermétrico."""

    # ── Pestaña y Fase Activa ───────────────────────────────────────────────────
    active_tab: str = "bateo"  # "bateo", "pitcheo", "fildeo", "comparador"
    selected_phase: str = "Temporada Regular"
    phase_options: List[str] = [
        "Temporada Regular",
        "Round Robin",
        "Serie Final",
        "Todas las Fases",
    ]

    # ── Filtros de Equipo ───────────────────────────────────────────────────────
    selected_batting_team: str = "Toda la LVBP (Overall)"
    selected_pitching_team: str = "Toda la LVBP (Overall)"
    selected_fielding_team: str = "Toda la LVBP (Overall)"

    team_options: List[str] = [
        "Toda la LVBP (Overall)",
        "Leones del Caracas",
        "Navegantes del Magallanes",
        "Tiburones de La Guaira",
        "Tigres de Aragua",
        "Cardenales de Lara",
        "Águilas del Zulia",
        "Caribes de Anzoátegui",
        "Bravos de Margarita",
    ]

    # ── Filtros de Bateo ────────────────────────────────────────────────────────
    search_batting: str = ""
    min_ab: int = 10
    selected_batting_pos: str = "Todas"
    sort_batting_by: str = "ops"

    # ── Filtros de Pitcheo ──────────────────────────────────────────────────────
    search_pitching: str = ""
    pitcher_role: str = "Todos"  # "Todos", "Abridores", "Relevistas"
    min_ip: float = 3.0
    sort_pitching_by: str = "era"

    # ── Filtros de Fildeo ───────────────────────────────────────────────────────
    search_fielding: str = ""
    selected_fielding_pos: str = "Todas"

    # ── Filtros del Comparador H2H ──────────────────────────────────────────────
    compare_type: str = "Bateadores"  # "Bateadores" o "Lanzadores"
    comparator_team_1: str = "Toda la LVBP (Overall)"
    comparator_team_2: str = "Toda la LVBP (Overall)"
    selected_player_1: str = ""
    selected_player_2: str = ""

    # ── Datos Procesados en Memoria ─────────────────────────────────────────────
    batting_data_raw: List[Dict[str, Any]] = []
    pitching_data_raw: List[Dict[str, Any]] = []
    fielding_data_raw: List[Dict[str, Any]] = []

    # ── Tarjetas de Líderes KPI ────────────────────────────────────────────────
    batting_kpis: Dict[str, Any] = {
        "avg_val": ".000", "avg_player": "-",
        "hr_val": "0", "hr_player": "-",
        "rbi_val": "0", "rbi_player": "-",
        "ops_val": ".000", "ops_player": "-",
        "woba_val": ".000", "woba_player": "-",
        "wrc_val": "100", "wrc_player": "-",
    }
    pitching_kpis: Dict[str, Any] = {
        "era_val": "0.00", "era_player": "-",
        "so_val": "0", "so_player": "-",
        "whip_val": "0.00", "whip_player": "-",
        "fip_val": "0.00", "fip_player": "-",
        "k9_val": "0.00", "k9_player": "-",
        "sv_val": "0", "sv_player": "-",
    }
    fielding_kpis: Dict[str, Any] = {
        "fpct_val": "1.000", "fpct_player": "-",
        "a_val": "0", "a_player": "-",
        "dp_val": "0", "dp_player": "-",
        "po_val": "0", "po_player": "-",
        "cs_val": "0", "cs_player": "-",
    }

    # ── Listas de Jugadores para Selects ────────────────────────────────────────
    available_batters: List[str] = []
    available_pitchers: List[str] = []

    # ── Datos de la Comparación H2H ────────────────────────────────────────────
    h2h_rows: List[Dict[str, Any]] = []
    player_1_card: Dict[str, Any] = {
        "name": "-", "pos": "-", "team": "Leones del Caracas", "team_logo": "/logo.png", "headshot": "", "badge": "CAR",
        "kpi_1": "-", "kpi_2": "-", "kpi_3": "-"
    }
    player_2_card: Dict[str, Any] = {
        "name": "-", "pos": "-", "team": "Leones del Caracas", "team_logo": "/logo.png", "headshot": "", "badge": "CAR",
        "kpi_1": "-", "kpi_2": "-", "kpi_3": "-"
    }
    h2h_verdict: str = "Seleccione dos jugadores para generar el veredicto sabermétrico."
    is_generating_card: bool = False

    # ── Handler Principal on_load ───────────────────────────────────────────────
    def on_load(self):
        """Carga inicial de todos los datos individuales."""
        self.is_loading = True
        self.has_error = False
        try:
            self.load_all_stats()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error al Cargar Estadísticas Individuales"
            self.error_message = str(e)
        finally:
            self.is_loading = False

    def _phase_code(self) -> str:
        """Mapea el nombre de la fase en español al código de la BD/API."""
        mapping = {
            "Temporada Regular": "R",
            "Round Robin": "L",
            "Serie Final": "F",
            "Todas las Fases": "all",
        }
        return mapping.get(self.selected_phase, "R")

    def set_selected_phase(self, phase: str):
        """Cambia la fase seleccionada y recarga las estadísticas individuales."""
        self.selected_phase = phase
        self.load_all_stats()
        if self.selected_player_1 and self.selected_player_2:
            self.update_h2h_comparison()

    def load_season_data(self):
        """Sobrescribe la recarga por temporada para refrescar estadísticas individuales."""
        super().load_season_data()
        self.load_all_stats()

    # ── Carga y Cálculo de Estadísticas ─────────────────────────────────────────
    def load_all_stats(self):
        """Descarga datos de Supabase y calcula métricas sabermétricas avanzadas para toda la LVBP."""
        season = self.selected_season
        phase = self._phase_code()

        # ── 1. BATEO (Toda la LVBP) ─────────────────────────────────────────────
        df_bat = get_batting_stats(team_id=None, limit=600, season=season, phase=phase)
        if df_bat is not None and not df_bat.empty:
            bat_list = []
            for _, row in df_bat.iterrows():
                p_id = _safe_int(row.get("player_id", 0))
                name = _safe_str(row.get("player_name", "Desconocido"))
                t_id = _safe_int(row.get("team_id", 695))
                t_abbr = _safe_str(row.get("team_abbr", get_team_abbr(t_id)))
                t_name = _safe_str(row.get("team_name", get_team_name(t_id)))
                t_logo = get_team_logo(t_id, size=72)
                ab = _safe_int(row.get("ab", 0))
                r = _safe_int(row.get("r", 0))
                h = _safe_int(row.get("h", 0))
                d2 = _safe_int(row.get("doubles", 0))
                d3 = _safe_int(row.get("triples", 0))
                hr = _safe_int(row.get("hr", 0))
                rbi = _safe_int(row.get("rbi", 0))
                bb = _safe_int(row.get("bb", 0))
                so = _safe_int(row.get("so", 0))
                sb = _safe_int(row.get("sb", 0))
                cs = _safe_int(row.get("cs", 0))
                hbp = _safe_int(row.get("hbp", 0))
                sf = _safe_int(row.get("sf", 0))
                sh = _safe_int(row.get("sh", 0))

                pa = ab + bb + hbp + sf + sh
                d1 = max(0, h - d2 - d3 - hr)

                avg = (h / ab) if ab > 0 else 0.0
                obp_den = ab + bb + hbp + sf
                obp = ((h + bb + hbp) / obp_den) if obp_den > 0 else 0.0
                slg = ((d1 + 2 * d2 + 3 * d3 + 4 * hr) / ab) if ab > 0 else 0.0
                ops = obp + slg
                iso = (slg - avg) if ab > 0 else 0.0

                babip_den = ab - so - hr + sf
                babip = ((h - hr) / babip_den) if babip_den > 0 else 0.0

                woba_num = 0.690 * bb + 0.722 * hbp + 0.888 * d1 + 1.271 * d2 + 1.616 * d3 + 2.101 * hr
                woba_den = ab + bb - 0 + sf + hbp
                woba = (woba_num / woba_den) if woba_den > 0 else 0.0

                # wRC+ escalado respecto a promedio de liga (.320 wOBA)
                wrc_plus = int(round((woba / 0.320) * 100)) if pa >= 5 else 100

                bb_pct = round((bb / pa * 100), 1) if pa > 0 else 0.0
                k_pct = round((so / pa * 100), 1) if pa > 0 else 0.0

                headshot_url = f"https://midfield.mlbstatic.com/v1/people/{p_id}/spots/120" if p_id > 0 else ""

                bat_list.append({
                    "player_id": p_id,
                    "player_name": name,
                    "team_id": t_id,
                    "team_name": t_name,
                    "team_abbr": t_abbr,
                    "team_logo": t_logo,
                    "headshot": headshot_url,
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
                    "hbp": hbp,
                    "sf": sf,
                    "avg": avg,
                    "avg_str": f"{avg:.3f}".replace("0.", "."),
                    "obp": obp,
                    "obp_str": f"{obp:.3f}".replace("0.", "."),
                    "slg": slg,
                    "slg_str": f"{slg:.3f}".replace("0.", "."),
                    "ops": ops,
                    "ops_str": f"{ops:.3f}",
                    "iso": iso,
                    "iso_str": f"{iso:.3f}".replace("0.", "."),
                    "babip": babip,
                    "babip_str": f"{babip:.3f}".replace("0.", "."),
                    "woba": woba,
                    "woba_str": f"{woba:.3f}".replace("0.", "."),
                    "wrc_plus": wrc_plus,
                    "wrc_color": "green" if wrc_plus >= 100 else "gray",
                    "bb_pct": bb_pct,
                    "bb_pct_str": f"{bb_pct:.1f}%",
                    "k_pct": k_pct,
                    "k_pct_str": f"{k_pct:.1f}%",
                })

            self.batting_data_raw = bat_list
            self.available_batters = [
                f"{p['player_name']} ({p['team_abbr']})"
                for p in sorted(bat_list, key=lambda x: (x["pa"], x["ops"]), reverse=True)
            ]
            self.update_batting_kpis()
        else:
            self.batting_data_raw = []
            self.available_batters = []

        # ── 2. PITCHEO (Toda la LVBP) ───────────────────────────────────────────
        df_pit = get_pitching_stats(team_id=None, limit=600, season=season, phase=phase)
        if df_pit is not None and not df_pit.empty:
            pit_list = []
            for _, row in df_pit.iterrows():
                p_id = _safe_int(row.get("player_id", 0))
                name = _safe_str(row.get("player_name", "Desconocido"))
                t_id = _safe_int(row.get("team_id", 695))
                t_abbr = _safe_str(row.get("team_abbr", get_team_abbr(t_id)))
                t_name = _safe_str(row.get("team_name", get_team_name(t_id)))
                t_logo = get_team_logo(t_id, size=72)
                ip = _safe_float(row.get("ip", 0.0))
                h = _safe_int(row.get("h", 0))
                r = _safe_int(row.get("r", 0))
                er = _safe_int(row.get("er", 0))
                bb = _safe_int(row.get("bb", 0))
                so = _safe_int(row.get("so", 0))
                hr = _safe_int(row.get("hr", 0))
                g = _safe_int(row.get("g", 1))
                gs = _safe_int(row.get("gs", 0))
                w = _safe_int(row.get("w", 0))
                l = _safe_int(row.get("l", 0))
                sv = _safe_int(row.get("sv", 0))
                hbp = _safe_int(row.get("hbp", 0))

                era = ((er * 9.0) / ip) if ip > 0 else 0.0
                whip = ((h + bb) / ip) if ip > 0 else 0.0
                k9 = ((so * 9.0) / ip) if ip > 0 else 0.0
                bb9 = ((bb * 9.0) / ip) if ip > 0 else 0.0
                k_bb = (so / bb) if bb > 0 else float(so)
                fip_comp = ((13.0 * hr + 3.0 * (bb + hbp) - 2.0 * so) / ip) + 3.20 if ip > 0 else 0.0
                fip = max(0.0, fip_comp)

                role = "Abridor" if (gs > 0 and gs >= (g / 2)) else "Relevista"
                headshot_url = f"https://midfield.mlbstatic.com/v1/people/{p_id}/spots/120" if p_id > 0 else ""

                pit_list.append({
                    "player_id": p_id,
                    "player_name": name,
                    "team_id": t_id,
                    "team_name": t_name,
                    "team_abbr": t_abbr,
                    "team_logo": t_logo,
                    "headshot": headshot_url,
                    "role": role,
                    "role_color": "blue" if role == "Abridor" else "purple",
                    "g": g,
                    "gs": gs,
                    "w": w,
                    "l": l,
                    "sv": sv,
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
                    "fip": fip,
                    "fip_str": f"{fip:.2f}",
                })

            self.pitching_data_raw = pit_list
            self.available_pitchers = [
                f"{p['player_name']} ({p['team_abbr']})"
                for p in sorted(pit_list, key=lambda x: (x["ip"], x["so"]), reverse=True)
            ]
            self.update_pitching_kpis()
        else:
            self.pitching_data_raw = []
            self.available_pitchers = []

        # ── 3. FILDEO / DEFENSA (Toda la LVBP) ──────────────────────────────────
        df_fld = get_individual_fielding_stats(season=season, team_id=None, phase=phase)
        if df_fld is not None and not df_fld.empty:
            fld_list = []
            for _, row in df_fld.iterrows():
                p_id = _safe_int(row.get("player_id", 0))
                name = _safe_str(row.get("player_name", "Desconocido"))
                t_id = _safe_int(row.get("team_id", 695))
                t_abbr = _safe_str(row.get("team_abbr", get_team_abbr(t_id)))
                t_name = _safe_str(row.get("team_name", get_team_name(t_id)))
                t_logo = get_team_logo(t_id, size=72)
                pos = _safe_str(row.get("position", "UT"))
                g = _safe_int(row.get("games", 0))
                gs = _safe_int(row.get("games_started", 0))
                inn = _safe_str(row.get("innings", "0.0"))
                po = _safe_int(row.get("po", row.get("putouts", 0)))
                a = _safe_int(row.get("a", row.get("assists", 0)))
                e = _safe_int(row.get("e", row.get("errors", 0)))
                tc = _safe_int(row.get("tc", row.get("chances", 0)))
                fpct = _safe_float(row.get("fpct", row.get("fielding_pct", 1.0)), 1.0)
                dp = _safe_int(row.get("dp", row.get("double_plays", 0)))
                rf9 = _safe_float(row.get("rf9", row.get("range_factor_per_9", 0.0)))
                cs = _safe_int(row.get("cs", row.get("caught_stealing", 0)))
                sb = _safe_int(row.get("sb", row.get("stolen_bases", 0)))
                cs_pct = _safe_float(row.get("cs_pct", row.get("caught_stealing_pct", 0.0)))
                pb = _safe_int(row.get("pb", row.get("passed_balls", 0)))

                headshot_url = f"https://midfield.mlbstatic.com/v1/people/{p_id}/spots/120" if p_id > 0 else ""

                fld_list.append({
                    "player_id": p_id,
                    "player_name": name,
                    "team_id": t_id,
                    "team_name": t_name,
                    "team_abbr": t_abbr,
                    "team_logo": t_logo,
                    "headshot": headshot_url,
                    "position": pos,
                    "games": g,
                    "games_started": gs,
                    "innings": inn,
                    "po": po,
                    "a": a,
                    "e": e,
                    "tc": tc,
                    "fpct": fpct,
                    "fpct_str": f"{fpct:.3f}".replace("0.", "."),
                    "dp": dp,
                    "rf9": rf9,
                    "rf9_str": f"{rf9:.2f}",
                    "cs": cs,
                    "sb": sb,
                    "cs_pct": cs_pct,
                    "cs_pct_str": f"{cs_pct:.3f}".replace("0.", "."),
                    "pb": pb,
                })

            self.fielding_data_raw = fld_list
            self.update_fielding_kpis()
        else:
            self.fielding_data_raw = []

        # Inicializar selección por defecto en Comparador H2H
        if self.compare_type == "Bateadores" and self.available_batters:
            car_batters = [b for b in self.available_batters if "(CAR)" in b]
            rival_batters = [b for b in self.available_batters if "(CAR)" not in b]
            if not self.selected_player_1 or self.selected_player_1 not in self.available_batters:
                self.selected_player_1 = car_batters[0] if car_batters else self.available_batters[0]
            if not self.selected_player_2 or self.selected_player_2 not in self.available_batters:
                if rival_batters:
                    self.selected_player_2 = rival_batters[0]
                elif len(self.available_batters) > 1:
                    self.selected_player_2 = self.available_batters[1]
                else:
                    self.selected_player_2 = self.available_batters[0]
        elif self.compare_type != "Bateadores" and self.available_pitchers:
            car_pitchers = [p for p in self.available_pitchers if "(CAR)" in p]
            rival_pitchers = [p for p in self.available_pitchers if "(CAR)" not in p]
            if not self.selected_player_1 or self.selected_player_1 not in self.available_pitchers:
                self.selected_player_1 = car_pitchers[0] if car_pitchers else self.available_pitchers[0]
            if not self.selected_player_2 or self.selected_player_2 not in self.available_pitchers:
                if rival_pitchers:
                    self.selected_player_2 = rival_pitchers[0]
                elif len(self.available_pitchers) > 1:
                    self.selected_player_2 = self.available_pitchers[1]
                else:
                    self.selected_player_2 = self.available_pitchers[0]

        self.update_h2h_comparison()

    # ── Actualización Dinámica de KPIs por Equipo ──────────────────────────────
    def update_batting_kpis(self):
        """Calcula tarjetas de líderes de bateo respondiendo al equipo seleccionado."""
        pool = self.batting_data_raw
        if self.selected_batting_team != "Toda la LVBP (Overall)":
            pool = [b for b in pool if b.get("team_name") == self.selected_batting_team]
        qual_bat = [b for b in pool if b["ab"] >= 10] or pool
        if qual_bat:
            best_avg = max(qual_bat, key=lambda x: x["avg"])
            best_hr = max(qual_bat, key=lambda x: x["hr"])
            best_rbi = max(qual_bat, key=lambda x: x["rbi"])
            best_ops = max(qual_bat, key=lambda x: x["ops"])
            best_woba = max(qual_bat, key=lambda x: x["woba"])
            best_wrc = max(qual_bat, key=lambda x: x["wrc_plus"])

            show_team = f" ({best_avg.get('team_abbr', '')})" if self.selected_batting_team == "Toda la LVBP (Overall)" else ""
            self.batting_kpis = {
                "avg_val": best_avg["avg_str"], "avg_player": f"{best_avg['player_name']}{show_team}",
                "hr_val": str(best_hr["hr"]), "hr_player": f"{best_hr['player_name']}{show_team}",
                "rbi_val": str(best_rbi["rbi"]), "rbi_player": f"{best_rbi['player_name']}{show_team}",
                "ops_val": best_ops["ops_str"], "ops_player": f"{best_ops['player_name']}{show_team}",
                "woba_val": best_woba["woba_str"], "woba_player": f"{best_woba['player_name']}{show_team}",
                "wrc_val": f"{best_wrc['wrc_plus']} wRC+", "wrc_player": f"{best_wrc['player_name']}{show_team}",
            }
        else:
            self.batting_kpis = {
                "avg_val": ".000", "avg_player": "-",
                "hr_val": "0", "hr_player": "-",
                "rbi_val": "0", "rbi_player": "-",
                "ops_val": ".000", "ops_player": "-",
                "woba_val": ".000", "woba_player": "-",
                "wrc_val": "100", "wrc_player": "-",
            }

    def update_pitching_kpis(self):
        """Calcula tarjetas de líderes de pitcheo respondiendo al equipo seleccionado."""
        pool = self.pitching_data_raw
        if self.selected_pitching_team != "Toda la LVBP (Overall)":
            pool = [p for p in pool if p.get("team_name") == self.selected_pitching_team]
        qual_pit = [p for p in pool if p["ip"] >= 3.0] or pool
        if qual_pit:
            best_era = min(qual_pit, key=lambda x: x["era"])
            best_so = max(qual_pit, key=lambda x: x["so"])
            best_whip = min(qual_pit, key=lambda x: x["whip"])
            best_fip = min(qual_pit, key=lambda x: x["fip"])
            best_k9 = max(qual_pit, key=lambda x: x["k9"])
            best_sv = max(qual_pit, key=lambda x: x["sv"])

            show_team = f" ({best_era.get('team_abbr', '')})" if self.selected_pitching_team == "Toda la LVBP (Overall)" else ""
            self.pitching_kpis = {
                "era_val": best_era["era_str"], "era_player": f"{best_era['player_name']}{show_team}",
                "so_val": str(best_so["so"]), "so_player": f"{best_so['player_name']}{show_team}",
                "whip_val": best_whip["whip_str"], "whip_player": f"{best_whip['player_name']}{show_team}",
                "fip_val": best_fip["fip_str"], "fip_player": f"{best_fip['player_name']}{show_team}",
                "k9_val": best_k9["k9_str"], "k9_player": f"{best_k9['player_name']}{show_team}",
                "sv_val": str(best_sv["sv"]), "sv_player": f"{best_sv['player_name']}{show_team}",
            }
        else:
            self.pitching_kpis = {
                "era_val": "0.00", "era_player": "-",
                "so_val": "0", "so_player": "-",
                "whip_val": "0.00", "whip_player": "-",
                "fip_val": "0.00", "fip_player": "-",
                "k9_val": "0.00", "k9_player": "-",
                "sv_val": "0", "sv_player": "-",
            }

    def update_fielding_kpis(self):
        """Calcula tarjetas de líderes defensivos respondiendo al equipo seleccionado."""
        pool = self.fielding_data_raw
        if self.selected_fielding_team != "Toda la LVBP (Overall)":
            pool = [f for f in pool if f.get("team_name") == self.selected_fielding_team]
        qual_fld = [f for f in pool if f["tc"] >= 10] or pool
        if qual_fld:
            best_fpct = max(qual_fld, key=lambda x: x["fpct"])
            best_a = max(qual_fld, key=lambda x: x["a"])
            best_dp = max(qual_fld, key=lambda x: x["dp"])
            best_po = max(qual_fld, key=lambda x: x["po"])
            best_cs = max(qual_fld, key=lambda x: x["cs"])

            show_team = f" ({best_fpct.get('team_abbr', '')})" if self.selected_fielding_team == "Toda la LVBP (Overall)" else ""
            self.fielding_kpis = {
                "fpct_val": best_fpct["fpct_str"], "fpct_player": f"{best_fpct['player_name']}{show_team} ({best_fpct['position']})",
                "a_val": str(best_a["a"]), "a_player": f"{best_a['player_name']}{show_team} ({best_a['position']})",
                "dp_val": str(best_dp["dp"]), "dp_player": f"{best_dp['player_name']}{show_team} ({best_dp['position']})",
                "po_val": str(best_po["po"]), "po_player": f"{best_po['player_name']}{show_team} ({best_po['position']})",
                "cs_val": str(best_cs["cs"]), "cs_player": f"{best_cs['player_name']}{show_team} (C)",
            }
        else:
            self.fielding_kpis = {
                "fpct_val": "1.000", "fpct_player": "-",
                "a_val": "0", "a_player": "-",
                "dp_val": "0", "dp_player": "-",
                "po_val": "0", "po_player": "-",
                "cs_val": "0", "cs_player": "-",
            }

    # ── Handlers de Filtrado y Navegación ───────────────────────────────────────
    def set_active_tab(self, tab: str):
        """Cambia la pestaña activa."""
        self.active_tab = tab

    def set_selected_batting_team(self, val: str):
        self.selected_batting_team = val
        self.update_batting_kpis()

    def set_selected_pitching_team(self, val: str):
        self.selected_pitching_team = val
        self.update_pitching_kpis()

    def set_selected_fielding_team(self, val: str):
        self.selected_fielding_team = val
        self.update_fielding_kpis()

    def set_search_batting(self, val: str):
        self.search_batting = val

    def set_min_ab(self, val: Any):
        try:
            self.min_ab = int(val)
        except (ValueError, TypeError):
            self.min_ab = 10

    def set_selected_batting_pos(self, val: str):
        self.selected_batting_pos = val

    def set_sort_batting_by(self, val: str):
        self.sort_batting_by = val

    def set_search_pitching(self, val: str):
        self.search_pitching = val

    def set_pitcher_role(self, val: str):
        self.pitcher_role = val

    def set_min_ip(self, val: Any):
        try:
            self.min_ip = float(val)
        except (ValueError, TypeError):
            self.min_ip = 3.0

    def set_sort_pitching_by(self, val: str):
        self.sort_pitching_by = val

    def set_search_fielding(self, val: str):
        self.search_fielding = val

    def set_selected_fielding_pos(self, val: str):
        self.selected_fielding_pos = val

    def _get_team_player_names(self, team: str, is_batter: bool) -> List[str]:
        if is_batter:
            data = self.batting_data_raw
            if team != "Toda la LVBP (Overall)":
                data = [p for p in data if p.get("team_name") == team]
            return [
                f"{p['player_name']} ({p.get('team_abbr', 'LVBP')})"
                for p in sorted(data, key=lambda x: (x.get("pa", 0), x.get("ops", 0.0)), reverse=True)
            ]
        else:
            data = self.pitching_data_raw
            if team != "Toda la LVBP (Overall)":
                data = [p for p in data if p.get("team_name") == team]
            return [
                f"{p['player_name']} ({p.get('team_abbr', 'LVBP')})"
                for p in sorted(data, key=lambda x: (x.get("ip", 0.0), x.get("so", 0)), reverse=True)
            ]

    def set_comparator_team_1(self, val: str):
        self.comparator_team_1 = val
        is_batter = (self.compare_type == "Bateadores")
        avail = self._get_team_player_names(val, is_batter)
        if avail and (not self.selected_player_1 or self.selected_player_1 not in avail):
            self.selected_player_1 = avail[0]
        self.update_h2h_comparison()

    def set_comparator_team_2(self, val: str):
        self.comparator_team_2 = val
        is_batter = (self.compare_type == "Bateadores")
        avail = self._get_team_player_names(val, is_batter)
        if avail and (not self.selected_player_2 or self.selected_player_2 not in avail):
            self.selected_player_2 = avail[0]
        self.update_h2h_comparison()

    def set_compare_type(self, val: str):
        self.compare_type = val
        is_bat = (val == "Bateadores")
        avail1 = self._get_team_player_names(self.comparator_team_1, is_bat)
        avail2 = self._get_team_player_names(self.comparator_team_2, is_bat)
        if avail1:
            self.selected_player_1 = avail1[0]
        if avail2:
            self.selected_player_2 = avail2[1] if (len(avail2) > 1 and avail1 == avail2) else avail2[0]
        self.update_h2h_comparison()

    def set_selected_player_1(self, val: str):
        self.selected_player_1 = val
        self.update_h2h_comparison()

    def set_selected_player_2(self, val: str):
        self.selected_player_2 = val
        self.update_h2h_comparison()

    def download_matchup_card(self):
        """Genera y descarga la tarjeta gráfica Matchup 360 en formato PNG."""
        self.is_generating_card = True
        try:
            is_batter = (self.compare_type == "Bateadores")
            season = self.selected_season
            png_bytes = build_matchup_image(
                player_1=self.player_1_card,
                player_2=self.player_2_card,
                h2h_rows=self.h2h_rows,
                is_batter=is_batter,
                season=season,
                phase=self.selected_phase,
            )
            safe1 = "".join(c for c in str(self.selected_player_1) if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_") or "Jugador1"
            safe2 = "".join(c for c in str(self.selected_player_2) if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_") or "Jugador2"
            safe_phase = "".join(c for c in str(self.selected_phase) if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
            filename = f"LVBP360_Matchup_{safe1}_vs_{safe2}_{season}_{safe_phase}.png"
            return rx.download(data=png_bytes, filename=filename, mime_type="image/png")
        finally:
            self.is_generating_card = False


    @rx.var
    def available_batters_p1(self) -> List[str]:
        return self._get_team_player_names(self.comparator_team_1, is_batter=True)

    @rx.var
    def available_batters_p2(self) -> List[str]:
        return self._get_team_player_names(self.comparator_team_2, is_batter=True)

    @rx.var
    def available_pitchers_p1(self) -> List[str]:
        return self._get_team_player_names(self.comparator_team_1, is_batter=False)

    @rx.var
    def available_pitchers_p2(self) -> List[str]:
        return self._get_team_player_names(self.comparator_team_2, is_batter=False)

    # ── Computed Properties: Listas Filtradas ───────────────────────────────────
    @rx.var
    def filtered_batting(self) -> List[Dict[str, Any]]:
        """Lista filtrada y ordenada de bateadores."""
        data = self.batting_data_raw
        if self.selected_batting_team != "Toda la LVBP (Overall)":
            data = [p for p in data if p.get("team_name") == self.selected_batting_team]
        data = [p for p in data if p["ab"] >= self.min_ab]
        if self.search_batting:
            s = self.search_batting.lower().strip()
            data = [p for p in data if s in p["player_name"].lower()]
        
        # Ordenamiento
        key_map = {
            "ops": ("ops", True),
            "avg": ("avg", True),
            "hr": ("hr", True),
            "rbi": ("rbi", True),
            "h": ("h", True),
            "woba": ("woba", True),
            "wrc_plus": ("wrc_plus", True),
            "sb": ("sb", True),
        }
        sort_key, reverse_order = key_map.get(self.sort_batting_by, ("ops", True))
        return sorted(data, key=lambda x: x.get(sort_key, 0), reverse=reverse_order)

    @rx.var
    def filtered_pitching(self) -> List[Dict[str, Any]]:
        """Lista filtrada y ordenada de lanzadores."""
        data = self.pitching_data_raw
        if self.selected_pitching_team != "Toda la LVBP (Overall)":
            data = [p for p in data if p.get("team_name") == self.selected_pitching_team]
        data = [p for p in data if p["ip"] >= self.min_ip]
        if self.pitcher_role != "Todos":
            data = [p for p in data if p["role"] == self.pitcher_role]
        if self.search_pitching:
            s = self.search_pitching.lower().strip()
            data = [p for p in data if s in p["player_name"].lower()]

        # Ordenamiento
        key_map = {
            "era": ("era", False),
            "whip": ("whip", False),
            "fip": ("fip", False),
            "so": ("so", True),
            "ip": ("ip", True),
            "k9": ("k9", True),
            "sv": ("sv", True),
        }
        sort_key, reverse_order = key_map.get(self.sort_pitching_by, ("era", False))
        return sorted(data, key=lambda x: x.get(sort_key, 0), reverse=reverse_order)

    @rx.var
    def filtered_fielding(self) -> List[Dict[str, Any]]:
        """Lista filtrada de defensores."""
        data = self.fielding_data_raw
        if self.selected_fielding_team != "Toda la LVBP (Overall)":
            data = [p for p in data if p.get("team_name") == self.selected_fielding_team]
        if self.selected_fielding_pos != "Todas":
            data = [p for p in data if p["position"] == self.selected_fielding_pos]
        if self.search_fielding:
            s = self.search_fielding.lower().strip()
            data = [p for p in data if s in p["player_name"].lower()]
        return sorted(data, key=lambda x: x["tc"], reverse=True)

    @rx.var
    def is_catcher_view(self) -> bool:
        return self.selected_fielding_pos == "C"

    def _find_player(self, query: str, data: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Busca un jugador en data o en batting_data_raw/pitching_data_raw."""
        target_data = data if data is not None else (self.batting_data_raw if self.compare_type == "Bateadores" else self.pitching_data_raw)
        return _find_player(target_data, query)

    def _get_player_defense(self, player_id: int, player_name: str) -> Dict[str, Any]:
        """Obtiene el perfil defensivo principal de un jugador a partir de fielding_data_raw."""
        matches = [
            f for f in self.fielding_data_raw
            if (player_id and f.get("player_id") == player_id) or (f.get("player_name") == player_name)
        ]
        if not matches:
            return {
                "has_defense": False,
                "pos": "BD",
                "games": 0,
                "inn": "0.0",
                "inn_float": 0.0,
                "tc": 0,
                "po": 0,
                "a": 0,
                "e": 0,
                "fpct": 1.0,
                "fpct_str": "1.000",
                "dp": 0,
                "rf9": 0.0,
                "rf9_str": "0.00",
                "cs": 0,
                "sb": 0,
                "cs_pct": 0.0,
                "cs_pct_str": ".000",
                "pb": 0,
            }
        best = sorted(matches, key=lambda x: (x.get("tc", 0), x.get("games", 0)), reverse=True)[0]
        inn_str = str(best.get("innings", "0.0"))
        try:
            inn_flt = float(inn_str)
        except (ValueError, TypeError):
            inn_flt = 0.0

        return {
            "has_defense": True,
            "pos": best.get("position", "UT"),
            "games": best.get("games", 0),
            "inn": inn_str,
            "inn_float": inn_flt,
            "tc": best.get("tc", 0),
            "po": best.get("po", 0),
            "a": best.get("a", 0),
            "e": best.get("e", 0),
            "fpct": best.get("fpct", 1.0),
            "fpct_str": best.get("fpct_str", f"{best.get('fpct', 1.0):.3f}".replace("0.", ".")),
            "dp": best.get("dp", 0),
            "rf9": best.get("rf9", 0.0),
            "rf9_str": best.get("rf9_str", f"{best.get('rf9', 0.0):.2f}"),
            "cs": best.get("cs", 0),
            "sb": best.get("sb", 0),
            "cs_pct": best.get("cs_pct", 0.0),
            "cs_pct_str": best.get("cs_pct_str", f"{best.get('cs_pct', 0.0):.3f}".replace("0.", ".")),
            "pb": best.get("pb", 0),
        }

    def generate_h2h_comparison(self):
        """Genera la comparativa sabermétrica entre los dos jugadores seleccionados."""
        return self.update_h2h_comparison()

    # ── Actualización de Comparación H2H (Matchup 360) ─────────────────────────
    def update_h2h_comparison(self):
        """Calcula percentiles sabermétricos relativos, tarjetas de perfil, tabla categorizada y veredicto."""
        if not self.selected_player_1 or not self.selected_player_2:
            self.h2h_verdict = "Seleccione dos jugadores para generar la comparativa sabermétrica."
            self.h2h_rows = []
            return

        if self.compare_type == "Bateadores":
            p1 = _find_player(self.batting_data_raw, self.selected_player_1)
            p2 = _find_player(self.batting_data_raw, self.selected_player_2)
            if not p1 or not p2:
                self.h2h_verdict = "Seleccione dos jugadores para generar la comparativa sabermétrica."
                self.h2h_rows = []
                return

            t1_id = p1.get("team_id", 695)
            t2_id = p2.get("team_id", 695)
            self.player_1_card = {
                "name": p1["player_name"],
                "pos": "Bateador",
                "team": f"{p1.get('team_name', 'Leones del Caracas')} ({p1.get('team_abbr', 'CAR')})",
                "team_logo": p1.get("team_logo") or get_team_logo(t1_id, size=72),
                "headshot": p1.get("headshot", ""),
                "badge": p1.get("team_abbr", "CAR"),
                "kpi_1": f"AVG {p1['avg_str']}",
                "kpi_2": f"OPS {p1['ops_str']}",
                "kpi_3": f"{p1['hr']} HR",
            }
            self.player_2_card = {
                "name": p2["player_name"],
                "pos": "Bateador",
                "team": f"{p2.get('team_name', 'Equipo Rival')} ({p2.get('team_abbr', 'LVBP')})",
                "team_logo": p2.get("team_logo") or get_team_logo(t2_id, size=72),
                "headshot": p2.get("headshot", ""),
                "badge": p2.get("team_abbr", "LVBP"),
                "kpi_1": f"AVG {p2['avg_str']}",
                "kpi_2": f"OPS {p2['ops_str']}",
                "kpi_3": f"{p2['hr']} HR",
            }

            d1 = p1.get("doubles", p1.get("h_2b", 0))
            t1 = p1.get("triples", p1.get("h_3b", 0))
            h1 = p1.get("h", 0)
            hr1 = p1.get("hr", 0)
            d1_1 = max(0, h1 - d1 - t1 - hr1)

            d2 = p2.get("doubles", p2.get("h_2b", 0))
            t2 = p2.get("triples", p2.get("h_3b", 0))
            h2 = p2.get("h", 0)
            hr2 = p2.get("hr", 0)
            d1_2 = max(0, h2 - d2 - t2 - hr2)

            tb1 = d1_1 + 2 * d1 + 3 * t1 + 4 * hr1
            tb2 = d1_2 + 2 * d2 + 3 * t2 + 4 * hr2
            xbh1 = d1 + t1 + hr1
            xbh2 = d2 + t2 + hr2

            # Baserunning
            sb1, cs1 = p1.get("sb", 0), p1.get("cs", 0)
            sb2, cs2 = p2.get("sb", 0), p2.get("cs", 0)
            att1 = sb1 + cs1
            att2 = sb2 + cs2
            sb_pct1 = (sb1 / att1 * 100.0) if att1 > 0 else 0.0
            sb_pct2 = (sb2 / att2 * 100.0) if att2 > 0 else 0.0
            sb_pct1_str = f"{sb_pct1:.1f}%" if att1 > 0 else "0.0%"
            sb_pct2_str = f"{sb_pct2:.1f}%" if att2 > 0 else "0.0%"

            # Defense
            def1 = self._get_player_defense(p1.get("player_id", 0), p1.get("player_name", ""))
            def2 = self._get_player_defense(p2.get("player_id", 0), p2.get("player_name", ""))

            cats = [
                # ⚡ Ofensiva & Sabermetría
                ("⚡ Ofensiva & Sabermetría", "wOBA", p1.get("woba_str", ".000"), p2.get("woba_str", ".000"), p1.get("woba", 0.0) > p2.get("woba", 0.0), p2.get("woba", 0.0) > p1.get("woba", 0.0)),
                ("⚡ Ofensiva & Sabermetría", "wRC+", f"{p1.get('wrc_plus', 100)}", f"{p2.get('wrc_plus', 100)}", p1.get("wrc_plus", 100) > p2.get("wrc_plus", 100), p2.get("wrc_plus", 100) > p1.get("wrc_plus", 100)),
                ("⚡ Ofensiva & Sabermetría", "ISO", p1.get("iso_str", ".000"), p2.get("iso_str", ".000"), p1.get("iso", 0.0) > p2.get("iso", 0.0), p2.get("iso", 0.0) > p1.get("iso", 0.0)),
                ("⚡ Ofensiva & Sabermetría", "OPS", p1.get("ops_str", ".000"), p2.get("ops_str", ".000"), p1.get("ops", 0.0) > p2.get("ops", 0.0), p2.get("ops", 0.0) > p1.get("ops", 0.0)),
                ("⚡ Ofensiva & Sabermetría", "OBP", p1.get("obp_str", ".000"), p2.get("obp_str", ".000"), p1.get("obp", 0.0) > p2.get("obp", 0.0), p2.get("obp", 0.0) > p1.get("obp", 0.0)),
                ("⚡ Ofensiva & Sabermetría", "SLG", p1.get("slg_str", ".000"), p2.get("slg_str", ".000"), p1.get("slg", 0.0) > p2.get("slg", 0.0), p2.get("slg", 0.0) > p1.get("slg", 0.0)),
                ("⚡ Ofensiva & Sabermetría", "AVG", p1.get("avg_str", ".000"), p2.get("avg_str", ".000"), p1.get("avg", 0.0) > p2.get("avg", 0.0), p2.get("avg", 0.0) > p1.get("avg", 0.0)),
                ("⚡ Ofensiva & Sabermetría", "BB%", p1.get("bb_pct_str", "0.0%"), p2.get("bb_pct_str", "0.0%"), p1.get("bb_pct", 0) > p2.get("bb_pct", 0), p2.get("bb_pct", 0) > p1.get("bb_pct", 0)),
                ("⚡ Ofensiva & Sabermetría", "K%", p1.get("k_pct_str", "0.0%"), p2.get("k_pct_str", "0.0%"), p1.get("k_pct", 0) < p2.get("k_pct", 0), p2.get("k_pct", 0) < p1.get("k_pct", 0)),
                ("⚡ Ofensiva & Sabermetría", "BABIP", p1.get("babip_str", ".000"), p2.get("babip_str", ".000"), p1.get("babip", 0.0) > p2.get("babip", 0.0), p2.get("babip", 0.0) > p1.get("babip", 0.0)),

                # 🔢 Estadísticas de Volumen
                ("🔢 Estadísticas de Volumen", "Apariciones al Plato (PA)", str(p1.get("pa", 0)), str(p2.get("pa", 0)), p1.get("pa", 0) > p2.get("pa", 0), p2.get("pa", 0) > p1.get("pa", 0)),
                ("🔢 Estadísticas de Volumen", "Turnos al Bate (AB)", str(p1.get("ab", 0)), str(p2.get("ab", 0)), p1.get("ab", 0) > p2.get("ab", 0), p2.get("ab", 0) > p1.get("ab", 0)),
                ("🔢 Estadísticas de Volumen", "Hits (H)", str(p1.get("h", 0)), str(p2.get("h", 0)), p1.get("h", 0) > p2.get("h", 0), p2.get("h", 0) > p1.get("h", 0)),
                ("🔢 Estadísticas de Volumen", "Sencillos (1B)", str(d1_1), str(d1_2), d1_1 > d1_2, d1_2 > d1_1),
                ("🔢 Estadísticas de Volumen", "Dobles (2B)", str(d1), str(d2), d1 > d2, d2 > d1),
                ("🔢 Estadísticas de Volumen", "Triples (3B)", str(t1), str(t2), t1 > t2, t2 > t1),
                ("🔢 Estadísticas de Volumen", "Jonrones (HR)", str(hr1), str(hr2), hr1 > hr2, hr2 > hr1),
                ("🔢 Estadísticas de Volumen", "Bases Totales (TB)", str(tb1), str(tb2), tb1 > tb2, tb2 > tb1),
                ("🔢 Estadísticas de Volumen", "Extrabases (XBH)", str(xbh1), str(xbh2), xbh1 > xbh2, xbh2 > xbh1),
                ("🔢 Estadísticas de Volumen", "Carreras Impulsadas (RBI)", str(p1["rbi"]), str(p2["rbi"]), p1["rbi"] > p2["rbi"], p2["rbi"] > p1["rbi"]),
                ("🔢 Estadísticas de Volumen", "Carreras Anotadas (R)", str(p1["r"]), str(p2["r"]), p1["r"] > p2["r"], p2["r"] > p1["r"]),
                ("🔢 Estadísticas de Volumen", "Bases por Bolas (BB)", str(p1["bb"]), str(p2["bb"]), p1["bb"] > p2["bb"], p2["bb"] > p1["bb"]),
                ("🔢 Estadísticas de Volumen", "Ponches (SO)", str(p1["so"]), str(p2["so"]), p1["so"] < p2["so"], p2["so"] < p1["so"]),
                ("🔢 Estadísticas de Volumen", "Golpes Recibidos (HBP)", str(p1.get("hbp", 0)), str(p2.get("hbp", 0)), p1.get("hbp", 0) > p2.get("hbp", 0), p2.get("hbp", 0) > p1.get("hbp", 0)),
                ("🔢 Estadísticas de Volumen", "Fly de Sacrificio (SF)", str(p1.get("sf", 0)), str(p2.get("sf", 0)), p1.get("sf", 0) > p2.get("sf", 0), p2.get("sf", 0) > p1.get("sf", 0)),

                # 🏃 Corrido de Bases
                ("🏃 Corrido de Bases", "Bases Robadas (SB)", str(sb1), str(sb2), sb1 > sb2, sb2 > sb1),
                ("🏃 Corrido de Bases", "Atrapado Robando (CS)", str(cs1), str(cs2), cs1 < cs2, cs2 < cs1),
                ("🏃 Corrido de Bases", "Efectividad de Robo (SB%)", sb_pct1_str, sb_pct2_str, sb_pct1 > sb_pct2, sb_pct2 > sb_pct1),
                ("🏃 Corrido de Bases", "Intentos de Robo", str(att1), str(att2), att1 > att2, att2 > att1),

                # 🧤 Defensa & Fildeo
                ("🧤 Defensa & Fildeo", "Posición Principal", def1["pos"], def2["pos"], False, False),
                ("🧤 Defensa & Fildeo", "Juegos Defensivos (JJ)", str(def1["games"]), str(def2["games"]), def1["games"] > def2["games"], def2["games"] > def1["games"]),
                ("🧤 Defensa & Fildeo", "Innings Defensivos (Inn)", def1["inn"], def2["inn"], def1["inn_float"] > def2["inn_float"], def2["inn_float"] > def1["inn_float"]),
                ("🧤 Defensa & Fildeo", "Lances Totales (TC)", str(def1["tc"]), str(def2["tc"]), def1["tc"] > def2["tc"], def2["tc"] > def1["tc"]),
                ("🧤 Defensa & Fildeo", "Outs Realizados (PO)", str(def1["po"]), str(def2["po"]), def1["po"] > def2["po"], def2["po"] > def1["po"]),
                ("🧤 Defensa & Fildeo", "Asistencias (A)", str(def1["a"]), str(def2["a"]), def1["a"] > def2["a"], def2["a"] > def1["a"]),
                ("🧤 Defensa & Fildeo", "Errores Defensivos (E)", str(def1["e"]), str(def2["e"]), def1["e"] < def2["e"], def2["e"] < def1["e"]),
                ("🧤 Defensa & Fildeo", "Porcentaje de Fildeo (FPCT)", def1["fpct_str"], def2["fpct_str"], def1["fpct"] > def2["fpct"], def2["fpct"] > def1["fpct"]),
                ("🧤 Defensa & Fildeo", "Doble Plays (DP)", str(def1["dp"]), str(def2["dp"]), def1["dp"] > def2["dp"], def2["dp"] > def1["dp"]),
                ("🧤 Defensa & Fildeo", "Factor de Rango (RF/9)", def1["rf9_str"], def2["rf9_str"], def1["rf9"] > def2["rf9"], def2["rf9"] > def1["rf9"]),
            ]

            if def1["pos"] == "C" or def2["pos"] == "C":
                cats.extend([
                    ("🧤 Defensa & Fildeo", "Atrapados Robando (CS - C)", str(def1["cs"]), str(def2["cs"]), def1["cs"] > def2["cs"], def2["cs"] > def1["cs"]),
                    ("🧤 Defensa & Fildeo", "Efectividad de Freno (CS% - C)", def1["cs_pct_str"], def2["cs_pct_str"], def1["cs_pct"] > def2["cs_pct"], def2["cs_pct"] > def1["cs_pct"]),
                    ("🧤 Defensa & Fildeo", "Passed Balls (PB - C)", str(def1["pb"]), str(def2["pb"]), def1["pb"] < def2["pb"], def2["pb"] < def1["pb"]),
                ])

            rows = []
            p1_wins, p2_wins = 0, 0
            current_cat = None
            for category, metric_name, v1_str, v2_str, is_p1_win, is_p2_win in cats:
                if category != current_cat:
                    current_cat = category
                    rows.append({
                        "category": category,
                        "metric": category,
                        "val_1": "",
                        "val_2": "",
                        "winner": "",
                        "winner_color": "",
                        "winner_scheme": "gray",
                        "is_header": True,
                    })
                if is_p1_win:
                    p1_wins += 1
                    winner = f"{_shorten_name(p1['player_name'])} ({p1.get('team_abbr', 'CAR')})"
                    w_color = "#FDB827"
                    w_scheme = "amber"
                elif is_p2_win:
                    p2_wins += 1
                    winner = f"{_shorten_name(p2['player_name'])} ({p2.get('team_abbr', 'LVBP')})"
                    w_color = "#38BDF8"
                    w_scheme = "blue"
                else:
                    winner = "Empate"
                    w_color = "#94A3B8"
                    w_scheme = "gray"

                rows.append({
                    "category": category,
                    "metric": metric_name,
                    "val_1": v1_str,
                    "val_2": v2_str,
                    "winner": winner,
                    "winner_color": w_color,
                    "winner_scheme": w_scheme,
                    "is_header": False,
                })
            self.h2h_rows = rows

            name1 = f"{p1['player_name']} ({p1.get('team_abbr', 'CAR')})"
            name2 = f"{p2['player_name']} ({p2.get('team_abbr', 'LVBP')})"
            if p1_wins > p2_wins:
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {name1} lidera la comparativa cara a cara ganando {p1_wins} de las métricas evaluadas. "
                    f"Destaca en producción con OPS de {p1['ops_str']} y {p1['wrc_plus']} wRC+ frente a {name2} ({p2['ops_str']} OPS, {p2['wrc_plus']} wRC+)."
                )
            elif p2_wins > p1_wins:
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {name2} lidera la comparativa cara a cara ganando {p2_wins} de las métricas evaluadas. "
                    f"Destaca en producción con OPS de {p2['ops_str']} y {p2['wrc_plus']} wRC+ frente a {name1} ({p1['ops_str']} OPS, {p1['wrc_plus']} wRC+)."
                )
            else:
                self.h2h_verdict = (
                    f"⚖️ Veredicto Sabermétrico: Duelo sumamente parejo entre {name1} y {name2}. "
                    f"Ambos toleteros empatan en balance general con rendimiento sabermétrico muy equilibrado."
                )

        else:
            # LANZADORES
            p1 = _find_player(self.pitching_data_raw, self.selected_player_1)
            p2 = _find_player(self.pitching_data_raw, self.selected_player_2)
            if not p1 or not p2:
                self.h2h_verdict = "Seleccione dos jugadores para generar la comparativa sabermétrica."
                self.h2h_rows = []
                return

            t1_id = p1.get("team_id", 695)
            t2_id = p2.get("team_id", 695)
            self.player_1_card = {
                "name": p1["player_name"],
                "pos": p1.get("role", "Lanzador"),
                "team": f"{p1.get('team_name', 'Leones del Caracas')} ({p1.get('team_abbr', 'CAR')})",
                "team_logo": p1.get("team_logo") or get_team_logo(t1_id, size=72),
                "headshot": p1.get("headshot", ""),
                "badge": p1.get("team_abbr", "CAR"),
                "kpi_1": f"ERA {p1['era_str']}",
                "kpi_2": f"WHIP {p1['whip_str']}",
                "kpi_3": f"{p1['so']} K",
            }
            self.player_2_card = {
                "name": p2["player_name"],
                "pos": p2.get("role", "Lanzador"),
                "team": f"{p2.get('team_name', 'Equipo Rival')} ({p2.get('team_abbr', 'LVBP')})",
                "team_logo": p2.get("team_logo") or get_team_logo(t2_id, size=72),
                "headshot": p2.get("headshot", ""),
                "badge": p2.get("team_abbr", "LVBP"),
                "kpi_1": f"ERA {p2['era_str']}",
                "kpi_2": f"WHIP {p2['whip_str']}",
                "kpi_3": f"{p2['so']} K",
            }

            ip1, ip2 = p1["ip"], p2["ip"]
            h9_1 = (p1["h"] * 9.0 / ip1) if ip1 > 0 else 0.0
            h9_2 = (p2["h"] * 9.0 / ip2) if ip2 > 0 else 0.0
            r9_1 = (p1["r"] * 9.0 / ip1) if ip1 > 0 else 0.0
            r9_2 = (p2["r"] * 9.0 / ip2) if ip2 > 0 else 0.0
            hr9_1 = (p1["hr"] * 9.0 / ip1) if ip1 > 0 else 0.0
            hr9_2 = (p2["hr"] * 9.0 / ip2) if ip2 > 0 else 0.0

            w1, l1 = p1.get("w", 0), p1.get("l", 0)
            w2, l2 = p2.get("w", 0), p2.get("l", 0)
            wl_pct1 = (w1 / (w1 + l1)) if (w1 + l1) > 0 else 0.0
            wl_pct2 = (w2 / (w2 + l2)) if (w2 + l2) > 0 else 0.0

            cats_p = [
                # ⚡ Sabermetría & Dominio
                ("⚡ Sabermetría & Dominio", "FIP Independiente", p1["fip_str"], p2["fip_str"], p1["fip"] < p2["fip"], p2["fip"] < p1["fip"]),
                ("⚡ Sabermetría & Dominio", "WHIP (Control de Tráfico)", p1["whip_str"], p2["whip_str"], p1["whip"] < p2["whip"], p2["whip"] < p1["whip"]),
                ("⚡ Sabermetría & Dominio", "Ponches por 9 (K/9)", p1["k9_str"], p2["k9_str"], p1["k9"] > p2["k9"], p2["k9"] > p1["k9"]),
                ("⚡ Sabermetría & Dominio", "Boletos por 9 (BB/9)", p1["bb9_str"], p2["bb9_str"], p1["bb9"] < p2["bb9"], p2["bb9"] < p1["bb9"]),
                ("⚡ Sabermetría & Dominio", "Relación K/BB", p1["k_bb_str"], p2["k_bb_str"], p1["k_bb"] > p2["k_bb"], p2["k_bb"] > p1["k_bb"]),

                # 📊 Estadísticas de Rate
                ("📊 Estadísticas de Rate", "Efectividad (ERA)", p1["era_str"], p2["era_str"], p1["era"] < p2["era"], p2["era"] < p1["era"]),
                ("📊 Estadísticas de Rate", "Hits por 9 (H/9)", f"{h9_1:.2f}", f"{h9_2:.2f}", h9_1 < h9_2, h9_2 < h9_1),
                ("📊 Estadísticas de Rate", "Carreras por 9 (R/9)", f"{r9_1:.2f}", f"{r9_2:.2f}", r9_1 < r9_2, r9_2 < r9_1),
                ("📊 Estadísticas de Rate", "Jonrones por 9 (HR/9)", f"{hr9_1:.2f}", f"{hr9_2:.2f}", hr9_1 < hr9_2, hr9_2 < hr9_1),

                # 🔢 Estadísticas de Volumen
                ("🔢 Estadísticas de Volumen", "Innings Lanzados (IP)", p1["ip_str"], p2["ip_str"], p1["ip"] > p2["ip"], p2["ip"] > p1["ip"]),
                ("🔢 Estadísticas de Volumen", "Ponches Totales (SO)", str(p1["so"]), str(p2["so"]), p1["so"] > p2["so"], p2["so"] > p1["so"]),
                ("🔢 Estadísticas de Volumen", "Juegos Lanzados (G)", str(p1["g"]), str(p2["g"]), p1["g"] > p2["g"], p2["g"] > p1["g"]),
                ("🔢 Estadísticas de Volumen", "Juegos Iniciados (GS)", str(p1["gs"]), str(p2["gs"]), p1["gs"] > p2["gs"], p2["gs"] > p1["gs"]),
                ("🔢 Estadísticas de Volumen", "Victorias (W)", str(w1), str(w2), w1 > w2, w2 > w1),
                ("🔢 Estadísticas de Volumen", "Derrotas (L)", str(l1), str(l2), l1 < l2, l2 < l1),
                ("🔢 Estadísticas de Volumen", "Porcentaje de Victorias (W-L%)", f"{wl_pct1:.3f}".replace("0.", "."), f"{wl_pct2:.3f}".replace("0.", "."), wl_pct1 > wl_pct2, wl_pct2 > wl_pct1),
                ("🔢 Estadísticas de Volumen", "Juegos Salvados (SV)", str(p1["sv"]), str(p2["sv"]), p1["sv"] > p2["sv"], p2["sv"] > p1["sv"]),
                ("🔢 Estadísticas de Volumen", "Hits Permitidos (H)", str(p1["h"]), str(p2["h"]), p1["h"] < p2["h"], p2["h"] < p1["h"]),
                ("🔢 Estadísticas de Volumen", "Carreras Permitidas (R)", str(p1["r"]), str(p2["r"]), p1["r"] < p2["r"], p2["r"] < p1["r"]),
                ("🔢 Estadísticas de Volumen", "Carreras Limpias (ER)", str(p1["er"]), str(p2["er"]), p1["er"] < p2["er"], p2["er"] < p1["er"]),
                ("🔢 Estadísticas de Volumen", "Bases por Bolas (BB)", str(p1["bb"]), str(p2["bb"]), p1["bb"] < p2["bb"], p2["bb"] < p1["bb"]),
                ("🔢 Estadísticas de Volumen", "Jonrones Permitidos (HR)", str(p1["hr"]), str(p2["hr"]), p1["hr"] < p2["hr"], p2["hr"] < p1["hr"]),
            ]

            rows_p = []
            p1_wins, p2_wins = 0, 0
            current_cat = None
            for category, metric_name, v1_str, v2_str, is_p1_win, is_p2_win in cats_p:
                if category != current_cat:
                    current_cat = category
                    rows_p.append({
                        "category": category,
                        "metric": category,
                        "val_1": "",
                        "val_2": "",
                        "winner": "",
                        "winner_color": "",
                        "winner_scheme": "gray",
                        "is_header": True,
                    })
                if is_p1_win:
                    p1_wins += 1
                    winner = f"{_shorten_name(p1['player_name'])} ({p1.get('team_abbr', 'CAR')})"
                    w_color = "#FDB827"
                    w_scheme = "amber"
                elif is_p2_win:
                    p2_wins += 1
                    winner = f"{_shorten_name(p2['player_name'])} ({p2.get('team_abbr', 'LVBP')})"
                    w_color = "#38BDF8"
                    w_scheme = "blue"
                else:
                    winner = "Empate"
                    w_color = "#94A3B8"
                    w_scheme = "gray"

                rows_p.append({
                    "category": category,
                    "metric": metric_name,
                    "val_1": v1_str,
                    "val_2": v2_str,
                    "winner": winner,
                    "winner_color": w_color,
                    "winner_scheme": w_scheme,
                    "is_header": False,
                })
            self.h2h_rows = rows_p

            name1 = f"{p1['player_name']} ({p1.get('team_abbr', 'CAR')})"
            name2 = f"{p2['player_name']} ({p2.get('team_abbr', 'LVBP')})"
            if p1_wins > p2_wins:
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {name1} domina el montículo ganando {p1_wins} de las métricas evaluadas. "
                    f"Aventaja con efectividad de {p1['era_str']} ERA y WHIP de {p1['whip_str']} frente a {name2} ({p2['era_str']} ERA, {p2['whip_str']} WHIP)."
                )
            elif p2_wins > p1_wins:
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {name2} domina el montículo ganando {p2_wins} de las métricas evaluadas. "
                    f"Aventaja con efectividad de {p2['era_str']} ERA y WHIP de {p2['whip_str']} frente a {name1} ({p1['era_str']} ERA, {p1['whip_str']} WHIP)."
                )
            else:
                self.h2h_verdict = (
                    f"⚖️ Veredicto Sabermétrico: Duelo de brazos sumamente equilibrado entre {name1} y {name2}. "
                    f"Ambos lanzadores exhiben solidez similar en su staff monticular."
                )

    # ── Percentiles y Gráficos Reactivos (@rx.var) ───────────────────────────
    @rx.var
    def percentile_table_rows(self) -> List[Dict[str, Any]]:
        """Tabla estructurada de percentiles 0-100 para ambos jugadores con valores y ventajas."""
        if not self.selected_player_1 or not self.selected_player_2:
            return []

        if self.compare_type == "Bateadores":
            p1 = _find_player(self.batting_data_raw, self.selected_player_1)
            p2 = _find_player(self.batting_data_raw, self.selected_player_2)
            pool = [p for p in self.batting_data_raw if p["ab"] >= 5] or self.batting_data_raw

            if not p1 or not p2 or not pool:
                return []

            axes = [
                ("Contacto (AVG)", "avg", "avg_str", True),
                ("Embasado (OBP)", "obp", "obp_str", True),
                ("Poder (SLG)", "slg", "slg_str", True),
                ("Producción (OPS)", "ops", "ops_str", True),
                ("wOBA", "woba", "woba_str", True),
                ("wRC+", "wrc_plus", "wrc_plus", True),
                ("Extrabases (ISO)", "iso", "iso_str", True),
                ("Paciencia (BB%)", "bb_pct", "bb_pct_str", True),
            ]

            def get_pct(val, key, higher_better):
                vals = [x.get(key, 0) for x in pool]
                if not vals:
                    return 50
                if higher_better:
                    return min(100, max(5, int((sum(1 for v in vals if v <= val) / len(vals)) * 100)))
                else:
                    return min(100, max(5, int((sum(1 for v in vals if v >= val) / len(vals)) * 100)))

            rows = []
            for name, key, str_key, higher_better in axes:
                v1_raw = p1.get(key, 0)
                v2_raw = p2.get(key, 0)
                v1_str = str(p1.get(str_key, v1_raw))
                v2_str = str(p2.get(str_key, v2_raw))
                pct1 = get_pct(v1_raw, key, higher_better)
                pct2 = get_pct(v2_raw, key, higher_better)

                if pct1 > pct2:
                    leader = f"{_shorten_name(p1['player_name'])} ({p1.get('team_abbr', 'CAR')})"
                    leader_scheme = "amber"
                elif pct2 > pct1:
                    leader = f"{_shorten_name(p2['player_name'])} ({p2.get('team_abbr', 'LVBP')})"
                    leader_scheme = "blue"
                else:
                    leader = "Empate"
                    leader_scheme = "gray"

                rows.append({
                    "metric": name,
                    "val_1": v1_str,
                    "pct_1": pct1,
                    "pct_1_str": f"P{pct1}",
                    "val_2": v2_str,
                    "pct_2": pct2,
                    "pct_2_str": f"P{pct2}",
                    "leader": leader,
                    "leader_scheme": leader_scheme,
                })
            return rows

        else:
            # Lanzadores
            p1 = _find_player(self.pitching_data_raw, self.selected_player_1)
            p2 = _find_player(self.pitching_data_raw, self.selected_player_2)
            pool = [p for p in self.pitching_data_raw if p["ip"] >= 2.0] or self.pitching_data_raw

            if not p1 or not p2 or not pool:
                return []

            axes_p = [
                ("Efectividad (ERA)", "era", "era_str", False),
                ("Control (WHIP)", "whip", "whip_str", False),
                ("FIP Independiente", "fip", "fip_str", False),
                ("Dominio (K/9)", "k9", "k9_str", True),
                ("Comando (BB/9)", "bb9", "bb9_str", False),
                ("Relación K/BB", "k_bb", "k_bb_str", True),
                ("Innings (IP)", "ip", "ip_str", True),
                ("Ponches (SO)", "so", "so", True),
            ]

            def get_pct_p(val, key, higher_better):
                vals = [x.get(key, 0) for x in pool]
                if not vals:
                    return 50
                if higher_better:
                    return min(100, max(5, int((sum(1 for v in vals if v <= val) / len(vals)) * 100)))
                else:
                    return min(100, max(5, int((sum(1 for v in vals if v >= val) / len(vals)) * 100)))

            rows = []
            for name, key, str_key, higher_better in axes_p:
                v1_raw = p1.get(key, 0)
                v2_raw = p2.get(key, 0)
                v1_str = str(p1.get(str_key, v1_raw))
                v2_str = str(p2.get(str_key, v2_raw))
                pct1 = get_pct_p(v1_raw, key, higher_better)
                pct2 = get_pct_p(v2_raw, key, higher_better)

                if pct1 > pct2:
                    leader = f"{_shorten_name(p1['player_name'])} ({p1.get('team_abbr', 'CAR')})"
                    leader_scheme = "amber"
                elif pct2 > pct1:
                    leader = f"{_shorten_name(p2['player_name'])} ({p2.get('team_abbr', 'LVBP')})"
                    leader_scheme = "blue"
                else:
                    leader = "Empate"
                    leader_scheme = "gray"

                rows.append({
                    "metric": name,
                    "val_1": v1_str,
                    "pct_1": pct1,
                    "pct_1_str": f"P{pct1}",
                    "val_2": v2_str,
                    "pct_2": pct2,
                    "pct_2_str": f"P{pct2}",
                    "leader": leader,
                    "leader_scheme": leader_scheme,
                })
            return rows

    @rx.var
    def radar_chart_figure(self) -> go.Figure:
        """Genera el Radar Polar sabermétrico multidimensional de 8 ejes (Percentiles 0-100 relativos a toda la LVBP)."""
        fig = go.Figure()

        if self.compare_type == "Bateadores":
            p1 = _find_player(self.batting_data_raw, self.selected_player_1)
            p2 = _find_player(self.batting_data_raw, self.selected_player_2)
            pool = [p for p in self.batting_data_raw if p["ab"] >= 5] or self.batting_data_raw

            if not p1 or not p2 or not pool:
                fig.update_layout(template="plotly_dark", height=420)
                return fig

            axes = [
                ("Contacto (AVG)", "avg", True),
                ("Embasado (OBP)", "obp", True),
                ("Poder (SLG)", "slg", True),
                ("Producción (OPS)", "ops", True),
                ("wOBA", "woba", True),
                ("wRC+", "wrc_plus", True),
                ("Extrabases (ISO)", "iso", True),
                ("Paciencia (BB%)", "bb_pct", True),
            ]

            def get_pct(val, key, higher_better):
                vals = [x.get(key, 0) for x in pool]
                if not vals:
                    return 50
                if higher_better:
                    return min(100, max(5, int((sum(1 for v in vals if v <= val) / len(vals)) * 100)))
                else:
                    return min(100, max(5, int((sum(1 for v in vals if v >= val) / len(vals)) * 100)))

            r1 = [get_pct(p1.get(k, 0), k, hb) for _, k, hb in axes]
            r2 = [get_pct(p2.get(k, 0), k, hb) for _, k, hb in axes]
            theta = [name for name, _, _ in axes]

            # Cerrar el loop del radar
            r1.append(r1[0])
            r2.append(r2[0])
            theta.append(theta[0])

            fig.add_trace(go.Scatterpolar(
                r=r1,
                theta=theta,
                fill="toself",
                fillcolor="rgba(253, 184, 39, 0.25)",
                line=dict(color="#FDB827", width=3),
                name=f"🔴 {p1['player_name']} ({p1.get('team_abbr', 'CAR')})",
            ))
            fig.add_trace(go.Scatterpolar(
                r=r2,
                theta=theta,
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.25)",
                line=dict(color="#38BDF8", width=3),
                name=f"🔵 {p2['player_name']} ({p2.get('team_abbr', 'LVBP')})",
            ))

        else:
            # LANZADORES
            p1 = _find_player(self.pitching_data_raw, self.selected_player_1)
            p2 = _find_player(self.pitching_data_raw, self.selected_player_2)
            pool = [p for p in self.pitching_data_raw if p["ip"] >= 2.0] or self.pitching_data_raw

            if not p1 or not p2 or not pool:
                fig.update_layout(template="plotly_dark", height=420)
                return fig

            axes_p = [
                ("Efectividad (ERA)", "era", False),
                ("Control (WHIP)", "whip", False),
                ("FIP Independiente", "fip", False),
                ("Dominio (K/9)", "k9", True),
                ("Comando (BB/9)", "bb9", False),
                ("Relación K/BB", "k_bb", True),
                ("Innings (IP)", "ip", True),
                ("Ponches (SO)", "so", True),
            ]

            def get_pct_p(val, key, higher_better):
                vals = [x.get(key, 0) for x in pool]
                if not vals:
                    return 50
                if higher_better:
                    return min(100, max(5, int((sum(1 for v in vals if v <= val) / len(vals)) * 100)))
                else:
                    return min(100, max(5, int((sum(1 for v in vals if v >= val) / len(vals)) * 100)))

            r1 = [get_pct_p(p1.get(k, 0), k, hb) for _, k, hb in axes_p]
            r2 = [get_pct_p(p2.get(k, 0), k, hb) for _, k, hb in axes_p]
            theta_p = [name for name, _, _ in axes_p]

            r1.append(r1[0])
            r2.append(r2[0])
            theta_p.append(theta_p[0])

            fig.add_trace(go.Scatterpolar(
                r=r1,
                theta=theta_p,
                fill="toself",
                fillcolor="rgba(253, 184, 39, 0.25)",
                line=dict(color="#FDB827", width=3),
                name=f"🔴 {p1['player_name']} ({p1.get('team_abbr', 'CAR')})",
            ))
            fig.add_trace(go.Scatterpolar(
                r=r2,
                theta=theta_p,
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.25)",
                line=dict(color="#38BDF8", width=3),
                name=f"🔵 {p2['player_name']} ({p2.get('team_abbr', 'LVBP')})",
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[20, 40, 60, 80, 100],
                    ticktext=["20", "40", "60", "80", "100"],
                    tickfont=dict(size=10, color="#94A3B8"),
                    gridcolor="rgba(255, 255, 255, 0.1)",
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color="#FFFFFF", family="Inter"),
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    linecolor="rgba(255, 255, 255, 0.2)",
                ),
                bgcolor="#0D152B",
            ),
            paper_bgcolor="#070B19",
            plot_bgcolor="#070B19",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(color="#FFFFFF", size=12),
            ),
            margin=dict(l=40, r=40, t=30, b=50),
            height=420,
        )
        return fig

    @rx.var
    def top_batters_chart(self) -> go.Figure:
        """Gráfico de barras horizontal para los 10 mejores bateadores en OPS."""
        fig = go.Figure()
        data = self.batting_data_raw
        if self.selected_batting_team != "Toda la LVBP (Overall)":
            data = [p for p in data if p.get("team_name") == self.selected_batting_team]
        data = sorted([p for p in data if p["ab"] >= self.min_ab], key=lambda x: x["ops"], reverse=False)[-10:]
        if data:
            names = [f"{p['player_name']} ({p.get('team_abbr', '')})" if self.selected_batting_team == "Toda la LVBP (Overall)" else p["player_name"] for p in data]
            ops_vals = [p["ops"] for p in data]

            fig.add_trace(go.Bar(
                x=ops_vals,
                y=names,
                orientation="h",
                marker=dict(
                    color=ops_vals,
                    colorscale=[[0, "#002D62"], [0.5, "#D8252C"], [1.0, "#FDB827"]],
                    line=dict(color="rgba(253, 184, 39, 0.4)", width=1),
                ),
                text=[f"{v:.3f}" for v in ops_vals],
                textposition="auto",
            ))

        team_title = f" ({self.selected_batting_team})" if self.selected_batting_team != "Toda la LVBP (Overall)" else " (Toda la LVBP)"
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text=f"Top 10 — Líderes en OPS{team_title}", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title="OPS (On-base Plus Slugging)", gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            margin=dict(l=120, r=30, t=40, b=40),
            height=340,
        )
        return fig

    @rx.var
    def top_pitchers_chart(self) -> go.Figure:
        """Gráfico de barras horizontal para los mejores lanzadores en Ponches (SO)."""
        fig = go.Figure()
        data = self.pitching_data_raw
        if self.selected_pitching_team != "Toda la LVBP (Overall)":
            data = [p for p in data if p.get("team_name") == self.selected_pitching_team]
        data = sorted([p for p in data if p["ip"] >= self.min_ip], key=lambda x: x["so"], reverse=False)[-10:]
        if data:
            names = [f"{p['player_name']} ({p.get('team_abbr', '')})" if self.selected_pitching_team == "Toda la LVBP (Overall)" else p["player_name"] for p in data]
            so_vals = [p["so"] for p in data]

            fig.add_trace(go.Bar(
                x=so_vals,
                y=names,
                orientation="h",
                marker=dict(
                    color=so_vals,
                    colorscale=[[0, "#002D62"], [1.0, "#FDB827"]],
                    line=dict(color="rgba(253, 184, 39, 0.4)", width=1),
                ),
                text=[str(v) for v in so_vals],
                textposition="auto",
            ))

        team_title = f" ({self.selected_pitching_team})" if self.selected_pitching_team != "Toda la LVBP (Overall)" else " (Toda la LVBP)"
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text=f"Top 10 — Líderes en Ponches (SO){team_title}", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title="Ponches (SO)", gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            margin=dict(l=120, r=30, t=40, b=40),
            height=340,
        )
        return fig

