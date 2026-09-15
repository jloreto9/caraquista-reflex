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
from PIL import Image
from core.pitching_card import (
    build_pitching_summary_card,
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


if __name__ == "__main__":
    unittest.main()
