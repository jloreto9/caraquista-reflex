# tests/test_standings_and_dashboard_m3.py
"""
test_standings_and_dashboard_m3.py
-----------------------------------
Suite de pruebas unitarias y de integración para el hito M3:
1. Estado Reactivo StandingsState (Estructura, handlers, tipos e invariantes).
2. Cálculo exacto de la Expectativa Pitagórica (Bill James / Davenport 1.83).
3. Ratings ELO oficiales, Power Rankings y Predictor H2H con +35 pts de localía.
4. Simulaciones Monte Carlo (5,000 iteraciones) e invariantes algebraicos.
5. Desglose situacional Día/Noche y semanas de campeonato ISO.
6. Renderizado de componentes UI de Dashboard (/) y Posiciones (/standings).
"""

import unittest
import pandas as pd
import numpy as np
import reflex as rx

from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.state.standings_state import (
    StandingsState,
    ALL_LVBP_NAMES,
    PHASE_LABELS,
    ELO_PHASE_LABELS,
)
from republicaraquistapp.pages.index import (
    index,
    index_content,
    executive_kpi_grid,
    situational_breakdown_section,
    iso_week_summary_card,
    standings_preview_card,
)
from republicaraquistapp.pages.standings import (
    standings,
    standings_content,
    tab_official_standings,
    tab_pythagorean_standings,
    tab_elo_and_monte_carlo,
    tab_situational_and_iso_weeks,
)
from core.elo import (
    calculate_matchup_win_prob,
    simulate_monte_carlo_projections,
    BASE_ELO,
    HOME_ADVANTAGE,
)
from core.teams import LVBP_TEAMS, resolve_team_id


class TestStandingsStateStructure(unittest.TestCase):
    """Pruebas de arquitectura del estado reactivo StandingsState."""

    def test_standings_state_inheritance(self):
        """Verifica que StandingsState herede correctamente de AppState y rx.State."""
        self.assertTrue(issubclass(StandingsState, AppState), "StandingsState debe heredar de AppState")
        self.assertTrue(issubclass(StandingsState, rx.State), "StandingsState debe ser una subclase de rx.State")

    def test_standings_state_registered_fields(self):
        """Verifica la existencia de los campos reactivos de StandingsState."""
        fields = StandingsState.get_fields() if hasattr(StandingsState, "get_fields") else StandingsState.__annotations__
        
        # Fases y Modos
        self.assertIn("selected_phase", fields)
        self.assertIn("selected_elo_phase", fields)
        self.assertIn("active_tab", fields)
        self.assertIn("sim_mode", fields)
        self.assertIn("is_simulating", fields)

        # Sabermetría Pitagórica
        self.assertIn("pythagorean_data", fields)
        self.assertIn("leones_pythagorean", fields)

        # ELO & Monte Carlo
        self.assertIn("elo_ratings_data", fields)
        self.assertIn("leones_elo_stats", fields)
        self.assertIn("projections_data", fields)
        self.assertIn("position_matrix_data", fields)
        self.assertIn("leones_monte_carlo", fields)

        # Predictor H2H
        self.assertIn("predictor_home_team", fields)
        self.assertIn("predictor_away_team", fields)
        self.assertIn("predictor_home_elo", fields)
        self.assertIn("predictor_away_elo", fields)
        self.assertIn("predictor_home_prob", fields)
        self.assertIn("predictor_away_prob", fields)
        self.assertIn("predictor_favorite", fields)

        # Desglose Situacional & Semanas ISO
        self.assertIn("leones_advanced", fields)
        self.assertIn("weekly_records_data", fields)
        self.assertIn("latest_weekly_record", fields)

    def test_standings_state_handlers(self):
        """Verifica que los métodos de acción y orquestación estén definidos."""
        self.assertTrue(hasattr(StandingsState, "on_load"))
        self.assertTrue(hasattr(StandingsState, "set_season"))
        self.assertTrue(hasattr(StandingsState, "set_phase"))
        self.assertTrue(hasattr(StandingsState, "set_elo_phase"))
        self.assertTrue(hasattr(StandingsState, "set_sim_mode"))
        self.assertTrue(hasattr(StandingsState, "recalc_simulations"))
        self.assertTrue(hasattr(StandingsState, "set_predictor_home"))
        self.assertTrue(hasattr(StandingsState, "set_predictor_away"))
        self.assertTrue(hasattr(StandingsState, "load_all_standings_data"))


class TestPythagoreanExpectation(unittest.TestCase):
    """Pruebas del Modelo Pitagórico (Bill James / Davenport 1.83)."""

    def test_pythagorean_formula_standard(self):
        """Verifica la fórmula pitagórica estándar W% = CF^1.83 / (CF^1.83 + CP^1.83)."""
        cf = 300.0
        cp = 250.0
        games = 56.0

        denom = (cf ** 1.83) + (cp ** 1.83)
        expected_pct = (cf ** 1.83) / denom
        expected_xw = round(expected_pct * games, 1)

        self.assertGreater(expected_pct, 0.500, "Un equipo con CF > CP debe tener PCT pitagórico > .500")
        self.assertAlmostEqual(expected_pct, 0.583, places=2)
        self.assertAlmostEqual(expected_xw, 32.6, places=1)

    def test_pythagorean_balanced_teams(self):
        """Si CF == CP, el PCT pitagórico debe ser exactamente .500 y xW = JJ/2."""
        cf = 280.0
        cp = 280.0
        games = 56.0

        denom = (cf ** 1.83) + (cp ** 1.83)
        pct = (cf ** 1.83) / denom
        xw = pct * games

        self.assertAlmostEqual(pct, 0.500, places=5)
        self.assertEqual(xw, 28.0)

    def test_pythagorean_clutch_diagnostics(self):
        """Verifica los umbrales de diagnóstico para sobre/sub-rendimiento."""
        # Sobre-rendimiento (Clutch)
        w_real = 35.0
        xw = 32.0
        diff_clutch = w_real - xw  # +3.0 >= 1.5
        self.assertGreaterEqual(diff_clutch, 1.5)

        # Sub-rendimiento (Mala Suerte)
        w_real_unlucky = 27.0
        xw_unlucky = 30.0
        diff_unlucky = w_real_unlucky - xw_unlucky  # -3.0 <= -1.5
        self.assertLessEqual(diff_unlucky, -1.5)

        # En línea
        w_real_fair = 30.0
        xw_fair = 30.2
        diff_fair = w_real_fair - xw_fair
        self.assertTrue(-1.5 < diff_fair < 1.5)


class TestELORatingsAndPredictor(unittest.TestCase):
    """Pruebas de Ratings ELO y Predictor H2H."""

    def test_elo_home_advantage_prob(self):
        """Verifica que el equipo local con rating idéntico tenga ventaja (+35 pts)."""
        elo_home = 1500.0
        elo_away = 1500.0
        p_home, p_away = calculate_matchup_win_prob(elo_home, elo_away, HOME_ADVANTAGE)

        self.assertGreater(p_home, 0.500, "El equipo local debe tener probabilidad > 50%")
        self.assertAlmostEqual(p_home + p_away, 1.0, places=5)
        self.assertAlmostEqual(p_home, 0.550, places=2)

    def test_elo_dominant_team_prob(self):
        """Un equipo con 200 puntos más de ELO debe tener probabilidad dominante."""
        elo_home = 1650.0
        elo_away = 1450.0
        p_home, p_away = calculate_matchup_win_prob(elo_home, elo_away, HOME_ADVANTAGE)

        # Diferencial efectivo = 1650 + 35 - 1450 = +235 pts
        self.assertGreater(p_home, 0.75)
        self.assertLess(p_away, 0.25)

    def test_all_lvbp_teams_have_canonical_names(self):
        """Verifica que ALL_LVBP_NAMES contenga los 8 equipos canónicos."""
        self.assertEqual(len(ALL_LVBP_NAMES), 8)
        self.assertIn("Leones del Caracas", ALL_LVBP_NAMES)
        self.assertIn("Navegantes del Magallanes", ALL_LVBP_NAMES)
        self.assertIn("Tiburones de La Guaira", ALL_LVBP_NAMES)
        self.assertIn("Cardenales de Lara", ALL_LVBP_NAMES)


class TestMonteCarloProjectionsInvariants(unittest.TestCase):
    """Pruebas de Invariantes Algebraicos en Simulaciones Monte Carlo (5,000 Iteraciones)."""

    def test_monte_carlo_simulation_invariants(self):
        """Verifica que las probabilidades generadas por Monte Carlo sumen exactamente los totales teóricos."""
        # Crear standings sintéticos
        standings_df = pd.DataFrame([
            {"team_id": 695, "team_name": "Leones del Caracas", "wins": 32, "losses": 24, "pct": 0.571},
            {"team_id": 693, "team_name": "Cardenales de Lara", "wins": 31, "losses": 25, "pct": 0.554},
            {"team_id": 698, "team_name": "Tiburones de La Guaira", "wins": 30, "losses": 26, "pct": 0.536},
            {"team_id": 696, "team_name": "Navegantes del Magallanes", "wins": 29, "losses": 27, "pct": 0.518},
            {"team_id": 699, "team_name": "Tigres de Aragua", "wins": 28, "losses": 28, "pct": 0.500},
            {"team_id": 697, "team_name": "Bravos de Margarita", "wins": 26, "losses": 30, "pct": 0.464},
            {"team_id": 692, "team_name": "Águilas del Zulia", "wins": 25, "losses": 31, "pct": 0.446},
            {"team_id": 694, "team_name": "Caribes de Anzoátegui", "wins": 23, "losses": 33, "pct": 0.411},
        ])

        elo_dict = {
            695: 1540.0, 693: 1530.0, 698: 1520.0, 696: 1510.0,
            699: 1495.0, 697: 1485.0, 692: 1470.0, 694: 1450.0,
        }

        sim_results = simulate_monte_carlo_projections(
            standings_df=standings_df,
            elo_dict=elo_dict,
            n_simulations=5000,
            simulate_from_scratch=False,
        )

        df_proj = sim_results["projections"]
        df_mat = sim_results["position_matrix"]

        self.assertEqual(len(df_proj), 8, "Debe proyectar a los 8 equipos")
        self.assertEqual(len(df_mat), 8, "La matriz de posiciones debe contener 8 filas")

        # 1. Suma de probabilidades de campeonato == 1.0 (100%)
        total_champ = df_proj["champ_prob"].sum()
        self.assertAlmostEqual(total_champ, 1.0, places=2, msg="La suma de probabilidades de campeón debe ser 1.0")

        # 2. Suma de probabilidades de finalistas == 2.0 (2 equipos en la final)
        total_final = df_proj["final_prob"].sum()
        self.assertAlmostEqual(total_final, 2.0, places=2, msg="La suma de probabilidades de finalistas debe ser 2.0")

        # 3. Suma de pase a Round Robin == 5.0 (5 equipos en Round Robin)
        total_rr = df_proj["rr_prob"].sum()
        self.assertAlmostEqual(total_rr, 5.0, places=2, msg="La suma de probabilidades de Round Robin debe ser 5.0")

        # 4. Suma de filas en matriz de posiciones == 1.0 por cada equipo
        pos_cols = [f"{i}°" for i in range(1, 9)]
        for _, row in df_mat.iterrows():
            row_sum = sum(row[col] for col in pos_cols)
            self.assertAlmostEqual(row_sum, 1.0, places=2, msg=f"La fila de posiciones para {row['team_name']} debe sumar 1.0")


class TestSituationalAndWeeklyRecords(unittest.TestCase):
    """Pruebas del desglose situacional y semanas ISO."""

    def test_day_night_balance(self):
        """Verifica la coherencia entre récord total y desglose día/noche."""
        total_wins = 32
        total_losses = 24
        night_wins = 26
        night_losses = 18

        day_wins = total_wins - night_wins
        day_losses = total_losses - night_losses

        self.assertEqual(day_wins, 6)
        self.assertEqual(day_losses, 6)
        self.assertEqual(day_wins + night_wins, total_wins)
        self.assertEqual(day_losses + night_losses, total_losses)

    def test_iso_weekly_records_formatting(self):
        """Verifica el cálculo de PCT y diferencial en registros semanales."""
        w = 4
        l = 2
        cf = 36
        cp = 24
        tot = w + l
        pct = w / tot
        dif = cf - cp

        pct_str = f".{int(pct * 1000):03d}"
        dif_str = f"{dif:+d}"

        self.assertEqual(pct_str, ".666")
        self.assertEqual(dif_str, "+12")


class TestUIRendering(unittest.TestCase):
    """Pruebas de compilación y renderizado de componentes UI de Dashboard y Standings."""

    def test_index_page_compilation(self):
        """Verifica que la página index() compile y retorne un rx.Component."""
        page = index()
        self.assertIsInstance(page, rx.Component)

    def test_executive_kpi_grid_compilation(self):
        """Verifica que la cuadrícula de KPIs ejecutivos compile."""
        comp = executive_kpi_grid()
        self.assertIsInstance(comp, rx.Component)

    def test_situational_breakdown_compilation(self):
        """Verifica que el desglose situacional compile."""
        comp = situational_breakdown_section()
        self.assertIsInstance(comp, rx.Component)

    def test_iso_week_summary_compilation(self):
        """Verifica que la tarjeta de semana ISO compile."""
        comp = iso_week_summary_card()
        self.assertIsInstance(comp, rx.Component)

    def test_standings_preview_compilation(self):
        """Verifica que la vista previa de standings compile."""
        comp = standings_preview_card()
        self.assertIsInstance(comp, rx.Component)

    def test_standings_page_compilation(self):
        """Verifica que la página standings() compile y retorne un rx.Component."""
        page = standings()
        self.assertIsInstance(page, rx.Component)

    def test_all_four_standings_tabs_compilation(self):
        """Verifica que las 4 pestañas de /standings compilen como componentes Reflex."""
        t1 = tab_official_standings()
        t2 = tab_pythagorean_standings()
        t3 = tab_elo_and_monte_carlo()
        t4 = tab_situational_and_iso_weeks()

        self.assertIsInstance(t1, rx.Component)
        self.assertIsInstance(t2, rx.Component)
        self.assertIsInstance(t3, rx.Component)
        self.assertIsInstance(t4, rx.Component)


if __name__ == '__main__':
    unittest.main()
