# republicaraquistapp/state/standings_state.py
"""
standings_state.py
------------------
Estado reactivo especializado para las vistas de Dashboard (/) y Posiciones (/standings).
Maneja de forma centralizada y genuina:
1. Tabla de Posiciones Oficial con soporte de fases (Regular, Round Robin, Wild Card, Final, Acumulado).
2. Sabermetría Pitagórica (Bill James / Davenport 1.83) con xW, xL, Delta W y diagnóstico de clutch.
3. Ratings ELO oficiales de la LVBP y Power Rankings.
4. Simulaciones Monte Carlo de 5,000 iteraciones (Probabilidades de Playoff, Round Robin, Final y Campeón).
5. Predictor de enfrentamientos H2H con ventaja reglamentaria de localía (+35 pts ELO).
6. Desglose Situacional (Día/Noche, Home/Away, 1 Carrera, Remontadas) y Récord por Semanas ISO.
"""

from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd
import numpy as np

from republicaraquistapp.state.base_state import AppState
from core.supabase_client import (
    get_available_seasons,
    get_current_season,
    get_standings,
    get_recent_games,
    get_leones_advanced_stats,
    get_weekly_records,
    init_supabase,
)
from core.teams import (
    LVBP_TEAMS,
    LVBP_ABBR,
    LVBP_COLORS,
    get_team_logo,
    get_team_name,
    get_team_abbr,
    get_team_color,
    resolve_team_id,
)
from core.elo import (
    calculate_matchup_win_prob,
    simulate_monte_carlo_projections,
    BASE_ELO,
    HOME_ADVANTAGE,
)

# Nombres canónicos de los 8 equipos LVBP
ALL_LVBP_NAMES: List[str] = [
    "Leones del Caracas",
    "Navegantes del Magallanes",
    "Tiburones de La Guaira",
    "Tigres de Aragua",
    "Cardenales de Lara",
    "Águilas del Zulia",
    "Caribes de Anzoátegui",
    "Bravos de Margarita",
]

PHASE_LABELS: Dict[str, str] = {
    "regular": "Temporada Regular (56 JJ)",
    "round_robin": "Round Robin (Todos contra Todos)",
    "wildcard_playin": "Serie del Comodín (Wild Card)",
    "final": "Serie Final",
    "all": "Acumulado Total (Todas las Fases)",
}

ELO_PHASE_LABELS: Dict[str, str] = {
    "regular": "1. Temporada Regular",
    "round_robin": "2. Round Robin",
    "wildcard_playin": "3. Serie del Comodín",
    "final": "4. Serie Final",
}


class StandingsState(AppState):
    """Estado Reactivo para Dashboard Home y Vista Completa de Standings & ELO."""

    # ── Fases y Pestañas ────────────────────────────────────────────────────
    selected_phase: str = "regular"
    selected_phase_label: str = "Temporada Regular (56 JJ)"
    phase_keys: List[str] = ["regular", "round_robin", "wildcard_playin", "final", "all"]

    selected_elo_phase: str = "regular"
    selected_elo_phase_label: str = "1. Temporada Regular"
    elo_phase_keys: List[str] = ["regular", "round_robin", "wildcard_playin", "final"]

    active_tab: str = "oficial"  # 'oficial', 'pitagorica', 'elo', 'situacional'
    sim_mode: str = "actual"     # 'actual', 'scratch'
    is_simulating: bool = False

    # ── Datos de Sabermetría Pitagórica ─────────────────────────────────────
    pythagorean_data: List[Dict[str, Any]] = []
    leones_pythagorean: Dict[str, str] = {
        "wins_real": "0",
        "losses_real": "0",
        "xw": "0.0",
        "xl": "0.0",
        "w_diff": "+0.0",
        "pyth_pct": ".000",
        "rf_per_g": "0.00",
        "ra_per_g": "0.00",
        "diagnostico": "⚖️ En línea con lo esperado",
    }

    # ── Ratings ELO & Power Rankings ────────────────────────────────────────
    elo_ratings_data: List[Dict[str, Any]] = []
    leones_elo_stats: Dict[str, str] = {
        "rank": "1°",
        "elo": "1500.0",
        "games_played": "0",
        "diff_from_base": "+0.0",
    }

    # ── Simulaciones Monte Carlo (5,000 Iteraciones) ────────────────────────
    projections_data: List[Dict[str, Any]] = []
    position_matrix_data: List[Dict[str, Any]] = []
    leones_monte_carlo: Dict[str, str] = {
        "top4": "0.0%",
        "wc": "0.0%",
        "rr": "0.0%",
        "final": "0.0%",
        "champ": "0.0%",
    }

    # ── Predictor de Partidos H2H ───────────────────────────────────────────
    all_team_options: List[str] = ALL_LVBP_NAMES
    predictor_home_team: str = "Leones del Caracas"
    predictor_away_team: str = "Navegantes del Magallanes"
    predictor_home_logo: str = get_team_logo(695, size=96)
    predictor_away_logo: str = get_team_logo(696, size=96)
    predictor_home_elo: float = 1500.0
    predictor_away_elo: float = 1500.0
    predictor_home_prob: float = 0.55
    predictor_away_prob: float = 0.45
    predictor_home_prob_str: str = "55.0%"
    predictor_away_prob_str: str = "45.0%"
    predictor_home_prob_pct: int = 55
    predictor_away_prob_pct: int = 45
    predictor_favorite: str = "Leones del Caracas"
    predictor_favorite_prob_str: str = "55.0%"
    predictor_diff_eff_str: str = "+35.0"

    # ── Desglose Situacional & Semanas ISO ───────────────────────────────────
    leones_advanced: Dict[str, str] = {
        "home_record": "0-0",
        "away_record": "0-0",
        "night_record": "0-0",
        "day_record": "0-0",
        "one_run": "0-0",
        "remontados": "0",
        "up": "0-0",
        "terreneadas": "0",
        "starters": "0-0",
        "relievers": "0-0",
        "saves": "0",
        "oct": "0G-0P",
        "nov": "0G-0P",
        "dec": "0G-0P",
    }
    weekly_records_data: List[Dict[str, Any]] = []
    latest_weekly_record: Dict[str, Any] = {
        "semana": "Semana Actual",
        "juegos": 0,
        "w": 0,
        "l": 0,
        "pct": ".000",
        "cf": 0,
        "cp": 0,
        "dif": "0",
        "record": "0G-0P",
        "dif_color": "var(--gray-9)",
    }

    # ── Handlers de Carga e Inicialización ───────────────────────────────────
    def on_load(self):
        """Inicialización reactiva completa para vistas de Standings y Dashboard."""
        self.is_loading = True
        self.has_error = False
        self.error_message = ""
        try:
            seasons = get_available_seasons()
            if seasons:
                self.available_seasons = seasons
                self.season_options = [f"{s}-{s+1}" for s in seasons]
                if self.selected_season not in seasons:
                    self.selected_season = seasons[0]
                    self.selected_season_str = f"{seasons[0]}-{seasons[0]+1}"
            self.load_all_standings_data()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error de Carga"
            self.error_message = f"Error al inicializar datos de posiciones: {str(e)}"
        finally:
            self.is_loading = False

    def load_all_standings_data(self):
        """Carga y orquesta todas las secciones analíticas de Standings."""
        try:
            # 1. Standings Oficiales
            df_standings = self._compute_standings()
            
            # 2. Expectativa Pitagórica
            self._compute_pythagorean(df_standings)

            # 3. Ratings ELO Oficiales
            elo_dict = self._compute_elo_ratings()

            # 4. Simulaciones Monte Carlo (5,000 Iteraciones)
            self._compute_monte_carlo(df_standings, elo_dict)

            # 5. Predictor de Enfrentamiento H2H
            self._compute_matchup_prediction(elo_dict)

            # 6. Estadísticas Avanzadas Situacionales (Día/Noche)
            self._compute_advanced_situational()

            # 7. Récords por Semanas ISO
            self._compute_weekly_records()

            # 8. Juegos Recientes para el Scoreboard del Home
            self._compute_recent_games()

        except Exception as e:
            self.has_error = True
            self.error_title = "Error de Cálculo Sabermétrico"
            self.error_message = f"Error procesando estadísticas de standings: {str(e)}"

    # ── Handlers de Selección ────────────────────────────────────────────────
    def set_season(self, season_val: str):
        """Cambia la temporada y recalcula todas las estadísticas."""
        self.is_loading = True
        try:
            if "-" in season_val:
                season_int = int(season_val.split("-")[0])
                self.selected_season_str = season_val
            else:
                season_int = int(season_val)
                self.selected_season_str = f"{season_int}-{season_int+1}"
            
            self.selected_season = season_int
            self.load_all_standings_data()
        except Exception as e:
            self.set_error(f"Error cambiando a temporada {season_val}: {str(e)}")
        finally:
            self.is_loading = False

    def set_phase(self, phase_key: str):
        """Cambia la fase del torneo (Regular, Round Robin, Wild Card, Final, All)."""
        self.selected_phase = phase_key
        self.selected_phase_label = PHASE_LABELS.get(phase_key, phase_key)
        df_standings = self._compute_standings()
        self._compute_pythagorean(df_standings)
        self._compute_weekly_records()

    def set_elo_phase(self, elo_phase_key: str):
        """Cambia la fase para la consulta de ratings ELO."""
        self.selected_elo_phase = elo_phase_key
        self.selected_elo_phase_label = ELO_PHASE_LABELS.get(elo_phase_key, elo_phase_key)
        self._compute_elo_ratings()

    def set_active_tab(self, tab: str):
        """Cambia la pestaña activa de la vista /standings."""
        self.active_tab = tab

    def set_sim_mode(self, mode: str):
        """Cambia el modo de simulación Monte Carlo ('actual' vs 'scratch')."""
        self.sim_mode = mode
        self.recalc_simulations()

    def recalc_simulations(self):
        """Re-ejecuta las 5,000 simulaciones Monte Carlo."""
        self.is_simulating = True
        try:
            df_standings = get_standings(self.selected_season, phase="regular")
            elo_dict = self._get_current_elo_dict()
            self._compute_monte_carlo(df_standings, elo_dict)
        except Exception as e:
            self.set_error(f"Error re-ejecutando simulaciones Monte Carlo: {str(e)}")
        finally:
            self.is_simulating = False

    def set_predictor_home(self, team_name: str):
        """Actualiza el equipo local del simulador H2H."""
        self.predictor_home_team = team_name
        elo_dict = self._get_current_elo_dict()
        self._compute_matchup_prediction(elo_dict)

    def set_predictor_away(self, team_name: str):
        """Actualiza el equipo visitante del simulador H2H."""
        self.predictor_away_team = team_name
        elo_dict = self._get_current_elo_dict()
        self._compute_matchup_prediction(elo_dict)

    # ── Métodos Internos de Cálculo y Transformación ────────────────────────
    def _compute_standings(self) -> pd.DataFrame:
        """Calcula y formatea la tabla oficial de posiciones."""
        df = get_standings(self.selected_season, phase=self.selected_phase)
        records = []
        if df is not None and not df.empty:
            df = df.sort_values("pct", ascending=False).reset_index(drop=True)
            for idx, row in df.iterrows():
                t_id = int(row.get("team_id", 0))
                team_name = str(row.get("team_name", "Equipo"))
                t_logo = get_team_logo(t_id if t_id > 0 else team_name, size=72)
                is_leones = (t_id == 695 or "Leones" in team_name)
                streak_str = str(row.get("streak", "-"))
                diff_val = int(row.get("run_diff", row.get("runs_for", 0) - row.get("runs_against", 0)))
                diff_str = f"{diff_val:+d}" if diff_val != 0 else "0"
                pct_float = float(row.get("pct", 0.0))
                pct_str = f".{int(pct_float * 1000):03d}" if pct_float < 1.0 else "1.000"
                gb_val = row.get("games_back", 0.0)
                gb_str = "-" if gb_val == 0.0 else f"{gb_val:.1f}"

                streak_color = (
                    "green" if "G" in streak_str or "W" in streak_str
                    else ("red" if "P" in streak_str or "L" in streak_str else "gray")
                )
                diff_color = (
                    "var(--green-9)" if diff_val > 0
                    else ("var(--red-9)" if diff_val < 0 else "var(--gray-9)")
                )

                records.append({
                    "pos": idx + 1,
                    "pos_str": f"{idx + 1}°",
                    "team_id": t_id,
                    "team_name": team_name,
                    "team_abbr": get_team_abbr(t_id if t_id > 0 else team_name),
                    "logo": t_logo,
                    "games": int(row.get("wins", 0)) + int(row.get("losses", 0)),
                    "wins": int(row.get("wins", 0)),
                    "losses": int(row.get("losses", 0)),
                    "pct": pct_str,
                    "pct_float": pct_float,
                    "gb": gb_str,
                    "streak": streak_str,
                    "streak_color": streak_color,
                    "l10": str(row.get("last_10", "-")),
                    "home": str(row.get("home_record", "-")),
                    "away": str(row.get("away_record", "-")),
                    "rf": int(row.get("runs_for", 0)),
                    "ra": int(row.get("runs_against", 0)),
                    "diff": diff_str,
                    "diff_val": diff_val,
                    "diff_color": diff_color,
                    "is_leones": is_leones,
                    "row_bg": "rgba(253, 184, 39, 0.12)" if is_leones else "transparent",
                    "row_border": "3px solid #FDB827" if is_leones else "none",
                    "text_color": "#FDB827" if is_leones else "#FFFFFF",
                })

            self.standings_data = records

            # Actualizar KPIs de Leones del Caracas
            leones_row = next((r for r in records if r["is_leones"]), None)
            if leones_row:
                self.leones_kpis = {
                    "posicion": leones_row["pos_str"],
                    "record": f"{leones_row['wins']}-{leones_row['losses']}",
                    "pct": leones_row["pct"],
                    "streak": leones_row["streak"],
                    "l10": leones_row["l10"],
                    "run_diff": leones_row["diff"],
                    "rf": str(leones_row["rf"]),
                    "ra": str(leones_row["ra"]),
                    "gb": leones_row["gb"],
                }
        else:
            self.standings_data = []

        return df if df is not None else pd.DataFrame()

    def _compute_pythagorean(self, df: pd.DataFrame):
        """Calcula la expectativa pitagórica de victorias (Bill James / Davenport 1.83)."""
        pyth_records = []
        if df is not None and not df.empty and "runs_for" in df.columns:
            for _, row in df.iterrows():
                t_id = int(row.get("team_id", 0))
                team_name = str(row.get("team_name", "Equipo"))
                rf = float(row.get("runs_for", 0))
                ra = float(row.get("runs_against", 0))
                w = float(row.get("wins", 0))
                l = float(row.get("losses", 0))
                tot_games = w + l

                denom = (rf ** 1.83) + (ra ** 1.83)
                pyth_pct = (rf ** 1.83) / denom if denom > 0 else 0.500
                xw = round(pyth_pct * tot_games, 1)
                xl = round(tot_games - xw, 1)
                w_diff = round(w - xw, 1)
                diff_str = f"{w_diff:+.1f}"

                rf_per_g = (rf / tot_games) if tot_games > 0 else 0.0
                ra_per_g = (ra / tot_games) if tot_games > 0 else 0.0

                if w_diff >= 1.5:
                    diagnostico = "🔥 Sobre-rendimiento (Clutch)"
                    diag_color = "var(--green-9)"
                elif w_diff <= -1.5:
                    diagnostico = "❄️ Sub-rendimiento (Mala Suerte)"
                    diag_color = "var(--red-9)"
                else:
                    diagnostico = "⚖️ En línea con lo esperado"
                    diag_color = "var(--gray-9)"

                is_leones = (t_id == 695 or "Leones" in team_name)

                pyth_records.append({
                    "team_id": t_id,
                    "team_name": team_name,
                    "team_abbr": get_team_abbr(t_id if t_id > 0 else team_name),
                    "logo": get_team_logo(t_id if t_id > 0 else team_name, size=72),
                    "wins_real": int(w),
                    "losses_real": int(l),
                    "rf": int(rf),
                    "ra": int(ra),
                    "run_diff": f"{int(rf - ra):+d}",
                    "pct_real": f".{int((w / tot_games if tot_games > 0 else 0) * 1000):03d}",
                    "pyth_pct": f".{int(pyth_pct * 1000):03d}",
                    "xw": f"{xw:.1f}",
                    "xl": f"{xl:.1f}",
                    "w_diff": diff_str,
                    "w_diff_val": w_diff,
                    "diagnostico": diagnostico,
                    "diag_color": diag_color,
                    "is_leones": is_leones,
                    "row_bg": "rgba(253, 184, 39, 0.12)" if is_leones else "transparent",
                    "text_color": "#FDB827" if is_leones else "#FFFFFF",
                })

            self.pythagorean_data = pyth_records

            # KPIs Pitagóricos de Leones
            leones_p = next((r for r in pyth_records if r["is_leones"]), None)
            if leones_p:
                tot_leo = leones_p["wins_real"] + leones_p["losses_real"]
                self.leones_pythagorean = {
                    "wins_real": str(leones_p["wins_real"]),
                    "losses_real": str(leones_p["losses_real"]),
                    "xw": leones_p["xw"],
                    "xl": leones_p["xl"],
                    "w_diff": leones_p["w_diff"],
                    "pyth_pct": leones_p["pyth_pct"],
                    "rf_per_g": f"{(leones_p['rf'] / tot_leo):.2f}" if tot_leo > 0 else "0.00",
                    "ra_per_g": f"{(leones_p['ra'] / tot_leo):.2f}" if tot_leo > 0 else "0.00",
                    "diagnostico": leones_p["diagnostico"],
                }
        else:
            self.pythagorean_data = []

    def _get_current_elo_dict(self) -> Dict[int, float]:
        """Obtiene el diccionario {team_id: elo} actual desde Supabase o fallback."""
        elo_dict = {tid: float(BASE_ELO) for tid in LVBP_TEAMS.keys()}
        try:
            supabase = init_supabase()
            res = supabase.table("elo_ratings") \
                .select("team_id, elo") \
                .eq("season", self.selected_season) \
                .eq("phase", "regular") \
                .execute()
            if res.data:
                for r in res.data:
                    tid = int(r.get("team_id", 0))
                    if tid in elo_dict:
                        elo_dict[tid] = float(r.get("elo", BASE_ELO))
        except Exception:
            # Fallback a partir de standings
            for r in self.standings_data:
                tid = r.get("team_id", 0)
                pct_val = r.get("pct_float", 0.500)
                if tid in elo_dict:
                    elo_dict[tid] = float(BASE_ELO + (pct_val - 0.500) * 300.0)
        return elo_dict

    def _compute_elo_ratings(self) -> Dict[int, float]:
        """Consulta y estructura los ratings ELO oficiales de la temporada y fase."""
        elo_dict = self._get_current_elo_dict()
        elo_records = []
        try:
            supabase = init_supabase()
            res = supabase.table("elo_ratings") \
                .select("team_id, elo, games_played") \
                .eq("season", self.selected_season) \
                .eq("phase", self.selected_elo_phase) \
                .order("elo", desc=True) \
                .execute()
            
            raw_data = res.data if res.data else []
            if not raw_data:
                # Generar desde elo_dict
                raw_data = [{"team_id": tid, "elo": elo_dict.get(tid, BASE_ELO), "games_played": 56} for tid in LVBP_TEAMS.keys()]
                raw_data = sorted(raw_data, key=lambda x: x["elo"], reverse=True)

            for rank_idx, r in enumerate(raw_data):
                t_id = int(r.get("team_id", 0))
                team_name = get_team_name(t_id)
                elo_val = float(r.get("elo", BASE_ELO))
                elo_dict[t_id] = elo_val
                diff_val = elo_val - BASE_ELO
                is_leones = (t_id == 695 or "Leones" in team_name)

                elo_records.append({
                    "rank": rank_idx + 1,
                    "rank_str": f"{rank_idx + 1}°",
                    "team_id": t_id,
                    "team_name": team_name,
                    "team_abbr": get_team_abbr(t_id),
                    "logo": get_team_logo(t_id, size=72),
                    "elo": elo_val,
                    "elo_fmt": f"{elo_val:.1f}",
                    "games_played": int(r.get("games_played", 0)),
                    "diff_from_base": f"{diff_val:+.1f}",
                    "diff_color": "var(--green-9)" if diff_val > 0 else ("var(--red-9)" if diff_val < 0 else "var(--gray-9)"),
                    "is_leones": is_leones,
                    "row_bg": "rgba(253, 184, 39, 0.12)" if is_leones else "transparent",
                    "text_color": "#FDB827" if is_leones else "#FFFFFF",
                })

            self.elo_ratings_data = elo_records

            # KPIs ELO de Leones
            leones_elo = next((r for r in elo_records if r["is_leones"]), None)
            if leones_elo:
                self.leones_elo_stats = {
                    "rank": leones_elo["rank_str"],
                    "elo": leones_elo["elo_fmt"],
                    "games_played": str(leones_elo["games_played"]),
                    "diff_from_base": leones_elo["diff_from_base"],
                }
        except Exception:
            self.elo_ratings_data = []

        return elo_dict

    def _compute_monte_carlo(self, df_standings: pd.DataFrame, elo_dict: Dict[int, float]):
        """Ejecuta 5,000 simulaciones Monte Carlo para proyectar postemporada."""
        try:
            res_mc = simulate_monte_carlo_projections(
                standings_df=df_standings if df_standings is not None else pd.DataFrame(),
                elo_dict=elo_dict,
                n_simulations=5000,
                simulate_from_scratch=(self.sim_mode == "scratch"),
            )

            # 1. Proyecciones de Avance
            df_proj = res_mc.get("projections", pd.DataFrame())
            proj_records = []
            if not df_proj.empty:
                for _, r in df_proj.iterrows():
                    tid = int(r.get("team_id", 0))
                    t_name = str(r.get("team_name", "Equipo"))
                    is_leones = (tid == 695 or "Leones" in t_name)

                    proj_records.append({
                        "team_id": tid,
                        "team_name": t_name,
                        "team_abbr": get_team_abbr(tid),
                        "logo": get_team_logo(tid, size=72),
                        "elo_fmt": f"{float(r.get('elo', BASE_ELO)):.1f}",
                        "top4_prob": f"{float(r.get('top4_prob', 0.0)):.1%}",
                        "wc_prob": f"{float(r.get('wc_prob', 0.0)):.1%}",
                        "rr_prob": f"{float(r.get('rr_prob', 0.0)):.1%}",
                        "final_prob": f"{float(r.get('final_prob', 0.0)):.1%}",
                        "champ_prob": f"{float(r.get('champ_prob', 0.0)):.1%}",
                        "champ_prob_pct": int(float(r.get('champ_prob', 0.0)) * 100),
                        "is_leones": is_leones,
                        "row_bg": "rgba(253, 184, 39, 0.12)" if is_leones else "transparent",
                        "text_color": "#FDB827" if is_leones else "#FFFFFF",
                    })
            self.projections_data = proj_records

            # KPIs Monte Carlo de Leones
            leones_mc = next((r for r in proj_records if r["is_leones"]), None)
            if leones_mc:
                self.leones_monte_carlo = {
                    "top4": leones_mc["top4_prob"],
                    "wc": leones_mc["wc_prob"],
                    "rr": leones_mc["rr_prob"],
                    "final": leones_mc["final_prob"],
                    "champ": leones_mc["champ_prob"],
                }

            # 2. Matriz de Posición Final (1° al 8°)
            df_mat = res_mc.get("position_matrix", pd.DataFrame())
            mat_records = []
            if not df_mat.empty:
                for _, r in df_mat.iterrows():
                    tid = int(r.get("team_id", 0))
                    t_name = str(r.get("team_name", "Equipo"))
                    is_leones = (tid == 695 or "Leones" in t_name)

                    mat_records.append({
                        "team_id": tid,
                        "team_name": t_name,
                        "team_abbr": get_team_abbr(tid),
                        "logo": get_team_logo(tid, size=72),
                        "elo_fmt": f"{float(r.get('elo', BASE_ELO)):.1f}",
                        "p1": f"{float(r.get('1°', 0.0)):.1%}",
                        "p2": f"{float(r.get('2°', 0.0)):.1%}",
                        "p3": f"{float(r.get('3°', 0.0)):.1%}",
                        "p4": f"{float(r.get('4°', 0.0)):.1%}",
                        "p5": f"{float(r.get('5°', 0.0)):.1%}",
                        "p6": f"{float(r.get('6°', 0.0)):.1%}",
                        "p7": f"{float(r.get('7°', 0.0)):.1%}",
                        "p8": f"{float(r.get('8°', 0.0)):.1%}",
                        "is_leones": is_leones,
                        "row_bg": "rgba(253, 184, 39, 0.12)" if is_leones else "transparent",
                        "text_color": "#FDB827" if is_leones else "#FFFFFF",
                    })
            self.position_matrix_data = mat_records

        except Exception as e:
            self.projections_data = []
            self.position_matrix_data = []

    def _compute_matchup_prediction(self, elo_dict: Dict[int, float]):
        """Calcula probabilidades de victoria para el predictor H2H."""
        h_id = resolve_team_id(self.predictor_home_team) or 695
        a_id = resolve_team_id(self.predictor_away_team) or 696

        h_elo = elo_dict.get(h_id, BASE_ELO)
        a_elo = elo_dict.get(a_id, BASE_ELO)

        p_home, p_away = calculate_matchup_win_prob(h_elo, a_elo, HOME_ADVANTAGE)
        diff_eff = (h_elo + HOME_ADVANTAGE) - a_elo

        fav_name = self.predictor_home_team if p_home >= 0.5 else self.predictor_away_team
        fav_prob = max(p_home, p_away)

        self.predictor_home_logo = get_team_logo(h_id, size=96)
        self.predictor_away_logo = get_team_logo(a_id, size=96)
        self.predictor_home_elo = h_elo
        self.predictor_away_elo = a_elo
        self.predictor_home_prob = p_home
        self.predictor_away_prob = p_away
        self.predictor_home_prob_str = f"{p_home:.1%}"
        self.predictor_away_prob_str = f"{p_away:.1%}"
        self.predictor_home_prob_pct = int(p_home * 100)
        self.predictor_away_prob_pct = int(p_away * 100)
        self.predictor_favorite = fav_name
        self.predictor_favorite_prob_str = f"{fav_prob:.1%}"
        self.predictor_diff_eff_str = f"{diff_eff:+.1f} pts"

    def _compute_advanced_situational(self):
        """Consulta estadísticas situacionales avanzadas (Día vs Noche, 1 carrera, etc.)."""
        adv = get_leones_advanced_stats(self.selected_season)
        if adv:
            # Calcular día si no viene explícito
            day_rec = adv.get("day_record")
            if not day_rec or day_rec == "-":
                try:
                    tot_w = int(adv.get("record", "0-0").split("-")[0])
                    tot_l = int(adv.get("record", "0-0").split("-")[1])
                    n_w = int(adv.get("night_record", "0-0").split("-")[0])
                    n_l = int(adv.get("night_record", "0-0").split("-")[1])
                    day_rec = f"{tot_w - n_w}-{tot_l - n_l}"
                except Exception:
                    day_rec = "0-0"

            self.leones_advanced = {
                "home_record": str(adv.get("home_record", "-")),
                "away_record": str(adv.get("away_record", "-")),
                "night_record": str(adv.get("night_record", "-")),
                "day_record": str(day_rec),
                "one_run": str(adv.get("one_run", "-")),
                "remontados": str(adv.get("remontados", "0")),
                "up": str(adv.get("up", "-")),
                "terreneadas": str(adv.get("terreneadas", "0")),
                "starters": str(adv.get("starters", "-")),
                "relievers": str(adv.get("relievers", "-")),
                "saves": str(adv.get("saves", "0")),
                "oct": str(adv.get("oct", "-")),
                "nov": str(adv.get("nov", "-")),
                "dec": str(adv.get("dec", "-")),
            }
        else:
            self.leones_advanced = {
                "home_record": "-",
                "away_record": "-",
                "night_record": "-",
                "day_record": "-",
                "one_run": "-",
                "remontados": "0",
                "up": "-",
                "terreneadas": "0",
                "starters": "-",
                "relievers": "-",
                "saves": "0",
                "oct": "-",
                "nov": "-",
                "dec": "-",
            }

    def _compute_weekly_records(self):
        """Consulta y formatea el rendimiento por semanas de campeonato ISO."""
        df_w = get_weekly_records(self.selected_season, team_id=695, phase=self.selected_phase)
        records = []
        if df_w is not None and not df_w.empty:
            for _, r in df_w.iterrows():
                dif_str = str(r.get("dif", r.get("DIF", "0")))
                dif_val = int(dif_str) if dif_str.replace("+", "").replace("-", "").isdigit() else 0
                dif_color = (
                    "var(--green-9)" if dif_val > 0
                    else ("var(--red-9)" if dif_val < 0 else "var(--gray-9)")
                )

                records.append({
                    "semana": str(r.get("semana", r.get("Semana", ""))),
                    "juegos": int(r.get("juegos", r.get("Juegos", 0))),
                    "w": int(r.get("w", r.get("G", 0))),
                    "l": int(r.get("l", r.get("P", 0))),
                    "pct": str(r.get("pct", r.get("PCT", ".000"))),
                    "cf": int(r.get("cf", r.get("CF", 0))),
                    "cp": int(r.get("cp", r.get("CP", 0))),
                    "dif": dif_str,
                    "dif_color": dif_color,
                    "record": str(r.get("record", r.get("Récord", "0G-0P"))),
                })
            self.weekly_records_data = records
            if records:
                self.latest_weekly_record = records[-1]
        else:
            self.weekly_records_data = []
            self.latest_weekly_record = {
                "semana": "Sin datos",
                "juegos": 0,
                "w": 0,
                "l": 0,
                "pct": ".000",
                "cf": 0,
                "cp": 0,
                "dif": "0",
                "record": "0G-0P",
                "dif_color": "var(--gray-9)",
            }

    def _compute_recent_games(self):
        """Consulta los juegos recientes para el Dashboard ejecutivo."""
        recent = get_recent_games(team_id=695, limit=5, season=self.selected_season)
        g_records = []
        if recent is not None and not recent.empty:
            for _, g in recent.iterrows():
                h_name = str(g.get("home_team", "Home"))
                a_name = str(g.get("away_team", "Away"))
                h_id = g.get("home_team_id", 0)
                a_id = g.get("away_team_id", 0)
                h_score = int(g.get("home_score", 0))
                a_score = int(g.get("away_score", 0))
                is_leones_home = ("Leones" in h_name or h_id == 695)
                leones_won = (h_score > a_score) if is_leones_home else (a_score > h_score)

                g_records.append({
                    "date": str(g.get("game_date", ""))[:10],
                    "home_name": h_name,
                    "away_name": a_name,
                    "home_logo": get_team_logo(h_id if h_id else h_name, size=72),
                    "away_logo": get_team_logo(a_id if a_id else a_name, size=72),
                    "home_score": h_score,
                    "away_score": a_score,
                    "score_str": f"{a_score} - {h_score}",
                    "result_badge": "Victoria" if leones_won else "Derrota",
                    "result_color": "green" if leones_won else "red",
                    "is_win": leones_won,
                })
            self.recent_games_data = g_records
            if g_records:
                self.last_game_data = g_records[0]
        else:
            self.recent_games_data = []
            self.last_game_data = {
                "date": "-",
                "home_name": "Leones del Caracas",
                "away_name": "Rival",
                "home_logo": get_team_logo(695, size=72),
                "away_logo": get_team_logo(696, size=72),
                "home_score": 0,
                "away_score": 0,
                "score_str": "0 - 0",
                "result_badge": "Sin juegos",
                "result_color": "gray",
                "is_win": True,
            }
