# republicaraquistapp/pages/wpa.py
"""
wpa.py
------
Vista completa para el Módulo Sabermétrico de Win Expectancy (WE),
Win Probability Added (WPA), Leverage Index (LI) y Clutch.
Ruta: /wpa
"""

import reflex as rx
import plotly.graph_objects as go
from typing import Dict, Any

from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    ACCENT_GOLD,
    LEONES_RED,
    TEXT_PRIMARY,
    TEXT_MUTED,
    BORDER_CARD,
    BORDER_SUBTLE,
    BORDER_GOLD,
    CARD_STYLE,
    GOLD_BADGE_STYLE,
)
from republicaraquistapp.state.wpa_state import WpaState
from republicaraquistapp.components.layout import layout


def pivotal_play_row(play: Dict[str, Any]) -> rx.Component:
    """Fila para la tabla de jugadas clave (Pivotal Plays)."""
    return rx.table.row(
        rx.table.cell(
            rx.badge(play["inning_str"], color_scheme="amber", variant="soft", size="1"),
        ),
        rx.table.cell(rx.text(play["outs_str"], size="2", color=TEXT_MUTED)),
        rx.table.cell(
            rx.text(play["bases"], size="2", font_family="monospace", color=ACCENT_GOLD, font_weight="700")
        ),
        rx.table.cell(rx.text(play["batter"], size="2", font_weight="600", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(play["pitcher"], size="2", color=TEXT_MUTED)),
        rx.table.cell(
            rx.badge(play["event"], color_scheme="blue", variant="surface", size="1")
        ),
        rx.table.cell(
            rx.text(play["desc"], size="1", color=TEXT_MUTED, max_width="260px", is_truncated=True)
        ),
        rx.table.cell(
            rx.badge(
                play["wpa_str"],
                color_scheme=play["wpa_color"],
                variant="solid",
                size="1",
                font_weight="800"
            )
        ),
        rx.table.cell(rx.text(play["li_str"], size="2", color=TEXT_PRIMARY, font_weight="600")),
        rx.table.cell(rx.text(play["score"], size="2", color=TEXT_PRIMARY, font_weight="700")),
    )


def player_wpa_row(p: Dict[str, Any]) -> rx.Component:
    """Fila para la tabla de WPA por jugador en el partido."""
    return rx.table.row(
        rx.table.cell(rx.text(p["player"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(
            rx.badge(p["wpa"], color_scheme=p["wpa_color"], variant="soft", size="1", font_weight="700")
        ),
        rx.table.cell(rx.text(p["wpa_li"], size="2", color=TEXT_MUTED)),
        rx.table.cell(
            rx.badge(p["clutch"], color_scheme=p["clutch_color"], variant="solid", size="1", font_weight="700")
        ),
    )


def season_batter_row(b: Dict[str, Any]) -> rx.Component:
    """Fila para el ranking de bateadores de la temporada."""
    return rx.table.row(
        rx.table.cell(rx.text(b["player"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(b["jj"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(b["pa"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(
            rx.badge(b["wpa"], color_scheme=b["wpa_color"], variant="solid", size="1", font_weight="700")
        ),
        rx.table.cell(rx.text(b["wpa_li"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(b["li_avg"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(b["high_li_pa"], size="2", color=ACCENT_GOLD, font_weight="600")),
        rx.table.cell(
            rx.badge(b["clutch"], color_scheme=b["clutch_color"], variant="soft", size="1", font_weight="700")
        ),
    )


def season_pitcher_row(p: Dict[str, Any]) -> rx.Component:
    """Fila para el ranking de lanzadores de la temporada."""
    return rx.table.row(
        rx.table.cell(rx.text(p["player"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(p["jj"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(p["bf"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(
            rx.badge(p["wpa"], color_scheme=p["wpa_color"], variant="solid", size="1", font_weight="700")
        ),
        rx.table.cell(rx.text(p["wpa_li"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(p["li_avg"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(p["high_li_bf"], size="2", color=ACCENT_GOLD, font_weight="600")),
        rx.table.cell(
            rx.badge(p["clutch"], color_scheme=p["clutch_color"], variant="soft", size="1", font_weight="700")
        ),
    )


def top_play_row(play: Dict[str, Any], is_pos: bool = True) -> rx.Component:
    """Fila para las mejores o peores jugadas de toda la temporada."""
    return rx.table.row(
        rx.table.cell(rx.text(play["date"], size="1", color=TEXT_MUTED)),
        rx.table.cell(rx.badge(play["inn"], color_scheme="amber", variant="soft", size="1")),
        rx.table.cell(rx.text(play["batter"], size="2", font_weight="600", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(play["pitcher"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.badge(play["event"], color_scheme="blue", variant="surface", size="1")),
        rx.table.cell(rx.text(play["desc"], size="1", color=TEXT_MUTED, max_width="280px", is_truncated=True)),
        rx.table.cell(
            rx.badge(
                play["wpa"],
                color_scheme="green" if is_pos else "red",
                variant="solid",
                size="1",
                font_weight="800"
            )
        ),
        rx.table.cell(rx.text(play["li"], size="2", color=TEXT_PRIMARY, font_weight="600")),
    )


def single_game_view() -> rx.Component:
    """Vista de WPA y Win Expectancy para un partido individual."""
    return rx.vstack(
        # 1. Selector de Partido y Badges de Marcador
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("SELECCIONAR JUEGO FINALIZADO", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.select(
                            WpaState.game_labels,
                            value=WpaState.selected_game_label,
                            on_change=WpaState.set_selected_game,
                            size="3",
                            variant="soft",
                            color_scheme="amber",
                            width="100%",
                        ),
                        spacing="1",
                        align="start",
                        flex="1",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.vstack(
                            rx.text("RESULTADO", size="1", font_weight="700", color=TEXT_MUTED),
                            rx.badge(
                                WpaState.game_result_badge,
                                color_scheme=WpaState.game_result_color,
                                variant="solid",
                                size="2",
                            ),
                            align="center",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("MARCADOR", size="1", font_weight="700", color=TEXT_MUTED),
                            rx.heading(WpaState.game_score_str, size="5", color=ACCENT_GOLD, font_weight="800"),
                            align="center",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("PICO LI", size="1", font_weight="700", color=TEXT_MUTED),
                            rx.heading(WpaState.game_max_li, size="5", color=TEXT_PRIMARY, font_weight="800"),
                            align="center",
                            spacing="1",
                        ),
                        spacing="5",
                        align="center",
                    ),
                    align="center",
                    width="100%",
                ),
                # KPIs de Héroe y Villano del Juego
                rx.grid(
                    rx.box(
                        rx.hstack(
                            rx.icon("award", size=22, color="#10b981"),
                            rx.vstack(
                                rx.text("JUGADA CLAVE HEROICA (+WPA)", size="1", font_weight="700", color=TEXT_MUTED),
                                rx.text(WpaState.game_top_hero, size="2", font_weight="700", color=TEXT_PRIMARY),
                                spacing="0",
                            ),
                            rx.spacer(),
                            rx.badge(WpaState.game_top_hero_wpa, color_scheme="green", variant="solid", size="2"),
                            align="center",
                            spacing="3",
                            width="100%",
                        ),
                        padding="0.75rem 1rem",
                        background="rgba(16, 185, 129, 0.1)",
                        border="1px solid rgba(16, 185, 129, 0.25)",
                        border_radius="10px",
                        width="100%",
                    ),
                    rx.box(
                        rx.hstack(
                            rx.icon("triangle-alert", size=22, color="#ef4444"),
                            rx.vstack(
                                rx.text("JUGADA DE MAYOR IMPACTO ADVERSO (-WPA)", size="1", font_weight="700", color=TEXT_MUTED),
                                rx.text(WpaState.game_top_villain, size="2", font_weight="700", color=TEXT_PRIMARY),
                                spacing="0",
                            ),
                            rx.spacer(),
                            rx.badge(WpaState.game_top_villain_wpa, color_scheme="red", variant="solid", size="2"),
                            align="center",
                            spacing="3",
                            width="100%",
                        ),
                        padding="0.75rem 1rem",
                        background="rgba(239, 68, 68, 0.1)",
                        border="1px solid rgba(239, 68, 68, 0.25)",
                        border_radius="10px",
                        width="100%",
                    ),
                    columns=rx.breakpoints(initial="1", md="2"),
                    spacing="3",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # 2. Gráfico Interactivo de Win Expectancy
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("trending-up", size=18, color=ACCENT_GOLD),
                    rx.heading("EVOLUCIÓN DE PROBABILIDAD DE VICTORIA (WIN EXPECTANCY)", size="3", color=TEXT_PRIMARY),
                    rx.spacer(),
                    align="center",
                    width="100%",
                ),
                rx.plotly(data=WpaState.we_chart_figure, height="460px", width="100%"),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # 3. Grilla de 2 Columnas: WPA por Inning y Rendimiento por Jugador
        rx.grid(
            # Columna Izquierda: WPA por Inning
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("bar-chart-2", size=18, color=ACCENT_GOLD),
                        rx.heading("WPA NETO POR ENTRADA", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.plotly(data=WpaState.inning_wpa_figure, height="320px", width="100%"),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            # Columna Derecha: Tabla de Jugadores
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("users", size=18, color=ACCENT_GOLD),
                        rx.heading("WPA & CLUTCH POR JUGADOR", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Jugador"),
                                rx.table.column_header_cell("WPA Total"),
                                rx.table.column_header_cell("WPA / LI"),
                                rx.table.column_header_cell("Clutch"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(WpaState.player_game_wpa, player_wpa_row)
                        ),
                        variant="surface",
                        size="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", lg="2"),
            spacing="5",
            width="100%",
        ),
        # 4. Tabla de Jugadas Decisivas (Pivotal Plays)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("zap", size=18, color=ACCENT_GOLD),
                    rx.heading("JUGADAS DECISIVAS DEL PARTIDO (MÁXIMO IMPACTO WPA)", size="3", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.badge("Top Swings", color_scheme="amber", variant="soft", size="1"),
                    align="center",
                    width="100%",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Inning"),
                            rx.table.column_header_cell("Outs"),
                            rx.table.column_header_cell("Bases"),
                            rx.table.column_header_cell("Bateador"),
                            rx.table.column_header_cell("Lanzador"),
                            rx.table.column_header_cell("Evento"),
                            rx.table.column_header_cell("Descripción"),
                            rx.table.column_header_cell("WPA"),
                            rx.table.column_header_cell("LI"),
                            rx.table.column_header_cell("Score"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(WpaState.pivotal_plays, pivotal_play_row)
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def season_leaderboard_view() -> rx.Component:
    """Vista de rankings acumulados de WPA y jugadas históricas de la temporada."""
    return rx.vstack(
        # Resumen de Cobertura
        rx.hstack(
            rx.box(
                rx.hstack(
                    rx.icon("calendar", size=20, color=ACCENT_GOLD),
                    rx.vstack(
                        rx.text("JUEGOS PROCESADOS", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.heading(f"{WpaState.season_total_games} JJ", size="5", color=TEXT_PRIMARY),
                        spacing="0",
                    ),
                    spacing="3",
                    align="center",
                ),
                style=CARD_STYLE,
                flex="1",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("activity", size=20, color=ACCENT_GOLD),
                    rx.vstack(
                        rx.text("JUGADAS EVALUADAS", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.heading(f"{WpaState.season_total_plays} Plays", size="5", color=TEXT_PRIMARY),
                        spacing="0",
                    ),
                    spacing="3",
                    align="center",
                ),
                style=CARD_STYLE,
                flex="1",
            ),
            spacing="4",
            width="100%",
        ),
        # Grilla de Líderes Bateadores y Lanzadores
        rx.grid(
            # Tabla de Bateadores
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("target", size=18, color=ACCENT_GOLD),
                        rx.heading("TOP BATEADORES EN WPA & CLUTCH", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Bateador"),
                                rx.table.column_header_cell("JJ"),
                                rx.table.column_header_cell("PA"),
                                rx.table.column_header_cell("WPA"),
                                rx.table.column_header_cell("WPA/LI"),
                                rx.table.column_header_cell("LI Prom"),
                                rx.table.column_header_cell("High LI"),
                                rx.table.column_header_cell("Clutch"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(WpaState.season_batters, season_batter_row)
                        ),
                        variant="surface",
                        size="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            # Tabla de Lanzadores
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("shield", size=18, color=ACCENT_GOLD),
                        rx.heading("TOP LANZADORES EN WPA & CLUTCH", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Lanzador"),
                                rx.table.column_header_cell("JJ"),
                                rx.table.column_header_cell("BF"),
                                rx.table.column_header_cell("WPA"),
                                rx.table.column_header_cell("WPA/LI"),
                                rx.table.column_header_cell("LI Prom"),
                                rx.table.column_header_cell("High LI"),
                                rx.table.column_header_cell("Clutch"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(WpaState.season_pitchers, season_pitcher_row)
                        ),
                        variant="surface",
                        size="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", xl="2"),
            spacing="5",
            width="100%",
        ),
        # Top 10 Jugadas Positivas de la Temporada
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("award", size=18, color="#10b981"),
                    rx.heading("TOP 10 JUGADAS MÁS DECISIVAS (+WPA DE LA TEMPORADA)", size="3", color=TEXT_PRIMARY),
                    align="center",
                    spacing="2",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Fecha"),
                            rx.table.column_header_cell("Inn"),
                            rx.table.column_header_cell("Bateador"),
                            rx.table.column_header_cell("Lanzador"),
                            rx.table.column_header_cell("Evento"),
                            rx.table.column_header_cell("Descripción"),
                            rx.table.column_header_cell("WPA"),
                            rx.table.column_header_cell("LI"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            WpaState.season_top_positive_plays,
                            lambda p: top_play_row(p, is_pos=True)
                        )
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Top 10 Jugadas Negativas de la Temporada
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("circle-alert", size=18, color="#ef4444"),
                    rx.heading("TOP 10 JUGADAS MÁS ADVERSAS (-WPA DE LA TEMPORADA)", size="3", color=TEXT_PRIMARY),
                    align="center",
                    spacing="2",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Fecha"),
                            rx.table.column_header_cell("Inn"),
                            rx.table.column_header_cell("Bateador"),
                            rx.table.column_header_cell("Lanzador"),
                            rx.table.column_header_cell("Evento"),
                            rx.table.column_header_cell("Descripción"),
                            rx.table.column_header_cell("WPA"),
                            rx.table.column_header_cell("LI"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            WpaState.season_top_negative_plays,
                            lambda p: top_play_row(p, is_pos=False)
                        )
                    ),
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def wpa_content() -> rx.Component:
    """Contenido principal de la página WPA."""
    return rx.vstack(
        # Tabs de Navegación del Módulo
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon("trending-up", size=16),
                    rx.text("Análisis por Partido", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(WpaState.active_tab == "juego", "solid", "outline"),
                color_scheme="amber",
                on_click=WpaState.set_active_tab("juego"),
                size="2",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("award", size=16),
                    rx.text("Líderes de Temporada", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(WpaState.active_tab == "temporada", "solid", "outline"),
                color_scheme="amber",
                on_click=WpaState.set_active_tab("temporada"),
                size="2",
            ),
            spacing="3",
            padding_bottom="0.5rem",
        ),
        # Renderizado Condicional de la Vista
        rx.cond(
            WpaState.active_tab == "juego",
            single_game_view(),
            season_leaderboard_view(),
        ),
        # Guía Metodológica Tango RE24 & WPA
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon("book-open", size=16, color=ACCENT_GOLD),
                    rx.text("Guía y Metodología Sabermétrica: Tango RE24, Win Expectancy y Leverage Index", size="2", font_weight="700", color=TEXT_PRIMARY),
                    spacing="2",
                    align="center",
                ),
                content=rx.vstack(
                    rx.text(
                        "El modelo WPA (Win Probability Added) mide cuánto varió la probabilidad de que los Leones del Caracas "
                        "ganaran el partido a partir de una jugada específica, considerando la entrada, el marcador, los outs y "
                        "los corredores en circulación mediante la matriz Tango RE24 de 24 estados.",
                        size="2",
                        color=TEXT_MUTED,
                    ),
                    rx.grid(
                        rx.box(
                            rx.text("📈 WPA (Win Probability Added)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Mide el impacto directo en la victoria. Un hit de oro en la 9na entrada puede valer +0.450 WPA, mientras que un jonrón en un juego 10-0 aporta menos de +0.010 WPA.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("⚡ LI (Leverage Index)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Apalancamiento de la situación. LI = 1.0 es el promedio de la liga. LI > 1.5 es alta presión (High Leverage); LI < 0.7 es baja presión.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("🔥 Clutch (Oportunismo)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Clutch = WPA - (WPA / LI). Mide si el jugador rinde por encima de su nivel habitual en los momentos de mayor tensión competitiva.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        columns=rx.breakpoints(initial="1", md="3"),
                        spacing="3",
                        width="100%",
                    ),
                    spacing="3",
                    padding_y="1rem",
                ),
                value="methodology",
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def wpa() -> rx.Component:
    """Vista principal de WPA y Win Expectancy en Reflex."""
    return layout(
        content=wpa_content(),
        page_title="Win Expectancy & Probabilidad de Victoria (WPA)",
        page_description="Modelos estocásticos de 24 estados Tango RE24, apalancamiento situacional (LI) y héroes del partido.",
        current_route="/wpa",
    )
