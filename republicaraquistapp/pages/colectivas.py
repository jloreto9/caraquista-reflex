# republicaraquistapp/pages/colectivas.py
"""
colectivas.py
-------------
Vista completa de Estadísticas Colectivas de los 8 equipos de la LVBP en Reflex.
Contiene:
1. Pestaña de Bateo Colectivo (KPIs líderes, tabla comparativa de 8 equipos y gráfico horizontal Plotly interactivo).
2. Pestaña de Pitcheo Colectivo (KPIs líderes, tabla comparativa de efectividad y staff monticular con gráfico Plotly).
3. Pestaña de Fildeo Colectivo (KPIs líderes, tabla defensiva de 8 franquicias con gráfico Plotly).
4. Selector de Fase del Torneo (Regular, Round Robin, Serie Final, Comodín, Todas).
"""

from typing import Dict, Any
import reflex as rx

from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
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
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
)
from republicaraquistapp.components.layout import layout
from republicaraquistapp.state.colectivas_state import ColectivasState


# ── Componente de KPI Colectivo ───────────────────────────────────────────────
def collective_kpi_card(title: str, value: str, team_name: str, icon_name: str) -> rx.Component:
    """Tarjeta KPI estilizada para líderes colectivos de la liga."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon_name, size=18, color=ACCENT_GOLD),
                rx.text(title, size="1", font_weight="700", color=TEXT_MUTED, letter_spacing="0.05em"),
                rx.spacer(),
                align="center",
                width="100%",
            ),
            rx.heading(value, size="6", font_weight="800", color=TEXT_PRIMARY),
            rx.text(team_name, size="2", font_weight="600", color=ACCENT_GOLD, no_of_lines=1),
            spacing="1",
            align="start",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


# ── Fila de Bateo Colectivo ──────────────────────────────────────────────────
def collective_batting_row(t: Dict[str, Any]) -> rx.Component:
    """Fila de equipo en la tabla de bateo colectivo."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=t["logo"], width="28px", height="28px", border_radius="6px"),
                rx.text(t["team_name"], size="2", font_weight="700", color=rx.cond(t["is_leones"], ACCENT_GOLD, TEXT_PRIMARY)),
                rx.cond(t["is_leones"], rx.badge("CAR", style=GOLD_BADGE_STYLE), rx.fragment()),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(t["games"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["pa"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["ab"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(t["r"], size="2", color=TEXT_PRIMARY, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["h"], size="2", color=TEXT_PRIMARY, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["doubles"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["triples"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["hr"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["rbi"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(t["bb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["so"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["sb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["avg_str"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["obp_str"], size="2", color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(t["slg_str"], size="2", color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.badge(t["ops_str"], color_scheme="amber", variant="soft", size="1")),
        rx.table.cell(rx.text(t["lob"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["babip_str"], size="2", color=TEXT_MUTED, text_align="center")),
        background=rx.cond(t["is_leones"], "rgba(253, 184, 39, 0.08)", "transparent"),
        border_left=rx.cond(t["is_leones"], "3px solid #FDB827", "none"),
        _hover={"background": "rgba(253, 184, 39, 0.05)"},
    )


# ── Fila de Pitcheo Colectivo ────────────────────────────────────────────────
def collective_pitching_row(t: Dict[str, Any]) -> rx.Component:
    """Fila de equipo en la tabla de pitcheo colectivo."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=t["logo"], width="28px", height="28px", border_radius="6px"),
                rx.text(t["team_name"], size="2", font_weight="700", color=rx.cond(t["is_leones"], ACCENT_GOLD, TEXT_PRIMARY)),
                rx.cond(t["is_leones"], rx.badge("CAR", style=GOLD_BADGE_STYLE), rx.fragment()),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(t["games"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["wins"], size="2", color="var(--green-9)", font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["losses"], size="2", color="var(--red-9)", font_weight="700", text_align="center")),
        rx.table.cell(rx.badge(t["era_str"], color_scheme="amber", variant="soft", size="1")),
        rx.table.cell(rx.text(t["whip_str"], size="2", color=TEXT_PRIMARY, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["sv"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["holds"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["blown_saves"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["ip_str"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(t["h"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["r"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["er"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["bb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["so"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["hr"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["k9_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["bb9_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["k_bb_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["baa_str"], size="2", color=TEXT_PRIMARY, text_align="center")),
        background=rx.cond(t["is_leones"], "rgba(253, 184, 39, 0.08)", "transparent"),
        border_left=rx.cond(t["is_leones"], "3px solid #FDB827", "none"),
        _hover={"background": "rgba(253, 184, 39, 0.05)"},
    )


# ── Fila de Fildeo Colectivo ─────────────────────────────────────────────────
def collective_fielding_row(t: Dict[str, Any]) -> rx.Component:
    """Fila de equipo en la tabla de fildeo colectivo."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=t["logo"], width="28px", height="28px", border_radius="6px"),
                rx.text(t["team_name"], size="2", font_weight="700", color=rx.cond(t["is_leones"], ACCENT_GOLD, TEXT_PRIMARY)),
                rx.cond(t["is_leones"], rx.badge("CAR", style=GOLD_BADGE_STYLE), rx.fragment()),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(t["games"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["innings"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["po"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(t["a"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(t["e"], size="2", color="var(--red-9)", font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["tc"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.badge(t["fpct_str"], color_scheme="green", variant="soft", size="1")),
        rx.table.cell(rx.text(t["dp"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(t["tp"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["pb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(t["cs"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(t["sb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.badge(t["cs_pct_str"], color_scheme="amber", variant="solid", size="1")),
        rx.table.cell(rx.text(t["rf9_str"], size="2", color=TEXT_MUTED, text_align="center")),
        background=rx.cond(t["is_leones"], "rgba(253, 184, 39, 0.08)", "transparent"),
        border_left=rx.cond(t["is_leones"], "3px solid #FDB827", "none"),
        _hover={"background": "rgba(253, 184, 39, 0.05)"},
    )


# ── 1. VISTA DE BATEO COLECTIVO ──────────────────────────────────────────────
def collective_batting_tab() -> rx.Component:
    """Vista comparativa de bateo para los 8 equipos."""
    return rx.vstack(
        # Rejilla de KPIs
        rx.grid(
            collective_kpi_card("LÍDER AVG LIGA", ColectivasState.batting_kpis["avg_val"], ColectivasState.batting_kpis["avg_team"], "award"),
            collective_kpi_card("LÍDER OPS LIGA", ColectivasState.batting_kpis["ops_val"], ColectivasState.batting_kpis["ops_team"], "zap"),
            collective_kpi_card("LÍDER JONRONES", ColectivasState.batting_kpis["hr_val"], ColectivasState.batting_kpis["hr_team"], "flame"),
            collective_kpi_card("LÍDER ANOTADAS", ColectivasState.batting_kpis["r_val"], ColectivasState.batting_kpis["r_team"], "trending-up"),
            columns=rx.breakpoints(initial="2", md="4"),
            spacing="3",
            width="100%",
        ),
        # Tabla de Bateo Colectivo
        rx.box(
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Equipo"),
                            rx.table.column_header_cell("JJ"),
                            rx.table.column_header_cell("PA"),
                            rx.table.column_header_cell("AB"),
                            rx.table.column_header_cell("R"),
                            rx.table.column_header_cell("H"),
                            rx.table.column_header_cell("2B"),
                            rx.table.column_header_cell("3B"),
                            rx.table.column_header_cell("HR"),
                            rx.table.column_header_cell("RBI"),
                            rx.table.column_header_cell("BB"),
                            rx.table.column_header_cell("SO"),
                            rx.table.column_header_cell("SB"),
                            rx.table.column_header_cell("AVG"),
                            rx.table.column_header_cell("OBP"),
                            rx.table.column_header_cell("SLG"),
                            rx.table.column_header_cell("OPS"),
                            rx.table.column_header_cell("LOB"),
                            rx.table.column_header_cell("BABIP"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(ColectivasState.collective_batting_data, collective_batting_row),
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
                overflow_x="auto",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Gráfico Comparativo Horizontal
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("COMPARADOR GRÁFICO DE OFENSIVA", size="3", font_weight="800", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.hstack(
                        rx.text("Métrica:", size="2", font_weight="600", color=TEXT_MUTED),
                        rx.select(
                            ["ops", "avg", "obp", "slg", "hr", "r", "h", "bb", "sb", "lob"],
                            value=ColectivasState.selected_batting_metric,
                            on_change=ColectivasState.set_batting_metric,
                            size="2",
                            variant="soft",
                            color_scheme="amber",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.plotly(data=ColectivasState.batting_bar_chart),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Glosario Desplegable
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text("📖 Glosario: Métricas de Bateo Colectivo", font_weight="700", color=ACCENT_GOLD),
                content=rx.vstack(
                    rx.text("• R (Carreras): Total de anotaciones registradas por el equipo.", size="2", color=TEXT_MUTED),
                    rx.text("• OPS Colectivo: On-base Plus Slugging global. Mide la potencia combinada de la franquicia.", size="2", color=TEXT_MUTED),
                    rx.text("• LOB (Left On Base): Corredores dejados en base que no lograron anotar.", size="2", color=TEXT_MUTED),
                    rx.text("• BABIP Colectivo: Promedio en bolas puestas en juego de todo el lineup.", size="2", color=TEXT_MUTED),
                    spacing="2",
                    padding_y="0.5rem",
                ),
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── 2. VISTA DE PITCHEO COLECTIVO ────────────────────────────────────────────
def collective_pitching_tab() -> rx.Component:
    """Vista comparativa de pitcheo para los 8 equipos."""
    return rx.vstack(
        # Rejilla de KPIs
        rx.grid(
            collective_kpi_card("MEJOR EFECTIVIDAD", ColectivasState.pitching_kpis["era_val"], ColectivasState.pitching_kpis["era_team"], "shield"),
            collective_kpi_card("MEJOR WHIP LIGA", ColectivasState.pitching_kpis["whip_val"], ColectivasState.pitching_kpis["whip_team"], "target"),
            collective_kpi_card("LÍDER EN PONCHES", ColectivasState.pitching_kpis["so_val"], ColectivasState.pitching_kpis["so_team"], "zap"),
            collective_kpi_card("LÍDER EN SALVADOS", ColectivasState.pitching_kpis["sv_val"], ColectivasState.pitching_kpis["sv_team"], "lock"),
            columns=rx.breakpoints(initial="2", md="4"),
            spacing="3",
            width="100%",
        ),
        # Tabla de Pitcheo Colectivo
        rx.box(
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Equipo"),
                            rx.table.column_header_cell("JJ"),
                            rx.table.column_header_cell("G"),
                            rx.table.column_header_cell("P"),
                            rx.table.column_header_cell("ERA"),
                            rx.table.column_header_cell("WHIP"),
                            rx.table.column_header_cell("SV"),
                            rx.table.column_header_cell("HLD"),
                            rx.table.column_header_cell("BS"),
                            rx.table.column_header_cell("IP"),
                            rx.table.column_header_cell("H"),
                            rx.table.column_header_cell("R"),
                            rx.table.column_header_cell("CL"),
                            rx.table.column_header_cell("BB"),
                            rx.table.column_header_cell("SO"),
                            rx.table.column_header_cell("HR"),
                            rx.table.column_header_cell("K/9"),
                            rx.table.column_header_cell("BB/9"),
                            rx.table.column_header_cell("K/BB"),
                            rx.table.column_header_cell("BAA"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(ColectivasState.collective_pitching_data, collective_pitching_row),
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
                overflow_x="auto",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Gráfico Comparativo Horizontal
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("COMPARADOR GRÁFICO DE PITCHEO", size="3", font_weight="800", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.hstack(
                        rx.text("Métrica:", size="2", font_weight="600", color=TEXT_MUTED),
                        rx.select(
                            ["era", "whip", "so", "k9", "bb", "k_bb", "sv", "baa"],
                            value=ColectivasState.selected_pitching_metric,
                            on_change=ColectivasState.set_pitching_metric,
                            size="2",
                            variant="soft",
                            color_scheme="amber",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.plotly(data=ColectivasState.pitching_bar_chart),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Glosario Desplegable
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text("📖 Glosario: Métricas de Pitcheo Colectivo", font_weight="700", color=ACCENT_GOLD),
                content=rx.vstack(
                    rx.text("• ERA Colectivo: Carreras limpias permitidas por el staff monticular completo cada 9 entradas.", size="2", color=TEXT_MUTED),
                    rx.text("• WHIP Colectivo: Tráfico promedio de corredores permitidos por entrada.", size="2", color=TEXT_MUTED),
                    rx.text("• HLD (Holds) & BS (Blown Saves): Eficiencia y solvencia del cuerpo de relevistas en ventajas.", size="2", color=TEXT_MUTED),
                    rx.text("• BAA: Batting Average Against (promedio de bateo que le conectan a los lanzadores del equipo).", size="2", color=TEXT_MUTED),
                    spacing="2",
                    padding_y="0.5rem",
                ),
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── 3. VISTA DE FILDEO COLECTIVO ─────────────────────────────────────────────
def collective_fielding_tab() -> rx.Component:
    """Vista comparativa de fildeo para los 8 equipos."""
    return rx.vstack(
        # Rejilla de KPIs
        rx.grid(
            collective_kpi_card("MEJOR % FILDEO", ColectivasState.fielding_kpis["fpct_val"], ColectivasState.fielding_kpis["fpct_team"], "shield-check"),
            collective_kpi_card("MENOS ERRORES", ColectivasState.fielding_kpis["e_val"], ColectivasState.fielding_kpis["e_team"], "check"),
            collective_kpi_card("MÁS DOUBLE PLAYS", ColectivasState.fielding_kpis["dp_val"], ColectivasState.fielding_kpis["dp_team"], "shuffle"),
            collective_kpi_card("MEJOR % CAPTURA", ColectivasState.fielding_kpis["cs_pct_val"], ColectivasState.fielding_kpis["cs_pct_team"], "lock"),
            columns=rx.breakpoints(initial="2", md="4"),
            spacing="3",
            width="100%",
        ),
        # Tabla de Fildeo Colectivo
        rx.box(
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Equipo"),
                            rx.table.column_header_cell("JJ"),
                            rx.table.column_header_cell("Inn"),
                            rx.table.column_header_cell("PO"),
                            rx.table.column_header_cell("A"),
                            rx.table.column_header_cell("E"),
                            rx.table.column_header_cell("TC"),
                            rx.table.column_header_cell("FPCT"),
                            rx.table.column_header_cell("DP"),
                            rx.table.column_header_cell("TP"),
                            rx.table.column_header_cell("PB"),
                            rx.table.column_header_cell("CS"),
                            rx.table.column_header_cell("SB"),
                            rx.table.column_header_cell("CS%"),
                            rx.table.column_header_cell("RF/9"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(ColectivasState.collective_fielding_data, collective_fielding_row),
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
                overflow_x="auto",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Gráfico Comparativo Horizontal
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("COMPARADOR GRÁFICO DE FILDEO", size="3", font_weight="800", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.hstack(
                        rx.text("Métrica:", size="2", font_weight="600", color=TEXT_MUTED),
                        rx.select(
                            ["fpct", "e", "dp", "a", "po", "tc", "cs_pct"],
                            value=ColectivasState.selected_fielding_metric,
                            on_change=ColectivasState.set_fielding_metric,
                            size="2",
                            variant="soft",
                            color_scheme="amber",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.plotly(data=ColectivasState.fielding_bar_chart),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Glosario Desplegable
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text("📖 Glosario: Métricas de Fildeo Colectivo", font_weight="700", color=ACCENT_GOLD),
                content=rx.vstack(
                    rx.text("• FPCT Colectivo: Porcentaje de fildeo sin error de toda la franquicia.", size="2", color=TEXT_MUTED),
                    rx.text("• DP (Double Plays): Jugadas de dos outs simultáneos completadas para abortar rallies rivales.", size="2", color=TEXT_MUTED),
                    rx.text("• CS% Colectivo: Eficiencia de la receptoría del equipo para atrapar corredores en intento de robo.", size="2", color=TEXT_MUTED),
                    spacing="2",
                    padding_y="0.5rem",
                ),
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Contenido Principal de /colectivas ────────────────────────────────────────
def colectivas_content() -> rx.Component:
    """Cuerpo de la vista /colectivas con selector de fase y pestañas."""
    return rx.vstack(
        # Barra Superior de Control: Fase y Pestañas
        rx.box(
            rx.hstack(
                # Selector de Fase del Torneo
                rx.hstack(
                    rx.icon("trophy", size=16, color=ACCENT_GOLD),
                    rx.text("Fase:", size="2", font_weight="700", color=TEXT_MUTED),
                    rx.select(
                        ColectivasState.phase_options,
                        value=ColectivasState.selected_phase_name,
                        on_change=ColectivasState.set_phase_by_name,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                # Pestañas
                rx.hstack(
                    rx.button(
                        rx.hstack(rx.icon("flame", size=16), rx.text("🏏 Bateo"), align="center", spacing="2"),
                        on_click=ColectivasState.set_active_tab("bateo"),
                        style=rx.cond(ColectivasState.active_tab == "bateo", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
                    ),
                    rx.button(
                        rx.hstack(rx.icon("zap", size=16), rx.text("⚡ Pitcheo"), align="center", spacing="2"),
                        on_click=ColectivasState.set_active_tab("pitcheo"),
                        style=rx.cond(ColectivasState.active_tab == "pitcheo", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
                    ),
                    rx.button(
                        rx.hstack(rx.icon("shield", size=16), rx.text("🧤 Fildeo"), align="center", spacing="2"),
                        on_click=ColectivasState.set_active_tab("fildeo"),
                        style=rx.cond(ColectivasState.active_tab == "fildeo", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
                    ),
                    spacing="2",
                ),
                align="center",
                width="100%",
                wrap="wrap",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Vistas Condicionales
        rx.cond(
            ColectivasState.active_tab == "bateo",
            collective_batting_tab(),
            rx.cond(
                ColectivasState.active_tab == "pitcheo",
                collective_pitching_tab(),
                collective_fielding_tab(),
            ),
        ),
        spacing="5",
        width="100%",
    )


def colectivas() -> rx.Component:
    """Página de Estadísticas Colectivas de la LVBP."""
    return layout(
        content=colectivas_content(),
        page_title="ESTADÍSTICAS COLECTIVAS — 8 EQUIPOS LVBP",
        page_description="Comparativa completa de ofensiva, pitcheo y fildeo entre todos los equipos de la liga con gráficos Plotly interactivos.",
        current_route="/colectivas",
    )
