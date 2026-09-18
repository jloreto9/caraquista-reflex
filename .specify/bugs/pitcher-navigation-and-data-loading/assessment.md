# Bug Assessment: Falla de Navegación, Búsqueda y Visualización de Lanzadores en Pitching Summary

- **Slug**: `pitcher-navigation-and-data-loading`
- **Fecha**: 2026-09-18
- **Severidad**: Alta
- **Componentes**: `republicaraquistapp/state/pitching_state.py`, `core/pitching_engine.py`, `republicaraquistapp/pages/pitching.py`, `core/pitching_card.py`

## Síntoma Observado

Al intentar visualizar el Pitching Summary de múltiples lanzadores:
1. Al navegar desde los enlaces de la tabla de estadísticas de pitcheo en `/individuales` (`/pitching?pitcher_id=XXXX`), la aplicación no cambia de lanzador y mantiene al lanzador anterior (o no carga nada si no había ninguno).
2. Para lanzadores de equipos de la LVBP distintos a Leones del Caracas (ej: Ricardo Sánchez de Magallanes, Max Castillo de Lara, Osmer Morales de Margarita, Zac Grotz de La Guaira, Junior Guerra de Magallanes, Silvino Bracho de Zulia), la interfaz abre la rama MLB sin salidas y bloquea el botón de LVBP con `disabled`.
3. Al buscar por ID de lanzador, la API de MLB devuelve peloteros no relacionados (como Aaron Judge o Rafael Devers), arruinando la selección.
4. La temporada por defecto era `2024`, pero la temporada actual de la LVBP con datos es `2025`.

## Disparador y Reproducción

1. Ingresar a `/pitching` y cargar a Erick Leal (`612797`).
2. Navegar a `/individuales` e intentar hacer clic en el ícono de llama de Ricardo Sánchez (`645307`) o Max Castillo (`666721`).
3. Observar que `/pitching?pitcher_id=645307` mantiene a Erick Leal debido al `return` temprano en `on_load`.
4. Si se limpia el estado y se navega directamente a `/pitching?pitcher_id=645307`, `select_pitcher_by_id` llama a `search_pitchers("645307")`, lo que consulta `names=645307` en la API de MLB, fallando en resolver a Ricardo Sánchez.
5. Si se busca por nombre "Ricardo Sanchez", el sistema lo cataloga con `has_caracas_history = False`, lo asigna forzosamente a la rama `mlb`, desactiva el botón de LVBP (`disabled=~has_caracas_history`) y muestra "0 salidas".

## Causa Raíz

1. **`pitching_state.py:on_load()`**: `if self.has_pitcher_selected: return` impedía procesar `router.page.params.get("pitcher_id")` si ya existía un lanzador cargado en la sesión.
2. **`pitching_engine.py:search_pitchers()`**: No existía una función `get_pitcher_by_id()` dedicada que consultara `api/v1/people/{id}`. Tratar IDs como nombres en `people/search?names={id}` arrojaba resultados arbitrarios.
3. **Restricción artificial Caracas vs LVBP**: `has_caracas_history` solo contemplaba un set limitado de Caracas (`team_id == 695`), bloqueando la pestaña LVBP para el resto de las franquicias a pesar de que el motor de extracción `_get_lvbp_pitcher_game_logs` sí extrae datos para toda la liga.
4. **Temporada por defecto**: `pitcher_season: str = "2024"` cuando los registros activos de la LVBP corresponden a `2025`.

## Criterio de Éxito

1. Cualquier lanzador con enlace en `/individuales` debe abrir su Pitching Summary en `/pitching` inmediatamente, cambiando el lanzador activo sin importar el estado previo.
2. Todo lanzador con historial en cualquiera de los 8 equipos de la LVBP debe tener disponible la pestaña LVBP y cargar sus salidas de la temporada 2025 (o su temporada más reciente).
3. Los lanzadores con salidas en MLB/MiLB (como Albert Suárez o Carlos Hernández) deben poder alternar entre MLB y LVBP fluidamente.
4. Búsquedas por ID numérico en el buscador deben resolver al jugador exacto en menos de 1 segundo.
