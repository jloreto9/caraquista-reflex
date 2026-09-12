# Implementation Plan: Renombrado a RepubliCaraquistApp Reflex y Actualización Exhaustiva del README

**Branch**: `002-republicaraquistapp-reflex-readme` | **Date**: 2026-09-12 | **Spec**: [specs/002-republicaraquistapp-reflex-readme/spec.md](file:///c:/Users/Administrator/Projets/caraquista-reflex/specs/002-republicaraquistapp-reflex-readme/spec.md)  
**Input**: Feature specification from `specs/002-republicaraquistapp-reflex-readme/spec.md`  

---

## 1. Resumen Ejecutivo y Enfoque Técnico

Modernizar de forma integral la documentación pública y la identidad del proyecto en el repositorio:
1. Renombrar la solución a **`republicaraquistapp-reflex`** en `README.md`, manifiesto `docker-compose.yml` y documentación de gobernanza del workspace (`GEMINI.md`, `CLAUDE.md`).
2. Redactar un `README.md` de nivel profesional y sabermétrico que cubra el 100% de la arquitectura construida:
   - Las 8 vistas SPA completas (`/`, `/standings`, `/individuales`, `/colectivas`, `/wpa`, `/situacional`, `/spray-charts`, `/bullpen`).
   - Matchup 360 con filtros por fases independientes, radares polares y exportación de tarjetas HD a 300 DPI con tipografía TrueType.
   - Pestaña de Fildeo / Defensa Individual con métricas sabermétricas (FPCT, RF/9, CS, CS%, DP, PB).
   - Ingesta de 4 temporadas (2022-2025) con 1,161 juegos vía `ingest_lvbp_batch.py` y GitHub Actions diario.
   - Despliegue en producción con arquitectura dual Docker (Caddy daemon + Reflex backend-only) bajo Traefik SSL.
   - Suite de 162 pruebas automatizadas y gobernanza Spec Kit SDD con los 4 MDs por repositorio.

---

## 2. Escalera de Simplicidad (Ponytail Ladder Check)

- [x] **YAGNI**: No se tocan dependencias ni lógica de cálculo interno en Python; el cambio se acota a documentación, identidad y orquestación Docker.
- [x] **Reuso Local**: Se aprovechan los textos técnicos y métricas ya consolidadas en `GEMINI.md` y `specs/001-matchup360-phases-export/`.
- [x] **Plataforma Nativa**: Uso de Markdown con tablas de GitHub Flavored Markdown y sintaxis matemática LaTeX ($PCT, xW, RE24$).
- [x] **Diff Mínimo**: Cambios focalizados en `README.md`, `docker-compose.yml` y archivos de gobernanza.

---

## 3. Chequeo Constitucional y Guardrails de Negocio

### A. Leyes Generales de Ingeniería (`CLAUDE.md`)
- [x] **Causa Raíz Identificada**: El README anterior reflejaba una etapa temprana (4 vistas, rutas viejas `caraquista_reflex/`). Se reescribe para reflejar fielmente la suite actual de 8 vistas y `republicaraquistapp/`.
- [x] **Fuente de Verdad Única**: Modificación directa en `README.md` y `docker-compose.yml`. Cero scripts temporales.
- [x] **Punto de Retorno / Rollback**: `git checkout main` o `git revert`.

### C. Analítica Deportiva (LVBP / LIDOM):
- [x] **Prohibición de Jerga Corporativa**: Prohibido usar "Dashboard Ejecutivo". Se usa "Centro de Mando" y "Resumen de Temporada".
- [x] **Prohibición Estricta de Statcast en LVBP**: No incluir métricas de Statcast (Launch Angle, Barrels, Exit Velocity).
- [x] **Idioma Oficial**: 100% en español.
- [x] **Gobernanza Spec Kit**: Mantener los 4 MDs dentro del repositorio.

---

## 4. Archivos Exactos Afectados y Estructura

### Archivos Fuente a Modificar
- `[MOD]` `README.md`: Documentación completa de la plataforma, identidad, 8 vistas SPA, pipeline ETL, despliegue y testing.
- `[MOD]` `docker-compose.yml`: Renombrar `service` y `container_name` a `republicaraquistapp-reflex`.
- `[MOD]` `c:/Users/Administrator/Projets/GEMINI.md`: Actualizar denominación canónica a `republicaraquistapp-reflex`.
- `[MOD]` `c:/Users/Administrator/Projets/CLAUDE.md`: Actualizar referencias a `republicaraquistapp-reflex`.
- `[TEST]` `tests/`: Re-ejecutar la suite completa de 162 pruebas unitarias.

---

## 5. Plan de Rollback y Mitigación de Riesgos

- **Disparador de Rollback**: Error de sintaxis en `docker-compose.yml` que impida levantar el contenedor en el VPS.
- **Acción de Retorno**: `git revert HEAD` y `docker compose up -d`.
- **Riesgo Downstream**: Nulo. No se alteran APIs, esquemas de Supabase ni lógica reactiva de Reflex.
