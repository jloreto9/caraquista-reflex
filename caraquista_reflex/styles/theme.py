# caraquista_reflex/styles/theme.py
import reflex as rx

# Paleta de Colores Oficial República Caraquista
BG_DARK = "#070B19"          # Dark Slate Navy profundo
CARD_BG = "#0D152B"          # Fondo de tarjeta con contraste
CARD_HOVER = "#121D3A"       # Hover en tarjeta
ACCENT_GOLD = "#FDB827"      # Oro Caraquista Oficial
GOLD_HOVER = "#FFC72C"       # Oro brillante
NAVY_PRIMARY = "#001D4A"     # Azul Caracas profundo
TEXT_PRIMARY = "#FFFFFF"     # Texto blanco brillante
TEXT_MUTED = "#94A3B8"       # Texto secundario gris slate
BORDER_SUBTLE = "rgba(253, 184, 39, 0.15)"
BORDER_CARD = "rgba(255, 255, 255, 0.08)"

# Estilos de Componentes Reusables
CARD_STYLE = {
    "background": CARD_BG,
    "border": f"1px solid {BORDER_CARD}",
    "border_radius": "16px",
    "padding": "1.5rem",
    "box_shadow": "0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
    "transition": "all 0.2s ease-in-out",
    "_hover": {
        "border": f"1px solid {BORDER_SUBTLE}",
        "box_shadow": "0 20px 30px -10px rgba(0, 0, 0, 0.6)",
    }
}

GOLD_BADGE_STYLE = {
    "background": "rgba(253, 184, 39, 0.12)",
    "color": ACCENT_GOLD,
    "border": f"1px solid rgba(253, 184, 39, 0.3)",
    "border_radius": "9999px",
    "font_weight": "600",
    "font_size": "0.75rem",
    "padding": "0.25rem 0.75rem",
}
