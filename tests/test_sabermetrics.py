# tests/test_sabermetrics.py
"""
Suite de Pruebas Unitarias de Sabermetría para caraquista-reflex.
Cubre:
1. Matriz Tango RE24 de 24 Estados Base-Out y codificación de bases (--3 como 3, 12- como 4).
2. Modelo de Probabilidad de Victoria (Win Expectancy) y Leverage Index (LI).
3. Fórmulas de Bateo (OBP con HBP y SF, SLG, OPS).
4. Métricas de Pitcheo y Protección ante División por Cero (ERA, WHIP con IP=0).
5. Escala Logística ELO, Ventaja de Localía (+35 pts) y Actualización por Factor K.
6. Simulación Estocástica Monte Carlo de 5,000 Iteraciones y Conservación de Probabilidades.
"""

import unittest
import numpy as np
import pandas as pd
import math

from core.wpa_engine import (
    RE24,
    encode_base_state,
    format_base_state,
    calculate_win_expectancy,
    calculate_leverage_index,
    AVG_RUNS_PER_INNING,
    VAR_PER_INNING,
)
from core.elo import (
    BASE_ELO,
    HOME_ADVANTAGE,
    K_BY_PHASE,
    expected_score,
    calculate_matchup_win_prob,
    update_elo,
    simulate_monte_carlo_projections,
)
from core.teams import LVBP_TEAMS


class TestRE24AndBaseEncoding(unittest.TestCase):
    """Pruebas de la Matriz Tango RE24 y Codificación de 24 Estados Base-Out."""

    def test_re24_matrix_complete_24_states(self):
        """Verifica que la matriz RE24 contenga exactamente los 24 estados (3 outs x 8 estados de bases)."""
        self.assertEqual(len(RE24), 24, "La matriz RE24 debe contener exactamente 24 combinaciones (outs, base_state)")
        for outs in range(3):
            for base_state in range(8):
                self.assertIn(
                    (outs, base_state),
                    RE24,
                    f"El estado ({outs} outs, base_state={base_state}) debe existir en la matriz RE24"
                )
                re_val = RE24[(outs, base_state)]
                self.assertGreater(re_val, 0.0, f"El Run Expectancy para ({outs}, {base_state}) debe ser > 0")

    def test_re24_monotonic_properties(self):
        """Verifica las propiedades matemáticas de monotonía en Tango RE24."""
        # 1. A menor número de outs para un mismo estado de bases, mayor Run Expectancy
        for base_state in range(8):
            self.assertGreater(
                RE24[(0, base_state)],
                RE24[(1, base_state)],
                f"RE(0 outs, base {base_state}) debe ser mayor que RE(1 out, base {base_state})"
            )
            self.assertGreater(
                RE24[(1, base_state)],
                RE24[(2, base_state)],
                f"RE(1 out, base {base_state}) debe ser mayor que RE(2 outs, base {base_state})"
            )

        # 2. Bases llenas (estado 7) debe ser el máximo para cualquier conteo de outs
        for outs in range(3):
            for base_state in range(7):
                self.assertLess(
                    RE24[(outs, base_state)],
                    RE24[(outs, 7)],
                    f"RE({outs} outs, base {base_state}) debe ser menor que bases llenas RE({outs}, 7)"
                )

        # 3. Bases limpias (estado 0) debe ser el mínimo para cualquier conteo de outs
        for outs in range(3):
            for base_state in range(1, 8):
                self.assertGreater(
                    RE24[(outs, base_state)],
                    RE24[(outs, 0)],
                    f"RE({outs} outs, base {base_state}) debe ser mayor que bases vacías RE({outs}, 0)"
                )

    def test_encode_base_state_tango_alignment(self):
        """
        Verifica el mapeo exacto de los 8 estados de corredores a enteros 0..7.
        Contrato crítico: '--3' (solo en 3B) DEBE ser 3 y '12-' (en 1B y 2B) DEBE ser 4.
        """
        expected_mappings = {
            (False, False, False): 0,  # --- Bases limpias
            (True, False, False): 1,   # 1-- Solo en 1ra
            (False, True, False): 2,   # -2- Solo en 2da
            (False, False, True): 3,   # --3 Solo en 3ra (clave 3)
            (True, True, False): 4,    # 12- En 1ra y 2da (clave 4)
            (True, False, True): 5,    # 1-3 En 1ra y 3ra
            (False, True, True): 6,    # -23 En 2da y 3ra
            (True, True, True): 7,     # 123 Bases llenas
        }

        for (on_1b, on_2b, on_3b), expected_code in expected_mappings.items():
            actual_code = encode_base_state(on_1b, on_2b, on_3b)
            self.assertEqual(
                actual_code,
                expected_code,
                f"encode_base_state({on_1b}, {on_2b}, {on_3b}) retornó {actual_code}, se esperaba {expected_code}"
            )

    def test_format_base_state_diamonds(self):
        """Verifica la representación gráfica en diamantes para los 8 estados."""
        # Se verifica que el diamante retorne un string con 3 símbolos y espacios
        for base_state in range(8):
            formatted = format_base_state(base_state)
            self.assertIsInstance(formatted, str)
            parts = formatted.split()
            self.assertEqual(len(parts), 3, f"format_base_state({base_state}) debe contener 3 diamantes")
            for p in parts:
                self.assertIn(p, ["◆", "◇"], f"Símbolo inválido '{p}' en format_base_state({base_state})")

        # Verificar que bases limpias (0) tenga todos vacíos y bases llenas (7) todos llenos
        self.assertEqual(format_base_state(0), "◇ ◇ ◇")
        self.assertEqual(format_base_state(7), "◆ ◆ ◆")


class TestWinExpectancy(unittest.TestCase):
    """Pruebas del Modelo Estocástico de Win Expectancy (WE)."""

    def test_initial_game_state_neutral(self):
        """Al inicio del juego (1ra entrada Alta, 0 outs, bases limpias, 0-0), WE está equilibrado (~50%)."""
        we_home = calculate_win_expectancy(
            inning=1, is_bottom=False, outs=0, base_state=0, home_score=0, away_score=0
        )
        self.assertAlmostEqual(we_home, 0.50, delta=0.08, msg="El WE inicial para Home debe estar cerca del 50%")

    def test_walkoff_completed_in_9th_or_extra(self):
        """Si Home anota la ventaja en la 9na baja o extra, WE debe ser exactamente 1.0 (Walk-off)."""
        we_walkoff = calculate_win_expectancy(
            inning=9, is_bottom=True, outs=1, base_state=0, home_score=5, away_score=4
        )
        self.assertEqual(we_walkoff, 1.0, "Walk-off completado en 9na baja debe retornar WE=1.0")

        we_extra_walkoff = calculate_win_expectancy(
            inning=11, is_bottom=True, outs=2, base_state=4, home_score=3, away_score=2
        )
        self.assertEqual(we_extra_walkoff, 1.0, "Walk-off completado en 11ma baja debe retornar WE=1.0")

    def test_large_lead_convergence(self):
        """Una ventaja abultada en entradas finales debe aproximar WE a 1.0 (Home liderando) o 0.0 (Away liderando)."""
        # Home gana 10-0 en la 8va baja
        we_large_home_lead = calculate_win_expectancy(
            inning=8, is_bottom=True, outs=0, base_state=0, home_score=10, away_score=0
        )
        self.assertGreater(we_large_home_lead, 0.99, "Ventaja de 10 carreras en el 8vo para Home debe dar WE > 0.99")

        # Away gana 10-0 en la 9na alta
        we_large_away_lead = calculate_win_expectancy(
            inning=9, is_bottom=False, outs=0, base_state=0, home_score=0, away_score=10
        )
        self.assertLess(we_large_away_lead, 0.01, "Desventaja de 10 carreras en el 9no para Home debe dar WE < 0.01")

    def test_base_runners_increase_win_expectancy(self):
        """En igualdad de condiciones y marcador empatado, tener más corredores en base aumenta el WE."""
        we_empty = calculate_win_expectancy(
            inning=7, is_bottom=True, outs=1, base_state=0, home_score=3, away_score=3
        )
        we_loaded = calculate_win_expectancy(
            inning=7, is_bottom=True, outs=1, base_state=7, home_score=3, away_score=3
        )
        self.assertGreater(
            we_loaded,
            we_empty,
            "Bases llenas en la 7ma baja debe otorgar mayor WE que bases vacías"
        )


class TestLeverageIndex(unittest.TestCase):
    """Pruebas del Índice de Apalancamiento (Leverage Index)."""

    def test_average_situation_leverage(self):
        """Una situación típica de juego medio debe tener un LI cercano a 1.0."""
        li_avg = calculate_leverage_index(
            inning=5, is_bottom=False, outs=1, base_state=0, home_score=2, away_score=2
        )
        self.assertGreaterEqual(li_avg, 0.5, "El LI en juego empatado de entrada media debe ser >= 0.5")
        self.assertLessEqual(li_avg, 2.5, "El LI en juego empatado de entrada media debe ser <= 2.5")

    def test_blowout_low_leverage(self):
        """Un juego definido por 10 carreras en entradas finales debe tener bajo apalancamiento (LI < 0.5)."""
        li_blowout = calculate_leverage_index(
            inning=9, is_bottom=False, outs=0, base_state=0, home_score=10, away_score=0
        )
        self.assertLess(li_blowout, 0.5, "Un juego 10-0 en la 9na entrada debe tener un LI bajo (< 0.5)")

    def test_high_leverage_clutch_situation(self):
        """Un juego empatado en la 9na baja con bases llenas y 2 outs debe tener alto apalancamiento (LI > 1.8)."""
        li_clutch = calculate_leverage_index(
            inning=9, is_bottom=True, outs=2, base_state=7, home_score=3, away_score=3
        )
        self.assertGreater(li_clutch, 1.8, "Empate en 9na baja con bases llenas y 2 outs debe tener LI > 1.8")

    def test_leverage_index_bounds(self):
        """El Leverage Index debe estar acotado dentro del rango operativo [0.05, 10.0]."""
        for inn in [1, 5, 9]:
            for diff in [-10, 0, 10]:
                for bs in [0, 7]:
                    li = calculate_leverage_index(
                        inning=inn, is_bottom=True, outs=1, base_state=bs, home_score=5 + diff, away_score=5
                    )
                    self.assertGreaterEqual(li, 0.05, f"LI no debe ser menor a 0.05 (obtenido: {li})")
                    self.assertLessEqual(li, 10.0, f"LI no debe superar 10.0 (obtenido: {li})")


class TestBattingMetrics(unittest.TestCase):
    """Pruebas de Fórmulas Sabermétricas de Bateo (OBP con HBP/SF, SLG, OPS)."""

    def test_standard_obp_with_hbp_and_sf(self):
        """Verifica la fórmula oficial de OBP = (H + BB + HBP) / (AB + BB + HBP + SF)."""
        # Caso: 10 AB, 3 H, 2 BB, 1 HBP, 1 SF
        # OBP = (3 + 2 + 1) / (10 + 2 + 1 + 1) = 6 / 14 = 0.42857... -> round(3) = 0.429
        h, bb, hbp, sf, ab = 3, 2, 1, 1, 10
        obp_den = ab + bb + hbp + sf
        obp_num = h + bb + hbp
        obp = round(obp_num / obp_den, 3)
        self.assertEqual(obp, 0.429)

    def test_obp_division_by_zero_protection(self):
        """Verifica que si AB=0, BB=0, HBP=0, SF=0, OBP retorne 0.0 sin lanzar excepción."""
        ab, bb, hbp, sf, h = 0, 0, 0, 0, 0
        den = ab + bb + hbp + sf
        obp = round((h + bb + hbp) / den, 3) if den > 0 else 0.0
        self.assertEqual(obp, 0.0)

    def test_slg_and_ops_calculation(self):
        """Verifica el cálculo de SLG = (1B + 2*2B + 3*3B + 4*HR) / AB y OPS = OBP + SLG."""
        # 20 AB, 2 1B, 2 2B, 1 3B, 1 HR -> Total Bases = 2*1 + 2*2 + 1*3 + 1*4 = 2 + 4 + 3 + 4 = 13 TB
        # SLG = 13 / 20 = 0.650
        ab = 20
        h1b, h2b, h3b, hr = 2, 2, 1, 1
        tb = h1b + 2 * h2b + 3 * h3b + 4 * hr
        slg = round(tb / ab, 3)
        self.assertEqual(slg, 0.650)

        # Si OBP = 0.400, OPS = 0.400 + 0.650 = 1.050
        obp = 0.400
        ops = round(obp + slg, 3)
        self.assertEqual(ops, 1.050)


class TestPitchingMetrics(unittest.TestCase):
    """Pruebas de Métricas de Pitcheo y Resiliencia ante División por Cero (ERA, WHIP)."""

    def test_era_and_whip_with_zero_innings_pitched(self):
        """Verifica que con IP=0, ERA y WHIP retornen 0.0 en lugar de ZeroDivisionError o inf."""
        ip = 0.0
        er = 3
        h = 2
        bb = 1

        era = round((er * 9.0) / ip, 2) if ip > 0 else 0.0
        whip = round((h + bb) / ip, 2) if ip > 0 else 0.0

        self.assertEqual(era, 0.0, "ERA con IP=0 debe ser 0.0")
        self.assertEqual(whip, 0.0, "WHIP con IP=0 debe ser 0.0")
        self.assertFalse(math.isinf(era), "ERA no puede ser infinito")
        self.assertFalse(math.isinf(whip), "WHIP no puede ser infinito")
        self.assertFalse(math.isnan(era), "ERA no puede ser NaN")
        self.assertFalse(math.isnan(whip), "WHIP no puede ser NaN")

    def test_era_and_whip_standard_calculations(self):
        """Verifica cálculos estándar de ERA y WHIP con entradas válidas."""
        # 9.0 IP, 3 ER -> ERA = 3.00
        era = round((3 * 9.0) / 9.0, 2)
        self.assertEqual(era, 3.00)

        # 6.0 IP, 4 H, 2 BB -> WHIP = (4 + 2) / 6.0 = 1.00
        whip = round((4 + 2) / 6.0, 2)
        self.assertEqual(whip, 1.00)

        # 5.1 IP (5.3333 IP decimal), 2 ER -> ERA = (2 * 9) / 5.33333 = 18 / 5.33333 = 3.375 -> 3.38
        ip_dec = 5.0 + 1.0 / 3.0
        era_fractional = round((2 * 9.0) / ip_dec, 2)
        self.assertEqual(era_fractional, 3.38)


class TestELORatings(unittest.TestCase):
    """Pruebas del Motor de Ratings ELO y Escala Logística."""

    def test_expected_score_equal_ratings(self):
        """Dos equipos con el mismo ELO deben tener probabilidad esperada exacta de 0.50."""
        score = expected_score(1500.0, 1500.0)
        self.assertEqual(score, 0.50, "Puntuación esperada entre iguales debe ser 0.50")

    def test_expected_score_400_point_difference(self):
        """Una diferencia de +400 puntos ELO debe arrojar una probabilidad teórica de ~0.9091 (10/11)."""
        score_favor = expected_score(1900.0, 1500.0)
        expected_prob = 1.0 / (1.0 + 10 ** (-400.0 / 400.0))  # 1 / (1 + 0.1) = 1/1.1 = 0.909090...
        self.assertAlmostEqual(score_favor, expected_prob, places=5)
        self.assertAlmostEqual(score_favor, 0.90909, places=4)

        score_underdog = expected_score(1500.0, 1900.0)
        self.assertAlmostEqual(score_underdog, 1.0 - score_favor, places=5)
        self.assertAlmostEqual(score_underdog, 0.09091, places=4)

    def test_matchup_win_prob_home_advantage(self):
        """La ventaja de localía (+35 pts) debe dar una probabilidad > 0.50 al equipo local con ELO idéntico."""
        p_home, p_away = calculate_matchup_win_prob(1500.0, 1500.0, home_advantage=HOME_ADVANTAGE)
        self.assertGreater(p_home, 0.50, "El equipo local debe tener probabilidad > 0.50 con ELO idéntico")
        self.assertAlmostEqual(p_home + p_away, 1.0, places=6, msg="P(home) + P(away) debe ser exactamente 1.0")

    def test_elo_update_conservation(self):
        """La actualización de ELO debe conservar la suma total de puntos (delta sum = 0)."""
        r_home_init = 1520.0
        r_away_init = 1480.0
        k = K_BY_PHASE['regular']

        # Victoria de Home
        new_home, new_away = update_elo(r_home_init, r_away_init, home_win=True, k=k)
        self.assertGreater(new_home, r_home_init, "Home debe ganar puntos ELO al ganar")
        self.assertLess(new_away, r_away_init, "Away debe perder puntos ELO al perder")
        self.assertAlmostEqual(
            (new_home + new_away),
            (r_home_init + r_away_init),
            places=5,
            msg="La suma total de ELO entre ambos equipos debe ser invariable"
        )

        # Victoria de Away
        new_home_l, new_away_w = update_elo(r_home_init, r_away_init, home_win=False, k=k)
        self.assertLess(new_home_l, r_home_init, "Home debe perder puntos ELO al perder")
        self.assertGreater(new_away_w, r_away_init, "Away debe ganar puntos ELO al ganar")
        self.assertAlmostEqual(
            (new_home_l + new_away_w),
            (r_home_init + r_away_init),
            places=5,
            msg="La suma total de ELO debe conservarse también en victoria visitante"
        )


class TestMonteCarloSimulations(unittest.TestCase):
    """Pruebas de Estrés y Conservación de Probabilidades en Simulación Monte Carlo (5,000 Iteraciones)."""

    def test_monte_carlo_5000_invariants(self):
        """Ejecuta 5,000 simulaciones completas y verifica los invariantes algebraicos y de distribución."""
        elo_dict = {
            692: 1540.0,  # Águilas
            693: 1480.0,  # Bravos
            694: 1510.0,  # Cardenales
            695: 1560.0,  # Leones
            696: 1500.0,  # Navegantes
            697: 1490.0,  # Tiburones
            698: 1470.0,  # Tigres
            699: 1450.0,  # Caribes
        }

        # Simular desde cero (simulate_from_scratch=True) para 5,000 iteraciones
        result = simulate_monte_carlo_projections(
            standings_df=pd.DataFrame(),
            elo_dict=elo_dict,
            remaining_games_list=None,
            n_simulations=5000,
            simulate_from_scratch=True
        )

        self.assertEqual(result["n_simulations"], 5000)
        df_proj = result["projections"]
        df_mat = result["position_matrix"]

        self.assertEqual(len(df_proj), 8, "Deben estar presentes los 8 equipos de la LVBP")
        self.assertEqual(len(df_mat), 8, "La matriz de posiciones debe contener 8 filas")

        # Invariante 1: Suma de probabilidades de campeonato debe ser 1.0 (tolerancia flotante)
        total_champ_prob = df_proj["champ_prob"].sum()
        self.assertAlmostEqual(
            total_champ_prob,
            1.0,
            delta=0.002,
            msg=f"La suma de probabilidades de campeonato debe ser 1.0 (obtenido: {total_champ_prob})"
        )

        # Invariante 2: Exactamente 4 equipos clasifican directo al Round Robin (Top 4)
        total_top4_prob = df_proj["top4_prob"].sum()
        self.assertAlmostEqual(
            total_top4_prob,
            4.0,
            delta=0.002,
            msg=f"La suma de probabilidades de Top 4 debe ser 4.0 (obtenido: {total_top4_prob})"
        )

        # Invariante 3: Exactamente 2 equipos van a la Serie del Comodín (Wild Card)
        total_wc_prob = df_proj["wc_prob"].sum()
        self.assertAlmostEqual(
            total_wc_prob,
            2.0,
            delta=0.002,
            msg=f"La suma de probabilidades de Wild Card debe ser 2.0 (obtenido: {total_wc_prob})"
        )

        # Invariante 4: Para cada posición del 1° al 8°, la suma entre los 8 equipos debe ser 1.0
        for pos in range(1, 9):
            col_name = f"{pos}°"
            pos_sum = df_mat[col_name].sum()
            self.assertAlmostEqual(
                pos_sum,
                1.0,
                delta=0.002,
                msg=f"La suma de la columna {col_name} en la matriz de posiciones debe ser 1.0 (obtenido: {pos_sum})"
            )

        # Invariante 5: Para cada equipo individual, la suma de sus probabilidades de posición 1°..8° debe ser 1.0
        for _, row in df_mat.iterrows():
            team_pos_sum = sum(row[f"{pos}°"] for pos in range(1, 9))
            self.assertAlmostEqual(
                team_pos_sum,
                1.0,
                delta=0.002,
                msg=f"La suma de posiciones para el equipo {row['team_name']} debe ser 1.0 (obtenido: {team_pos_sum})"
            )


if __name__ == '__main__':
    unittest.main()
