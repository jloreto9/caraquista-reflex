# caraquista_reflex/components/navbar.py
import reflex as rx
from caraquista_reflex.styles.theme import (
    BG_DARK, CARD_BG, ACCENT_GOLD, TEXT_PRIMARY, TEXT_MUTED, BORDER_CARD, GOLD_BADGE_STYLE
)
from caraquista_reflex.state.base_state import AppState

def navbar() -> rx.Component:
    """Barra de navegación principal con look premium glassmorphism."""
    return rx.box(
        rx.hstack(
            # Logo y Título
            rx.hstack(
                rx.image(
                    src="/logo.png",
                    width="44px",
                    height="44px",
                    border_radius="10px",
                    alt="República Caraquista Logo"
                ),
                rx.vstack(
                    rx.hstack(
                        rx.heading("REPÚBLICA CARAQUISTA", size="4", color=TEXT_PRIMARY, font_weight="800", letter_spacing="0.05em"),
                        rx.badge("LVBP SABERMETRICS", style=GOLD_BADGE_STYLE),
                        align="center",
                        spacing="2"
                    ),
                    rx.text("Plataforma de Analítica Avanzada • Leones del Caracas", size="1", color=TEXT_MUTED),
                    spacing="0"
                ),
                align="center",
                spacing="3"
            ),
            
            rx.spacer(),
            
            # Selector de Temporada y Enlaces
            rx.hstack(
                rx.hstack(
                    rx.icon("calendar", size=16, color=ACCENT_GOLD),
                    rx.select(
                        ["2025-2026", "2024-2025"],
                        value=AppState.selected_season.to_string() + "-" + (AppState.selected_season + 1).to_string(),
                        on_change=AppState.set_season,
                        size="2",
                        variant="soft",
                        color_scheme="amber"
                    ),
                    align="center",
                    spacing="2",
                    padding_x="3",
                    padding_y="1",
                    background="rgba(255, 255, 255, 0.05)",
                    border_radius="8px",
                    border=f"1px solid {BORDER_CARD}"
                ),
                rx.link(
                    rx.button(
                        rx.icon("github", size=16),
                        "GitHub",
                        size="2",
                        variant="outline",
                        color_scheme="gray"
                    ),
                    href="https://github.com/jloreto9/caraquista-reflex",
                    is_external=True
                ),
                align="center",
                spacing="3"
            ),
            
            justify="between",
            align="center",
            width="100%",
            max_width="1400px",
            margin="0 auto",
            padding_x="1.5rem"
        ),
        position="sticky",
        top="0",
        z_index="50",
        width="100%",
        padding_y="0.85rem",
        background="rgba(7, 11, 25, 0.85)",
        backdrop_filter="blur(16px)",
        border_bottom=f"1px solid {BORDER_CARD}"
    )
