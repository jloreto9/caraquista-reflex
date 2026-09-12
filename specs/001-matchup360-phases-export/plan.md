# Implementation Plan: Matchup 360 Cross-Phase & HD 300 DPI Export

**Branch**: `001-matchup360-phases-export` | **Date**: 2026-09-12 | **Spec**: [specs/001-matchup360-phases-export/spec.md](file:///C:/Users/Administrator/Projets/specs/001-matchup360-phases-export/spec.md)  
**Input**: Feature specification from `specs/001-matchup360-phases-export/spec.md`  

---

## 1. Resumen Ejecutivo y Enfoque Técnico

Extender el módulo Matchup 360 de `caraquista-reflex` para admitir selección independiente de fases de campeonato (`Temporada Regular`, `Round Robin`, `Serie Final`, `Todas las Fases`) para Jugador 1 y Jugador 2, con un control de sincronización global.
Preservar la asignación de franquicia por fase específica (Leandro Cedeño en Caracas para Regular Season y en Magallanes como refuerzo de postemporada), calculando modalmente el equipo canónico en la fase agregada.
Elevar la exportación de tarjetas Matchup 360 a $1360\text{ px}$ de ancho a 300 DPI con tipografía TrueType empaquetada (`DejaVuSans`) para garantizar renderizado perfecto de caracteres Unicode (`ñ`, acentos).

---

## 2. Escalera de Simplicidad (Ponytail Ladder Check)

- [x] **YAGNI**: Resuelve directamente el dolor reportado por el usuario sobre refuerzos en postemporada y la resolución de exportación sin introducir frameworks adicionales.
- [x] **Reuso Local**: Reutiliza `_get_dataset_for_phase()`, `primary_team_map` y el generador `build_matchup_image()`.
- [x] **Python Standard Library**: Pillow (`ImageFont`, `ImageDraw`) escalado con factor multiplicador directo (`scale = 2.0`).
- [x] **Plataforma Nativa**: Estado reactivo nativo de Reflex (`rx.select`, `rx.Var`, event handlers).
- [x] **Diff Mínimo**: Modificaciones focalizadas en 4 archivos centrales sin crear capas intermedias redundantes.

---

## 3. Chequeo Constitucional y Guardrails de Negocio

### A. Leyes Generales de Ingeniería (`CLAUDE.md`)
- [x] **Causa Raíz Identificada**: Se ataca el cálculo modal de franquicia en Supabase y la carga de fuentes TrueType en Pillow en vez de emparchar strings en la UI.
- [x] **Fuente de Verdad Única**: Modificaciones directas en `individuales_state.py`, `individuales.py`, `supabase_client.py` y `matchup_card.py`. Cero scripts temporales.
- [x] **Punto de Retorno / Rollback**: Git commit atómico reversible vía `git revert 98898f9`.

### C. Analítica Deportiva (LVBP / LIDOM):
- [x] **Esquema Supabase**: 100% compatible con tablas existentes (`batting_stats`, `pitching_stats`, `games`).
- [x] **Constantes Sabermétricas**: Constantes intactas y cálculos relativos a la fase seleccionada.
- [x] **Idioma**: Interfaz y tarjetas 100% en español.

---

## 4. Archivos Exactos Afectados y Estructura

### Archivos Fuente a Modificar (Fuente de Verdad)
- `[MOD]` `republicaraquistapp/state/individuales_state.py`: Incorporar variables `comparator_phase_1`, `comparator_phase_2`, `comparator_global_phase`, handlers de fase y evaluación de percentiles por fase.
- `[MOD]` `republicaraquistapp/pages/individuales.py`: Agregar selectores de fase por jugador y sincronizador global en la UI.
- `[MOD]` `core/supabase_client.py`: Asegurar filtrado por `phase` y resolución modal de franquicia canónica en Temporada Regular.
- `[MOD]` `core/matchup_card.py`: Escalar a 1360px de ancho, metadatos a 300 DPI, renderizado de badges de fase y uso de `DejaVuSans.ttf`.
- `[TEST]` `tests/test_matchup360_overall.py`: Pruebas de resolución HD 300 DPI, sincronización de fases y preservación de franquicia para Leandro Cedeño.

---

## 5. Plan de Rollback y Mitigación de Riesgos

- **Disparador de Rollback**: Ruptura de carga de estadísticas individuales o falla en tests unitarios.
- **Acción de Retorno**: `git checkout main` o `git revert HEAD`.
- **Riesgo Downstream**: Mitigado mediante la suite de 162 tests pasando al 100% y caché en memoria con TTL de 30 minutos.
