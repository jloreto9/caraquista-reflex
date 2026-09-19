# tests/test_pitching_engine.py
"""
test_pitching_engine.py
-----------------------
Suite de pruebas unitarias para el motor analítico de datos de Pitching Summary (core/pitching_engine.py).
Valida:
1. Búsqueda de lanzadores y estructura de respuesta.
2. Detección de historial de Leones del Caracas.
3. Formato y ordenamiento de Game Logs (aperturas y relevos).
4. Exactitud matemática de métricas Statcast (IVB, HB, Whiff%, CSW%, Zone%).
5. Exactitud matemática de métricas Play-by-Play LVBP (Destinos, 1stS%, Carga y Splits).
"""

import unittest
from core.pitching_engine import (
    search_pitchers,
    _build_statcast_table,
    _build_pbp_summary,
    _build_inning_workload,
    _build_platoon_splits,
    _get_caracas_pitcher_ids,
)


class TestPitchingEngine(unittest.TestCase):
    """Pruebas del motor sabermétrico de pitcheo."""

    def test_caracas_pitcher_ids_present(self):
        """Verifica que el set de IDs caraquistas contenga los lanzadores emblemáticos."""
        ids = _get_caracas_pitcher_ids()
        self.assertIn(544150, ids)  # Albert Suárez
        self.assertIn(518586, ids)  # Jhoulys Chacín
        self.assertIn(612797, ids)  # Erick Leal

    def test_statcast_table_math(self):
        """Valida los cálculos de IVB, HB, Whiff%, CSW% y Zone% sobre una muestra determinista."""
        pitches = [
            # 4-Seam: 4 pitcheos
            {
                "pitch_name": "4-Seam Fastball", "speed": 96.0, "spin": 2400,
                "ivb": 18.0, "hb": 8.0, "is_whiff": True, "is_called": False,
                "is_foul": False, "is_in_play": False, "is_zone": True,
            },
            {
                "pitch_name": "4-Seam Fastball", "speed": 95.0, "spin": 2350,
                "ivb": 16.0, "hb": 10.0, "is_whiff": False, "is_called": True,
                "is_foul": False, "is_in_play": False, "is_zone": True,
            },
            {
                "pitch_name": "4-Seam Fastball", "speed": 94.0, "spin": 2300,
                "ivb": 17.0, "hb": 9.0, "is_whiff": False, "is_called": False,
                "is_foul": True, "is_in_play": False, "is_zone": False,
            },
            {
                "pitch_name": "4-Seam Fastball", "speed": 95.0, "spin": 2350,
                "ivb": 17.0, "hb": 9.0, "is_whiff": False, "is_called": False,
                "is_foul": False, "is_in_play": True, "is_zone": True,
            },
        ]

        table = _build_statcast_table(pitches)
        self.assertEqual(len(table), 1)
        row = table[0]

        self.assertEqual(row["count"], 4)
        self.assertEqual(row["velo_avg"], 95.0)
        self.assertEqual(row["velo_max"], 96.0)
        self.assertEqual(row["spin_avg"], 2350)
        self.assertEqual(row["ivb"], 17.0)
        self.assertEqual(row["hb"], 9.0)

        # Swings: whiff(1) + foul(1) + in_play(1) = 3
        # Whiff%: 1 / 3 = 33.3%
        self.assertEqual(row["whiff_pct"], "33.3%")

        # CSW: called(1) + whiff(1) = 2 de 4 = 50.0%
        self.assertEqual(row["csw_pct"], "50.0%")

        # Zone: 3 de 4 = 75.0%
        self.assertEqual(row["zone_pct"], "75.0%")

    def test_pbp_summary_math(self):
        """Valida la tabla de destinos de pitcheos y los KPIs agregados."""
        pitches = [
            {"is_ball": True, "is_called": False, "is_whiff": False, "is_foul": False, "is_in_play": False, "is_strike": False, "balls": 0, "strikes": 0},
            {"is_ball": False, "is_called": True, "is_whiff": False, "is_foul": False, "is_in_play": False, "is_strike": True, "balls": 0, "strikes": 0},
            {"is_ball": False, "is_called": False, "is_whiff": True, "is_foul": False, "is_in_play": False, "is_strike": True, "balls": 1, "strikes": 1},
            {"is_ball": False, "is_called": False, "is_whiff": False, "is_foul": True, "is_in_play": False, "is_strike": True, "balls": 1, "strikes": 2},
            {"is_ball": False, "is_called": False, "is_whiff": False, "is_foul": False, "is_in_play": True, "is_strike": True, "balls": 2, "strikes": 2},
        ]

        table, kpis = _build_pbp_summary(pitches)
        self.assertEqual(len(table), 5)
        self.assertEqual(kpis["total_pitches"], 5)
        self.assertEqual(kpis["strikes"], 4)
        self.assertEqual(kpis["strike_pct"], "80.0%")
        # CSW%: (called: 1 + whiff: 1) / 5 = 40.0%
        self.assertEqual(kpis["csw_pct"], "40.0%")
        # Whiff%: whiff: 1 / swings: (whiff:1 + foul:1 + in_play:1 = 3) = 33.3%
        self.assertEqual(kpis["whiff_pct"], "33.3%")
        # First pitch strikes: 2 first pitches (1 ball, 1 called strike) -> 50.0%
        self.assertEqual(kpis["fps_pct"], "50.0%")

    def test_inning_workload(self):
        """Valida el cálculo de carga por entrada."""
        pitches = [
            {"inning": 1, "is_strike": True, "is_whiff": True, "leverage_index": 1.2},
            {"inning": 1, "is_strike": False, "is_whiff": False, "leverage_index": 1.0},
            {"inning": 2, "is_strike": True, "is_whiff": False, "leverage_index": 1.8},
        ]
        workload = _build_inning_workload(pitches)
        self.assertEqual(len(workload), 2)
        self.assertEqual(workload[0]["inning"], 1)
        self.assertEqual(workload[0]["pitches"], 2)
        self.assertEqual(workload[0]["strikes"], 1)
        self.assertEqual(workload[0]["avg_li"], 1.1)

        self.assertEqual(workload[1]["inning"], 2)
        self.assertEqual(workload[1]["pitches"], 1)
        self.assertEqual(workload[1]["strikes"], 1)
        self.assertEqual(workload[1]["avg_li"], 1.8)

    def test_platoon_splits(self):
        """Valida los splits vs bateadores zurdos y derechos."""
        pitches = [
            {"stand": "L", "is_called": True, "is_whiff": False, "is_foul": False, "is_in_play": False, "is_strike": True},
            {"stand": "L", "is_called": False, "is_whiff": True, "is_foul": False, "is_in_play": False, "is_strike": True},
            {"stand": "R", "is_called": False, "is_whiff": False, "is_foul": False, "is_in_play": False, "is_strike": False},
        ]
        splits = _build_platoon_splits(pitches)
        self.assertIn("vs_lhb", splits)
        self.assertIn("vs_rhb", splits)
        self.assertEqual(splits["vs_lhb"]["pitches"], 2)
        self.assertEqual(splits["vs_lhb"]["csw_pct"], "100.0%")
        self.assertEqual(splits["vs_rhb"]["pitches"], 1)
    def test_get_pitcher_by_id_various_teams(self):
        """Valida que get_pitcher_by_id resuelva lanzadores de diversas franquicias LVBP y MLB."""
        from core.pitching_engine import get_pitcher_by_id

        # 1. Erick Leal (CAR)
        p_leal = get_pitcher_by_id(612797)
        self.assertIsNotNone(p_leal)
        self.assertIn("Leal", p_leal["name"])
        self.assertTrue(p_leal["has_lvbp_history"])
        self.assertTrue(p_leal["has_caracas_history"])

        # 2. Ricardo Sánchez (MAG)
        p_sanchez = get_pitcher_by_id(645307)
        self.assertIsNotNone(p_sanchez)
        self.assertIn("S", p_sanchez["name"])
        self.assertTrue(p_sanchez["has_lvbp_history"])
        self.assertEqual(p_sanchez["lvbp_team_abbr"], "MAG")

        # 3. Max Castillo (LAR)
        p_castillo = get_pitcher_by_id(666721)
        self.assertIsNotNone(p_castillo)
        self.assertIn("Castillo", p_castillo["name"])
        self.assertTrue(p_castillo["has_lvbp_history"])
        self.assertEqual(p_castillo["lvbp_team_abbr"], "LAR")

        # 4. Albert Suárez (MLB / Caracas reserve)
        p_suarez = get_pitcher_by_id(544150)
        self.assertIsNotNone(p_suarez)
        self.assertIn("Su", p_suarez["name"])
        self.assertTrue(p_suarez["has_caracas_history"])

    def test_search_pitchers_numeric_id_query(self):
        """Valida que search_pitchers soporte consultas por ID numérico en string."""
        res = search_pitchers("645307")
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["id"], 645307)
        self.assertEqual(res[0]["lvbp_team_abbr"], "MAG")

    def test_get_lvbp_pitcher_game_logs_multiple_pitchers(self):
        """Valida que _get_lvbp_pitcher_game_logs extraiga salidas para lanzadores de distintas franquicias."""
        from core.pitching_engine import _get_lvbp_pitcher_game_logs

        # Ricardo Sánchez (MAG) en 2025
        logs_mag = _get_lvbp_pitcher_game_logs(645307, 2025)
        self.assertTrue(len(logs_mag) > 0)
        self.assertEqual(logs_mag[0]["league"], "LVBP")

        # Max Castillo (LAR) en 2025
        logs_lar = _get_lvbp_pitcher_game_logs(666721, 2025)
        self.assertTrue(len(logs_lar) > 0)
        self.assertEqual(logs_lar[0]["league"], "LVBP")

    def test_get_mexico_pitcher_game_logs_and_decisions(self):
        """Valida que get_pitcher_game_logs con branch='mexico' extraiga salidas y decisiones (W, L, SV, HLD)."""
        from core.pitching_engine import get_pitcher_game_logs

        # Erick Leal (612797) en México 2024
        logs_mex = get_pitcher_game_logs(612797, 2024, branch="mexico", phase="all")
        self.assertTrue(len(logs_mex) > 0)
        self.assertEqual(logs_mex[0]["league"], "México")
        decisions = [g["decision"] for g in logs_mex if g.get("decision")]
        self.assertTrue(len(decisions) > 0)
        self.assertIn("W", decisions)


if __name__ == "__main__":
    unittest.main()
