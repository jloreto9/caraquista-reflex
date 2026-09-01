# tests/test_reflex_routes.py
"""
Suite de Pruebas de Rutas, Estado Reactivo y Componentes Reflex para caraquista-reflex.
Cubre:
1. Configuración de Reflex (`rxconfig.py`) y registro de la aplicación.
2. Integridad de importación y compilación de `republicaraquistapp.py`.
3. Estructura y handlers de `AppState` (`republicaraquistapp.state.base_state.AppState`).
4. Renderizado e integridad de componentes modulares (`navbar`, `scoreboard_card`, `kpi_grid`, `standings_table`).
5. Paleta visual y constantes de estilo (`republicaraquistapp.styles.theme`).
6. Función de página principal (`republicaraquistapp.pages.index.index`).
"""

import unittest
import reflex as rx

from rxconfig import config
import republicaraquistapp.republicaraquistapp as main_app
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    ACCENT_GOLD,
    NAVY_PRIMARY,
    TEXT_PRIMARY,
    TEXT_MUTED,
    CARD_STYLE,
    GOLD_BADGE_STYLE,
)
from republicaraquistapp.components.navbar import navbar
from republicaraquistapp.components.scoreboard import scoreboard_card
from republicaraquistapp.components.kpi_grid import kpi_grid
from republicaraquistapp.components.standings_table import standings_table
from republicaraquistapp.pages.index import index


class TestReflexConfiguration(unittest.TestCase):
    """Pruebas de Configuración Global de Reflex (rxconfig.py)."""

    def test_app_configuration_name(self):
        """Verifica que el nombre de la aplicación esté configurado como 'republicaraquistapp'."""
        self.assertEqual(config.app_name, "republicaraquistapp", "El app_name en rxconfig.py debe ser 'republicaraquistapp'")

    def test_app_instance_creation(self):
        """Verifica que la instancia 'app' en republicaraquistapp.py sea una instancia válida de rx.App."""
        self.assertIsInstance(main_app.app, rx.App, "main_app.app debe ser una instancia de rx.App")


class TestAppStateReactive(unittest.TestCase):
    """Pruebas de la Estructura de Estado Reactivo (AppState)."""

    def test_app_state_inheritance(self):
        """Verifica que AppState herede correctamente de rx.State."""
        self.assertTrue(issubclass(AppState, rx.State), "AppState debe ser una subclase de rx.State")

    def test_app_state_default_fields(self):
        """Verifica la inicialización de los campos de estado y KPIs."""
        fields = AppState.get_fields() if hasattr(AppState, "get_fields") else AppState.__annotations__
        
        self.assertIn("selected_season", fields)
        self.assertIn("available_seasons", fields)
        self.assertIn("standings_data", fields)
        self.assertIn("recent_games_data", fields)
        self.assertIn("last_game_data", fields)
        self.assertIn("leones_kpis", fields)
        self.assertIn("is_loading", fields)

    def test_app_state_handler_methods(self):
        """Verifica que los métodos de acción y carga estén definidos en AppState."""
        self.assertTrue(hasattr(AppState, "on_load"), "AppState debe definir el método 'on_load'")
        self.assertTrue(hasattr(AppState, "set_season"), "AppState debe definir el método 'set_season'")
        self.assertTrue(hasattr(AppState, "load_season_data"), "AppState debe definir el método 'load_season_data'")


class TestThemeAndUIConstants(unittest.TestCase):
    """Pruebas de la Paleta Oficial y Estilos Glassmorphism."""

    def test_official_color_palette(self):
        """Verifica los códigos hexadecimales de la paleta oficial de República Caraquista."""
        self.assertEqual(BG_DARK, "#070B19", "El fondo Dark Navy debe ser #070B19")
        self.assertEqual(CARD_BG, "#0D152B", "El fondo de tarjetas Glassmorphism debe ser #0D152B")
        self.assertEqual(ACCENT_GOLD, "#FDB827", "El acento Oro Caraquista debe ser #FDB827")
        self.assertEqual(NAVY_PRIMARY, "#001D4A", "El azul Navy primario debe ser #001D4A")
        self.assertEqual(TEXT_PRIMARY, "#FFFFFF", "El texto principal debe ser blanco brillante #FFFFFF")

    def test_card_style_dict(self):
        """Verifica que CARD_STYLE y GOLD_BADGE_STYLE contengan estilos CSS válidos."""
        self.assertIsInstance(CARD_STYLE, dict)
        self.assertIn("background", CARD_STYLE)
        self.assertIn("border_radius", CARD_STYLE)
        self.assertIn("padding", CARD_STYLE)

        self.assertIsInstance(GOLD_BADGE_STYLE, dict)
        self.assertIn("color", GOLD_BADGE_STYLE)
        self.assertEqual(GOLD_BADGE_STYLE["color"], ACCENT_GOLD)


class TestUIComponentsRendering(unittest.TestCase):
    """Pruebas de Integridad de Renderizado de Componentes Reflex."""

    def test_navbar_component_returns_rx_component(self):
        """Verifica que el componente navbar retorne un componente válido de Reflex."""
        nav = navbar()
        self.assertIsInstance(nav, rx.Component, "navbar() debe retornar un rx.Component")

    def test_scoreboard_component_returns_rx_component(self):
        """Verifica que el componente scoreboard_card retorne un componente válido de Reflex."""
        sb = scoreboard_card()
        self.assertIsInstance(sb, rx.Component, "scoreboard_card() debe retornar un rx.Component")

    def test_kpi_grid_component_returns_rx_component(self):
        """Verifica que el componente kpi_grid retorne un componente válido de Reflex."""
        grid = kpi_grid()
        self.assertIsInstance(grid, rx.Component, "kpi_grid() debe retornar un rx.Component")

    def test_standings_table_component_returns_rx_component(self):
        """Verifica que el componente standings_table retorne un componente válido de Reflex."""
        tbl = standings_table()
        self.assertIsInstance(tbl, rx.Component, "standings_table() debe retornar un rx.Component")

    def test_index_page_returns_rx_component(self):
        """Verifica que la función de vista principal index() retorne un componente válido de Reflex."""
        page = index()
        self.assertIsInstance(page, rx.Component, "index() debe retornar un rx.Component")


if __name__ == '__main__':
    unittest.main()
