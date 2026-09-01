# tests/test_adversarial_stress.py
"""
test_adversarial_stress.py
---------------------------
Tier 5 Adversarial Stress & Robustness Test Suite for caraquista-reflex.

Covers:
1. Missing API responses, network timeouts, malformed payloads, and null/NaN DataFrames across all 8 reactive state handlers:
   - AppState / BaseState
   - StandingsState
   - IndividualesState
   - ColectivasState
   - WpaState
   - SituationalState
   - SprayState
   - BullpenState
2. Concurrency, thread safety, and cache invalidation under parallel load in `core/cache.py`.
3. Extreme spatial and physical boundaries in Spray Charts and Strike Zone engines.
"""
import os
os.environ.setdefault("PYTEST_CURRENT_TEST", "true")

import unittest
from unittest.mock import patch, MagicMock
import threading
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import reflex as rx

# Core imports
from core.cache import cache_ttl
from core.spray_chart import (
    transform_coordinates,
    classify_direction,
    classify_batted_ball_hardness,
    calculate_spray_stats,
    create_spray_chart_figure,
    generate_spray_chart_figure,
)
from core.strike_zone import (
    convert_pitch_coordinates,
    classify_pitch_event,
    calculate_discipline_metrics,
    create_strike_zone_figure,
    generate_strike_zone_figure,
)
from core.wpa_engine import (
    encode_base_state,
    format_base_state,
    calculate_win_expectancy,
    calculate_leverage_index,
    process_game_wpa_advanced,
    calculate_player_game_wpa,
    get_season_wpa_leaderboard,
)
from core.elo import (
    calculate_matchup_win_prob,
    simulate_monte_carlo_projections,
    BASE_ELO,
    HOME_ADVANTAGE,
)
from core.situational import (
    compute_all_situational_splits,
    compute_lob_analytics,
    compute_bvp_summary,
    summarize_slash_line,
)
from core.bullpen_lineups import (
    compute_bullpen_inherited_stats,
)
from core.teams import (
    resolve_team_id,
    get_team_name,
    get_team_abbr,
    get_team_logo,
    get_team_color,
    LVBP_TEAMS,
)

# Reflex States
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.state.standings_state import StandingsState
from republicaraquistapp.state.individuales_state import IndividualesState
from republicaraquistapp.state.colectivas_state import ColectivasState
from republicaraquistapp.state.wpa_state import WpaState, build_wp_evolution_chart
from republicaraquistapp.state.situacional_state import (
    SituationalState,
    build_ops_by_situation_chart,
    build_top_risp_lob_chart,
)
from republicaraquistapp.state.spray_state import SprayState
from republicaraquistapp.state.bullpen_state import (
    BullpenState,
    build_bullpen_ir_chart,
    build_lineup_heatmap_chart,
)


class TestAdversarialAppState(unittest.TestCase):
    """Stress testing AppState and BaseState resilience under network failures and corrupt data."""

    @patch("republicaraquistapp.state.base_state.get_available_seasons")
    @patch("republicaraquistapp.state.base_state.get_standings")
    @patch("republicaraquistapp.state.base_state.get_recent_games")
    def test_app_state_network_timeout_on_load(self, mock_games, mock_standings, mock_seasons):
        """AppState.on_load debe capturar timeouts de red sin propagar excepciones no controladas."""
        mock_seasons.side_effect = TimeoutError("Connection to Supabase timed out after 30s")
        mock_standings.return_value = None
        mock_games.return_value = None

        state = AppState()
        state.on_load()

        self.assertTrue(state.has_error)
        self.assertIn("Error de Inicialización", state.error_title)
        self.assertFalse(state.is_loading)

    @patch("republicaraquistapp.state.base_state.get_standings")
    @patch("republicaraquistapp.state.base_state.get_recent_games")
    def test_app_state_nan_and_corrupt_dataframe_load(self, mock_games, mock_standings):
        """AppState debe manejar DataFrames con valores NaN y nulos en standings y juegos recientes."""
        corrupt_standings = pd.DataFrame([
            {
                "pos": np.nan,
                "team_id": None,
                "team_name": np.nan,
                "games_played": np.nan,
                "wins": None,
                "losses": np.nan,
                "win_pct": np.nan,
                "games_behind": None,
                "streak": None,
                "last_10": None,
                "home_record": None,
                "away_record": None,
                "runs_scored": None,
                "runs_against": None,
                "run_differential": None,
            }
        ])
        mock_standings.return_value = corrupt_standings

        corrupt_games = pd.DataFrame([
            {
                "game_date": None,
                "home_team": None,
                "away_team": None,
                "home_team_id": None,
                "away_team_id": None,
                "home_score": None,
                "away_score": None,
            }
        ])
        mock_games.return_value = corrupt_games

        state = AppState()
        state.load_season_data()

        # No debe lanzar excepción y debe estructurar registros seguros
        self.assertEqual(len(state.standings_data), 1)
        record = state.standings_data[0]
        self.assertEqual(record["team_name"], "nan")
        self.assertEqual(record["wins"], 0)
        self.assertEqual(record["losses"], 0)
        self.assertEqual(record["pct"], ".000")

        self.assertEqual(len(state.recent_games_data), 1)
        game_record = state.recent_games_data[0]
        self.assertEqual(game_record["home_score"], 0)
        self.assertEqual(game_record["away_score"], 0)

    def test_app_state_invalid_season_strings(self):
        """set_season debe procesar entradas malformadas de forma resiliente."""
        state = AppState()
        # Probar season string corrupta
        state.set_season("INVALID_SEASON")
        self.assertTrue(state.has_error)
        self.assertFalse(state.is_loading)


class TestAdversarialStandingsState(unittest.TestCase):
    """Stress testing StandingsState math, Monte Carlo, and ELO under edge inputs."""

    @patch("republicaraquistapp.state.standings_state.get_standings")
    @patch("republicaraquistapp.state.standings_state.init_supabase")
    @patch("republicaraquistapp.state.standings_state.get_weekly_records")
    @patch("republicaraquistapp.state.standings_state.get_leones_advanced_stats")
    @patch("republicaraquistapp.state.standings_state.get_recent_games")
    def test_standings_zero_games_zero_runs_pythagorean(
        self, mock_recent, mock_adv, mock_weekly, mock_supabase, mock_standings
    ):
        """Expectativa Pitagórica con 0 carreras y 0 juegos debe ser 0.500 sin ZeroDivisionError."""
        zero_df = pd.DataFrame([
            {"team_id": 695, "team_name": "Leones del Caracas", "runs_for": 0, "runs_against": 0, "wins": 0, "losses": 0, "pct": 0.0}
        ])
        mock_standings.return_value = zero_df
        mock_supabase.side_effect = Exception("Supabase offline")
        mock_weekly.return_value = pd.DataFrame()
        mock_adv.return_value = {}
        mock_recent.return_value = pd.DataFrame()

        state = StandingsState()
        state.load_all_standings_data()

        self.assertEqual(len(state.pythagorean_data), 1)
        pyth_entry = state.pythagorean_data[0]
        self.assertEqual(pyth_entry["pyth_pct"], ".500")
        self.assertEqual(pyth_entry["xw"], "0.0")
        self.assertEqual(pyth_entry["xl"], "0.0")

    def test_monte_carlo_projections_empty_and_nan_elo(self):
        """simulate_monte_carlo_projections debe manejar ELO dicts con valores extremos o NaN."""
        empty_standings = pd.DataFrame()
        corrupt_elo = {
            695: np.nan,
            696: 1500.0,
            697: -9999.0,
            698: 9999.0,
            699: 1500.0,
            700: 1500.0,
            701: 1500.0,
            702: 1500.0,
        }
        # Deben sanitizarse los NaNs a BASE_ELO
        res = simulate_monte_carlo_projections(empty_standings, corrupt_elo, n_simulations=100)
        self.assertIn("projections", res)
        self.assertIn("position_matrix", res)
        self.assertEqual(len(res["projections"]), 8)

    def test_h2h_predictor_extreme_and_unrecognized_teams(self):
        """H2H Matchup Predictor con nombres de equipos desconocidos o vacíos."""
        state = StandingsState()
        state.predictor_home_team = "Equipo Inexistente"
        state.predictor_away_team = ""
        elo_dict = {695: 1500.0, 696: 1500.0}
        state._compute_matchup_prediction(elo_dict)

        self.assertGreaterEqual(state.predictor_home_prob, 0.0)
        self.assertLessEqual(state.predictor_home_prob, 1.0)
        self.assertEqual(round(state.predictor_home_prob + state.predictor_away_prob, 4), 1.0)


class TestAdversarialIndividualesState(unittest.TestCase):
    """Stress testing IndividualesState calculations under zero PA/AB/IP and corrupt values."""

    @patch("republicaraquistapp.state.individuales_state.get_batting_stats")
    @patch("republicaraquistapp.state.individuales_state.get_pitching_stats")
    @patch("republicaraquistapp.state.individuales_state.get_individual_fielding_stats")
    def test_individuales_zero_denominators_and_nan_stats(self, mock_field, mock_pit, mock_bat):
        """Bateo y Pitcheo con AB=0, IP=0 y nulos deben producir 0.0/strings seguros sin excepciones."""
        mock_bat.return_value = pd.DataFrame([
            {
                "player_id": 999999,
                "player_name": "Novato Fantasma",
                "ab": 0, "r": 0, "h": 0, "doubles": 0, "triples": 0, "hr": 0,
                "rbi": 0, "bb": 0, "so": 0, "sb": 0, "cs": 0, "hbp": 0, "sf": 0, "sh": 0
            },
            {
                "player_id": 888888,
                "player_name": "Jugador Con NaNs",
                "ab": np.nan, "r": np.nan, "h": np.nan, "doubles": np.nan, "triples": np.nan,
                "hr": np.nan, "rbi": np.nan, "bb": np.nan, "so": np.nan, "sb": np.nan,
                "cs": np.nan, "hbp": np.nan, "sf": np.nan, "sh": np.nan
            }
        ])

        mock_pit.return_value = pd.DataFrame([
            {
                "player_id": 777777,
                "player_name": "Lanzador Cero IP",
                "g": 1, "gs": 0, "w": 0, "l": 0, "sv": 0, "hld": 0, "ip": 0.0,
                "h": 0, "r": 0, "er": 0, "bb": 0, "so": 0, "hr": 0, "hbp": 0
            }
        ])

        mock_field.return_value = pd.DataFrame([
            {
                "player_id": 666666,
                "player_name": "Defensor Cero Oportunidades",
                "pos": "SS", "g": 1, "po": 0, "a": 0, "e": 0, "dp": 0, "inn": 0.0, "cs": 0, "sb": 0, "pb": 0
            }
        ])

        state = IndividualesState()
        state.load_all_stats()

        self.assertEqual(len(state.batting_data_raw), 2)
        novato = state.batting_data_raw[0]
        self.assertEqual(novato["avg"], 0.0)
        self.assertEqual(novato["obp"], 0.0)
        self.assertEqual(novato["slg"], 0.0)
        self.assertEqual(novato["ops"], 0.0)
        self.assertEqual(novato["wrc_plus"], 100)

        self.assertEqual(len(state.pitching_data_raw), 1)
        pitcher = state.pitching_data_raw[0]
        self.assertEqual(pitcher["era"], 0.0)
        self.assertEqual(pitcher["whip"], 0.0)

        self.assertEqual(len(state.fielding_data_raw), 1)
        fielding = state.fielding_data_raw[0]
        self.assertEqual(fielding["fpct"], 1.0)
        self.assertEqual(fielding["rf9"], 0.0)

    def test_h2h_comparator_missing_or_empty_selection(self):
        """El comparador H2H debe manejar selección de jugadores inexistentes sin fallar."""
        state = IndividualesState()
        state.selected_player_1 = "Inexistente 1"
        state.selected_player_2 = "Inexistente 2"
        state.generate_h2h_comparison()

        self.assertIn("Seleccione dos jugadores", state.h2h_verdict)
        self.assertEqual(len(state.h2h_rows), 0)


class TestAdversarialColectivasState(unittest.TestCase):
    """Stress testing ColectivasState across empty tables and missing categories."""

    @patch("republicaraquistapp.state.colectivas_state.get_collective_team_stats")
    def test_colectivas_empty_and_nan_collective_stats(self, mock_stats):
        """ColectivasState debe manejar DataFrames vacíos o con NaNs en bateo, pitcheo y fildeo."""
        mock_stats.return_value = pd.DataFrame()

        state = ColectivasState()
        state.load_collective_stats()

        self.assertEqual(len(state.collective_batting_data), 0)
        self.assertEqual(len(state.collective_pitching_data), 0)
        self.assertEqual(len(state.collective_fielding_data), 0)
        self.assertEqual(state.batting_kpis["avg_team"], "-")
        self.assertEqual(state.pitching_kpis["era_team"], "-")
        self.assertEqual(state.fielding_kpis["fpct_team"], "-")


class TestAdversarialWpaAndSituational(unittest.TestCase):
    """Stress testing WpaState, SituationalState, and Plotly figure generators under edge inputs."""

    def test_wpa_chart_builder_empty_and_extreme_wpa(self):
        """build_wp_evolution_chart con DF vacío, 1 fila y swings de WPA de +-1.0."""
        # 1. DF Vacío
        fig_empty = build_wp_evolution_chart(pd.DataFrame(), "Sin Datos")
        self.assertIsInstance(fig_empty, go.Figure)

        # 2. DF con swings extremos
        extreme_wpa_df = pd.DataFrame([
            {
                "atbat_index": 0,
                "inning": 1,
                "halfInning": "top",
                "score_str": "0-0",
                "batter": "Bateador 1",
                "pitcher": "Lanzador 1",
                "eventType": "Walk",
                "base_icons": "◆ ◇ ◇",
                "outs_before": 0,
                "li": 1.0,
                "wp_after": 0.45,
                "wpa": -0.05,
            },
            {
                "atbat_index": 1,
                "inning": 9,
                "halfInning": "bottom",
                "score_str": "3-2",
                "batter": "Bateador Walkoff",
                "pitcher": "Cerrador",
                "eventType": "Home Run",
                "base_icons": "◆ ◆ ◆",
                "outs_before": 2,
                "li": 5.8,
                "wp_after": 1.0,
                "wpa": 0.55,
            }
        ])
        fig_extreme = build_wp_evolution_chart(extreme_wpa_df, "Leones vs Magallanes")
        self.assertIsInstance(fig_extreme, go.Figure)
        self.assertGreaterEqual(len(fig_extreme.data), 4)

    def test_situational_and_lob_builders_empty_data(self):
        """build_ops_by_situation_chart y build_top_risp_lob_chart con DataFrames vacíos."""
        fig_ops = build_ops_by_situation_chart(pd.DataFrame())
        self.assertIsInstance(fig_ops, go.Figure)

        fig_lob = build_top_risp_lob_chart(pd.DataFrame())
        self.assertIsInstance(fig_lob, go.Figure)

    def test_lob_analytics_with_malformed_and_missing_events(self):
        """compute_lob_analytics debe procesar jugadas con campos None/NaN sin fallar."""
        malformed_plays = [
            {"about": {}, "matchup": {}, "result": {}},
            {"about": {"isComplete": True, "inning": 1, "halfInning": "top", "hasOut": True}, "matchup": {"batter": {"fullName": "B1"}}, "result": {"event": "Strikeout"}},
            {"about": {"isComplete": True, "inning": 2, "halfInning": "bottom", "hasOut": True}, "matchup": {"batter": {"fullName": None}}, "result": {"event": None}},
        ]
        lob_res = compute_lob_analytics(malformed_plays)
        self.assertIn("summary", lob_res)
        self.assertIn("players_df", lob_res)


class TestAdversarialSprayAndStrikeZone(unittest.TestCase):
    """Stress testing spray coordinates, strike zone 3x3, and extreme physical values."""

    def test_transform_coordinates_extreme_and_none(self):
        """transform_coordinates con None, NaN y coordenadas astronómicas."""
        # 1. Nulos
        x, y, d, a = transform_coordinates(None, None)
        self.assertEqual((x, y, d, a), (0.0, 0.0, 0.0, 0.0))

        # 2. Coordenadas astronómicas
        x_huge, y_huge, d_huge, a_huge = transform_coordinates(100000.0, -100000.0)
        self.assertGreater(d_huge, 0.0)
        self.assertGreaterEqual(a_huge, -180.0)
        self.assertLessEqual(a_huge, 180.0)

    def test_classify_direction_boundaries(self):
        """classify_direction en las fronteras exactas de +-15 grados."""
        # Bateador derecho
        self.assertEqual(classify_direction(-15.1, "R"), "Pull (Hacia LF)")
        self.assertEqual(classify_direction(-15.0, "R"), "Center (Centro)")
        self.assertEqual(classify_direction(0.0, "R"), "Center (Centro)")
        self.assertEqual(classify_direction(15.0, "R"), "Center (Centro)")
        self.assertEqual(classify_direction(15.1, "R"), "Oppo (Hacia RF)")

        # Bateador zurdo
        self.assertEqual(classify_direction(15.1, "L"), "Pull (Hacia RF)")
        self.assertEqual(classify_direction(15.0, "L"), "Center (Centro)")
        self.assertEqual(classify_direction(-15.1, "L"), "Oppo (Hacia LF)")

        # Bateador con valor nulo o no estándar
        self.assertEqual(classify_direction(20.0, None), "Oppo (Hacia RF)")

    def test_classify_hardness_adversarial_events(self):
        """classify_batted_ball_hardness con eventos inesperados o distancias negativas/gigantes."""
        # Distancia negativa por error de sensor
        h_neg = classify_batted_ball_hardness("Flyout", "fly_ball", -50.0, "unknown")
        self.assertEqual(h_neg, "soft")

        # Jonrón de 600 pies
        h_hr = classify_batted_ball_hardness("Home Run", "fly_ball", 600.0, "unknown")
        self.assertEqual(h_hr, "hard")

        # Evento desconocido
        h_weird = classify_batted_ball_hardness("Triple Play Raro", "unknown", 100.0, None)
        self.assertEqual(h_weird, "medium")

    def test_convert_pitch_coordinates_inverted_and_extreme_strike_zone(self):
        """convert_pitch_coordinates con sz_top <= sz_bot, valores negativos y NaNs."""
        # 1. Zona invertida (sz_top < sz_bot)
        x_inv, z_inv = convert_pitch_coordinates(110.0, 156.0, sz_top=1.5, sz_bot=3.5)
        self.assertEqual(x_inv, 0.0)
        self.assertIsInstance(z_inv, float)

        # 2. sz_top y sz_bot como NaN
        x_nan, z_nan = convert_pitch_coordinates(110.0, 156.0, sz_top=np.nan, sz_bot=np.nan)
        self.assertEqual(x_nan, 0.0)
        self.assertIsInstance(z_nan, float)

        # 3. Pitcheo descontrolado a 50 pies del home plate
        x_wild, z_wild = convert_pitch_coordinates(-500.0, -500.0)
        self.assertIsInstance(x_wild, float)
        self.assertIsInstance(z_wild, float)

    def test_calculate_discipline_metrics_zero_and_all_whiffs(self):
        """calculate_discipline_metrics con 0 pitcheos y con 100% de swings abanicados."""
        # 1. Vacío
        m_empty = calculate_discipline_metrics(pd.DataFrame())
        self.assertEqual(m_empty["total_pitches"], 0)
        self.assertEqual(m_empty["csw_pct"], 0.0)

        # 2. 100% Whiffs en zona
        whiff_df = pd.DataFrame([
            {
                "x_ft": 0.0, "z_ft": 2.5,
                "is_in_zone": True, "is_swing": True, "is_whiff": True,
                "is_contact": False, "is_called_strike": False, "is_ball": False, "is_strike": True
            }
        ] * 10)
        m_whiff = calculate_discipline_metrics(whiff_df)
        self.assertEqual(m_whiff["total_pitches"], 10)
        self.assertEqual(m_whiff["whiff_pct"], 100.0)
        self.assertEqual(m_whiff["z_swing_pct"], 100.0)
        self.assertEqual(m_whiff["z_contact_pct"], 0.0)


class TestAdversarialBullpenAndLineups(unittest.TestCase):
    """Stress testing Bullpen inherited runner calculations and Lineup heatmap builders."""

    def test_bullpen_inherited_stats_zero_and_nan(self):
        """compute_bullpen_inherited_stats con lista vacía de jugadas y sin relevistas."""
        empty_stats = compute_bullpen_inherited_stats([])
        self.assertIn("summary_df", empty_stats)
        self.assertIn("detailed_df", empty_stats)
        self.assertEqual(empty_stats["total_ir"], 0)
        self.assertEqual(empty_stats["total_irs"], 0)
        self.assertEqual(empty_stats["irs_pct"], 0.0)

    def test_bullpen_and_lineup_figure_builders_empty(self):
        """build_bullpen_ir_chart y build_lineup_heatmap_chart con DataFrames vacíos."""
        fig_ir = build_bullpen_ir_chart(pd.DataFrame())
        self.assertIsInstance(fig_ir, go.Figure)

        fig_heat = build_lineup_heatmap_chart(pd.DataFrame())
        self.assertIsInstance(fig_heat, go.Figure)


class TestConcurrencyAndCacheInvalidation(unittest.TestCase):
    """Stress testing concurrent state executions and @cache_ttl thread-safety."""

    def test_cache_ttl_concurrency_and_invalidation(self):
        """50 hilos concurrentes llamando y limpiando la caché simultáneamente no deben causar colisión."""
        call_count = 0
        lock = threading.Lock()

        @cache_ttl(ttl_seconds=60)
        def compute_heavy_metric(x: int, y: int) -> int:
            nonlocal call_count
            with lock:
                call_count += 1
            time.sleep(0.001)
            return x + y

        errors = []

        def worker(thread_id: int):
            try:
                for i in range(20):
                    val = compute_heavy_metric(i % 5, (i % 5) * 2)
                    self.assertEqual(val, (i % 5) * 3)
                    if thread_id == 0 and i % 5 == 0:
                        compute_heavy_metric.clear_cache()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errores encontrados durante estrés concurrente: {errors}")
        self.assertGreater(call_count, 0)

    def test_concurrent_state_simulations(self):
        """Múltiples simulaciones Monte Carlo ejecutadas en paralelo no deben interferir entre sí."""
        elo_dict = {tid: 1500.0 for tid in LVBP_TEAMS.keys()}
        results = []
        errors = []

        def sim_task(sim_id: int):
            try:
                res = simulate_monte_carlo_projections(
                    standings_df=pd.DataFrame(),
                    elo_dict=elo_dict,
                    n_simulations=500,
                    simulate_from_scratch=True,
                )
                champ_sum = res["projections"]["champ_prob"].sum()
                results.append(champ_sum)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=sim_task, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errores en simulaciones concurrentes: {errors}")
        self.assertEqual(len(results), 8)
        for champ_sum in results:
            self.assertAlmostEqual(champ_sum, 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
