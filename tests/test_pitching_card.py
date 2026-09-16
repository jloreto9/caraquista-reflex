# tests/test_pitching_card.py
"""
test_pitching_card.py
---------------------
Suite de pruebas unitarias para el generador gráfico de tarjetas panorámicas
de Pitching Summary (core/pitching_card.py).
Valida:
1. Generación de tarjeta PNG para MLB/MiLB (Statcast).
2. Generación de tarjeta PNG para Leones del Caracas (LVBP PBP).
3. Dimensiones exactas (2400 x 1350 px), formato PNG válido y metadatos DPI (300, 300).
4. Mapeo de paleta de colores para tipos de lanzamiento.
"""

import io
import unittest
import pandas as pd
from PIL import Image
from core.pitching_card import (
    build_pitching_summary_card,
    build_nestico_pitching_summary,
    build_lvbp_matplotlib_summary,
    _get_pitch_color,
    PITCH_COLORS,
    CANVAS_SIZE,
    DPI,
)


class TestPitchingCard(unittest.TestCase):
    """Pruebas del generador gráfico de tarjetas HD."""

    def setUp(self):
        self.dummy_pitcher = {
            "name": "Albert Suárez",
            "throws": "R",
            "team": "Baltimore Orioles",
            "photo_url": None,
        }
        self.dummy_game = {
            "role": "Abridor",
            "opponent": "Minnesota Twins",
            "date": "2024-04-17",
            "ip": "5.2",
            "h": 3,
            "r": 0,
            "er": 0,
            "bb": 0,
            "so": 4,
            "pitches": 75,
            "league": "MLB",
        }
        self.dummy_statcast_analysis = {
            "total_pitches": 75,
            "has_statcast": True,
            "statcast_table": [
                {
                    "pitch_name": "4-Seam Fastball", "count": 47, "usage_pct": "62.7%",
                    "velo_avg": 95.9, "velo_max": 97.8, "spin_avg": 2413,
                    "ivb": 16.9, "hb": 10.5, "whiff_pct": "23.4%", "csw_pct": "23.4%", "zone_pct": "57.4%",
                }
            ],
            "pbp_kpis": {
                "csw_pct": "23.4%",
                "whiff_pct": "23.4%",
            },
            "pitches": [
                {
                    "pitch_name": "4-Seam Fastball", "hb": 10.5, "ivb": 16.9,
                    "plate_x": 0.2, "plate_z": 2.8, "is_whiff": False,
                }
            ],
            "innings_workload": [
                {"inning": 1, "pitches": 15, "strikes": 10, "avg_li": 1.1},
                {"inning": 2, "pitches": 12, "strikes": 9, "avg_li": 0.8},
            ],
            "splits_platoon": {
                "vs_lhb": {"pitches": 30, "csw_pct": "25.0%", "whiff_pct": "20.0%", "strike_pct": "65.0%"},
                "vs_rhb": {"pitches": 45, "csw_pct": "22.0%", "whiff_pct": "25.0%", "strike_pct": "67.0%"},
            },
        }

    def test_build_mlb_statcast_card(self):
        """Verifica la generación de la tarjeta PNG de MLB/MiLB a 300 DPI y dimensiones 2400x1350."""
        png_bytes = build_pitching_summary_card(
            pitcher_data=self.dummy_pitcher,
            game_data=self.dummy_game,
            pitch_analysis=self.dummy_statcast_analysis,
            is_lvbp=False,
            season=2024,
        )

        self.assertIsInstance(png_bytes, bytes)
        self.assertGreater(len(png_bytes), 50000)

        # Validar formato con PIL
        img = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(img.format, "PNG")
        self.assertEqual(img.size, CANVAS_SIZE)
        # Validar metadatos DPI
        dpi = img.info.get("dpi")
        if dpi:
            self.assertEqual(int(round(dpi[0])), 300)
            self.assertEqual(int(round(dpi[1])), 300)

    def test_build_lvbp_card(self):
        """Verifica la generación de la tarjeta PNG adaptada de Leones del Caracas (LVBP)."""
        caracas_pitcher = {
            "name": "Erick Leal",
            "throws": "R",
            "team": "Leones del Caracas",
            "photo_url": None,
        }
        caracas_game = {
            "role": "Abridor",
            "opponent": "Navegantes del Magallanes",
            "date": "2025-11-20",
            "ip": "5.0",
            "h": 4,
            "r": 1,
            "er": 1,
            "bb": 1,
            "so": 6,
            "pitches": 78,
            "league": "LVBP",
        }
        caracas_analysis = {
            "total_pitches": 78,
            "has_statcast": False,
            "pbp_table": [
                {"destination": "Bolas", "count": 28, "pct": "35.9%"},
                {"destination": "Strikes Cantados", "count": 18, "pct": "23.1%"},
                {"destination": "Strikes Abanicados (Whiff)", "count": 12, "pct": "15.4%"},
                {"destination": "Fouls", "count": 10, "pct": "12.8%"},
                {"destination": "En Juego (Out / Hit)", "count": 10, "pct": "12.8%"},
            ],
            "pbp_kpis": {
                "csw_pct": "38.5%",
                "whiff_pct": "37.5%",
            },
            "innings_workload": [
                {"inning": 1, "pitches": 18, "strikes": 12, "avg_li": 1.2},
                {"inning": 2, "pitches": 15, "strikes": 11, "avg_li": 0.9},
                {"inning": 3, "pitches": 16, "strikes": 10, "avg_li": 1.4},
            ],
            "splits_platoon": {
                "vs_lhb": {"pitches": 35, "csw_pct": "35.0%", "whiff_pct": "30.0%", "strike_pct": "60.0%"},
                "vs_rhb": {"pitches": 43, "csw_pct": "40.0%", "whiff_pct": "42.0%", "strike_pct": "65.0%"},
            },
        }

        png_bytes = build_pitching_summary_card(
            pitcher_data=caracas_pitcher,
            game_data=caracas_game,
            pitch_analysis=caracas_analysis,
            is_lvbp=True,
            season=2025,
        )

        self.assertIsInstance(png_bytes, bytes)
        self.assertGreater(len(png_bytes), 50000)

        img = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(img.format, "PNG")
        self.assertEqual(img.size, CANVAS_SIZE)

    def test_pitch_colors_coverage(self):
        """Valida que los pitcheos estándar tengan colores definidos."""
        self.assertEqual(_get_pitch_color("4-Seam Fastball"), (210, 45, 73))
        self.assertEqual(_get_pitch_color("Slider"), (238, 231, 22))
        self.assertEqual(_get_pitch_color("Changeup"), (29, 190, 58))
        self.assertEqual(_get_pitch_color("Pitcheo Desconocido"), (140, 140, 140))

    def test_build_nestico_season_and_range_modes(self):
        """Valida que el generador Matplotlib genere correctamente en modo season y range."""
        dummy_df = pd.DataFrame([
            {
                "pitch_type": "FF",
                "pitch_name": "4-Seam Fastball",
                "release_speed": 95.5,
                "pfx_x": 10.2,
                "pfx_z": 16.5,
                "release_spin_rate": 2350,
                "release_pos_x": -1.8,
                "release_pos_z": 5.9,
                "release_extension": 6.4,
                "plate_x": 0.1,
                "plate_z": 2.5,
                "game_date": "2024-05-10",
                "p_throws": "R",
                "swing": True,
                "whiff": False,
                "in_zone": True,
                "out_zone": False,
                "chase": False,
                "events": "strikeout",
                "description": "swinging_strike",
                "delta_run_exp": -0.15,
                "estimated_woba_using_speedangle": 0.220,
            },
            {
                "pitch_type": "SL",
                "pitch_name": "Slider",
                "release_speed": 85.2,
                "pfx_x": -4.2,
                "pfx_z": 2.1,
                "release_spin_rate": 2500,
                "release_pos_x": -1.9,
                "release_pos_z": 5.8,
                "release_extension": 6.3,
                "plate_x": 0.6,
                "plate_z": 1.8,
                "game_date": "2024-05-15",
                "p_throws": "R",
                "swing": True,
                "whiff": True,
                "in_zone": False,
                "out_zone": True,
                "chase": True,
                "events": None,
                "description": "swinging_strike",
                "delta_run_exp": -0.10,
                "estimated_woba_using_speedangle": 0.180,
            }
        ])

        # Probar modo season
        png_season = build_nestico_pitching_summary(
            df=dummy_df,
            pitcher_info=self.dummy_pitcher,
            mode="season",
            season=2024,
            dpi=100,
        )
        self.assertIsInstance(png_season, bytes)
        self.assertGreater(len(png_season), 30000)
        img_season = Image.open(io.BytesIO(png_season))
        self.assertEqual(img_season.format, "PNG")

        # Probar modo range
        png_range = build_nestico_pitching_summary(
            df=dummy_df,
            pitcher_info=self.dummy_pitcher,
            mode="range",
            season=2024,
            start_date="2024-05-01",
            end_date="2024-05-31",
            dpi=100,
        )
        self.assertIsInstance(png_range, bytes)
        self.assertGreater(len(png_range), 30000)
        img_range = Image.open(io.BytesIO(png_range))
        self.assertEqual(img_range.format, "PNG")

    def test_build_lvbp_matplotlib_summary_direct(self):
        """Valida que build_lvbp_matplotlib_summary genere un PNG válido."""
        caracas_pitcher = {
            "name": "Erick Leal",
            "throws": "R",
            "team": "Leones del Caracas",
            "photo_url": None,
        }
        caracas_game = {
            "opponent": "Navegantes del Magallanes",
            "date": "2025-11-20",
            "ip": "5.0",
            "h": 4,
            "r": 1,
            "er": 1,
            "bb": 1,
            "so": 6,
            "pitches": 78,
        }
        analysis = {
            "total_pitches": 78,
            "pbp_table": [
                {"destination": "Strikes Cantados", "count": 18, "pct": "23.1%"},
                {"destination": "Bolas", "count": 28, "pct": "35.9%"},
            ],
            "pbp_kpis": {"csw_pct": "35.0%"},
            "innings_workload": [
                {"inning": 1, "pitches": 18, "strikes": 12, "avg_li": 1.2}
            ],
            "splits_platoon": {
                "vs_lhb": {"pitches": 35, "csw_pct": "35.0%", "whiff_pct": "30.0%", "strike_pct": "60.0%"},
                "vs_rhb": {"pitches": 43, "csw_pct": "40.0%", "whiff_pct": "42.0%", "strike_pct": "65.0%"},
            },
        }
        png_lvbp = build_lvbp_matplotlib_summary(
            pitcher_info=caracas_pitcher,
            game_summary=caracas_game,
            analysis=analysis,
            season=2025,
            dpi=100,
        )
        self.assertIsInstance(png_lvbp, bytes)
        self.assertGreater(len(png_lvbp), 30000)
        img = Image.open(io.BytesIO(png_lvbp))
        self.assertEqual(img.format, "PNG")


if __name__ == "__main__":
    unittest.main()
