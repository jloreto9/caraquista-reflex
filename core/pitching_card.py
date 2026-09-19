# core/pitching_card.py
"""
pitching_card.py
----------------
Generador de resúmenes gráficos de pitcheo (Pitching Summary) para República Caraquista
utilizando el framework y diseño original de Thomas Nestico (@TJStats) en Matplotlib.

Características:
1. Cuadrícula 20x20 (GridSpec 6x8) en fondo blanco pulcro.
2. Cabecera: Headshot oficial del lanzador, Biografía completa y Logo oficial de República Caraquista / Equipo.
3. Tabla Resumen: Métricas de temporada / rango (IP, PA, WHIP, ERA, FIP, K%, BB%, K-BB%) o boxscore de salida.
4. Panel Gráfico Triple:
   - Izquierda: Distribución de velocidades (Velocity KDEs) con medias individuales y de liga (statcast_2024_grouped.csv).
   - Centro: Strike Zone Plot (salida individual) o 5-Game Rolling Pitch Usage (temporada / rango).
   - Derecha: Short-Form Pitch Breaks (quiebre horizontal vs inducido vertical en pulgadas ±25 in con Glove/Arm side).
5. Tabla Sabermétrica de Repertorio:
   - Matriz detallada de lanzamientos con mapas de calor celulares (cmap_sum / cmap_sum_r) comparados contra MLB.
6. Soporte dual adaptativo para Leones del Caracas (LVBP):
   - Misma cuadrícula 20x20 en Matplotlib con Workload por entrada, Leverage Index Tango RE24, Platoon splits y destinos PBP.
7. Créditos oficiales a Thomas Nestico (@TJStats) en el pie de página.
"""

import io
import os
import math
import warnings
import urllib.request
from typing import Dict, List, Any, Tuple, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.ticker as mtick
import seaborn as sns
import pandas as pd
import numpy as np
from PIL import Image

# ── Compatibilidad con la suite de pruebas previa ─────────────────────────────
CANVAS_SIZE = (2400, 2400)
CANVAS_SIZE_LVBP = (2400, 2400)
DPI = (300, 300)

PITCH_COLORS: Dict[str, Tuple[int, int, int]] = {
    "4-Seam Fastball": (210, 45, 73),
    "Four-Seam Fastball": (210, 45, 73),
    "Fastball": (210, 45, 73),
    "Sinker": (254, 157, 0),
    "Cutter": (147, 63, 44),
    "Slider": (238, 231, 22),
    "Sweeper": (221, 179, 59),
    "Curveball": (0, 161, 222),
    "Knuckle Curve": (0, 120, 200),
    "Changeup": (29, 190, 58),
    "Split-Finger": (59, 172, 172),
    "Splitter": (59, 172, 172),
    "Knuckleball": (102, 45, 145),
    "Desconocido": (140, 140, 140),
}

def _get_pitch_color(p_name: str) -> Tuple[int, int, int]:
    for k, v in PITCH_COLORS.items():
        if k.lower() in p_name.lower():
            return v
    return (140, 140, 140)


# ── Paleta y Diccionarios Canónicos de Thomas Nestico (@TJStats) ───────────────
PITCH_COLOURS = {
    'FF': {'colour': '#FF007D', 'name': '4-Seam Fastball'},
    'FA': {'colour': '#FF007D', 'name': 'Fastball'},
    'SI': {'colour': '#98165D', 'name': 'Sinker'},
    'FC': {'colour': '#BE5FA0', 'name': 'Cutter'},
    'CH': {'colour': '#F79E70', 'name': 'Changeup'},
    'FS': {'colour': '#FE6100', 'name': 'Splitter'},
    'SC': {'colour': '#F08223', 'name': 'Screwball'},
    'FO': {'colour': '#FFB000', 'name': 'Forkball'},
    'SL': {'colour': '#67E18D', 'name': 'Slider'},
    'ST': {'colour': '#1BB999', 'name': 'Sweeper'},
    'SV': {'colour': '#376748', 'name': 'Slurve'},
    'KC': {'colour': '#311D8B', 'name': 'Knuckle Curve'},
    'CU': {'colour': '#3025CE', 'name': 'Curveball'},
    'CS': {'colour': '#274BFC', 'name': 'Slow Curve'},
    'EP': {'colour': '#648FFF', 'name': 'Eephus'},
    'KN': {'colour': '#867A08', 'name': 'Knuckleball'},
    'PO': {'colour': '#472C30', 'name': 'Pitch Out'},
    'UN': {'colour': '#9C8975', 'name': 'Unknown'},
}

DICT_COLOUR = {k: v['colour'] for k, v in PITCH_COLOURS.items()}
DICT_PITCH = {k: v['name'] for k, v in PITCH_COLOURS.items()}

# Colormaps para tablas degradadas
CMAP_SUM = mcolors.LinearSegmentedColormap.from_list("", ['#648FFF', '#FFFFFF', '#FFB000'])
CMAP_SUM_R = mcolors.LinearSegmentedColormap.from_list("", ['#FFB000', '#FFFFFF', '#648FFF'])
COLOUR_STATS = ['release_speed', 'release_extension', 'delta_run_exp_per_100', 'whiff_rate', 'in_zone_rate', 'chase_rate', 'xwoba']

PITCH_STATS_DICT = {
    'pitch': {'table_header': r'$\bf{Count}$', 'format': '.0f'},
    'release_speed': {'table_header': r'$\bf{Velocity}$', 'format': '.1f'},
    'pfx_z': {'table_header': r'$\bf{iVB}$', 'format': '.1f'},
    'pfx_x': {'table_header': r'$\bf{HB}$', 'format': '.1f'},
    'release_spin_rate': {'table_header': r'$\bf{Spin}$', 'format': '.0f'},
    'release_pos_x': {'table_header': r'$\bf{hRel}$', 'format': '.1f'},
    'release_pos_z': {'table_header': r'$\bf{vRel}$', 'format': '.1f'},
    'release_extension': {'table_header': r'$\bf{Ext.}$', 'format': '.1f'},
    'xwoba': {'table_header': r'$\bf{xwOBA}$', 'format': '.3f'},
    'pitch_usage': {'table_header': r'$\bf{Pitch\%}$', 'format': '.1%'},
    'whiff_rate': {'table_header': r'$\bf{Whiff\%}$', 'format': '.1%'},
    'in_zone_rate': {'table_header': r'$\bf{Zone\%}$', 'format': '.1%'},
    'chase_rate': {'table_header': r'$\bf{Chase\%}$', 'format': '.1%'},
    'delta_run_exp_per_100': {'table_header': r'$\bf{RV/100}$', 'format': '.1f'},
}

TABLE_COLUMNS = [
    'pitch_description', 'pitch', 'pitch_usage', 'release_speed',
    'pfx_z', 'pfx_x', 'release_spin_rate', 'release_pos_x',
    'release_pos_z', 'release_extension', 'delta_run_exp_per_100',
    'whiff_rate', 'in_zone_rate', 'chase_rate', 'xwoba'
]

BASELINES_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statcast_2024_grouped.csv")
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logo.png")


# ── 1. Funciones Auxiliares de Agrupación y Color ─────────────────────────────

def _clean_team_name(t_name: str) -> str:
    """Normaliza nombres de franquicias de LVBP y LMB México con soporte para variantes con o sin tildes."""
    t = str(t_name or "").replace("vs ", "").strip()
    subs = {
        # LVBP
        "Navegantes del Magallanes": "Magallanes",
        "Leones del Caracas": "Caracas",
        "Tiburones de La Guaira": "La Guaira",
        "Tigres de Aragua": "Aragua",
        "Cardenales de Lara": "Lara",
        "Águilas del Zulia": "Zulia",
        "Aguilas del Zulia": "Zulia",
        "Caribes de Anzoátegui": "Caribes",
        "Caribes de Anzoategui": "Caribes",
        "Bravos de Margarita": "Bravos",
        # LMB México
        "Diablos Rojos del México": "Diablos Rojos",
        "Diablos Rojos del Mexico": "Diablos Rojos",
        "Tecolotes de los Dos Laredos": "Tecolotes",
        "Pericos de Puebla": "Pericos",
        "Tigres de Quintana Roo": "Tigres QR",
        "Piratas de Campeche": "Piratas",
        "El Águila de Veracruz": "El Águila",
        "El Aguila de Veracruz": "El Águila",
        "Conspiradores de Querétaro": "Conspiradores",
        "Conspiradores de Queretaro": "Conspiradores",
        "Saraperos de Saltillo": "Saraperos",
        "Dorados de Chihuahua": "Dorados",
        "Algodoneros del Unión Laguna": "Algodoneros",
        "Algodoneros del Union Laguna": "Algodoneros",
        "Algodoneros Union Laguna": "Algodoneros",
        "Olmecas de Tabasco": "Olmecas",
        "Leones de Yucatán": "Leones YUC",
        "Leones de Yucatan": "Leones YUC",
        "Guerreros de Oaxaca": "Guerreros",
        "Acereros de Monclova": "Acereros",
        "Sultanes de Monterrey": "Sultanes",
        "Toros de Tijuana": "Toros TIJ",
        "Rieleros de Aguascalientes": "Rieleros",
        "Charros de Jalisco": "Charros",
        "Caliente de Durango": "Caliente",
        "Bravos de León": "Bravos LEO",
        "Bravos de Leon": "Bravos LEO",
    }
    return subs.get(t, t[:14])


def _fmt_date_short(d_str: str) -> str:
    """Convierte fecha YYYY-MM-DD a formato DD/MM/YY."""
    parts = str(d_str or "").split('-')
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0][2:]}"
    return str(d_str)


def _ip_str_to_outs(ip_val: Any) -> int:
    """Convierte '5.2' a 17 outs, o 5.0 a 15 outs."""
    try:
        s = str(ip_val).strip()
        if '.' in s:
            parts = s.split('.')
            return int(parts[0]) * 3 + int(parts[1])
        return int(float(s)) * 3
    except Exception:
        return 0


def _outs_to_ip_str(outs: int) -> str:
    """Convierte 17 outs a '5.2'."""
    return f"{outs // 3}.{outs % 3}"


def _load_statcast_group() -> pd.DataFrame:
    if os.path.exists(BASELINES_CSV):
        try:
            return pd.read_csv(BASELINES_CSV)
        except Exception:
            pass
    return pd.DataFrame()


def _get_cell_colors(df_group: pd.DataFrame, df_statcast_group: pd.DataFrame) -> List[List[str]]:
    """Calcula colores hexadecimales de fondo para cada celda de la tabla."""
    colour_list_df = []
    if df_statcast_group is None or df_statcast_group.empty:
        return [['#ffffff'] * len(TABLE_COLUMNS) for _ in range(len(df_group))]

    for pt in df_group['pitch_type'].unique():
        inner = []
        sel_lg = df_statcast_group[df_statcast_group['pitch_type'] == pt]
        sel_p = df_group[df_group['pitch_type'] == pt]

        for col in TABLE_COLUMNS:
            if col in COLOUR_STATS and col in sel_p.columns and not sel_p.empty:
                val = sel_p[col].values[0]
                if pd.isna(val) or type(val) not in (float, np.float64, int, np.int64):
                    inner.append('#ffffff')
                elif col == 'release_speed':
                    lg_mean = pd.to_numeric(sel_lg[col], errors='coerce').mean() if not sel_lg.empty else 90.0
                    norm = mcolors.Normalize(vmin=lg_mean * 0.95, vmax=lg_mean * 1.05)
                    inner.append(mcolors.to_hex(CMAP_SUM(norm(float(val)))))
                elif col == 'delta_run_exp_per_100':
                    norm = mcolors.Normalize(vmin=-1.5, vmax=1.5)
                    inner.append(mcolors.to_hex(CMAP_SUM(norm(float(val)))))
                elif col == 'xwoba':
                    lg_mean = pd.to_numeric(sel_lg[col], errors='coerce').mean() if not sel_lg.empty else 0.300
                    norm = mcolors.Normalize(vmin=lg_mean * 0.7, vmax=lg_mean * 1.3)
                    inner.append(mcolors.to_hex(CMAP_SUM_R(norm(float(val)))))
                else:
                    lg_mean = pd.to_numeric(sel_lg[col], errors='coerce').mean() if not sel_lg.empty else 0.300
                    norm = mcolors.Normalize(vmin=lg_mean * 0.7, vmax=lg_mean * 1.3)
                    inner.append(mcolors.to_hex(CMAP_SUM(norm(float(val)))))
            else:
                inner.append('#ffffff')
        colour_list_df.append(inner)
    return colour_list_df


def _group_pitches(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Agrupa pitcheos por tipo y calcula totales para la fila 'All'."""
    agg_dict = {
        'pitch': ('pitch_type', 'count'),
        'release_speed': ('release_speed', 'mean'),
        'pfx_z': ('pfx_z', 'mean'),
        'pfx_x': ('pfx_x', 'mean'),
        'release_spin_rate': ('release_spin_rate', 'mean') if 'release_spin_rate' in df.columns else ('release_speed', 'count'),
        'release_pos_x': ('release_pos_x', 'mean') if 'release_pos_x' in df.columns else ('release_speed', 'count'),
        'release_pos_z': ('release_pos_z', 'mean') if 'release_pos_z' in df.columns else ('release_speed', 'count'),
        'release_extension': ('release_extension', 'mean') if 'release_extension' in df.columns else ('release_speed', 'count'),
        'delta_run_exp': ('delta_run_exp', 'sum') if 'delta_run_exp' in df.columns else ('pitch_type', 'count'),
        'swing': ('swing', 'sum') if 'swing' in df.columns else ('pitch_type', 'count'),
        'whiff': ('whiff', 'sum') if 'whiff' in df.columns else ('pitch_type', 'count'),
        'in_zone': ('in_zone', 'sum') if 'in_zone' in df.columns else ('pitch_type', 'count'),
        'out_zone': ('out_zone', 'sum') if 'out_zone' in df.columns else ('pitch_type', 'count'),
        'chase': ('chase', 'sum') if 'chase' in df.columns else ('pitch_type', 'count'),
        'xwoba': ('estimated_woba_using_speedangle', 'mean') if 'estimated_woba_using_speedangle' in df.columns else ('pitch_type', 'count'),
    }

    df_group = df.groupby(['pitch_type']).agg(**agg_dict).reset_index()
    df_group['pitch_description'] = df_group['pitch_type'].map(DICT_PITCH).fillna(df_group['pitch_type'])
    total_pitches = max(1, df_group['pitch'].sum())
    df_group['pitch_usage'] = df_group['pitch'] / total_pitches

    swings_total = df_group['swing'].replace(0, np.nan)
    df_group['whiff_rate'] = (df_group['whiff'] / swings_total).fillna(0.0)
    df_group['in_zone_rate'] = (df_group['in_zone'] / df_group['pitch']).fillna(0.0)
    out_zone_total = df_group['out_zone'].replace(0, np.nan)
    df_group['chase_rate'] = (df_group['chase'] / out_zone_total).fillna(0.0)

    if 'delta_run_exp' in df.columns:
        df_group['delta_run_exp_per_100'] = -df_group['delta_run_exp'] / df_group['pitch'] * 100
    else:
        df_group['delta_run_exp_per_100'] = 0.0

    df_group['colour'] = df_group['pitch_type'].map(DICT_COLOUR).fillna('#808080')
    df_group = df_group.sort_values(by='pitch_usage', ascending=False).reset_index(drop=True)
    colour_list = df_group['colour'].tolist()

    # Fila de Resumen General "All"
    ext_mean = df['release_extension'].mean() if 'release_extension' in df.columns else np.nan
    whiff_all = df['whiff'].sum() / max(1, df['swing'].sum()) if 'whiff' in df.columns else 0.0
    in_zone_all = df['in_zone'].sum() / total_pitches if 'in_zone' in df.columns else 0.0
    chase_all = df['chase'].sum() / max(1, df['out_zone'].sum()) if 'chase' in df.columns else 0.0
    xwoba_all = df['estimated_woba_using_speedangle'].mean() if 'estimated_woba_using_speedangle' in df.columns else np.nan
    rv_all = df['delta_run_exp'].sum() / total_pitches * -100 if 'delta_run_exp' in df.columns else 0.0

    plot_all = pd.DataFrame([{
        'pitch_type': 'All',
        'pitch_description': 'All Pitches',
        'pitch': total_pitches,
        'pitch_usage': 1.0,
        'release_speed': df['release_speed'].mean() if 'release_speed' in df.columns else np.nan,
        'pfx_z': np.nan,
        'pfx_x': np.nan,
        'release_spin_rate': df['release_spin_rate'].mean() if 'release_spin_rate' in df.columns else np.nan,
        'release_pos_x': np.nan,
        'release_pos_z': np.nan,
        'release_extension': ext_mean,
        'delta_run_exp_per_100': rv_all,
        'whiff_rate': whiff_all,
        'in_zone_rate': in_zone_all,
        'chase_rate': chase_all,
        'xwoba': xwoba_all,
        'colour': '#070B19',
    }])

    df_plot = pd.concat([df_group, plot_all], ignore_index=True)
    return df_plot, colour_list


def _format_table_df(df_plot: pd.DataFrame) -> pd.DataFrame:
    """Aplica formato de números y porcentajes según las especificaciones de Nestico."""
    df_fmt = df_plot[TABLE_COLUMNS].copy()
    for col, props in PITCH_STATS_DICT.items():
        if col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(
                lambda x: format(x, props['format']) if isinstance(x, (int, float, np.number)) and not np.isnan(x) else ('—' if pd.isna(x) else x)
            )
    return df_fmt.fillna('—')


# ── 2. Componentes Visuales del Pitching Summary (Matplotlib) ─────────────────

def _plot_headshot(ax: plt.Axes, photo_url: Optional[str]):
    ax.axis('off')
    img = None
    if photo_url:
        try:
            req = urllib.request.Request(photo_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                img = Image.open(io.BytesIO(resp.read()))
        except Exception:
            img = None

    if img is None and os.path.exists(LOGO_PATH):
        try:
            img = Image.open(LOGO_PATH)
        except Exception:
            pass

    if img is not None:
        ax.set_xlim(0, 1.0)
        ax.set_ylim(0, 1.0)
        ax.imshow(img, extent=[0.0, 1.0, 0.0, 1.0], origin='upper')


def _plot_bio(ax: plt.Axes, pitcher_info: Dict[str, Any], subtitle_line1: str, subtitle_line2: str):
    ax.axis('off')
    p_name = pitcher_info.get("name", "Pitcher")
    throws = pitcher_info.get("throws", "R")
    age = pitcher_info.get("age", 28)
    height = pitcher_info.get("height", "6' 2\"")
    weight = pitcher_info.get("weight", 200)

    ax.text(0.5, 0.88, f"{p_name}", va='top', ha='center', fontsize=36, fontweight='bold', color='#070B19')
    ax.text(0.5, 0.62, f"{throws}HP • Edad: {age} • {height} / {weight} lbs", va='top', ha='center', fontsize=18, color='#475569')

    # Subtítulos con tamaño y ajuste adaptable para evitar desborde
    fs_sub1 = 20 if len(subtitle_line1) <= 35 else (17 if len(subtitle_line1) <= 45 else 15)
    ax.text(0.5, 0.38, f"{subtitle_line1}", va='top', ha='center', fontsize=fs_sub1, fontweight='bold', color='#D97706')

    fs_sub2 = 16 if len(subtitle_line2) <= 35 else 14
    ax.text(0.5, 0.16, f"{subtitle_line2}", va='top', ha='center', fontsize=fs_sub2, fontstyle='italic', color='#64748B')


def _plot_logo(ax: plt.Axes):
    """Renderiza el logo oficial de República Caraquista en la esquina superior derecha."""
    ax.axis('off')
    if os.path.exists(LOGO_PATH):
        try:
            img = Image.open(LOGO_PATH)
            ax.set_xlim(0, 1.0)
            ax.set_ylim(0, 1.0)
            ax.imshow(img, extent=[0.0, 1.0, 0.0, 1.0], origin='upper')
            return
        except Exception:
            pass
    ax.text(0.5, 0.5, "REPÚBLICA\nCARAQUISTA", ha='center', va='center', fontsize=18, fontweight='bold', color='#D97706')


def _plot_summary_table(ax: plt.Axes, stats_data: Dict[str, Any], is_game: bool):
    """Muestra la tabla compacta superior de resumen de temporada o salida."""
    ax.axis('off')
    if is_game:
        cols = ['IP', 'H', 'R', 'ER', 'BB', 'SO', 'PITCHES', 'CSW%']
        vals = [
            str(stats_data.get('ip', '0.0')),
            str(stats_data.get('h', 0)),
            str(stats_data.get('r', 0)),
            str(stats_data.get('er', 0)),
            str(stats_data.get('bb', 0)),
            str(stats_data.get('so', 0)),
            str(stats_data.get('pitches', 0)),
            str(stats_data.get('csw_pct', '—')),
        ]
    else:
        cols = ['IP', 'PA', 'WHIP', 'ERA', 'FIP', 'K%', 'BB%', 'K-BB%']
        vals = [
            str(stats_data.get('ip', '—')),
            str(stats_data.get('pa', '—')),
            str(stats_data.get('whip', '—')),
            str(stats_data.get('era', '—')),
            str(stats_data.get('fip', '—')),
            str(stats_data.get('k_pct', '—')),
            str(stats_data.get('bb_pct', '—')),
            str(stats_data.get('k_bb_pct', '—')),
        ]

    tbl = ax.table(
        cellText=[vals],
        colLabels=cols,
        cellLoc='center',
        bbox=[0.0, 0.0, 1.0, 1.0]
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(18)
    for i in range(len(cols)):
        tbl.get_celld()[(0, i)].set_facecolor('#0F172A')
        tbl.get_celld()[(0, i)].get_text().set_color('#FDB827')
        tbl.get_celld()[(0, i)].get_text().set_fontweight('bold')
        tbl.get_celld()[(1, i)].set_facecolor('#F8FAFC')
        tbl.get_celld()[(1, i)].get_text().set_fontweight('bold')


def _plot_velocity_kdes(df: pd.DataFrame, ax: plt.Axes, subplot_spec: Any, fig: plt.Figure, df_statcast_group: pd.DataFrame):
    """Genera las curvas de densidad KDE de velocidad por tipo de lanzamiento."""
    ax.axis('off')
    ax.set_title('Pitch Velocity Distribution', fontdict={'size': 16, 'weight': 'bold', 'color': '#070B19'}, pad=10)

    counts = df['pitch_type'].value_counts()
    items = counts.index.tolist()
    if not items:
        return

    inner_grid = gridspec.GridSpecFromSubplotSpec(len(items), 1, subplot_spec=subplot_spec)
    ax_top = []
    for inner in inner_grid:
        ax_top.append(fig.add_subplot(inner))

    speeds_all = df['release_speed'].dropna()
    min_lim = math.floor(speeds_all.min() / 5) * 5 if not speeds_all.empty else 75
    max_lim = math.ceil(speeds_all.max() / 5) * 5 if not speeds_all.empty else 105
    min_lim = max(60, min_lim)
    max_lim = min(110, max(max_lim, min_lim + 10))

    for idx, pt in enumerate(items):
        cur_ax = ax_top[idx]
        pt_speeds = df[df['pitch_type'] == pt]['release_speed'].dropna()
        p_color = DICT_COLOUR.get(pt, '#808080')

        if pt_speeds.empty:
            continue

        if pt_speeds.nunique() <= 1:
            val = pt_speeds.iloc[0]
            cur_ax.plot([val, val], [0, 1], linewidth=4, color=p_color, zorder=20)
        else:
            sns.kdeplot(pt_speeds, ax=cur_ax, fill=True, clip=(pt_speeds.min(), pt_speeds.max()), color=p_color)

        # Media individual
        m_speed = pt_speeds.mean()
        ylim = cur_ax.get_ylim()
        cur_ax.plot([m_speed, m_speed], [ylim[0], ylim[1]], color=p_color, linestyle='--', linewidth=2)

        # Media de la liga
        if df_statcast_group is not None and not df_statcast_group.empty:
            lg_sel = df_statcast_group[df_statcast_group['pitch_type'] == pt]
            if not lg_sel.empty and 'release_speed' in lg_sel.columns:
                lg_speed = float(lg_sel['release_speed'].iloc[0])
                cur_ax.plot([lg_speed, lg_speed], [ylim[0], ylim[1]], color='#1E293B', linestyle=':', linewidth=2)

        cur_ax.set_xlim(min_lim, max_lim)
        cur_ax.set_xlabel('')
        cur_ax.set_ylabel('')
        cur_ax.spines['top'].set_visible(False)
        cur_ax.spines['right'].set_visible(False)
        cur_ax.spines['left'].set_visible(False)

        if idx < len(items) - 1:
            cur_ax.tick_params(axis='x', colors='none')

        cur_ax.set_xticks(range(int(min_lim), int(max_lim), 5))
        cur_ax.set_yticks([])
        cur_ax.grid(axis='x', linestyle='--', alpha=0.4)
        cur_ax.text(-0.01, 0.5, pt, transform=cur_ax.transAxes, fontsize=13, va='center', ha='right', fontweight='bold', color=p_color)

    if ax_top:
        ax_top[-1].set_xlabel('Velocity (mph)', fontsize=14, fontweight='bold', color='#070B19')


def _plot_strike_zone(df: pd.DataFrame, ax: plt.Axes):
    """Renderiza el scatter de pitcheos sobre la zona de strike 3x3 para salidas individuales."""
    for pt in df['pitch_type'].unique():
        pt_df = df[df['pitch_type'] == pt]
        ax.scatter(
            pt_df['plate_x'], pt_df['plate_z'],
            color=DICT_COLOUR.get(pt, '#808080'),
            edgecolors='black', alpha=0.85, s=75, label=pt, zorder=3
        )

    # Cajón de strike zone
    sz_b = float(df['sz_bot'].median()) if 'sz_bot' in df.columns and df['sz_bot'].notnull().any() else 1.5
    sz_t = float(df['sz_top'].median()) if 'sz_top' in df.columns and df['sz_top'].notnull().any() else 3.5
    sz_w = 17.0 / 12.0
    sz_l = -sz_w / 2.0

    rect = patches.Rectangle((sz_l, sz_b), sz_w, sz_t - sz_b, linewidth=2.5, edgecolor='#0F172A', facecolor='none', zorder=2)
    ax.add_patch(rect)

    # Rejilla 3x3
    w_third = sz_w / 3.0
    h_third = (sz_t - sz_b) / 3.0
    for c in range(1, 3):
        ax.plot([sz_l + c * w_third, sz_l + c * w_third], [sz_b, sz_t], color='#64748B', linestyle=':', linewidth=1.2, zorder=2)
    for r in range(1, 3):
        ax.plot([sz_l, sz_l + sz_w], [sz_b + r * h_third, sz_b + r * h_third], color='#64748B', linestyle=':', linewidth=1.2, zorder=2)

    # Home plate
    plate = patches.Polygon([[-0.708, 0], [0.708, 0], [0.708, -0.2], [0, -0.4], [-0.708, -0.2]],
                            closed=True, facecolor='#CBD5E1', edgecolor='#0F172A', linewidth=1.5, zorder=2)
    ax.add_patch(plate)

    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-0.5, 4.5)
    ax.set_xlabel('Horizontal Plate Location (ft)', fontsize=15, fontweight='bold', color='#070B19')
    ax.set_ylabel('Vertical Plate Location (ft)', fontsize=15, fontweight='bold', color='#070B19')
    ax.set_title('Pitch Locations & Strike Zone', fontsize=20, fontweight='bold', color='#070B19')
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, linestyle='--', alpha=0.3)


def _plot_rolling_usage(df: pd.DataFrame, ax: plt.Axes, window: int = 5):
    """Renderiza el gráfico de evolución continua de uso (Rolling Usage) para temporada / rango."""
    if 'game_date' not in df.columns or df['game_date'].nunique() < 2:
        _plot_strike_zone(df, ax)
        return

    df_game = df.groupby(['game_pk', 'game_date', 'pitch_type'])['release_speed'].count().reset_index()
    tot_per_game = df.groupby(['game_pk', 'game_date'])['release_speed'].count().reset_index(name='tot')
    merged = pd.merge(df_game, tot_per_game, on=['game_pk', 'game_date'])
    merged['usage'] = merged['release_speed'] / merged['tot']

    all_games = df.sort_values(by='game_date')['game_pk'].unique()
    all_types = df['pitch_type'].unique()
    full_idx = pd.MultiIndex.from_product([all_games, all_types], names=['game_pk', 'pitch_type']).to_frame(index=False)
    comp = pd.merge(full_idx, merged, on=['game_pk', 'pitch_type'], how='left')
    comp['usage'] = comp['usage'].fillna(0.0)

    game_order = {g: idx + 1 for idx, g in enumerate(all_games)}
    comp['game_number'] = comp['game_pk'].map(game_order)
    comp = comp.sort_values(by='game_number')

    counts = df['pitch_type'].value_counts()
    max_roll = 0.5
    for pt in counts.index:
        pt_data = comp[comp['pitch_type'] == pt].sort_values(by='game_number')
        roll_vals = pt_data['usage'].rolling(window, min_periods=1).mean()
        if not roll_vals.empty:
            max_roll = max(max_roll, roll_vals.max())
            ax.plot(pt_data['game_number'], roll_vals, color=DICT_COLOUR.get(pt, '#808080'), linewidth=3, label=pt)

    ax.set_xlim(1, max(1, len(all_games)))
    ax.set_ylim(0, min(1.0, math.ceil(max_roll * 10) / 10 + 0.05))
    ax.set_xlabel('Game Number', fontsize=15, fontweight='bold', color='#070B19')
    ax.set_ylabel('Pitch Usage', fontsize=15, fontweight='bold', color='#070B19')
    ax.set_title(f"{window}-Game Rolling Pitch Usage", fontsize=20, fontweight='bold', color='#070B19')
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0, decimals=0))
    ax.grid(axis='both', linestyle='--', alpha=0.4)


def _plot_breaks(df: pd.DataFrame, ax: plt.Axes):
    """Renderiza el gráfico sabermétrico Short-Form Pitch Breaks (iVB vs HB en pulgadas)."""
    p_throws = 'R'
    if 'p_throws' in df.columns and not df['p_throws'].dropna().empty:
        p_throws = str(df['p_throws'].iloc[0]).upper()

    for pt in df['pitch_type'].unique():
        pt_df = df[df['pitch_type'] == pt]
        x_val = pt_df['pfx_x'] * -1 if p_throws == 'R' else pt_df['pfx_x']
        y_val = pt_df['pfx_z']
        ax.scatter(
            x_val, y_val,
            color=DICT_COLOUR.get(pt, '#808080'),
            edgecolors='black', alpha=0.85, s=65, label=pt, zorder=2
        )

    ax.axhline(y=0, color='#64748B', alpha=0.6, linestyle='--', zorder=1)
    ax.axvline(x=0, color='#64748B', alpha=0.6, linestyle='--', zorder=1)
    ax.set_xlabel('Horizontal Break (in)', fontsize=15, fontweight='bold', color='#070B19')
    ax.set_ylabel('Induced Vertical Break (in)', fontsize=15, fontweight='bold', color='#070B19')
    ax.set_title("Pitch Breaks", fontsize=20, fontweight='bold', color='#070B19')
    ax.set_xlim((-25, 25))
    ax.set_ylim((-25, 25))
    ax.set_xticks(range(-20, 21, 10))
    ax.set_yticks(range(-20, 21, 10))

    if p_throws == 'R':
        ax.text(-24.0, -24.0, s='← Glove Side', fontstyle='italic', ha='left', va='bottom',
                bbox=dict(facecolor='white', edgecolor='#0F172A', boxstyle='round,pad=0.3'), fontsize=11, zorder=3)
        ax.text(24.0, -24.0, s='Arm Side →', fontstyle='italic', ha='right', va='bottom',
                bbox=dict(facecolor='white', edgecolor='#0F172A', boxstyle='round,pad=0.3'), fontsize=11, zorder=3)
    else:
        ax.invert_xaxis()
        ax.text(24.0, -24.0, s='← Arm Side', fontstyle='italic', ha='left', va='bottom',
                bbox=dict(facecolor='white', edgecolor='#0F172A', boxstyle='round,pad=0.3'), fontsize=11, zorder=3)
        ax.text(-24.0, -24.0, s='Glove Side →', fontstyle='italic', ha='right', va='bottom',
                bbox=dict(facecolor='white', edgecolor='#0F172A', boxstyle='round,pad=0.3'), fontsize=11, zorder=3)

    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, linestyle='--', alpha=0.3)


def _plot_pitch_table(df: pd.DataFrame, ax: plt.Axes, df_statcast_group: pd.DataFrame, fontsize: int = 15):
    """Construye la tabla sabermétrica con celdas degradadas por mapa de calor."""
    ax.axis('off')
    df_plot, colour_list = _group_pitches(df)
    colour_cells = _get_cell_colors(df_plot, df_statcast_group)
    df_fmt = _format_table_df(df_plot)

    table_plot = ax.table(
        cellText=df_fmt.values,
        colLabels=TABLE_COLUMNS,
        cellLoc='center',
        bbox=[0.0, -0.05, 1.0, 1.05],
        colWidths=[2.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        cellColours=colour_cells
    )
    table_plot.auto_set_font_size(False)
    table_plot.set_fontsize(fontsize)
    table_plot.scale(1, 0.5)

    new_headers = [r'$\bf{Pitch\ Name}$'] + [
        PITCH_STATS_DICT[c]['table_header'] if c in PITCH_STATS_DICT else '---'
        for c in TABLE_COLUMNS[1:]
    ]

    for i, col_name in enumerate(new_headers):
        cell = table_plot.get_celld()[(0, i)]
        cell.get_text().set_text(col_name)
        cell.set_facecolor('#0F172A')
        cell.get_text().set_color('#FDB827')
        cell.get_text().set_fontweight('bold')

    # Resaltar la primera columna con el color del tipo de lanzamiento
    for i in range(len(df_fmt)):
        row_idx = i + 1
        cell_0 = table_plot.get_celld()[(row_idx, 0)]
        cell_0.get_text().set_fontweight('bold')
        if row_idx <= len(colour_list):
            cell_0.set_facecolor(colour_list[row_idx - 1])
            txt = cell_0.get_text().get_text()
            if txt in ['Split-Finger', 'Slider', 'Changeup', 'Splitter']:
                cell_0.set_text_props(color='#000000', fontweight='bold')
            else:
                cell_0.set_text_props(color='#FFFFFF', fontweight='bold')
        else:
            # Fila "All"
            cell_0.set_facecolor('#0F172A')
            cell_0.set_text_props(color='#FDB827', fontweight='bold')


def _plot_footer(ax: plt.Axes, is_lvbp: bool = False):
    """Muestra el pie de página oficial con atribución y créditos claros sin solapamientos."""
    ax.axis('off')
    # Izquierda: Branding República Caraquista
    ax.text(0.0, 0.72, 'República Caraquista', ha='left', va='center', fontsize=18, fontweight='bold', color='#070B19')
    ax.text(0.0, 0.28, '@republicaraquista • Jorge Leonardo Loreto', ha='left', va='center', fontsize=13, color='#64748B')

    # Derecha: Créditos y Fuentes
    ax.text(1.0, 0.72, 'Diseño inspirado en Thomas Nestico (@TJStats)', ha='right', va='center', fontsize=14, fontweight='bold', color='#070B19')
    src_data = 'Data: MLB Stats API / Gameday PBP' if is_lvbp else 'Data: MLB Statcast / Baseball Savant'
    ax.text(1.0, 0.28, src_data, ha='right', va='center', fontsize=13, color='#64748B')


# ── 3. Generador Principal de Pitching Summary en Matplotlib ──────────────────

def build_nestico_pitching_summary(
    df: pd.DataFrame,
    pitcher_info: Dict[str, Any],
    mode: str = "game",
    season: int = 2024,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    game_summary: Optional[Dict[str, Any]] = None,
    stats_data: Optional[Dict[str, Any]] = None,
    game_logs: Optional[List[Dict[str, Any]]] = None,
    dpi: int = 180,
) -> bytes:
    """
    Construye la imagen completa de Pitching Summary en Matplotlib (20x20)
    siguiendo la metodología de Thomas Nestico (@TJStats) y branding de República Caraquista.
    """
    if df is None or df.empty:
        # Generar tarjeta vacía con aviso
        fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
        ax.axis('off')
        ax.text(0.5, 0.5, "No se encontraron lanzamientos Statcast para este período.", ha='center', va='center', fontsize=20, color='#64748B')
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        return buf.getvalue()

    df_statcast_group = _load_statcast_group()

    fig = plt.figure(figsize=(20, 20), facecolor='white')
    gs = gridspec.GridSpec(
        6, 8,
        height_ratios=[2, 20, 9, 36, 36, 7],
        width_ratios=[1, 18, 18, 18, 18, 18, 18, 1]
    )

    ax_headshot = fig.add_subplot(gs[1, 1])
    ax_bio = fig.add_subplot(gs[1, 2:6])
    ax_logo = fig.add_subplot(gs[1, 6])

    ax_season_table = fig.add_subplot(gs[2, 1:7])

    gs_plots = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[3, 1:7], wspace=0.36)
    ax_plot_1 = fig.add_subplot(gs_plots[0, 0])
    ax_plot_2 = fig.add_subplot(gs_plots[0, 1])
    ax_plot_3 = fig.add_subplot(gs_plots[0, 2])

    ax_table = fig.add_subplot(gs[4, 1:7])
    ax_footer = fig.add_subplot(gs[-1, 1:7])

    # Subtítulos según modo
    if mode == "game":
        opp = _clean_team_name((game_summary or {}).get("opponent", "Rival"))
        dt = (game_summary or {}).get("date", "")
        sub1 = f"Salida Individual vs {opp}"
        sub2 = f"Fecha: {dt}"
    elif mode == "season":
        sub1 = "Resumen de Temporada Completa"
        sub2 = f"Temporada {season} MLB"
    else:
        s = start_date or f"{season}-04-01"
        e = end_date or f"{season}-06-30"
        sub1 = "Resumen por Rango de Fechas"
        sub2 = f"{s} al {e}"

    # Renderizar subplots
    _plot_headshot(ax_headshot, pitcher_info.get("photo_url"))
    _plot_bio(ax_bio, pitcher_info, sub1, sub2)
    _plot_logo(ax_logo)

    # Tabla resumen de métricas
    _calc_and_plot_summary_table(
        ax_season_table, df, mode, stats_data, game_summary,
        game_logs=game_logs, start_date=start_date, end_date=end_date
    )

    # Panel triple
    _plot_velocity_kdes(df, ax_plot_1, gs_plots[0, 0], fig, df_statcast_group)

    if mode == "game" or df['game_date'].nunique() < 3:
        _plot_strike_zone(df, ax_plot_2)
    else:
        _plot_rolling_usage(df, ax_plot_2, window=5)

    _plot_breaks(df, ax_plot_3)

    # Tabla de repertorio
    _plot_pitch_table(df, ax_table, df_statcast_group, fontsize=15)

    # Footer con atribución
    _plot_footer(ax_footer)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return buf.getvalue()


def _calc_and_plot_summary_table(
    ax: plt.Axes,
    df: pd.DataFrame,
    mode: str,
    stats_data: Optional[Dict[str, Any]],
    game_summary: Optional[Dict[str, Any]],
    game_logs: Optional[List[Dict[str, Any]]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Calcula o formatea las estadísticas para la barra resumen."""
    if mode == "game" and game_summary:
        st = {
            'ip': game_summary.get('ip', '—'),
            'h': game_summary.get('h', 0),
            'r': game_summary.get('r', 0),
            'er': game_summary.get('er', 0),
            'bb': game_summary.get('bb', 0),
            'so': game_summary.get('so', 0),
            'pitches': game_summary.get('pitches', len(df)),
            'csw_pct': _calc_csw_pct(df),
        }
        _plot_summary_table(ax, st, is_game=True)
    else:
        # Calcular desde df si stats_data no está provisto
        tot_pitches = len(df)
        pa_events = df[df['events'].notnull()] if 'events' in df.columns else pd.DataFrame()
        tbf = len(pa_events) if not pa_events.empty else max(1, tot_pitches // 4)
        so = len(df[df['events'].str.contains('strikeout', na=False)]) if 'events' in df.columns else 0
        bb = len(df[df['events'] == 'walk']) if 'events' in df.columns else 0
        k_pct = f"{round(so / max(1, tbf) * 100.0, 1)}%"
        bb_pct = f"{round(bb / max(1, tbf) * 100.0, 1)}%"
        k_bb = f"{round((so - bb) / max(1, tbf) * 100.0, 1)}%"

        calc_whip = (stats_data or {}).get('whip', '—')
        calc_era = (stats_data or {}).get('era', '—')
        calc_fip = (stats_data or {}).get('fip', '—')
        calc_ip = (stats_data or {}).get('ip')

        if game_logs and (calc_whip in (None, '—') or calc_era in (None, '—')):
            m_logs = list(game_logs)
            if mode == "range" and start_date and end_date:
                m_logs = [g for g in m_logs if str(start_date) <= str(g.get("date", "")) <= str(end_date)]
            if m_logs:
                tot_outs = sum(_ip_str_to_outs(g.get("ip", "0.0")) for g in m_logs)
                float_ip = tot_outs / 3.0
                tot_er = sum(int(g.get("er") or 0) for g in m_logs)
                tot_bb = sum(int(g.get("bb") or 0) for g in m_logs)
                tot_h = sum(int(g.get("h") or 0) for g in m_logs)
                tot_so = sum(int(g.get("so") or 0) for g in m_logs)
                tot_hr = sum(int(g.get("hr") or 0) for g in m_logs)
                if float_ip > 0:
                    calc_era = f"{(tot_er * 9.0 / float_ip):.2f}"
                    calc_whip = f"{((tot_bb + tot_h) / float_ip):.2f}"
                    calc_fip = f"{(((13 * tot_hr + 3 * tot_bb - 2 * tot_so) / float_ip) + 3.10):.2f}"
                    calc_ip = f"{tot_outs // 3}.{tot_outs % 3}"

        st = {
            'ip': calc_ip or (stats_data or {}).get('ip', f"{tot_pitches // 15}.0"),
            'pa': (stats_data or {}).get('tbf', tbf),
            'whip': calc_whip,
            'era': calc_era,
            'fip': calc_fip,
            'k_pct': (stats_data or {}).get('k_pct', k_pct),
            'bb_pct': (stats_data or {}).get('bb_pct', bb_pct),
            'k_bb_pct': (stats_data or {}).get('k_bb_pct', k_bb),
        }
        _plot_summary_table(ax, st, is_game=False)


def _calc_csw_pct(df: pd.DataFrame) -> str:
    called = df[df['description'] == 'called_strike'].shape[0] if 'description' in df.columns else 0
    whiffs = df['whiff'].sum() if 'whiff' in df.columns else 0
    tot = max(1, len(df))
    return f"{round((called + whiffs) / tot * 100.0, 1)}%"


# ── 4. Soporte Adaptativo para Leones del Caracas (LVBP) ──────────────────────

def build_lvbp_matplotlib_summary(
    pitcher_info: Dict[str, Any],
    game_summary: Optional[Dict[str, Any]] = None,
    analysis: Optional[Dict[str, Any]] = None,
    season: int = 2025,
    dpi: int = 180,
    mode: str = "game",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    game_logs: Optional[List[Dict[str, Any]]] = None,
    phase: str = "all",
    is_mexico: bool = False,
) -> bytes:
    """
    Construye la tarjeta Matplotlib 20x20 adaptada para Leones del Caracas / LVBP / México.
    Soporta modo salida individual ('game'), temporada completa ('season') o rango de fechas ('range'),
    y filtrado por fase de campeonato ('R', 'L', 'F', 'P', 'all').
    """
    game_summary = game_summary or {}
    analysis = analysis or {}

    # Si es modo temporada completa o rango de fechas
    if mode in ("season", "range"):
        logs = list(game_logs or [])
        if is_mexico:
            mex_team = None
            if logs:
                teams = [g.get("team") for g in logs if g.get("team") and g.get("team") not in ("Liga Mexicana", "Rival")]
                if teams:
                    mex_team = max(set(teams), key=teams.count)
            if not mex_team and game_summary:
                mex_team = game_summary.get("team")
            if not mex_team:
                mex_team = pitcher_info.get("team") or "Diablos Rojos"
            team_label = _clean_team_name(mex_team)
        else:
            team_label = pitcher_info.get("lvbp_team_name") or pitcher_info.get("team") or "Leones del Caracas"

        if is_mexico:
            phase_labels = {
                "R": "Temporada Regular",
                "P": "Postemporada",
                "L": "Postemporada",
                "F": "Serie Final",
                "all": "Temporada Completa",
            }
        else:
            phase_labels = {
                "R": "Temporada Regular",
                "L": "Round Robin",
                "F": "Serie Final",
                "all": "Temporada Completa",
            }
        phase_txt = phase_labels.get(phase, "Temporada Completa")

        if phase and phase != "all":
            if is_mexico and phase == "P":
                logs = [g for g in logs if g.get("game_type") in ("P", "L", "W", "D", "F") or g.get("phase") in ("P", "L", "W", "D", "F")]
            else:
                logs = [g for g in logs if g.get("game_type") == phase or g.get("phase") == phase]

        league_title = "México" if is_mexico else "LVBP"
        if mode == "range":
            s_d = str(start_date) if start_date else (f"{season}-04-01" if is_mexico else f"{season}-10-01")
            e_d = str(end_date) if end_date else (f"{season}-09-30" if is_mexico else f"{season}-12-31")
            logs = [g for g in logs if s_d <= str(g.get("date", "")) <= e_d]
            sub1 = f"{league_title} • Resumen por Rango ({phase_txt})"
            sub2 = f"{team_label} | {s_d} al {e_d}"
        else:
            sub1 = f"{league_title} • {phase_txt}"
            season_prefix = "LMB Verano " if is_mexico else "Temporada "
            sub2 = f"{team_label} | {season_prefix}{season}"

        if not logs:
            fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
            ax.axis('off')
            ax.text(0.5, 0.5, f"No se encontraron salidas registradas para {phase_txt.lower()}.", ha='center', va='center', fontsize=20, color='#64748B')
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            return buf.getvalue()

        # Enriquecer logs con telemetría pitcheo a pitcheo para Whiff% y CSW% si faltan
        needs_pbp = any(g.get('csw_pct') is None or g.get('whiff_pct') is None or not g.get('pitches') for g in logs)
        if needs_pbp and pitcher_info.get("id"):
            from concurrent.futures import ThreadPoolExecutor
            p_id_int = pitcher_info["id"]
            def _enrich_log(g):
                gpk = g.get('game_pk')
                if gpk and (g.get('csw_pct') is None or g.get('whiff_pct') is None or not g.get('pitches')):
                    try:
                        try:
                            from utils.pitching_engine import get_game_pitch_data
                        except ImportError:
                            from core.pitching_engine import get_game_pitch_data
                        p_data = get_game_pitch_data(gpk, p_id_int, is_lvbp=True)
                        kpis = p_data.get('pbp_kpis', {})
                        tot_p = g.get('pitches') or p_data.get('total_pitches', 0)
                        strk = g.get('strikes') or kpis.get('strikes') or int(tot_p * 0.62)
                        csw = float(str(kpis.get('csw_pct', '0%')).replace('%', ''))
                        whiff = float(str(kpis.get('whiff_pct', '0%')).replace('%', ''))
                        g['pitches'] = tot_p
                        g['strikes'] = strk
                        g['csw_pct'] = csw
                        g['whiff_pct'] = whiff
                        if 'is_starter' in p_data and p_data.get('is_starter') is not None:
                            g['is_starter'] = p_data['is_starter']
                            g['role'] = 'Abridor' if p_data['is_starter'] else 'Relevista'
                        if (not g.get('decision') or g.get('decision') in ('—', '-', 'None')) and p_data.get('decision'):
                            g['decision'] = p_data['decision']
                    except Exception:
                        pass
                return g

            with ThreadPoolExecutor(max_workers=6) as ex:
                logs = list(ex.map(_enrich_log, logs))

        fig = plt.figure(figsize=(20, 20), facecolor='white')
        gs = gridspec.GridSpec(
            7, 8,
            height_ratios=[2, 18, 7, 36, 4, 27, 5],
            width_ratios=[1, 18, 18, 18, 18, 18, 18, 1]
        )

        ax_headshot = fig.add_subplot(gs[1, 1])
        ax_bio = fig.add_subplot(gs[1, 2:6])
        ax_logo = fig.add_subplot(gs[1, 6])
        ax_season_table = fig.add_subplot(gs[2, 1:7])

        gs_plots = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[3, 1:7], wspace=0.36)
        ax_plot_1 = fig.add_subplot(gs_plots[0, 0])
        ax_plot_2 = fig.add_subplot(gs_plots[0, 1])
        ax_plot_3 = fig.add_subplot(gs_plots[0, 2])

        # gs[4] es un espaciador vertical de 4 unidades para aislar los labels a 45° del eje X
        ax_table = fig.add_subplot(gs[5, 1:7])
        ax_footer = fig.add_subplot(gs[6, 1:7])

        _plot_headshot(ax_headshot, pitcher_info.get("photo_url"))
        _plot_bio(ax_bio, pitcher_info, sub1, sub2)
        _plot_logo(ax_logo)

        # Cómputo agregado de temporada / rango
        tot_outs = sum(_ip_str_to_outs(g.get("ip", "0.0")) for g in logs)
        tot_ip_str = _outs_to_ip_str(tot_outs)
        float_ip = tot_outs / 3.0
        tot_games = len(logs)
        tot_h = sum(int(g.get("h") or 0) for g in logs)
        tot_r = sum(int(g.get("r") or 0) for g in logs)
        tot_er = sum(int(g.get("er") or 0) for g in logs)
        tot_bb = sum(int(g.get("bb") or 0) for g in logs)
        tot_so = sum(int(g.get("so") or 0) for g in logs)
        tot_pitches = sum(int(g.get("pitches") or 0) for g in logs)

        era_val = f"{(tot_er * 9.0 / float_ip):.2f}" if float_ip > 0 else "0.00"
        whip_val = f"{((tot_bb + tot_h) / float_ip):.2f}" if float_ip > 0 else "0.00"
        csw_season = f"{(sum(float(g.get('csw_pct', 0)) * int(g.get('pitches', 0)) for g in logs) / tot_pitches):.1f}%" if tot_pitches > 0 else "0.0%"
        whiff_season = f"{(sum(float(g.get('whiff_pct', 0)) * int(g.get('pitches', 0)) for g in logs) / tot_pitches):.1f}%" if tot_pitches > 0 else "0.0%"

        # Barra superior de KPIs resumidos
        cols_sum = ['IP', 'JUEGOS', 'WHIP', 'ERA', 'SO (K)', 'BB', 'PITCHES', 'CSW%', 'Whiff%']
        vals_sum = [tot_ip_str, str(tot_games), whip_val, era_val, str(tot_so), str(tot_bb), str(tot_pitches), csw_season, whiff_season]

        ax_season_table.axis('off')
        tbl = ax_season_table.table(
            cellText=[vals_sum],
            colLabels=cols_sum,
            cellLoc='center',
            bbox=[0.0, 0.0, 1.0, 1.0]
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(16)
        for i in range(len(cols_sum)):
            tbl.get_celld()[(0, i)].set_facecolor('#0F172A')
            tbl.get_celld()[(0, i)].get_text().set_color('#FDB827')
            tbl.get_celld()[(0, i)].get_text().set_fontweight('bold')
            tbl.get_celld()[(1, i)].set_facecolor('#F8FAFC')
            tbl.get_celld()[(1, i)].get_text().set_fontweight('bold')

        # Ordenar cronológicamente para los gráficos
        sorted_logs = sorted(logs, key=lambda x: str(x.get('date', '')))
        plot_logs = sorted_logs[-10:] if len(sorted_logs) > 10 else sorted_logs
        x_indices = list(range(len(plot_logs)))
        date_labels = [str(g.get('date', ''))[-5:].replace('-', '/') for g in plot_logs]

        # ── Plot 1: Bolas y Strikes por Salida ──────────────────────────────────
        p_counts = [int(g.get('pitches') or 0) for g in plot_logs]
        strks = [int(g.get('strikes') or int(p * 0.62)) for g, p in zip(plot_logs, p_counts)]
        bolas = [max(0, p - s) for p, s in zip(p_counts, strks)]

        ax_plot_1.bar(x_indices, strks, color='#002D62', edgecolor='#0F172A', label='Strikes', width=0.55)
        ax_plot_1.bar(x_indices, bolas, bottom=strks, color='#FDB827', edgecolor='#0F172A', label='Bolas', width=0.55)
        for idx, tot in zip(x_indices, p_counts):
            if tot > 0:
                ax_plot_1.text(idx, tot + 1.2, str(tot), ha='center', va='bottom', fontsize=10, fontweight='bold', color='#070B19')
        ax_plot_1.set_xticks(x_indices)
        ax_plot_1.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=11, fontweight='bold')
        ax_plot_1.set_ylim(0, max(p_counts) * 1.22 if p_counts and max(p_counts) > 0 else 30)
        ax_plot_1.set_ylabel('Conteo Pitcheos', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_1.set_title('Bolas y Strikes por Salida', fontsize=15, fontweight='bold', color='#070B19')
        ax_plot_1.legend(loc='upper right', fontsize=11)
        ax_plot_1.grid(True, linestyle='--', alpha=0.3)

        # ── Plot 2: Whiff% por Salida ───────────────────────────────────────────
        whiff_vals = [float(g.get('whiff_pct', 0.0)) for g in plot_logs]
        ax_plot_2.plot(x_indices, whiff_vals, color='#2563EB', marker='o', linewidth=2.8, markersize=8, label='Whiff%')
        avg_whiff = np.mean(whiff_vals) if whiff_vals else 0.0
        ax_plot_2.axhline(avg_whiff, color='#94A3B8', linestyle='--', linewidth=1.8, label=f'Promedio ({avg_whiff:.1f}%)')
        for idx, w in zip(x_indices, whiff_vals):
            ax_plot_2.text(idx, w + 1.6, f"{w:.1f}%", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1E40AF')
        ax_plot_2.set_xticks(x_indices)
        ax_plot_2.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=11, fontweight='bold')
        ax_plot_2.set_ylim(0, max(max(whiff_vals or [10]) * 1.35, 38))
        ax_plot_2.set_ylabel('Whiff% (Abanicados)', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_2.set_title('Whiff% por Salida', fontsize=15, fontweight='bold', color='#070B19')
        ax_plot_2.legend(loc='upper right', fontsize=11)
        ax_plot_2.grid(True, linestyle='--', alpha=0.3)

        # ── Plot 3: CSW% por Salida ─────────────────────────────────────────────
        csw_vals = [float(g.get('csw_pct', 0.0)) for g in plot_logs]
        ax_plot_3.plot(x_indices, csw_vals, color='#059669', marker='s', linewidth=2.8, markersize=8, label='CSW%')
        avg_csw = np.mean(csw_vals) if csw_vals else 0.0
        ax_plot_3.axhline(30.0, color='#DC2626', linestyle=':', linewidth=2.0, label='Elite CSW (30%)')
        ax_plot_3.axhline(avg_csw, color='#94A3B8', linestyle='--', linewidth=1.8, label=f'Promedio ({avg_csw:.1f}%)')
        for idx, c in zip(x_indices, csw_vals):
            ax_plot_3.text(idx, c + 1.6, f"{c:.1f}%", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#065F46')
        ax_plot_3.set_xticks(x_indices)
        ax_plot_3.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=11, fontweight='bold')
        ax_plot_3.set_ylim(0, max(max(csw_vals or [10]) * 1.35, 48))
        ax_plot_3.set_ylabel('CSW% (Called + Whiff)', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_3.set_title('CSW% por Salida', fontsize=15, fontweight='bold', color='#070B19')
        ax_plot_3.legend(loc='lower left', fontsize=11)
        ax_plot_3.grid(True, linestyle='--', alpha=0.3)

        # ── Tabla Fila 5: Historial de Salidas del Período ─────────────────────
        ax_table.axis('off')
        display_logs = sorted_logs[::-1][:8]

        t_data = []
        for g in display_logs:
            p_val = int(g.get('pitches') or 0)
            s_val = int(g.get('strikes') or int(p_val * 0.62))
            b_val = max(0, p_val - s_val)
            p_str = f"{p_val} ({s_val}-{b_val})" if p_val > 0 else "—"
            csw_s = f"{float(g.get('csw_pct', 0)):.1f}%" if p_val > 0 else "—"
            wh_s = f"{float(g.get('whiff_pct', 0)):.1f}%" if p_val > 0 else "—"
            t_data.append([
                _fmt_date_short(g.get('date', '')),
                _clean_team_name(g.get('opponent', 'Rival')),
                str(g.get('role', 'Abridor')),
                str(g.get('decision', '—') or '—'),
                str(g.get('ip', '0.0')),
                str(g.get('h', 0)),
                str(g.get('er', 0)),
                str(g.get('bb', 0)),
                str(g.get('so', 0)),
                p_str,
                csw_s,
                wh_s,
            ])

        t_cols = ['Fecha', 'Rival', 'Rol', 'Dec.', 'IP', 'H', 'CL', 'BB', 'K', 'Pitcheos (P-S)', 'CSW%', 'Whiff%']
        game_log_table = ax_table.table(
            cellText=t_data,
            colLabels=t_cols,
            cellLoc='center',
            bbox=[0.0, 0.0, 1.0, 1.0]
        )
        game_log_table.auto_set_font_size(False)
        game_log_table.set_fontsize(13)
        for i in range(len(t_cols)):
            game_log_table.get_celld()[(0, i)].set_facecolor('#0F172A')
            game_log_table.get_celld()[(0, i)].get_text().set_color('#FDB827')
            game_log_table.get_celld()[(0, i)].get_text().set_fontweight('bold')
        for r_idx in range(len(t_data)):
            bg = '#FFFFFF' if r_idx % 2 == 0 else '#F8FAFC'
            for c_idx in range(len(t_cols)):
                game_log_table.get_celld()[(r_idx + 1, c_idx)].set_facecolor(bg)

        _plot_footer(ax_footer, is_lvbp=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return buf.getvalue()

    # Modo Salida Individual ('game')
    fig = plt.figure(figsize=(20, 20), facecolor='white')
    gs = gridspec.GridSpec(
        6, 8,
        height_ratios=[2, 20, 9, 36, 36, 7],
        width_ratios=[1, 18, 18, 18, 18, 18, 18, 1]
    )

    ax_headshot = fig.add_subplot(gs[1, 1])
    ax_bio = fig.add_subplot(gs[1, 2:6])
    ax_logo = fig.add_subplot(gs[1, 6])
    ax_season_table = fig.add_subplot(gs[2, 1:7])

    gs_plots = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[3, 1:7], wspace=0.36)
    ax_plot_1 = fig.add_subplot(gs_plots[0, 0])
    ax_plot_2 = fig.add_subplot(gs_plots[0, 1])
    ax_plot_3 = fig.add_subplot(gs_plots[0, 2])

    ax_table = fig.add_subplot(gs[4, 1:7])
    ax_footer = fig.add_subplot(gs[-1, 1:7])

    opp = _clean_team_name(game_summary.get("opponent", "Rival"))
    dt = game_summary.get("date", "")
    if is_mexico:
        mex_team = game_summary.get("team")
        if not mex_team or mex_team in ("Liga Mexicana", "Rival"):
            if game_logs:
                teams = [g.get("team") for g in game_logs if g.get("team") and g.get("team") not in ("Liga Mexicana", "Rival")]
                if teams:
                    mex_team = max(set(teams), key=teams.count)
        if not mex_team:
            mex_team = pitcher_info.get("team") or "Diablos Rojos"
        team_label = _clean_team_name(mex_team)
    else:
        team_label = pitcher_info.get("lvbp_team_name") or pitcher_info.get("team") or "Leones del Caracas"

    _plot_headshot(ax_headshot, pitcher_info.get("photo_url"))
    league_title = "México" if is_mexico else "LVBP"
    season_prefix = "LMB Verano " if is_mexico else "Temporada "
    _plot_bio(ax_bio, pitcher_info, f"{league_title} • {team_label} vs {opp}", f"Fecha: {dt} | {season_prefix}{season}")
    _plot_logo(ax_logo)

    kpis = analysis.get("pbp_kpis", {})
    tot_pitches = game_summary.get('pitches') or analysis.get('total_pitches') or len(analysis.get('pitches', [])) or 0
    st = {
        'ip': game_summary.get('ip', '0.0'),
        'h': game_summary.get('h', 0),
        'r': game_summary.get('r', 0),
        'er': game_summary.get('er', 0),
        'bb': game_summary.get('bb', 0),
        'so': game_summary.get('so', 0),
        'pitches': tot_pitches,
        'csw_pct': kpis.get('csw_pct', '—'),
    }
    _plot_summary_table(ax_season_table, st, is_game=True)

    # Plot 1: Workload por entrada (Stacked bar: Strikes vs Bolas)
    workload = analysis.get("innings_workload", [])
    if workload:
        inns = [w["inning"] for w in workload]
        p_counts = [w["pitches"] for w in workload]
        strks = [w.get("strikes", 0) for w in workload]
        bolas = [max(0, p - s) for p, s in zip(p_counts, strks)]

        ax_plot_1.bar(inns, strks, color='#0F172A', edgecolor='#0F172A', label='Strikes', width=0.55)
        ax_plot_1.bar(inns, bolas, bottom=strks, color='#FDB827', edgecolor='#0F172A', label='Bolas', width=0.55)

        for inn, tot in zip(inns, p_counts):
            ax_plot_1.text(inn, tot + 0.6, str(tot), ha='center', va='bottom', fontsize=11, fontweight='bold', color='#070B19')

        ax_plot_1.set_xticks(inns)
        ax_plot_1.set_xticklabels([f"Inn {i}" for i in inns], fontsize=11, fontweight='bold')
        ax_plot_1.set_ylim(0, max(p_counts) * 1.25 if p_counts else 25)
        ax_plot_1.set_xlabel('Entrada (Inning)', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_1.set_ylabel('Pitcheos Totales', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_1.set_title('Carga por Entrada', fontsize=16, fontweight='bold', color='#070B19')
        ax_plot_1.legend(loc='upper right', fontsize=10)
        ax_plot_1.grid(True, linestyle='--', alpha=0.3)
    else:
        ax_plot_1.axis('off')

    # Plot 2: Leverage Index Tango RE24
    if workload:
        inns = [w["inning"] for w in workload]
        lis = [w.get("avg_li", 1.0) for w in workload]
        ax_plot_2.plot(inns, lis, marker='o', linewidth=2.8, markersize=8, color='#D97706', label='LI Promedio')
        ax_plot_2.axhline(y=1.0, color='#64748B', linestyle='--', linewidth=1.5, label='Presión Base (1.0 LI)')

        for inn, li_val in zip(inns, lis):
            ax_plot_2.text(inn, li_val + 0.08, f"{li_val:.2f}", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#D97706')

        ax_plot_2.set_xticks(inns)
        ax_plot_2.set_xticklabels([f"Inn {i}" for i in inns], fontsize=11, fontweight='bold')
        max_li = max(lis) if lis else 1.0
        ax_plot_2.set_ylim(0, max(max_li * 1.3, 2.0))
        ax_plot_2.set_xlabel('Entrada (Inning)', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_2.set_ylabel('Leverage Index (LI)', fontsize=13, fontweight='bold', color='#070B19')
        ax_plot_2.set_title('Apalancamiento (Tango RE24)', fontsize=16, fontweight='bold', color='#070B19')
        ax_plot_2.legend(loc='upper right', fontsize=10)
        ax_plot_2.grid(True, linestyle='--', alpha=0.3)
    else:
        ax_plot_2.axis('off')

    # Plot 3: Platoon Splits (LHB vs RHB en tasa 0-100%)
    splits = analysis.get("splits_platoon", {})
    vs_l = splits.get("vs_lhb", {})
    vs_r = splits.get("vs_rhb", {})
    p_l = vs_l.get('pitches', 0)
    p_r = vs_r.get('pitches', 0)

    cats = ['Strike%', 'Whiff%', 'CSW%']
    vals_l = [
        float(str(vs_l.get('strike_pct', '0')).replace('%', '')),
        float(str(vs_l.get('whiff_pct', '0')).replace('%', '')),
        float(str(vs_l.get('csw_pct', '0')).replace('%', ''))
    ]
    vals_r = [
        float(str(vs_r.get('strike_pct', '0')).replace('%', '')),
        float(str(vs_r.get('whiff_pct', '0')).replace('%', '')),
        float(str(vs_r.get('csw_pct', '0')).replace('%', ''))
    ]

    x = np.arange(len(cats))
    width = 0.35
    bars_l = ax_plot_3.bar(x - width/2, vals_l, width, label=f"vs Zurdos ({p_l} P)", color='#3B82F6', edgecolor='#0F172A')
    bars_r = ax_plot_3.bar(x + width/2, vals_r, width, label=f"vs Derechos ({p_r} P)", color='#F59E0B', edgecolor='#0F172A')

    for rect in bars_l:
        h = rect.get_height()
        if h > 0:
            ax_plot_3.text(rect.get_x() + rect.get_width()/2., h + 1.2, f"{h:.0f}%", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1E40AF')
    for rect in bars_r:
        h = rect.get_height()
        if h > 0:
            ax_plot_3.text(rect.get_x() + rect.get_width()/2., h + 1.2, f"{h:.0f}%", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#B45309')

    ax_plot_3.set_xticks(x)
    ax_plot_3.set_xticklabels(cats, fontsize=11, fontweight='bold')
    ax_plot_3.set_ylim(0, 100)
    ax_plot_3.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))
    ax_plot_3.set_ylabel('Porcentaje (%)', fontsize=13, fontweight='bold', color='#070B19')
    ax_plot_3.set_title('Platoon Splits (LHB vs RHB)', fontsize=16, fontweight='bold', color='#070B19')
    ax_plot_3.legend(loc='upper right', fontsize=10)
    ax_plot_3.grid(True, linestyle='--', alpha=0.3)

    # Tabla PBP de destinos
    ax_table.axis('off')
    pbp_rows = analysis.get("pbp_table", [])
    if pbp_rows:
        t_data = [[r.get('destination', ''), str(r.get('count', 0)), str(r.get('pct', ''))] for r in pbp_rows]
        t_cols = ['Destino del Pitcheo', 'Total Conteo', 'Distribución %']
        pbp_table = ax_table.table(
            cellText=t_data,
            colLabels=t_cols,
            cellLoc='center',
            bbox=[0.12, 0.05, 0.76, 0.90]
        )
        pbp_table.auto_set_font_size(False)
        pbp_table.set_fontsize(15)
        for i in range(3):
            pbp_table.get_celld()[(0, i)].set_facecolor('#0F172A')
            pbp_table.get_celld()[(0, i)].get_text().set_color('#FDB827')
            pbp_table.get_celld()[(0, i)].get_text().set_fontweight('bold')
        for r_idx in range(len(t_data)):
            bg = '#FFFFFF' if r_idx % 2 == 0 else '#F8FAFC'
            for c_idx in range(3):
                pbp_table.get_celld()[(r_idx + 1, c_idx)].set_facecolor(bg)

    _plot_footer(ax_footer, is_lvbp=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return buf.getvalue()


# ── 5. Wrapper de Compatibilidad Retroactiva ───────────────────────────────────

def build_pitching_summary_card(
    pitcher_data: Optional[Dict[str, Any]] = None,
    game_data: Optional[Dict[str, Any]] = None,
    pitch_analysis: Optional[Dict[str, Any]] = None,
    is_lvbp: bool = False,
    is_mexico: bool = False,
    branch: Optional[str] = None,
    season: int = 2024,
    # Parámetros alternativos y expandidos para compatibilidad universal
    pitcher_info: Optional[Dict[str, Any]] = None,
    game_summary: Optional[Dict[str, Any]] = None,
    analysis: Optional[Dict[str, Any]] = None,
    mode: str = "game",
    game_logs: Optional[List[Dict[str, Any]]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    phase: str = "all",
    df_statcast: Optional[pd.DataFrame] = None,
    df: Optional[pd.DataFrame] = None,
    dpi: int = 150,
    **kwargs,
) -> bytes:
    """
    Función de compatibilidad universal para generación de tarjetas HD (2400x1350 px a 300 DPI).
    Admite indistintamente (pitcher_info / pitcher_data), (game_summary / game_data),
    (analysis / pitch_analysis), modos de tiempo ('game', 'season', 'range') y DataFrames Statcast.
    """
    p_info = pitcher_info or pitcher_data or {}
    g_data = game_summary or game_data or {}
    p_analysis = analysis or pitch_analysis or {}
    statcast_df = df if df is not None else df_statcast
    phase_arg = phase or kwargs.get("phase", "all")
    use_mexico = is_mexico or (branch == "mexico")

    if is_lvbp or use_mexico or branch == "lvbp":
        raw_bytes = build_lvbp_matplotlib_summary(
            pitcher_info=p_info,
            game_summary=g_data,
            analysis=p_analysis,
            season=season,
            dpi=dpi,
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            game_logs=game_logs,
            phase=phase_arg,
            is_mexico=use_mexico,
        )
    else:
        if statcast_df is not None and not statcast_df.empty:
            df_to_use = statcast_df
        else:
            pitches = p_analysis.get("pitches", [])
            if pitches:
                df_to_use = pd.DataFrame(pitches)
                if 'pitch_name' in df_to_use.columns and 'pitch_type' not in df_to_use.columns:
                    rev_pitch = {v['name'].lower(): k for k, v in PITCH_COLOURS.items()}
                    df_to_use['pitch_type'] = df_to_use['pitch_name'].apply(lambda n: rev_pitch.get(str(n).lower(), 'FF'))
                if 'release_speed' not in df_to_use.columns:
                    df_to_use['release_speed'] = 93.0
                if 'pfx_x' not in df_to_use.columns:
                    df_to_use['pfx_x'] = df_to_use.get('hb', 0.0)
                if 'pfx_z' not in df_to_use.columns:
                    df_to_use['pfx_z'] = df_to_use.get('ivb', 0.0)
                if 'game_date' not in df_to_use.columns:
                    df_to_use['game_date'] = g_data.get('date', '2024-04-17')
                if 'p_throws' not in df_to_use.columns:
                    df_to_use['p_throws'] = p_info.get('throws', 'R')
                df_to_use['swing'] = True
                df_to_use['whiff'] = df_to_use.get('is_whiff', False)
                df_to_use['in_zone'] = True
                df_to_use['out_zone'] = False
                df_to_use['chase'] = False
            else:
                df_to_use = pd.DataFrame()

        raw_bytes = build_nestico_pitching_summary(
            df=df_to_use,
            pitcher_info=p_info,
            mode=mode,
            season=season,
            start_date=start_date,
            end_date=end_date,
            game_summary=g_data,
            game_logs=game_logs,
            dpi=dpi,
        )

    # Redimensionar al formato canónico vertical (2400x2400) a 300 DPI (paridad total con LVBP)
    target_size = CANVAS_SIZE_LVBP
    im = Image.open(io.BytesIO(raw_bytes))
    im_resized = im.resize(target_size, Image.Resampling.LANCZOS)
    out_buf = io.BytesIO()
    im_resized.save(out_buf, format="PNG", dpi=DPI)
    return out_buf.getvalue()

