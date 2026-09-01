# tests/test_m5_sabermetrics_views.py
"""
Suite de Pruebas Unitarias y de Integración para el Módulo M5:
Advanced Sabermetrics Suite (/wpa, /situacional, /spray-charts, /bullpen)
y Registro de las 8 Rutas SPA en caraquista-reflex.
"""

import unittest
import reflex as rx
import pandas as pd
import numpy as np
import plotly.graph_objects as go

import republicaraquistapp.republicaraquistapp as main_app
from republicaraquistapp.state.wpa_state import (
    WpaState,
    build_wp_evolution_chart,
    build_wpa_by_inning_chart,
)
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

from republicaraquistapp.pages.wpa import wpa
from republicaraquistapp.pages.situacional import situacional
from republicaraquistapp.pages.spray_charts import spray_charts
from republicaraquistapp.pages.bullpen import bullpen


class TestM5StateStructures(unittest.TestCase):
    """Pruebas de la Estructura de Estados Reactivos M5."""

    def test_wpa_state_structure(self):
        """Verifica los atributos y métodos del estado reactivo WpaState."""
        self.assertTrue(issubclass(WpaState, rx.State))
        self.assertTrue(hasattr(WpaState, "on_load_wpa"))
        self.assertTrue(hasattr(WpaState, "set_selected_game"))
        self.assertTrue(hasattr(WpaState, "set_active_tab"))
        self.assertTrue(hasattr(WpaState, "load_selected_game_wpa"))
        self.assertTrue(hasattr(WpaState, "load_season_leaderboards"))

    def test_situational_state_structure(self):
        """Verifica los atributos y métodos del estado reactivo SituationalState."""
        self.assertTrue(issubclass(SituationalState, rx.State))
        self.assertTrue(hasattr(SituationalState, "on_load_situacional"))
        self.assertTrue(hasattr(SituationalState, "set_selected_batter"))
        self.assertTrue(hasattr(SituationalState, "set_active_tab"))
        self.assertTrue(hasattr(SituationalState, "set_bvp_batter"))
        self.assertTrue(hasattr(SituationalState, "set_rival_team"))

    def test_spray_state_structure(self):
        """Verifica los atributos y métodos del estado reactivo SprayState."""
        self.assertTrue(issubclass(SprayState, rx.State))
        self.assertTrue(hasattr(SprayState, "on_load_spray"))
        self.assertTrue(hasattr(SprayState, "set_active_view"))
        self.assertTrue(hasattr(SprayState, "set_selected_spray_player"))
        self.assertTrue(hasattr(SprayState, "set_spray_color_mode"))
        self.assertTrue(hasattr(SprayState, "set_sz_perspective"))
        self.assertTrue(hasattr(SprayState, "set_selected_sz_player"))

    def test_bullpen_state_structure(self):
        """Verifica los atributos y métodos del estado reactivo BullpenState."""
        self.assertTrue(issubclass(BullpenState, rx.State))
        self.assertTrue(hasattr(BullpenState, "on_load_bullpen"))
        self.assertTrue(hasattr(BullpenState, "set_active_tab"))
        self.assertTrue(hasattr(BullpenState, "set_lineup_subtab"))
        self.assertTrue(hasattr(BullpenState, "set_selected_game_lineup"))
        self.assertTrue(hasattr(BullpenState, "set_selected_player_lineup"))


class TestM5FigureBuilders(unittest.TestCase):
    """Pruebas de las funciones constructoras de gráficos Plotly."""

    def test_wpa_chart_builder(self):
        """Verifica que build_wp_evolution_chart genere un objeto go.Figure válido."""
        df_sample = pd.DataFrame([
            {
                "atbat_index": 0, "inning": 1, "halfInning": "top", "score_str": "0-0",
                "batter": "Bateador 1", "pitcher": "Pitcher 1", "eventType": "Single",
                "base_icons": "◇ ◇ ◆", "outs_before": 0, "li": 1.0, "wpa": 0.05, "wp_after": 0.55
            },
            {
                "atbat_index": 1, "inning": 1, "halfInning": "bottom", "score_str": "1-0",
                "batter": "Bateador 2", "pitcher": "Pitcher 2", "eventType": "Home Run",
                "base_icons": "◇ ◇ ◇", "outs_before": 1, "li": 1.5, "wpa": 0.15, "wp_after": 0.70
            }
        ])
        fig = build_wp_evolution_chart(df_sample, "Leones vs. Magallanes")
        self.assertIsInstance(fig, go.Figure)
        self.assertGreater(len(fig.data), 0)

        # Caso vacío
        fig_empty = build_wp_evolution_chart(pd.DataFrame(), "Sin datos")
        self.assertIsInstance(fig_empty, go.Figure)

    def test_inning_wpa_chart_builder(self):
        """Verifica que build_wpa_by_inning_chart genere barras de WPA por entrada."""
        df_sample = pd.DataFrame([
            {"inning": 1, "wpa": 0.12},
            {"inning": 2, "wpa": -0.08},
            {"inning": 3, "wpa": 0.05}
        ])
        fig = build_wpa_by_inning_chart(df_sample)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 1)

    def test_ops_by_situation_builder(self):
        """Verifica que build_ops_by_situation_chart genere el gráfico horizontal de OPS."""
        splits_df = pd.DataFrame([
            {"Situación": "Total General", "OPS": "0.750"},
            {"Situación": "Bases Limpias", "OPS": "0.680"},
            {"Situación": "RISP", "OPS": "0.820"}
        ])
        fig = build_ops_by_situation_chart(splits_df)
        self.assertIsInstance(fig, go.Figure)
        self.assertGreater(len(fig.data), 0)

    def test_top_risp_lob_builder(self):
        """Verifica que build_top_risp_lob_chart genere el gráfico de bateadores con más RISP LOB."""
        df_lob = pd.DataFrame([
            {"Bateador": "Jugador A", "Total RISP LOB": 15},
            {"Bateador": "Jugador B", "Total RISP LOB": 12},
        ])
        fig = build_top_risp_lob_chart(df_lob)
        self.assertIsInstance(fig, go.Figure)
        self.assertGreater(len(fig.data), 0)

    def test_bullpen_ir_builder(self):
        """Verifica que build_bullpen_ir_chart genere el gráfico agrupado de IR vs IRS."""
        df_irs = pd.DataFrame([
            {"Lanzador Relevista": "Relevista 1", "Corredores Heredados (IR)": 10, "Heredados Anotados (IRS)": 2},
            {"Lanzador Relevista": "Relevista 2", "Corredores Heredados (IR)": 8, "Heredados Anotados (IRS)": 3},
        ])
        fig = build_bullpen_ir_chart(df_irs)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 2)  # 2 trazas: IR e IRS

    def test_lineup_heatmap_builder(self):
        """Verifica que build_lineup_heatmap_chart genere la matriz de calor 1-9."""
        df_starters = pd.DataFrame([
            {"Jugador": "Bateador 1", "Turno_Num": 1},
            {"Jugador": "Bateador 1", "Turno_Num": 1},
            {"Jugador": "Bateador 2", "Turno_Num": 2},
            {"Jugador": "Bateador 3", "Turno_Num": 4},
        ])
        fig = build_lineup_heatmap_chart(df_starters)
        self.assertIsInstance(fig, go.Figure)


class TestM5PageComponentsRendering(unittest.TestCase):
    """Pruebas de renderizado de componentes Reflex para las 4 páginas M5."""

    def test_wpa_page_returns_rx_component(self):
        """Verifica que la función de página wpa() retorne un rx.Component válido."""
        page = wpa()
        self.assertIsInstance(page, rx.Component)

    def test_situacional_page_returns_rx_component(self):
        """Verifica que la función de página situacional() retorne un rx.Component válido."""
        page = situacional()
        self.assertIsInstance(page, rx.Component)

    def test_spray_charts_page_returns_rx_component(self):
        """Verifica que la función de página spray_charts() retorne un rx.Component válido."""
        page = spray_charts()
        self.assertIsInstance(page, rx.Component)

    def test_bullpen_page_returns_rx_component(self):
        """Verifica que la función de página bullpen() retorne un rx.Component válido."""
        page = bullpen()
        self.assertIsInstance(page, rx.Component)


class TestAll8RoutesRegistration(unittest.TestCase):
    """Pruebas de Registro Integral de las 8 Rutas SPA en Reflex."""

    def test_all_8_routes_registered_in_app(self):
        """Verifica que las 8 rutas requeridas estén debidamente registradas en main_app.app."""
        registered_routes = list(main_app.app._unevaluated_pages.keys())

        expected_keys = [
            "index",
            "standings",
            "individuales",
            "colectivas",
            "wpa",
            "situacional",
            "spray-charts",
            "bullpen"
        ]

        for r_key in expected_keys:
            self.assertIn(
                r_key,
                registered_routes,
                f"La ruta '{r_key}' debe estar registrada en republicaraquistapp.py"
            )

        self.assertEqual(len(registered_routes), 8, "Deben existir exactamente 8 rutas SPA registradas.")


if __name__ == '__main__':
    unittest.main()
