# republicaraquistapp/pages/spray_charts.py
"""
spray_charts.py
---------------
Vista para la visualización de Spray Charts espaciales en diamante geométrico
con modelo BIS de dureza y análisis de Zona de Strike 3x3 con disciplina en el plato.
Ruta: /spray-charts
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
from republicaraquistapp.state.spray_state import SprayState
from republicaraquistapp.components.layout import layout


def spray_charts_tab() -> rx.Component:
    """Pestaña de Spray Charts en Diamante."""
    return rx.vstack(
        # 1. Filtros y Selectores de Bateador y Color Mode
        rx.box(
            rx.grid(
                rx.vstack(
                    rx.text("SELECCIONAR BATEADOR", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.select(
                        SprayState.spray_player_options,
                        value=SprayState.selected_spray_player,
                        on_change=SprayState.set_selected_spray_player,
                        size="3",
                        variant="soft",
                        color_scheme="amber",
                        width="100%",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text("COLOREAR BATAZOS POR", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.hstack(
                        rx.button(
                            "Por Evento",
                            variant=rx.cond(SprayState.spray_color_mode == "event", "solid", "outline"),
                            color_scheme="amber",
                            on_click=SprayState.set_spray_color_mode("event"),
                            size="2",
                        ),
                        rx.button(
                            "Por Trayectoria",
                            variant=rx.cond(SprayState.spray_color_mode == "trajectory", "solid", "outline"),
                            color_scheme="blue",
                            on_click=SprayState.set_spray_color_mode("trajectory"),
                            size="2",
                        ),
                        rx.button(
                            "Por Dureza (BIS)",
                            variant=rx.cond(SprayState.spray_color_mode == "hardness", "solid", "outline"),
                            color_scheme="red",
                            on_click=SprayState.set_spray_color_mode("hardness"),
                            size="2",
                        ),
                        spacing="2",
                        align="center",
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
        # 2. Rejilla de Métricas y Desgloses
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("TOTAL BATAZOS", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{SprayState.spray_total_batted}", size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text(f"Imparables: {SprayState.spray_total_hits}", size="1", color=ACCENT_GOLD),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("BABIP", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SprayState.spray_babip, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Pelotas en juego", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("DIRECCIÓN BATAZOS", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.hstack(
                        rx.badge(f"Pull: {SprayState.spray_pct_pull}", color_scheme="orange", size="1"),
                        rx.badge(f"Cent: {SprayState.spray_pct_center}", color_scheme="blue", size="1"),
                        rx.badge(f"Oppo: {SprayState.spray_pct_oppo}", color_scheme="green", size="1"),
                        spacing="1",
                    ),
                    rx.text("Distribución de campo", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("DUREZA DE CONTACTO (BIS)", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.hstack(
                        rx.badge(f"Hard: {SprayState.spray_pct_hard}", color_scheme="red", size="1"),
                        rx.badge(f"Med: {SprayState.spray_pct_medium}", color_scheme="amber", size="1"),
                        rx.badge(f"Soft: {SprayState.spray_pct_soft}", color_scheme="gray", size="1"),
                        spacing="1",
                    ),
                    rx.text("Calidad de impacto", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("TRAYECTORIA", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.hstack(
                        rx.badge(f"GB: {SprayState.spray_pct_gb}", color_scheme="green", size="1"),
                        rx.badge(f"LD: {SprayState.spray_pct_ld}", color_scheme="blue", size="1"),
                        rx.badge(f"FB: {SprayState.spray_pct_fb}", color_scheme="orange", size="1"),
                        rx.badge(f"PU: {SprayState.spray_pct_pu}", color_scheme="purple", size="1"),
                        spacing="1",
                    ),
                    rx.text("Ángulo de salida", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="5"),
            spacing="3",
            width="100%",
        ),
        # 3. Lienzo Espacial del Spray Chart
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("disc", size=18, color=ACCENT_GOLD),
                    rx.heading("DIAMANTE GEOMÉTRICO & DISPERSIÓN ESPACIAL", size="3", color=TEXT_PRIMARY),
                    rx.spacer(),
                    align="center",
                    width="100%",
                ),
                rx.plotly(data=SprayState.spray_chart_figure, height="680px", width="100%"),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def strike_zone_tab() -> rx.Component:
    """Pestaña de Disciplina en el Plato y Zona de Strike 3x3."""
    return rx.vstack(
        # 1. Filtros de Perspectiva y Jugador
        rx.box(
            rx.grid(
                rx.vstack(
                    rx.text("PERSPECTIVA DE ANÁLISIS", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.hstack(
                        rx.button(
                            "🦁 Bateadores de Leones",
                            variant=rx.cond(SprayState.sz_perspective == "Bateadores de Leones", "solid", "outline"),
                            color_scheme="amber",
                            on_click=SprayState.set_sz_perspective("Bateadores de Leones"),
                            size="2",
                        ),
                        rx.button(
                            "⚾ Lanzadores de Leones",
                            variant=rx.cond(SprayState.sz_perspective == "Lanzadores de Leones", "solid", "outline"),
                            color_scheme="blue",
                            on_click=SprayState.set_sz_perspective("Lanzadores de Leones"),
                            size="2",
                        ),
                        spacing="2",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text("SELECCIONAR JUGADOR", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.select(
                        SprayState.sz_player_options,
                        value=SprayState.selected_sz_player,
                        on_change=SprayState.set_selected_sz_player,
                        size="3",
                        variant="soft",
                        color_scheme="amber",
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
        # 2. Rejilla de 6 KPIs de Disciplina
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("TOTAL PITCHEOS", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(f"{SprayState.sz_total_pitches}", size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Muestra de lanzamientos", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("CSW%", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SprayState.sz_csw_pct, size="6", color=ACCENT_GOLD, font_weight="800"),
                    rx.text("Called Strike + Whiff", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("WHIFF RATE", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SprayState.sz_whiff_pct, size="6", color=LEONES_RED, font_weight="800"),
                    rx.text("Abanicados / Swings", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("O-SWING% (CHASE)", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SprayState.sz_o_swing_pct, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Swings fuera de zona", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("Z-SWING%", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SprayState.sz_z_swing_pct, size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Swings dentro de zona", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            rx.box(
                rx.vstack(
                    rx.text("Z-CONTACT%", size="1", font_weight="700", color=TEXT_MUTED),
                    rx.heading(SprayState.sz_z_contact_pct, size="6", color="#10b981", font_weight="800"),
                    rx.text("Contacto en zona de strike", size="1", color=TEXT_MUTED),
                    spacing="1",
                ),
                style=CARD_STYLE,
            ),
            columns=rx.breakpoints(initial="2", sm="3", lg="6"),
            spacing="3",
            width="100%",
        ),
        # 3. Lienzo de la Zona de Strike 3x3
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("crosshair", size=18, color=ACCENT_GOLD),
                    rx.heading("ZONA DE STRIKE 3X3 & LOCALIZACIÓN DE PITCHEOS", size="3", color=TEXT_PRIMARY),
                    rx.spacer(),
                    align="center",
                    width="100%",
                ),
                rx.plotly(data=SprayState.strike_zone_figure, height="620px", width="100%"),
                spacing="3",
                width="100%",
            ),
            style=CARD_STYLE,
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def spray_content() -> rx.Component:
    """Contenido principal de la página Spray Charts & Zonas."""
    return rx.vstack(
        # Tabs de Navegación del Módulo
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon("disc", size=16),
                    rx.text("Spray Charts en Diamante", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(SprayState.active_view == "spray", "solid", "outline"),
                color_scheme="amber",
                on_click=SprayState.set_active_view("spray"),
                size="2",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("crosshair", size=16),
                    rx.text("Disciplina & Zona de Strike 3x3", size="2", font_weight="700"),
                    spacing="2",
                    align="center",
                ),
                variant=rx.cond(SprayState.active_view == "strike_zone", "solid", "outline"),
                color_scheme="amber",
                on_click=SprayState.set_active_view("strike_zone"),
                size="2",
            ),
            spacing="3",
            padding_bottom="0.5rem",
        ),
        # Renderizado Condicional de la Vista
        rx.cond(
            SprayState.active_view == "spray",
            spray_charts_tab(),
            strike_zone_tab(),
        ),
        # Glosario & Metodología
        rx.accordion.root(
            rx.accordion.item(
                header=rx.hstack(
                    rx.icon("book-open", size=16, color=ACCENT_GOLD),
                    rx.text("Guía y Metodología: Modelo BIS de Dureza y Métricas de Disciplina", size="2", font_weight="700", color=TEXT_PRIMARY),
                    spacing="2",
                    align="center",
                ),
                content=rx.vstack(
                    rx.grid(
                        rx.box(
                            rx.text("💥 Modelo BIS de Dureza", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Clasifica los batazos determinísticamente en Hard, Medium y Soft combinando eventos clave (HRs, 3B, 2B), distancias calibradas y tipo de contacto.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("🎯 CSW% (Called Strikes + Whiffs)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Porcentaje de lanzamientos que resultan en strike cantado o abanicado. Es la métrica reina para evaluar dominio de pitcheo.", size="1", color=TEXT_MUTED),
                            padding="0.75rem",
                            background="rgba(255, 255, 255, 0.03)",
                            border_radius="8px",
                        ),
                        rx.box(
                            rx.text("👀 O-Swing% (Chase Rate)", size="2", font_weight="700", color=ACCENT_GOLD),
                            rx.text("Frecuencia con la que el bateador persigue pitcheos fuera de la zona de strike. Menor valor indica mayor disciplina.", size="1", color=TEXT_MUTED),
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
                value="spray_methodology",
            ),
            collapsible=True,
            variant="ghost",
            width="100%",
        ),
        spacing="5",
        width="100%",
    )


def spray_charts() -> rx.Component:
    """Vista principal de Spray Charts y Zonas de Strike en Reflex."""
    return layout(
        content=spray_content(),
        page_title="Spray Charts & Disciplina en el Plato",
        page_description="Mapas espaciales de dispersión de batazos en diamante con dureza BIS y matriz 3x3 de localización de pitcheos.",
        current_route="/spray-charts",
    )
