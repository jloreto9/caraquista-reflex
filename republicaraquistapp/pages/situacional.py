# republicaraquistapp/pages/situacional.py
"""
situacional.py
--------------
Vista para el análisis de Desempeño Situacional (RISP, Clutch),
LOB Tracker (Dejados en Base) y Matriz de Enfrentamientos BvP.
Ruta: /situacional
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
from republicaraquistapp.state.situacional_state import SituationalState
from republicaraquistapp.components.layout import layout


def split_table_row(s: Dict[str, Any]) -> rx.Component:
    """Fila para la tabla de splits situacionales."""
    return rx.table.row(
        rx.table.cell(rx.text(s["sit"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(s["pa"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["ab"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["h"], size="2", color=TEXT_PRIMARY, font_weight="600")),
        rx.table.cell(rx.text(s["h2b"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["h3b"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["hr"], size="2", color=ACCENT_GOLD, font_weight="600")),
        rx.table.cell(rx.text(s["bb"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["so"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["rbi"], size="2", color=TEXT_PRIMARY, font_weight="700")),
        rx.table.cell(rx.text(s["avg"], size="2", color=TEXT_PRIMARY, font_weight="700")),
        rx.table.cell(rx.text(s["obp"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(s["slg"], size="2", color=TEXT_MUTED)),
        rx.table.cell(
            rx.badge(s["ops"], color_scheme="amber", variant="solid", size="1", font_weight="800")
        ),
    )


def lob_table_row(p: Dict[str, Any]) -> rx.Component:
    """Fila para la tabla de dejados en base por bateador."""
    return rx.table.row(
        rx.table.cell(rx.text(p["batter"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(p["pa"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(p["risp_pa"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(p["rbi"], size="2", color=TEXT_PRIMARY, font_weight="600")),
        rx.table.cell(rx.text(p["risp_avg"], size="2", color=ACCENT_GOLD, font_weight="700")),
        rx.table.cell(rx.text(p["lob_ending"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(p["risp_lob_ending"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(p["risp_lob_mid"], size="2", color=TEXT_PRIMARY)),
        rx.table.cell(
            rx.badge(p["total_risp_lob"], color_scheme="red", variant="solid", size="1", font_weight="800")
        ),
    )


def bvp_table_row(r: Dict[str, Any]) -> rx.Component:
    """Fila para la matriz BvP contra lanzadores rivales."""
    return rx.table.row(
        rx.table.cell(
            rx.image(src=r["logo"], width="22px", height="22px", border_radius="4px")
        ),
        rx.table.cell(rx.text(r["pitcher"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(r["opp_team"], size="1", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["pa"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["ab"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["h"], size="2", color=TEXT_PRIMARY, font_weight="600")),
        rx.table.cell(rx.text(r["hr"], size="2", color=ACCENT_GOLD, font_weight="600")),
        rx.table.cell(rx.text(r["rbi"], size="2", color=TEXT_PRIMARY, font_weight="700")),
        rx.table.cell(rx.text(r["bb"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["so"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["avg"], size="2", color=TEXT_PRIMARY, font_weight="700")),
        rx.table.cell(rx.text(r["obp"], size="2", color=TEXT_MUTED)),
        rx.table.cell(rx.text(r["slg"], size="2", color=TEXT_MUTED)),
        rx.table.cell(
            rx.badge(r["ops"], color_scheme="amber", variant="solid", size="1", font_weight="800")
        ),
    )


def situational_splits_tab() -> rx.Component:
    """Vista de splits situacionales y comparativa de OPS."""
    return rx.vstack(
        # 1. Selector de Bateador
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("SELECCIONAR BATEADOR DE LEONES", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.select(
                        SituationalState.batter_options,
                        value=SituationalState.selected_batter,
                        on_change=SituationalState.set_selected_batter,
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
                align="center",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # 2. Rejilla de 6 KPIs Situacionales
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("TOTAL PA", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SituationalState.kpi_pa, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Viajes al plato", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("AVG GENERAL", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SituationalState.kpi_avg, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Promedio H / AB", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("AVG EN RISP", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.badge(SituationalState.kpi_risp_avg_delta, color_scheme="green", variant="soft", size="1"),
                        align="center",
                        spacing="2",
                    ),
                    rx.heading(SituationalState.kpi_risp_avg, size="6", color=ACCENT_GOLD, font_weight="800"),
                    rx.text("Posición Anotadora", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("OPS EN RISP", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.badge(SituationalState.kpi_risp_ops_delta, color_scheme="amber", variant="soft", size="1"),
                        align="center",
                        spacing="2",
                    ),
                    rx.heading(SituationalState.kpi_risp_ops, size="6", color=ACCENT_GOLD, font_weight="800"),
                    rx.text("OBP + SLG con RISP", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("2-OUTS RISP", size="1", font_weight="700", color=TEXT_MUTED),
                        rx.badge(SituationalState.kpi_clutch_avg_delta, color_scheme="blue", variant="soft", size="1"),
                        align="center",
                        spacing="2",
                    ),
                    rx.heading(SituationalState.kpi_clutch_avg, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Bateo Clutch", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("TOTAL RBI", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SituationalState.kpi_rbi, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Carreras impulsadas", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            columns=rx.breakpoints(initial="2", sm="3", lg="6"),
            spacing="3",
            width="100%",
        ),
        # 3. Grilla de Gráfico OPS y Tabla Completa de Splits
        rx.grid(
            # Gráfico Comparativo OPS
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("bar-chart-3", size=18, color=ACCENT_GOLD),
                        rx.heading("PRODUCCIÓN OFENSIVA (OPS) POR SITUACIÓN", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.plotly(data=SituationalState.ops_chart_figure, height="400px", width="100%"),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            # Tabla Completa de Splits
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("table", size=18, color=ACCENT_GOLD),
                        rx.heading("TABLA DE SPLITS SITUACIONALES", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Situación"),
                                    rx.table.column_header_cell("PA"),
                                    rx.table.column_header_cell("AB"),
                                    rx.table.column_header_cell("H"),
                                    rx.table.column_header_cell("2B"),
                                    rx.table.column_header_cell("3B"),
                                    rx.table.column_header_cell("HR"),
                                    rx.table.column_header_cell("BB"),
                                    rx.table.column_header_cell("SO"),
                                    rx.table.column_header_cell("RBI"),
                                    rx.table.column_header_cell("AVG"),
                                    rx.table.column_header_cell("OBP"),
                                    rx.table.column_header_cell("SLG"),
                                    rx.table.column_header_cell("OPS"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(SituationalState.splits_table_data, split_table_row)
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
        spacing="5",
        width="100%",
    )


def lob_tracker_tab() -> rx.Component:
    """Vista de Dejados en Base (LOB Tracker)."""
    return rx.vstack(
        # 1. Rejilla de 4 KPIs de LOB
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("LOB AL TERMINAR INNING", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{SituationalState.lob_total_ending}", size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("3er out de la entrada", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("RISP LOB AL TERMINAR INNING", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{SituationalState.lob_risp_ending}", size="6", color=ACCENT_GOLD, font_weight="800"),
                    rx.text("Corredores en 2B/3B con 2 outs", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("RISP LOB DENTRO DE INNING", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{SituationalState.lob_risp_mid}", size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("0-1 out sin remolcar carrera", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("TOTAL GENERAL RISP LOB", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{SituationalState.lob_risp_total}", size="6", color=LEONES_RED, font_weight="800"),
                    rx.text("Tráfico total no capitalizado", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            columns=rx.breakpoints(initial="2", sm="4"),
            spacing="3",
            width="100%",
        ),
        # 2. Grilla de Gráfico y Tabla LOB
        rx.grid(
            # Gráfico de Top Bateadores RISP LOB
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("octagon-alert", size=18, color=LEONES_RED),
                        rx.heading("TOP BATEADORES CON MÁS RISP LOB", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.plotly(data=SituationalState.lob_chart_figure, height="360px", width="100%"),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            # Tabla Individual LOB
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("list", size=18, color=ACCENT_GOLD),
                        rx.heading("DESGLOSE INDIVIDUAL DE DEJADOS EN BASE", size="3", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Bateador"),
                                    rx.table.column_header_cell("PA"),
                                    rx.table.column_header_cell("PA RISP"),
                                    rx.table.column_header_cell("RBI"),
                                    rx.table.column_header_cell("AVG RISP"),
                                    rx.table.column_header_cell("LOB 3er Out"),
                                    rx.table.column_header_cell("RISP 3er Out"),
                                    rx.table.column_header_cell("RISP Mid-Inn"),
                                    rx.table.column_header_cell("Total RISP LOB"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(SituationalState.lob_players_data, lob_table_row)
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
        spacing="5",
        width="100%",
    )


def bvp_matchup_tab() -> rx.Component:
    """Vista de Enfrentamientos Cara a Cara (BvP: Bateador vs Lanzador)."""
    return rx.vstack(
        # Filtros de Bateador y Equipo Rival
        rx.box(
            rx.grid(
                rx.vstack(
                    rx.text("BATEADOR DE LEONES", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.select(
                        SituationalState.bvp_batter_options,
                        value=SituationalState.selected_bvp_batter,
                        on_change=SituationalState.set_bvp_batter,
                        size="3",
                        variant="soft",
                        color_scheme="amber",
                        width="100%",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text("FILTRAR POR EQUIPO RIVAL", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.select(
                        SituationalState.rival_team_options,
                        value=SituationalState.selected_rival_team,
                        on_change=SituationalState.set_rival_team,
                        size="3",
                        variant="soft",
                        color_scheme="gray",
                        width="100%",
                    ),
                    spacing="1",
                    align="start",
                ),
                columns=rx.breakpoints(initial="1", md="2"),
                spacing="4",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Tabla BvP
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("swords", size=18, color=ACCENT_GOLD),
                    rx.heading("HISTORIAL CARA A CARA (BVP)", size="3", color=TEXT_PRIMARY),
                    rx.spacer(),
                    align="center",
                    width="100%",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Logo"),
                                rx.table.column_header_cell("Lanzador Rival"),
                                rx.table.column_header_cell("Equipo"),
                                rx.table.column_header_cell("PA"),
                                rx.table.column_header_cell("AB"),
                                rx.table.column_header_cell("H"),
                                rx.table.column_header_cell("HR"),
                                rx.table.column_header_cell("RBI"),
                                rx.table.column_header_cell("BB"),
                                rx.table.column_header_cell("SO"),
                                rx.table.column_header_cell("AVG"),
                                rx.table.column_header_cell("OBP"),
                                rx.table.column_header_cell("SLG"),
                                rx.table.column_header_cell("OPS"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(SituationalState.bvp_table_data, bvp_table_row)
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


def situacional_content() -> rx.Component:
    """Contenido principal de la página Situacional."""
    return rx.vstack(
        # Tabs de Navegación del Módulo
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon("target", size=16),
                    rx.text("Rendimiento Situacional (RISP)", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(SituationalState.active_tab == "splits", "solid", "outline"),
                color_scheme="amber",
                on_click=SituationalState.set_active_tab("splits"),
                size="2",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("octagon-alert", size=16),
                    rx.text("LOB Tracker (Dejados en Base)", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(SituationalState.active_tab == "lob", "solid", "outline"),
                color_scheme="amber",
                on_click=SituationalState.set_active_tab("lob"),
                size="2",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("swords", size=16),
                    rx.text("Cara a Cara BvP", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(SituationalState.active_tab == "bvp", "solid", "outline"),
                color_scheme="amber",
                on_click=SituationalState.set_active_tab("bvp"),
                size="2",
            ),
            spacing="3",
            padding_bottom="0.5rem",
        ),
        # Renderizado Condicional de la Pestaña
        rx.cond(
            SituationalState.active_tab == "splits",
            situational_splits_tab(),
            rx.cond(
                SituationalState.active_tab == "lob",
                lob_tracker_tab(),
                bvp_matchup_tab(),
            ),
        ),
        # Glosario & Metodología
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon("book-open", size=16, color=ACCENT_GOLD),
                    rx.text("Guía y Glosario Sabermétrico de Métricas Situacionales y LOB", size="2", font_weight="700", color=TEXT_PRIMARY),
                    spacing="2",
                    align="center",
                ),
                content=rx.vstack(
                    rx.grid(
                        rx.box(
                            rx.text("🎯 RISP (Runners in Scoring Position)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Bateo con corredores en 2da o 3ra base. Mide la habilidad oportuna para producir carreras cuando hay hombres en posición de anotar.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("🛑 RISP LOB al 3er Out", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Corredores en 2B o 3B varados al caer el último out de la entrada. Equivale al LOB de alta presión que cierra el episodio.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("⚡ RISP LOB Dentro de Inning", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Turnos con 0 o 1 out con hombres en RISP donde el bateador fue puesto out sin empujar carrera (RBI=0). Oportunidades no aprovechadas antes del 3er out.", size="1", color=TEXT_MUTED),
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
                value="sit_methodology",
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def situacional() -> rx.Component:
    """Vista principal de Análisis Situacional y LOB en Reflex."""
    return layout(
        content=situacional_content(),
        page_title="Desempeño Situacional & LOB Tracker",
        page_description="Splits ofensivos (RISP, Clutch, Bases Llenas), rastreo científico de Dejados en Base y matriz BvP.",
        current_route="/situacional",
    )
