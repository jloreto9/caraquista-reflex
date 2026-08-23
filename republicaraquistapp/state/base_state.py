# republicaraquistapp/state/base_state.py
import reflex as rx
import pandas as pd
from core.supabase_client import (
    get_available_seasons,
    get_current_season,
    get_standings,
    get_recent_games,
    get_leones_advanced_stats
)
from core.teams import get_team_logo, get_team_name, get_team_abbr, LVBP_TEAMS

class AppState(rx.State):
    """Estado global y reactivo de República Caraquista."""
    
    # Temporada
    selected_season: int = 2025
    available_seasons: list[int] = [2025]
    
    # Datos cargados
    standings_data: list[dict] = []
    recent_games_data: list[dict] = []
    last_game_data: dict = {}
    leones_kpis: dict = {
        "posicion": "1°",
        "record": "0-0",
        "pct": ".000",
        "streak": "N/A",
        "l10": "0-0",
        "run_diff": "+0"
    }
    
    is_loading: bool = False
    
    def on_load(self):
        """Carga inicial de datos al abrir la página."""
        self.is_loading = True
        try:
            seasons = get_available_seasons()
            if seasons:
                self.available_seasons = seasons
                self.selected_season = seasons[0]
            self.load_season_data()
        finally:
            self.is_loading = False
            
    def set_season(self, season_val: str):
        """Cambia la temporada seleccionada."""
        try:
            season_int = int(season_val.split("-")[0])
            self.selected_season = season_int
            self.load_season_data()
        except Exception:
            pass

    def load_season_data(self):
        """Consulta y actualiza los standings y juegos recientes."""
        # 1. Standings
        df_standings = get_standings(self.selected_season, phase='regular')
        if not df_standings.empty:
            records = []
            for _, row in df_standings.iterrows():
                t_id = int(row.get('team_id', 0))
                team_name = str(row.get('team_name', 'Equipo'))
                t_logo = get_team_logo(t_id if t_id > 0 else team_name, size=72)
                is_leones = (t_id == 695 or "Leones" in team_name)
                streak_str = str(row.get('streak', '-'))
                diff_val = int(row.get('run_differential', 0))
                diff_str = f"{diff_val:+d}"
                
                streak_color = "green" if "G" in streak_str else ("red" if "P" in streak_str else "gray")
                diff_color = "var(--green-9)" if diff_val > 0 else ("var(--red-9)" if diff_val < 0 else "var(--gray-9)")
                
                records.append({
                    "pos": int(row.get('pos', 1)),
                    "team_id": t_id,
                    "team_name": team_name,
                    "team_abbr": get_team_abbr(t_id if t_id > 0 else team_name),
                    "logo": t_logo,
                    "games": int(row.get('games_played', 0)),
                    "wins": int(row.get('wins', 0)),
                    "losses": int(row.get('losses', 0)),
                    "pct": f"{float(row.get('win_pct', 0.0)):.3f}".replace("0.", "."),
                    "gb": str(row.get('games_behind', '-')),
                    "streak": streak_str,
                    "streak_color": streak_color,
                    "l10": str(row.get('last_10', '-')),
                    "home": str(row.get('home_record', '-')),
                    "away": str(row.get('away_record', '-')),
                    "rs": int(row.get('runs_scored', 0)),
                    "ra": int(row.get('runs_against', 0)),
                    "diff": diff_str,
                    "diff_color": diff_color,
                    "is_leones": is_leones,
                    "row_bg": "rgba(253, 184, 39, 0.08)" if is_leones else "transparent",
                    "row_border": "3px solid #FDB827" if is_leones else "none",
                    "text_color": "#FDB827" if is_leones else "#FFFFFF"
                })
            self.standings_data = records
            
            # Extraer KPIs de Leones (ID 695)
            leones_row = next((r for r in records if r["is_leones"]), None)
            if leones_row:
                self.leones_kpis = {
                    "posicion": f"{leones_row['pos']}°",
                    "record": f"{leones_row['wins']}-{leones_row['losses']}",
                    "pct": leones_row['pct'],
                    "streak": leones_row['streak'],
                    "l10": leones_row['l10'],
                    "run_diff": leones_row['diff']
                }
        else:
            self.standings_data = []

        # 2. Juegos Recientes
        recent = get_recent_games(team_id=695, limit=5, season=self.selected_season)
        if not recent.empty:
            g_records = []
            for _, g in recent.iterrows():
                h_name = str(g.get('home_team', 'Home'))
                a_name = str(g.get('away_team', 'Away'))
                h_id = g.get('home_team_id', 0)
                a_id = g.get('away_team_id', 0)
                h_score = int(g.get('home_score', 0))
                a_score = int(g.get('away_score', 0))
                is_leones_home = ("Leones" in h_name or h_id == 695)
                leones_won = (h_score > a_score) if is_leones_home else (a_score > h_score)
                
                g_records.append({
                    "date": str(g.get('game_date', '')),
                    "home_name": h_name,
                    "away_name": a_name,
                    "home_logo": get_team_logo(h_id if h_id else h_name, size=72),
                    "away_logo": get_team_logo(a_id if a_id else a_name, size=72),
                    "home_score": h_score,
                    "away_score": a_score,
                    "score_str": f"{a_score} - {h_score}",
                    "result_badge": "Victoria" if leones_won else "Derrota",
                    "result_color": "green" if leones_won else "red",
                    "is_win": leones_won
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
                "is_win": True
            }
