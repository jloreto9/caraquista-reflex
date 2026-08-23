# utils/teams.py
"""
teams.py
--------
Mapeo oficial de los 8 equipos de la Liga Venezolana de Béisbol Profesional (LVBP).
Incluye IDs oficiales de MLB Stats API, abreviaciones, colores y URLs de logos oficiales
transparentes desde el CDN oficial de MLB (midfield.mlbstatic.com).
"""

from typing import Dict, Optional, Any

# ── IDs Oficiales de MLB Stats API (League ID = 135) ───────────────────────────
LVBP_TEAMS: Dict[int, str] = {
    695: "Leones del Caracas",
    696: "Navegantes del Magallanes",
    698: "Tiburones de La Guaira",
    699: "Tigres de Aragua",
    693: "Cardenales de Lara",
    692: "Águilas del Zulia",
    694: "Caribes de Anzoátegui",
    697: "Bravos de Margarita",
}

# ── Abreviaturas Oficiales ──────────────────────────────────────────────────
LVBP_ABBR: Dict[int, str] = {
    695: "CAR",
    696: "MAG",
    698: "LAG",
    699: "ARA",
    693: "LAR",
    692: "ZUL",
    694: "ORI",
    697: "MAR",
}

# ── Colores Primarios y Secundarios ─────────────────────────────────────────
LVBP_COLORS: Dict[int, Dict[str, str]] = {
    695: {"primary": "#002D62", "secondary": "#FDB827", "text": "#FFFFFF"},  # Leones: Azul Marino / Oro
    696: {"primary": "#003876", "secondary": "#FFC72C", "text": "#FFFFFF"},  # Magallanes: Azul / Amarillo
    698: {"primary": "#002B49", "secondary": "#D8252C", "text": "#FFFFFF"},  # Tiburones: Azul / Rojo
    699: {"primary": "#0C2340", "secondary": "#E31837", "text": "#FFFFFF"},  # Tigres: Marino / Rojo
    693: {"primary": "#BA0C2F", "secondary": "#000000", "text": "#FFFFFF"},  # Cardenales: Rojo / Negro
    692: {"primary": "#E05A10", "secondary": "#000000", "text": "#FFFFFF"},  # Águilas: Naranja / Negro
    694: {"primary": "#002D62", "secondary": "#FF6720", "text": "#FFFFFF"},  # Caribes: Azul / Naranja
    697: {"primary": "#41748D", "secondary": "#000000", "text": "#FFFFFF"},  # Bravos: Turquesa / Negro
}

# ── Mapeo de búsqueda por texto / aliases ───────────────────────────────────
_TEAM_TEXT_SEARCH: Dict[str, int] = {
    # Leones
    "695": 695, "leones": 695, "caracas": 695, "leones del caracas": 695, "car": 695, "leo": 695,
    # Magallanes
    "696": 696, "magallanes": 696, "navegantes": 696, "navegantes del magallanes": 696, "mag": 696, "nav": 696,
    # Tiburones
    "698": 698, "tiburones": 698, "la guaira": 698, "tiburones de la guaira": 698, "lag": 698, "tib": 698, "gua": 698,
    # Tigres
    "699": 699, "tigres": 699, "aragua": 699, "tigres de aragua": 699, "ara": 699, "tig": 699,
    # Cardenales
    "693": 693, "cardenales": 693, "lara": 693, "cardenales de lara": 693, "lar": 693,
    # Águilas
    "692": 692, "aguilas": 692, "águilas": 692, "zulia": 692, "aguilas del zulia": 692, "águilas del zulia": 692, "zul": 692, "agu": 692,
    # Caribes
    "694": 694, "caribes": 694, "anzoategui": 694, "anzoátegui": 694, "caribes de anzoategui": 694, "caribes de anzoátegui": 694, "ori": 694, "crb": 694, "anz": 694,
    # Bravos
    "697": 697, "bravos": 697, "margarita": 697, "bravos de margarita": 697, "mar": 697, "bra": 697,
}

# ── URL Base Oficial MLB Spots ──────────────────────────────────────────────
_MLB_SPOT_BASE = "https://midfield.mlbstatic.com/v1/team"


def resolve_team_id(team_identifier: Any) -> Optional[int]:
    """Resuelve cualquier ID, nombre o abreviación al ID oficial de MLB del equipo."""
    if team_identifier is None:
        return None
    try:
        if isinstance(team_identifier, (int, float)) and int(team_identifier) in LVBP_TEAMS:
            return int(team_identifier)
    except (ValueError, TypeError):
        pass

    s = str(team_identifier).strip().lower()
    if s in _TEAM_TEXT_SEARCH:
        return _TEAM_TEXT_SEARCH[s]

    for key, tid in _TEAM_TEXT_SEARCH.items():
        if key in s or s in key:
            return tid

    return None


def get_team_logo(team_identifier: Any, size: int = 144) -> str:
    """
    Retorna la URL oficial del logo del equipo en el CDN de MLB.
    Tamaños soportados: 72, 96, 120, 144, 240.
    """
    tid = resolve_team_id(team_identifier)
    if tid and tid in LVBP_TEAMS:
        return f"{_MLB_SPOT_BASE}/{tid}/spots/{size}"
    
    # Fallback genérico de la liga si no se reconoce
    return f"{_MLB_SPOT_BASE}/695/spots/{size}"


def get_team_name(team_identifier: Any) -> str:
    """Retorna el nombre canónico del equipo."""
    tid = resolve_team_id(team_identifier)
    if tid and tid in LVBP_TEAMS:
        return LVBP_TEAMS[tid]
    return str(team_identifier) if team_identifier else "Equipo Desconocido"


def get_team_abbr(team_identifier: Any) -> str:
    """Retorna la abreviación de 3 letras del equipo."""
    tid = resolve_team_id(team_identifier)
    if tid and tid in LVBP_ABBR:
        return LVBP_ABBR[tid]
    return "LVBP"


def get_team_color(team_identifier: Any, color_type: str = "primary") -> str:
    """Retorna el color primario o secundario en formato hexadecimal."""
    tid = resolve_team_id(team_identifier)
    if tid and tid in LVBP_COLORS:
        return LVBP_COLORS[tid].get(color_type, "#002D62")
    return "#002D62"


import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPUBLICA_CARAQUISTA_LOGO = os.path.join(_REPO_ROOT, "logo.png")


def get_brand_logo() -> str:
    """
    Retorna la ruta absoluta al logo oficial de República Caraquista (logo.png).
    Garantiza que la imagen cargue sin importar desde qué subpágina se invoque.
    """
    if os.path.exists(REPUBLICA_CARAQUISTA_LOGO):
        return REPUBLICA_CARAQUISTA_LOGO
    return "logo.png"
