# republicaraquistapp/pages/pitching.py
"""
pitching.py
-----------
9ª Vista de la aplicación web República Caraquista en Reflex.
Implementa el Pitching Summary estilo Thomas Nestico con:
1. Buscador centrado estilo Google / Baseball Reference en estado inicial.
2. Cabecera con avatar oficial de MLB, boxscore en pastillas KPIs y controles.
3. Conmutador de ramas: "MLB / MiLB (Statcast)" vs "Leones del Caracas (LVBP)".
4. Tablas sabermétricas (Repertorio Hawk-Eye o Destinos PBP).
5. Triple panel gráfico interactivo Plotly (Movimiento IVB vs HB, Strike Zone,
   Carga por entrada, Leverage Index y Splits Platoon).
6. Botón de descarga de tarjeta gráfica panorámica en alta resolución (PNG a 300 DPI).
"""

from typing import Dict, Any
import reflex as rx

from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    CARD_HOVER,
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
    CONTAINER_STYLE,
    PAGE_HEADER_STYLE,
)
from republicaraquistapp.components.layout import layout
from republicaraquistapp.state.pitching_state import PitchingState


# ── 1. Estado Inicial: Buscador Centrado ──────────────────────────────────────

def landing_search_view() -> rx.Component:
    """Pantalla inicial limpia con buscador centrado estilo Baseball Reference."""
    return rx.center(
        rx.vstack(
            rx.image(
                src="/logo.png",
                width="96px",
                height="96px",
                border_radius="16px",
                box_shadow="0 0 30px rgba(253, 184, 39, 0.25)",
                alt="República Caraquista",
            ),
            rx.heading(
                "PITCHING SUMMARY & STATCAST",
                size="7",
                color=TEXT_PRIMARY,
                font_weight="900",
                letter_spacing="-0.02em",
                text_align="center",
            ),
            rx.text(
                "Telemetría Hawk-Eye (IVB, HB, Spin, Velo, CSW%) para MLB/MiLB y analítica Play-by-Play "
                "adaptada para Leones del Caracas y la LVBP.",
                size="3",
                color=TEXT_MUTED,
                text_align="center",
                max_width="600px",
            ),
            rx.hstack(
                rx.text("Marco metodológico inspirado en el trabajo de", size="2", color=TEXT_DIM),
                rx.link(
                    rx.text("Thomas Nestico (@TJStats)", size="2", font_weight="700", color=ACCENT_GOLD),
                    href="https://github.com/tnestico/pitching_summary",
                    is_external=True,
                ),
                align="center",
                spacing="1",
            ),
            # Caja de búsqueda principal
            rx.box(
                rx.hstack(
                    rx.icon("search", size=20, color=ACCENT_GOLD),
                    rx.input(
                        placeholder="Buscar lanzador por nombre (ej: Albert Suárez, Erick Leal, Tarik Skubal...)",
                        value=PitchingState.search_query,
                        on_change=PitchingState.set_search_query,
                        variant="soft",
                        size="3",
                        color_scheme="amber",
                        width="100%",
                        style={
                            "background": "transparent",
                            "color": TEXT_PRIMARY,
                            "border": "none",
                            "outline": "none",
                        },
                    ),
                    rx.cond(
                        PitchingState.is_searching,
                        rx.spinner(size="2", color=ACCENT_GOLD),
                        rx.button(
                            "Buscar",
                            size="2",
                            style=BUTTON_PRIMARY_STYLE,
                            on_click=PitchingState.perform_search,
                        ),
                    ),
                    align="center",
                    padding="0.8rem 1.2rem",
                    width="100%",
                ),
                style={
                    "background": CARD_BG,
                    "border": f"1px solid {BORDER_GOLD}",
                    "border_radius": "16px",
                    "box_shadow": "0 10px 30px rgba(0, 0, 0, 0.5)",
                    "width": "100%",
                    "max_width": "680px",
                },
                margin_top="1.5rem",
                width="100%",
            ),
            # Resultados de Búsqueda Desplegables
            rx.cond(
                PitchingState.search_results.length() > 0,
                rx.vstack(
                    rx.foreach(
                        PitchingState.search_results,
                        search_result_item,
                    ),
                    spacing="2",
                    width="100%",
                    max_width="680px",
                    margin_top="1rem",
                    max_height="400px",
                    overflow_y="auto",
                ),
            ),
            spacing="4",
            align="center",
            width="100%",
            padding_y="4rem",
        ),
        width="100%",
        min_height="70vh",
    )


def search_result_item(p: Dict[str, Any]) -> rx.Component:
    """Fila individual de resultado de búsqueda."""
    return rx.box(
        rx.hstack(
            rx.image(
                src=p["photo_url"],
                width="42px",
                height="42px",
                border_radius="50%",
                border=f"2px solid {ACCENT_GOLD}",
                fallback="/favicon.ico",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(p["name"], size="3", font_weight="700", color=TEXT_PRIMARY),
                    rx.cond(
                        p["has_caracas_history"],
                        rx.badge("🦁 LEONES DEL CARACAS", style=GOLD_BADGE_STYLE, size="1"),
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.text(
                    f"{p['team']} • Lanza: {p['throws']}HP • {p['position']}",
                    size="1",
                    color=TEXT_MUTED,
                ),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.button(
                "Ver Resumen",
                size="1",
                style=BUTTON_SECONDARY_STYLE,
                on_click=PitchingState.select_pitcher_by_id(p["id"]),
            ),
            align="center",
            width="100%",
            padding="0.6rem 1rem",
        ),
        style={
            "background": CARD_BG,
            "border": f"1px solid {BORDER_CARD}",
            "border_radius": "10px",
            "transition": "all 0.15s ease",
            "cursor": "pointer",
            "_hover": {"background": CARD_HOVER, "border_color": ACCENT_GOLD},
        },
        width="100%",
        on_click=PitchingState.select_pitcher_by_id(p["id"]),
    )


# ── 2. Barra Superior y Controles de la Vista Activa ──────────────────────────

def controls_bar() -> rx.Component:
    """Barra de navegación secundaria con selectores de juego, temporada y bifurcación."""
    return rx.box(
        rx.hstack(
            # Botón Volver
            rx.button(
                rx.icon("arrow-left", size=16),
                "Buscar Otro",
                size="2",
                variant="outline",
                color_scheme="gray",
                on_click=PitchingState.clear_selection,
            ),
            rx.divider(orientation="vertical", size="2"),
            # Bifurcación: MLB vs LVBP
            rx.hstack(
                rx.button(
                    "⚾ MLB / MiLB (Statcast)",
                    size="2",
                    variant=rx.cond(PitchingState.active_branch == "mlb", "solid", "outline"),
                    color_scheme=rx.cond(PitchingState.active_branch == "mlb", "amber", "gray"),
                    on_click=PitchingState.set_active_branch("mlb"),
                ),
                rx.button(
                    "🦁 Leones del Caracas (LVBP)",
                    size="2",
                    variant=rx.cond(PitchingState.active_branch == "lvbp", "solid", "outline"),
                    color_scheme=rx.cond(PitchingState.active_branch == "lvbp", "amber", "gray"),
                    disabled=~PitchingState.has_caracas_history,
                    on_click=PitchingState.set_active_branch("lvbp"),
                ),
                spacing="2",
            ),
            rx.spacer(),
            # Selectores de Temporada y Salida
            rx.hstack(
                rx.select(
                    ["2025", "2024", "2023", "2022"],
                    value=PitchingState.pitcher_season,
                    on_change=PitchingState.set_pitcher_season,
                    size="2",
                    color_scheme="amber",
                ),
                rx.select(
                    PitchingState.game_log_options,
                    value=PitchingState.selected_game_label,
                    placeholder="Seleccionar Salida",
                    on_change=PitchingState.set_selected_game_by_label,
                    size="2",
                    color_scheme="amber",
                    max_width="300px",
                ),
                # Botón de Descarga HD PNG
                rx.button(
                    rx.icon("download", size=16),
                    "Descargar Tarjeta HD",
                    size="2",
                    style=BUTTON_PRIMARY_STYLE,
                    loading=PitchingState.is_generating_card,
                    on_click=PitchingState.download_pitching_card,
                ),
                spacing="3",
                align="center",
            ),
            align="center",
            width="100%",
            wrap="wrap",
        ),
        style=CARD_STYLE,
        width="100%",
        padding="0.8rem 1.2rem",
    )


# ── 3. Perfil y Boxscore Banner ───────────────────────────────────────────────

def pitcher_header_banner() -> rx.Component:
    """Banner estilizado con foto oficial, nombre, fecha, rival y pastillas de boxscore."""
    p = PitchingState.selected_pitcher
    g = PitchingState.current_game_summary
    k = PitchingState.pbp_kpis

    return rx.box(
        rx.vstack(
            rx.hstack(
                # Headshot circular oficial
                rx.image(
                    src=p["photo_url"],
                    width="72px",
                    height="72px",
                    border_radius="50%",
                    border=f"3px solid {ACCENT_GOLD}",
                    box_shadow="0 0 20px rgba(253, 184, 39, 0.3)",
                    fallback="/favicon.ico",
                ),
                # Nombre y datos
                rx.vstack(
                    rx.hstack(
                        rx.heading(p["name"], size="6", font_weight="800", color=TEXT_PRIMARY),
                        rx.cond(
                            PitchingState.active_branch == "lvbp",
                            rx.badge("LVBP • LEONES DEL CARACAS", style=GOLD_BADGE_STYLE),
                            rx.badge("STATCAST HAWK-EYE", color_scheme="blue"),
                        ),
                        rx.badge("Inspirado en @TJStats", variant="surface", color_scheme="gray", size="1"),
                        align="center",
                        spacing="2",
                    ),
                    rx.text(
                        f"Lanza: {p['throws']}HP  |  {g['role']}  |  vs {g['opponent']}  |  Fecha: {g['date']}",
                        size="2",
                        color=TEXT_MUTED,
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                align="center",
                width="100%",
            ),
            # Grilla de Boxscore KPIs
            rx.grid(
                kpi_pill("IP", g["ip"].to_string()),
                kpi_pill("H", g["h"].to_string()),
                kpi_pill("R", g["r"].to_string()),
                kpi_pill("ER", g["er"].to_string()),
                kpi_pill("BB", g["bb"].to_string()),
                kpi_pill("K", g["so"].to_string(), highlight=True),
                kpi_pill("PITCHES", g["pitches"].to_string()),
                kpi_pill("CSW%", k["csw_pct"].to_string(), highlight=True),
                kpi_pill("WHIFF%", k["whiff_pct"].to_string(), highlight=True),
                columns="9",
                spacing="2",
                width="100%",
                margin_top="0.5rem",
            ),
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def kpi_pill(label: str, val: str, highlight: bool = False) -> rx.Component:
    """Pastilla compacta para cada estadística del boxscore."""
    return rx.box(
        rx.vstack(
            rx.text(val, size="4", font_weight="800", color=ACCENT_GOLD if highlight else TEXT_PRIMARY),
            rx.text(label, size="1", font_weight="700", color=TEXT_MUTED),
            spacing="0",
            align="center",
        ),
        style={
            "background": "rgba(20, 31, 62, 0.7)",
            "border": f"1px solid {BORDER_CARD}",
            "border_radius": "8px",
            "padding": "0.4rem 0.6rem",
            "text_align": "center",
        },
        width="100%",
    )


# ── 4. Tabla de Repertorio Statcast ───────────────────────────────────────────

def statcast_repertoire_table() -> rx.Component:
    """Tabla de repertorio y métricas ópticas Hawk-Eye."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("activity", size=18, color=ACCENT_GOLD),
                rx.heading("REPERTORIO & TELEMETRÍA DE PITCHEOS (HAWK-EYE)", size="3", color=TEXT_PRIMARY),
                rx.spacer(),
                align="center",
                width="100%",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("TIPO DE PITCHEO"),
                        rx.table.column_header_cell("CANT"),
                        rx.table.column_header_cell("USO %"),
                        rx.table.column_header_cell("VELO AVG"),
                        rx.table.column_header_cell("VELO MAX"),
                        rx.table.column_header_cell("SPIN (RPM)"),
                        rx.table.column_header_cell("IVB (IN)"),
                        rx.table.column_header_cell("HB (IN)"),
                        rx.table.column_header_cell("WHIFF %"),
                        rx.table.column_header_cell("CSW %"),
                        rx.table.column_header_cell("ZONE %"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        PitchingState.statcast_table,
                        statcast_row,
                    )
                ),
                width="100%",
                variant="surface",
            ),
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def statcast_row(row: Dict[str, Any]) -> rx.Component:
    """Fila de la tabla de repertorio Statcast."""
    return rx.table.row(
        rx.table.cell(rx.text(row["pitch_name"], font_weight="700", color=TEXT_PRIMARY)),
        rx.table.cell(row["count"]),
        rx.table.cell(rx.text(row["usage_pct"], font_weight="600", color=TEXT_PRIMARY)),
        rx.table.cell(f"{row['velo_avg']} mph"),
        rx.table.cell(f"{row['velo_max']} mph"),
        rx.table.cell(row["spin_avg"]),
        rx.table.cell(rx.text(f"{row['ivb']}\"", color=ACCENT_GOLD)),
        rx.table.cell(f"{row['hb']}\""),
        rx.table.cell(rx.text(row["whiff_pct"], font_weight="700", color=ACCENT_GOLD)),
        rx.table.cell(rx.text(row["csw_pct"], font_weight="700", color=ACCENT_GOLD)),
        rx.table.cell(row["zone_pct"]),
        style={"_hover": {"background": "rgba(255, 255, 255, 0.03)"}},
    )


# ── 5. Tabla de Destinos Play-by-Play (LVBP) ──────────────────────────────────

def pbp_outcomes_table() -> rx.Component:
    """Tabla de resultados y destinos de pitcheos para LVBP."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("target", size=18, color=ACCENT_GOLD),
                rx.heading("DESTINOS Y RESULTADOS DE PITCHEOS (PLAY-BY-PLAY SABERMÉTRICO)", size="3", color=TEXT_PRIMARY),
                rx.spacer(),
                align="center",
                width="100%",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("DESTINO DEL PITCHEO"),
                        rx.table.column_header_cell("TOTAL CONTEO"),
                        rx.table.column_header_cell("DISTRIBUCIÓN %"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        PitchingState.pbp_table,
                        lambda r: rx.table.row(
                            rx.table.cell(rx.text(r["destination"], font_weight="700", color=TEXT_PRIMARY)),
                            rx.table.cell(r["count"]),
                            rx.table.cell(rx.text(r["pct"], font_weight="700", color=ACCENT_GOLD)),
                            style={"_hover": {"background": "rgba(255, 255, 255, 0.03)"}},
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )


# ── 6. Vistas Gráficas Plotly (Triple Panel) ──────────────────────────────────

def mlb_statcast_visual_panel() -> rx.Component:
    """Panel triple para MLB/MiLB: Movimiento (IVB vs HB), Strike Zone y Carga."""
    return rx.grid(
        rx.box(
            rx.plotly(data=PitchingState.fig_movement, style={"width": "100%", "height": "420px"}),
            style=CARD_STYLE,
        ),
        rx.box(
            rx.plotly(data=PitchingState.fig_strike_zone, style={"width": "100%", "height": "420px"}),
            style=CARD_STYLE,
        ),
        rx.box(
            rx.plotly(data=PitchingState.fig_workload, style={"width": "100%", "height": "420px"}),
            style=CARD_STYLE,
        ),
        columns="3",
        spacing="3",
        width="100%",
    )


def lvbp_adapted_visual_panel() -> rx.Component:
    """Panel triple adaptado para Leones del Caracas: Carga por entrada, Leverage Index y Splits Platoon."""
    return rx.grid(
        rx.box(
            rx.plotly(data=PitchingState.fig_workload, style={"width": "100%", "height": "420px"}),
            style=CARD_STYLE,
        ),
        rx.box(
            rx.plotly(data=PitchingState.fig_leverage, style={"width": "100%", "height": "420px"}),
            style=CARD_STYLE,
        ),
        rx.box(
            rx.plotly(data=PitchingState.fig_splits, style={"width": "100%", "height": "420px"}),
            style=CARD_STYLE,
        ),
        columns="3",
        spacing="3",
        width="100%",
    )


# ── 7. Página Principal /pitching ─────────────────────────────────────────────

def pitching_content() -> rx.Component:
    """Contenido dinámico que conmuta entre buscador inicial y dashboard del lanzador."""
    return rx.cond(
        ~PitchingState.has_pitcher_selected,
        landing_search_view(),
        rx.vstack(
            controls_bar(),
            pitcher_header_banner(),
            # Bifurcación de Tablas
            rx.cond(
                (PitchingState.active_branch == "mlb") & (PitchingState.statcast_table.length() > 0),
                statcast_repertoire_table(),
                pbp_outcomes_table(),
            ),
            # Bifurcación de Gráficos
            rx.cond(
                (PitchingState.active_branch == "mlb") & (PitchingState.statcast_table.length() > 0),
                mlb_statcast_visual_panel(),
                lvbp_adapted_visual_panel(),
            ),
            spacing="4",
            width="100%",
        ),
    )


def pitching() -> rx.Component:
    """Página completa integrada con el Layout de República Caraquista."""
    return layout(pitching_content())
