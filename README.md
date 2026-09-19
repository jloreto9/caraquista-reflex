# 🦁 RepubliCaraquistApp Reflex

<div align="center">

[![Reflex Version](https://img.shields.io/badge/Reflex-0.9.8-3B82F6.svg?logo=react&logoColor=white)](https://reflex.dev)
[![Python Version](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com)
[![Tests](https://img.shields.io/badge/Tests-162%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](#-suite-de-pruebas-automatizadas)
[![Deploy](https://img.shields.io/badge/Production-Live%20on%20VPS-FDB827.svg?logo=docker&logoColor=black)](https://caraquista.srv929207.hstgr.cloud/)
[![Spec Kit](https://img.shields.io/badge/SDD-Spec%20Kit%20Ready-6F42C1.svg?logo=github&logoColor=white)](#-gobernanza-spec-driven-development-spec-kit)

**Plataforma Web Sabermétrica de Élite para los Leones del Caracas y la Liga Venezolana de Béisbol Profesional (LVBP)**

[⚾ Explorar Plataforma en Vivo](https://caraquista.srv929207.hstgr.cloud/) • [📖 Documentación](#-suite-de-8-vistas-spa) • [🛠️ Instalación Local](#-instalación-y-configuración-local)

</div>

---

## ⚾ Visión General

**RepubliCaraquistApp Reflex** es la plataforma sabermétrica de referencia para la Liga Venezolana de Béisbol Profesional (LVBP) y la fanaticada de los **Leones del Caracas**, construida como una **Single Page Application (SPA)** de alto rendimiento en **[Reflex](https://reflex.dev)** (React 19 / Next.js en frontend compilado y FastAPI en backend asíncrono con WebSockets persistentes).

La aplicación supera las limitaciones estéticas y de estado de plataformas monolíticas anteriores, ofreciendo una experiencia deportiva inmersiva, reactiva y con paridad matemática total contra los motores sabermétricos de MLB Stats API.

### Identidad Visual y Estética
- **Paleta Oficial:** Dark Navy profundo (`#070B19`), Tarjetas Glassmorphism con bordes sutiles (`#0D152B`, `#16203D`), Acentos dorados caraquistas (`#FDB827`) y Tipografía Inter/Geist.
- **Activos Oficiales:** Escudos vectoriales transparentes de los 8 equipos de la LVBP, logo oficial de **República Caraquista** (`assets/logo.png`) y fotos oficiales de MLB ID.

---

## 🚀 Suite Completa de 9 Vistas SPA

La plataforma cuenta con 9 módulos analíticos independientes y especializados:

| Ruta | Vista | Enfoque Sabermétrico Principal |
| :--- | :--- | :--- |
| `/` | **Centro de Mando & Resumen** | Scoreboard cara a cara, desglose Día/Noche (`day_record`), récord por semanas ISO de campeonato y KPIs en tiempo real. |
| `/standings` | **Posiciones & ELO** | Tabla oficial, Expectativa Pitagórica ($xW$), ratings ELO dinámicos y simulación Monte Carlo (5,000 iteraciones). |
| `/individuales` | **Estadísticas Individuales, Fildeo & Matchup 360** | Líderes generales Toda la LVBP, métricas avanzadas (wOBA, wRC+, FIP), Fildeo (FPCT, RF/9, CS%), y comparador Matchup 360 H2H con exportación HD a 300 DPI. |
| `/colectivas` | **Estadísticas Colectivas 8 Equipos** | Comparación de Bateo, Pitcheo y Fildeo colectivo entre las 8 franquicias de la LVBP con gráficos interactivos en Plotly. |
| `/wpa` | **Win Expectancy & WPA** | Curvas de probabilidad de victoria jugada a jugada, matriz Tango RE24 de 24 estados base-out, Leverage Index (LI) y momentos Clutch. |
| `/situacional` | **Splits Situacionales & LOB Tracker** | Rendimiento en RISP, Clutch con 2 outs, Bases Llenas, Platoon LHP/RHP, Tracker de Dejados en Base (LOB) y matriz BvP. |
| `/spray-charts` | **Spray Charts & Strike Zone** | Gráficos espaciales en diamante con modelo determinístico de dureza BIS, y mapas de calor 3x3 de disciplina en el plato. |
| `/bullpen` | **Bullpen & Alineaciones 1-9** | Efectividad de relevistas, control de corredores heredados ($IR$, $IRS$, $IRS\%$), retención de ventajas y matriz de calor de alineaciones. |
| `/pitching` | **Pitching Summary & Telemetría** | Telemetría Statcast Hawk-Eye (IVB, HB, Spin, Velo, Zone%) para MLB/MiLB, analítica PBP para Leones del Caracas (LVBP) y exportación de tarjeta HD a 300 DPI inspirada en Thomas Nestico (@TJStats). |

---

### 1. 📊 Centro de Mando (`/`)
- **Scoreboard Interactivo:** Marcador del encuentro más reciente con escudos de alta definición, líneas de anotación por entrada (R, H, E) y récord actualizado.
- **Splits Temporales y de Calendario:** Desglose de rendimiento en juegos de Día vs Noche y evolución histórica del porcentaje de victorias agrupado por semanas ISO del calendario oficial.
- **KPIs Sabermétricos de Alto Impacto:** Tarjetas con posición en tabla, balance $W-L$, diferencial de carreras ($RS - RA$) y expectativa pitagórica.

### 2. 🏆 Posiciones & Modelo ELO (`/standings`)
- **Tabla Oficial LVBP:** Juegos jugados ($G$), ganados ($W$), perdidos ($L$), porcentaje ($PCT$), juegos de diferencia ($GB$) y rachas.
- **Expectativa Pitagórica ($xW$):** Cálculo del récord esperado basado en la relación exponencial entre carreras anotadas y permitidas ($Exp = 1.83$).
- **Ratings ELO Dinámicos:** Modelo estocástico con rating base 400 que actualiza el poder relativo de cada equipo tras cada partido, ajustando por ventaja de localía (+24 pts) y dificultad del rival.
- **Simulador Monte Carlo:** Proyección de 5,000 torneos simulados calculando la probabilidad porcentual de clasificar al Round Robin, disputar la Serie Final y alzarse con el Campeonato.

### 3. 👤 Estadísticas Individuales, Fildeo & Comparador Matchup 360 (`/individuales`)
- **Universo Completo de la Liga:** Líderes de toda la LVBP por defecto (`"Toda la LVBP (Overall)"`) con selectores reactivos por franquicia y fase.
- **Bateo Tradicional y Sabermétrico:** AVG, OBP, SLG, OPS, ISO, BABIP, wOBA (con coeficientes calibrados de la temporada) y wRC+ (con factor de liga y parque).
- **Pitcheo Tradicional y de Precisión:** ERA, WHIP, FIP (Fielding Independent Pitching), K/9, BB/9, K/BB, IP, SV.
- **Pestaña de Fildeo / Defensa Individual:** Métricas detalladas de guante y receptoría: Outs realizados ($PO$), Asistencias ($A$), Errores ($E$), Total de Chances ($TC$), Porcentaje de Fildeo ($FPCT$), Doble Plays ($DP$), Factor de Alcance por 9 innings ($RF/9$), Corredores Atrapados ($CS$), Bases Robadas Permitidas ($SB$), Porcentaje de Atrapados ($CS\%$) y Passed Balls ($PB$).
- **Comparador Matchup 360 Head-to-Head (H2H):**
  - Selectores independientes de franquicia, jugador y **fase de campeonato** (*Temporada Regular*, *Round Robin*, *Serie Final*, *Todas las Fases*) para Jugador 1 y Jugador 2, con control de **Sincronización Global**.
  - Asignación canónica por fase: Leandro Cedeño figura fielmente en Leones del Caracas en Temporada Regular y con Navegantes del Magallanes en postemporada (donde actuó como refuerzo).
  - **Radar Polar de 8 Dimensiones:** Percentiles normalizados relativos al universo específico de la fase seleccionada ($P_0$ a $P_{100}$).
  - Desglose estructurado por 4 categorías clave: *Ofensiva Sabermétrica*, *Volumen Expandido*, *Corrido de Bases* y *Defensa/Fildeo*.
- **Exportación de Tarjeta Gráfica en Alta Resolución (300 DPI):**
  - Generación en un clic de tarjetas descargables PNG a escala 2x (**1360 px de ancho**).
  - Metadatos incrustados de **300 DPI** (`dpi=(300, 300)`).
  - Tipografía TrueType empaquetada (`DejaVuSans`) con renderizado impecable de caracteres Unicode (`á`, `é`, `ñ`, `Ú`, `·`, `—`).
  - Badges de fase específicos para cada jugador y avatares circulares HD de $128 \times 128\text{ px}$.

### 4. 👥 Estadísticas Colectivas 8 Equipos (`/colectivas`)
- Comparativas de franquicias en gráficos de barras horizontales interactivos en Plotly:
  - Bateo colectivo: AVG, OBP, SLG, OPS, HR, Carreras Anotadas.
  - Pitcheo colectivo: ERA, WHIP, FIP, Ponches y Boletos.
  - Fildeo colectivo: Porcentaje de fildeo global ($FPCT$), asistencias y doble matanzas.

### 5. ⚡ Win Expectancy & Análisis WPA (`/wpa`)
- **Curvas Interactivas de Win Probability:** Visualización jugada a jugada de la probabilidad de victoria a lo largo de los 9 episodios (y extra-innings).
- **Matriz Tango RE24:** Modelo de 24 estados (*Run Expectancy*) cruzando combinaciones de corredores en base (Bases Limpias, 1B, 2B, 3B, 1B-2B, 1B-3B, 2B-3B, Llenas) y outs (0, 1, 2).
- **Leverage Index (LI) & Clutch:** Medición del apalancamiento emocional del juego e identificación de los momentos definitorios y líderes de WPA acumulado.

### 6. 🎯 Splits Situacionales & LOB Tracker (`/situacional`)
- Rendimiento en situaciones de alta presión: con corredores en posición de anotar ($RISP$), $Clutch$ con 2 outs en RISP, y con bases llenas.
- Platoon split: Rendimiento ante lanzadores zurdos ($LHP$) vs. derechos ($RHP$).
- **Tracker de Dejados en Base (LOB Tracker):** Conteo exacto de hombres dejados en base a lo largo de cada entrada, desglosando específicamente el 3er out y RISP LOB.
- **Matriz BvP:** Registro histórico de enfrentamientos cara a cara entre bateador y lanzador.

### 7. 💎 Spray Charts & Strike Zone (`/spray-charts`)
- **Spray Charts Espaciales en Diamante:** Gráficos de dispersión en coordenadas de campo con modelo determinístico de dureza BIS (*Baseball Info Solutions*): $41.2\%$ Hard, $48.5\%$ Medium, $10.4\%$ Soft.
- **Strike Zone 3x3:** Mapas de calor de disciplina en el plato: $O\text{-}Swing\%$, $Z\text{-}Contact\%$, $SwStr\%$, $CSW\%$.
- *(Nota de dominio: Se excluyen métricas de Statcast como Launch Angle o Barrels al no existir infraestructura Hawkeye en la LVBP).*

### 8. 🛡️ Analítica de Bullpen & Líneas de Alineación (`/bullpen`)
- **Control de Corredores Heredados:** Corredores heredados ($IR$), corredores anotados ($IRS$) y tasa de prevención ($IRS\%$).
- **Matriz de Calor de Alineaciones 1-9:** Desglose del aporte ofensivo según el turno al bate y récord del equipo con alineaciones titulares específicas.

### 9. 🔥 Pitching Summary & Telemetría Nestico (`/pitching`)
- **Buscador Universal Multiliga:** Búsqueda en tiempo real de lanzadores cubriendo Leones del Caracas (LVBP), Liga Mexicana de Béisbol (LMB Verano, `sportId=23`) y MLB/MiLB.
- **Filtro Reactivo por Fases:** Desglose por *Temporada Regular*, *Round Robin*, *Serie Final*, *Postemporada* y *Todas las Fases*.
- **Historial de Salidas & Decisiones:** Detección automática del rol (*Abridor* / *Relevista*) y decisión oficial (*W*, *L*, *SV*, *HLD*), métricas de dominio ($IP$, $H$, $CL$, $BB$, $K$) y telemetría de lanzamientos (P-S, $CSW\%$, $Whiff\%$).
- **Tarjeta de Exportación Gráfica HD (2400 x 2400 px a 300 DPI):**
  - Formato vertical de póster sabermétrico unificado inspirado en Thomas Nestico (@TJStats).
  - **Rama LVBP / LMB:** Gráficos de carga por episodio (Strikes vs Bolas apiladas), índice de apalancamiento Leverage Index (Tango RE24), splits LHB/RHB y tabla histórica de salidas.
  - **Rama MLB / MiLB:** Telemetría Hawk-Eye completa, ridgeplots de velocidad, quiebre inducido (iVB vs HB), evolución de repertorio (5-Game Rolling Usage) y matriz de repertorio con mapas de calor relativos a MLB.

---

## 🛠️ Stack Tecnológico y Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                       Cliente Web                           │
│     SPA React / Next.js / Tailwind CSS / Radix UI           │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / WSS (_event)
┌──────────────────────────────▼──────────────────────────────┐
│                    Traefik Edge Router                      │
│            SSL Automático Let's Encrypt / Proxy             │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP :3000
┌──────────────────────────────▼──────────────────────────────┐
│                  Contenedor Docker Multi-Stage              │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │   Caddy Web Server    │──────>│     Reflex Backend    │  │
│  │   (Daemon Proxy :3000)│       │    (FastAPI :8000)    │  │
│  └───────────────────────┘       └───────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │ PostgreSQL SSL
┌──────────────────────────────▼──────────────────────────────┐
│                  Supabase Cloud Database                    │
│     batting_stats • pitching_stats • games • players        │
└─────────────────────────────────────────────────────────────┘
```

| Capa | Tecnologías |
| :--- | :--- |
| **Frontend SPA** | Reflex 0.9.8 (React 19 / Next.js, Radix UI, Lucide Icons, Tailwind CSS) |
| **Backend & WebSockets** | Python 3.12, FastAPI, Starlette, Uvicorn, Pillow (Generación HD) |
| **Base de Datos & Almacenamiento** | Supabase (PostgreSQL), decoradores de caché en memoria con TTL |
| **Visualización Científica** | Plotly 6.0, KaTeX (renderizado matemático) |
| **Fuentes & Assets** | TrueType `DejaVuSans.ttf` empaquetadas en repositorio |
| **Infraestructura de Despliegue** | Docker Multi-Stage, Caddy Server, Traefik, Hostinger KVM2 VPS |

---

## 📂 Estructura del Repositorio

```
republicaraquistapp-reflex/
├── assets/                       # Activos de marca, logos y fuentes TrueType
│   ├── fonts/                    # DejaVuSans.ttf y DejaVuSans-Bold.ttf (Unicode HD)
│   ├── logo.png                  # Logo oficial de República Caraquista
│   └── favicon.ico               # Favicon
├── core/                         # Motores sabermétricos compartidos
│   ├── cache.py                  # Caché en memoria con TTL configurable
│   ├── elo.py                    # Algoritmo ELO y simulador Monte Carlo
│   ├── matchup_card.py           # Generador gráfico de tarjetas Matchup 360 (300 DPI)
│   ├── situational.py            # Tracking estado por estado y LOB Tracker
│   ├── spray_chart.py            # Modelo espacial de spray chart BIS
│   ├── strike_zone.py            # Mapas 3x3 de disciplina en el plato
│   ├── supabase_client.py        # Cliente Supabase con pertenencia canónica modal
│   ├── teams.py                  # Mapeo de los 8 equipos LVBP y CDN oficial
│   └── wpa_engine.py             # Matriz Tango RE24 de 24 estados y WPA
├── republicaraquistapp/          # Código fuente de la aplicación Reflex
│   ├── components/               # Componentes UI (Navbar, Scoreboard, Standings, etc.)
│   ├── pages/                    # Vistas SPA (index, standings, individuales, etc.)
│   ├── state/                    # Manejadores de estado reactivo (AppState, IndividualesState)
│   ├── styles/                   # Paleta Dark Navy, temas y estilos globales
│   └── republicaraquistapp.py    # Punto de entrada y enrutador principal
├── scripts/                      # Pipelines de ingesta y tareas de fondo
│   └── ingest_lvbp_batch.py      # ETL concurrente multi-hilo para 4 temporadas
├── specs/                        # Marco de Gobernanza Spec-Driven Development (SDD)
│   ├── 001-matchup360-phases-export/ # Especificación Matchup 360 y tarjetas 300 DPI
│   └── 002-republicaraquistapp-reflex-readme/ # Renombrado y modernización de README
├── tests/                        # Suite completa de 162 pruebas automatizadas
│   ├── test_matchup360_overall.py# Pruebas de Matchup 360, fases y 300 DPI
│   ├── test_sabermetrics.py      # Validación matemática de fórmulas avanzadas
│   └── ...                       # Tests de integración, ELO y WPA
├── Caddyfile                     # Configuración de proxy inverso de producción
├── Dockerfile                    # Construcción Docker multi-etapa optimizada
├── docker-compose.yml            # Orquestación de producción con Traefik
├── entrypoint.sh                 # Script de arranque dual Caddy + Reflex
├── requirements.txt              # Dependencias de Python
└── rxconfig.py                   # Configuración de la aplicación Reflex
```

---

## ⚡ Pipeline de Ingesta por Lotes (ETL)

La aplicación cuenta con un pipeline de ingesta masiva automatizado en [`scripts/ingest_lvbp_batch.py`](file:///c:/Users/Administrator/Projets/caraquista-reflex/scripts/ingest_lvbp_batch.py):
- **Concurrencia:** `ThreadPoolExecutor(max_workers=12)` consumiendo la API oficial de MLB Stats (`sportId=17`, `leagueId=135`).
- **Cobertura Histórica:** **4 temporadas consolidadas (2022, 2023, 2024 y 2025)**.
- **Volumen Procesado:** **1,161 juegos oficiales**, 2,089 registros de bullpen y 2,182 alineaciones 1 al 9.
- **Persistencia Atómica:** Upserts por lotes en Supabase con resolución de conflictos en claves compuestas (`on_conflict="game_id,player_id"`).
- **Automatización CI/CD:** GitHub Actions en [`.github/workflows/daily_ingest_lvbp.yml`](file:///c:/Users/Administrator/Projets/caraquista-reflex/.github/workflows/daily_ingest_lvbp.yml) ejecutándose diariamente a las 06:00 UTC (02:00 AST).

---

## 🧪 Suite de Pruebas Automatizadas

El proyecto cuenta con una cobertura integral de **162 pruebas unitarias y de estrés adversario** pasando al 100%:

```bash
python -m unittest discover -s tests
```

```text
----------------------------------------------------------------------
Ran 162 tests in 17.677s

OK
```

### Validaciones Clave Verificadas
- **Paridad Matemática Sabermétrica:** Cuadre exacto de wOBA, wRC+, FIP y matriz Tango RE24.
- **Fases y Refuerzos:** Preservación de la franquicia canónica de Leandro Cedeño en Caracas para temporada regular y Magallanes en postemporada.
- **Integridad Gráfica:** Detección binaria de chunks `pHYs` a 300 DPI y renderizado de caracteres Unicode sin glifos rotos.
- **Estado Reactivo:** Resiliencia ante desconexión de base de datos y fallbacks seguros con `.get()`.

---

## 📋 Gobernanza Spec-Driven Development (Spec Kit)

Este repositorio opera bajo el marco de **Spec-Driven Development (SDD)** gobernado por la [Constitución del Workspace](file:///c:/Users/Administrator/Projets/.specify/memory/constitution.md) y [`.agents/rules/spec-driven.md`](file:///c:/Users/Administrator/Projets/.agents/rules/spec-driven.md).

En cada ciclo de desarrollo, residen de forma innegociable los **4 Markdown canónicos** dentro del directorio `specs/<NNN-feature-slug>/`:

```text
specs/
└── 001-matchup360-phases-export/
    ├── spec.md                   # 1. Especificar (QUÉ): Historias de usuario, requerimientos y criterios de éxito
    ├── plan.md                   # 2. Planificar (CÓMO): Arquitectura, Escalera Ponytail y chequeo constitucional
    ├── tasks.md                  # 3. Tareas (ORDEN): Tareas atómicas numeradas T001..Tn por historias
    ├── implementation.md         # 4. Implementar (PRUEBAS): Informe de ejecución, evidencia de tests y convergencia
    └── checklists/
        └── requirements.md       # Checklist de completitud y calidad
```

---

## ⚙️ Instalación y Configuración Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/jloreto9/caraquista-reflex.git republicaraquistapp-reflex
cd republicaraquistapp-reflex
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-o-service-key
OPENAI_API_KEY=tu-api-key-opcional
```

### 4. Iniciar la aplicación
```bash
reflex run
```
La aplicación estará disponible en:
- **Frontend SPA:** `http://localhost:3000`
- **Backend FastAPI / WebSockets:** `http://localhost:8000`

---

## 🌐 Despliegue en Producción

El despliegue de producción se gestiona en un VPS Hostinger KVM2 mediante Docker Compose integrado a Traefik:

```bash
docker compose up -d --build
```

- **URL Pública:** **[https://caraquista.srv929207.hstgr.cloud/](https://caraquista.srv929207.hstgr.cloud/)**
- **Salud del Servicio:** Verificación automática de Caddy en puerto 3000 y FastAPI en puerto 8000 con certificados SSL Let's Encrypt renovados automáticamente por Traefik.

---

## 📄 Licencia

Este proyecto es software libre desarrollado por **Jorge Leonardo Loreto** bajo la Licencia MIT. Las estadísticas oficiales de juego y marcas comerciales de los equipos pertenecen a la Liga Venezolana de Béisbol Profesional (LVBP) y a la MLB.
