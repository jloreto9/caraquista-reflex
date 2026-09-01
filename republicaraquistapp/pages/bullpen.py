# republicaraquistapp/pages/bullpen.py
"""
bullpen.py
----------
Vista para el análisis de Relevistas con Corredores Heredados (IR / IRS),
Tracker de Alineaciones Titulares y Rendimiento por Orden al Bate (1-9).
Ruta: /bullpen
"""

from typing import Dict, Any
import reflex as rx

from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    ACCENT_GOLD,
    LEONES_RED,
    TEXT_PRIMARY,
    TEXT_MUTED,
    BORDER_CARD,
    BORDER_SUBTLE,
    CARD_STYLE,
    GOLD_BADGE_STYLE,
)
from republicaraquistapp.state.bullpen_state import BullpenState
from republicaraquistapp.components.layout import layout


def reliever_table_row(r: Dict[str, Any]) -> rx.Component:
    """Fila para la tabla de efectividad de relevistas."""
    return rx.table.row(
        rx.table.cell(rx.text(r["pitcher"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(r["appearances"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["ir"], size="2", color="#3b82f6", font_weight="600")),
        rx.table.cell(rx.text(r["irs"], size="2", color="#ef4444", font_weight="600")),
        rx.table.cell(
            rx.badge(r["irs_pct"], color_scheme="amber", variant="solid", size="1", font_weight="700")
        ),
    )


def inherited_log_row(log: Dict[str, Any]) -> rx.Component:
    """Fila para el registro detallado de entradas con herencia."""
    return rx.table.row(
        rx.table.cell(rx.text(log["date"], size="1", color=TEXT_MUTED)),
        rx.table.cell(rx.text(log["opp"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(rx.badge(log["inning"], color_scheme="amber", variant="soft", size="1")),
        rx.table.cell(rx.text(log["pitcher"], size="2", font_weight="600", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(log["ir"], size="2", color="#3b82f6", font_weight="700")),
        rx.table.cell(rx.text(log["irs"], size="2", color="#ef4444", font_weight="700")),
    )


def starter_item_card(s: Dict[str, Any]) -> rx.Component:
    """Tarjeta individual para un jugador en el orden al bate 1-9."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(s["order_str"], size="2", font_weight="800", color="#FFFFFF"),
                padding="4px 10px",
                border_radius="6px",
                background=s["badge_color"],
            ),
            rx.text(s["player_name"], size="2", font_weight="700", color=TEXT_PRIMARY),
            rx.spacer(),
            rx.badge(s["position_full"], color_scheme="gray", variant="surface", size="1"),
            align="center",
            width="100%",
            spacing="3",
        ),
        padding="10px 14px",
        background="rgba(15, 23, 42, 0.85)",
        border="1px solid rgba(255, 255, 255, 0.08)",
        border_radius="8px",
        width="100%",
    )


def top_lineup_item(lu: Dict[str, Any]) -> rx.Component:
    """Elemento para la lista de alineaciones más frecuentes."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(lu["rank_str"], color_scheme="amber", variant="solid", size="1"),
                rx.text(lu["summary"], size="2", font_weight="700", color=TEXT_PRIMARY),
                rx.spacer(),
                align="center",
                width="100%",
            ),
            rx.text(lu["preview"], size="1", color=TEXT_MUTED),
            spacing="2",
            width="100%",
        ),
        padding="12px 16px",
        background="rgba(255, 255, 255, 0.03)",
        border="1px solid rgba(255, 255, 255, 0.08)",
        border_radius="8px",
        width="100%",
    )


def player_slot_row(b: Dict[str, Any]) -> rx.Component:
    """Fila para el desglose por turno de un jugador."""
    return rx.table.row(
        rx.table.cell(rx.text(b["slot"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(b["starts"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(b["wins"], size="2", color="#10b981", font_weight="600")),
        rx.table.cell(rx.text(b["losses"], size="2", color="#ef4444", font_weight="600")),
        rx.table.cell(
            rx.badge(b["pct"], color_scheme="amber", variant="soft", size="1", font_weight="700")
        ),
    )


def bullpen_tab_view() -> rx.Component:
    """Vista de Corredores Heredados del Bullpen."""
    return rx.vstack(
        # 1. Rejilla de 4 KPIs de Bullpen
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("CORREDORES HEREDADOS (IR)", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{BullpenState.kpi_tot_ir}", size="6", color="#3b82f6", font_weight="800"),
                    rx.text("Encontrados en base al relevar", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("HEREDADOS QUE ANOTARON (IRS)", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{BullpenState.kpi_tot_irs}", size="6", color="#ef4444", font_weight="800"),
                    rx.text("Carreras ajenas permitidas", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("TASA IRS% COLECTIVA", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(BullpenState.kpi_irs_pct, size="6", color=ACCENT_GOLD, font_weight="800"),
                    rx.text("Porcentaje de contención", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("LÍDER 'APAGAFUEGOS' (MÍN. 5 IR)", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(BullpenState.kpi_best_reliever, size="5", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text(BullpenState.kpi_best_reliever_sub, size="1", color="#10b981"),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
            width="100%",
        ),
        # 2. Grilla de Gráfico y Tabla
        rx.grid(
            # Gráfico IR vs IRS
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("bar-chart-2", size=18, color=ACCENT_GOLD),
                        rx.heading("HEREDADOS (IR) VS. ANOTARON (IRS)", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.plotly(data=BullpenState.bullpen_chart_figure, height="380px", width="100%"),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            # Tabla por Relevista
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("shield", size=18, color=ACCENT_GOLD),
                        rx.heading("EFECTIVIDAD POR RELEVISTA", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Lanzador Relevista"),
                                    rx.table.column_header_cell("Juegos"),
                                    rx.table.column_header_cell("Total IR"),
                                    rx.table.column_header_cell("Total IRS"),
                                    rx.table.column_header_cell("% IRS"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(BullpenState.relievers_table_data, reliever_table_row)
                            ),
                            variant="surface",
                            size="1",
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
            columns=rx.breakpoints(initial="1", xl="2"),
            spacing="5",
            width="100%",
        ),
        # 3. Log Detallado de Relevos con Corredores en Base
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("list-ordered", size=18, color=ACCENT_GOLD),
                    rx.heading("REGISTRO DE ENTRADAS CON CORREDORES EN BASE", size="3", color=TEXT_PRIMARY),
                    rx.spacer(),
                    align="center",
                    width="100%",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Fecha"),
                                rx.table.column_header_cell("Rival"),
                                rx.table.column_header_cell("Inning"),
                                rx.table.column_header_cell("Lanzador"),
                                rx.table.column_header_cell("Heredados (IR)"),
                                rx.table.column_header_cell("Anotaron (IRS)"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(BullpenState.detailed_inherited_logs, inherited_log_row)
                        ),
                        variant="surface",
                        size="1",
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
        spacing="5",
        width="100%",
    )


def lineups_tab_view() -> rx.Component:
    """Vista del Tracker de Alineaciones 1-9."""
    return rx.vstack(
        # 1. KPIs Globales de Lineups
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("JUEGOS ANALIZADOS", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{BullpenState.lineup_kpi_total_games} JJ", size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Muestra de partidos", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("JUGADORES TITULARES USADOS", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{BullpenState.lineup_kpi_total_players}", size="6", color=ACCENT_GOLD, font_weight="800"),
                    rx.text("Peloteros en el 1-9", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("MÁS TITULARIDADES", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(BullpenState.lineup_kpi_top_starter, size="5", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text(BullpenState.lineup_kpi_top_starter_jj, size="1", color="#10b981"),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("4TO BATE MÁS FRECUENTE", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(BullpenState.lineup_kpi_top_cleanup, size="5", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text(BullpenState.lineup_kpi_top_cleanup_jj, size="1", color=ACCENT_GOLD),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
            width="100%",
        ),
        # 2. Sub-Tabs de Lineups
        rx.hstack(
            rx.button(
                rx.hstack(rx.icon("credit-card", size=14), rx.text("Tarjeta de Juego (Lineup Card)"), spacing="1"),
                variant=rx.cond(BullpenState.lineup_subtab == "card", "solid", "outline"),
                color_scheme="amber",
                on_click=BullpenState.set_lineup_subtab("card"),
                size="1",
            ),
            rx.button(
                rx.hstack(rx.icon("star", size=14), rx.text("Alineaciones Frecuentes"), spacing="1"),
                variant=rx.cond(BullpenState.lineup_subtab == "frequent", "solid", "outline"),
                color_scheme="amber",
                on_click=BullpenState.set_lineup_subtab("frequent"),
                size="1",
            ),
            rx.button(
                rx.hstack(rx.icon("layout-grid", size=14), rx.text("Matriz de Calor (1 al 9)"), spacing="1"),
                variant=rx.cond(BullpenState.lineup_subtab == "heatmap", "solid", "outline"),
                color_scheme="amber",
                on_click=BullpenState.set_lineup_subtab("heatmap"),
                size="1",
            ),
            rx.button(
                rx.hstack(rx.icon("user", size=14), rx.text("Impacto por Jugador"), spacing="1"),
                variant=rx.cond(BullpenState.lineup_subtab == "player", "solid", "outline"),
                color_scheme="amber",
                on_click=BullpenState.set_lineup_subtab("player"),
                size="1",
            ),
            spacing="2",
        ),
        # 3. Contenido de Sub-Tabs
        rx.cond(
            BullpenState.lineup_subtab == "card",
            # Vista Tarjeta de Juego (Dugout Scorecard)
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.text("SELECCIONAR PARTIDO", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.select(
                            BullpenState.game_lineup_options,
                            value=BullpenState.selected_game_lineup_label,
                            on_change=BullpenState.set_selected_game_lineup,
                            size="3",
                            variant="soft",
                            color_scheme="amber",
                            width="100%",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    style=CARD_STYLE,
                    width="100%",
                ),
                # Dugout Scorecard Banner
                rx.box(
                    rx.hstack(
                        rx.hstack(
                            rx.image(src="/logo.png", width="44px", height="44px", border_radius="8px"),
                            rx.vstack(
                                rx.heading("🦁 Leones del Caracas — Orden al Bate Titular", size="3", color=TEXT_PRIMARY),
                                rx.text(
                                    f"📅 {BullpenState.selected_game_card_date} • {BullpenState.selected_game_card_score}",
                                    size="2",
                                    color=TEXT_MUTED,
                                ),
                                spacing="0",
                            ),
                            align="center",
                            spacing="3",
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.badge(
                                BullpenState.selected_game_card_result,
                                color_scheme=rx.cond(BullpenState.selected_game_card_won, "green", "red"),
                                variant="solid",
                                size="2",
                            ),
                            rx.image(src=BullpenState.selected_game_opp_logo, width="38px", height="38px"),
                            align="center",
                            spacing="3",
                        ),
                        align="center",
                        width="100%",
                    ),
                    padding="1rem 1.25rem",
                    background="rgba(15, 23, 42, 0.95)",
                    border="1px solid rgba(255, 255, 255, 0.1)",
                    border_radius="10px",
                    width="100%",
                ),
                # Lista de Jugadores 1 al 9
                rx.grid(
                    rx.foreach(BullpenState.selected_game_starters, starter_item_card),
                    columns=rx.breakpoints(initial="1", md="2", lg="3"),
                    spacing="3",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.cond(
                BullpenState.lineup_subtab == "frequent",
                # Vista Alineaciones Frecuentes
                rx.box(
                    rx.vstack(
                        rx.heading("COMBINACIONES DE ALINEACIÓN MÁS UTILIZADAS", size="3", color=TEXT_PRIMARY),
                        rx.vstack(
                            rx.foreach(BullpenState.top_frequent_lineups, top_lineup_item),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    style=CARD_STYLE,
                    width="100%",
                ),
                rx.cond(
                    BullpenState.lineup_subtab == "heatmap",
                    # Vista Matriz de Calor
                    rx.box(
                        rx.vstack(
                            rx.heading("MATRIZ DE CALOR: TITULARIDADES POR TURNO 1 AL 9", size="3", color=TEXT_PRIMARY),
                            rx.plotly(data=BullpenState.lineup_heatmap_figure, height="480px", width="100%"),
                            spacing="3",
                            width="100%",
                        ),
                        style=CARD_STYLE,
                        width="100%",
                    ),
                    # Vista Impacto por Jugador
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.text("SELECCIONAR JUGADOR TITULAR", size="1", font_weight="700", color=TEXT_MUTED),
                                rx.select(
                                    BullpenState.player_lineup_options,
                                    value=BullpenState.selected_player_lineup,
                                    on_change=BullpenState.set_selected_player_lineup,
                                    size="3",
                                    variant="soft",
                                    color_scheme="amber",
                                    width="100%",
                                ),
                                spacing="1",
                                align="start",
                            ),
                            style=CARD_STYLE,
                            width="100%",
                        ),
                        rx.grid(
                            rx.box(
                                rx.vstack(
                                    rx.text("JUEGOS COMO TITULAR", size="1", font_weight="700", color=TEXT_MUTED),
                                    rx.heading(f"{BullpenState.player_impact_games} JJ", size="6", color=TEXT_PRIMARY),
                                    spacing="1",
                                ),
                                style=CARD_STYLE,
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("RÉCORD DEL EQUIPO", size="1", font_weight="700", color=TEXT_MUTED),
                                    rx.heading(BullpenState.player_impact_record, size="6", color=ACCENT_GOLD),
                                    spacing="1",
                                ),
                                style=CARD_STYLE,
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("% VICTORIAS", size="1", font_weight="700", color=TEXT_MUTED),
                                    rx.heading(BullpenState.player_impact_pct, size="6", color="#10b981"),
                                    spacing="1",
                                ),
                                style=CARD_STYLE,
                            ),
                            columns=rx.breakpoints(initial="1", sm="3"),
                            spacing="3",
                            width="100%",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.heading("DESGLOSE DE RENDIMIENTO POR TURNO AL BATE", size="3", color=TEXT_PRIMARY),
                                rx.box(
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell("Turno"),
                                                rx.table.column_header_cell("Titularidades"),
                                                rx.table.column_header_cell("Victorias"),
                                                rx.table.column_header_cell("Derrotas"),
                                                rx.table.column_header_cell("% Victorias"),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(BullpenState.player_order_breakdown, player_slot_row)
                                        ),
                                        variant="surface",
                                        size="1",
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
                    ),
                ),
            ),
        ),
        spacing="5",
        width="100%",
    )


def bullpen_content() -> rx.Component:
    """Contenido principal de la página Bullpen & Lineups."""
    return rx.vstack(
        # Tabs de Navegación del Módulo
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon("shield", size=16),
                    rx.text("Efectividad Relevistas (IR/IRS)", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(BullpenState.active_tab == "bullpen", "solid", "outline"),
                color_scheme="amber",
                on_click=BullpenState.set_active_tab("bullpen"),
                size="2",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("clipboard-list", size=16),
                    rx.text("Tracker de Lineups 1-9", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(BullpenState.active_tab == "lineups", "solid", "outline"),
                color_scheme="amber",
                on_click=BullpenState.set_active_tab("lineups"),
                size="2",
            ),
            spacing="3",
            padding_bottom="0.5rem",
        ),
        # Renderizado Condicional
        rx.cond(
            BullpenState.active_tab == "bullpen",
            bullpen_tab_view(),
            lineups_tab_view(),
        ),
        # Glosario & Metodología
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon("book-open", size=16, color=ACCENT_GOLD),
                    rx.text("Guía y Metodología: Relevistas IR/IRS y Optimización de Lineups", size="2", font_weight="700", color=TEXT_PRIMARY),
                    spacing="2",
                    align="center",
                ),
                content=rx.vstack(
                    rx.grid(
                        rx.box(
                            rx.text("🛡️ Corredores Heredados (IR / IRS)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("IR son corredores que ya estaban en base cuando entró el relevista; IRS son los que anotaron. Una tasa IRS% < 20% califica al relevista como 'apagafuegos élite'.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("📋 Optimización de Órdenes al Bate (Tom Tango)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("El 1ro y 2do bate requieren máximo OBP; el 4to y 5to bate maximizan el poder de extrabases (SLG) para remolcar las carreras.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("📊 Rotación de Alineaciones", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Rastrear qué combinación exacta de 9 jugadores genera mayor porcentaje de victorias permite al cuerpo técnico optimizar el balance ofensivo.", size="1", color=TEXT_MUTED),
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
                value="bullpen_methodology",
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def bullpen() -> rx.Component:
    """Vista principal de Bullpen y Lineups en Reflex."""
    return layout(
        content=bullpen_content(),
        page_title="Bullpen & Tracker de Alineaciones",
        page_description="Efectividad en herencia de corredores (IR/IRS) y optimización del orden al bate 1-9.",
        current_route="/bullpen",
    )
