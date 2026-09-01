# republicaraquistapp/state/base_state.py
"""
base_state.py
-------------
Estado reactivo centralizado de República Caraquista en Reflex.
Maneja la temporada seleccionada, estado de carga, errores, navegación de rutas,
y la carga de standings y juegos recientes de los Leones del Caracas.
"""

from typing import List, Dict, Any, Optional
import reflex as rx
import pandas as pd

from core.supabase_client import (
    get_available_seasons,
    get_current_season,
    get_standings,
    get_recent_games,
    get_leones_advanced_stats,
)
from core.teams import get_team_logo, get_team_name, get_team_abbr, LVBP_TEAMS


def safe_int(val, default: int = 0) -> int:
    if val is None or pd.isna(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def safe_float(val, default: float = 0.0) -> float:
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_str(val, default: str = "-") -> str:
    if val is None:
        return default
    return str(val)


class AppState(rx.State):
    """Estado global y reactivo principal de República Caraquista."""

    def __setattr__(self, name: str, value: Any):
        if getattr(self, "parent_state", None) is None:
            object.__setattr__(self, name, value)
            if hasattr(self, "dirty_vars") and self.dirty_vars is not None:
                self.dirty_vars.add(name)
            return
        super().__setattr__(name, value)

    # ── Rutas y Navegación ──────────────────────────────────────────────────
    current_route: str = "/"
    drawer_open: bool = False

    # ── Temporada ───────────────────────────────────────────────────────────
    selected_season: int = 2025
    selected_season_str: str = "2025-2026"
    available_seasons: List[int] = [2025, 2024, 2023, 2022, 2021]
    season_options: List[str] = [
        "2025-2026",
        "2024-2025",
        "2023-2024",
        "2022-2023",
        "2021-2022",
    ]

    # ── Estados de Carga y Errores ──────────────────────────────────────────
    is_loading: bool = False
    loading_text: str = "Cargando datos sabermétricos..."
    has_error: bool = False
    error_title: str = ""
    error_message: str = ""

    # ── Datos de la Temporada ───────────────────────────────────────────────
    standings_data: List[Dict[str, Any]] = []
    recent_games_data: List[Dict[str, Any]] = []
    last_game_data: Dict[str, Any] = {
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
    leones_kpis: Dict[str, str] = {
        "posicion": "1°",
        "record": "0-0",
        "pct": ".000",
        "streak": "N/A",
        "l10": "0-0",
        "run_diff": "+0",
    }

    # ── Handlers de Carga e Inicialización ───────────────────────────────────
    def on_load(self):
        """Inicialización de la aplicación y carga de datos iniciales."""
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
            self.load_season_data()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error de Inicialización"
            self.error_message = f"No se pudieron inicializar los datos: {str(e)}"
        finally:
            self.is_loading = False

    # ── Handlers de Navegación y Rutas ──────────────────────────────────────
    def set_route(self, route: str):
        """Actualiza la ruta actual y cierra el menú lateral si está abierto."""
        self.current_route = route
        self.drawer_open = False

    def toggle_drawer(self):
        """Alterna la visibilidad del drawer móvil."""
        self.drawer_open = not self.drawer_open

    def set_drawer_open(self, is_open: bool):
        """Ajusta explícitamente el estado del drawer móvil."""
        self.drawer_open = is_open

    def close_drawer(self):
        """Cierra el drawer móvil."""
        self.drawer_open = False

    # ── Handlers de Temporada ────────────────────────────────────────────────
    def set_season(self, season_val: str):
        """Cambia la temporada seleccionada y recarga los datos correspondientes."""
        self.is_loading = True
        self.has_error = False
        self.error_message = ""
        try:
            if "-" in season_val:
                season_int = int(season_val.split("-")[0])
                self.selected_season_str = season_val
            else:
                season_int = int(season_val)
                self.selected_season_str = f"{season_int}-{season_int+1}"
            
            self.selected_season = season_int
            self.load_season_data()
        except Exception as e:
            self.has_error = True
            self.error_title = "Error al Cambiar Temporada"
            self.error_message = f"Error al procesar la temporada {season_val}: {str(e)}"
        finally:
            self.is_loading = False

    # ── Handlers de Errores y Loading ───────────────────────────────────────
    def set_error(self, message: str, title: str = "Error al Cargar Datos"):
        """Establece un estado de error visible."""
        self.has_error = True
        self.error_title = title
        self.error_message = message

    def clear_error(self):
        """Limpia el estado de error."""
        self.has_error = False
        self.error_title = ""
        self.error_message = ""

    def set_loading(self, is_loading: bool, text: str = "Cargando datos sabermétricos..."):
        """Ajusta el indicador de carga."""
        self.is_loading = is_loading
        self.loading_text = text

    # ── Carga de Datos de Standings y Juegos ──────────────────────────────────
    def load_season_data(self):
        """Consulta y actualiza la tabla de posiciones y los juegos recientes."""
        try:
            # 1. Tabla de Posiciones
            df_standings = get_standings(self.selected_season, phase="regular")
            if df_standings is not None and not df_standings.empty:
                records = []
                for _, row in df_standings.iterrows():
                    t_id = safe_int(row.get("team_id", 0))
                    team_name = safe_str(row.get("team_name", "Equipo"))
                    t_logo = get_team_logo(t_id if t_id > 0 else team_name, size=72)
                    is_leones = (t_id == 695 or "Leones" in team_name)
                    streak_str = safe_str(row.get("streak", "-"))
                    diff_val = safe_int(row.get("run_differential", 0))
                    diff_str = f"{diff_val:+d}"

                    streak_color = (
                        "green" if "G" in streak_str
                        else ("red" if "P" in streak_str else "gray")
                    )
                    diff_color = (
                        "var(--green-9)" if diff_val > 0
                        else ("var(--red-9)" if diff_val < 0 else "var(--gray-9)")
                    )

                    pct_val = safe_float(row.get("win_pct", 0.0))
                    pct_str = f"{pct_val:.3f}".replace("0.", ".")

                    records.append({
                        "pos": safe_int(row.get("pos", 1)),
                        "team_id": t_id,
                        "team_name": team_name,
                        "team_abbr": get_team_abbr(t_id if t_id > 0 else team_name),
                        "logo": t_logo,
                        "games": safe_int(row.get("games_played", 0)),
                        "wins": safe_int(row.get("wins", 0)),
                        "losses": safe_int(row.get("losses", 0)),
                        "pct": pct_str,
                        "gb": safe_str(row.get("games_behind", "-")),
                        "streak": streak_str,
                        "streak_color": streak_color,
                        "l10": safe_str(row.get("last_10", "-")),
                        "home": safe_str(row.get("home_record", "-")),
                        "away": safe_str(row.get("away_record", "-")),
                        "rs": safe_int(row.get("runs_scored", 0)),
                        "ra": safe_int(row.get("runs_against", 0)),
                        "diff": diff_str,
                        "diff_color": diff_color,
                        "is_leones": is_leones,
                        "row_bg": "rgba(253, 184, 39, 0.08)" if is_leones else "transparent",
                        "row_border": "3px solid #FDB827" if is_leones else "none",
                        "text_color": "#FDB827" if is_leones else "#FFFFFF",
                    })
                self.standings_data = records

                # Extraer KPIs de Leones del Caracas (ID 695)
                leones_row = next((r for r in records if r["is_leones"]), None)
                if leones_row:
                    self.leones_kpis = {
                        "posicion": f"{leones_row['pos']}°",
                        "record": f"{leones_row['wins']}-{leones_row['losses']}",
                        "pct": leones_row["pct"],
                        "streak": leones_row["streak"],
                        "l10": leones_row["l10"],
                        "run_diff": leones_row["diff"],
                    }
            else:
                self.standings_data = []

            # 2. Juegos Recientes
            recent = get_recent_games(team_id=695, limit=5, season=self.selected_season)
            if recent is not None and not recent.empty:
                g_records = []
                for _, g in recent.iterrows():
                    h_name = safe_str(g.get("home_team", "Home"))
                    a_name = safe_str(g.get("away_team", "Away"))
                    h_id = safe_int(g.get("home_team_id", 0))
                    a_id = safe_int(g.get("away_team_id", 0))
                    h_score = safe_int(g.get("home_score", 0))
                    a_score = safe_int(g.get("away_score", 0))
                    is_leones_home = ("Leones" in h_name or h_id == 695)
                    leones_won = (h_score > a_score) if is_leones_home else (a_score > h_score)

                    g_records.append({
                        "date": safe_str(g.get("game_date", "")),
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
        except Exception as e:
            self.has_error = True
            self.error_title = "Error al Cargar Datos de Temporada"
            self.error_message = f"Ocurrió un error al consultar Supabase: {str(e)}"


# Alias para compatibilidad con sub-estados
BaseState = AppState
