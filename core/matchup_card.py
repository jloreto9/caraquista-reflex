# core/matchup_card.py
"""
matchup_card.py
---------------
Generador de tarjetas gráficas Matchup 360 en formato PNG de alta definición
para República Caraquista, con diseño Dark Navy Glass, escudos de franquicias,
fotos circulares oficiales de MLB API y créditos sabermétricos de autoría.
"""

import io
import os
import urllib.request
from typing import Dict, List, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Carga fuentes multiplataforma con soporte Unicode completo para acentos y caracteres especiales."""
    suffix = "-Bold" if bold else ""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    paths = [
        # 1. Fuentes TrueType empaquetadas en el repositorio (garantía total multiplataforma)
        os.path.join(repo_root, "assets", "fonts", f"DejaVuSans{suffix}.ttf"),
        os.path.join(here, "fonts", f"DejaVuSans{suffix}.ttf"),
        # 2. Fuentes estándar del sistema Linux
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans{'-Bold' if bold else '-Regular'}.ttf",
        # 3. Fuentes del sistema Windows
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
        f"C:/Windows/Fonts/{'segoeuib' if bold else 'segoeui'}.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fetch_circular_image(
    url: Optional[str],
    size: Tuple[int, int] = (128, 128),
    border_color: Tuple[int, int, int] = (253, 184, 39),
    initials: str = "LV",
) -> Image.Image:
    """Descarga y recorta en formato circular el headshot del jugador con borde coloreado y fallback seguro."""
    circ = Image.new("RGBA", size, (0, 0, 0, 0))
    raw_img = None

    if url:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = resp.read()
            raw_img = Image.open(io.BytesIO(data)).convert("RGBA")
            raw_img = raw_img.resize(size, Image.Resampling.LANCZOS)
        except Exception:
            raw_img = None

    if raw_img:
        mask = Image.new("L", size, 0)
        draw_m = ImageDraw.Draw(mask)
        draw_m.ellipse((0, 0) + size, fill=255)
        circ.paste(raw_img, (0, 0), mask=mask)
    else:
        # Fallback elegante: avatar circular oscuro con iniciales
        draw_f = ImageDraw.Draw(circ)
        draw_f.ellipse((0, 0) + size, fill=(20, 29, 56, 255))
        f_init = _load_font(size[0] // 3, bold=True)
        try:
            bb = draw_f.textbbox((0, 0), initials, font=f_init)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
        except AttributeError:
            tw, th = size[0] // 2, size[1] // 2
        draw_f.text(
            ((size[0] - tw) // 2, (size[1] - th) // 2),
            initials,
            font=f_init,
            fill=border_color,
        )

    # Borde decorativo proporcional al tamaño
    b_width = max(2, int(round(3 * (size[0] / 64.0))))
    border_draw = ImageDraw.Draw(circ)
    border_draw.ellipse((0, 0, size[0] - 1, size[1] - 1), outline=border_color + (255,), width=b_width)
    return circ


def _fetch_team_logo(url: Optional[str], size: Tuple[int, int] = (52, 52)) -> Optional[Image.Image]:
    """Descarga y redimensiona el logo oficial de la franquicia."""
    if not url:
        return None
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = resp.read()
        raw_img = Image.open(io.BytesIO(data)).convert("RGBA")
        return raw_img.resize(size, Image.Resampling.LANCZOS)
    except Exception:
        return None


def build_matchup_image(
    player_1: Dict[str, Any],
    player_2: Dict[str, Any],
    h2h_rows: List[Dict[str, Any]],
    is_batter: bool = True,
    season: int = 2025,
    phase: str = "Temporada Regular",
    phase_1: Optional[str] = None,
    phase_2: Optional[str] = None,
    scale: float = 2.0,
) -> bytes:
    """Genera una tarjeta PNG descargable de alta definición (300 DPI) con diseño Dark Navy Glass y créditos oficiales."""
    sc = float(scale) if scale > 0 else 2.0
    p1_phase = phase_1 or player_1.get("phase") or phase
    p2_phase = phase_2 or player_2.get("phase") or phase

    name1 = player_1.get("name", "Jugador 1")
    team1 = player_1.get("badge") or player_1.get("team", "CAR")
    pos1 = player_1.get("pos", "Bateador" if is_batter else "Lanzador")
    headshot1 = player_1.get("headshot")
    logo1 = player_1.get("team_logo")

    name2 = player_2.get("name", "Jugador 2")
    team2 = player_2.get("badge") or player_2.get("team", "LVBP")
    pos2 = player_2.get("pos", "Bateador" if is_batter else "Lanzador")
    headshot2 = player_2.get("headshot")
    logo2 = player_2.get("team_logo")

    # Geometría escalada a alta definición (300 PPI)
    COL1 = int(round(240 * sc))
    COL2 = int(round(200 * sc))
    COL3 = int(round(240 * sc))
    W = COL1 + COL2 + COL3
    ROW_H = int(round(30 * sc))
    HDR_H = int(round(116 * sc))
    FOOT_H = int(round(86 * sc))
    LINE_W = max(1, int(round(1 * sc)))

    # Filtrar solo filas de datos (no headers de categoría), max 18 filas
    data_rows = [r for r in h2h_rows if not r.get("is_header", False)]
    if len(data_rows) > 18:
        data_rows = data_rows[:18]

    n = len(data_rows)
    H = HDR_H + n * ROW_H + FOOT_H

    # Paleta de Colores Oficial
    BG_DARK   = (7, 11, 25)
    CARD_BG   = (13, 21, 43)
    ALT_BG    = (9, 14, 30)
    BORDER_C  = (30, 41, 69)
    GOLD_CLR  = (253, 184, 39)    # Acento Jugador 1 (Oro Caraquista)
    BLUE_CLR  = (56, 189, 248)    # Acento Jugador 2 (Azul Cielo)
    WHITE     = (255, 255, 255)
    GRAY_TEXT = (148, 163, 184)
    DIM_TEXT  = (100, 116, 139)

    fb = _load_font(int(round(12 * sc)), bold=True)
    fn = _load_font(int(round(11 * sc)))
    fs = _load_font(int(round(9 * sc)))
    f_large = _load_font(int(round(14 * sc)), bold=True)
    f_title = _load_font(int(round(13 * sc)), bold=True)
    f_badge = _load_font(int(round(8.5 * sc)), bold=True)

    img = Image.new("RGBA", (W, H), BG_DARK + (255,))
    draw = ImageDraw.Draw(img)

    def _tc(cx: int, cy: int, text: str, font: ImageFont.ImageFont, color: Tuple[int, ...]):
        """Dibuja texto centrado horizontal y verticalmente en (cx, cy)."""
        s = str(text)
        try:
            bb = draw.textbbox((0, 0), s, font=font)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
        except AttributeError:
            tw, th = int(len(s) * 6 * sc), int(12 * sc)
        draw.text((cx - tw // 2, cy - th // 2), s, font=font, fill=color)

    # ── 1. Header Cards ────────────────────────────────────────────────────────
    # Header Left (Jugador 1)
    draw.rectangle([0, 0, COL1 - 1, HDR_H - 1], fill=(24, 18, 20))
    draw.rectangle([0, 0, int(round(5 * sc)), HDR_H - 1], fill=GOLD_CLR)

    # Header Center (VS Branding)
    draw.rectangle([COL1, 0, COL1 + COL2 - 1, HDR_H - 1], fill=(13, 21, 43))

    # Header Right (Jugador 2)
    draw.rectangle([COL1 + COL2, 0, W - 1, HDR_H - 1], fill=(10, 25, 45))
    draw.rectangle([W - int(round(5 * sc)), 0, W - 1, HDR_H - 1], fill=BLUE_CLR)

    avatar_sz = int(round(64 * sc))
    logo_sz = int(round(26 * sc))

    # Pegar Headshots y Logos - Jugador 1
    init1 = "".join([part[0] for part in name1.split()[:2]]).upper() or "P1"
    hs1 = _fetch_circular_image(headshot1, size=(avatar_sz, avatar_sz), border_color=GOLD_CLR, initials=init1)
    img.paste(hs1, (int(round(12 * sc)), (HDR_H - avatar_sz) // 2), mask=hs1)

    p1_cx = COL1 // 2 + int(round(26 * sc))
    _tc(p1_cx, int(round(32 * sc)), name1, f_title, WHITE)
    _tc(p1_cx, int(round(58 * sc)), f"{team1} · {pos1}", fs, GOLD_CLR)
    _tc(p1_cx, int(round(82 * sc)), f"[{p1_phase}]", f_badge, (240, 200, 120))

    tlogo1 = _fetch_team_logo(logo1, size=(logo_sz, logo_sz))
    if tlogo1:
        img.paste(tlogo1, (COL1 - logo_sz - int(round(10 * sc)), int(round(12 * sc))), mask=tlogo1)

    # Center Branding & Temporada
    _tc(COL1 + COL2 // 2, int(round(28 * sc)), "REPÚBLICA CARAQUISTA", f_large, GOLD_CLR)
    _tc(COL1 + COL2 // 2, int(round(52 * sc)), "MATCHUP 360 · LVBP", fb, WHITE)
    if p1_phase != p2_phase:
        center_phase_txt = f"{season}-{season+1} · Fases Cruzadas"
    else:
        center_phase_txt = f"{season}-{season+1} · {p1_phase}"
    _tc(COL1 + COL2 // 2, int(round(76 * sc)), center_phase_txt, fs, GRAY_TEXT)

    # Pegar Headshots y Logos - Jugador 2
    init2 = "".join([part[0] for part in name2.split()[:2]]).upper() or "P2"
    hs2 = _fetch_circular_image(headshot2, size=(avatar_sz, avatar_sz), border_color=BLUE_CLR, initials=init2)
    img.paste(hs2, (COL1 + COL2 + int(round(12 * sc)), (HDR_H - avatar_sz) // 2), mask=hs2)

    p2_cx = COL1 + COL2 + COL3 // 2 + int(round(26 * sc))
    _tc(p2_cx, int(round(32 * sc)), name2, f_title, WHITE)
    _tc(p2_cx, int(round(58 * sc)), f"{team2} · {pos2}", fs, BLUE_CLR)
    _tc(p2_cx, int(round(82 * sc)), f"[{p2_phase}]", f_badge, (160, 210, 255))

    tlogo2 = _fetch_team_logo(logo2, size=(logo_sz, logo_sz))
    if tlogo2:
        img.paste(tlogo2, (W - logo_sz - int(round(10 * sc)), int(round(12 * sc))), mask=tlogo2)

    # Línea Divisoria Header
    draw.line([(0, HDR_H), (W, HDR_H)], fill=BORDER_C, width=LINE_W)

    # ── 2. Filas de Comparación ────────────────────────────────────────────────
    y = HDR_H
    for idx, row in enumerate(data_rows):
        row_bg = CARD_BG if idx % 2 == 0 else ALT_BG
        draw.rectangle([0, y, W - 1, y + ROW_H - 1], fill=row_bg)

        metric_label = str(row.get("metric", "—")).strip()
        v1_str = str(row.get("val_1", "—"))
        v2_str = str(row.get("val_2", "—"))
        winner = str(row.get("winner", ""))

        is_p1_win = name1 in winner or f"({team1})" in winner
        is_p2_win = name2 in winner or f"({team2})" in winner

        c1 = GOLD_CLR if is_p1_win else WHITE
        c2 = BLUE_CLR if is_p2_win else WHITE
        f1 = fb if is_p1_win else fn
        f2 = fb if is_p2_win else fn

        _tc(COL1 // 2, y + ROW_H // 2, v1_str, f1, c1)
        _tc(COL1 + COL2 // 2, y + ROW_H // 2, metric_label, fb, (220, 225, 235))
        _tc(COL1 + COL2 + COL3 // 2, y + ROW_H // 2, v2_str, f2, c2)

        draw.line([(0, y + ROW_H), (W, y + ROW_H)], fill=BORDER_C, width=LINE_W)
        y += ROW_H

    # ── 3. Footer Branding & Créditos Oficiales ────────────────────────────────
    draw.rectangle([0, y, W - 1, H - 1], fill=(7, 11, 25))
    draw.line([(0, y), (W, y)], fill=BORDER_C, width=LINE_W)
    _tc(W // 2, y + int(round(20 * sc)), "REPÚBLICA CARAQUISTA — Plataforma Sabermétrica & Analítica Integral LVBP", fb, GOLD_CLR)
    _tc(W // 2, y + int(round(44 * sc)), "Fuentes: MLB Stats API (sportId=17, leagueId=135) · Tom Tango (RE24 / WPA) · BIS Hardness", fs, GRAY_TEXT)
    _tc(W // 2, y + int(round(66 * sc)), "Desarrollado por Jorge Leonardo Loreto · AI Data Scientist & Baseball Sabermetrician", fs, DIM_TEXT)

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300), optimize=True)
    return buf.getvalue()
