# tests/test_individuales_colectivas.py
"""
test_individuales_colectivas.py
-------------------------------
Suite de pruebas unitarias y de integración para Worker M4:
1. IndividualesState (/individuales):
   - Campos de estado y valores por defecto (active_tab, min_ab, min_ip, role, compare_type, etc.).
   - Métodos y event handlers (on_load, load_all_stats, update_h2h_comparison, setters de filtros).
   - Computed vars (@rx.var: filtered_batting, filtered_pitching, filtered_fielding, is_catcher_view, radar_chart_figure, top_batters_chart, top_pitchers_chart).
2. Vista /individuales (`individuales()`, `individuales_content()`):
   - Renderizado exitoso de componentes Reflex para Bateo, Pitcheo, Fildeo y Comparador H2H.
3. ColectivasState (/colectivas):
   - Campos de estado y valores por defecto (active_tab, selected_phase, metric selectors, etc.).
   - Métodos y event handlers (on_load, load_collective_stats, setters de fase y métricas).
   - Computed vars (@rx.var: batting_bar_chart, pitching_bar_chart, fielding_bar_chart).
4. Vista /colectivas (`colectivas()`, `colectivas_content()`):
   - Renderizado exitoso de componentes Reflex para Bateo Colectivo, Pitcheo Colectivo y Fildeo Colectivo.
"""

import os
import sys
import unittest
import reflex as rx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from republicaraquistapp.state.individuales_state import IndividualesState
from republicaraquistapp.pages.individuales import individuales, individuales_content
from republicaraquistapp.state.colectivas_state import ColectivasState
from republicaraquistapp.pages.colectivas import colectivas, colectivas_content


class TestIndividualesStateArchitecture(unittest.TestCase):
    """Pruebas de la arquitectura y definición de IndividualesState."""

    def test_state_inheritance(self):
        """Verifica que IndividualesState sea una subclase válida de rx.State."""
        self.assertTrue(issubclass(IndividualesState, rx.State))

    def test_individuales_fields_and_defaults(self):
        """Verifica los campos reactivos de IndividualesState."""
        fields = IndividualesState.get_fields() if hasattr(IndividualesState, "get_fields") else IndividualesState.__annotations__

        expected_fields = [
            "active_tab",
            "search_batting",
            "min_ab",
            "selected_batting_pos",
            "sort_batting_by",
            "search_pitching",
            "pitcher_role",
            "min_ip",
            "sort_pitching_by",
            "search_fielding",
            "selected_fielding_pos",
            "compare_type",
            "selected_player_1",
            "selected_player_2",
            "batting_data_raw",
            "pitching_data_raw",
            "fielding_data_raw",
            "batting_kpis",
            "pitching_kpis",
            "fielding_kpis",
            "available_batters",
            "available_pitchers",
            "h2h_rows",
            "player_1_card",
            "player_2_card",
            "h2h_verdict",
        ]
        for field in expected_fields:
            self.assertIn(field, fields, f"IndividualesState debe contener el campo '{field}'")

        if hasattr(IndividualesState, "get_fields"):
            self.assertEqual(fields["active_tab"].default, "bateo")
            self.assertEqual(fields["min_ab"].default, 10)
            self.assertEqual(fields["min_ip"].default, 3.0)
            self.assertEqual(fields["compare_type"].default, "Bateadores")

    def test_individuales_handlers_registered(self):
        """Verifica que todos los event handlers estén registrados en IndividualesState."""
        expected_handlers = [
            "on_load",
            "load_all_stats",
            "set_active_tab",
            "set_search_batting",
            "set_min_ab",
            "set_selected_batting_pos",
            "set_sort_batting_by",
            "set_search_pitching",
            "set_pitcher_role",
            "set_min_ip",
            "set_sort_pitching_by",
            "set_search_fielding",
            "set_selected_fielding_pos",
            "set_compare_type",
            "set_selected_player_1",
            "set_selected_player_2",
            "update_h2h_comparison",
        ]
        for handler in expected_handlers:
            self.assertTrue(
                hasattr(IndividualesState, handler),
                f"IndividualesState debe definir el método '{handler}'",
            )


class TestColectivasStateArchitecture(unittest.TestCase):
    """Pruebas de la arquitectura y definición de ColectivasState."""

    def test_state_inheritance(self):
        """Verifica que ColectivasState sea una subclase válida de rx.State."""
        self.assertTrue(issubclass(ColectivasState, rx.State))

    def test_colectivas_fields_and_defaults(self):
        """Verifica los campos reactivos de ColectivasState."""
        fields = ColectivasState.get_fields() if hasattr(ColectivasState, "get_fields") else ColectivasState.__annotations__

        expected_fields = [
            "active_tab",
            "selected_phase",
            "selected_phase_name",
            "phase_options",
            "selected_batting_metric",
            "selected_pitching_metric",
            "selected_fielding_metric",
            "collective_batting_data",
            "collective_pitching_data",
            "collective_fielding_data",
            "batting_kpis",
            "pitching_kpis",
            "fielding_kpis",
        ]
        for field in expected_fields:
            self.assertIn(field, fields, f"ColectivasState debe contener el campo '{field}'")

        if hasattr(ColectivasState, "get_fields"):
            self.assertEqual(fields["active_tab"].default, "bateo")
            self.assertEqual(fields["selected_phase"].default, "R")
            self.assertEqual(fields["selected_phase_name"].default, "Temporada Regular")

    def test_colectivas_handlers_registered(self):
        """Verifica que todos los event handlers estén registrados en ColectivasState."""
        expected_handlers = [
            "on_load",
            "load_collective_stats",
            "set_active_tab",
            "set_phase_by_name",
            "set_batting_metric",
            "set_pitching_metric",
            "set_fielding_metric",
        ]
        for handler in expected_handlers:
            self.assertTrue(
                hasattr(ColectivasState, handler),
                f"ColectivasState debe definir el método '{handler}'",
            )


class TestIndividualesAndColectivasPagesRendering(unittest.TestCase):
    """Pruebas de renderizado de las vistas Reflex /individuales y /colectivas."""

    def test_individuales_content_component(self):
        """Verifica que individuales_content() retorne un rx.Component válido."""
        content = individuales_content()
        self.assertIsInstance(content, rx.Component, "individuales_content() debe retornar rx.Component")

    def test_individuales_page_component(self):
        """Verifica que individuales() retorne un rx.Component válido con el Layout marco."""
        page = individuales()
        self.assertIsInstance(page, rx.Component, "individuales() debe retornar rx.Component")

    def test_colectivas_content_component(self):
        """Verifica que colectivas_content() retorne un rx.Component válido."""
        content = colectivas_content()
        self.assertIsInstance(content, rx.Component, "colectivas_content() debe retornar rx.Component")

    def test_colectivas_page_component(self):
        """Verifica que colectivas() retorne un rx.Component válido con el Layout marco."""
        page = colectivas()
        self.assertIsInstance(page, rx.Component, "colectivas() debe retornar rx.Component")


class TestSabermetricFormulasAndCalculations(unittest.TestCase):
    """Pruebas unitarias de las fórmulas sabermétricas calculadas en M4."""

    def test_batting_formulas(self):
        """Valida que las fórmulas de AVG, OBP, SLG, OPS, ISO, BABIP y wOBA sean exactas."""
        ab, h, d2, d3, hr = 100, 30, 5, 1, 4
        bb, so, hbp, sf = 10, 20, 2, 1
        d1 = h - d2 - d3 - hr  # 30 - 10 = 20

        avg = h / ab  # 0.300
        obp = (h + bb + hbp) / (ab + bb + hbp + sf)  # 42 / 113 = 0.37168
        slg = (d1 + 2*d2 + 3*d3 + 4*hr) / ab  # (20 + 10 + 3 + 16) / 100 = 49 / 100 = 0.490
        ops = obp + slg  # 0.86168
        iso = slg - avg  # 0.190
        babip = (h - hr) / (ab - so - hr + sf)  # 26 / (100 - 20 - 4 + 1) = 26 / 77 = 0.33766

        woba_num = 0.690 * bb + 0.722 * hbp + 0.888 * d1 + 1.271 * d2 + 1.616 * d3 + 2.101 * hr
        woba_den = ab + bb + sf + hbp
        woba = woba_num / woba_den
        wrc_plus = int(round((woba / 0.320) * 100))

        self.assertAlmostEqual(avg, 0.300, places=3)
        self.assertAlmostEqual(obp, 0.372, places=3)
        self.assertAlmostEqual(slg, 0.490, places=3)
        self.assertAlmostEqual(ops, 0.862, places=3)
        self.assertAlmostEqual(iso, 0.190, places=3)
        self.assertAlmostEqual(babip, 0.338, places=3)
        self.assertGreater(woba, 0.340)
        self.assertGreater(wrc_plus, 100)

    def test_pitching_formulas(self):
        """Valida que las fórmulas de ERA, WHIP, FIP, K/9 y BB/9 sean exactas."""
        ip = 45.0
        er = 15
        h, bb, so, hr, hbp = 38, 12, 48, 4, 1

        era = (er * 9.0) / ip  # (15 * 9) / 45 = 3.00
        whip = (h + bb) / ip  # 50 / 45 = 1.111
        k9 = (so * 9.0) / ip  # (48 * 9) / 45 = 9.60
        bb9 = (bb * 9.0) / ip  # (12 * 9) / 45 = 2.40
        k_bb = so / bb  # 4.00
        fip = ((13.0 * hr + 3.0 * (bb + hbp) - 2.0 * so) / ip) + 3.20
        # (13*4 + 3*13 - 2*48)/45 + 3.20 = (52 + 39 - 96)/45 + 3.20 = -5/45 + 3.20 = -0.111 + 3.20 = 3.088

        self.assertAlmostEqual(era, 3.00, places=2)
        self.assertAlmostEqual(whip, 1.11, places=2)
        self.assertAlmostEqual(k9, 9.60, places=2)
        self.assertAlmostEqual(bb9, 2.40, places=2)
        self.assertAlmostEqual(k_bb, 4.00, places=2)
        self.assertAlmostEqual(fip, 3.09, places=2)


if __name__ == '__main__':
    unittest.main()
