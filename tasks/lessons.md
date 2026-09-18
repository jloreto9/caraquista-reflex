# Lessons Learned — República Caraquista (caraquista-reflex)

## Visualización y Tarjetas de Pitcheo (Matplotlib / Thomas Nestico)

### 1. Arquitectura de GridSpec (20x20)
- **Cabecera:** El headshot debe asignarse exclusivamente a `gs[1, 1]`, la biografía a `gs[1, 2:6]` (garantizando 72 unidades de ancho para evitar colisiones con fotos o logos), y el logo a `gs[1, 6]`.
- **Textos de Biografía:** El nombre del lanzador debe posicionarse en `y=0.88` para balancearse verticalmente con el headshot y el logo, usando tamaños de fuente dinámicos según la longitud del rival o fecha.

### 2. Aislamiento del Panel Gráfico Triple (Fila 3)
- Nunca declarar los 3 subplots adyacentes directamente sobre el GridSpec principal sin espaciado.
- Debe utilizarse siempre: `GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[3, 1:7], wspace=0.36)` para garantizar un 36% de separación horizontal que impida el solapamiento de títulos y etiquetas de los ejes Y.

### 3. Consistencia Estadística en Modo PBP (LVBP)
- **Gráfico de Carga:** Barras apiladas (Strikes en la base + Bolas en la parte superior) con etiquetas enteras `Inn {i}` (nunca marcas decimales continuas).
- **Leverage Index:** Gráfico de líneas con cota visual promedio de 1.0 LI y etiquetas numéricas por punto.
- **Platoon Splits:** Comparar únicamente tasas porcentuales (0-100% para Strike%, Whiff% y CSW%) con etiquetas sobre las barras, y registrar el conteo absoluto de pitcheos (`N=X`) en la leyenda para evitar mezclas de escalas.
- **Fallback de Pitcheos:** `game_summary.get('pitches') or analysis.get('total_pitches') or len(pitches) or 0` para evitar desplegar 0 lanzamientos en el boxscore.

### 4. Pie de Página y Atribución
- Footer organizado en 2 líneas independientes para evitar colisiones: izquierda con marca `@republicaraquista • Jorge Leonardo Loreto`, centro con metodología/subtítulo y derecha con créditos a Thomas Nestico (@TJStats) y origen de la data.

### 5. Política de Base de Datos (Zero Bloat)
- La data Statcast de MLB/MiLB descargada debe almacenarse exclusivamente en caché local Parquet (`.cache/statcast/`) y nunca ocupar espacio ni tablas en Supabase.

## Políticas de Red y Prevención de Bloqueos (Curls & Timeouts)

### 1. Requisito Innegociable de Timeouts en `curl`
- **Nunca ejecutar `curl` sin límites de tiempo:** En shells, scripts `.sh` / `.bat`, Dockerfiles, workflows de CI/CD y healthchecks de contenedores, la invocación de `curl` sin banderas de timeout corre el riesgo de congelar el proceso indefinidamente si la conexión se bloquea o el servidor no responde ("fatal").
- **Tupla obligatoria de banderas en `curl`:**
  - En comprobaciones de salud o verificaciones de endpoints: `curl -f --connect-timeout 5 --max-time 15 ...`
  - En descargas e instalaciones en Dockerfile o scripts de setup: `curl -fsSL --connect-timeout 15 --max-time 120 --retry 3 --retry-delay 2 ...`
  - En verificaciones rápidas por CLI / PowerShell: `curl.exe -sS -I --connect-timeout 5 -m 10 ...`

### 2. Timeouts en Peticiones HTTP y Sockets en Python
- Todas las peticiones con `requests` o `urllib.request` deben declarar un argumento `timeout=` explícito (ej: `timeout=15` o `timeout=30`).
- Para blindar librerías de terceros que internamente abren sockets sin timeouts parametrizables (como `pybaseball` o clientes de APIs), debe definirse un timeout por defecto a nivel de socket del sistema operativo al inicio del proceso:
  ```python
  import socket
  socket.setdefaulttimeout(30.0)
  ```
