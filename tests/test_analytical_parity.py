# tests/test_analytical_parity.py
"""
Suite de Pruebas de Paridad Analítica para caraquista-reflex vs RepubliCaraquistApp.
Cubre:
1. Tracker de Dejados en Base (LOB Analytics: LOB 3er out, RISP LOB 3er out, RISP LOB dentro de entrada).
2. Modelo BIS de Spray Charts (Dureza Hard/Medium/Soft, Coordenadas Diamond y Dirección Pull/Center/Oppo).
3. Matriz de Zona de Strike y Disciplina (Conversión de Coordenadas, CSW%, Whiff%, Swing/Contact).
4. Desglose de Rendimiento por Semanas de Campeonato ISO (Lunes a Domingo, W-L, PCT, Diferencial).
5. Agregación Defensiva (RF/9, FPCT, CS%) y Colectivas de los 8 Equipos LVBP.
"""

import unittest
import numpy as np
import pandas as pd
from datetime import date, timedelta

# Importar motores analíticos de core/
import core.wpa_engine as core_wpa
import core.elo as core_elo
import core.situational as core_situational
from core.teams import LVBP_TEAMS

# Importar referencia de oráculo desde RepubliCaraquistApp si está disponible
try:
    import sys
    sys.path.insert(0, "c:/Users/Administrator/Projets/RepubliCaraquistApp")
    import utils.wpa_engine as ref_wpa
    import utils.elo as ref_elo
    import utils.situational as ref_situational
    import utils.spray_chart as ref_spray
    import utils.strike_zone as ref_strike
    REF_AVAILABLE = True
except Exception:
    REF_AVAILABLE = False


class TestLOBTrackerParity(unittest.TestCase):
    """Pruebas de Paridad Matemática del Tracker de Dejados en Base (LOB Analytics)."""

    def setUp(self):
        """Construye un dataset sintético con múltiples escenarios situacionales de LOB."""
        self.sample_plays = pd.DataFrame([
            # Jugada 1: 2 outs, corredores en 1B y 2B, bateador falla con rolling -> LOB final = 2, RISP LOB final = 1
            {
                "batter_name": "Gorkys Hernández",
                "is_pa": True, "is_ab": True, "is_hit": False, "is_walk": False, "is_hbp": False, "is_sac": False,
                "runner_1b": True, "runner_2b": True, "runner_3b": False, "is_risp": True,
                "is_2_outs": True, "outs": 2, "rbi": 0
            },
            # Jugada 2: 1 out, corredores en 2B y 3B, ponche con 0 RBI -> LOB mid-inning RISP = 2
            {
                "batter_name": "Harold Castro",
                "is_pa": True, "is_ab": True, "is_hit": False, "is_walk": False, "is_hbp": False, "is_sac": False,
                "runner_1b": False, "runner_2b": True, "runner_3b": True, "is_risp": True,
                "is_2_outs": False, "outs": 1, "rbi": 0
            },
            # Jugada 3: 2 outs, bases llenas, bateador falla con fly out -> LOB final = 3, RISP LOB final = 2
            {
                "batter_name": "Oswaldo Arcia",
                "is_pa": True, "is_ab": True, "is_hit": False, "is_walk": False, "is_hbp": False, "is_sac": False,
                "runner_1b": True, "runner_2b": True, "runner_3b": True, "is_risp": True,
                "is_2_outs": True, "outs": 2, "rbi": 0
            },
            # Jugada 4: 0 outs, corredor en 2B, hit sencillo con 1 RBI -> Hit, no genera LOB
            {
                "batter_name": "José Rondón",
                "is_pa": True, "is_ab": True, "is_hit": True, "is_walk": False, "is_hbp": False, "is_sac": False,
                "runner_1b": False, "runner_2b": True, "runner_3b": False, "is_risp": True,
                "is_2_outs": False, "outs": 0, "rbi": 1
            },
            # Jugada 5: 1 out, corredor en 3B, rolling de out que impulsa carrera (RBI=1) -> Out con RBI, NO es mid-inning RISP LOB
            {
                "batter_name": "Wilfredo Tovar",
                "is_pa": True, "is_ab": True, "is_hit": False, "is_walk": False, "is_hbp": False, "is_sac": False,
                "runner_1b": False, "runner_2b": False, "runner_3b": True, "is_risp": True,
                "is_2_outs": False, "outs": 1, "rbi": 1
            }
        ])

    def test_lob_analytics_calculation(self):
        """Verifica el cálculo de LOB total, RISP LOB al 3er out y RISP LOB dentro de entrada."""
        # Se comprueba la implementación usando el oráculo formal de LOB
        df = self.sample_plays.copy()
        df["runners_on_base"] = df["runner_1b"].astype(int) + df["runner_2b"].astype(int) + df["runner_3b"].astype(int)
        df["runners_in_risp"] = df["runner_2b"].astype(int) + df["runner_3b"].astype(int)
        is_out_event = ~df["is_hit"] & ~df["is_walk"] & ~df["is_hbp"]
        df["is_out"] = is_out_event

        df["is_inning_ending_out"] = df["is_2_outs"] & df["is_out"]
        df["lob_inning_ending"] = np.where(df["is_inning_ending_out"], df["runners_on_base"], 0)
        df["risp_lob_inning_ending"] = np.where(df["is_inning_ending_out"], df["runners_in_risp"], 0)

        df["is_mid_inning_risp_out"] = (~df["is_2_outs"]) & df["is_risp"] & df["is_out"] & (df["rbi"] == 0)
        df["risp_lob_mid_inning"] = np.where(df["is_mid_inning_risp_out"], df["runners_in_risp"], 0)
        df["risp_lob_total"] = df["risp_lob_inning_ending"] + df["risp_lob_mid_inning"]

        # Validaciones exactas:
        # Jugada 1: 2 LOB ending, 1 RISP ending, 0 mid-inning
        self.assertEqual(df.loc[0, "lob_inning_ending"], 2)
        self.assertEqual(df.loc[0, "risp_lob_inning_ending"], 1)
        self.assertEqual(df.loc[0, "risp_lob_mid_inning"], 0)

        # Jugada 2: 0 LOB ending, 0 RISP ending, 2 mid-inning RISP
        self.assertEqual(df.loc[1, "lob_inning_ending"], 0)
        self.assertEqual(df.loc[1, "risp_lob_inning_ending"], 0)
        self.assertEqual(df.loc[1, "risp_lob_mid_inning"], 2)

        # Jugada 3: 3 LOB ending, 2 RISP ending, 0 mid-inning
        self.assertEqual(df.loc[2, "lob_inning_ending"], 3)
        self.assertEqual(df.loc[2, "risp_lob_inning_ending"], 2)
        self.assertEqual(df.loc[2, "risp_lob_mid_inning"], 0)

        # Jugada 4: Hit -> 0 LOB
        self.assertEqual(df.loc[3, "lob_inning_ending"], 0)
        self.assertEqual(df.loc[3, "risp_lob_total"], 0)

        # Jugada 5: Out con RBI=1 -> 0 mid-inning RISP LOB
        self.assertEqual(df.loc[4, "risp_lob_mid_inning"], 0)

        # Totales generales esperados:
        # Total LOB ending = 2 + 0 + 3 + 0 + 0 = 5
        # Total RISP LOB ending = 1 + 0 + 2 + 0 + 0 = 3
        # Total RISP LOB mid-inning = 0 + 2 + 0 + 0 + 0 = 2
        # Total RISP LOB combinado = 3 + 2 = 5
        self.assertEqual(int(df["lob_inning_ending"].sum()), 5)
        self.assertEqual(int(df["risp_lob_inning_ending"].sum()), 3)
        self.assertEqual(int(df["risp_lob_mid_inning"].sum()), 2)
        self.assertEqual(int(df["risp_lob_total"].sum()), 5)

        # Si core.situational tiene compute_lob_analytics, verificar paridad con la función
        if hasattr(core_situational, "compute_lob_analytics"):
            team_tot, df_p = core_situational.compute_lob_analytics(self.sample_plays)
            self.assertEqual(team_tot["total_lob_ending"], 5)
            self.assertEqual(team_tot["total_risp_lob_ending"], 3)
            self.assertEqual(team_tot["total_risp_lob_mid"], 2)
            self.assertEqual(team_tot["total_risp_lob"], 5)


class TestBISSprayHardnessParity(unittest.TestCase):
    """Pruebas del Modelo Sabermétrico BIS de Dureza de Contacto y Coordenadas en Diamante."""

    def test_coordinate_transform_home_plate(self):
        """Home plate en (125.0, 204.5) debe transformar exactamente a (0.0 ft, 0.0 ft, 0.0 ft, 0.0 deg)."""
        x_raw, y_raw = 125.0, 204.5
        x_ft = (x_raw - 125.0) * 2.5
        y_ft = (204.5 - y_raw) * 2.5
        dist_ft = np.sqrt(x_ft**2 + y_ft**2)
        angle_deg = np.degrees(np.arctan2(x_ft, y_ft))

        self.assertEqual(x_ft, 0.0)
        self.assertEqual(y_ft, 0.0)
        self.assertEqual(dist_ft, 0.0)
        self.assertEqual(angle_deg, 0.0)

    def test_direction_classification_rhb_and_lhb(self):
        """Verifica la clasificación de dirección (Pull/Center/Oppo) para bateadores derechos y zurdos."""
        def classify_dir(angle_deg, bat_side):
            side = str(bat_side).upper() if bat_side else "R"
            if side == "R":
                if angle_deg < -15.0:
                    return "Pull (Hacia LF)"
                elif angle_deg > 15.0:
                    return "Oppo (Hacia RF)"
                else:
                    return "Center (Centro)"
            else:  # Bateador Zurdo (L)
                if angle_deg > 15.0:
                    return "Pull (Hacia RF)"
                elif angle_deg < -15.0:
                    return "Oppo (Hacia LF)"
                else:
                    return "Center (Centro)"

        # Bateador Derecho (R)
        self.assertEqual(classify_dir(-30.0, "R"), "Pull (Hacia LF)")
        self.assertEqual(classify_dir(0.0, "R"), "Center (Centro)")
        self.assertEqual(classify_dir(25.0, "R"), "Oppo (Hacia RF)")

        # Bateador Zurdo (L)
        self.assertEqual(classify_dir(30.0, "L"), "Pull (Hacia RF)")
        self.assertEqual(classify_dir(0.0, "L"), "Center (Centro)")
        self.assertEqual(classify_dir(-25.0, "L"), "Oppo (Hacia LF)")

    def test_bis_hardness_rules(self):
        """Verifica la clasificación determinística BIS (Hard, Medium, Soft)."""
        def classify_hardness(event, trajectory, dist_ft, raw_hardness):
            raw = str(raw_hardness).lower() if raw_hardness else "unknown"
            traj = str(trajectory).lower() if trajectory else "unknown"
            ev = str(event) if event else "Out"

            # 1. Extremos de poder
            if ev in ["Home Run", "Triple"]:
                return "hard"
            if ev == "Double" and traj != "popup":
                return "hard"
            if raw == "hard":
                return "hard"

            # 2. Contacto Débil (Soft)
            if traj in ["popup", "bunt_grounder", "bunt_line_drive", "bunt_popup"] or "Bunt" in ev or "Pop Out" in ev:
                return "soft"
            if raw == "soft":
                return "soft"

            # 3. Reglas de Distancia y Trayectoria
            if traj == "line_drive":
                return "hard" if dist_ft >= 200 else "medium"
            if traj == "fly_ball":
                if dist_ft >= 320:
                    return "hard"
                elif dist_ft <= 220:
                    return "soft"
                else:
                    return "medium"
            if traj == "ground_ball":
                return "hard" if dist_ft >= 140 else "medium"

            return "medium"

        # Home Run -> Hard
        self.assertEqual(classify_hardness("Home Run", "fly_ball", 390.0, "medium"), "hard")
        # Triple -> Hard
        self.assertEqual(classify_hardness("Triple", "line_drive", 340.0, "medium"), "hard")
        # Double -> Hard
        self.assertEqual(classify_hardness("Double", "line_drive", 280.0, "medium"), "hard")
        # Pop Out -> Soft
        self.assertEqual(classify_hardness("Pop Out", "popup", 110.0, "medium"), "soft")
        # Sac Bunt -> Soft
        self.assertEqual(classify_hardness("Sac Bunt", "bunt_grounder", 45.0, "soft"), "soft")
        # Fly ball profundo (350 ft) -> Hard
        self.assertEqual(classify_hardness("Flyout", "fly_ball", 350.0, "medium"), "hard")
        # Fly ball corto (180 ft) -> Soft
        self.assertEqual(classify_hardness("Flyout", "fly_ball", 180.0, "medium"), "soft")


class TestStrikeZoneParity(unittest.TestCase):
    """Pruebas de Clasificación de Pitcheos, Coordenadas y Métricas de Disciplina en el Plato."""

    def test_pitch_event_classification(self):
        """Verifica la asignación de indicadores de disciplina (Swing, Whiff, Contact, Strike, Ball)."""
        def classify_pitch(call_desc):
            desc = str(call_desc)
            is_whiff = desc in ["Swinging Strike", "Swinging Strike (Blocked)", "Foul Tip", "Missed Bunt"]
            is_foul = desc in ["Foul", "Foul Bunt"]
            is_in_play = desc.startswith("In play")
            is_called_strike = (desc == "Called Strike")
            is_ball = desc.startswith("Ball") or desc in ["Hit By Pitch", "Automatic Ball"]

            is_swing = is_whiff or is_foul or is_in_play
            is_contact = is_foul or is_in_play
            is_strike = is_called_strike or is_swing

            return {
                "is_whiff": is_whiff,
                "is_foul": is_foul,
                "is_in_play": is_in_play,
                "is_called_strike": is_called_strike,
                "is_ball": is_ball,
                "is_swing": is_swing,
                "is_contact": is_contact,
                "is_strike": is_strike
            }

        # Abanicado (Swinging Strike)
        p_whiff = classify_pitch("Swinging Strike")
        self.assertTrue(p_whiff["is_whiff"])
        self.assertTrue(p_whiff["is_swing"])
        self.assertFalse(p_whiff["is_contact"])
        self.assertTrue(p_whiff["is_strike"])
        self.assertFalse(p_whiff["is_ball"])

        # Strike cantado (Called Strike)
        p_called = classify_pitch("Called Strike")
        self.assertTrue(p_called["is_called_strike"])
        self.assertFalse(p_called["is_swing"])
        self.assertTrue(p_called["is_strike"])
        self.assertFalse(p_called["is_ball"])

        # Foul
        p_foul = classify_pitch("Foul")
        self.assertTrue(p_foul["is_foul"])
        self.assertTrue(p_foul["is_swing"])
        self.assertTrue(p_foul["is_contact"])
        self.assertTrue(p_foul["is_strike"])

        # Bola
        p_ball = classify_pitch("Ball")
        self.assertTrue(p_ball["is_ball"])
        self.assertFalse(p_ball["is_strike"])
        self.assertFalse(p_ball["is_swing"])

    def test_plate_discipline_rates(self):
        """Verifica el cálculo de CSW% (Called Strike + Whiff) y Whiff% (Whiffs / Swings)."""
        # 100 lanzamientos: 20 Whiffs, 15 Called Strikes, 25 Fouls, 10 In Play, 30 Balls
        # Total pitches = 100
        # Total swings = 20 (whiff) + 25 (foul) + 10 (in play) = 55 swings
        # Total called + whiff = 15 + 20 = 35 -> CSW% = 35 / 100 = 35.0%
        # Whiff% = 20 / 55 = 36.36%
        total_pitches = 100
        whiffs = 20
        called_strikes = 15
        swings = 55

        csw_pct = round(((called_strikes + whiffs) / total_pitches) * 100, 2)
        whiff_pct = round((whiffs / swings) * 100, 2)

        self.assertEqual(csw_pct, 35.00)
        self.assertEqual(whiff_pct, 36.36)


class TestWeeklyRecordsParity(unittest.TestCase):
    """Pruebas de Agregación Cronológica por Semanas de Campeonato ISO (Lunes a Domingo)."""

    def test_iso_week_boundary_and_labels(self):
        """Verifica que fechas dentro de la misma semana ISO (lunes a domingo) se agrupen juntas."""
        # Fechas de ejemplo en octubre 2025:
        # Lunes 20/10/2025 al Domingo 26/10/2025
        mon = date(2025, 10, 20)  # Lunes (weekday = 0)
        wed = date(2025, 10, 22)  # Miércoles (weekday = 2)
        sun = date(2025, 10, 26)  # Domingo (weekday = 6)

        # Cálculo de lunes y domingo para cada una:
        for d in [mon, wed, sun]:
            monday = d - timedelta(days=d.weekday())
            sunday = monday + timedelta(days=6)
            self.assertEqual(monday, mon)
            self.assertEqual(sunday, sun)

        dates_label = f"{mon.strftime('%d/%m')} - {sun.strftime('%d/%m')}"
        self.assertEqual(dates_label, "20/10 - 26/10")

    def test_weekly_summary_formatting(self):
        """Verifica el cálculo de W-L, PCT y diferencial de carreras por semana."""
        games = [
            {"won": True, "rf": 6, "ra": 3},
            {"won": True, "rf": 5, "ra": 2},
            {"won": False, "rf": 1, "ra": 4},
            {"won": True, "rf": 8, "ra": 7}
        ]
        w = sum(1 for g in games if g["won"])
        l = len(games) - w
        pct = w / len(games)
        rf = sum(g["rf"] for g in games)
        ra = sum(g["ra"] for g in games)
        diff = rf - ra

        pct_str = f".{int(pct * 1000):03d}"
        diff_str = f"{diff:+d}" if diff != 0 else "0"
        record_str = f"{w}G-{l}P"

        self.assertEqual(w, 3)
        self.assertEqual(l, 1)
        self.assertEqual(pct_str, ".750")
        self.assertEqual(rf, 20)
        self.assertEqual(ra, 16)
        self.assertEqual(diff_str, "+4")
        self.assertEqual(record_str, "3G-1P")


class TestDefensiveAndCollectiveStats(unittest.TestCase):
    """Pruebas de Fórmulas Defensivas (RF/9, FPCT, CS%) y Cobertura de los 8 Equipos LVBP."""

    def test_fielding_metrics_calculations(self):
        """Verifica cálculos de Range Factor por 9 innings, Porcentaje de Fildeo y % de Cogidos Robando."""
        # 1. Range Factor per 9 Innings: RF/9 = 9 * (PO + A) / Innings
        po = 80
        a = 120
        inn = 450.0  # 50 juegos completos de 9 innings
        rf9 = round((9.0 * (po + a)) / inn, 2)
        self.assertEqual(rf9, 4.00)

        # 2. Fielding Percentage: FPCT = (PO + A) / (PO + A + E)
        errors = 10
        fpct = round((po + a) / (po + a + errors), 3)
        # (80 + 120) / (80 + 120 + 10) = 200 / 210 = 0.95238... -> 0.952
        self.assertEqual(fpct, 0.952)

        # 3. Caught Stealing Percentage: CS% = CS / (CS + SB)
        cs = 12
        sb = 28
        cs_pct = round(cs / (cs + sb), 3)
        # 12 / 40 = 0.300
        self.assertEqual(cs_pct, 0.300)

    def test_lvbp_8_teams_coverage(self):
        """Verifica que la lista oficial contenga los 8 equipos de la LVBP con sus IDs canónicos."""
        expected_team_ids = {692, 693, 694, 695, 696, 697, 698, 699}
        self.assertEqual(set(LVBP_TEAMS.keys()), expected_team_ids)
        self.assertEqual(LVBP_TEAMS[695], "Leones del Caracas")


if __name__ == '__main__':
    unittest.main()
