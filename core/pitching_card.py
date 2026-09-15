# core/pitching_card.py
"""
pitching_card.py
----------------
Generador de tarjetas gráficas panorámicas (16:9, 2400x1350 px a 300 DPI) para el
Pitching Summary de República Caraquista, inspirado en Thomas Nestico (@TJStats).
Soporta:
1. Rama MLB/MiLB: Telemetría Statcast (Tabla de repertorio, Movimiento IVB vs HB,
   Strike Zone y Perfil de Velocidades).
2. Rama Leones del Caracas (LVBP): Sabermetría PBP adaptada (Tabla de destinos,
   Carga por entrada, Leverage Index Tango RE24 y Splits LHB vs RHB).
Identidad visual: Dark Navy (#070B19), Tarjetas Glass (#0D152B), Oro Caraquista (#FDB827),
fuentes empaquetadas DejaVuSans con soporte Unicode y créditos oficiales.
"""

import io
import os
import math
import urllib.request
from typing import Dict, List, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

# ── Constantes de Diseño y Paleta ─────────────────────────────────────────────
CANVAS_SIZE = (2400, 1350)
DPI = (300, 300)

BG_DARK = (7, 11, 25, 255)            # #070B19
CARD_BG = (13, 21, 43, 230)           # #0D152B
CARD_BORDER = (30, 42, 74, 255)       # #1E2A4A
ACCENT_GOLD = (253, 184, 39, 255)     # #FDB827
GOLD_DIM = (180, 130, 25, 255)
TEXT_WHITE = (248, 250, 252, 255)     # #F8FAFC
TEXT_MUTED = (148, 163, 184, 255)     # #94A3B8
TEXT_DIM = (100, 116, 139, 255)       # #64748B
ZONE_OUTLINE = (59, 130, 246, 200)    # Azul zona

# Paleta canónica sabermétrica para tipos de pitcheos
PITCH_COLORS: Dict[str, Tuple[int, int, int]] = {
    "4-Seam Fastball": (210, 45, 73),    # Rojo / Carmesí
    "Four-Seam Fastball": (210, 45, 73),
    "Fastball": (210, 45, 73),
    "Sinker": (254, 157, 0),             # Naranja
    "Cutter": (147, 63, 44),             # Marrón / Óxido
    "Slider": (238, 231, 22),            # Amarillo
    "Sweeper": (221, 179, 59),           # Ocre dorado
    "Curveball": (0, 161, 222),          # Cyan / Azul cielo
    "Knuckle Curve": (0, 120, 200),
    "Changeup": (29, 190, 58),           # Verde esmeralda
    "Split-Finger": (59, 172, 172),      # Teal
    "Splitter": (59, 172, 172),
    "Knuckleball": (102, 45, 145),       # Púrpura
    "Desconocido": (140, 140, 140),      # Gris
}


def _get_pitch_color(p_name: str) -> Tuple[int, int, int]:
    for k, v in PITCH_COLORS.items():
        if k.lower() in p_name.lower():
            return v
    return (140, 140, 140)


# ── Helpers de Fuentes e Imágenes ─────────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Carga fuentes TrueType empaquetadas con soporte Unicode total."""
    suffix = "-Bold" if bold else ""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    paths = [
        os.path.join(repo_root, "assets", "fonts", f"DejaVuSans{suffix}.ttf"),
        os.path.join(here, "fonts", f"DejaVuSans{suffix}.ttf"),
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf",
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
    size: Tuple[int, int] = (160, 160),
    border_color: Tuple[int, int, int] = (253, 184, 39),
    initials: str = "P",
) -> Image.Image:
    """Descarga y recorta en formato circular el headshot del jugador."""
    circ = Image.new("RGBA", size, (0, 0, 0, 0))
    raw_img = None

    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
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
        draw_f = ImageDraw.Draw(circ)
        draw_f.ellipse((0, 0) + size, fill=(20, 29, 56, 255))
        f_init = _load_font(size[0] // 3, bold=True)
        bb = draw_f.textbbox((0, 0), initials, font=f_init)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw_f.text(((size[0] - tw) // 2, (size[1] - th) // 2), initials, font=f_init, fill=border_color)

    b_width = max(3, int(round(4 * (size[0] / 128.0))))
    border_draw = ImageDraw.Draw(circ)
    border_draw.ellipse((0, 0, size[0] - 1, size[1] - 1), outline=border_color + (255,), width=b_width)
    return circ


def _load_caraquista_logo(size: Tuple[int, int] = (120, 120)) -> Optional[Image.Image]:
    """Carga el logo oficial de República Caraquista."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    p = os.path.join(repo_root, "assets", "logo.png")
    if os.path.exists(p):
        try:
            img = Image.open(p).convert("RGBA")
            return img.resize(size, Image.Resampling.LANCZOS)
        except Exception:
            pass
    return None


# ── Renderizado de Paneles y Gráficos PIL ──────────────────────────────────────

def _draw_card_box(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], radius: int = 16):
    """Dibuja una caja con fondo glass y borde sutil."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=CARD_BG, outline=CARD_BORDER, width=2)


def _draw_movement_plot(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], pitches: List[Dict[str, Any]]):
    """
    Dibuja el gráfico cartesiano de movimiento de pitcheos:
    IVB (Eje Y: -25 a +25 in) vs HB (Eje X: -25 a +25 in).
    """
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    w = x1 - x0
    h = y1 - y0
    scale = (min(w, h) - 60) / 50.0  # 50 pulgadas de rango total (-25 a +25)

    # Ejes coordenados principales
    draw.line([(cx, y0 + 30), (cx, y1 - 30)], fill=(60, 80, 120, 255), width=2)
    draw.line([(x0 + 30, cy), (x1 - 30, cy)], fill=(60, 80, 120, 255), width=2)

    # Círculos de distancia (10 in, 20 in)
    for r_in in (10, 20):
        r_px = int(r_in * scale)
        draw.ellipse([cx - r_px, cy - r_px, cx + r_px, cy + r_px], outline=(35, 50, 80, 200), width=1)

    # Etiquetas de cuadrantes
    f_quad = _load_font(18, bold=True)
    draw.text((x1 - 130, cy - 25), "BRAZO →", font=f_quad, fill=TEXT_DIM)
    draw.text((x0 + 40, cy - 25), "← GUANTE", font=f_quad, fill=TEXT_DIM)
    draw.text((cx + 10, y0 + 35), "↑ +IVB", font=f_quad, fill=TEXT_DIM)
    draw.text((cx + 10, y1 - 55), "↓ -IVB", font=f_quad, fill=TEXT_DIM)

    # Dibujar puntos de pitcheos
    for p in pitches:
        hb = p.get("hb")
        ivb = p.get("ivb")
        if hb is None or ivb is None:
            continue
        # En coordenadas béisbol: X positivo = HB, Y positivo = IVB
        px = int(cx + (hb * scale))
        py = int(cy - (ivb * scale))

        if x0 + 10 <= px <= x1 - 10 and y0 + 10 <= py <= y1 - 10:
            col = _get_pitch_color(p.get("pitch_name", ""))
            r = 7
            draw.ellipse([px - r, py - r, px + r, py + r], fill=col + (220,), outline=(255, 255, 255, 180), width=1)


def _draw_strike_zone_plot(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], pitches: List[Dict[str, Any]]):
    """
    Dibuja la zona de strike y los puntos de localización (plate_x, plate_z).
    """
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    scale = 130.0  # px por pie

    # Rectángulo de zona de strike (ancho ~1.42 ft, alto 1.5 a 3.5 ft)
    zw = int(1.42 * scale)
    zh = int(2.0 * scale)
    zx0 = cx - zw // 2
    zx1 = cx + zw // 2
    zy0 = cy - zh // 2
    zy1 = cy + zh // 2

    # Zona exterior difuminada
    draw.rectangle([zx0 - 30, zy0 - 30, zx1 + 30, zy1 + 30], outline=(40, 55, 90, 180), width=1)
    # Zona oficial 3x3
    draw.rectangle([zx0, zy0, zx1, zy1], outline=ZONE_OUTLINE, width=3)
    # Líneas de cuadrantes 3x3
    draw.line([(zx0 + zw // 3, zy0), (zx0 + zw // 3, zy1)], fill=(40, 80, 150, 160), width=1)
    draw.line([(zx0 + 2 * zw // 3, zy0), (zx0 + 2 * zw // 3, zy1)], fill=(40, 80, 150, 160), width=1)
    draw.line([(zx0, zy0 + zh // 3), (zx1, zy0 + zh // 3)], fill=(40, 80, 150, 160), width=1)
    draw.line([(zx0, zy0 + 2 * zh // 3), (zx1, zy0 + 2 * zh // 3)], fill=(40, 80, 150, 160), width=1)

    # Home Plate estilizado en la parte inferior
    hp_y = zy1 + 35
    draw.polygon([
        (cx - 35, hp_y),
        (cx + 35, hp_y),
        (cx + 35, hp_y + 15),
        (cx, hp_y + 35),
        (cx - 35, hp_y + 15)
    ], fill=(120, 140, 180, 180), outline=(200, 220, 255, 220))

    # Puntos de pitcheos
    for p in pitches:
        px_ft = p.get("plate_x")
        pz_ft = p.get("plate_z")
        if px_ft is None or pz_ft is None:
            continue

        px = int(cx + (px_ft * scale))
        py = int(cy - ((pz_ft - 2.5) * scale))

        if x0 + 10 <= px <= x1 - 10 and y0 + 10 <= py <= y1 - 10:
            col = _get_pitch_color(p.get("pitch_name", ""))
            r = 7
            if p.get("is_whiff"):
                # Cruz o anillo dorado para swing fallido
                draw.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2], outline=(253, 184, 39, 255), width=2)
            draw.ellipse([px - r, py - r, px + r, py + r], fill=col + (230,), outline=(255, 255, 255, 180), width=1)


def _draw_workload_bars(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], workload: List[Dict[str, Any]]):
    """Dibuja barras de pitcheos por entrada con hito de strikes."""
    x0, y0, x1, y1 = box
    if not workload:
        f = _load_font(22)
        draw.text((x0 + 40, y0 + 60), "Sin datos por entrada", font=f, fill=TEXT_MUTED)
        return

    n = len(workload)
    bar_w = min(60, (x1 - x0 - 100) // (n * 2))
    max_p = max((w["pitches"] for w in workload), default=25)
    max_p = max(max_p, 20)
    base_y = y1 - 70
    chart_h = base_y - (y0 + 70)

    f_lbl = _load_font(18, bold=True)
    f_num = _load_font(18)

    for idx, w in enumerate(workload):
        inn = w["inning"]
        tot = w["pitches"]
        strk = w["strikes"]

        bx = x0 + 60 + idx * (bar_w * 2 + 15)
        h_tot = int((tot / max_p) * chart_h)
        h_strk = int((strk / max_p) * chart_h)

        # Barra total (Bolas / lanzamientos totales)
        draw.rounded_rectangle([bx, base_y - h_tot, bx + bar_w, base_y], radius=6, fill=(50, 70, 110, 220))
        # Barra Strikes
        draw.rounded_rectangle([bx, base_y - h_strk, bx + bar_w, base_y], radius=6, fill=(253, 184, 39, 240))

        # Texto Inning
        draw.text((bx + (bar_w // 4), base_y + 12), f"In {inn}", font=f_lbl, fill=TEXT_MUTED)
        # Conteo
        draw.text((bx + (bar_w // 4) - 2, base_y - h_tot - 25), str(tot), font=f_num, fill=TEXT_WHITE)

    # Leyenda
    draw.rectangle([x0 + 40, y0 + 25, x0 + 55, y0 + 40], fill=(253, 184, 39, 255))
    draw.text((x0 + 65, y0 + 22), "Strikes", font=f_num, fill=TEXT_MUTED)
    draw.rectangle([x0 + 160, y0 + 25, x0 + 175, y0 + 40], fill=(50, 70, 110, 255))
    draw.text((x0 + 185, y0 + 22), "Bolas", font=f_num, fill=TEXT_MUTED)


def _draw_leverage_bars(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], workload: List[Dict[str, Any]]):
    """Dibuja el Leverage Index (LI) por entrada con línea de High Leverage."""
    x0, y0, x1, y1 = box
    if not workload:
        f = _load_font(22)
        draw.text((x0 + 40, y0 + 60), "Sin datos de apalancamiento", font=f, fill=TEXT_MUTED)
        return

    n = len(workload)
    bar_w = min(50, (x1 - x0 - 100) // (n * 2))
    base_y = y1 - 70
    chart_h = base_y - (y0 + 70)
    max_li = 3.0

    f_lbl = _load_font(18, bold=True)
    f_num = _load_font(18)

    # Línea promedio LI = 1.0
    y_li_1 = base_y - int((1.0 / max_li) * chart_h)
    draw.line([(x0 + 40, y_li_1), (x1 - 40, y_li_1)], fill=(80, 100, 140, 180), width=1)
    draw.text((x1 - 120, y_li_1 - 20), "LI = 1.0 (Avg)", font=_load_font(14), fill=TEXT_DIM)

    # Línea High Leverage LI = 1.5
    y_li_high = base_y - int((1.5 / max_li) * chart_h)
    draw.line([(x0 + 40, y_li_high), (x1 - 40, y_li_high)], fill=(239, 68, 68, 160), width=1)
    draw.text((x1 - 150, y_li_high - 20), "Alto Apalancamiento", font=_load_font(14), fill=(239, 68, 68, 200))

    for idx, w in enumerate(workload):
        inn = w["inning"]
        li = w.get("avg_li", 1.0)
        bx = x0 + 60 + idx * (bar_w * 2 + 15)
        h_bar = int((min(li, max_li) / max_li) * chart_h)

        col = (239, 68, 68, 240) if li >= 1.5 else ((253, 184, 39, 240) if li >= 0.9 else (59, 130, 246, 240))
        draw.rounded_rectangle([bx, base_y - h_bar, bx + bar_w, base_y], radius=6, fill=col)

        draw.text((bx + (bar_w // 4), base_y + 12), f"In {inn}", font=f_lbl, fill=TEXT_MUTED)
        draw.text((bx + 2, base_y - h_bar - 25), f"{li:.1f}", font=f_num, fill=TEXT_WHITE)


def _draw_platoon_card(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], splits: Dict[str, Any]):
    """Dibuja la comparativa de rendimiento vs bateadores zurdos y derechos."""
    x0, y0, x1, y1 = box
    lhb = splits.get("vs_lhb", {})
    rhb = splits.get("vs_rhb", {})

    f_title = _load_font(24, bold=True)
    f_metric = _load_font(20, bold=True)
    f_val = _load_font(28, bold=True)
    f_lbl = _load_font(18)

    mid_x = (x0 + x1) // 2

    # Columna LHB (Zurdos)
    draw.text((x0 + 40, y0 + 30), "VS ZURDOS (LHB)", font=f_title, fill=ACCENT_GOLD)
    draw.text((x0 + 40, y0 + 80), "Pitcheos Totales:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((x0 + 40, y0 + 105), str(lhb.get("pitches", 0)), font=f_val, fill=TEXT_WHITE)

    draw.text((x0 + 40, y0 + 160), "Strike %:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((x0 + 40, y0 + 185), str(lhb.get("strike_pct", "0.0%")), font=f_val, fill=TEXT_WHITE)

    draw.text((x0 + 40, y0 + 240), "CSW %:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((x0 + 40, y0 + 265), str(lhb.get("csw_pct", "0.0%")), font=f_val, fill=ACCENT_GOLD)

    draw.text((x0 + 40, y0 + 320), "Whiff %:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((x0 + 40, y0 + 345), str(lhb.get("whiff_pct", "0.0%")), font=f_val, fill=TEXT_WHITE)

    # Divisor central
    draw.line([(mid_x, y0 + 40), (mid_x, y1 - 40)], fill=CARD_BORDER, width=2)

    # Columna RHB (Derechos)
    draw.text((mid_x + 40, y0 + 30), "VS DERECHOS (RHB)", font=f_title, fill=ACCENT_GOLD)
    draw.text((mid_x + 40, y0 + 80), "Pitcheos Totales:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((mid_x + 40, y0 + 105), str(rhb.get("pitches", 0)), font=f_val, fill=TEXT_WHITE)

    draw.text((mid_x + 40, y0 + 160), "Strike %:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((mid_x + 40, y0 + 185), str(rhb.get("strike_pct", "0.0%")), font=f_val, fill=TEXT_WHITE)

    draw.text((mid_x + 40, y0 + 240), "CSW %:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((mid_x + 40, y0 + 265), str(rhb.get("csw_pct", "0.0%")), font=f_val, fill=ACCENT_GOLD)

    draw.text((mid_x + 40, y0 + 320), "Whiff %:", font=f_lbl, fill=TEXT_MUTED)
    draw.text((mid_x + 40, y0 + 345), str(rhb.get("whiff_pct", "0.0%")), font=f_val, fill=TEXT_WHITE)


# ── Función Principal de Renderizado ──────────────────────────────────────────

def build_pitching_summary_card(
    pitcher_data: Dict[str, Any],
    game_data: Dict[str, Any],
    pitch_analysis: Dict[str, Any],
    is_lvbp: bool = False,
    season: int = 2025,
) -> bytes:
    """
    Genera la tarjeta gráfica panorámica oficial (2400x1350 px a 300 DPI)
    en formato PNG en memoria.
    """
    img = Image.new("RGBA", CANVAS_SIZE, BG_DARK)
    draw = ImageDraw.Draw(img)

    # 1. Cabecera (Header Banner)
    _draw_card_box(draw, (40, 40, 2360, 230), radius=20)

    # Avatar del lanzador
    headshot_url = pitcher_data.get("photo_url")
    avatar = _fetch_circular_image(headshot_url, size=(150, 150), border_color=(253, 184, 39))
    img.paste(avatar, (65, 60), mask=avatar)

    # Textos del lanzador
    p_name = pitcher_data.get("name", "Lanzador")
    throws = pitcher_data.get("throws", "R")
    team = pitcher_data.get("team", "Equipo")
    role = game_data.get("role", "Abridor")
    date_str = game_data.get("date", "")
    opp = game_data.get("opponent", "Rival")
    league = "LVBP • LEONES DEL CARACAS" if is_lvbp else f"{game_data.get('league', 'MLB')} • STATCAST"

    f_title = _load_font(44, bold=True)
    f_sub = _load_font(22)
    f_league = _load_font(20, bold=True)

    draw.text((240, 65), p_name.upper(), font=f_title, fill=TEXT_WHITE)
    draw.text((240, 125), f"Lanza: {throws}HP  |  {role}  |  vs {opp}  |  {date_str}", font=f_sub, fill=TEXT_MUTED)
    draw.text((240, 160), league, font=f_league, fill=ACCENT_GOLD)

    # Boxscore KPIs en pastillas
    ip = game_data.get("ip", "0.0")
    h = game_data.get("h", 0)
    r = game_data.get("r", 0)
    er = game_data.get("er", 0)
    bb = game_data.get("bb", 0)
    so = game_data.get("so", 0)
    tot_p = pitch_analysis.get("total_pitches", game_data.get("pitches", 0))
    pbp_kpis = pitch_analysis.get("pbp_kpis", {})
    csw = pbp_kpis.get("csw_pct", "0.0%")
    whiff = pbp_kpis.get("whiff_pct", "0.0%")

    kpis_box = [
        ("IP", str(ip)),
        ("H", str(h)),
        ("R", str(r)),
        ("ER", str(er)),
        ("BB", str(bb)),
        ("K", str(so)),
        ("PITCHES", str(tot_p)),
        ("CSW%", str(csw)),
        ("WHIFF%", str(whiff)),
    ]

    kx = 1050
    ky = 75
    f_kpi_val = _load_font(28, bold=True)
    f_kpi_lbl = _load_font(16, bold=True)

    for lbl, val in kpis_box:
        draw.rounded_rectangle([kx, ky, kx + 105, ky + 105], radius=10, fill=(20, 31, 62, 220), outline=CARD_BORDER)
        # Centrar texto
        bb_v = draw.textbbox((0, 0), val, font=f_kpi_val)
        tw_v = bb_v[2] - bb_v[0]
        draw.text((kx + (105 - tw_v) // 2, ky + 18), val, font=f_kpi_val, fill=TEXT_WHITE if lbl not in ("CSW%", "K") else ACCENT_GOLD)

        bb_l = draw.textbbox((0, 0), lbl, font=f_kpi_lbl)
        tw_l = bb_l[2] - bb_l[0]
        draw.text((kx + (105 - tw_l) // 2, ky + 68), lbl, font=f_kpi_lbl, fill=TEXT_MUTED)

        kx += 120

    # Logo República Caraquista a la derecha
    rc_logo = _load_caraquista_logo(size=(140, 140))
    if rc_logo:
        img.paste(rc_logo, (2180, 65), mask=rc_logo)

    # 2. Panel Central (Tabla de Repertorio o Destinos)
    _draw_card_box(draw, (40, 250, 2360, 710), radius=20)
    f_tbl_title = _load_font(26, bold=True)
    f_tbl_hdr = _load_font(19, bold=True)
    f_tbl_row = _load_font(20)
    f_tbl_row_b = _load_font(20, bold=True)

    if not is_lvbp and pitch_analysis.get("has_statcast"):
        draw.text((70, 275), "REPERTORIO & TELEMETRÍA DE PITCHEOS (HAWK-EYE / STATCAST)", font=f_tbl_title, fill=ACCENT_GOLD)

        headers = [
            ("PITCH TYPE", 70),
            ("COUNT", 420),
            ("USO %", 580),
            ("VELO AVG", 750),
            ("VELO MAX", 930),
            ("SPIN (RPM)", 1120),
            ("IVB (IN)", 1320),
            ("HB (IN)", 1500),
            ("WHIFF %", 1690),
            ("CSW %", 1880),
            ("ZONE %", 2070),
        ]
        # Línea de cabecera
        draw.line([(65, 325), (2335, 325)], fill=CARD_BORDER, width=2)
        for h_text, hx in headers:
            draw.text((hx, 335), h_text, font=f_tbl_hdr, fill=TEXT_MUTED)
        draw.line([(65, 375), (2335, 375)], fill=CARD_BORDER, width=2)

        # Filas de pitcheos
        ry = 390
        for row in pitch_analysis.get("statcast_table", []):
            p_col = _get_pitch_color(row["pitch_name"])
            # Bala de color del pitcheo
            draw.ellipse([70, ry + 5, 88, ry + 23], fill=p_col)
            draw.text((105, ry), row["pitch_name"], font=f_tbl_row_b, fill=TEXT_WHITE)
            draw.text((420, ry), str(row["count"]), font=f_tbl_row, fill=TEXT_WHITE)
            draw.text((580, ry), str(row["usage_pct"]), font=f_tbl_row_b, fill=TEXT_WHITE)
            draw.text((750, ry), f"{row['velo_avg']} mph", font=f_tbl_row, fill=TEXT_WHITE)
            draw.text((930, ry), f"{row['velo_max']} mph", font=f_tbl_row, fill=TEXT_WHITE)
            draw.text((1120, ry), str(row["spin_avg"]), font=f_tbl_row, fill=TEXT_WHITE)
            draw.text((1320, ry), f"{row['ivb']}\"", font=f_tbl_row, fill=ACCENT_GOLD if isinstance(row['ivb'], (int, float)) and row['ivb'] > 15 else TEXT_WHITE)
            draw.text((1500, ry), f"{row['hb']}\"", font=f_tbl_row, fill=TEXT_WHITE)
            draw.text((1690, ry), str(row["whiff_pct"]), font=f_tbl_row_b, fill=ACCENT_GOLD if float(row["whiff_pct"].replace("%", "")) >= 25.0 else TEXT_WHITE)
            draw.text((1880, ry), str(row["csw_pct"]), font=f_tbl_row_b, fill=ACCENT_GOLD if float(row["csw_pct"].replace("%", "")) >= 30.0 else TEXT_WHITE)
            draw.text((2070, ry), str(row["zone_pct"]), font=f_tbl_row, fill=TEXT_WHITE)

            ry += 52
            if ry > 660:
                break
    else:
        # Pestaña Leones del Caracas (LVBP) o MiLB sin Hawkeye
        title_tag = "DESTINOS Y RESULTADOS DE PITCHEOS (PLAY-BY-PLAY SABERMÉTRICO LVBP)" if is_lvbp else "DESTINOS DE PITCHEOS (PLAY-BY-PLAY)"
        draw.text((70, 275), title_tag, font=f_tbl_title, fill=ACCENT_GOLD)

        pbp_headers = [
            ("DESTINO DEL PITCHEO", 120),
            ("TOTAL CONTEO", 700),
            ("DISTRIBUCIÓN %", 1100),
            ("IMPACTO SABERMÉTRICO", 1550),
        ]
        draw.line([(65, 325), (2335, 325)], fill=CARD_BORDER, width=2)
        for h_text, hx in pbp_headers:
            draw.text((hx, 335), h_text, font=f_tbl_hdr, fill=TEXT_MUTED)
        draw.line([(65, 375), (2335, 375)], fill=CARD_BORDER, width=2)

        ry = 400
        for r_pbp in pitch_analysis.get("pbp_table", []):
            dest = r_pbp.get("destination", "")
            cnt = r_pbp.get("count", 0)
            pct = r_pbp.get("pct", "0.0%")

            impact = "Ventaja del lanzador (Cuenta a favor)" if "Cantados" in dest or "Whiff" in dest else ("Riesgo de daño / Bip" if "En Juego" in dest else "Control / Strike counting")

            draw.text((120, ry), dest, font=f_tbl_row_b, fill=TEXT_WHITE)
            draw.text((700, ry), str(cnt), font=f_tbl_row, fill=TEXT_WHITE)
            draw.text((1100, ry), str(pct), font=f_tbl_row_b, fill=ACCENT_GOLD if "Whiff" in dest or "Cantados" in dest else TEXT_WHITE)
            draw.text((1550, ry), impact, font=f_tbl_row, fill=TEXT_MUTED)

            ry += 55

    # 3. Triple Panel Inferior (Gráficos)
    panel_y0 = 730
    panel_y1 = 1280

    if not is_lvbp and pitch_analysis.get("has_statcast"):
        # Panel 1: Gráfico de Movimiento (IVB vs HB)
        _draw_card_box(draw, (40, panel_y0, 780, panel_y1), radius=16)
        draw.text((70, panel_y0 + 25), "MOVIMIENTO (IVB vs HB)", font=f_tbl_hdr, fill=ACCENT_GOLD)
        _draw_movement_plot(draw, (50, panel_y0 + 60, 770, panel_y1 - 20), pitch_analysis.get("pitches", []))

        # Panel 2: Strike Zone
        _draw_card_box(draw, (820, panel_y0, 1560, panel_y1), radius=16)
        draw.text((850, panel_y0 + 25), "LOCALIZACIÓN EN ZONA DE STRIKE", font=f_tbl_hdr, fill=ACCENT_GOLD)
        _draw_strike_zone_plot(draw, (830, panel_y0 + 60, 1550, panel_y1 - 20), pitch_analysis.get("pitches", []))

        # Panel 3: Inning Workload & LI
        _draw_card_box(draw, (1600, panel_y0, 2360, panel_y1), radius=16)
        draw.text((1630, panel_y0 + 25), "CARGA DE PITCHEO POR ENTRADA", font=f_tbl_hdr, fill=ACCENT_GOLD)
        _draw_workload_bars(draw, (1610, panel_y0 + 60, 2350, panel_y1 - 20), pitch_analysis.get("innings_workload", []))
    else:
        # Panel 1: Carga de Pitcheos por Entrada
        _draw_card_box(draw, (40, panel_y0, 780, panel_y1), radius=16)
        draw.text((70, panel_y0 + 25), "CARGA DE PITCHEO POR ENTRADA", font=f_tbl_hdr, fill=ACCENT_GOLD)
        _draw_workload_bars(draw, (50, panel_y0 + 60, 770, panel_y1 - 20), pitch_analysis.get("innings_workload", []))

        # Panel 2: Apalancamiento (Leverage Index por Entrada)
        _draw_card_box(draw, (820, panel_y0, 1560, panel_y1), radius=16)
        draw.text((850, panel_y0 + 25), "APALANCAMIENTO (LEVERAGE INDEX RE24)", font=f_tbl_hdr, fill=ACCENT_GOLD)
        _draw_leverage_bars(draw, (830, panel_y0 + 60, 1550, panel_y1 - 20), pitch_analysis.get("innings_workload", []))

        # Panel 3: Splits LHB vs RHB
        _draw_card_box(draw, (1600, panel_y0, 2360, panel_y1), radius=16)
        draw.text((1630, panel_y0 + 25), "RENDIMIENTO VS ZURDOS Y DERECHOS", font=f_tbl_hdr, fill=ACCENT_GOLD)
        _draw_platoon_card(draw, (1610, panel_y0 + 60, 2350, panel_y1 - 20), pitch_analysis.get("splits_platoon", {}))

    # 4. Pie de Página y Créditos Institucionales
    f_footer = _load_font(18)
    f_footer_b = _load_font(18, bold=True)
    draw.text((50, 1305), "REPÚBLICA CARAQUISTA • PLATAFORMA ANALÍTICA SABERMÉTRICA • LVBP / MLB", font=f_footer_b, fill=TEXT_MUTED)
    draw.text((1580, 1305), "Autor: Jorge Leonardo Loreto • @republicaraquista • Datos: MLB Stats API / Savant", font=f_footer, fill=TEXT_DIM)

    # Exportar a bytes PNG con metadatos 300 DPI
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=DPI, optimize=True)
    return buf.getvalue()
