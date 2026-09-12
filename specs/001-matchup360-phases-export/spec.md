# Feature Specification: Matchup 360 Cross-Phase & HD 300 DPI Export

**Feature Branch**: `001-matchup360-phases-export`  
**Created**: 2026-09-12  
**Status**: Implemented & Verified  
**Input**: "Matchup 360 comparador con soporte de fases independientes y exportacion de tarjetas HD a 300 DPI"  

---

## 1. User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparación Cruzada por Fases en Matchup 360 (Priority: P1) 🎯 MVP

Como analista sabermétrico y aficionado de la LVBP, quiero comparar el rendimiento de dos jugadores en diferentes fases del torneo (ej: Temporada Regular vs Round Robin) o el mismo jugador contra sí mismo en distintas fases, para evaluar su evolución y rendimiento bajo presión.

**Why this priority**: Es el núcleo del requerimiento analítico. Los jugadores a menudo cambian de rol o son tomados como refuerzos en postemporada, lo que distorsiona comparaciones planas sin contexto de fase.

**Independent Test**: Seleccionar a Leandro Cedeño en Temporada Regular (Jugador 1) y a Leandro Cedeño en Round Robin (Jugador 2) y verificar que sus métricas, percentiles y gráficos de radar reflejen de forma independiente los números de cada etapa.

**Acceptance Scenarios**:
1. **Given** un usuario en el comparador Matchup 360, **When** selecciona una fase global en "Sincronizar Fase", **Then** ambos jugadores se actualizan inmediatamente a dicha fase.
2. **Given** un usuario que desea comparar dos fases distintas, **When** modifica el selector de fase individual del Jugador 1 o Jugador 2, **Then** solo se recalculan las estadísticas y percentiles del jugador respectivo frente al universo de esa fase sin afectar al otro.

---

### User Story 2 - Preservación Canónica de Franquicias y Refuerzos (Priority: P2)

Como usuario de la app, quiero que la franquicia asignada a cada jugador corresponda fielmente a la fase que disputó (Leandro Cedeño en Leones del Caracas en Temporada Regular, y con Navegantes del Magallanes en Round Robin / Serie Final), y que en la vista general conserve su pertenencia canónica original.

**Why this priority**: Evita la distorsión donde un jugador refuerzo de postemporada aparezca incorrectamente afiliado a un equipo rival durante la temporada regular.

**Independent Test**: Consultar las estadísticas de bateo en Temporada Regular (`phase='R'`) y verificar que Leandro Cedeño pertenezca al equipo Caracas (`695`, `CAR`), y en Round Robin (`phase='L'`) pertenezca a Magallanes (`696`, `MAG`).

**Acceptance Scenarios**:
1. **Given** la consulta de temporada regular, **When** se agrupan las estadísticas de bateadores, **Then** Leandro Cedeño tiene como equipo `CAR`.
2. **Given** la consulta agregada de todas las fases (`phase='all'`), **When** se resuelve el equipo principal, **Then** se asigna modalmente el equipo de temporada regular (`game_type == 'R'`), preservando `CAR`.

---

### User Story 3 - Exportación de Tarjeta Matchup 360 en Alta Resolución (300 DPI) y UTF-8 (Priority: P3)

Como analista que comparte contenido en redes sociales o reportes impresos/digitales, quiero descargar la tarjeta gráfica PNG de Matchup 360 en alta resolución (1360px de ancho, 300 DPI) con tipografía TrueType nítida y caracteres con acentos impecables (`ñ`, `á`, `é`, `í`, `ó`, `ú`).

**Why this priority**: La tarjeta descargable es el entregable de difusión de la plataforma; la baja resolución o fuentes bitmap por defecto degradan la calidad visual y rompen los nombres de jugadores venezolanos.

**Independent Test**: Generar la tarjeta PNG invocando `build_matchup_image` y verificar que las dimensiones sean exactamente de 1360px de ancho, los metadatos contengan `dpi=(300, 300)` y los textos con caracteres como `Leandro Cedeño` no contengan símbolos de reemplazo.

**Acceptance Scenarios**:
1. **Given** dos jugadores seleccionados en Matchup 360, **When** el usuario presiona "Descargar Tarjeta Matchup 360", **Then** se descarga un PNG con resolución $1360 \times 780$ a 300 DPI.
2. **Given** nombres de jugadores con tildes o eñes, **When** se renderiza la imagen en Linux/Docker, **Then** la tipografía `DejaVuSans` dibuja perfectamente todos los glifos.

---

### Edge Cases & Data Boundaries

- **Jugadores sin turnos en una fase**: Si un jugador no participó en Round Robin, el selector solo debe mostrar jugadores con registros en dicha fase o deshabilitar el cálculo con mensaje informativo sin generar excepciones `ZeroDivisionError`.
- **Manejo de percentiles con pool pequeño**: En fases con pocos jugadores (Serie Final con solo 2 equipos), los percentiles relativos se calculan sobre el subconjunto disponible sin fallar por divisiones entre cero (`min=0`, `max=100`).
- **Compatibilidad multiplataforma de fuentes**: Si por algún motivo fallara la ruta local de fuentes, debe existir un mecanismo de fallback controlado que no interrumpa la ejecución.

---

## 2. Invariantes de Dominio y Contrato de Datos *(mandatory)*

### B. Sabermetría / Deportes (LVBP / LIDOM):
- [x] **Esquema relacional Supabase**: Tablas `batting_stats`, `pitching_stats`, `games`, `players` inmutables, sin alterar columnas existentes.
- [x] **Convención de temporada**: Identificador `season=2025` respetado.
- [x] **Constantes sabermétricas**: Métricas calculadas con fórmulas de la temporada activa.
- [x] **Idioma**: Interfaz, etiquetas, tooltips y mensajes 100% en **español**.
- [x] **Acceso defensivo**: Uso estricto de `.get()` y fallbacks de dominio al acceder a diccionarios de métricas.

---

## 3. Requerimientos Funcionales *(mandatory)*

- **FR-001**: El estado reactivo de individuales DEBE soportar `comparator_phase_1`, `comparator_phase_2` y `comparator_global_phase`.
- **FR-002**: El dataset de evaluación DEBE consultar y almacenar en caché las métricas por fase (`R`, `L`, `F`, `all`) de forma independiente.
- **FR-003**: La tarjeta gráfica DEBE generarse a escala $2.0\times$ (1360px de ancho) e incorporar metadatos de 300 DPI (`dpi=(300, 300)`).
- **FR-004**: La tipografía de la tarjeta DEBE utilizar fuentes TrueType `DejaVuSans.ttf` empaquetadas en el repositorio para garantizar renderizado idéntico en Windows y Linux.

---

## 4. Criterios de Éxito y Demostración Cuantificable *(mandatory)*

- **SC-001**: Los 162 tests automatizados de la suite pasan al 100% (`OK`).
- **SC-002**: La imagen generada tiene exactamente un ancho de 1360px y metadatos de 300 DPI comprobables por análisis binario de chunks PNG (`pHYs`).
- **SC-003**: Despliegue en contenedor Docker en VPS Hostinger activo, respondiendo `HTTP 200` y WebSocket `101 Switching Protocols`.

---

## 5. Supuestos y Dependencias

- Dependencia de datos históricos en Supabase (`batting_stats`, `pitching_stats`, `games`).
- Suposición de que los códigos de fase en MLB Stats API / Supabase son `R` (Regular), `L` (Round Robin / Semifinal), `F` (Final).
