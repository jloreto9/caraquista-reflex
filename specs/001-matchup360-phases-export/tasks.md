# Tasks: Matchup 360 Cross-Phase & HD 300 DPI Export

**Input**: Design documents from `specs/001-matchup360-phases-export/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `constitution.md`  

---

## Reglas de Ejecución de Tareas (`CLAUDE.md` & Ponytail)

1. **Edición Directa:** Modificar directamente los archivos fuente canónicos. **PROHIBIDO** crear scripts temporales (`fix.py`, `patch.py`, `temp.py`).
2. **Validación Obligatoria:** Ninguna tarea se marca como completada sin evidencia (tests unitarios/integración, o validación de shapes, dtypes y totales de control).
3. **No Regresión:** Validar que los cambios no afecten consumers aguas abajo (DAX, vistas SQL, componentes UI).

---

## Phase 1: Setup & Prerrequisitos

**Propósito**: Preparación de infraestructura base y confirmación de entorno

- [x] T001 Confirmar branches limpios y entorno activo en `c:\Users\Administrator\Projets\caraquista-reflex`
- [x] T002 Validar contratos de datos iniciales en Supabase y endpoints de MLB Stats API

---

## Phase 2: User Story 1 - Comparación Cruzada por Fases en Matchup 360 (Priority: P1) 🎯 MVP

**Meta**: Permitir seleccionar fases independientes para Jugador 1 y Jugador 2 en Matchup 360 con opción de sincronización global.  
**Test / Validación Independiente**: `test_comparator_cross_phase_support` en `tests/test_matchup360_overall.py`.

### Validación / Tests para US1
- [x] T003 [P] [US1] Escribir test unitario de comparación cruzada en `tests/test_matchup360_overall.py`
- [x] T004 [US1] Confirmar falla inicial cuando no existían variables de fase independiente en el estado

### Implementación Directa para US1
- [x] T005 [US1] Modificar `republicaraquistapp/state/individuales_state.py` incorporando `comparator_phase_1`, `comparator_phase_2` y `comparator_global_phase`
- [x] T006 [US1] Implementar `_get_dataset_for_phase()` para extraer y cachear de forma reactiva las estadísticas de cada fase (`R`, `L`, `F`, `all`)
- [x] T007 [US1] Integrar los controles selectores (`rx.select`) en `republicaraquistapp/pages/individuales.py`
- [x] T008 [US1] Ejecutar test unitario para confirmar pase al 100%

---

## Phase 3: User Story 2 - Franquicia de Refuerzos y Leandro Cedeño (Priority: P2)

**Meta**: Asignar el equipo real de cada fase y preservar la franquicia canónica en la vista general.  
**Test / Validación Independiente**: `test_leandro_cedeno_franchise_preservation` en `tests/test_matchup360_overall.py`.

- [x] T009 [P] [US2] Escribir test unitario de simulación de refuerzo evaluando `phase='R'`, `phase='L'` y `phase='all'`
- [x] T010 [US2] Modificar `core/supabase_client.py` con resolución modal sobre juegos de Temporada Regular (`game_type == 'R'`)
- [x] T011 [US2] Validar que Leandro Cedeño conserve `CAR` en Temporada Regular y `MAG` en Round Robin

---

## Phase 4: User Story 3 - Exportación HD a 300 DPI y UTF-8 (Priority: P3)

**Meta**: Generar la tarjeta gráfica PNG a 1360px de ancho y 300 DPI con fuentes TrueType empaquetadas.  
**Test / Validación Independiente**: `test_build_matchup_image_png_header` y `test_unicode_matchup_image_generation`.

- [x] T012 [P] [US3] Copiar `DejaVuSans.ttf` y `DejaVuSans-Bold.ttf` en `assets/fonts/` y añadirlas al `Dockerfile`
- [x] T013 [US3] Escalar la tarjeta en `core/matchup_card.py` con `scale = 2.0` (1360px de ancho, badges de fase, avatares HD de 128x128)
- [x] T014 [US3] Guardar metadatos `dpi=(300, 300)` en el guardado PNG de Pillow
- [x] T015 [US3] Ejecutar tests unitarios de validación de encabezado PNG y caracteres acentuados

---

## Phase 5: Validación Final y Cierre (Convergencia)

- [x] T016 **Suite Completa**: Ejecutar los 162 tests automatizados pasando al 100% en 14.5s
- [x] T017 **Limpieza**: Confirmar ausencia de scripts temporales de parcheo en el repositorio
- [x] T018 **Commit Convencional**: Registrar commit `98898f9` con mensaje descriptivo en español
- [x] T019 **Despliegue VPS**: Reconstruir contenedor Docker en `srv929207.hstgr.cloud` y verificar salud en vivo
