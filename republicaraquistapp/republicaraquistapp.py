# republicaraquistapp/republicaraquistapp.py
"""
republicaraquistapp.py
----------------------
Punto de entrada principal de la aplicación República Caraquista en Reflex.
Registra las 8 rutas de la Single Page Application (SPA) con sus respectivos
títulos, favicons y manejadores reactivos on_load.
"""

import reflex as rx
from rxconfig import config

# Estados Reactivos
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.state.standings_state import StandingsState
from republicaraquistapp.state.individuales_state import IndividualesState
from republicaraquistapp.state.colectivas_state import ColectivasState
from republicaraquistapp.state.wpa_state import WpaState
from republicaraquistapp.state.situacional_state import SituationalState
from republicaraquistapp.state.spray_state import SprayState
from republicaraquistapp.state.bullpen_state import BullpenState

# Páginas SPA
from republicaraquistapp.pages.index import index
from republicaraquistapp.pages.standings import standings
from republicaraquistapp.pages.individuales import individuales
from republicaraquistapp.pages.colectivas import colectivas
from republicaraquistapp.pages.wpa import wpa
from republicaraquistapp.pages.situacional import situacional
from republicaraquistapp.pages.spray_charts import spray_charts
from republicaraquistapp.pages.bullpen import bullpen

# Instancia Global de la Aplicación Reflex
app = rx.App(
    head_components=[
        rx.el.link(rel="icon", href="/logo.png"),
        rx.el.meta(name="theme-color", content="#070B19"),
    ]
)

# ── 1. Ruta / (Dashboard Ejecutivo) ─────────────────────────────────────────
app.add_page(
    index,
    route="/",
    title="República Caraquista • Analítica Sabermétrica LVBP",
    image="/logo.png",
    on_load=StandingsState.on_load
)

# ── 2. Ruta /standings (Posiciones & ELO) ────────────────────────────────────
app.add_page(
    standings,
    route="/standings",
    title="Posiciones, Sabermetría & Ratings ELO • República Caraquista",
    image="/logo.png",
    on_load=StandingsState.on_load
)

# ── 3. Ruta /individuales (Individuales & Fildeo) ────────────────────────────
app.add_page(
    individuales,
    route="/individuales",
    title="Estadísticas Individuales & Defensivas • República Caraquista",
    image="/logo.png",
    on_load=IndividualesState.on_load
)

# ── 4. Ruta /colectivas (Colectivas 8 Equipos) ──────────────────────────────
app.add_page(
    colectivas,
    route="/colectivas",
    title="Estadísticas Colectivas LVBP • República Caraquista",
    image="/logo.png",
    on_load=ColectivasState.on_load
)

# ── 5. Ruta /wpa (Win Expectancy & WPA) ─────────────────────────────────────
app.add_page(
    wpa,
    route="/wpa",
    title="Win Expectancy & Análisis WPA • República Caraquista",
    image="/logo.png",
    on_load=WpaState.on_load_wpa
)

# ── 6. Ruta /situacional (Situacional & LOB) ────────────────────────────────
app.add_page(
    situacional,
    route="/situacional",
    title="Desempeño Situacional & LOB Tracker • República Caraquista",
    image="/logo.png",
    on_load=SituationalState.on_load_situacional
)

# ── 7. Ruta /spray-charts (Spray Charts & Zonas) ────────────────────────────
app.add_page(
    spray_charts,
    route="/spray-charts",
    title="Spray Charts & Disciplina en el Plato • República Caraquista",
    image="/logo.png",
    on_load=SprayState.on_load_spray
)

# ── 8. Ruta /bullpen (Bullpen & Lineups) ────────────────────────────────────
app.add_page(
    bullpen,
    route="/bullpen",
    title="Bullpen & Tracker de Alineaciones • República Caraquista",
    image="/logo.png",
    on_load=BullpenState.on_load_bullpen
)
