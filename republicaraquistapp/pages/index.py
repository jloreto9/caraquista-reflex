# republicaraquistapp/pages/index.py
"""
index.py
--------
Dashboard Ejecutivo Sabermétrico de República Caraquista (Ruta /).
Presenta:
1. Rejilla ejecutiva de KPIs (Posición, Récord W-L, Diferencial de Carreras, Racha/L10, Rating ELO).
2. Tarjeta Scoreboard del último compromiso con logos oficiales de MLB y marcador final.
3. Historial de los últimos 5 resultados del Caracas.
4. Desglose situacional avanzado (Día vs Noche, Home Club vs Visitante, 1 Carrera, Remontadas).
5. Desempeño de la última semana de campeonato ISO disputada.
6. Vista previa de la tabla de posiciones con enlace a /standings.
Todo encapsulado en el marco layout() con tema Dark Navy y Glassmorphism.
"""

from typing import Any, Optional
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
)
from republicaraquistapp.state.standings_state import StandingsState
from republicaraquistapp.components.layout import layout
from republicaraquistapp.components.scoreboard import scoreboard_card


def executive_kpi_card(
    title: str,
    value: Any,
    subtitle: str,
    icon_name: str,
    badge_text: Optional[str] = None,
) -> rx.Component:
    """Tarjeta individual para la cuadrícula ejecutiva de KPIs."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(title, size="2", color=TEXT_MUTED, font_weight="600"),
                    rx.cond(
                        badge_text is not None,
                        rx.badge(badge_text, color_scheme="amber", variant="soft", size="1"),
                        rx.fragment(),
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.heading(value, size="7", color=TEXT_PRIMARY, font_weight="800"),
                rx.text(subtitle, size="1", color=TEXT_MUTED),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.box(
                rx.icon(icon_name, size=24, color=ACCENT_GOLD),
                padding="10px",
                border_radius="10px",
                background="rgba(253, 184, 39, 0.1)",
                border=f"1px solid {BORDER_SUBTLE}",
            ),
            align="center",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def executive_kpi_grid() -> rx.Component:
    """Rejilla con los 5 KPIs primarios del conjunto caraquista."""
    return rx.grid(
        executive_kpi_card(
            title="POSICIÓN TABLA",
            value=StandingsState.leones_kpis["posicion"],
            subtitle="Ronda Regular LVBP",
            icon_name="trophy",
        ),
        executive_kpi_card(
            title="RÉCORD W - L",
            value=StandingsState.leones_kpis["record"],
            subtitle=f"PCT: {StandingsState.leones_kpis['pct']}",
            icon_name="chart-bar",
        ),
        executive_kpi_card(
            title="DIF. CARRERAS",
            value=StandingsState.leones_kpis["run_diff"],
            subtitle=f"CF: {StandingsState.leones_kpis['rf']} | CP: {StandingsState.leones_kpis['ra']}",
            icon_name="scale",
        ),
        executive_kpi_card(
            title="RACHA & L10",
            value=StandingsState.leones_kpis["streak"],
            subtitle=f"Últimos 10: {StandingsState.leones_kpis['l10']}",
            icon_name="flame",
        ),
        executive_kpi_card(
            title="RATING ELO",
            value=StandingsState.leones_elo_stats["elo"],
            subtitle=f"Puesto {StandingsState.leones_elo_stats['rank']} • Base 1500",
            icon_name="zap",
        ),
        columns=rx.breakpoints(initial="1", sm="2", md="3", lg="5"),
        spacing="4",
        width="100%",
    )


def recent_game_item(game: dict) -> rx.Component:
    """Fila visual representativa de un juego previo de los Leones."""
    return rx.hstack(
        rx.text(game["date"], size="1", color=TEXT_MUTED, width="75px"),
        rx.hstack(
            rx.image(src=game["away_logo"], width="20px", height="20px"),
            rx.text(game["away_name"], size="2", color=TEXT_PRIMARY, font_weight="500"),
            align="center",
            spacing="2",
            flex="1",
        ),
        rx.text(
            game["score_str"],
            size="2",
            font_weight="800",
            color=ACCENT_GOLD,
            width="60px",
            text_align="center",
        ),
        rx.hstack(
            rx.image(src=game["home_logo"], width="20px", height="20px"),
            rx.text(game["home_name"], size="2", color=TEXT_PRIMARY, font_weight="500"),
            align="center",
            spacing="2",
            flex="1",
        ),
        rx.badge(
            game["result_badge"],
            color_scheme=game["result_color"],
            variant="soft",
            size="1",
        ),
        align="center",
        width="100%",
        padding_y="0.45rem",
        border_bottom=f"1px solid {BORDER_CARD}",
    )


def situational_mini_card(label: str, value: str, icon_name: str) -> rx.Component:
    """Tarjeta compacta de métrica situacional (ej. Día vs Noche)."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon_name, size=18, color=ACCENT_GOLD),
                padding="8px",
                border_radius="8px",
                background="rgba(253, 184, 39, 0.08)",
            ),
            rx.vstack(
                rx.text(label, size="1", color=TEXT_MUTED, font_weight="600"),
                rx.heading(value, size="3", color=TEXT_PRIMARY, font_weight="800"),
                spacing="0",
                align="start",
            ),
            align="center",
            spacing="3",
            width="100%",
        ),
        padding="0.75rem",
        border_radius="10px",
        background="rgba(255, 255, 255, 0.02)",
        border=f"1px solid {BORDER_CARD}",
        width="100%",
    )


def situational_breakdown_section() -> rx.Component:
    """Sección de desglose situacional (Día/Noche, Local/Visitante, 1 Carrera, Remontadas)."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("sun-moon", size=18, color=ACCENT_GOLD),
                    rx.heading("DESGLOSE SITUACIONAL", size="3", color=TEXT_PRIMARY, font_weight="700"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.badge("Condiciones", color_scheme="gray", variant="soft", size="1"),
                align="center",
                width="100%",
                padding_bottom="0.75rem",
                border_bottom=f"1px solid {BORDER_CARD}",
            ),
            rx.grid(
                situational_mini_card("🏠 HOME CLUB", StandingsState.leones_advanced["home_record"], "home"),
                situational_mini_card("✈️ VISITANTE", StandingsState.leones_advanced["away_record"], "plane"),
                situational_mini_card("🌙 DE NOCHE", StandingsState.leones_advanced["night_record"], "moon"),
                situational_mini_card("☀️ DE DÍA", StandingsState.leones_advanced["day_record"], "sun"),
                situational_mini_card("⚡ 1 CARRERA", StandingsState.leones_advanced["one_run"], "target"),
                situational_mini_card("🔄 REMONTADAS", StandingsState.leones_advanced["remontados"], "refresh-cw"),
                columns=rx.breakpoints(initial="2", sm="3"),
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def iso_week_summary_card() -> rx.Component:
    """Tarjeta ejecutiva que reporta el rendimiento en la semana ISO más reciente."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("calendar", size=18, color=ACCENT_GOLD),
                    rx.heading("ÚLTIMA SEMANA ISO", size="3", color=TEXT_PRIMARY, font_weight="700"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.badge(
                    StandingsState.latest_weekly_record["semana"],
                    color_scheme="amber",
                    variant="soft",
                    size="1",
                ),
                align="center",
                width="100%",
                padding_bottom="0.75rem",
                border_bottom=f"1px solid {BORDER_CARD}",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("RÉCORD SEMANAL", size="1", color=TEXT_MUTED, font_weight="600"),
                    rx.heading(
                        StandingsState.latest_weekly_record["record"],
                        size="6",
                        color=ACCENT_GOLD,
                        font_weight="800",
                    ),
                    rx.text(f"PCT: {StandingsState.latest_weekly_record['pct']}", size="1", color=TEXT_MUTED),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                rx.divider(orientation="vertical", size="4"),
                rx.vstack(
                    rx.text("CARRERAS A FAVOR", size="1", color=TEXT_MUTED, font_weight="600"),
                    rx.heading(
                        StandingsState.latest_weekly_record["cf"].to_string(),
                        size="5",
                        color=TEXT_PRIMARY,
                        font_weight="800",
                    ),
                    rx.text("Ofensiva colectiva", size="1", color=TEXT_MUTED),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                rx.divider(orientation="vertical", size="4"),
                rx.vstack(
                    rx.text("CARRERAS PERMITIDAS", size="1", color=TEXT_MUTED, font_weight="600"),
                    rx.heading(
                        StandingsState.latest_weekly_record["cp"].to_string(),
                        size="5",
                        color=TEXT_PRIMARY,
                        font_weight="800",
                    ),
                    rx.text("Pitcheo y defensa", size="1", color=TEXT_MUTED),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                rx.divider(orientation="vertical", size="4"),
                rx.vstack(
                    rx.text("DIFERENCIAL", size="1", color=TEXT_MUTED, font_weight="600"),
                    rx.heading(
                        StandingsState.latest_weekly_record["dif"],
                        size="5",
                        color=StandingsState.latest_weekly_record["dif_color"],
                        font_weight="800",
                    ),
                    rx.text("Margen neto", size="1", color=TEXT_MUTED),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                align="center",
                justify="center",
                width="100%",
                padding_y="0.75rem",
            ),
            rx.hstack(
                rx.spacer(),
                rx.link(
                    rx.button(
                        rx.icon("arrow-right", size=14),
                        "Ver histórico de semanas completo",
                        size="1",
                        variant="ghost",
                        color=ACCENT_GOLD,
                    ),
                    href="/standings",
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def standings_preview_row(team: dict) -> rx.Component:
    """Fila para la tabla de posiciones condensada del Dashboard."""
    return rx.table.row(
        rx.table.cell(rx.text(team["pos"].to_string() + "°", font_weight="700", color=team["text_color"])),
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="24px", height="24px"),
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
        rx.table.cell(rx.text(team["diff"], font_weight="700", color=team["diff_color"], text_align="center")),
        rx.table.cell(
            rx.badge(team["streak"], color_scheme=team["streak_color"], variant="soft", size="1")
        ),
        background=team["row_bg"],
        border_left=team["row_border"],
    )


def standings_preview_card() -> rx.Component:
    """Tabla condensada de la clasificación de la LVBP."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("table", size=18, color=ACCENT_GOLD),
                    rx.heading("TABLA DE POSICIONES", size="3", color=TEXT_PRIMARY, font_weight="700"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=13),
                        "Ver Vista Completa (/standings)",
                        size="1",
                        variant="outline",
                        color_scheme="amber",
                    ),
                    href="/standings",
                ),
                align="center",
                width="100%",
                padding_bottom="0.75rem",
                border_bottom=f"1px solid {BORDER_CARD}",
            ),
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
                        rx.table.column_header_cell("DIF"),
                        rx.table.column_header_cell("RACHA"),
                    )
                ),
                rx.table.body(
                    rx.foreach(StandingsState.standings_data, standings_preview_row)
                ),
                variant="surface",
                size="2",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def index_content() -> rx.Component:
    """Cuerpo principal del Dashboard Ejecutivo (/)."""
    return rx.vstack(
        # 1. Banner de Bienvenida y Propósito
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            width="4px",
                            height="32px",
                            background=ACCENT_GOLD,
                            border_radius="2px",
                        ),
                        rx.heading(
                            "DASHBOARD EJECUTIVO SABERMÉTRICO",
                            size="6",
                            color=TEXT_PRIMARY,
                            font_weight="800",
                            letter_spacing="0.02em",
                        ),
                        align="center",
                        spacing="3",
                    ),
                    rx.text(
                        "Seguimiento analítico en tiempo real, probabilidades y modelos de última "
                        "generación para los Leones del Caracas en la LVBP.",
                        size="2",
                        color=TEXT_MUTED,
                        padding_left="1rem",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.badge("Ronda Regular", style=GOLD_BADGE_STYLE),
                align="center",
                width="100%",
            ),
            padding_bottom="0.5rem",
            width="100%",
        ),

        # 2. Rejilla Ejecutiva de KPIs Principales
        executive_kpi_grid(),

        # 3. Grilla Principal de 2 Columnas
        rx.grid(
            # Columna Izquierda: Scoreboard y Juegos Recientes
            rx.vstack(
                scoreboard_card(),
                # Tarjeta de Historial Reciente (Últimos 5 partidos)
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon("calendar-days", size=18, color=ACCENT_GOLD),
                                rx.heading(
                                    "ÚLTIMOS RESULTADOS",
                                    size="3",
                                    color=TEXT_PRIMARY,
                                    font_weight="700",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            rx.spacer(),
                            rx.badge("Últimos 5", color_scheme="gray", variant="soft", size="1"),
                            align="center",
                            width="100%",
                            padding_bottom="0.75rem",
                            border_bottom=f"1px solid {BORDER_CARD}",
                        ),
                        rx.foreach(StandingsState.recent_games_data, recent_game_item),
                        spacing="2",
                        width="100%",
                    ),
                    style=CARD_STYLE,
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),

            # Columna Derecha: Desglose Situacional y Desempeño Semanal ISO
            rx.vstack(
                situational_breakdown_section(),
                iso_week_summary_card(),
                spacing="4",
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", lg="2"),
            spacing="5",
            width="100%",
        ),

        # 4. Tabla de Posiciones Oficial Completa / Previa
        standings_preview_card(),

        spacing="5",
        width="100%",
    )


def index() -> rx.Component:
    """Página principal de República Caraquista en Reflex con Layout Global."""
    return layout(
        content=index_content(),
        page_title="Dashboard Ejecutivo Sabermétrico",
        page_description="Panel de control analítico, métricas de rendimiento y seguimiento de los Leones del Caracas.",
        current_route="/",
    )
