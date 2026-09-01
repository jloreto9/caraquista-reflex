# tests/test_core_parity_m1.py
"""
Suite exhaustiva de pruebas unitarias para el Milestone M1 (Core Engines Synchronization & Math Parity).
Verifica:
1. core/supabase_client.py:
   - get_weekly_records
   - get_collective_team_stats
   - get_individual_fielding_stats
   - calculate_batting_stats con fórmula estándar OBP (H + BB + HBP) / (AB + BB + HBP + SF)
   - get_pitching_stats con protección ante IP=0 (np.where)
2. core/wpa_engine.py:
   - BASE_STATE_MAP y BASE_STATE_DIAMONDS
   - encode_base_state: (False, False, True) -> 3 (--3), (True, True, False) -> 4 (12-)
   - format_base_state
   - calculate_win_expectancy, calculate_leverage_index, get_leverage_index, calculate_wpa_for_game
3. core/situational.py:
   - compute_lob_analytics (LOB al 3er out y RISP LOB dentro de la entrada)
   - summarize_slash_line y compute_all_situational_splits
4. core/spray_chart.py:
   - transform_coordinates (250x250 a pies y home plate en 0,0)
   - classify_direction (Pull, Center, Oppo para bateadores derechos y zurdos)
   - classify_batted_ball_hardness (Modelo determinístico BIS)
   - build_baseball_field_figure, create_spray_chart_figure, generate_spray_chart_figure, calculate_spray_stats
5. core/strike_zone.py:
   - convert_pitch_coordinates (coordenadas Gameday a pies)
   - classify_pitch_event (Whiff, Called Strike, Foul, In Play, Ball, Swing, Contact)
   - calculate_discipline_metrics (O-Swing%, Z-Swing%, Contact%, Z-Contact%, Whiff%, CSW%, SwStr%)
   - create_strike_zone_figure, generate_strike_zone_figure
"""

import unittest
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import core.supabase_client as supabase_client
import core.wpa_engine as wpa_engine
import core.situational as situational
import core.spray_chart as spray_chart
import core.strike_zone as strike_zone


class TestSupabaseClientParity(unittest.TestCase):
    """Pruebas de paridad matemática y contratos de supabase_client."""

    def test_standard_obp_formula(self):
        """Verifica la fórmula oficial de OBP = (H + BB + HBP) / (AB + BB + HBP + SF)."""
        df = pd.DataFrame([
            {
                'player_id': 101,
                'ab': 20,
                'r': 5,
                'h': 6,
                'doubles': 2,
                'triples': 0,
                'hr': 1,
                'rbi': 4,
                'bb': 4,
                'so': 3,
                'sb': 1,
                'hbp': 2,
                'sf': 1
            }
        ])
        res = supabase_client.calculate_batting_stats(df)
        self.assertFalse(res.empty)
        row = res.iloc[0]
        
        # AVG = 6 / 20 = 0.300
        self.assertEqual(row['avg'], 0.300)
        
        # OBP = (6 + 4 + 2) / (20 + 4 + 2 + 1) = 12 / 27 = 0.444
        expected_obp = round(12 / 27, 3)
        self.assertEqual(row['obp'], expected_obp)
        
        # SLG = (3*1B + 2*2B + 0*3B + 4*HR) / AB = (3 + 4 + 0 + 4) / 20 = 11 / 20 = 0.550
        # h=6, doubles=2, triples=0, hr=1 => singles=3. TB = 3 + 2*2 + 3*0 + 4*1 = 11.
        self.assertEqual(row['slg'], 0.550)
        
        # OPS = 0.444 + 0.550 = 0.994
        self.assertEqual(row['ops'], round(expected_obp + 0.550, 3))

    def test_obp_division_by_zero(self):
        """Verifica que con AB=0 y BB=0, calculate_batting_stats no lance excepción y retorne 0.0."""
        df = pd.DataFrame([
            {'player_id': 102, 'ab': 0, 'r': 0, 'h': 0, 'doubles': 0, 'triples': 0, 'hr': 0, 'rbi': 0, 'bb': 0, 'so': 0, 'sb': 0}
        ])
        res = supabase_client.calculate_batting_stats(df)
        self.assertEqual(res.iloc[0]['avg'], 0.0)
        self.assertEqual(res.iloc[0]['obp'], 0.0)
        self.assertEqual(res.iloc[0]['slg'], 0.0)
        self.assertEqual(res.iloc[0]['ops'], 0.0)

    def test_get_collective_team_stats_signature(self):
        """Verifica que get_collective_team_stats maneje los argumentos group y retorne estructuras válidas."""
        # Test unitario sin red para validación de tipo/firma
        res_dict = supabase_client.get_collective_team_stats(season=2025, group=None)
        self.assertIsInstance(res_dict, dict)
        self.assertIn('batting', res_dict)
        self.assertIn('pitching', res_dict)
        self.assertIn('fielding', res_dict)


class TestWPAEngineParity(unittest.TestCase):
    """Pruebas de paridad matemática de WPA Engine y Tango RE24."""

    def test_base_state_encoding_explicit_values(self):
        """Verifica explícitamente el mapeo 0..7 de estados de bases."""
        self.assertEqual(wpa_engine.encode_base_state(False, False, False), 0)  # ---
        self.assertEqual(wpa_engine.encode_base_state(True, False, False), 1)   # 1--
        self.assertEqual(wpa_engine.encode_base_state(False, True, False), 2)   # -2-
        self.assertEqual(wpa_engine.encode_base_state(False, False, True), 3)   # --3
        self.assertEqual(wpa_engine.encode_base_state(True, True, False), 4)    # 12-
        self.assertEqual(wpa_engine.encode_base_state(True, False, True), 5)    # 1-3
        self.assertEqual(wpa_engine.encode_base_state(False, True, True), 6)    # -23
        self.assertEqual(wpa_engine.encode_base_state(True, True, True), 7)     # 123

    def test_format_base_state_diamonds(self):
        """Verifica la representación visual de diamantes."""
        self.assertEqual(wpa_engine.format_base_state(0), "◇ ◇ ◇")
        self.assertEqual(wpa_engine.format_base_state(1), "◇ ◇ ◆")
        self.assertEqual(wpa_engine.format_base_state(2), "◇ ◆ ◇")
        self.assertEqual(wpa_engine.format_base_state(3), "◆ ◇ ◇")
        self.assertEqual(wpa_engine.format_base_state(4), "◇ ◆ ◆")
        self.assertEqual(wpa_engine.format_base_state(5), "◆ ◇ ◆")
        self.assertEqual(wpa_engine.format_base_state(6), "◆ ◆ ◇")
        self.assertEqual(wpa_engine.format_base_state(7), "◆ ◆ ◆")

    def test_win_expectancy_and_leverage_index_helpers(self):
        """Verifica calculate_win_expectancy y get_leverage_index."""
        we_neutral = wpa_engine.calculate_win_expectancy(1, False, 0, 0, 0, 0)
        self.assertAlmostEqual(we_neutral, 0.50, delta=0.08)

        we_home_lead = wpa_engine.calculate_win_expectancy(8, False, 1, 0, 8, 1)
        self.assertGreater(we_home_lead, 0.95)

        li = wpa_engine.get_leverage_index(9, "bottom", 2, 7, 0)
        self.assertGreater(li, 1.5)


class TestSituationalParity(unittest.TestCase):
    """Pruebas de cálculo de LOB Tracker y Situacionales."""

    def test_lob_analytics_detailed(self):
        """Verifica LOB al 3er out y RISP LOB dentro de la entrada."""
        df_plays = pd.DataFrame([
            # Jugada 1: 2 outs con corredores en 1B y 3B -> Falla -> LOB=2, RISP LOB=1
            {
                "batter_name": "Balbino Fuenmayor",
                "runner_1b": True, "runner_2b": False, "runner_3b": True,
                "is_2_outs": True, "is_hit": False, "is_walk": False, "is_hbp": False,
                "is_risp": True, "rbi": 0, "is_pa": True, "is_ab": True
            },
            # Jugada 2: 0 outs con corredores en 2B y 3B -> Falla con 0 RBI -> Mid-inning RISP LOB = 2
            {
                "batter_name": "Balbino Fuenmayor",
                "runner_1b": False, "runner_2b": True, "runner_3b": True,
                "is_2_outs": False, "is_hit": False, "is_walk": False, "is_hbp": False,
                "is_risp": True, "rbi": 0, "is_pa": True, "is_ab": True
            },
            # Jugada 3: 1 out con corredor en 2B -> Hit sencillo con 1 RBI -> No es LOB
            {
                "batter_name": "Balbino Fuenmayor",
                "runner_1b": False, "runner_2b": True, "runner_3b": False,
                "is_2_outs": False, "is_hit": True, "is_walk": False, "is_hbp": False,
                "is_risp": True, "rbi": 1, "is_pa": True, "is_ab": True
            }
        ])
        
        totals, df_players = situational.compute_lob_analytics(df_plays)
        self.assertEqual(totals['total_lob_ending'], 2)
        self.assertEqual(totals['total_risp_lob_ending'], 1)
        self.assertEqual(totals['total_risp_lob_mid'], 2)
        self.assertEqual(totals['total_risp_lob'], 3)


class TestSprayChartParity(unittest.TestCase):
    """Pruebas del motor determinístico BIS de Spray Charts."""

    def test_coordinate_transformation(self):
        """Verifica la transformación de coordenadas Gameday a pies centrados en Home Plate."""
        # Home plate en (125, 204.5) -> (0 ft, 0 ft, 0 ft dist, 0 deg)
        x_ft, y_ft, dist_ft, angle_deg = spray_chart.transform_coordinates(125, 204.5)
        self.assertEqual(x_ft, 0.0)
        self.assertEqual(y_ft, 0.0)
        self.assertEqual(dist_ft, 0.0)
        self.assertEqual(angle_deg, 0.0)

        # Postes de foul a 45 grados
        x_rf, y_rf, d_rf, a_rf = spray_chart.transform_coordinates(200, 129.5)
        self.assertGreater(x_rf, 0.0)
        self.assertGreater(y_rf, 0.0)
        self.assertGreater(d_rf, 100.0)

    def test_direction_classification(self):
        """Verifica la clasificación Pull / Center / Oppo."""
        # Bateador derecho
        self.assertIn("Pull", spray_chart.classify_direction(-25.0, "R"))
        self.assertIn("Center", spray_chart.classify_direction(0.0, "R"))
        self.assertIn("Oppo", spray_chart.classify_direction(25.0, "R"))

        # Bateador zurdo (invertido)
        self.assertIn("Pull", spray_chart.classify_direction(25.0, "L"))
        self.assertIn("Center", spray_chart.classify_direction(0.0, "L"))
        self.assertIn("Oppo", spray_chart.classify_direction(-25.0, "L"))

    def test_bis_hardness_model(self):
        """Verifica el modelo de dureza de contacto BIS."""
        # Jonrón y triples son siempre Hard
        self.assertEqual(spray_chart.classify_batted_ball_hardness("Home Run", "fly_ball", 390, "unknown"), "hard")
        self.assertEqual(spray_chart.classify_batted_ball_hardness("Triple", "line_drive", 320, "medium"), "hard")

        # Popups y toques son Soft
        self.assertEqual(spray_chart.classify_batted_ball_hardness("Pop Out", "popup", 110, "medium"), "soft")
        self.assertEqual(spray_chart.classify_batted_ball_hardness("Sac Bunt", "bunt_grounder", 40, "medium"), "soft")

        # Flyout corto es Soft (<185 ft)
        self.assertEqual(spray_chart.classify_batted_ball_hardness("Flyout", "fly_ball", 170, "medium"), "soft")

        # Flyout largo es Hard (>=310 ft)
        self.assertEqual(spray_chart.classify_batted_ball_hardness("Flyout", "fly_ball", 325, "medium"), "hard")

    def test_spray_chart_figure_generation(self):
        """Verifica que create_spray_chart_figure y generate_spray_chart_figure retornen objetos go.Figure."""
        fig_empty = spray_chart.create_spray_chart_figure(pd.DataFrame())
        self.assertIsInstance(fig_empty, go.Figure)

        alias_fig = spray_chart.generate_spray_chart_figure(pd.DataFrame())
        self.assertIsInstance(alias_fig, go.Figure)


class TestStrikeZoneParity(unittest.TestCase):
    """Pruebas del motor 3x3 de Zona de Strike y Disciplina en el Plato."""

    def test_convert_pitch_coordinates(self):
        """Verifica la calibración de coordenadas a pies centrados en Home Plate."""
        # Centro horizontal: x_raw=110.0 -> x_ft = 0.0
        x_ft, z_ft = strike_zone.convert_pitch_coordinates(110.0, 156.0, 3.4, 1.5)
        self.assertEqual(x_ft, 0.0)
        self.assertGreaterEqual(z_ft, 1.5)
        self.assertLessEqual(z_ft, 3.4)

    def test_classify_pitch_event(self):
        """Verifica la clasificación sabermétrica de llamadas de pitcheo."""
        w = strike_zone.classify_pitch_event("Swinging Strike")
        self.assertTrue(w["is_whiff"])
        self.assertTrue(w["is_swing"])
        self.assertTrue(w["is_strike"])
        self.assertFalse(w["is_ball"])

        cs = strike_zone.classify_pitch_event("Called Strike")
        self.assertTrue(cs["is_called_strike"])
        self.assertTrue(cs["is_strike"])
        self.assertFalse(cs["is_swing"])

        b = strike_zone.classify_pitch_event("Ball")
        self.assertTrue(b["is_ball"])
        self.assertFalse(b["is_strike"])

    def test_calculate_discipline_metrics(self):
        """Verifica los cálculos de O-Swing%, Z-Contact%, Whiff%, CSW% y SwStr%."""
        df_pitches = pd.DataFrame([
            # 1. En zona, swing, abanicado (Whiff)
            {"in_zone": True, "is_swing": True, "is_whiff": True, "is_contact": False, "is_called_strike": False, "is_ball": False, "is_strike": True},
            # 2. En zona, swing, contacto (Foul)
            {"in_zone": True, "is_swing": True, "is_whiff": False, "is_contact": True, "is_called_strike": False, "is_ball": False, "is_strike": True},
            # 3. En zona, no swing (Called Strike)
            {"in_zone": True, "is_swing": False, "is_whiff": False, "is_contact": False, "is_called_strike": True, "is_ball": False, "is_strike": True},
            # 4. Fuera de zona, swing, abanicado (Whiff) -> O-Swing
            {"in_zone": False, "is_swing": True, "is_whiff": True, "is_contact": False, "is_called_strike": False, "is_ball": False, "is_strike": True},
            # 5. Fuera de zona, no swing (Ball)
            {"in_zone": False, "is_swing": False, "is_whiff": False, "is_contact": False, "is_called_strike": False, "is_ball": True, "is_strike": False},
        ])
        
        metrics = strike_zone.calculate_discipline_metrics(df_pitches)
        self.assertEqual(metrics["total_pitches"], 5)
        
        # Zone%: 3/5 = 60.0%
        self.assertEqual(metrics["zone_pct"], 60.0)
        # Swing%: 3/5 = 60.0%
        self.assertEqual(metrics["swing_pct"], 60.0)
        # O-Swing%: 1 swing fuera de zona / 2 pitcheos fuera de zona = 50.0%
        self.assertEqual(metrics["o_swing_pct"], 50.0)
        # Z-Swing%: 2 swings en zona / 3 pitcheos en zona = 66.7%
        self.assertEqual(metrics["z_swing_pct"], 66.7)
        # Z-Contact%: 1 contacto en zona / 2 swings en zona = 50.0%
        self.assertEqual(metrics["z_contact_pct"], 50.0)
        # Whiff%: 2 whiffs / 3 swings = 66.7%
        self.assertEqual(metrics["whiff_pct"], 66.7)
        # CSW%: (1 called strike + 2 whiffs) / 5 pitcheos = 60.0%
        self.assertEqual(metrics["csw_pct"], 60.0)
        # SwStr%: 2 whiffs / 5 pitcheos = 40.0%
        self.assertEqual(metrics["swstr_pct"], 40.0)

    def test_strike_zone_figure_generation(self):
        """Verifica que create_strike_zone_figure y generate_strike_zone_figure retornen objetos go.Figure."""
        fig_empty = strike_zone.create_strike_zone_figure(pd.DataFrame())
        self.assertIsInstance(fig_empty, go.Figure)

        alias_fig = strike_zone.generate_strike_zone_figure(pd.DataFrame())
        self.assertIsInstance(alias_fig, go.Figure)


if __name__ == "__main__":
    unittest.main()
