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
from core.teams import get_team_logo, get_team_abbr
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


class IndividualesState(AppState):
    """Estado reactivo para estadísticas individuales y comparador sabermétrico."""

    # ── Pestaña Activa ──────────────────────────────────────────────────────────
    active_tab: str = "bateo"  # "bateo", "pitcheo", "fildeo", "comparador"

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
        "name": "-", "pos": "-", "team": "Leones del Caracas", "headshot": "", "badge": "LEO"
    }
    player_2_card: Dict[str, Any] = {
        "name": "-", "pos": "-", "team": "Leones del Caracas", "headshot": "", "badge": "LEO"
    }
    h2h_verdict: str = "Seleccione dos jugadores para generar el veredicto sabermétrico."

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

    # ── Carga y Cálculo de Estadísticas ─────────────────────────────────────────
    def load_all_stats(self):
        """Descarga datos de Supabase y calcula métricas sabermétricas avanzadas."""
        season = self.selected_season

        # ── 1. BATEO ────────────────────────────────────────────────────────────
        df_bat = get_batting_stats(team_id=695, limit=150, season=season)
        if df_bat is not None and not df_bat.empty:
            bat_list = []
            for _, row in df_bat.iterrows():
                p_id = _safe_int(row.get("player_id", 0))
                name = _safe_str(row.get("player_name", "Desconocido"))
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

                headshot_url = f"https://midfield.mlbstatic.com/v1/people/{p_id}/spots/120" if p_id > 0 else ""

                bat_list.append({
                    "player_id": p_id,
                    "player_name": name,
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
                })

            self.batting_data_raw = bat_list
            self.available_batters = [p["player_name"] for p in sorted(bat_list, key=lambda x: x["pa"], reverse=True)]

            # Calcular KPIs de Bateo (con mínimo de 10 AB si existen)
            qual_bat = [b for b in bat_list if b["ab"] >= 10] or bat_list
            if qual_bat:
                best_avg = max(qual_bat, key=lambda x: x["avg"])
                best_hr = max(qual_bat, key=lambda x: x["hr"])
                best_rbi = max(qual_bat, key=lambda x: x["rbi"])
                best_ops = max(qual_bat, key=lambda x: x["ops"])
                best_woba = max(qual_bat, key=lambda x: x["woba"])
                best_wrc = max(qual_bat, key=lambda x: x["wrc_plus"])

                self.batting_kpis = {
                    "avg_val": best_avg["avg_str"], "avg_player": best_avg["player_name"],
                    "hr_val": str(best_hr["hr"]), "hr_player": best_hr["player_name"],
                    "rbi_val": str(best_rbi["rbi"]), "rbi_player": best_rbi["player_name"],
                    "ops_val": best_ops["ops_str"], "ops_player": best_ops["player_name"],
                    "woba_val": best_woba["woba_str"], "woba_player": best_woba["player_name"],
                    "wrc_val": f"{best_wrc['wrc_plus']} wRC+", "wrc_player": best_wrc["player_name"],
                }
        else:
            self.batting_data_raw = []
            self.available_batters = []

        # ── 2. PITCHEO ──────────────────────────────────────────────────────────
        df_pit = get_pitching_stats(team_id=695, limit=150, season=season)
        if df_pit is not None and not df_pit.empty:
            pit_list = []
            for _, row in df_pit.iterrows():
                p_id = _safe_int(row.get("player_id", 0))
                name = _safe_str(row.get("player_name", "Desconocido"))
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
            self.available_pitchers = [p["player_name"] for p in sorted(pit_list, key=lambda x: x["ip"], reverse=True)]

            qual_pit = [p for p in pit_list if p["ip"] >= 3.0] or pit_list
            if qual_pit:
                best_era = min(qual_pit, key=lambda x: x["era"])
                best_so = max(qual_pit, key=lambda x: x["so"])
                best_whip = min(qual_pit, key=lambda x: x["whip"])
                best_fip = min(qual_pit, key=lambda x: x["fip"])
                best_k9 = max(qual_pit, key=lambda x: x["k9"])
                best_sv = max(qual_pit, key=lambda x: x["sv"])

                self.pitching_kpis = {
                    "era_val": best_era["era_str"], "era_player": best_era["player_name"],
                    "so_val": str(best_so["so"]), "so_player": best_so["player_name"],
                    "whip_val": best_whip["whip_str"], "whip_player": best_whip["player_name"],
                    "fip_val": best_fip["fip_str"], "fip_player": best_fip["player_name"],
                    "k9_val": best_k9["k9_str"], "k9_player": best_k9["player_name"],
                    "sv_val": str(best_sv["sv"]), "sv_player": best_sv["player_name"],
                }
        else:
            self.pitching_data_raw = []
            self.available_pitchers = []

        # ── 3. FILDEO / DEFENSA ────────────────────────────────────────────────
        df_fld = get_individual_fielding_stats(season=season, team_id=695)
        if df_fld is not None and not df_fld.empty:
            fld_list = []
            for _, row in df_fld.iterrows():
                p_id = _safe_int(row.get("player_id", 0))
                name = _safe_str(row.get("player_name", "Desconocido"))
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

            qual_fld = [f for f in fld_list if f["tc"] >= 10] or fld_list
            if qual_fld:
                best_fpct = max(qual_fld, key=lambda x: x["fpct"])
                best_a = max(qual_fld, key=lambda x: x["a"])
                best_dp = max(qual_fld, key=lambda x: x["dp"])
                best_po = max(qual_fld, key=lambda x: x["po"])
                best_cs = max(qual_fld, key=lambda x: x["cs"])

                self.fielding_kpis = {
                    "fpct_val": best_fpct["fpct_str"], "fpct_player": f"{best_fpct['player_name']} ({best_fpct['position']})",
                    "a_val": str(best_a["a"]), "a_player": f"{best_a['player_name']} ({best_a['position']})",
                    "dp_val": str(best_dp["dp"]), "dp_player": f"{best_dp['player_name']} ({best_dp['position']})",
                    "po_val": str(best_po["po"]), "po_player": f"{best_po['player_name']} ({best_po['position']})",
                    "cs_val": str(best_cs["cs"]), "cs_player": f"{best_cs['player_name']} (C)",
                }
        else:
            self.fielding_data_raw = []

        # Inicializar selección por defecto en Comparador H2H
        if self.available_batters and len(self.available_batters) >= 2:
            if not self.selected_player_1:
                self.selected_player_1 = self.available_batters[0]
            if not self.selected_player_2:
                self.selected_player_2 = self.available_batters[1]
        self.update_h2h_comparison()

    # ── Handlers de Filtrado y Navegación ───────────────────────────────────────
    def set_active_tab(self, tab: str):
        """Cambia la pestaña activa."""
        self.active_tab = tab

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

    def set_compare_type(self, val: str):
        self.compare_type = val
        if val == "Bateadores":
            if self.available_batters and len(self.available_batters) >= 2:
                self.selected_player_1 = self.available_batters[0]
                self.selected_player_2 = self.available_batters[1]
        else:
            if self.available_pitchers and len(self.available_pitchers) >= 2:
                self.selected_player_1 = self.available_pitchers[0]
                self.selected_player_2 = self.available_pitchers[1]
        self.update_h2h_comparison()

    def set_selected_player_1(self, val: str):
        self.selected_player_1 = val
        self.update_h2h_comparison()

    def set_selected_player_2(self, val: str):
        self.selected_player_2 = val
        self.update_h2h_comparison()

    # ── Computed Properties: Listas Filtradas ───────────────────────────────────
    @rx.var
    def filtered_batting(self) -> List[Dict[str, Any]]:
        """Lista filtrada y ordenada de bateadores."""
        data = [p for p in self.batting_data_raw if p["ab"] >= self.min_ab]
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
        data = [p for p in self.pitching_data_raw if p["ip"] >= self.min_ip]
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
        data = list(self.fielding_data_raw)
        if self.selected_fielding_pos != "Todas":
            data = [p for p in data if p["position"] == self.selected_fielding_pos]
        if self.search_fielding:
            s = self.search_fielding.lower().strip()
            data = [p for p in data if s in p["player_name"].lower()]
        return sorted(data, key=lambda x: x["tc"], reverse=True)

    @rx.var
    def is_catcher_view(self) -> bool:
        return self.selected_fielding_pos == "C"

    def generate_h2h_comparison(self):
        """Genera la comparativa sabermétrica entre los dos jugadores seleccionados."""
        return self.update_h2h_comparison()

    # ── Actualización de Comparación H2H ───────────────────────────────────────
    def update_h2h_comparison(self):
        """Calcula percentiles sabermétricos relativos, tarjetas de perfil y veredicto."""
        if not self.selected_player_1 or not self.selected_player_2:
            self.h2h_verdict = "Seleccione dos jugadores para generar la comparativa sabermétrica."
            self.h2h_rows = []
            return

        if self.compare_type == "Bateadores":
            p1 = next((p for p in self.batting_data_raw if p["player_name"] == self.selected_player_1), None)
            p2 = next((p for p in self.batting_data_raw if p["player_name"] == self.selected_player_2), None)
            if not p1 or not p2:
                self.h2h_verdict = "Seleccione dos jugadores para generar la comparativa sabermétrica."
                self.h2h_rows = []
                return

            self.player_1_card = {
                "name": p1["player_name"],
                "pos": "OF/IF",
                "team": "Leones del Caracas",
                "headshot": p1["headshot"],
                "badge": "CAR",
                "kpi_1": f"AVG {p1['avg_str']}",
                "kpi_2": f"OPS {p1['ops_str']}",
                "kpi_3": f"{p1['hr']} HR",
            }
            self.player_2_card = {
                "name": p2["player_name"],
                "pos": "OF/IF",
                "team": "Leones del Caracas",
                "headshot": p2["headshot"],
                "badge": "CAR",
                "kpi_1": f"AVG {p2['avg_str']}",
                "kpi_2": f"OPS {p2['ops_str']}",
                "kpi_3": f"{p2['hr']} HR",
            }

            # Definición de las 8 categorías sabermétricas
            cats = [
                ("Promedio (AVG)", p1["avg_str"], p2["avg_str"], p1["avg"] > p2["avg"], p2["avg"] > p1["avg"]),
                ("Embasado (OBP)", p1["obp_str"], p2["obp_str"], p1["obp"] > p2["obp"], p2["obp"] > p1["obp"]),
                ("Slugging (SLG)", p1["slg_str"], p2["slg_str"], p1["slg"] > p2["slg"], p2["slg"] > p1["slg"]),
                ("OPS Total", p1["ops_str"], p2["ops_str"], p1["ops"] > p2["ops"], p2["ops"] > p1["ops"]),
                ("Poder Aislado (ISO)", p1["iso_str"], p2["iso_str"], p1["iso"] > p2["iso"], p2["iso"] > p1["iso"]),
                ("wOBA Sabermétrico", p1["woba_str"], p2["woba_str"], p1["woba"] > p2["woba"], p2["woba"] > p1["woba"]),
                ("wRC+ Normalizado", str(p1["wrc_plus"]), str(p2["wrc_plus"]), p1["wrc_plus"] > p2["wrc_plus"], p2["wrc_plus"] > p1["wrc_plus"]),
                ("Jonrones (HR)", str(p1["hr"]), str(p2["hr"]), p1["hr"] > p2["hr"], p2["hr"] > p1["hr"]),
                ("Impulsadas (RBI)", str(p1["rbi"]), str(p2["rbi"]), p1["rbi"] > p2["rbi"], p2["rbi"] > p1["rbi"]),
                ("Bases Robadas (SB)", str(p1["sb"]), str(p2["sb"]), p1["sb"] > p2["sb"], p2["sb"] > p1["sb"]),
            ]

            rows = []
            p1_wins, p2_wins = 0, 0
            for metric_name, v1_str, v2_str, is_p1_win, is_p2_win in cats:
                if is_p1_win:
                    p1_wins += 1
                    winner = p1["player_name"]
                    w_color = "#FDB827"
                elif is_p2_win:
                    p2_wins += 1
                    winner = p2["player_name"]
                    w_color = "#38BDF8"
                else:
                    winner = "Empate"
                    w_color = "#94A3B8"

                rows.append({
                    "metric": metric_name,
                    "val_1": v1_str,
                    "val_2": v2_str,
                    "winner": winner,
                    "winner_color": w_color,
                    "winner_scheme": "amber" if winner != "Empate" else "gray",
                })
            self.h2h_rows = rows

            # Veredicto automático
            if p1_wins > p2_wins:
                leader = p1["player_name"]
                margin = p1_wins
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {leader} aventaja en {margin} de las {len(cats)} métricas evaluadas. "
                    f"Destaca principalmente por su OPS de {p1['ops_str']} y wOBA de {p1['woba_str']} vs {p2['player_name']} ({p2['ops_str']} OPS)."
                )
            elif p2_wins > p1_wins:
                leader = p2["player_name"]
                margin = p2_wins
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {leader} aventaja en {margin} de las {len(cats)} métricas evaluadas. "
                    f"Destaca principalmente por su OPS de {p2['ops_str']} y wOBA de {p2['woba_str']} vs {p1['player_name']} ({p1['ops_str']} OPS)."
                )
            else:
                self.h2h_verdict = (
                    f"⚖️ Veredicto Sabermétrico: Duelo sumamente parejo. Ambos toleteros dividen honores con balance idéntico de métricas favorables."
                )

        else:
            # LANZADORES
            p1 = next((p for p in self.pitching_data_raw if p["player_name"] == self.selected_player_1), None)
            p2 = next((p for p in self.pitching_data_raw if p["player_name"] == self.selected_player_2), None)
            if not p1 or not p2:
                self.h2h_verdict = "Seleccione dos jugadores para generar la comparativa sabermétrica."
                self.h2h_rows = []
                return

            self.player_1_card = {
                "name": p1["player_name"],
                "pos": p1["role"],
                "team": "Leones del Caracas",
                "headshot": p1["headshot"],
                "badge": "CAR",
                "kpi_1": f"ERA {p1['era_str']}",
                "kpi_2": f"WHIP {p1['whip_str']}",
                "kpi_3": f"{p1['so']} K",
            }
            self.player_2_card = {
                "name": p2["player_name"],
                "pos": p2["role"],
                "team": "Leones del Caracas",
                "headshot": p2["headshot"],
                "badge": "CAR",
                "kpi_1": f"ERA {p2['era_str']}",
                "kpi_2": f"WHIP {p2['whip_str']}",
                "kpi_3": f"{p2['so']} K",
            }

            cats_p = [
                ("Efectividad (ERA)", p1["era_str"], p2["era_str"], p1["era"] < p2["era"], p2["era"] < p1["era"]),
                ("WHIP (Tráfico)", p1["whip_str"], p2["whip_str"], p1["whip"] < p2["whip"], p2["whip"] < p1["whip"]),
                ("FIP Independiente", p1["fip_str"], p2["fip_str"], p1["fip"] < p2["fip"], p2["fip"] < p1["fip"]),
                ("Ponches por 9 (K/9)", p1["k9_str"], p2["k9_str"], p1["k9"] > p2["k9"], p2["k9"] > p1["k9"]),
                ("Control (BB/9)", p1["bb9_str"], p2["bb9_str"], p1["bb9"] < p2["bb9"], p2["bb9"] < p1["bb9"]),
                ("Relación K/BB", p1["k_bb_str"], p2["k_bb_str"], p1["k_bb"] > p2["k_bb"], p2["k_bb"] > p1["k_bb"]),
                ("Innings Lanzados (IP)", p1["ip_str"], p2["ip_str"], p1["ip"] > p2["ip"], p2["ip"] > p1["ip"]),
                ("Ponches Totales (SO)", str(p1["so"]), str(p2["so"]), p1["so"] > p2["so"], p2["so"] > p1["so"]),
                ("Juegos Salvados (SV)", str(p1["sv"]), str(p2["sv"]), p1["sv"] > p2["sv"], p2["sv"] > p1["sv"]),
            ]

            rows_p = []
            p1_wins, p2_wins = 0, 0
            for metric_name, v1_str, v2_str, is_p1_win, is_p2_win in cats_p:
                if is_p1_win:
                    p1_wins += 1
                    winner = p1["player_name"]
                    w_color = "#FDB827"
                elif is_p2_win:
                    p2_wins += 1
                    winner = p2["player_name"]
                    w_color = "#38BDF8"
                else:
                    winner = "Empate"
                    w_color = "#94A3B8"

                rows_p.append({
                    "metric": metric_name,
                    "val_1": v1_str,
                    "val_2": v2_str,
                    "winner": winner,
                    "winner_color": w_color,
                    "winner_scheme": "amber" if winner != "Empate" else "gray",
                })
            self.h2h_rows = rows_p

            if p1_wins > p2_wins:
                leader = p1["player_name"]
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {leader} domina la comparativa con mejor efectividad ({p1['era_str']} ERA vs {p2['era_str']}) "
                    f"y un control más sólido ({p1['whip_str']} WHIP)."
                )
            elif p2_wins > p1_wins:
                leader = p2["player_name"]
                self.h2h_verdict = (
                    f"🏆 Veredicto Sabermétrico: {leader} domina la comparativa con mejor efectividad ({p2['era_str']} ERA vs {p1['era_str']}) "
                    f"y un control más sólido ({p2['whip_str']} WHIP)."
                )
            else:
                self.h2h_verdict = (
                    f"⚖️ Veredicto Sabermétrico: Rendimiento muy similar en el montículo entre ambos lanzadores."
                )

    # ── Gráficos Reactivos (@rx.var) ───────────────────────────────────────────
    @rx.var
    def radar_chart_figure(self) -> go.Figure:
        """Genera el Radar Polar sabermétrico multidimensional de 8 ejes (Percentiles 0-100)."""
        fig = go.Figure()

        if self.compare_type == "Bateadores":
            p1 = next((p for p in self.batting_data_raw if p["player_name"] == self.selected_player_1), None)
            p2 = next((p for p in self.batting_data_raw if p["player_name"] == self.selected_player_2), None)
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
                ("Paciencia (BB)", "bb", True),
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
                name=p1["player_name"],
            ))
            fig.add_trace(go.Scatterpolar(
                r=r2,
                theta=theta,
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.25)",
                line=dict(color="#38BDF8", width=3),
                name=p2["player_name"],
            ))

        else:
            # LANZADORES
            p1 = next((p for p in self.pitching_data_raw if p["player_name"] == self.selected_player_1), None)
            p2 = next((p for p in self.pitching_data_raw if p["player_name"] == self.selected_player_2), None)
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
                name=p1["player_name"],
            ))
            fig.add_trace(go.Scatterpolar(
                r=r2,
                theta=theta_p,
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.25)",
                line=dict(color="#38BDF8", width=3),
                name=p2["player_name"],
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
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
        data = sorted([p for p in self.batting_data_raw if p["ab"] >= self.min_ab], key=lambda x: x["ops"], reverse=False)[-10:]
        if data:
            names = [p["player_name"] for p in data]
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

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text="Top 10 — Líderes en OPS", font=dict(color="#FFFFFF", size=14)),
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
        data = sorted([p for p in self.pitching_data_raw if p["ip"] >= self.min_ip], key=lambda x: x["so"], reverse=False)[-10:]
        if data:
            names = [p["player_name"] for p in data]
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

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#070B19",
            plot_bgcolor="#0D152B",
            title=dict(text="Top 10 — Líderes en Ponches (SO)", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title="Ponches (SO)", gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            margin=dict(l=120, r=30, t=40, b=40),
            height=340,
        )
        return fig
