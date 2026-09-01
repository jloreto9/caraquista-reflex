# republicaraquistapp/components/layout.py
"""
layout.py
---------
Marco de diseño estándar (Layout Frame) de República Caraquista.
Incluye barra de navegación, contenedor responsivo, indicador de carga asíncrona,
banner de manejo de errores y pie de página sabermétrico detallado.
"""

from typing import Optional
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
    CONTAINER_STYLE,
    PAGE_HEADER_STYLE,
    FOOTER_STYLE,
    GOLD_BADGE_STYLE,
    CARD_STYLE,
)
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.components.navbar import navbar, NAV_ITEMS


def footer() -> rx.Component:
    """Pie de página institucional y sabermétrico con navegación y créditos."""
    return rx.box(
        rx.vstack(
            rx.grid(
                # Columna 1: Branding y Propósito
                rx.vstack(
                    rx.hstack(
                        rx.image(
                            src="/logo.png",
                            width="38px",
                            height="38px",
                            border_radius="8px",
                            alt="Logo Caraquista",
                        ),
                        rx.vstack(
                            rx.heading(
                                "REPÚBLICA CARAQUISTA",
                                size="3",
                                color=TEXT_PRIMARY,
                                font_weight="800",
                            ),
                            rx.badge("LVBP SABERMETRICS", style=GOLD_BADGE_STYLE),
                            spacing="0",
                            align="start",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    rx.text(
                        "Plataforma analítica avanzada para el seguimiento científico y "
                        "sabermétrico de los Leones del Caracas y la LVBP. Algoritmos de "
                        "Win Expectancy (RE24 Tango), ELO Ratings, Monte Carlo y LOB Tracker.",
                        size="2",
                        color=TEXT_MUTED,
                        line_height="1.6",
                    ),
                    rx.hstack(
                        rx.link(
                            rx.button(
                                rx.icon("git-branch", size=14),
                                "Repositorio GitHub",
                                size="1",
                                variant="outline",
                                color_scheme="gray",
                            ),
                            href="https://github.com/jloreto9/caraquista-reflex",
                            is_external=True,
                        ),
                        rx.link(
                            rx.button(
                                rx.icon("globe", size=14),
                                "MLB Stats API",
                                size="1",
                                variant="soft",
                                color_scheme="gray",
                            ),
                            href="https://statsapi.mlb.com",
                            is_external=True,
                        ),
                        align="center",
                        spacing="2",
                    ),
                    spacing="3",
                    align="start",
                ),
                # Columna 2: Navegación Rápida
                rx.vstack(
                    rx.heading(
                        "MÓDULOS DE ANÁLISIS",
                        size="2",
                        color=ACCENT_GOLD,
                        font_weight="700",
                        letter_spacing="0.05em",
                    ),
                    rx.grid(
                        *[
                            rx.link(
                                rx.hstack(
                                    rx.icon(item["icon"], size=13, color=TEXT_MUTED),
                                    rx.text(item["label"], size="2", color=TEXT_MUTED),
                                    align="center",
                                    spacing="2",
                                    _hover={"color": ACCENT_GOLD},
                                ),
                                href=item["route"],
                                on_click=AppState.set_route(item["route"]),
                                text_decoration="none",
                            )
                            for item in NAV_ITEMS
                        ],
                        columns="2",
                        spacing="2",
                        width="100%",
                    ),
                    spacing="3",
                    align="start",
                ),
                # Columna 3: Arquitectura y Autor
                rx.vstack(
                    rx.heading(
                        "DESARROLLO & CRÉDITOS",
                        size="2",
                        color=ACCENT_GOLD,
                        font_weight="700",
                        letter_spacing="0.05em",
                    ),
                    rx.text(
                        "Diseñado e implementado por Jorge Leonardo Loreto • AI Data Scientist "
                        "& Especialista en Sabermetría Aplicada.",
                        size="2",
                        color=TEXT_MUTED,
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("layers", size=14, color=ACCENT_GOLD),
                            rx.text("Stack: Reflex, Next.js, FastAPI, Radix UI", size="1", color=TEXT_MUTED),
                            align="center",
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.icon("database", size=14, color=ACCENT_GOLD),
                            rx.text("Persistencia: Supabase PostgreSQL & MLB API", size="1", color=TEXT_MUTED),
                            align="center",
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.icon("cpu", size=14, color=ACCENT_GOLD),
                            rx.text("Modelos: Tango RE24, ELO 5k Monte Carlo, BIS Hardness", size="1", color=TEXT_MUTED),
                            align="center",
                            spacing="2",
                        ),
                        spacing="2",
                        align="start",
                    ),
                    spacing="3",
                    align="start",
                ),
                columns=rx.breakpoints(initial="1", md="2", lg="3"),
                spacing="6",
                width="100%",
                padding_bottom="2rem",
            ),
            # Barra Inferior de Copyright
            rx.divider(color=BORDER_CARD),
            rx.hstack(
                rx.text(
                    "© 2025-2026 República Caraquista. Todos los derechos reservados.",
                    size="1",
                    color=TEXT_DIM,
                ),
                rx.spacer(),
                rx.text(
                    "¡Caracas pa' todo el mundo! 🦁⚾",
                    size="1",
                    color=ACCENT_GOLD,
                    font_weight="600",
                ),
                width="100%",
                align="center",
                padding_top="1rem",
            ),
            spacing="3",
            width="100%",
            max_width="1440px",
            margin="0 auto",
            padding_x="1.5rem",
        ),
        style=FOOTER_STYLE,
    )


def layout(
    content: rx.Component,
    page_title: Optional[str] = None,
    page_description: Optional[str] = None,
    current_route: str = "/",
) -> rx.Component:
    """
    Marco de layout reutilizable para todas las páginas de la aplicación.
    
    Args:
        content: Componente que contiene el cuerpo principal de la vista.
        page_title: Título opcional para el encabezado de la página.
        page_description: Descripción o subtítulo explicativo de la página.
        current_route: Ruta actual para asegurar el active link.
    """
    return rx.box(
        # 1. Barra de Navegación Superior
        navbar(),
        
        # 2. Contenedor Central
        rx.box(
            rx.vstack(
                # Banner de Encabezado Opcional
                rx.cond(
                    page_title is not None,
                    rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.hstack(
                                    rx.box(
                                        width="4px",
                                        height="28px",
                                        background=ACCENT_GOLD,
                                        border_radius="2px",
                                    ),
                                    rx.heading(
                                        page_title,
                                        size="6",
                                        color=TEXT_PRIMARY,
                                        font_weight="800",
                                        letter_spacing="0.02em",
                                    ),
                                    align="center",
                                    spacing="3",
                                ),
                                rx.cond(
                                    page_description is not None,
                                    rx.text(
                                        page_description,
                                        size="2",
                                        color=TEXT_MUTED,
                                        padding_left="1rem",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="1",
                                align="start",
                            ),
                            rx.spacer(),
                            rx.badge(
                                f"Temporada {AppState.selected_season_str}",
                                style=GOLD_BADGE_STYLE,
                            ),
                            align="center",
                            width="100%",
                        ),
                        style=PAGE_HEADER_STYLE,
                    ),
                    rx.fragment(),
                ),
                
                # Banner de Manejo de Errores
                rx.cond(
                    AppState.has_error,
                    rx.callout(
                        AppState.error_message,
                        title=AppState.error_title,
                        icon="circle-alert",
                        color_scheme="red",
                        variant="soft",
                        size="2",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                
                # Indicador de Carga Asíncrona Global
                rx.cond(
                    AppState.is_loading,
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3", color="amber"),
                            rx.text(AppState.loading_text, size="2", color=TEXT_MUTED),
                            align="center",
                            spacing="3",
                            padding="3rem",
                        ),
                        width="100%",
                    ),
                    # Contenido de la Página
                    content,
                ),
                
                spacing="5",
                width="100%",
            ),
            style=CONTAINER_STYLE,
        ),
        
        # 3. Pie de Página
        footer(),
        
        background=BG_DARK,
        min_height="100vh",
        width="100%",
    )
