# tests/test_navigation_state.py
"""
test_navigation_state.py
------------------------
Suite de pruebas unitarias y de integración para la arquitectura de Navegación,
AppState reactivo y Layout de República Caraquista (Milestone M2).
"""

import os
import sys
import unittest

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import reflex as rx
from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    CARD_HOVER,
    ACCENT_GOLD,
    GOLD_HOVER,
    NAVY_PRIMARY,
    NAVY_SECONDARY,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_DIM,
    BORDER_CARD,
    BORDER_SUBTLE,
    BORDER_GOLD,
    BORDER_ACTIVE,
    SUCCESS_COLOR,
    DANGER_COLOR,
    WARNING_COLOR,
    INFO_COLOR,
    CARD_STYLE,
    GLASS_PANEL_STYLE,
    CARD_HEADER_STYLE,
    NAVBAR_STYLE,
    NAV_LINK_STYLE,
    NAV_LINK_ACTIVE_STYLE,
    MOBILE_NAV_LINK_STYLE,
    MOBILE_NAV_LINK_ACTIVE_STYLE,
    GOLD_BADGE_STYLE,
    NAVY_BADGE_STYLE,
    SUCCESS_BADGE_STYLE,
    DANGER_BADGE_STYLE,
    MUTED_BADGE_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    CONTAINER_STYLE,
    PAGE_HEADER_STYLE,
    FOOTER_STYLE,
    DRAWER_CONTENT_STYLE,
)
from republicaraquistapp.state.base_state import AppState, BaseState
from republicaraquistapp.components.navbar import navbar, NAV_ITEMS
from republicaraquistapp.components.layout import layout, footer
from republicaraquistapp.pages.index import index


class TestThemeConstants(unittest.TestCase):
    """Valida que la paleta oficial y los estilos de diseño cumplan con la especificación."""

    def test_official_color_palette(self):
        self.assertEqual(BG_DARK, "#070B19", "BG_DARK debe ser #070B19")
        self.assertEqual(CARD_BG, "#0D152B", "CARD_BG debe ser #0D152B")
        self.assertEqual(CARD_HOVER, "#121D3A", "CARD_HOVER debe ser #121D3A")
        self.assertEqual(ACCENT_GOLD, "#FDB827", "ACCENT_GOLD debe ser #FDB827")
        self.assertEqual(GOLD_HOVER, "#FFC72C", "GOLD_HOVER debe ser #FFC72C")
        self.assertEqual(NAVY_PRIMARY, "#001D4A", "NAVY_PRIMARY debe ser #001D4A")
        self.assertEqual(TEXT_PRIMARY, "#FFFFFF", "TEXT_PRIMARY debe ser #FFFFFF")
        self.assertEqual(TEXT_MUTED, "#94A3B8", "TEXT_MUTED debe ser #94A3B8")

    def test_semantic_colors(self):
        self.assertEqual(SUCCESS_COLOR, "#10B981")
        self.assertEqual(DANGER_COLOR, "#EF4444")
        self.assertEqual(WARNING_COLOR, "#F59E0B")
        self.assertEqual(INFO_COLOR, "#3B82F6")

    def test_style_dictionaries_structure(self):
        for style_dict in [
            CARD_STYLE,
            GLASS_PANEL_STYLE,
            CARD_HEADER_STYLE,
            NAVBAR_STYLE,
            NAV_LINK_STYLE,
            NAV_LINK_ACTIVE_STYLE,
            MOBILE_NAV_LINK_STYLE,
            MOBILE_NAV_LINK_ACTIVE_STYLE,
            GOLD_BADGE_STYLE,
            NAVY_BADGE_STYLE,
            SUCCESS_BADGE_STYLE,
            DANGER_BADGE_STYLE,
            MUTED_BADGE_STYLE,
            BUTTON_PRIMARY_STYLE,
            BUTTON_SECONDARY_STYLE,
            CONTAINER_STYLE,
            PAGE_HEADER_STYLE,
            FOOTER_STYLE,
            DRAWER_CONTENT_STYLE,
        ]:
            self.assertIsInstance(style_dict, dict, f"{style_dict} debe ser un diccionario")
            self.assertGreater(len(style_dict), 0, f"{style_dict} no debe estar vacío")


class TestAppStateArchitecture(unittest.TestCase):
    """Valida la estructura y comportamiento del estado reactivo AppState."""

    def test_app_state_fields_and_defaults(self):
        fields = AppState.get_fields()
        self.assertIn("selected_season", fields)
        self.assertIn("selected_season_str", fields)
        self.assertIn("current_route", fields)
        self.assertIn("is_loading", fields)
        self.assertIn("has_error", fields)
        self.assertIn("drawer_open", fields)
        self.assertIn("standings_data", fields)
        self.assertIn("recent_games_data", fields)
        self.assertIn("last_game_data", fields)
        self.assertIn("leones_kpis", fields)

        self.assertEqual(fields["selected_season"].default, 2025)
        self.assertEqual(fields["selected_season_str"].default, "2025-2026")
        self.assertEqual(fields["current_route"].default, "/")
        self.assertEqual(fields["is_loading"].default, False)
        self.assertEqual(fields["has_error"].default, False)
        self.assertEqual(fields["drawer_open"].default, False)

        self.assertIs(BaseState, AppState)

    def test_app_state_handlers_registered(self):
        expected_handlers = [
            "set_route",
            "toggle_drawer",
            "set_drawer_open",
            "close_drawer",
            "set_season",
            "set_error",
            "clear_error",
            "set_loading",
            "load_season_data",
            "on_load",
        ]
        for handler in expected_handlers:
            self.assertTrue(
                hasattr(AppState, handler),
                f"AppState debe definir el handler o método '{handler}'",
            )


class TestNavigationRoutes(unittest.TestCase):
    """Valida que las 8 rutas requeridas estén presentes con etiquetas en español."""

    def test_eight_routes_inventory(self):
        self.assertEqual(len(NAV_ITEMS), 8, f"Se esperaban exactamente 8 rutas SPA, se encontraron {len(NAV_ITEMS)}")
        
        expected_routes = [
            "/",
            "/standings",
            "/individuales",
            "/colectivas",
            "/wpa",
            "/situacional",
            "/spray-charts",
            "/bullpen",
        ]
        actual_routes = [item["route"] for item in NAV_ITEMS]
        self.assertEqual(actual_routes, expected_routes)

    def test_routes_metadata_in_spanish(self):
        for item in NAV_ITEMS:
            self.assertIn("route", item)
            self.assertIn("label", item)
            self.assertIn("icon", item)
            self.assertIn("desc", item)
            self.assertGreater(len(item["label"]), 0)
            self.assertGreater(len(item["desc"]), 0)


class TestComponentCompilation(unittest.TestCase):
    """Valida la correcta instanciación de componentes Reflex sin errores sintácticos."""

    def test_navbar_compilation(self):
        comp = navbar()
        self.assertIsNotNone(comp)

    def test_footer_compilation(self):
        comp = footer()
        self.assertIsNotNone(comp)

    def test_layout_compilation(self):
        comp = layout(
            content=rx.text("Cuerpo de prueba"),
            page_title="Página de Prueba",
            page_description="Descripción didáctica en español",
            current_route="/standings",
        )
        self.assertIsNotNone(comp)

    def test_index_page_compilation(self):
        page = index()
        self.assertIsNotNone(page)


if __name__ == "__main__":
    unittest.main()
