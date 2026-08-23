# republicaraquistapp/pages/index.py
import reflex as rx
from republicaraquistapp.styles.theme import (
    BG_DARK, ACCENT_GOLD, TEXT_PRIMARY, TEXT_MUTED, BORDER_CARD, CARD_STYLE
)
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.components.navbar import navbar
from republicaraquistapp.components.kpi_grid import kpi_grid
from republicaraquistapp.components.scoreboard import scoreboard_card
from republicaraquistapp.components.standings_table import standings_table

def recent_game_item(game: dict) -> rx.Component:
    """Elemento individual de la lista de juegos recientes."""
    return rx.hstack(
        rx.text(game["date"], size="1", color=TEXT_MUTED, width="80px"),
        rx.hstack(
            rx.image(src=game["away_logo"], width="22px", height="22px"),
            rx.text(game["away_name"], size="2", color=TEXT_PRIMARY),
            align="center",
            spacing="1",
            flex="1"
        ),
        rx.text(game["score_str"], size="2", font_weight="800", color=ACCENT_GOLD, width="60px", text_align="center"),
        rx.hstack(
            rx.image(src=game["home_logo"], width="22px", height="22px"),
            rx.text(game["home_name"], size="2", color=TEXT_PRIMARY),
            align="center",
            spacing="1",
            flex="1"
        ),
        rx.badge(
            game["result_badge"],
            color_scheme=game["result_color"],
            variant="soft",
            size="1"
        ),
        align="center",
        width="100%",
        padding_y="0.5rem",
        border_bottom=f"1px solid {BORDER_CARD}"
    )

def index() -> rx.Component:
    """Dashboard Principal de República Caraquista en Reflex."""
    return rx.box(
        # Barra de Navegación
        navbar(),
        
        # Contenido Principal
        rx.vstack(
            # Banner de Bienvenida / Identidad
            rx.hstack(
                rx.vstack(
                    rx.heading("DASHBOARD SABERMÉTRICO OFICIAL", size="6", color=TEXT_PRIMARY, font_weight="800"),
                    rx.text("Seguimiento analítico en tiempo real, probabilidades y métricas de última generación para los Leones del Caracas.", size="2", color=TEXT_MUTED),
                    spacing="1"
                ),
                rx.spacer(),
                align="center",
                width="100%",
                padding_y="1rem"
            ),
            
            # Rejilla de KPIs Principales
            kpi_grid(),
            
            # Grilla Principal de 2 Columnas
            rx.grid(
                # Columna Izquierda: Scoreboard y Juegos Recientes
                rx.vstack(
                    scoreboard_card(),
                    
                    # Tarjeta de Historial Reciente
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("calendar-days", size=18, color=ACCENT_GOLD),
                                rx.heading("ÚLTIMOS RESULTADOS", size="3", color=TEXT_PRIMARY, font_weight="700"),
                                rx.spacer(),
                                rx.badge("Últimos 5", color_scheme="gray", variant="soft", size="1"),
                                align="center",
                                width="100%",
                                padding_bottom="0.75rem",
                                border_bottom=f"1px solid {BORDER_CARD}"
                            ),
                            rx.foreach(AppState.recent_games_data, recent_game_item),
                            spacing="2",
                            width="100%"
                        ),
                        style=CARD_STYLE,
                        width="100%"
                    ),
                    spacing="4",
                    width="100%"
                ),
                
                # Columna Derecha: Tabla de Posiciones
                rx.vstack(
                    standings_table(),
                    spacing="4",
                    width="100%"
                ),
                
                columns=rx.breakpoints(initial="1", lg="2"),
                spacing="5",
                width="100%"
            ),
            
            # Footer
            rx.vstack(
                rx.divider(color=BORDER_CARD),
                rx.hstack(
                    rx.text("Desarrollado por Jorge Leonardo Loreto • Científico de Datos & Analista Sabermétrico", size="1", color=TEXT_MUTED),
                    rx.spacer(),
                    rx.text("Powered by Reflex, FastAPI & Supabase", size="1", color=TEXT_MUTED),
                    width="100%",
                    align="center",
                    padding_y="1.5rem"
                ),
                width="100%",
                spacing="2"
            ),
            
            spacing="5",
            width="100%",
            max_width="1400px",
            margin="0 auto",
            padding="1.5rem"
        ),
        
        background=BG_DARK,
        min_height="100vh",
        width="100%"
    )
