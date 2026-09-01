# republicaraquistapp/pages/standings.py
"""
standings.py
------------
Vista completa de Posiciones, Sabermetría Pitagórica, Ratings ELO,
Simulaciones Monte Carlo (5,000 Iteraciones), Predictor H2H y Semanas ISO (Ruta /standings).
Contiene 4 pestañas interactivas:
1. 📊 Tabla Oficial (Posiciones con selector de fases, KPIs de Leones y glosario).
2. 🧮 Sabermetría Pitagórica (Bill James / Davenport 1.83, xW, xL, Delta W y diagnóstico).
3. ⚡ ELO & Monte Carlo (Proyecciones 5k simulaciones, Matriz 1°-8°, Predictor H2H y Power Rankings).
4. 📅 Día/Noche & Semanas ISO (Desglose situacional y récord semana a semana ISO).
"""

from typing import Any, Optional, Dict
import reflex as rx

from republicaraquistapp.styles.theme import (
    ACCENT_GOLD,
    GOLD_HOVER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_DIM,
    BORDER_CARD,
    BORDER_SUBTLE,
    BORDER_GOLD,
    CARD_STYLE,
    GOLD_BADGE_STYLE,
    CARD_BG,
    NAVY_PRIMARY,
)
from republicaraquistapp.state.standings_state import (
    StandingsState,
    PHASE_LABELS,
    ELO_PHASE_LABELS,
)
from republicaraquistapp.components.layout import layout


# ═════════════════════════════════════════════════════════════════════════════
# 1. PESTAÑA 1: TABLA OFICIAL DE POSICIONES
# ═════════════════════════════════════════════════════════════════════════════

def official_standings_row(team: dict) -> rx.Component:
    """Fila de la tabla de posiciones con estilo condicional dorado para Leones."""
    return rx.table.row(
        rx.table.cell(
            rx.text(team["pos_str"], font_weight="700", color=team["text_color"], text_align="center")
        ),
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="26px", height="26px"),
                rx.text(team["team_name"], font_weight="700", color=team["text_color"]),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(team["games"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(team["wins"], font_weight="700", color="var(--green-9)", text_align="center")),
        rx.table.cell(rx.text(team["losses"], font_weight="700", color="var(--red-9)", text_align="center")),
        rx.table.cell(rx.text(team["pct"], font_weight="700", color=team["text_color"], text_align="center")),
        rx.table.cell(rx.text(team["gb"], color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(team["home"], color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(team["away"], color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(team["rf"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(team["ra"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(
            rx.text(
                team["diff"],
                font_weight="700",
                color=team["diff_color"],
                text_align="center",
            )
        ),
        rx.table.cell(
            rx.badge(
                team["streak"],
                color_scheme=team["streak_color"],
                variant="soft",
                size="1",
            )
        ),
        rx.table.cell(rx.text(team["l10"], color=TEXT_MUTED, text_align="center")),
        background=team["row_bg"],
        border_left=team["row_border"],
    )


def tab_official_standings() -> rx.Component:
    """Contenido de la Pestaña 1: Tabla Oficial de Posiciones y Resumen."""
    return rx.vstack(
        # Controles y Selector de Fase
        rx.hstack(
            rx.vstack(
                rx.text("FASE DEL TORNEO", size="1", color=TEXT_MUTED, font_weight="700"),
                rx.select(
                    [
                        "regular",
                        "round_robin",
                        "wildcard_playin",
                        "final",
                        "all",
                    ],
                    value=StandingsState.selected_phase,
                    on_change=StandingsState.set_phase,
                    size="2",
                    variant="surface",
                    color_scheme="amber",
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.badge(
                f"Fase: {StandingsState.selected_phase_label}",
                style=GOLD_BADGE_STYLE,
            ),
            align="center",
            width="100%",
            padding_bottom="0.5rem",
        ),

        # Tabla de Posiciones
        rx.box(
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("POS"),
                            rx.table.column_header_cell("EQUIPO"),
                            rx.table.column_header_cell("JJ"),
                            rx.table.column_header_cell("G"),
                            rx.table.column_header_cell("P"),
                            rx.table.column_header_cell("PCT"),
                            rx.table.column_header_cell("JD"),
                            rx.table.column_header_cell("LOCAL"),
                            rx.table.column_header_cell("VISITANTE"),
                            rx.table.column_header_cell("CF"),
                            rx.table.column_header_cell("CP"),
                            rx.table.column_header_cell("DIF"),
                            rx.table.column_header_cell("RACHA"),
                            rx.table.column_header_cell("L10"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(StandingsState.standings_data, official_standings_row)
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                overflow_x="auto",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # Resumen Destacado de los Leones del Caracas
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("award", size=18, color=ACCENT_GOLD),
                        rx.heading("RESUMEN OFICIAL — LEONES DEL CARACAS", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.badge("Caracas 🦁", color_scheme="amber", variant="soft", size="1"),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("POSICIÓN OFICIAL", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_kpis["posicion"], size="6", color=ACCENT_GOLD, font_weight="800"),
                        rx.text("Clasificación general", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("RÉCORD W - L", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_kpis["record"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text(f"PCT: {StandingsState.leones_kpis['pct']}", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("JUEGOS DETRÁS (JD)", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_kpis["gb"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text("Distancia al 1er lugar", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("DIFERENCIAL DE CARRERAS", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_kpis["run_diff"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text(f"CF: {StandingsState.leones_kpis['rf']} | CP: {StandingsState.leones_kpis['ra']}", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("RACHA ACTUAL", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_kpis["streak"], size="6", color=ACCENT_GOLD, font_weight="800"),
                        rx.text(f"L10: {StandingsState.leones_kpis['l10']}", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    columns=rx.breakpoints(initial="2", sm="3", md="5"),
                    spacing="4",
                    width="100%",
                    padding_y="0.5rem",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # Glosario Expandible de la Tabla de Posiciones
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon("book-open", size=16, color=ACCENT_GOLD),
                    rx.text("Guía y Glosario: ¿Cómo entender la Tabla de Clasificación de la LVBP?", size="2", font_weight="600", color=TEXT_PRIMARY),
                    spacing="2",
                    align="center",
                ),
                content=rx.vstack(
                    rx.text(
                        "• POS (#): Posición que ocupa el equipo. Los puestos 1° al 4° clasifican directo al Round Robin; "
                        "el 5° y 6° disputan la Serie del Comodín (Wild Card).\n"
                        "• JJ (Juegos Jugados): Total de compromisos disputados (JJ = G + P). Ronda regular consta de 56 JJ.\n"
                        "• G / P: Victorias y Derrotas oficiales en la fase.\n"
                        "• PCT (Porcentaje): Proporción de triunfos (G / JJ) expresado con 3 decimales (.550 = 55% de victorias).\n"
                        "• JD (Juegos de Diferencia / Games Back): Distancia aritmética respecto al líder: [(G_líder - G) + (P - P_líder)] / 2.\n"
                        "• CF / CP: Carreras a Favor (ofensiva) y Carreras Permitidas (pitcheo y defensa).\n"
                        "• DIF: Diferencial neto (CF - CP). Un diferencial positivo indica dominio ofensivo y solidez monticular.",
                        size="2",
                        color=TEXT_MUTED,
                        line_height="1.6",
                    ),
                    padding="1rem",
                ),
            ),
            variant="ghost",
            collapsible=True,
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ═════════════════════════════════════════════════════════════════════════════
# 2. PESTAÑA 2: SABERMETRÍA PITAGÓRICA (BILL JAMES / DAVENPORT 1.83)
# ═════════════════════════════════════════════════════════════════════════════

def pythagorean_row(team: dict) -> rx.Component:
    """Fila para la tabla sabermétrica pitagórica."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="24px", height="24px"),
                rx.text(team["team_name"], font_weight="700", color=team["text_color"]),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(team["wins_real"], font_weight="700", color="var(--green-9)", text_align="center")),
        rx.table.cell(rx.text(team["losses_real"], font_weight="700", color="var(--red-9)", text_align="center")),
        rx.table.cell(rx.text(team["rf"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(team["ra"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(team["run_diff"], font_weight="700", color=team["text_color"], text_align="center")),
        rx.table.cell(rx.text(team["pct_real"], font_weight="600", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(team["pyth_pct"], font_weight="700", color=ACCENT_GOLD, text_align="center")),
        rx.table.cell(rx.text(team["xw"], font_weight="800", color=ACCENT_GOLD, text_align="center")),
        rx.table.cell(rx.text(team["xl"], font_weight="600", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(team["w_diff"], font_weight="700", color=team["diag_color"], text_align="center")),
        rx.table.cell(
            rx.badge(team["diagnostico"], color_scheme="gray", variant="soft", size="1")
        ),
        background=team["row_bg"],
    )


def tab_pythagorean_standings() -> rx.Component:
    """Contenido de la Pestaña 2: Expectativa Pitagórica de Victorias."""
    return rx.vstack(
        # Encabezado Metodológico
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("calculator", size=20, color=ACCENT_GOLD),
                    rx.heading("EXPECTATIVA PITAGÓRICA DE VICTORIAS", size="4", color=TEXT_PRIMARY, font_weight="800"),
                    rx.spacer(),
                    rx.badge("Fórmula Bill James / Davenport 1.83", style=GOLD_BADGE_STYLE),
                    align="center",
                    width="100%",
                ),
                rx.text(
                    "El modelo pitagórico calcula cuántos partidos debió haber ganado un equipo según "
                    "sus carreras anotadas (CF) y permitidas (CP): W% = CF^1.83 / (CF^1.83 + CP^1.83). "
                    "El diferencial (G - xW) mide el factor clutch y sobre/sub-rendimiento estocástico.",
                    size="2",
                    color=TEXT_MUTED,
                    line_height="1.5",
                ),
                spacing="2",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # KPIs Pitagóricos de Leones del Caracas
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("activity", size=18, color=ACCENT_GOLD),
                        rx.heading("LEONES DEL CARACAS — BALANCE PITAGÓRICO", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.badge(StandingsState.leones_pythagorean["diagnostico"], color_scheme="amber", variant="soft", size="1"),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("VICTORIAS REALES", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_pythagorean["wins_real"], size="6", color="var(--green-9)", font_weight="800"),
                        rx.text("Ganados en terreno", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("VICTORIAS ESPERADAS (xW)", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_pythagorean["xw"], size="6", color=ACCENT_GOLD, font_weight="800"),
                        rx.text(f"PCT Pit: {StandingsState.leones_pythagorean['pyth_pct']}", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("DIFERENCIAL (G - xW)", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_pythagorean["w_diff"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text("Factor Clutch / Suerte", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("CARRERAS ANOTADAS / J", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_pythagorean["rf_per_g"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text("Producción ofensiva", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("CARRERAS PERMITIDAS / J", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_pythagorean["ra_per_g"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text("Pitcheo y defensa", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    columns=rx.breakpoints(initial="2", sm="3", md="5"),
                    spacing="4",
                    width="100%",
                    padding_y="0.5rem",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # Tabla Completa Pitagórica
        rx.box(
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("EQUIPO"),
                            rx.table.column_header_cell("G REAL"),
                            rx.table.column_header_cell("P REAL"),
                            rx.table.column_header_cell("CF"),
                            rx.table.column_header_cell("CP"),
                            rx.table.column_header_cell("DIF"),
                            rx.table.column_header_cell("PCT REAL"),
                            rx.table.column_header_cell("PCT PIT"),
                            rx.table.column_header_cell("xW (ESP)"),
                            rx.table.column_header_cell("xL (ESP)"),
                            rx.table.column_header_cell("DIF (G-xW)"),
                            rx.table.column_header_cell("DIAGNÓSTICO"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(StandingsState.pythagorean_data, pythagorean_row)
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                overflow_x="auto",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # Glosario Pitagórico Expandible
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon("circle-help", size=16, color=ACCENT_GOLD),
                    rx.text("Guía: ¿Cómo interpretar el factor clutch y la suerte pitagórica?", size="2", font_weight="600", color=TEXT_PRIMARY),
                    spacing="2",
                    align="center",
                ),
                content=rx.vstack(
                    rx.text(
                        "• xW (Victorias Esperadas): Cuántos juegos debió ganar un equipo según su balance anotador.\n"
                        "• Dif (G - xW) >= +1.5 (🔥 Sobre-rendimiento / Clutch): El equipo ha ganado más partidos de lo que indican "
                        "sus carreras, generalmente por excelencia en juegos de 1 carrera o bateo oportuno con corredores en base.\n"
                        "• Dif (G - xW) <= -1.5 (❄️ Sub-rendimiento / Mala Suerte): El equipo juega mejor de lo que sugiere su récord, "
                        "pero ha perdido partidos cerrados por fallas en las postrimerías o mala fortuna en pelotas en juego (BABIP).\n"
                        "• Dif cercano a 0 (⚖️ En línea): El récord refleja con exactitud la calidad y producción del conjunto.",
                        size="2",
                        color=TEXT_MUTED,
                        line_height="1.6",
                    ),
                    padding="1rem",
                ),
            ),
            variant="ghost",
            collapsible=True,
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ═════════════════════════════════════════════════════════════════════════════
# 3. PESTAÑA 3: SUITE ELO & SIMULACIONES MONTE CARLO (5,000 ITERACIONES)
# ═════════════════════════════════════════════════════════════════════════════

def monte_carlo_proj_row(team: dict) -> rx.Component:
    """Fila de la tabla de probabilidades de postemporada Monte Carlo."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="24px", height="24px"),
                rx.text(team["team_name"], font_weight="700", color=team["text_color"]),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(team["elo_fmt"], font_weight="700", color=ACCENT_GOLD, text_align="center")),
        rx.table.cell(rx.text(team["top4_prob"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(team["wc_prob"], color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(team["rr_prob"], font_weight="700", color="var(--green-9)", text_align="center")),
        rx.table.cell(rx.text(team["final_prob"], font_weight="700", color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(
            rx.badge(
                team["champ_prob"],
                color_scheme="amber",
                variant="solid",
                size="1",
            )
        ),
        background=team["row_bg"],
    )


def position_matrix_row(team: dict) -> rx.Component:
    """Fila para la matriz de probabilidad de posición 1° al 8°."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="22px", height="22px"),
                rx.text(team["team_name"], font_weight="700", color=team["text_color"]),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(team["elo_fmt"], font_weight="700", color=ACCENT_GOLD, text_align="center")),
        rx.table.cell(rx.text(team["p1"], text_align="center")),
        rx.table.cell(rx.text(team["p2"], text_align="center")),
        rx.table.cell(rx.text(team["p3"], text_align="center")),
        rx.table.cell(rx.text(team["p4"], text_align="center")),
        rx.table.cell(rx.text(team["p5"], text_align="center")),
        rx.table.cell(rx.text(team["p6"], text_align="center")),
        rx.table.cell(rx.text(team["p7"], text_align="center")),
        rx.table.cell(rx.text(team["p8"], text_align="center")),
        background=team["row_bg"],
    )


def elo_ranking_row(team: dict) -> rx.Component:
    """Fila de la tabla de Power Rankings ELO oficiales."""
    return rx.table.row(
        rx.table.cell(rx.text(team["rank_str"], font_weight="700", color=team["text_color"], text_align="center")),
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="24px", height="24px"),
                rx.text(team["team_name"], font_weight="700", color=team["text_color"]),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(team["elo_fmt"], font_weight="800", color=ACCENT_GOLD, text_align="center")),
        rx.table.cell(rx.text(team["diff_from_base"], font_weight="700", color=team["diff_color"], text_align="center")),
        rx.table.cell(rx.text(team["games_played"], color=TEXT_MUTED, text_align="center")),
        background=team["row_bg"],
    )


def tab_elo_and_monte_carlo() -> rx.Component:
    """Contenido de la Pestaña 3: ELO, 5k Monte Carlo y Predictor H2H."""
    return rx.vstack(
        # Encabezado ELO & Monte Carlo
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("zap", size=20, color=ACCENT_GOLD),
                    rx.heading("SUITE ELO & SIMULACIONES MONTE CARLO", size="4", color=TEXT_PRIMARY, font_weight="800"),
                    rx.spacer(),
                    rx.badge("5,000 Iteraciones", style=GOLD_BADGE_STYLE),
                    align="center",
                    width="100%",
                ),
                rx.text(
                    "El motor ELO ajusta la fuerza de cada novena partido a partido con ventaja reglamentaria de localía (+35 pts). "
                    "Mediante 5,000 iteraciones Monte Carlo simulamos la temporada restante, la Serie del Comodín (5° vs 6°), "
                    "el Round Robin de 5 equipos y la Gran Final a 7 juegos para predecir al Campeón LVBP.",
                    size="2",
                    color=TEXT_MUTED,
                    line_height="1.5",
                ),
                spacing="2",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN A: PROYECCIONES MONTE CARLO ─────────────────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("dice-5", size=18, color=ACCENT_GOLD),
                        rx.heading("PROYECCIONES MONTE CARLO DE POSTEMPORADA", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("refresh-cw", size=14),
                        "Re-ejecutar 5,000 Simulaciones",
                        on_click=StandingsState.recalc_simulations,
                        loading=StandingsState.is_simulating,
                        size="1",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),

                # Selector de Modo de Simulación
                rx.hstack(
                    rx.text("Modo de Simulación:", size="2", color=TEXT_MUTED, font_weight="600"),
                    rx.radio(
                        ["actual", "scratch"],
                        value=StandingsState.sim_mode,
                        on_change=StandingsState.set_sim_mode,
                        direction="row",
                        spacing="3",
                    ),
                    rx.spacer(),
                    rx.badge("Estructura LVBP: Top 4 Directo + Wild Card (5° vs 6°)", color_scheme="gray", variant="soft", size="1"),
                    align="center",
                    width="100%",
                    padding_y="0.25rem",
                ),

                # Probabilidades de Leones del Caracas
                rx.grid(
                    rx.vstack(
                        rx.text("TOP 4 DIRECTO (RR)", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_monte_carlo["top4"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text("Clasificación sin Wild Card", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("SERIE COMODÍN (5°-6°)", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_monte_carlo["wc"], size="6", color=TEXT_MUTED, font_weight="800"),
                        rx.text("Puestos 5° o 6°", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("PASE TOTAL A ROUND ROBIN", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_monte_carlo["rr"], size="6", color="var(--green-9)", font_weight="800"),
                        rx.text("Top 4 + Ganador Wild Card", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("GRAN FINALISTA", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_monte_carlo["final"], size="6", color=TEXT_PRIMARY, font_weight="800"),
                        rx.text("Top 2 del Round Robin", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("🏆 CAMPEÓN LVBP", size="1", color=TEXT_MUTED, font_weight="600"),
                        rx.heading(StandingsState.leones_monte_carlo["champ"], size="6", color=ACCENT_GOLD, font_weight="800"),
                        rx.text("Ganador Serie 7 JJ", size="1", color=TEXT_MUTED),
                        align="center",
                        spacing="1",
                    ),
                    columns=rx.breakpoints(initial="2", sm="3", md="5"),
                    spacing="4",
                    width="100%",
                    padding_y="0.5rem",
                ),

                # Tabla de Probabilidades de Postemporada
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("EQUIPO"),
                                rx.table.column_header_cell("RATING ELO"),
                                rx.table.column_header_cell("TOP 4 (RR)"),
                                rx.table.column_header_cell("WILD CARD (5-6)"),
                                rx.table.column_header_cell("PASE TOTAL RR"),
                                rx.table.column_header_cell("GRAN FINAL"),
                                rx.table.column_header_cell("🏆 CAMPEÓN LVBP"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(StandingsState.projections_data, monte_carlo_proj_row)
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN B: MATRIZ DE PROBABILIDAD DE POSICIÓN FINAL (1° AL 8°) ──
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("layout-grid", size=18, color=ACCENT_GOLD),
                        rx.heading("MATRIZ DE PROBABILIDAD DE POSICIÓN FINAL (1° AL 8°)", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.badge("Distribución Estocástica", color_scheme="gray", variant="soft", size="1"),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("EQUIPO"),
                                rx.table.column_header_cell("ELO"),
                                rx.table.column_header_cell("1°"),
                                rx.table.column_header_cell("2°"),
                                rx.table.column_header_cell("3°"),
                                rx.table.column_header_cell("4°"),
                                rx.table.column_header_cell("5°"),
                                rx.table.column_header_cell("6°"),
                                rx.table.column_header_cell("7°"),
                                rx.table.column_header_cell("8°"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(StandingsState.position_matrix_data, position_matrix_row)
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN C: PREDICTOR DE ENFRENTAMIENTOS DIRECTOS H2H ────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("swords", size=18, color=ACCENT_GOLD),
                        rx.heading("PREDICTOR DE ENFRENTAMIENTOS H2H (100% ELO REAL)", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.badge("Ventaja Localía: +35 pts ELO", style=GOLD_BADGE_STYLE),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),

                # Selector de Equipos Local y Visitante
                rx.grid(
                    # Equipo Local
                    rx.vstack(
                        rx.text("🏠 EQUIPO LOCAL (HOME)", size="1", color=TEXT_MUTED, font_weight="700"),
                        rx.select(
                            StandingsState.all_team_options,
                            value=StandingsState.predictor_home_team,
                            on_change=StandingsState.set_predictor_home,
                            size="2",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.image(src=StandingsState.predictor_home_logo, width="48px", height="48px"),
                            rx.vstack(
                                rx.text(StandingsState.predictor_home_team, size="2", font_weight="700", color=TEXT_PRIMARY),
                                rx.text(
                                    f"Rating: {StandingsState.predictor_home_elo:.1f} (+35.0 = {StandingsState.predictor_home_elo + 35.0:.1f})",
                                    size="1",
                                    color=TEXT_MUTED,
                                ),
                                spacing="0",
                                align="start",
                            ),
                            align="center",
                            spacing="3",
                            padding_top="0.5rem",
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),

                    # Marcador Central / Probabilidad
                    rx.vstack(
                        rx.badge("PRONÓSTICO", color_scheme="amber", variant="soft", size="1"),
                        rx.heading(
                            f"{StandingsState.predictor_home_prob_str} vs {StandingsState.predictor_away_prob_str}",
                            size="6",
                            color=ACCENT_GOLD,
                            font_weight="900",
                        ),
                        rx.text(
                            f"Favorito: {StandingsState.predictor_favorite} ({StandingsState.predictor_favorite_prob_str})",
                            size="2",
                            color=TEXT_PRIMARY,
                            font_weight="700",
                        ),
                        rx.text(f"Margen efectivo: {StandingsState.predictor_diff_eff_str}", size="1", color=TEXT_MUTED),
                        spacing="1",
                        align="center",
                        justify="center",
                        width="100%",
                    ),

                    # Equipo Visitante
                    rx.vstack(
                        rx.text("✈️ EQUIPO VISITANTE (AWAY)", size="1", color=TEXT_MUTED, font_weight="700"),
                        rx.select(
                            StandingsState.all_team_options,
                            value=StandingsState.predictor_away_team,
                            on_change=StandingsState.set_predictor_away,
                            size="2",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.image(src=StandingsState.predictor_away_logo, width="48px", height="48px"),
                            rx.vstack(
                                rx.text(StandingsState.predictor_away_team, size="2", font_weight="700", color=TEXT_PRIMARY),
                                rx.text(f"Rating: {StandingsState.predictor_away_elo:.1f} ELO", size="1", color=TEXT_MUTED),
                                spacing="0",
                                align="start",
                            ),
                            align="center",
                            spacing="3",
                            padding_top="0.5rem",
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                    columns=rx.breakpoints(initial="1", md="3"),
                    spacing="4",
                    width="100%",
                    padding_y="0.75rem",
                ),

                # Barra de Probabilidad Visual
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.text(
                                f"{StandingsState.predictor_home_team}: {StandingsState.predictor_home_prob_str}",
                                size="1",
                                color="#070B19",
                                font_weight="800",
                                padding="6px 12px",
                            ),
                            width=f"{StandingsState.predictor_home_prob_pct}%",
                            background=ACCENT_GOLD,
                            border_radius="8px 0 0 8px",
                            transition="width 0.3s ease",
                        ),
                        rx.box(
                            rx.text(
                                f"{StandingsState.predictor_away_team}: {StandingsState.predictor_away_prob_str}",
                                size="1",
                                color="#FFFFFF",
                                font_weight="800",
                                padding="6px 12px",
                                text_align="right",
                            ),
                            width=f"{StandingsState.predictor_away_prob_pct}%",
                            background=NAVY_PRIMARY,
                            border_radius="0 8px 8px 0",
                            transition="width 0.3s ease",
                        ),
                        spacing="0",
                        width="100%",
                        border_radius="8px",
                        overflow="hidden",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    width="100%",
                    padding_top="0.5rem",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN D: RATINGS ELO & POWER RANKINGS POR FASE ────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("list-ordered", size=18, color=ACCENT_GOLD),
                        rx.heading("POWER RANKINGS & RATINGS ELO OFICIALES", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.select(
                        [
                            "regular",
                            "round_robin",
                            "wildcard_playin",
                            "final",
                        ],
                        value=StandingsState.selected_elo_phase,
                        on_change=StandingsState.set_elo_phase,
                        size="2",
                        variant="surface",
                        color_scheme="amber",
                    ),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("RANK"),
                                rx.table.column_header_cell("EQUIPO"),
                                rx.table.column_header_cell("RATING ELO"),
                                rx.table.column_header_cell("DIF BASE (1500)"),
                                rx.table.column_header_cell("JUEGOS"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(StandingsState.elo_ratings_data, elo_ranking_row)
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ═════════════════════════════════════════════════════════════════════════════
# 4. PESTAÑA 4: RÉCORD DÍA / NOCHE & SEMANAS DE CAMPEONATO ISO
# ═════════════════════════════════════════════════════════════════════════════

def iso_weekly_row(week: dict) -> rx.Component:
    """Fila de la tabla de rendimiento por semanas de campeonato ISO."""
    return rx.table.row(
        rx.table.cell(rx.text(week["semana"], font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(week["juegos"], text_align="center")),
        rx.table.cell(rx.text(week["w"], font_weight="700", color="var(--green-9)", text_align="center")),
        rx.table.cell(rx.text(week["l"], font_weight="700", color="var(--red-9)", text_align="center")),
        rx.table.cell(rx.text(week["pct"], font_weight="700", color=ACCENT_GOLD, text_align="center")),
        rx.table.cell(rx.text(week["cf"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(week["cp"], color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(week["dif"], font_weight="700", color=week["dif_color"], text_align="center")),
        rx.table.cell(
            rx.badge(week["record"], color_scheme="amber", variant="soft", size="1")
        ),
    )


def tab_situational_and_iso_weeks() -> rx.Component:
    """Contenido de la Pestaña 4: Desglose Situacional y Semanas ISO."""
    return rx.vstack(
        # Encabezado
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("calendar-range", size=20, color=ACCENT_GOLD),
                    rx.heading("DESGLOSE SITUACIONAL & SEMANAS ISO", size="4", color=TEXT_PRIMARY, font_weight="800"),
                    rx.spacer(),
                    rx.badge("Leones del Caracas 🦁", style=GOLD_BADGE_STYLE),
                    align="center",
                    width="100%",
                ),
                rx.text(
                    "Análisis detallado de rendimiento bajo diferentes condiciones ambientales y de juego "
                    "(horario diurno vs nocturno, localía, márgenes de 1 carrera, capacidad de remontada) "
                    "y desglose estricto semana a semana según el calendario de campeonato ISO (lunes a domingo).",
                    size="2",
                    color=TEXT_MUTED,
                    line_height="1.5",
                ),
                spacing="2",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN A: DESGLOSE SITUACIONAL AVANZADO ────────────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("sun-moon", size=18, color=ACCENT_GOLD),
                        rx.heading("MÉTRICAS SITUACIONALES DE JUEGO", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.badge("Condiciones Ambientales & Presión", color_scheme="gray", variant="soft", size="1"),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),
                rx.grid(
                    rx.box(
                        rx.vstack(
                            rx.text("🏠 HOME CLUB", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["home_record"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                            rx.text("En el estadio sede", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("✈️ VISITANTE", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["away_record"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                            rx.text("En la carretera", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🌙 DE NOCHE", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["night_record"], size="5", color=ACCENT_GOLD, font_weight="800"),
                            rx.text(">= 7:00 PM VET", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("☀️ DE DÍA", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["day_record"], size="5", color=ACCENT_GOLD, font_weight="800"),
                            rx.text("< 7:00 PM VET", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("⚡ 1 CARRERA", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["one_run"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                            rx.text("Márgenes mínimos", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🔄 REMONTADAS", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["remontados"], size="5", color="var(--green-9)", font_weight="800"),
                            rx.text("Abajo tras 6to inning", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🔒 LIDERANDO TRAS 6TO", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["up"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                            rx.text("Cierre de partidos", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🎉 TERRENEADAS", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(StandingsState.leones_advanced["terreneadas"], size="5", color=ACCENT_GOLD, font_weight="800"),
                            rx.text("Walk-off en 9na/Extra", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🧤 DECISIÓN ABRE/RELEVA", size="1", color=TEXT_MUTED, font_weight="600"),
                            rx.heading(f"SP: {StandingsState.leones_advanced['starters']} | RP: {StandingsState.leones_advanced['relievers']}", size="4", color=TEXT_PRIMARY, font_weight="800"),
                            rx.text(f"Salvados: {StandingsState.leones_advanced['saves']}", size="1", color=TEXT_MUTED),
                            spacing="1",
                            align="start",
                        ),
                        padding="1rem",
                        border_radius="12px",
                        background="rgba(255, 255, 255, 0.02)",
                        border=f"1px solid {BORDER_CARD}",
                    ),
                    columns=rx.breakpoints(initial="1", sm="2", md="3"),
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN B: RÉCORD POR MESES ─────────────────────────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("calendar", size=18, color=ACCENT_GOLD),
                    rx.heading("RÉCORD MENSUAL", size="3", color=TEXT_PRIMARY, font_weight="700"),
                    align="center",
                    spacing="2",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("OCTUBRE", size="1", color=TEXT_MUTED, font_weight="700"),
                        rx.heading(StandingsState.leones_advanced["oct"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("NOVIEMBRE", size="1", color=TEXT_MUTED, font_weight="700"),
                        rx.heading(StandingsState.leones_advanced["nov"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                        align="center",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("DICIEMBRE", size="1", color=TEXT_MUTED, font_weight="700"),
                        rx.heading(StandingsState.leones_advanced["dec"], size="5", color=TEXT_PRIMARY, font_weight="800"),
                        align="center",
                        spacing="1",
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                    padding_y="0.5rem",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),

        # ── SECCIÓN C: TABLA DE SEMANAS ISO ─────────────────────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon("calendar-days", size=18, color=ACCENT_GOLD),
                        rx.heading("RÉCORD POR SEMANAS DE CAMPEONATO (LUNES A DOMINGO ISO)", size="3", color=TEXT_PRIMARY, font_weight="700"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.badge("Semanas ISO", color_scheme="amber", variant="soft", size="1"),
                    align="center",
                    width="100%",
                    padding_bottom="0.75rem",
                    border_bottom=f"1px solid {BORDER_CARD}",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("SEMANA"),
                                rx.table.column_header_cell("JJ"),
                                rx.table.column_header_cell("G"),
                                rx.table.column_header_cell("P"),
                                rx.table.column_header_cell("PCT"),
                                rx.table.column_header_cell("CF"),
                                rx.table.column_header_cell("CP"),
                                rx.table.column_header_cell("DIF"),
                                rx.table.column_header_cell("RÉCORD"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(StandingsState.weekly_records_data, iso_weekly_row)
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ═════════════════════════════════════════════════════════════════════════════
# 5. VISTA PRINCIPAL /STANDINGS (ENRUTADOR DE TABS Y LAYOUT)
# ═════════════════════════════════════════════════════════════════════════════

def standings_content() -> rx.Component:
    """Contenedor de pestañas reactivas para la página de Standings."""
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("📊 Tabla Oficial", value="oficial"),
            rx.tabs.trigger("🧮 Sabermetría Pitagórica", value="pitagorica"),
            rx.tabs.trigger("⚡ ELO & Monte Carlo 5k", value="elo"),
            rx.tabs.trigger("📅 Día/Noche & Semanas ISO", value="situacional"),
            size="2",
        ),
        rx.tabs.content(
            tab_official_standings(),
            value="oficial",
            padding_top="1.5rem",
        ),
        rx.tabs.content(
            tab_pythagorean_standings(),
            value="pitagorica",
            padding_top="1.5rem",
        ),
        rx.tabs.content(
            tab_elo_and_monte_carlo(),
            value="elo",
            padding_top="1.5rem",
        ),
        rx.tabs.content(
            tab_situational_and_iso_weeks(),
            value="situacional",
            padding_top="1.5rem",
        ),
        default_value="oficial",
        width="100%",
    )


def standings() -> rx.Component:
    """Página de Posiciones & ELO en Reflex con Layout Frame institucional."""
    return layout(
        content=standings_content(),
        page_title="Posiciones, Sabermetría & Ratings ELO",
        page_description="Clasificación oficial, expectativa pitagórica, 5,000 simulaciones Monte Carlo y analítica situacional de la LVBP.",
        current_route="/standings",
    )
