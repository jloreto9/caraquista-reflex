# republicaraquistapp/pages/individuales.py
"""
individuales.py
---------------
Vista completa de Estadísticas Individuales de los Leones del Caracas en Reflex.
Contiene:
1. Pestaña de Bateo (Líderes, filtros de AB/búsqueda, tabla sabermétrica con AVG, OBP, SLG, OPS, ISO, BABIP, wOBA, wRC+).
2. Pestaña de Pitcheo (Líderes, filtros abridor/relevista/IP, tabla con ERA, WHIP, FIP, K/9, BB/9, K/BB, IP, SV).
3. Pestaña de Fildeo / Defensa (Líderes, filtros por posición, tabla defensiva con PO, A, E, TC, FPCT, DP, RF/9 y catchers CS/SB/CS%/PB).
4. Comparador Head-to-Head (H2H) con Radar Polar de 8 dimensiones sabermétricas, tarjetas de perfil, tabla cara a cara y veredicto.
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
from republicaraquistapp.state.individuales_state import IndividualesState


# ── Componente de KPI Individual ──────────────────────────────────────────────
def individual_kpi_card(title: str, value: str, subtitle: str, icon_name: str, color_scheme: str = "amber") -> rx.Component:
    """Tarjeta KPI estilizada para líderes individuales."""
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
            rx.text(subtitle, size="2", font_weight="600", color=ACCENT_GOLD, no_of_lines=1),
            spacing="1",
            align="start",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


# ── Fila de Bateador ─────────────────────────────────────────────────────────
def batting_row(p: Dict[str, Any]) -> rx.Component:
    """Fila de la tabla de bateo con métricas avanzadas."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=p["headshot"], width="28px", height="28px", border_radius="50%", fallback="/logo.png"),
                rx.text(p["player_name"], size="2", font_weight="700", color=TEXT_PRIMARY),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(p["pa"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["ab"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(p["r"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["h"], size="2", color=TEXT_PRIMARY, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["doubles"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["triples"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["hr"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["rbi"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(p["bb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["so"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["sb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["avg_str"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["obp_str"], size="2", color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(p["slg_str"], size="2", color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.badge(p["ops_str"], color_scheme="amber", variant="soft", size="1")),
        rx.table.cell(rx.text(p["iso_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["babip_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["woba_str"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(
            rx.badge(
                p["wrc_plus"],
                color_scheme=p["wrc_color"],
                variant="solid",
                size="1",
            )
        ),
        _hover={"background": "rgba(253, 184, 39, 0.05)"},
    )


# ── Fila de Lanzador ─────────────────────────────────────────────────────────
def pitching_row(p: Dict[str, Any]) -> rx.Component:
    """Fila de la tabla de pitcheo con métricas avanzadas."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=p["headshot"], width="28px", height="28px", border_radius="50%", fallback="/logo.png"),
                rx.vstack(
                    rx.text(p["player_name"], size="2", font_weight="700", color=TEXT_PRIMARY),
                    rx.badge(p["role"], color_scheme=p["role_color"], variant="soft", size="1"),
                    spacing="0",
                    align="start",
                ),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.text(p["g"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["gs"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(f"{p['w']}-{p['l']}", size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(p["sv"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["ip_str"], size="2", color=TEXT_PRIMARY, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["h"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["r"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["er"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["bb"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["so"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["hr"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.badge(p["era_str"], color_scheme="amber", variant="soft", size="1")),
        rx.table.cell(rx.text(p["whip_str"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(p["fip_str"], size="2", color=TEXT_PRIMARY, text_align="center")),
        rx.table.cell(rx.text(p["k9_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["bb9_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["k_bb_str"], size="2", color=TEXT_MUTED, text_align="center")),
        _hover={"background": "rgba(253, 184, 39, 0.05)"},
    )


# ── Fila de Fildeo ───────────────────────────────────────────────────────────
def fielding_row(p: Dict[str, Any]) -> rx.Component:
    """Fila de la tabla de fildeo y defensiva."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.image(src=p["headshot"], width="28px", height="28px", border_radius="50%", fallback="/logo.png"),
                rx.text(p["player_name"], size="2", font_weight="700", color=TEXT_PRIMARY),
                align="center",
                spacing="2",
            )
        ),
        rx.table.cell(rx.badge(p["position"], color_scheme="amber", variant="outline", size="1")),
        rx.table.cell(rx.text(p["games"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["innings"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["po"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(p["a"], size="2", color=TEXT_PRIMARY, font_weight="600", text_align="center")),
        rx.table.cell(rx.text(p["e"], size="2", color="var(--red-9)", font_weight="700", text_align="center")),
        rx.table.cell(rx.text(p["tc"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
        rx.table.cell(rx.badge(p["fpct_str"], color_scheme="green", variant="soft", size="1")),
        rx.table.cell(rx.text(p["dp"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.table.cell(rx.text(p["rf9_str"], size="2", color=TEXT_MUTED, text_align="center")),
        rx.cond(
            IndividualesState.is_catcher_view,
            rx.table.cell(rx.text(p["cs"], size="2", color=ACCENT_GOLD, font_weight="700", text_align="center")),
            rx.fragment(),
        ),
        rx.cond(
            IndividualesState.is_catcher_view,
            rx.table.cell(rx.text(p["sb"], size="2", color=TEXT_MUTED, text_align="center")),
            rx.fragment(),
        ),
        rx.cond(
            IndividualesState.is_catcher_view,
            rx.table.cell(rx.badge(p["cs_pct_str"], color_scheme="amber", variant="solid", size="1")),
            rx.fragment(),
        ),
        _hover={"background": "rgba(253, 184, 39, 0.05)"},
    )


# ── Fila de Tabla H2H ────────────────────────────────────────────────────────
def h2h_comparison_row(item: Dict[str, Any]) -> rx.Component:
    """Fila de la tabla comparativa Head-to-Head."""
    return rx.table.row(
        rx.table.cell(rx.text(item["metric"], size="2", font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(rx.text(item["val_1"], size="2", font_weight="600", color="#FDB827", text_align="center")),
        rx.table.cell(rx.text(item["val_2"], size="2", font_weight="600", color="#38BDF8", text_align="center")),
        rx.table.cell(
            rx.badge(
                item["winner"],
                color_scheme=item["winner_scheme"],
                variant="soft",
                size="1",
            )
        ),
        _hover={"background": "rgba(255, 255, 255, 0.03)"},
    )


# ── Tarjeta de Perfil H2H ───────────────────────────────────────────────────
def player_profile_card(card: Dict[str, Any], border_color: str, tag_color: str) -> rx.Component:
    """Tarjeta visual de jugador en el comparador H2H."""
    return rx.box(
        rx.hstack(
            rx.image(
                src=card["headshot"],
                width="64px",
                height="64px",
                border_radius="50%",
                border=f"2px solid {border_color}",
                fallback="/logo.png",
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(card["name"], size="3", font_weight="800", color=TEXT_PRIMARY),
                    rx.badge(card["badge"], color_scheme=tag_color, variant="solid", size="1"),
                    align="center",
                    spacing="2",
                ),
                rx.text(f"{card['pos']} • {card['team']}", size="1", color=TEXT_MUTED),
                rx.hstack(
                    rx.badge(card["kpi_1"], color_scheme="amber", variant="soft", size="1"),
                    rx.badge(card["kpi_2"], color_scheme="blue", variant="soft", size="1"),
                    rx.badge(card["kpi_3"], color_scheme="green", variant="soft", size="1"),
                    spacing="1",
                ),
                spacing="1",
                align="start",
            ),
            align="center",
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        border=f"1px solid {border_color}",
        width="100%",
    )


# ── 1. VISTA DE BATEO ────────────────────────────────────────────────────────
def batting_tab_view() -> rx.Component:
    """Vista de estadísticas de bateo."""
    return rx.vstack(
        # Rejilla de KPIs Líderes
        rx.grid(
            individual_kpi_card("LÍDER AVG", IndividualesState.batting_kpis["avg_val"], IndividualesState.batting_kpis["avg_player"], "award"),
            individual_kpi_card("LÍDER JONRONES", IndividualesState.batting_kpis["hr_val"], IndividualesState.batting_kpis["hr_player"], "flame"),
            individual_kpi_card("LÍDER IMPULSADAS", IndividualesState.batting_kpis["rbi_val"], IndividualesState.batting_kpis["rbi_player"], "trending-up"),
            individual_kpi_card("LÍDER OPS", IndividualesState.batting_kpis["ops_val"], IndividualesState.batting_kpis["ops_player"], "zap"),
            individual_kpi_card("LÍDER wOBA", IndividualesState.batting_kpis["woba_val"], IndividualesState.batting_kpis["woba_player"], "target"),
            individual_kpi_card("LÍDER wRC+", IndividualesState.batting_kpis["wrc_val"], IndividualesState.batting_kpis["wrc_player"], "crown"),
            columns=rx.breakpoints(initial="2", md="3", lg="6"),
            spacing="3",
            width="100%",
        ),
        # Barra de Filtros
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("search", size=16, color=TEXT_MUTED),
                    rx.input(
                        placeholder="Buscar bateador...",
                        value=IndividualesState.search_batting,
                        on_change=IndividualesState.set_search_batting,
                        size="2",
                        variant="surface",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Mínimo AB:", size="2", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["0", "5", "10", "15", "20", "30", "50"],
                        value=str(IndividualesState.min_ab),
                        on_change=IndividualesState.set_min_ab,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Ordenar por:", size="2", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["ops", "avg", "hr", "rbi", "h", "woba", "wrc_plus", "sb"],
                        value=IndividualesState.sort_batting_by,
                        on_change=IndividualesState.set_sort_batting_by,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                align="center",
                spacing="4",
                wrap="wrap",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Tabla Sabermétrica de Bateo
        rx.box(
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Jugador"),
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
                            rx.table.column_header_cell("ISO"),
                            rx.table.column_header_cell("BABIP"),
                            rx.table.column_header_cell("wOBA"),
                            rx.table.column_header_cell("wRC+"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(IndividualesState.filtered_batting, batting_row),
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
        # Gráfico Top 10 OPS
        rx.box(
            rx.plotly(data=IndividualesState.top_batters_chart),
            style=CARD_STYLE,
            width="100%",
        ),
        # Glosario Desplegable
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text("📖 Glosario Sabermétrico: Métricas Ofensivas y de Bateo", font_weight="700", color=ACCENT_GOLD),
                content=rx.vstack(
                    rx.text("• AVG: Promedio de bateo tradicional (H / AB).", size="2", color=TEXT_MUTED),
                    rx.text("• OBP: Porcentaje de embasado (H + BB + HBP) / (AB + BB + HBP + SF).", size="2", color=TEXT_MUTED),
                    rx.text("• SLG: Promedio de bases alcanzadas por turno (Total Bases / AB).", size="2", color=TEXT_MUTED),
                    rx.text("• OPS: On-base Plus Slugging (OBP + SLG). Métrica reina de productividad ofensiva.", size="2", color=TEXT_MUTED),
                    rx.text("• ISO: Poder Aislado (SLG - AVG). Mide exclusivamente la fuerza de extrabases.", size="2", color=TEXT_MUTED),
                    rx.text("• wOBA: Weighted On-Base Average. Ponderación lineal exacta de cada evento ofensivo.", size="2", color=TEXT_MUTED),
                    rx.text("• wRC+: Weighted Runs Created Plus. Creación de carreras normalizada (100 = promedio de liga).", size="2", color=TEXT_MUTED),
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


# ── 2. VISTA DE PITCHEO ──────────────────────────────────────────────────────
def pitching_tab_view() -> rx.Component:
    """Vista de estadísticas de pitcheo."""
    return rx.vstack(
        # Rejilla de KPIs Líderes
        rx.grid(
            individual_kpi_card("MEJOR ERA", IndividualesState.pitching_kpis["era_val"], IndividualesState.pitching_kpis["era_player"], "shield"),
            individual_kpi_card("LÍDER PONCHES", IndividualesState.pitching_kpis["so_val"], IndividualesState.pitching_kpis["so_player"], "zap"),
            individual_kpi_card("MEJOR WHIP", IndividualesState.pitching_kpis["whip_val"], IndividualesState.pitching_kpis["whip_player"], "target"),
            individual_kpi_card("MEJOR FIP", IndividualesState.pitching_kpis["fip_val"], IndividualesState.pitching_kpis["fip_player"], "activity"),
            individual_kpi_card("LÍDER K/9", IndividualesState.pitching_kpis["k9_val"], IndividualesState.pitching_kpis["k9_player"], "flame"),
            individual_kpi_card("LÍDER SALVADOS", IndividualesState.pitching_kpis["sv_val"], IndividualesState.pitching_kpis["sv_player"], "lock"),
            columns=rx.breakpoints(initial="2", md="3", lg="6"),
            spacing="3",
            width="100%",
        ),
        # Barra de Filtros
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("search", size=16, color=TEXT_MUTED),
                    rx.input(
                        placeholder="Buscar lanzador...",
                        value=IndividualesState.search_pitching,
                        on_change=IndividualesState.set_search_pitching,
                        size="2",
                        variant="surface",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Rol:", size="2", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["Todos", "Abridor", "Relevista"],
                        value=IndividualesState.pitcher_role,
                        on_change=IndividualesState.set_pitcher_role,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Mínimo IP:", size="2", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["0.0", "1.0", "3.0", "5.0", "10.0", "15.0"],
                        value=str(IndividualesState.min_ip),
                        on_change=IndividualesState.set_min_ip,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Ordenar por:", size="2", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["era", "whip", "fip", "so", "ip", "k9", "sv"],
                        value=IndividualesState.sort_pitching_by,
                        on_change=IndividualesState.set_sort_pitching_by,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                align="center",
                spacing="4",
                wrap="wrap",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Tabla Sabermétrica de Pitcheo
        rx.box(
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Lanzador"),
                            rx.table.column_header_cell("JJ"),
                            rx.table.column_header_cell("JI"),
                            rx.table.column_header_cell("W-L"),
                            rx.table.column_header_cell("SV"),
                            rx.table.column_header_cell("IP"),
                            rx.table.column_header_cell("H"),
                            rx.table.column_header_cell("R"),
                            rx.table.column_header_cell("CL"),
                            rx.table.column_header_cell("BB"),
                            rx.table.column_header_cell("SO"),
                            rx.table.column_header_cell("HR"),
                            rx.table.column_header_cell("ERA"),
                            rx.table.column_header_cell("WHIP"),
                            rx.table.column_header_cell("FIP"),
                            rx.table.column_header_cell("K/9"),
                            rx.table.column_header_cell("BB/9"),
                            rx.table.column_header_cell("K/BB"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(IndividualesState.filtered_pitching, pitching_row),
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
        # Gráfico Top 10 Ponches
        rx.box(
            rx.plotly(data=IndividualesState.top_pitchers_chart),
            style=CARD_STYLE,
            width="100%",
        ),
        # Glosario Desplegable
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text("📖 Glosario Sabermétrico: Métricas de Pitcheo", font_weight="700", color=ACCENT_GOLD),
                content=rx.vstack(
                    rx.text("• ERA: Efectividad tradicional (CL * 9 / IP). Menor es mejor.", size="2", color=TEXT_MUTED),
                    rx.text("• WHIP: Embasados por entrada (H + BB) / IP. Mide el tráfico de corredores.", size="2", color=TEXT_MUTED),
                    rx.text("• FIP: Fielding Independent Pitching. Efectividad pura aislada de la defensa del campo.", size="2", color=TEXT_MUTED),
                    rx.text("• K/9: Frecuencia de ponches propinados cada 9 entradas lanzadas.", size="2", color=TEXT_MUTED),
                    rx.text("• BB/9: Tasa de boletos regalados cada 9 entradas.", size="2", color=TEXT_MUTED),
                    rx.text("• K/BB: Relación de ponches por cada base por bolas otorgada.", size="2", color=TEXT_MUTED),
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


# ── 3. VISTA DE FILDEO / DEFENSA ─────────────────────────────────────────────
def fielding_tab_view() -> rx.Component:
    """Vista de estadísticas defensivas y fildeo."""
    return rx.vstack(
        # Rejilla de KPIs Líderes
        rx.grid(
            individual_kpi_card("MEJOR % FILDEO", IndividualesState.fielding_kpis["fpct_val"], IndividualesState.fielding_kpis["fpct_player"], "shield-check"),
            individual_kpi_card("LÍDER ASISTENCIAS", IndividualesState.fielding_kpis["a_val"], IndividualesState.fielding_kpis["a_player"], "hand"),
            individual_kpi_card("LÍDER DOUBLE PLAYS", IndividualesState.fielding_kpis["dp_val"], IndividualesState.fielding_kpis["dp_player"], "shuffle"),
            individual_kpi_card("LÍDER OUTS REALIZADOS", IndividualesState.fielding_kpis["po_val"], IndividualesState.fielding_kpis["po_player"], "target"),
            individual_kpi_card("LÍDER ATRAPADOS (CS)", IndividualesState.fielding_kpis["cs_val"], IndividualesState.fielding_kpis["cs_player"], "lock"),
            columns=rx.breakpoints(initial="2", md="3", lg="5"),
            spacing="3",
            width="100%",
        ),
        # Barra de Filtros
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("search", size=16, color=TEXT_MUTED),
                    rx.input(
                        placeholder="Buscar defensor...",
                        value=IndividualesState.search_fielding,
                        on_change=IndividualesState.set_search_fielding,
                        size="2",
                        variant="surface",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Posición:", size="2", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["Todas", "C", "1B", "2B", "3B", "SS", "OF", "LF", "CF", "RF", "P"],
                        value=IndividualesState.selected_fielding_pos,
                        on_change=IndividualesState.set_selected_fielding_pos,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                align="center",
                spacing="4",
                wrap="wrap",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Tabla de Fildeo
        rx.box(
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Defensor"),
                            rx.table.column_header_cell("Pos"),
                            rx.table.column_header_cell("JJ"),
                            rx.table.column_header_cell("Inn"),
                            rx.table.column_header_cell("PO"),
                            rx.table.column_header_cell("A"),
                            rx.table.column_header_cell("E"),
                            rx.table.column_header_cell("TC"),
                            rx.table.column_header_cell("FPCT"),
                            rx.table.column_header_cell("DP"),
                            rx.table.column_header_cell("RF/9"),
                            rx.cond(IndividualesState.is_catcher_view, rx.table.column_header_cell("CS"), rx.fragment()),
                            rx.cond(IndividualesState.is_catcher_view, rx.table.column_header_cell("SB"), rx.fragment()),
                            rx.cond(IndividualesState.is_catcher_view, rx.table.column_header_cell("CS%"), rx.fragment()),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(IndividualesState.filtered_fielding, fielding_row),
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
        # Glosario Desplegable
        rx.accordion.root(
            rx.accordion.item(
                header=rx.text("📖 Glosario Sabermétrico: Métricas Defensivas y Fildeo", font_weight="700", color=ACCENT_GOLD),
                content=rx.vstack(
                    rx.text("• PO (Putouts): Outs completados directamente por el defensor.", size="2", color=TEXT_MUTED),
                    rx.text("• A (Assists): Pases o tiros completados que derivan en un out.", size="2", color=TEXT_MUTED),
                    rx.text("• E (Errors): Pifias defensivas cometidas.", size="2", color=TEXT_MUTED),
                    rx.text("• TC (Total Chances): Total de lances y oportunidades defensivas (PO + A + E).", size="2", color=TEXT_MUTED),
                    rx.text("• FPCT: Porcentaje de fildeo sin error (PO + A) / TC.", size="2", color=TEXT_MUTED),
                    rx.text("• RF/9: Factor de rango por cada 9 innings ((PO + A) * 9 / Inn). Mide cobertura de terreno.", size="2", color=TEXT_MUTED),
                    rx.text("• CS% (Caught Stealing Pct): Porcentaje de corredores puestos out en intento de robo por el receptor.", size="2", color=TEXT_MUTED),
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


# ── 4. VISTA COMPARADOR HEAD-TO-HEAD (H2H) ──────────────────────────────────
def comparator_tab_view() -> rx.Component:
    """Vista de comparación cara a cara entre jugadores con radar polar sabermétrico."""
    return rx.vstack(
        # Barra de Selección de Jugadores
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.text("Tipo:", size="2", font_weight="700", color=ACCENT_GOLD),
                    rx.select(
                        ["Bateadores", "Lanzadores"],
                        value=IndividualesState.compare_type,
                        on_change=IndividualesState.set_compare_type,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("Jugador 1:", size="2", font_weight="700", color="#FDB827"),
                    rx.select(
                        rx.cond(
                            IndividualesState.compare_type == "Bateadores",
                            IndividualesState.available_batters,
                            IndividualesState.available_pitchers,
                        ),
                        value=IndividualesState.selected_player_1,
                        on_change=IndividualesState.set_selected_player_1,
                        size="2",
                        variant="surface",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.text("VS", size="3", font_weight="900", color=TEXT_MUTED),
                rx.hstack(
                    rx.text("Jugador 2:", size="2", font_weight="700", color="#38BDF8"),
                    rx.select(
                        rx.cond(
                            IndividualesState.compare_type == "Bateadores",
                            IndividualesState.available_batters,
                            IndividualesState.available_pitchers,
                        ),
                        value=IndividualesState.selected_player_2,
                        on_change=IndividualesState.set_selected_player_2,
                        size="2",
                        variant="surface",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                align="center",
                spacing="4",
                wrap="wrap",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        # Tarjetas de Perfil H2H
        rx.grid(
            player_profile_card(IndividualesState.player_1_card, "#FDB827", "amber"),
            player_profile_card(IndividualesState.player_2_card, "#38BDF8", "blue"),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
        ),
        # Grilla Central: Radar Polar y Tabla Comparativa
        rx.grid(
            # Columna Izquierda: Radar Polar de 8 Ejes Sabermétricos
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("pie-chart", size=18, color=ACCENT_GOLD),
                        rx.heading("RADAR POLAR SABERMÉTRICO (PERCENTILES 0-100)", size="3", font_weight="800", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.plotly(data=IndividualesState.radar_chart_figure),
                    spacing="3",
                    width="100%",
                ),
                style=CARD_STYLE,
                width="100%",
            ),
            # Columna Derecha: Tabla Cara a Cara
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("swords", size=18, color=ACCENT_GOLD),
                        rx.heading("DESGLOSE MÉTRICA POR MÉTRICA", size="3", font_weight="800", color=TEXT_PRIMARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Categoría"),
                                    rx.table.column_header_cell("Jugador 1"),
                                    rx.table.column_header_cell("Jugador 2"),
                                    rx.table.column_header_cell("Líder"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(IndividualesState.h2h_rows, h2h_comparison_row),
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
            columns=rx.breakpoints(initial="1", lg="2"),
            spacing="4",
            width="100%",
        ),
        # Tarjeta de Veredicto Sabermétrico
        rx.box(
            rx.hstack(
                rx.icon("award", size=24, color=ACCENT_GOLD),
                rx.text(
                    IndividualesState.h2h_verdict,
                    size="3",
                    font_weight="700",
                    color=TEXT_PRIMARY,
                ),
                align="center",
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            border=f"1px solid {BORDER_GOLD}",
            background="rgba(253, 184, 39, 0.08)",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Contenido Principal de /individuales ──────────────────────────────────────
def individuales_content() -> rx.Component:
    """Cuerpo de la vista /individuales con pestañas de navegación."""
    return rx.vstack(
        # Selector de Pestañas
        rx.hstack(
            rx.button(
                rx.hstack(rx.icon("flame", size=16), rx.text("🏏 Bateo"), align="center", spacing="2"),
                on_click=IndividualesState.set_active_tab("bateo"),
                style=rx.cond(IndividualesState.active_tab == "bateo", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
            ),
            rx.button(
                rx.hstack(rx.icon("zap", size=16), rx.text("⚡ Pitcheo"), align="center", spacing="2"),
                on_click=IndividualesState.set_active_tab("pitcheo"),
                style=rx.cond(IndividualesState.active_tab == "pitcheo", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
            ),
            rx.button(
                rx.hstack(rx.icon("shield", size=16), rx.text("🧤 Fildeo / Defensa"), align="center", spacing="2"),
                on_click=IndividualesState.set_active_tab("fildeo"),
                style=rx.cond(IndividualesState.active_tab == "fildeo", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
            ),
            rx.button(
                rx.hstack(rx.icon("swords", size=16), rx.text("⚔️ Comparador H2H"), align="center", spacing="2"),
                on_click=IndividualesState.set_active_tab("comparador"),
                style=rx.cond(IndividualesState.active_tab == "comparador", BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE),
            ),
            spacing="3",
            wrap="wrap",
            width="100%",
            padding_y="0.5rem",
        ),
        # Vistas Condicionales
        rx.cond(
            IndividualesState.active_tab == "bateo",
            batting_tab_view(),
            rx.cond(
                IndividualesState.active_tab == "pitcheo",
                pitching_tab_view(),
                rx.cond(
                    IndividualesState.active_tab == "fildeo",
                    fielding_tab_view(),
                    comparator_tab_view(),
                ),
            ),
        ),
        spacing="5",
        width="100%",
    )


def individuales() -> rx.Component:
    """Página de Estadísticas Individuales de República Caraquista."""
    return layout(
        content=individuales_content(),
        page_title="ESTADÍSTICAS INDIVIDUALES & DEFENSIVAS",
        page_description="Líderes de bateo, pitcheo, rendimiento defensivo de fildeadores y comparador Head-to-Head sabermétrico.",
        current_route="/individuales",
    )
