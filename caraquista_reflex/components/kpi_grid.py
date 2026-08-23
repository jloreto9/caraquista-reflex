# caraquista_reflex/components/kpi_grid.py
import reflex as rx
from caraquista_reflex.styles.theme import (
    CARD_STYLE, ACCENT_GOLD, TEXT_PRIMARY, TEXT_MUTED, BORDER_SUBTLE
)
from caraquista_reflex.state.base_state import AppState

def kpi_card(title: str, value: str, subtitle: str, icon_name: str, badge_text: str = None) -> rx.Component:
    """Tarjeta KPI moderna con acento caraquista."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(title, size="2", color=TEXT_MUTED, font_weight="600"),
                    rx.cond(
                        badge_text is not None,
                        rx.badge(badge_text, color_scheme="amber", variant="soft", size="1"),
                        rx.fragment()
                    ),
                    align="center",
                    spacing="2"
                ),
                rx.heading(value, size="7", color=TEXT_PRIMARY, font_weight="800"),
                rx.text(subtitle, size="1", color=TEXT_MUTED),
                spacing="1",
                align="start"
            ),
            rx.spacer(),
            rx.box(
                rx.icon(icon_name, size=26, color=ACCENT_GOLD),
                padding="12px",
                border_radius="12px",
                background="rgba(253, 184, 39, 0.1)",
                border=f"1px solid {BORDER_SUBTLE}"
            ),
            align="center",
            width="100%"
        ),
        style=CARD_STYLE,
        width="100%"
    )

def kpi_grid() -> rx.Component:
    """Rejilla de KPIs principales del Caracas."""
    return rx.grid(
        kpi_card(
            title="POSICIÓN TABLA",
            value=AppState.leones_kpis["posicion"],
            subtitle="Ronda Regular LVBP",
            icon_name="trophy"
        ),
        kpi_card(
            title="RÉCORD W - L",
            value=AppState.leones_kpis["record"],
            subtitle=f"PCT: {AppState.leones_kpis['pct']}",
            icon_name="chart-bar"
        ),
        kpi_card(
            title="RACHA ACTUAL",
            value=AppState.leones_kpis["streak"],
            subtitle="Tendencia inmediata",
            icon_name="flame"
        ),
        kpi_card(
            title="ÚLTIMOS 10 (L10)",
            value=AppState.leones_kpis["l10"],
            subtitle="Desempeño reciente",
            icon_name="history"
        ),
        kpi_card(
            title="DIF. CARRERAS",
            value=AppState.leones_kpis["run_diff"],
            subtitle="Balance Anotadas / Recibidas",
            icon_name="scale"
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="5"),
        spacing="4",
        width="100%"
    )
