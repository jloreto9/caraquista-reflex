# Tasks: Renombrado a RepubliCaraquistApp Reflex y Actualización Exhaustiva del README

**Input**: Design documents from `specs/002-republicaraquistapp-reflex-readme/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `constitution.md`  

---

## Reglas de Ejecución de Tareas (`CLAUDE.md` & Ponytail)

1. **Edición Directa:** Modificar directamente los archivos fuente canónicos (`README.md`, `docker-compose.yml`).
2. **Validación Obligatoria:** Ninguna tarea se marca como completada sin evidencia (tests y verificación de contenedor).
3. **No Regresión:** Validar que el router Traefik y los endpoints sigan respondiendo `HTTP 200`.

---

## Phase 1: Setup & Prerrequisitos

- [ ] T001 Confirmar branches limpios y entorno activo en el repositorio
- [ ] T002 Validar configuración actual de `docker-compose.yml` y `README.md`

---

## Phase 2: User Story 2 - Renombrado del Proyecto (Priority: P2)

**Meta**: Unificar el nombre a `republicaraquistapp-reflex` en orquestación y gobernanza.  
**Test / Validación Independiente**: `docker compose config` sin errores y nombres actualizados.

- [ ] T003 [US2] Modificar `docker-compose.yml` asignando `republicaraquistapp-reflex` como nombre de servicio y contenedor
- [ ] T004 [US2] Actualizar referencias en `c:/Users/Administrator/Projets/CLAUDE.md` y `c:/Users/Administrator/Projets/GEMINI.md`

---

## Phase 3: User Story 1 - Actualización Exhaustiva de README.md (Priority: P1) 🎯 MVP

**Meta**: Redactar un `README.md` completo, moderno y fiel a la producción actual.  
**Test / Validación Independiente**: Inspección visual del renderizado Markdown y verificación de enlaces.

- [ ] T005 [US1] Redactar encabezado principal con identidad `# 🦁 RepubliCaraquistApp Reflex` y badges de estado
- [ ] T006 [US1] Documentar en detalle la suite completa de las **8 Vistas SPA** (`/`, `/standings`, `/individuales`, `/colectivas`, `/wpa`, `/situacional`, `/spray-charts`, `/bullpen`)
- [ ] T007 [US1] Documentar el comparador **Matchup 360**, filtros de fases independientes y exportación de tarjetas HD a 300 DPI
- [ ] T008 [US1] Documentar la pestaña de **Fildeo / Defensa Individual** y estadísticas colectivas en Plotly
- [ ] T009 [US1] Documentar el pipeline de ingesta por lotes de **4 temporadas** (`scripts/ingest_lvbp_batch.py`) y automatización en GitHub Actions
- [ ] T010 [US1] Documentar la arquitectura de producción con contenedores duales (Caddy daemon + Reflex backend) bajo Traefik SSL
- [ ] T011 [US1] Documentar la suite de 162 pruebas unitarias y el marco de gobernanza Spec Kit con los 4 MDs

---

## Phase 4: Validación Final, Despliegue y Cierre

- [ ] T012 **Suite de Tests**: Ejecutar los 162 tests unitarios pasando al 100%
- [ ] T013 **Versionado Git**: Commit convencional en español y push a `origin/main`
- [ ] T014 **Despliegue VPS**: Actualizar contenedor en el VPS y verificar `HTTP 200` y WSS `101`
- [ ] T015 **Generación de implementation.md**: Registrar el informe final completando los 4 MDs
