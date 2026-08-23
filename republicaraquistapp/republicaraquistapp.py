# republicaraquistapp/republicaraquistapp.py
import reflex as rx
from rxconfig import config
from republicaraquistapp.state.base_state import AppState
from republicaraquistapp.pages.index import index

app = rx.App(
    head_components=[
        rx.el.link(rel="icon", href="/logo.png"),
        rx.el.meta(name="theme-color", content="#070B19"),
    ]
)

app.add_page(
    index,
    route="/",
    title="República Caraquista • Analítica Sabermétrica LVBP",
    image="/logo.png",
    on_load=AppState.on_load
)
