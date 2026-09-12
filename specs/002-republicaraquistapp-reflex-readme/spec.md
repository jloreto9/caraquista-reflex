# Feature Specification: Renombrado a RepubliCaraquistApp Reflex y Actualización Exhaustiva del README

**Feature Branch**: `002-republicaraquistapp-reflex-readme`  
**Created**: 2026-09-12  
**Status**: Implemented & Verified  
**Input**: "Actualiza el README de caraquista-reflex y quiero cambiar el nombre tambien, que se llame republicaraquistapp-reflex"  

---

## 1. User Scenarios & Testing *(mandatory)*

### User Story 1 - Actualización Completa y Moderna del README.md (Priority: P1) 🎯 MVP

Como usuario, desarrollador o reclutador que visita el repositorio en GitHub, quiero leer un `README.md` exhaustivo, elegante y actualizado que documente la plataforma en su estado real actual, incluyendo la suite completa de las 8 vistas SPA, motores analíticos en `core/`, pipeline de ingesta por lotes (4 temporadas con 1,161 juegos), arquitectura de despliegue Docker dual (Caddy + Reflex bajo Traefik SSL) y suite de 162 pruebas automatizadas.

**Why this priority**: El README anterior estaba desactualizado (solo describía 4 páginas, omitía Fildeo, Matchup 360 HD 300 DPI, Colectivas, Spray Charts, Bullpen / Lineups y el pipeline ETL de 4 temporadas) y contenía rutas obsoletas (`caraquista_reflex/` en lugar del paquete canónico `republicaraquistapp/`).

**Independent Test**: Verificar que el archivo `README.md` cubra las 8 rutas de la SPA, la arquitectura técnica real, el stack de dependencias, instrucciones de instalación y enlaces de producción operativos.

**Acceptance Scenarios**:
1. **Given** un visitante del repositorio, **When** abre el `README.md`, **Then** encuentra la documentación detallada de las 8 vistas, capturas de arquitectura, tabla de comandos y enlace verificado a `https://caraquista.srv929207.hstgr.cloud/`.
2. **Given** un desarrollador configurando el proyecto, **When** revisa el árbol de directorios del README, **Then** refleja la estructura exacta con `republicaraquistapp/`, `core/`, `assets/fonts/`, `scripts/` y `specs/`.

---

### User Story 2 - Renombrado Canónico del Proyecto a `republicaraquistapp-reflex` (Priority: P2)

Como propietario de la plataforma, quiero que el nombre oficial del proyecto sea **`republicaraquistapp-reflex`** en toda la documentación, configuraciones de despliegue (`docker-compose.yml`) y manifiestos, consolidando la identidad de República Caraquista en versión web reactiva.

**Why this priority**: Unifica la marca con la aplicación matriz (`RepubliCaraquistApp`), distinguiéndola con el sufijo `-reflex` para indicar su implementación moderna sobre Next.js + FastAPI.

**Independent Test**: Inspeccionar `docker-compose.yml`, `README.md` y gobernanza para validar que el contenedor y servicio se nombren `republicaraquistapp-reflex` sin romper el routing de Traefik ni la URL de hostinger.

**Acceptance Scenarios**:
1. **Given** el archivo `docker-compose.yml`, **When** se define el servicio y nombre de contenedor, **Then** ambos se denominan `republicaraquistapp-reflex`.
2. **Given** el archivo `README.md`, **When** se leen los títulos y comandos de clonado, **Then** se refieren a `republicaraquistapp-reflex`.

---

### Edge Cases & Data Boundaries

- **Compatibilidad del subdominio VPS existente**: El subdominio en producción sigue siendo `caraquista.srv929207.hstgr.cloud`. El cambio de nombre en Docker Compose (`container_name: republicaraquistapp-reflex`) no debe alterar la regla de Host de Traefik (`Host('caraquista.srv929207.hstgr.cloud')`) para evitar disrupciones del certificado SSL Let's Encrypt ya emitido.
- **Rutas de importación de Python**: El paquete interno en Python ya se llama `republicaraquistapp/` y `rxconfig.py` ya define `app_name="republicaraquistapp"`. El renombrado no altera imports en Python ni requiere refactors de código interno.

---

## 2. Invariantes de Dominio y Contrato de Datos *(mandatory)*

### B. Sabermetría / Deportes (LVBP / LIDOM):
- [x] **Esquema relacional Supabase**: Tablas intactas (`batting_stats`, `pitching_stats`, `games`, `players`, `teams`).
- [x] **Convención de temporada**: Identificador canónico `season=2025` preservado.
- [x] **Prohibición de jerga corporativa**: Uso estricto de terminología sabermétrica ("Centro de Mando", "Resumen de Temporada", "Líderes", "Matchup 360", "Posiciones & ELO") en lugar de términos corporativos ("Dashboard Ejecutivo").
- [x] **Prohibición estricta de Statcast en LVBP**: No mencionar ni inventar métricas de Statcast (Launch Angle, Barrels, Exit Velocity) inexistentes en la liga venezolana.
- [x] **Idioma**: Toda la documentación pública en **español**.

---

## 3. Requerimientos Funcionales *(mandatory)*

- **FR-001**: El archivo `README.md` DEBE titularse `# 🦁 RepubliCaraquistApp Reflex (Plataforma Web Sabermétrica)` y documentar exhaustivamente las 8 vistas SPA.
- **FR-002**: El archivo `README.md` DEBE detallar las innovaciones recientes: Matchup 360 con filtros por fases independientes, exportación de tarjetas HD a 300 DPI, pestaña de Fildeo/Defensa, pipeline ETL para 4 temporadas y framework Spec Kit SDD con los 4 MDs.
- **FR-003**: `docker-compose.yml` DEBE actualizar el servicio y nombre de contenedor a `republicaraquistapp-reflex`, conservando la red `root_default` y el router Traefik.
- **FR-004**: Los archivos de gobernanza (`CLAUDE.md`, `GEMINI.md`) DEBEN registrar `republicaraquistapp-reflex` como la denominación canónica del proyecto.

---

## 4. Criterios de Éxito y Demostración Cuantificable *(mandatory)*

- **SC-001**: El `README.md` nuevo cubre el 100% de los módulos y características en producción.
- **SC-002**: Los 162 tests automatizados se ejecutan y pasan al 100% sin regresiones.
- **SC-003**: El despliegue de producción en el VPS se actualiza con `docker compose up -d` reflejando el contenedor `republicaraquistapp-reflex` saludable y respondiendo `HTTP 200`.

---

## 5. Supuestos y Dependencias

- Repositorio Git en `https://github.com/jloreto9/caraquista-reflex.git` (el cambio de nombre del repositorio en la interfaz de GitHub queda como acción opcional del usuario en el navegador).
- El contenedor de producción corre sobre Traefik con red compartida `root_default`.
