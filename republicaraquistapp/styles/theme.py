# republicaraquistapp/styles/theme.py
"""
theme.py
--------
Definición de la paleta oficial y estilos visuales de República Caraquista en Reflex.
Paleta: Dark Slate Navy (#070B19), Tarjetas Glassmorphism (#0D152B), Acentos Dorados (#FDB827),
Tipografía Inter/Geist y componentes Radix UI.
"""

import reflex as rx

# ── Paleta de Colores Oficial República Caraquista ───────────────────────────
BG_DARK = "#070B19"          # Dark Slate Navy profundo (Fondo de app)
CARD_BG = "#0D152B"          # Fondo de tarjeta con alto contraste
CARD_HOVER = "#121D3A"       # Hover de tarjeta
ACCENT_GOLD = "#FDB827"      # Oro Caraquista Oficial
LEONES_GOLD = "#FDB827"      # Alias Oro Caraquista
LEONES_RED = "#CE1141"       # Rojo Secundario Caraquista
GOLD_HOVER = "#FFC72C"       # Oro brillante
NAVY_PRIMARY = "#001D4A"     # Azul Caracas profundo
NAVY_SECONDARY = "#0A2558"   # Azul intermedio
TEXT_PRIMARY = "#FFFFFF"     # Texto blanco brillante
TEXT_MUTED = "#94A3B8"       # Texto secundario gris slate
TEXT_DIM = "#64748B"         # Texto atenuado

# ── Bordes y Separadores ───────────────────────────────────────────────────
BORDER_SUBTLE = "rgba(253, 184, 39, 0.15)"
BORDER_CARD = "rgba(255, 255, 255, 0.08)"
BORDER_GOLD = "rgba(253, 184, 39, 0.4)"
BORDER_ACTIVE = "#FDB827"
BORDER_NAVY = "rgba(0, 29, 74, 0.5)"

# ── Colores Semánticos ──────────────────────────────────────────────────────
SUCCESS_COLOR = "#10B981"    # Verde victorias / positivo
DANGER_COLOR = "#EF4444"     # Rojo derrotas / negativo
WARNING_COLOR = "#F59E0B"    # Ámbar alerta
INFO_COLOR = "#3B82F6"       # Azul informativo

# ── Estilos de Tarjetas y Paneles Glassmorphism ─────────────────────────────
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
    },
}

GLASS_PANEL_STYLE = {
    "background": "rgba(13, 21, 43, 0.75)",
    "backdrop_filter": "blur(16px)",
    "-webkit-backdrop-filter": "blur(16px)",
    "border": f"1px solid {BORDER_CARD}",
    "border_radius": "16px",
    "padding": "1.5rem",
    "box_shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
}

CARD_HEADER_STYLE = {
    "display": "flex",
    "align_items": "center",
    "justify_content": "space-between",
    "width": "100%",
    "padding_bottom": "0.75rem",
    "border_bottom": f"1px solid {BORDER_CARD}",
    "margin_bottom": "1rem",
}

# ── Estilos de la Barra de Navegación ──────────────────────────────────────
NAVBAR_STYLE = {
    "position": "sticky",
    "top": "0",
    "z_index": "50",
    "width": "100%",
    "padding_y": "0.75rem",
    "background": "rgba(7, 11, 25, 0.90)",
    "backdrop_filter": "blur(20px)",
    "-webkit-backdrop-filter": "blur(20px)",
    "border_bottom": f"1px solid {BORDER_CARD}",
}

NAV_LINK_STYLE = {
    "display": "inline-flex",
    "align_items": "center",
    "gap": "0.4rem",
    "padding": "0.45rem 0.75rem",
    "border_radius": "8px",
    "font_size": "0.825rem",
    "font_weight": "600",
    "color": TEXT_MUTED,
    "text_decoration": "none",
    "transition": "all 0.15s ease-in-out",
    "border": "1px solid transparent",
    "_hover": {
        "color": TEXT_PRIMARY,
        "background": "rgba(255, 255, 255, 0.06)",
        "border": f"1px solid {BORDER_CARD}",
        "text_decoration": "none",
    },
}

NAV_LINK_ACTIVE_STYLE = {
    "display": "inline-flex",
    "align_items": "center",
    "gap": "0.4rem",
    "padding": "0.45rem 0.75rem",
    "border_radius": "8px",
    "font_size": "0.825rem",
    "font_weight": "700",
    "color": ACCENT_GOLD,
    "background": "rgba(253, 184, 39, 0.12)",
    "border": f"1px solid {BORDER_GOLD}",
    "text_decoration": "none",
    "box_shadow": "0 0 12px rgba(253, 184, 39, 0.15)",
}

MOBILE_NAV_LINK_STYLE = {
    "display": "flex",
    "align_items": "center",
    "gap": "0.75rem",
    "padding": "0.75rem 1rem",
    "border_radius": "10px",
    "font_size": "0.95rem",
    "font_weight": "600",
    "color": TEXT_MUTED,
    "text_decoration": "none",
    "width": "100%",
    "transition": "all 0.15s ease-in-out",
    "border": "1px solid transparent",
    "_hover": {
        "color": TEXT_PRIMARY,
        "background": "rgba(255, 255, 255, 0.06)",
        "border": f"1px solid {BORDER_CARD}",
        "text_decoration": "none",
    },
}

MOBILE_NAV_LINK_ACTIVE_STYLE = {
    "display": "flex",
    "align_items": "center",
    "gap": "0.75rem",
    "padding": "0.75rem 1rem",
    "border_radius": "10px",
    "font_size": "0.95rem",
    "font_weight": "700",
    "color": ACCENT_GOLD,
    "background": "rgba(253, 184, 39, 0.14)",
    "border": f"1px solid {BORDER_GOLD}",
    "text_decoration": "none",
    "width": "100%",
    "box_shadow": "0 0 15px rgba(253, 184, 39, 0.2)",
}

# ── Estilos de Badges Radix Reusables ───────────────────────────────────────
GOLD_BADGE_STYLE = {
    "background": "rgba(253, 184, 39, 0.12)",
    "color": ACCENT_GOLD,
    "border": f"1px solid rgba(253, 184, 39, 0.3)",
    "border_radius": "9999px",
    "font_weight": "600",
    "font_size": "0.75rem",
    "padding": "0.25rem 0.75rem",
}

NAVY_BADGE_STYLE = {
    "background": "rgba(0, 29, 74, 0.35)",
    "color": "#93C5FD",
    "border": "1px solid rgba(59, 130, 246, 0.3)",
    "border_radius": "9999px",
    "font_weight": "600",
    "font_size": "0.75rem",
    "padding": "0.25rem 0.75rem",
}

SUCCESS_BADGE_STYLE = {
    "background": "rgba(16, 185, 129, 0.12)",
    "color": SUCCESS_COLOR,
    "border": "1px solid rgba(16, 185, 129, 0.3)",
    "border_radius": "9999px",
    "font_weight": "600",
    "font_size": "0.75rem",
    "padding": "0.25rem 0.75rem",
}

DANGER_BADGE_STYLE = {
    "background": "rgba(239, 68, 68, 0.12)",
    "color": DANGER_COLOR,
    "border": "1px solid rgba(239, 68, 68, 0.3)",
    "border_radius": "9999px",
    "font_weight": "600",
    "font_size": "0.75rem",
    "padding": "0.25rem 0.75rem",
}

MUTED_BADGE_STYLE = {
    "background": "rgba(255, 255, 255, 0.05)",
    "color": TEXT_MUTED,
    "border": f"1px solid {BORDER_CARD}",
    "border_radius": "9999px",
    "font_weight": "500",
    "font_size": "0.75rem",
    "padding": "0.25rem 0.75rem",
}

# ── Estilos de Botones ───────────────────────────────────────────────────────
BUTTON_PRIMARY_STYLE = {
    "background": ACCENT_GOLD,
    "color": "#070B19",
    "font_weight": "700",
    "font_size": "0.875rem",
    "border_radius": "10px",
    "padding": "0.6rem 1.25rem",
    "transition": "all 0.2s ease-in-out",
    "cursor": "pointer",
    "_hover": {
        "background": GOLD_HOVER,
        "box_shadow": "0 0 15px rgba(253, 184, 39, 0.4)",
    },
}

BUTTON_SECONDARY_STYLE = {
    "background": "rgba(255, 255, 255, 0.05)",
    "color": TEXT_PRIMARY,
    "font_weight": "600",
    "font_size": "0.875rem",
    "border_radius": "10px",
    "padding": "0.6rem 1.25rem",
    "border": f"1px solid {BORDER_CARD}",
    "transition": "all 0.2s ease-in-out",
    "cursor": "pointer",
    "_hover": {
        "background": "rgba(255, 255, 255, 0.1)",
        "border": f"1px solid {BORDER_SUBTLE}",
    },
}

# ── Estilos de Layout y Contenedor ──────────────────────────────────────────
CONTAINER_STYLE = {
    "width": "100%",
    "max_width": "1440px",
    "margin": "0 auto",
    "padding": "1.5rem",
    "min_height": "calc(100vh - 80px)",
}

PAGE_HEADER_STYLE = {
    "width": "100%",
    "padding_y": "1.25rem",
    "border_bottom": f"1px solid {BORDER_CARD}",
    "margin_bottom": "1.5rem",
}

FOOTER_STYLE = {
    "width": "100%",
    "background": "rgba(7, 11, 25, 0.95)",
    "border_top": f"1px solid {BORDER_CARD}",
    "padding_y": "2.5rem",
    "margin_top": "3rem",
}

DRAWER_CONTENT_STYLE = {
    "background": BG_DARK,
    "border_left": f"1px solid {BORDER_CARD}",
    "padding": "1.5rem",
    "height": "100%",
    "box_shadow": "-10px 0 30px rgba(0, 0, 0, 0.7)",
}
