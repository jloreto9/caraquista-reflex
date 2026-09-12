# tests/test_matchup360_overall.py
"""
test_matchup360_overall.py
--------------------------
Suite de pruebas unitarias y de integración para:
1. Estadísticas Globales de la LVBP y Filtro por Franquicia en /individuales:
   - Carga del universo completo de jugadores (8 franquicias) con team_id, team_name y team_abbr.
   - Opciones de equipo completas y filtro predeterminado en "Leones del Caracas".
   - Filtrado dinámico por franquicia y vista "Toda la LVBP (Overall)" en Bateo, Pitcheo y Fildeo.
   - Recálculo dinámico de tarjetas KPI según el equipo seleccionado.
2. Comparador Head-to-Head (H2H) Matchup 360 (Sabermetría Pura LVBP / Cero Statcast):
   - Selector de jugadores con formato "Nombre (EQUIPO)".
   - Resolución resiliente con helper `_find_player`.
   - Secciones categorizadas en tabla H2H (Sabermetría & Valor, Rate, Volumen) con banderas is_header.
   - Radar Polar de 8 dimensiones sabermétricas normalizadas en percentiles [0, 100] contra el universo calificado.
   - Prohibición estricta de métricas Statcast inexistentes en LVBP (Exit Velocity, Launch Angle, Barrel%, etc.).
   - Tarjetas Hero con logos oficiales de franquicia y veredicto analítico en español.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from republicaraquistapp.state.individuales_state import IndividualesState
from core.supabase_client import get_batting_stats, get_pitching_stats


class TestOverallStatsAndTeamFiltering(unittest.TestCase):
    """Pruebas de carga global de la liga y filtros por equipo."""

    def setUp(self):
        self.state = IndividualesState()
        self.sample_batting = [
            {
                "player_id": 101,
                "player_name": "José Rondón",
                "team_id": 696,
                "team_name": "Leones del Caracas",
                "team_abbr": "CAR",
                "position": "3B",
                "ab": 120,
                "pa": 140,
                "h": 38,
                "doubles": 8,
                "triples": 1,
                "hr": 11,
                "rbi": 35,
                "r": 28,
                "bb": 18,
                "so": 25,
                "sb": 2,
                "avg": 0.317,
                "avg_str": ".317",
                "obp": 0.407,
                "obp_str": ".407",
                "slg": 0.675,
                "slg_str": ".675",
                "ops": 1.082,
                "ops_str": "1.082",
                "iso": 0.358,
                "iso_str": ".358",
                "babip": 0.321,
                "babip_str": ".321",
                "woba": 0.445,
                "woba_str": ".445",
                "wrc_plus": 178,
                "wrc_color": "green",
                "headshot": "/logo.png",
            },
            {
                "player_id": 102,
                "player_name": "Renato Núñez",
                "team_id": 697,
                "team_name": "Navegantes del Magallanes",
                "team_abbr": "MAG",
                "position": "1B",
                "ab": 130,
                "pa": 150,
                "h": 40,
                "doubles": 7,
                "triples": 0,
                "hr": 14,
                "rbi": 42,
                "r": 30,
                "bb": 15,
                "so": 32,
                "sb": 0,
                "avg": 0.308,
                "avg_str": ".308",
                "obp": 0.380,
                "obp_str": ".380",
                "slg": 0.685,
                "slg_str": ".685",
                "ops": 1.065,
                "ops_str": "1.065",
                "iso": 0.377,
                "iso_str": ".377",
                "babip": 0.310,
                "babip_str": ".310",
                "woba": 0.435,
                "woba_str": ".435",
                "wrc_plus": 170,
                "wrc_color": "green",
                "headshot": "/logo.png",
            },
            {
                "player_id": 103,
                "player_name": "Alberth Martínez",
                "team_id": 697,
                "team_name": "Navegantes del Magallanes",
                "team_abbr": "MAG",
                "position": "LF",
                "ab": 110,
                "pa": 125,
                "h": 32,
                "doubles": 6,
                "triples": 0,
                "hr": 8,
                "rbi": 25,
                "r": 20,
                "bb": 12,
                "so": 28,
                "sb": 1,
                "avg": 0.291,
                "avg_str": ".291",
                "obp": 0.360,
                "obp_str": ".360",
                "slg": 0.527,
                "slg_str": ".527",
                "ops": 0.887,
                "ops_str": ".887",
                "iso": 0.236,
                "iso_str": ".236",
                "babip": 0.324,
                "babip_str": ".324",
                "woba": 0.375,
                "woba_str": ".375",
                "wrc_plus": 130,
                "wrc_color": "green",
                "headshot": "/logo.png",
            },
        ]
        self.state.batting_data_raw = self.sample_batting

    def test_team_options_structure(self):
        """Verifica que team_options incluya 'Toda la LVBP (Overall)' y las 8 franquicias."""
        options = self.state.team_options
        self.assertIn("Toda la LVBP (Overall)", options)
        self.assertIn("Leones del Caracas", options)
        self.assertIn("Navegantes del Magallanes", options)
        self.assertIn("Tiburones de La Guaira", options)
        self.assertIn("Cardenales de Lara", options)
        self.assertIn("Águilas del Zulia", options)
        self.assertIn("Tigres de Aragua", options)
        self.assertIn("Caribes de Anzoátegui", options)
        self.assertIn("Bravos de Margarita", options)
        self.assertEqual(len(options), 9)

    def test_default_filters_are_overall(self):
        """El filtro por defecto para Bateo, Pitcheo y Fildeo debe ser 'Toda la LVBP (Overall)'."""
        self.assertEqual(self.state.selected_batting_team, "Toda la LVBP (Overall)")
        self.assertEqual(self.state.selected_pitching_team, "Toda la LVBP (Overall)")
        self.assertEqual(self.state.selected_fielding_team, "Toda la LVBP (Overall)")

    def test_filtered_batting_by_default_shows_all_lvbp(self):
        """Al estar por defecto en 'Toda la LVBP (Overall)', deben mostrarse todos los jugadores."""
        self.state.min_ab = 0
        filtered = self.state.filtered_batting
        self.assertEqual(len(filtered), 3)

    def test_filtered_batting_rival_team(self):
        """Al seleccionar 'Navegantes del Magallanes', solo deben filtrarse sus jugadores."""
        self.state.min_ab = 0
        self.state.selected_batting_team = "Navegantes del Magallanes"
        filtered = self.state.filtered_batting
        self.assertEqual(len(filtered), 2)
        for p in filtered:
            self.assertEqual(p["team_name"], "Navegantes del Magallanes")
            self.assertEqual(p["team_abbr"], "MAG")

    def test_filtered_batting_caracas_only_when_filtered(self):
        """Al filtrar explícitamente por 'Leones del Caracas', solo deben mostrarse sus jugadores."""
        self.state.min_ab = 0
        self.state.selected_batting_team = "Leones del Caracas"
        filtered = self.state.filtered_batting
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["player_name"], "José Rondón")
        self.assertEqual(filtered[0]["team_abbr"], "CAR")

    def test_dynamic_batting_kpis_recalculated_by_team(self):
        """Las tarjetas KPI de bateo deben recalcular líderes según el equipo seleccionado."""
        self.state.selected_batting_team = "Leones del Caracas"
        self.state.update_batting_kpis()
        self.assertEqual(self.state.batting_kpis["hr_player"], "José Rondón")
        self.assertEqual(self.state.batting_kpis["hr_val"], "11")

        # Al cambiar a Magallanes, el líder de HR es Renato Núñez con 14
        self.state.selected_batting_team = "Navegantes del Magallanes"
        self.state.update_batting_kpis()
        self.assertEqual(self.state.batting_kpis["hr_player"], "Renato Núñez")
        self.assertEqual(self.state.batting_kpis["hr_val"], "14")


class TestMatchup360HeadToHead(unittest.TestCase):
    """Pruebas para el comparador Head-to-Head Matchup 360 y radar polar sabermétrico."""

    def setUp(self):
        self.state = IndividualesState()
        self.state.batting_data_raw = [
            {
                "player_id": 201,
                "player_name": "José Rondón",
                "team_id": 696,
                "team_name": "Leones del Caracas",
                "team_abbr": "CAR",
                "position": "3B",
                "ab": 140,
                "pa": 160,
                "h": 45,
                "doubles": 10,
                "triples": 1,
                "hr": 14,
                "rbi": 42,
                "r": 35,
                "bb": 20,
                "so": 30,
                "sb": 3,
                "avg": 0.321,
                "avg_str": ".321",
                "obp": 0.406,
                "obp_str": ".406",
                "slg": 0.707,
                "slg_str": ".707",
                "ops": 1.113,
                "ops_str": "1.113",
                "iso": 0.386,
                "iso_str": ".386",
                "babip": 0.323,
                "babip_str": ".323",
                "woba": 0.452,
                "woba_str": ".452",
                "wrc_plus": 182,
                "headshot": "/rondon.png",
            },
            {
                "player_id": 202,
                "player_name": "Renato Núñez",
                "team_id": 697,
                "team_name": "Navegantes del Magallanes",
                "team_abbr": "MAG",
                "position": "1B",
                "ab": 150,
                "pa": 170,
                "h": 46,
                "doubles": 9,
                "triples": 0,
                "hr": 16,
                "rbi": 45,
                "r": 32,
                "bb": 18,
                "so": 38,
                "sb": 0,
                "avg": 0.307,
                "avg_str": ".307",
                "obp": 0.376,
                "obp_str": ".376",
                "slg": 0.687,
                "slg_str": ".687",
                "ops": 1.063,
                "ops_str": "1.063",
                "iso": 0.380,
                "iso_str": ".380",
                "babip": 0.313,
                "babip_str": ".313",
                "woba": 0.431,
                "woba_str": ".431",
                "wrc_plus": 168,
                "headshot": "/nunez.png",
            },
        ]
        self.state.available_batters = ["José Rondón (CAR)", "Renato Núñez (MAG)"]

    def test_available_batters_formatted_with_team_abbr(self):
        """Los selectores de jugadores deben formatearse como 'Nombre (EQUIPO)'."""
        for b in self.state.available_batters:
            self.assertRegex(b, r"^.+ \([A-Z]{2,4}\)$")

    def test_find_player_helper(self):
        """_find_player debe resolver correctamente tanto con 'Nombre (EQUIPO)' como con 'Nombre'."""
        p1 = self.state._find_player("José Rondón (CAR)", self.state.batting_data_raw)
        self.assertIsNotNone(p1)
        self.assertEqual(p1["player_name"], "José Rondón")

        p2 = self.state._find_player("Renato Núñez", self.state.batting_data_raw)
        self.assertIsNotNone(p2)
        self.assertEqual(p2["player_name"], "Renato Núñez")

    def test_h2h_comparison_generates_categorized_rows(self):
        """La tabla H2H debe estructurarse en 4 categorías sabermétricas 360 con encabezados."""
        self.state.compare_type = "Bateadores"
        self.state.selected_player_1 = "José Rondón (CAR)"
        self.state.selected_player_2 = "Renato Núñez (MAG)"
        self.state.update_h2h_comparison()

        rows = self.state.h2h_rows
        self.assertGreater(len(rows), 0)

        # Verificar presencia de las 4 categorías 360
        headers = [r["metric"] for r in rows if r.get("is_header")]
        self.assertIn("⚡ Ofensiva & Sabermetría", headers)
        self.assertIn("🔢 Estadísticas de Volumen", headers)
        self.assertIn("🏃 Corrido de Bases", headers)
        self.assertIn("🧤 Defensa & Fildeo", headers)

        # Verificar nombres limpios de métricas (sin sufijos redundantes)
        metrics = [r["metric"] for r in rows if not r.get("is_header")]
        self.assertIn("wOBA", metrics)
        self.assertIn("wRC+", metrics)
        self.assertIn("ISO", metrics)
        self.assertIn("OPS", metrics)
        self.assertIn("OBP", metrics)
        self.assertIn("SLG", metrics)
        self.assertIn("AVG", metrics)
        self.assertIn("BB%", metrics)
        self.assertIn("K%", metrics)
        self.assertNotIn("wOBA Sabermétrico", metrics)
        self.assertNotIn("wRC+ Normalizado", metrics)
        self.assertNotIn("Poder Aislado (ISO)", metrics)

        # Verificar volumen expandido
        self.assertTrue(any("Sencillos (1B)" in m for m in metrics))
        self.assertTrue(any("Dobles (2B)" in m for m in metrics))
        self.assertTrue(any("Bases Totales (TB)" in m for m in metrics))
        self.assertTrue(any("Extrabases (XBH)" in m for m in metrics))
        self.assertTrue(any("Apariciones al Plato (PA)" in m for m in metrics))

        # Verificar corrido de bases
        self.assertTrue(any("Bases Robadas (SB)" in m for m in metrics))
        self.assertTrue(any("Atrapado Robando (CS)" in m for m in metrics))
        self.assertTrue(any("Efectividad de Robo (SB%)" in m for m in metrics))

        # Verificar fildeo / defensa
        self.assertTrue(any("Posición Principal" in m for m in metrics))
        self.assertTrue(any("Lances Totales (TC)" in m for m in metrics))
        self.assertTrue(any("Porcentaje de Fildeo (FPCT)" in m for m in metrics))

    def test_pitching_h2h_comparison_360(self):
        """Verifica que el comparador H2H de lanzadores cubra Dominio, Rate y Volumen expandido."""
        self.state.compare_type = "Lanzadores"
        self.state.pitching_data_raw = [
            {
                "player_id": 301,
                "player_name": "Jhoulys Chacín",
                "team_id": 696,
                "team_name": "Leones del Caracas",
                "team_abbr": "CAR",
                "ip": 35.0,
                "ip_str": "35.0",
                "h": 30,
                "r": 14,
                "er": 12,
                "bb": 10,
                "so": 32,
                "hr": 3,
                "g": 8,
                "gs": 8,
                "w": 3,
                "l": 2,
                "sv": 0,
                "era": 3.09,
                "era_str": "3.09",
                "whip": 1.14,
                "whip_str": "1.14",
                "fip": 3.25,
                "fip_str": "3.25",
                "k9": 8.23,
                "k9_str": "8.23",
                "bb9": 2.57,
                "bb9_str": "2.57",
                "k_bb": 3.20,
                "k_bb_str": "3.20",
                "headshot": "/chacin.png",
            },
            {
                "player_id": 302,
                "player_name": "Erick Leal",
                "team_id": 697,
                "team_name": "Navegantes del Magallanes",
                "team_abbr": "MAG",
                "ip": 32.0,
                "ip_str": "32.0",
                "h": 34,
                "r": 16,
                "er": 15,
                "bb": 12,
                "so": 28,
                "hr": 4,
                "g": 7,
                "gs": 7,
                "w": 2,
                "l": 3,
                "sv": 0,
                "era": 4.22,
                "era_str": "4.22",
                "whip": 1.44,
                "whip_str": "1.44",
                "fip": 4.10,
                "fip_str": "4.10",
                "k9": 7.88,
                "k9_str": "7.88",
                "bb9": 3.38,
                "bb9_str": "3.38",
                "k_bb": 2.33,
                "k_bb_str": "2.33",
                "headshot": "/leal.png",
            },
        ]
        self.state.selected_player_1 = "Jhoulys Chacín (CAR)"
        self.state.selected_player_2 = "Erick Leal (MAG)"
        self.state.update_h2h_comparison()

        rows = self.state.h2h_rows
        self.assertGreater(len(rows), 0)
        headers = [r["metric"] for r in rows if r.get("is_header")]
        self.assertIn("⚡ Sabermetría & Dominio", headers)
        self.assertIn("📊 Estadísticas de Rate", headers)
        self.assertIn("🔢 Estadísticas de Volumen", headers)

        metrics = [r["metric"] for r in rows if not r.get("is_header")]
        self.assertTrue(any("FIP" in m for m in metrics))
        self.assertTrue(any("WHIP" in m for m in metrics))
        self.assertTrue(any("Hits por 9 (H/9)" in m for m in metrics))
        self.assertTrue(any("Carreras por 9 (R/9)" in m for m in metrics))
        self.assertTrue(any("Victorias (W)" in m for m in metrics))
        self.assertTrue(any("Derrotas (L)" in m for m in metrics))

    def test_strictly_no_statcast_in_h2h_rows(self):
        """No debe incluirse ninguna métrica de Statcast (EV, Launch Angle, Barrel%, Sprint Speed)."""
        self.state.compare_type = "Bateadores"
        self.state.selected_player_1 = "José Rondón (CAR)"
        self.state.selected_player_2 = "Renato Núñez (MAG)"
        self.state.update_h2h_comparison()

        metrics = [r["metric"].lower() for r in self.state.h2h_rows]
        prohibited = [
            "exit velocity",
            "velocidad de salida",
            "launch angle",
            "ángulo de lanzamiento",
            "barrel",
            "barriles",
            "hard hit",
            "sprint speed",
            "xwoba",
            "xba",
            "xera",
        ]
        for metric in metrics:
            for p in prohibited:
                self.assertNotIn(p, metric, f"Métrica Statcast prohibida '{p}' detectada en '{metric}'")

    def test_player_cards_contain_team_logo_and_metadata(self):
        """Las tarjetas Hero de los jugadores deben contener logo de equipo, badge y KPIs."""
        self.state.compare_type = "Bateadores"
        self.state.selected_player_1 = "José Rondón (CAR)"
        self.state.selected_player_2 = "Renato Núñez (MAG)"
        self.state.update_h2h_comparison()

        card1 = self.state.player_1_card
        self.assertEqual(card1["name"], "José Rondón")
        self.assertIn("CAR", card1["team"])
        self.assertTrue("mlbstatic" in card1["team_logo"] or "696" in card1["team_logo"] or "assets" in card1["team_logo"])
        self.assertNotEqual(card1["kpi_1"], "-")

        card2 = self.state.player_2_card
        self.assertEqual(card2["name"], "Renato Núñez")
        self.assertIn("MAG", card2["team"])
        self.assertTrue("mlbstatic" in card2["team_logo"] or "697" in card2["team_logo"] or "assets" in card2["team_logo"])
        self.assertNotEqual(card2["kpi_1"], "-")

    def test_radar_chart_figure_8_axes_and_percentiles(self):
        """El radar polar debe tener exactamente 8 ejes sabermétricos y percentiles acotados [0, 100]."""
        self.state.compare_type = "Bateadores"
        self.state.selected_player_1 = "José Rondón (CAR)"
        self.state.selected_player_2 = "Renato Núñez (MAG)"

        fig = self.state.radar_chart_figure
        self.assertIsInstance(fig, go.Figure)

        # Debe contener dos trazas (Jugador 1 y Jugador 2)
        self.assertEqual(len(fig.data), 2)
        trace1, trace2 = fig.data[0], fig.data[1]

        expected_axes = ["AVG", "OBP", "SLG", "OPS", "wOBA", "wRC+", "ISO", "BB%"]
        # En gráficos radar polar cerrados, la última coordenada repite la primera
        theta1 = list(trace1.theta)
        for axis in expected_axes:
            self.assertTrue(
                any(axis in t for t in theta1),
                f"El eje sabermétrico '{axis}' debe estar presente en theta: {theta1}"
            )

        # Todos los valores r deben ser percentiles dentro de [0, 100]
        for r_val in trace1.r:
            self.assertGreaterEqual(r_val, 0)
            self.assertLessEqual(r_val, 100)

        for r_val in trace2.r:
            self.assertGreaterEqual(r_val, 0)
            self.assertLessEqual(r_val, 100)

    def test_h2h_verdict_in_spanish_with_leader(self):
        """El veredicto sabermétrico debe redactarse en español y declarar la ventaja analítica."""
        self.state.compare_type = "Bateadores"
        self.state.selected_player_1 = "José Rondón (CAR)"
        self.state.selected_player_2 = "Renato Núñez (MAG)"
        self.state.update_h2h_comparison()

        verdict = self.state.h2h_verdict
        self.assertIn("Veredicto Sabermétrico", verdict)
        self.assertTrue("ventaja" in verdict or "lidera" in verdict or "balance" in verdict)


class TestSupabaseClientLeaguePoolContract(unittest.TestCase):
    """Verifica que el cliente Supabase soporte la carga global con team_id=None."""

    @patch("core.supabase_client.init_supabase")
    def test_get_batting_stats_team_id_none(self, mock_client_getter):
        """get_batting_stats con team_id=None no debe filtrar por team_id y debe enriquecer equipos."""
        mock_sb = MagicMock()
        mock_client_getter.return_value = mock_sb

        # Mock de respuesta Supabase con jugadores de Caracas (695) y Magallanes (696)
        mock_query = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value = mock_query
        mock_query.execute.return_value.data = [
            {"player_id": 1, "player_name": "Rondón", "team_id": 695, "ab": 100, "h": 30, "hr": 10},
            {"player_id": 2, "player_name": "Núñez", "team_id": 696, "ab": 100, "h": 30, "hr": 12},
        ]

        df = get_batting_stats(season=2025, team_id=None, limit=200)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("team_abbr", df.columns)
        self.assertIn("team_name", df.columns)
        self.assertEqual(df.loc[df["player_id"] == 1, "team_abbr"].values[0], "CAR")
        self.assertEqual(df.loc[df["player_id"] == 2, "team_abbr"].values[0], "MAG")


class TestMatchup360CardImageExport(unittest.TestCase):
    """Verifica la generación de la tarjeta gráfica Matchup 360 (PNG) y créditos."""

    def test_build_matchup_image_png_header(self):
        """La función build_matchup_image debe generar bytes de PNG válidos."""
        from core.matchup_card import build_matchup_image

        p1 = {"name": "José Rondón", "badge": "CAR", "pos": "OF", "headshot": None, "team_logo": None}
        p2 = {"name": "Renato Núñez", "badge": "MAG", "pos": "1B", "headshot": None, "team_logo": None}
        rows = [
            {"category": "Ofensiva", "metric": "wOBA", "val_1": ".412", "val_2": ".395", "winner": "José Rondón (CAR)", "is_header": False},
            {"category": "Ofensiva", "metric": "wRC+", "val_1": "155", "val_2": "142", "winner": "José Rondón (CAR)", "is_header": False},
            {"category": "Volumen", "metric": "HR", "val_1": "12", "val_2": "14", "winner": "Renato Núñez (MAG)", "is_header": False},
        ]
        png_bytes = build_matchup_image(p1, p2, rows, is_batter=True, season=2025)
        self.assertIsInstance(png_bytes, bytes)
        self.assertTrue(len(png_bytes) > 5000)
        # Magic bytes oficiales de formato PNG (\x89PNG\r\n\x1a\n)
        self.assertEqual(png_bytes[:8], b"\x89PNG\r\n\x1a\n")

    def test_download_matchup_card_event_spec(self):
        """IndividualesState.download_matchup_card() debe retornar un EventSpec de descarga de Reflex."""
        state = IndividualesState()
        state.batting_data_raw = [
            {
                "player_id": 1, "player_name": "José Rondón", "team_id": 695, "team_abbr": "CAR",
                "team_name": "Leones del Caracas", "headshot": "", "role": "Bateador", "pos": "OF",
                "ab": 120, "pa": 140, "h": 40, "h_1b": 24, "h_2b": 8, "h_3b": 1, "hr": 7, "rbi": 28,
                "r": 25, "bb": 18, "so": 22, "hbp": 1, "sf": 1, "sb": 3, "cs": 1,
                "avg": 0.333, "avg_str": ".333", "obp": 0.420, "obp_str": ".420", "slg": 0.592, "slg_str": ".592",
                "ops": 1.012, "ops_str": "1.012", "iso": 0.258, "iso_str": ".258", "babip": 0.363, "babip_str": ".363",
                "woba": 0.435, "woba_str": ".435", "wrc_plus": 165, "bb_pct": 12.9, "bb_pct_str": "12.9%", "k_pct": 15.7, "k_pct_str": "15.7%",
            },
            {
                "player_id": 2, "player_name": "Renato Núñez", "team_id": 696, "team_abbr": "MAG",
                "team_name": "Navegantes del Magallanes", "headshot": "", "role": "Bateador", "pos": "1B",
                "ab": 130, "pa": 150, "h": 42, "h_1b": 22, "h_2b": 9, "h_3b": 0, "hr": 11, "rbi": 35,
                "r": 27, "bb": 16, "so": 28, "hbp": 2, "sf": 2, "sb": 0, "cs": 0,
                "avg": 0.323, "avg_str": ".323", "obp": 0.400, "obp_str": ".400", "slg": 0.654, "slg_str": ".654",
                "ops": 1.054, "ops_str": "1.054", "iso": 0.331, "iso_str": ".331", "babip": 0.341, "babip_str": ".341",
                "woba": 0.442, "woba_str": ".442", "wrc_plus": 170, "bb_pct": 10.7, "bb_pct_str": "10.7%", "k_pct": 18.7, "k_pct_str": "18.7%",
            }
        ]
        state.selected_player_1 = "José Rondón (CAR)"
        state.selected_player_2 = "Renato Núñez (MAG)"
        state.update_h2h_comparison()

        event = state.download_matchup_card()
        self.assertIsNotNone(event)
        self.assertIn("EventSpec", type(event).__name__)

    def test_percentile_table_rows_batters(self):
        """Verifica que percentile_table_rows retorne 8 dimensiones sabermétricas con percentiles 0-100."""
        state = IndividualesState()
        state.batting_data_raw = [
            {
                "player_id": 1, "player_name": "Harold Castro", "team_id": 695, "team_abbr": "CAR",
                "ab": 100, "pa": 120, "avg": 0.352, "avg_str": ".352", "obp": 0.387, "obp_str": ".387",
                "slg": 0.471, "slg_str": ".471", "ops": 0.938, "ops_str": "0.938", "woba": 0.384, "woba_str": ".384",
                "wrc_plus": 114, "iso": 0.183, "iso_str": ".183", "bb_pct": 4.6, "bb_pct_str": "4.6%",
            },
            {
                "player_id": 2, "player_name": "Hernán Pérez", "team_id": 696, "team_abbr": "ARA",
                "ab": 120, "pa": 140, "avg": 0.314, "avg_str": ".314", "obp": 0.384, "obp_str": ".384",
                "slg": 0.522, "slg_str": ".522", "ops": 0.967, "ops_str": "0.967", "woba": 0.393, "woba_str": ".393",
                "wrc_plus": 125, "iso": 0.204, "iso_str": ".204", "bb_pct": 6.9, "bb_pct_str": "6.9%",
            },
        ]
        state.compare_type = "Bateadores"
        state.selected_player_1 = "Harold Castro (CAR)"
        state.selected_player_2 = "Hernán Pérez (ARA)"

        rows = state.percentile_table_rows
        self.assertEqual(len(rows), 8)
        metrics = [r["metric"] for r in rows]
        self.assertIn("Contacto (AVG)", metrics)
        self.assertIn("Producción (OPS)", metrics)
        self.assertIn("wOBA", metrics)
        self.assertIn("wRC+", metrics)
        for r in rows:
            self.assertIn("pct_1", r)
            self.assertIn("pct_2", r)
            self.assertIn("leader", r)
            self.assertIn(r["leader_scheme"], ["amber", "blue", "gray"])
            self.assertTrue(0 <= r["pct_1"] <= 100)
            self.assertTrue(0 <= r["pct_2"] <= 100)

    def test_winner_shortened_names_format(self):
        """Verifica que los ganadores en h2h_rows usen el formato abreviado compacto ('H. Castro (CAR)')."""
        state = IndividualesState()
        state.batting_data_raw = [
            {
                "player_id": 1, "player_name": "Harold Castro", "team_id": 695, "team_abbr": "CAR", "headshot": "",
                "ab": 100, "pa": 120, "h": 35, "hr": 6, "rbi": 25, "r": 20, "bb": 8, "so": 15,
                "avg": 0.350, "avg_str": ".350", "obp": 0.400, "obp_str": ".400",
                "slg": 0.550, "slg_str": ".550", "ops": 0.950, "ops_str": "0.950",
                "woba": 0.400, "woba_str": ".400", "wrc_plus": 140, "iso": 0.200, "iso_str": ".200",
                "babip": 0.350, "babip_str": ".350",
            },
            {
                "player_id": 2, "player_name": "Hernán Pérez", "team_id": 696, "team_abbr": "ARA", "headshot": "",
                "ab": 100, "pa": 120, "h": 25, "hr": 4, "rbi": 15, "r": 12, "bb": 6, "so": 20,
                "avg": 0.250, "avg_str": ".250", "obp": 0.310, "obp_str": ".310",
                "slg": 0.420, "slg_str": ".420", "ops": 0.730, "ops_str": "0.730",
                "woba": 0.320, "woba_str": ".320", "wrc_plus": 95, "iso": 0.170, "iso_str": ".170",
                "babip": 0.270, "babip_str": ".270",
            },
        ]
        state.compare_type = "Bateadores"
        state.selected_player_1 = "Harold Castro (CAR)"
        state.selected_player_2 = "Hernán Pérez (ARA)"
        state.update_h2h_comparison()

        avg_row = next((r for r in state.h2h_rows if r.get("metric") == "AVG"), None)
        self.assertIsNotNone(avg_row)
        self.assertEqual(avg_row["winner"], "H. Castro (CAR)")



if __name__ == "__main__":
    unittest.main()

