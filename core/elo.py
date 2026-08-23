# utils/elo.py
"""
Motor de Ratings ELO y Simulaciones Probabilísticas Monte Carlo para la LVBP.
Calcula probabilidades de victoria en partidos y proyecta probabilidades de:
- Posición en Ronda Regular (1° al 8°)
- Clasificación directa a Round Robin (Top 4)
- Clasificación a Serie del Comodín / Wild Card (5° y 6°)
- Avance a Gran Final y Campeonato LVBP
"""
import random
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional, Any

BASE_ELO = 1500
HOME_ADVANTAGE = 35
K_BY_PHASE = {
    'regular': 20,
    'wildcard_playin': 25,
    'round_robin': 22,
    'final': 28,
    'unknown': 20,
}

try:
    from core.teams import (
        LVBP_TEAMS,
        LVBP_ABBR,
        LVBP_COLORS,
        get_team_logo,
        get_team_name,
        get_team_abbr,
        get_team_color,
        resolve_team_id
    )
except ImportError:
    from streamlit_app.core.teams import (
        LVBP_TEAMS,
        LVBP_ABBR,
        LVBP_COLORS,
        get_team_logo,
        get_team_name,
        get_team_abbr,
        get_team_color,
        resolve_team_id
    )


def expected_score(r_a: float, r_b: float) -> float:
    """Probabilidad esperada de A contra B con escala logística base 400."""
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))


def calculate_matchup_win_prob(
    elo_home: float,
    elo_away: float,
    home_advantage: float = HOME_ADVANTAGE
) -> Tuple[float, float]:
    """
    Calcula la probabilidad de victoria para el equipo Local y Visitante
    considerando la ventaja de localía.
    """
    p_home = expected_score(elo_home + home_advantage, elo_away)
    return p_home, 1.0 - p_home


def update_elo(
    r_home: float,
    r_away: float,
    home_win: bool,
    k: float,
    home_advantage: float = HOME_ADVANTAGE
) -> Tuple[float, float]:
    """Actualiza ELO de local y visitante de forma determinista tras un partido."""
    home_effective = r_home + home_advantage
    exp_home = expected_score(home_effective, r_away)
    score_home = 1.0 if home_win else 0.0

    delta = k * (score_home - exp_home)
    new_home = r_home + delta
    new_away = r_away - delta
    return new_home, new_away


def simulate_game(
    elo_home: float,
    elo_away: float,
    home_advantage: float = HOME_ADVANTAGE
) -> bool:
    """Retorna True si gana el equipo Local, False si gana Visitante."""
    p_home, _ = calculate_matchup_win_prob(elo_home, elo_away, home_advantage)
    return random.random() < p_home


def simulate_wildcard_series(
    team_5_id: int,
    team_6_id: int,
    elo_dict: Dict[int, float],
    home_advantage: float = HOME_ADVANTAGE
) -> int:
    """
    Simula la Serie del Comodín de la LVBP:
    El 5to lugar juega de local y clasifica ganando 1 juego.
    El 6to lugar debe ganar 2 juegos de visitante para clasificar.
    """
    elo_5 = elo_dict.get(team_5_id, BASE_ELO)
    elo_6 = elo_dict.get(team_6_id, BASE_ELO)
    
    # Juego 1 (en casa del 5to)
    if simulate_game(elo_5, elo_6, home_advantage):
        return team_5_id  # 5to clasifica con 1 victoria
        
    # Juego 2 (en casa del 5to si el 6to ganó el primero)
    if simulate_game(elo_5, elo_6, home_advantage):
        return team_5_id
    else:
        return team_6_id


def simulate_round_robin(
    qualifiers: List[int],
    elo_dict: Dict[int, float],
    home_advantage: float = HOME_ADVANTAGE
) -> Tuple[int, int]:
    """
    Simula el Round Robin de 5 equipos (16 juegos cada uno, 40 juegos totales).
    Retorna los 2 equipos clasificados a la Gran Final.
    """
    rr_wins = {t: 0 for t in qualifiers}
    
    for i in range(len(qualifiers)):
        for j in range(i + 1, len(qualifiers)):
            t1, t2 = qualifiers[i], qualifiers[j]
            elo_1 = elo_dict.get(t1, BASE_ELO)
            elo_2 = elo_dict.get(t2, BASE_ELO)
            
            # 2 juegos t1 local, t2 visitante
            for _ in range(2):
                if simulate_game(elo_1, elo_2, home_advantage):
                    rr_wins[t1] += 1
                else:
                    rr_wins[t2] += 1
                    
            # 2 juegos t2 local, t1 visitante
            for _ in range(2):
                if simulate_game(elo_2, elo_1, home_advantage):
                    rr_wins[t2] += 1
                else:
                    rr_wins[t1] += 1
                    
    # Ordenar por victorias (desempate con ELO + ruido aleatorio)
    sorted_rr = sorted(
        qualifiers,
        key=lambda t: (rr_wins[t], elo_dict.get(t, BASE_ELO) + random.random() * 0.01),
        reverse=True
    )
    return sorted_rr[0], sorted_rr[1]


def simulate_final_series(
    team_1_id: int,
    team_2_id: int,
    elo_dict: Dict[int, float],
    home_advantage: float = HOME_ADVANTAGE
) -> int:
    """
    Simula la Serie Final al mejor de 7 juegos (formato 2-3-2 de localía).
    Retorna el ID del equipo Campeón.
    """
    elo_1 = elo_dict.get(team_1_id, BASE_ELO)
    elo_2 = elo_dict.get(team_2_id, BASE_ELO)
    
    w1, w2 = 0, 0
    home_pattern = [team_1_id, team_1_id, team_2_id, team_2_id, team_2_id, team_1_id, team_1_id]
    
    for h in home_pattern:
        if h == team_1_id:
            if simulate_game(elo_1, elo_2, home_advantage):
                w1 += 1
            else:
                w2 += 1
        else:
            if simulate_game(elo_2, elo_1, home_advantage):
                w2 += 1
            else:
                w1 += 1
                
        if w1 == 4:
            return team_1_id
        if w2 == 4:
            return team_2_id
            
    return team_1_id if w1 > w2 else team_2_id


def generate_balanced_regular_schedule() -> List[Tuple[int, int]]:
    """Genera calendario balanceado de 56 juegos por equipo (224 juegos totales)."""
    schedule = []
    teams = list(LVBP_TEAMS.keys())
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            t1, t2 = teams[i], teams[j]
            for _ in range(4):
                schedule.append((t1, t2))
                schedule.append((t2, t1))
    return schedule


def simulate_monte_carlo_projections(
    standings_df: pd.DataFrame,
    elo_dict: Dict[int, float],
    remaining_games_list: Optional[List[Tuple[int, int]]] = None,
    n_simulations: int = 5000,
    simulate_from_scratch: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta simulaciones Monte Carlo para proyectar probabilidades de clasificación
    y campeonato para todos los equipos de la LVBP.
    """
    teams_list = list(LVBP_TEAMS.keys())
    
    # Inicializar contadores
    pos_matrix = {t: [0] * 8 for t in teams_list}
    top4_counts = {t: 0 for t in teams_list}
    wc_counts = {t: 0 for t in teams_list}
    rr_counts = {t: 0 for t in teams_list}
    final_counts = {t: 0 for t in teams_list}
    champ_counts = {t: 0 for t in teams_list}
    
    # Extraer victorias actuales de standings_df si existen
    current_wins = {t: 0 for t in teams_list}
    current_losses = {t: 0 for t in teams_list}
    if not standings_df.empty and 'team_id' in standings_df.columns and not simulate_from_scratch:
        for _, row in standings_df.iterrows():
            tid = int(row['team_id'])
            if tid in current_wins:
                current_wins[tid] = int(row.get('wins', 0))
                current_losses[tid] = int(row.get('losses', 0))
                
    # Determinar si la temporada regular ya terminó o tiene juegos restantes
    total_played = sum(current_wins.values()) + sum(current_losses.values())
    regular_season_completed = (total_played >= 224 and not simulate_from_scratch) or (remaining_games_list is not None and len(remaining_games_list) == 0 and not simulate_from_scratch)
    
    balanced_sched = generate_balanced_regular_schedule()
    
    for _ in range(n_simulations):
        if regular_season_completed:
            # Si la temporada regular terminó, el orden se toma directamente de la tabla
            ranked = list(standings_df.sort_values('pct', ascending=False)['team_id'])
            # Asegurar que estén los 8 equipos
            for t in teams_list:
                if t not in ranked:
                    ranked.append(t)
        elif simulate_from_scratch:
            # Simular los 224 juegos completos
            sim_wins = {t: 0 for t in teams_list}
            for h, a in balanced_sched:
                if simulate_game(elo_dict.get(h, BASE_ELO), elo_dict.get(a, BASE_ELO)):
                    sim_wins[h] += 1
                else:
                    sim_wins[a] += 1
            ranked = sorted(teams_list, key=lambda t: (sim_wins[t], elo_dict.get(t, BASE_ELO) + random.random() * 0.01), reverse=True)
        else:
            # Simular a partir del récord actual + juegos restantes
            sim_wins = dict(current_wins)
            sched = remaining_games_list if remaining_games_list is not None else []
            for h, a in sched:
                if simulate_game(elo_dict.get(h, BASE_ELO), elo_dict.get(a, BASE_ELO)):
                    sim_wins[h] += 1
                else:
                    sim_wins[a] += 1
            ranked = sorted(teams_list, key=lambda t: (sim_wins[t], elo_dict.get(t, BASE_ELO) + random.random() * 0.01), reverse=True)
            
        # 1. Contabilizar posiciones regulares
        for r_idx, t in enumerate(ranked[:8]):
            pos_matrix[t][r_idx] += 1
            if r_idx < 4:
                top4_counts[t] += 1
            elif r_idx < 6:
                wc_counts[t] += 1
                
        # 2. Serie Wild Card (5to vs 6to)
        t5, t6 = ranked[4], ranked[5]
        wc_winner = simulate_wildcard_series(t5, t6, elo_dict)
        
        # 3. Round Robin (Top 4 + Ganador Wild Card)
        rr_qualifiers = ranked[:4] + [wc_winner]
        for q in rr_qualifiers:
            rr_counts[q] += 1
            
        f1, f2 = simulate_round_robin(rr_qualifiers, elo_dict)
        final_counts[f1] += 1
        final_counts[f2] += 1
        
        # 4. Gran Final
        champ = simulate_final_series(f1, f2, elo_dict)
        champ_counts[champ] += 1

    # Construir DataFrames de resultados
    res_rows = []
    matrix_rows = []
    
    for t in teams_list:
        name = LVBP_TEAMS.get(t, f"Equipo {t}")
        current_elo = elo_dict.get(t, BASE_ELO)
        
        res_rows.append({
            "team_id": t,
            "team_name": name,
            "elo": current_elo,
            "top4_prob": top4_counts[t] / n_simulations,
            "wc_prob": wc_counts[t] / n_simulations,
            "rr_prob": rr_counts[t] / n_simulations,
            "final_prob": final_counts[t] / n_simulations,
            "champ_prob": champ_counts[t] / n_simulations
        })
        
        mat_row = {"team_id": t, "team_name": name, "elo": current_elo}
        for pos in range(8):
            mat_row[f"{pos+1}°"] = pos_matrix[t][pos] / n_simulations
        matrix_rows.append(mat_row)
        
    df_projections = pd.DataFrame(res_rows).sort_values("champ_prob", ascending=False).reset_index(drop=True)
    df_matrix = pd.DataFrame(matrix_rows).sort_values("elo", ascending=False).reset_index(drop=True)
    
    return {
        "n_simulations": n_simulations,
        "is_completed_season": regular_season_completed,
        "projections": df_projections,
        "position_matrix": df_matrix
    }
