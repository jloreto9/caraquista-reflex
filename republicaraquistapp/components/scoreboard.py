# republicaraquistapp/components/scoreboard.py
import reflex as rx
from republicaraquistapp.styles.theme import (
    CARD_STYLE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_MUTED, BORDER_CARD, BORDER_SUBTLE
)
from republicaraquistapp.state.base_state import AppState

def scoreboard_card() -> rx.Component:
    """Tarjeta de Último Juego de los Leones del Caracas (Totalmente Responsiva)."""
    return rx.box(
        rx.vstack(
            # Header de la tarjeta
            rx.hstack(
                rx.hstack(
                    rx.icon("activity", size=18, color=ACCENT_GOLD),
                    rx.heading(
                        "ÚLTIMO COMPROMISO",
                        size="3",
                        color=TEXT_PRIMARY,
                        font_weight="700",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.badge(
                    AppState.last_game_data["result_badge"],
                    color_scheme=AppState.last_game_data["result_color"],
                    variant="solid",
                    size="2",
                ),
                align="center",
                width="100%",
                padding_bottom="0.75rem",
                border_bottom=f"1px solid {BORDER_CARD}",
            ),
            
            # Enfrentamiento cara a cara
            rx.hstack(
                # Equipo Visitante
                rx.vstack(
                    rx.image(
                        src=AppState.last_game_data["away_logo"],
                        width=rx.breakpoints(initial="44px", sm="58px", md="64px"),
                        height=rx.breakpoints(initial="44px", sm="58px", md="64px"),
                        border_radius="8px",
                    ),
                    rx.text(
                        AppState.last_game_data["away_name"],
                        size="2",
                        font_weight="700",
                        color=TEXT_PRIMARY,
                        text_align="center",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space=rx.breakpoints(initial="normal", sm="nowrap"),
                        max_width=rx.breakpoints(initial="90px", sm="130px", md="180px"),
                    ),
                    align="center",
                    spacing="1",
                    flex="1",
                ),
                
                # Marcador central
                rx.vstack(
                    rx.heading(
                        AppState.last_game_data["score_str"],
                        size=rx.breakpoints(initial="6", sm="7", md="8"),
                        font_weight="900",
                        color=ACCENT_GOLD,
                        letter_spacing="0.05em",
                    ),
                    rx.text(AppState.last_game_data["date"], size="1", color=TEXT_MUTED),
                    rx.badge("Final", color_scheme="gray", variant="soft", size="1"),
                    align="center",
                    spacing="1",
                    flex="1",
                    padding_x="2",
                ),
                
                # Equipo Local
                rx.vstack(
                    rx.image(
                        src=AppState.last_game_data["home_logo"],
                        width=rx.breakpoints(initial="44px", sm="58px", md="64px"),
                        height=rx.breakpoints(initial="44px", sm="58px", md="64px"),
                        border_radius="8px",
                    ),
                    rx.text(
                        AppState.last_game_data["home_name"],
                        size="2",
                        font_weight="700",
                        color=TEXT_PRIMARY,
                        text_align="center",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space=rx.breakpoints(initial="normal", sm="nowrap"),
                        max_width=rx.breakpoints(initial="90px", sm="130px", md="180px"),
                    ),
                    align="center",
                    spacing="1",
                    flex="1",
                ),
                
                align="center",
                justify="center",
                width="100%",
                padding_y=rx.breakpoints(initial="0.5rem", sm="1rem"),
            ),
            
            spacing="3",
            width="100%",
        ),
        style=CARD_STYLE,
        width="100%",
    )
