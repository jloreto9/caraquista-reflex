# tests/test_pitching_state.py
"""
test_pitching_state.py
-----------------------
Suite de pruebas unitarias para el estado reactivo de Pitching Summary (republicaraquistapp/state/pitching_state.py).
Valida:
1. Selección de lanzadores por ID numérico (Leones del Caracas y otras franquicias LVBP).
2. Conmutación dinámica de lanzador al navegar desde enlaces de individuales (?pitcher_id=...).
3. Selección automática de rama 'lvbp' y carga de salidas de la temporada 2025.
4. Conmutación de ramas permitida para lanzadores con historial LVBP.
"""

import unittest
from unittest.mock import MagicMock
from republicaraquistapp.state.pitching_state import PitchingState


class TestPitchingState(unittest.TestCase):
    """Pruebas del estado reactivo de Pitching Summary."""

    def setUp(self):
        self.state = PitchingState()
        self.state.clear_selection()

    def test_select_caracas_pitcher_by_id(self):
        """Valida la selección de un lanzador de Caracas (Erick Leal)."""
        self.state.select_pitcher_by_id(612797)
        self.assertTrue(self.state.has_pitcher_selected)
        self.assertEqual(self.state.selected_pitcher.get("id"), 612797)
        self.assertTrue(self.state.has_lvbp_history)
        self.assertTrue(self.state.has_caracas_history)
        self.assertEqual(self.state.active_branch, "lvbp")
        self.assertTrue(len(self.state.game_logs) > 0)

    def test_select_non_caracas_lvbp_pitcher(self):
        """Valida la selección de un lanzador de otra franquicia (Ricardo Sánchez - Magallanes)."""
        self.state.select_pitcher_by_id(645307)
        self.assertTrue(self.state.has_pitcher_selected)
        self.assertEqual(self.state.selected_pitcher.get("id"), 645307)
        self.assertTrue(self.state.has_lvbp_history)
        self.assertEqual(self.state.selected_pitcher.get("lvbp_team_abbr"), "MAG")
        self.assertEqual(self.state.active_branch, "lvbp")
        self.assertTrue(len(self.state.game_logs) > 0)

    def test_switch_pitcher_dynamically(self):
        """Valida el cambio de lanzador A (Erick Leal) a lanzador B (Max Castillo)."""
        self.state.select_pitcher_by_id(612797)
        self.assertEqual(self.state.selected_pitcher.get("id"), 612797)

        # Simular navegación a otro lanzador desde individuales
        self.state.select_pitcher_by_id(666721)
        self.assertEqual(self.state.selected_pitcher.get("id"), 666721)
        self.assertEqual(self.state.selected_pitcher.get("lvbp_team_abbr"), "LAR")
        self.assertTrue(self.state.has_lvbp_history)
        self.assertTrue(len(self.state.game_logs) > 0)

    def test_on_load_with_pitcher_id_param(self):
        """Valida que on_load procese el parámetro pitcher_id y cambie el lanzador activo."""
        # Simular router con parámetro pitcher_id=645307
        mock_router = MagicMock()
        mock_router.page.params = {"pitcher_id": "645307"}
        self.state.router = mock_router

        # Cargar lanzador inicial
        self.state.select_pitcher_by_id(612797)
        self.assertEqual(self.state.selected_pitcher.get("id"), 612797)

        # on_load debe detectar que el ID en params (645307) difiere del actual (612797) y conmutar
        self.state.on_load()
        self.assertEqual(self.state.selected_pitcher.get("id"), 645307)


if __name__ == "__main__":
    unittest.main()
