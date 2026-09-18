# Bug Fix: Soporte Universal de Lanzadores y Navegación desde Individuales

- **Slug**: `pitcher-navigation-and-data-loading`
- **Fecha**: 2026-09-18
- **Estado**: Implementando

## Resumen del Cambio

1. **`core/pitching_engine.py`**:
   - Se añade la función `get_pitcher_by_id(pitcher_id: int)` con consulta directa a `https://statsapi.mlb.com/api/v1/people/{id}` y fallback local/Supabase.
   - Detección universal de historial en LVBP para todos los equipos (`has_lvbp_history: bool`) y de Caracas (`has_caracas_history: bool`).
   - `search_pitchers(query)`: Detecta si `query` es numérico para delegar inmediatamente a `get_pitcher_by_id`.

2. **`republicaraquistapp/state/pitching_state.py`**:
   - `on_load()`: Procesa `pitcher_id` y `pitcher_name` desde los parámetros de la URL, permitiendo la conmutación inmediata de lanzador incluso si ya había uno seleccionado.
   - `select_pitcher_by_id()`: Resuelve lanzadores por ID mediante `get_pitcher_by_id()`. Si el lanzador tiene historial en LVBP, abre por defecto la rama `lvbp`.
   - `pitcher_season`: Inicializado en `"2025"` como temporada activa.
   - Conmutación flexible de ramas: `set_active_branch("lvbp")` permitido si `has_lvbp_history` es verdadero.

3. **`republicaraquistapp/pages/pitching.py`**:
   - El botón de rama LVBP queda disponible para cualquier lanzador con historial en la liga (`disabled=~PitchingState.has_lvbp_history`).
   - La etiqueta del botón indica dinámicamente el equipo LVBP del jugador.

4. **`core/pitching_card.py`**:
   - Adaptación de subtítulos de tarjetas para mostrar el nombre del equipo real del lanzador en la LVBP.
