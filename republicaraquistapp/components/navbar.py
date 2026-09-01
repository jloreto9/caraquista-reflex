# republicaraquistapp/components/navbar.py
"""
navbar.py
---------
Barra de navegación responsiva para República Caraquista con soporte para las 8 rutas SPA,
resaltado de ruta activa, selector de temporada, branding oficial y menú drawer para móviles.
"""

from typing import Dict, Any, List
import reflex as rx

from republicaraquistapp.styles.theme import (
    BG_DARK,
    CARD_BG,
    CARD_HOVER,
    ACCENT_GOLD,
    GOLD_HOVER,
    NAVY_PRIMARY,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_DIM,
    BORDER_CARD,
    BORDER_SUBTLE,
    BORDER_GOLD,
    NAVBAR_STYLE,
    NAV_LINK_STYLE,
    NAV_LINK_ACTIVE_STYLE,
    MOBILE_NAV_LINK_STYLE,
    MOBILE_NAV_LINK_ACTIVE_STYLE,
    GOLD_BADGE_STYLE,
    DRAWER_CONTENT_STYLE,
)
from republicaraquistapp.state.base_state import AppState

# ── Definición Canónica de las 8 Rutas SPA ──────────────────────────────────
NAV_ITEMS: List[Dict[str, str]] = [
    {
        "route": "/",
        "label": "Dashboard",
        "icon": "layout-dashboard",
        "desc": "Resumen Ejecutivo y Scoreboard",
    },
    {
        "route": "/standings",
        "label": "Posiciones & ELO",
        "icon": "trophy",
        "desc": "Standings, xW y Simulación 5k",
    },
    {
        "route": "/individuales",
        "label": "Individuales & Fildeo",
        "icon": "user-check",
        "desc": "Líderes, Fildeo y Comparador H2H",
    },
    {
        "route": "/colectivas",
        "label": "Colectivas LVBP",
        "icon": "bar-chart-3",
        "desc": "Métricas 8 Equipos LVBP",
    },
    {
        "route": "/wpa",
        "label": "Win Expectancy & WPA",
        "icon": "trending-up",
        "desc": "Tango RE24, LI y Clutch",
    },
    {
        "route": "/situacional",
        "label": "Situacional & LOB",
        "icon": "target",
        "desc": "Splits RISP y LOB Tracker",
    },
    {
        "route": "/spray-charts",
        "label": "Spray Charts & Zonas",
        "icon": "disc",
        "desc": "BIS Diamond y Strike Zone",
    },
    {
        "route": "/bullpen",
        "label": "Bullpen & Lineups",
        "icon": "shield",
        "desc": "Relevo IR/IRS% y Órdenes 1-9",
    },
]


def nav_link_desktop(item: Dict[str, str]) -> rx.Component:
    """Enlace de navegación para desktop con resaltado condicional de ruta activa."""
    route = item["route"]
    label = item["label"]
    icon_name = item["icon"]

    return rx.cond(
        AppState.current_route == route,
        rx.link(
            rx.hstack(
                rx.icon(icon_name, size=15, color=ACCENT_GOLD),
                rx.text(label, size="2", font_weight="700", color=ACCENT_GOLD),
                align="center",
                spacing="2",
            ),
            href=route,
            on_click=AppState.set_route(route),
            style=NAV_LINK_ACTIVE_STYLE,
        ),
        rx.link(
            rx.hstack(
                rx.icon(icon_name, size=15, color=TEXT_MUTED),
                rx.text(label, size="2", font_weight="600", color=TEXT_MUTED),
                align="center",
                spacing="2",
            ),
            href=route,
            on_click=AppState.set_route(route),
            style=NAV_LINK_STYLE,
        ),
    )


def nav_link_mobile(item: Dict[str, str]) -> rx.Component:
    """Enlace de navegación para el drawer móvil con descripción y estado activo."""
    route = item["route"]
    label = item["label"]
    icon_name = item["icon"]
    desc = item["desc"]

    return rx.cond(
        AppState.current_route == route,
        rx.link(
            rx.hstack(
                rx.box(
                    rx.icon(icon_name, size=20, color=ACCENT_GOLD),
                    padding="8px",
                    border_radius="8px",
                    background="rgba(253, 184, 39, 0.15)",
                ),
                rx.vstack(
                    rx.text(label, size="2", font_weight="700", color=ACCENT_GOLD),
                    rx.text(desc, size="1", color=TEXT_MUTED),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.badge("Activo", color_scheme="amber", variant="solid", size="1"),
                align="center",
                spacing="3",
                width="100%",
            ),
            href=route,
            on_click=AppState.set_route(route),
            style=MOBILE_NAV_LINK_ACTIVE_STYLE,
        ),
        rx.link(
            rx.hstack(
                rx.box(
                    rx.icon(icon_name, size=20, color=TEXT_MUTED),
                    padding="8px",
                    border_radius="8px",
                    background="rgba(255, 255, 255, 0.04)",
                ),
                rx.vstack(
                    rx.text(label, size="2", font_weight="600", color=TEXT_PRIMARY),
                    rx.text(desc, size="1", color=TEXT_MUTED),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.icon("chevron-right", size=16, color=TEXT_DIM),
                align="center",
                spacing="3",
                width="100%",
            ),
            href=route,
            on_click=AppState.set_route(route),
            style=MOBILE_NAV_LINK_STYLE,
        ),
    )


def mobile_drawer() -> rx.Component:
    """Drawer móvil lateral con todas las opciones de navegación y configuración."""
    return rx.drawer.root(
        rx.drawer.trigger(
            rx.button(
                rx.icon("menu", size=20, color=ACCENT_GOLD),
                variant="ghost",
                size="2",
                padding="8px",
                border_radius="8px",
                border=f"1px solid {BORDER_CARD}",
                background="rgba(255, 255, 255, 0.04)",
                _hover={"background": "rgba(253, 184, 39, 0.12)"},
            )
        ),
        rx.drawer.overlay(background="rgba(0, 0, 0, 0.7)"),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    # Header del Drawer
                    rx.hstack(
                        rx.hstack(
                            rx.image(
                                src="/logo.png",
                                width="36px",
                                height="36px",
                                border_radius="8px",
                                alt="Logo",
                            ),
                            rx.vstack(
                                rx.text(
                                    "REPÚBLICA CARAQUISTA",
                                    size="2",
                                    font_weight="800",
                                    color=TEXT_PRIMARY,
                                ),
                                rx.text("Menú de Navegación", size="1", color=TEXT_MUTED),
                                spacing="0",
                            ),
                            align="center",
                            spacing="2",
                        ),
                        rx.spacer(),
                        rx.drawer.close(
                            rx.button(
                                rx.icon("x", size=18),
                                variant="ghost",
                                size="1",
                                color_scheme="gray",
                            )
                        ),
                        align="center",
                        width="100%",
                        padding_bottom="1rem",
                        border_bottom=f"1px solid {BORDER_CARD}",
                    ),
                    # Selector de Temporada en Móvil
                    rx.vstack(
                        rx.text(
                            "TEMPORADA LVBP",
                            size="1",
                            font_weight="700",
                            color=TEXT_MUTED,
                            letter_spacing="0.05em",
                        ),
                        rx.select(
                            AppState.season_options,
                            value=AppState.selected_season_str,
                            on_change=AppState.set_season,
                            size="2",
                            variant="soft",
                            color_scheme="amber",
                            width="100%",
                        ),
                        width="100%",
                        padding_y="0.75rem",
                        border_bottom=f"1px solid {BORDER_CARD}",
                    ),
                    # Lista de Rutas
                    rx.vstack(
                        rx.text(
                            "SECCIONES DE LA PLATAFORMA",
                            size="1",
                            font_weight="700",
                            color=TEXT_MUTED,
                            letter_spacing="0.05em",
                        ),
                        rx.vstack(
                            *[nav_link_mobile(item) for item in NAV_ITEMS],
                            spacing="2",
                            width="100%",
                        ),
                        width="100%",
                        spacing="2",
                        padding_y="0.5rem",
                        overflow_y="auto",
                        max_height="55vh",
                    ),
                    rx.spacer(),
                    # Footer del Drawer
                    rx.vstack(
                        rx.divider(color=BORDER_CARD),
                        rx.hstack(
                            rx.link(
                                rx.button(
                                    rx.icon("git-branch", size=14),
                                    "GitHub Repo",
                                    size="1",
                                    variant="outline",
                                    color_scheme="gray",
                                    width="100%",
                                ),
                                href="https://github.com/jloreto9/caraquista-reflex",
                                is_external=True,
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.text(
                            "Leones del Caracas Sabermetrics • v2.0",
                            size="1",
                            color=TEXT_DIM,
                            text_align="center",
                            width="100%",
                        ),
                        width="100%",
                        spacing="2",
                        padding_top="0.5rem",
                    ),
                    spacing="3",
                    height="100%",
                    width="100%",
                ),
                style=DRAWER_CONTENT_STYLE,
                width="340px",
            )
        ),
        direction="right",
    )


def navbar() -> rx.Component:
    """Barra de navegación principal con look premium glassmorphism."""
    return rx.box(
        rx.hstack(
            # ── 1. Branding: Logo, Título y Badge ─────────────────────────
            rx.link(
                rx.hstack(
                    rx.image(
                        src="/logo.png",
                        width="42px",
                        height="42px",
                        border_radius="10px",
                        alt="República Caraquista Logo",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.heading(
                                "REPÚBLICA CARAQUISTA",
                                size="3",
                                color=TEXT_PRIMARY,
                                font_weight="800",
                                letter_spacing="0.05em",
                            ),
                            rx.badge("LVBP SABERMETRICS", style=GOLD_BADGE_STYLE),
                            align="center",
                            spacing="2",
                        ),
                        rx.text(
                            "Plataforma de Analítica Avanzada • Leones del Caracas",
                            size="1",
                            color=TEXT_MUTED,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    align="center",
                    spacing="3",
                ),
                href="/",
                on_click=AppState.set_route("/"),
                text_decoration="none",
            ),
            rx.spacer(),
            # ── 2. Enlaces Desktop (Ocultos en Móvil) ────────────────────
            rx.box(
                rx.hstack(
                    *[nav_link_desktop(item) for item in NAV_ITEMS],
                    spacing="1",
                    align="center",
                ),
                display=rx.breakpoints(initial="none", xl="flex"),
            ),
            rx.spacer(),
            # ── 3. Selector de Temporada y Utilidades ────────────────────
            rx.hstack(
                # Selector de Temporada
                rx.hstack(
                    rx.icon("calendar", size=15, color=ACCENT_GOLD),
                    rx.select(
                        AppState.season_options,
                        value=AppState.selected_season_str,
                        on_change=AppState.set_season,
                        size="2",
                        variant="soft",
                        color_scheme="amber",
                    ),
                    align="center",
                    spacing="2",
                    padding_x="2.5",
                    padding_y="1",
                    background="rgba(255, 255, 255, 0.05)",
                    border_radius="8px",
                    border=f"1px solid {BORDER_CARD}",
                ),
                # Botón GitHub
                rx.box(
                    rx.link(
                        rx.button(
                            rx.icon("git-branch", size=15),
                            "GitHub",
                            size="2",
                            variant="outline",
                            color_scheme="gray",
                        ),
                        href="https://github.com/jloreto9/caraquista-reflex",
                        is_external=True,
                    ),
                    display=rx.breakpoints(initial="none", sm="block"),
                ),
                # Drawer Móvil (Visible en Mobile/Tablet)
                rx.box(
                    mobile_drawer(),
                    display=rx.breakpoints(initial="block", xl="none"),
                ),
                align="center",
                spacing="3",
            ),
            justify="between",
            align="center",
            width="100%",
            max_width="1440px",
            margin="0 auto",
            padding_x="1.5rem",
        ),
        style=NAVBAR_STYLE,
    )
