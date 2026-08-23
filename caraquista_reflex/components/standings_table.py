# caraquista_reflex/components/standings_table.py
import reflex as rx
from caraquista_reflex.styles.theme import (
    CARD_STYLE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_MUTED, BORDER_CARD
)
from caraquista_reflex.state.base_state import AppState

def standings_row(team: dict) -> rx.Component:
    """Fila de la tabla de posiciones con estilo condicional para Leones."""
    return rx.table.row(
        # Posición
        rx.table.cell(
            rx.text(team["pos"].to_string() + "°", font_weight="700", color=team["text_color"])
        ),
        # Equipo con Logo Oficial
        rx.table.cell(
            rx.hstack(
                rx.image(src=team["logo"], width="28px", height="28px"),
                rx.text(team["team_name"], font_weight="700", color=team["text_color"]),
                align="center",
                spacing="2"
            )
        ),
        # JJ
        rx.table.cell(rx.text(team["games"], color=TEXT_PRIMARY, text_align="center")),
        # G
        rx.table.cell(rx.text(team["wins"], font_weight="700", color="var(--green-9)", text_align="center")),
        # P
        rx.table.cell(rx.text(team["losses"], font_weight="700", color="var(--red-9)", text_align="center")),
        # PCT
        rx.table.cell(rx.text(team["pct"], font_weight="700", color=team["text_color"], text_align="center")),
        # GB (DIF)
        rx.table.cell(rx.text(team["gb"], color=TEXT_MUTED, text_align="center")),
        # Racha
        rx.table.cell(
            rx.badge(
                team["streak"],
                color_scheme=team["streak_color"],
                variant="soft",
                size="1"
            )
        ),
        # L10
        rx.table.cell(rx.text(team["l10"], color=TEXT_MUTED, text_align="center")),
        # Dif Carreras
        rx.table.cell(
            rx.text(
                team["diff"],
                font_weight="700",
                color=team["diff_color"],
                text_align="center"
            )
        ),
        background=team["row_bg"],
        border_left=team["row_border"]
    )

def standings_table() -> rx.Component:
    """Tabla completa de posiciones de la LVBP."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("table", size=18, color=ACCENT_GOLD),
                rx.heading("TABLA DE POSICIONES OFICIAL", size="3", color=TEXT_PRIMARY, font_weight="700"),
                rx.spacer(),
                rx.badge("Ronda Regular", color_scheme="amber", variant="soft", size="1"),
                align="center",
                width="100%",
                padding_bottom="0.75rem",
                border_bottom=f"1px solid {BORDER_CARD}"
            ),
            
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("POS"),
                        rx.table.column_header_cell("EQUIPO"),
                        rx.table.column_header_cell("JJ"),
                        rx.table.column_header_cell("G"),
                        rx.table.column_header_cell("P"),
                        rx.table.column_header_cell("PCT"),
                        rx.table.column_header_cell("DIF"),
                        rx.table.column_header_cell("RACHA"),
                        rx.table.column_header_cell("L10"),
                        rx.table.column_header_cell("DIF. C"),
                    )
                ),
                rx.table.body(
                    rx.foreach(AppState.standings_data, standings_row)
                ),
                variant="surface",
                size="2",
                width="100%"
            ),
            spacing="3",
            width="100%"
        ),
        style=CARD_STYLE,
        width="100%"
    )
