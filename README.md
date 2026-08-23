# 🦁 República Caraquista Web (Reflex Edition)

> Plataforma de **Analítica Avanzada y Sabermetría** para los **Leones del Caracas** y la **Liga Venezolana de Béisbol Profesional (LVBP)**, desarrollada con **[Reflex](https://reflex.dev)** (React/Next.js frontend + FastAPI backend).

---

## ⚾ Visión General

**República Caraquista Web** es la evolución visual y de rendimiento de la plataforma sabermétrica de los Leones del Caracas. Diseñada bajo un enfoque de **Single Page Application (SPA)** moderna, ofrece una experiencia de usuario fluida, reactiva y con estética deportiva de primer nivel inspirada en los colores y la identidad del club capitalino.

---

## 🚀 Características Principales

### 1. 📊 Dashboard Ejecutivo & Standings
- **Scoreboard de Último Juego:** Marcador interactivo cara a cara con escudos oficiales transparentes de los 8 equipos de la LVBP.
- **Tabla de Posiciones Oficial:** Clasificación de ronda regular con cálculo de porcentaje de victorias ($PCT$), juegos de diferencia ($GB$), rachas, récord local/visitante y diferencial de carreras ($RS - RA$).
- **KPIs en Tiempo Real:** Tarjetas dinámicas con la posición en la tabla, balance $W-L$, racha inmediata y balance ofensivo/defensivo.

### 2. 📈 Modelos Sabermétricos & Simulación Monte Carlo
- **Ratings ELO:** Evaluación dinámica de poder de cada franquicia ajustada por localía y dificultad del calendario.
- **Simulador Monte Carlo:** Proyección de 5,000 iteraciones estocásticas para probabilidades de clasificación, comodín, Round Robin y Serie Final.

### 3. ⚡ Win Expectancy & WPA (Win Probability Added)
- **Motor Tango RE24:** Modelo de 24 estados base-out para medir el impacto exacto de cada jugada en la probabilidad de victoria.
- **Leverage Index (LI) & Clutch:** Identificación de situaciones de máxima tensión y cálculo de los MVPs sabermétricos de cada encuentro.

### 4. 🛡️ Analítica de Bullpen & Splits Situacionales
- **Control de Corredores Heredados (IR / IRS):** Métrica precisa de efectividad de relevistas apagafuegos ($IRS\%$) y retención de ventaja.
- **Splits Situacionales Exactos:** Desglose en $RISP$, $Clutch$ con 2 outs, bases llenas, y enfrentamientos bateador vs. lanzador ($BvP$).

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Framework Full-Stack** | [Reflex](https://reflex.dev) (Python a React/Next.js + FastAPI) |
| **Diseño & UI** | [Radix UI](https://www.radix-ui.com/), Tailwind CSS, Lucide Icons |
| **Backend & APIs** | Python 3.12, FastAPI, WebSockets, MLB Stats API |
| **Base de Datos** | [Supabase](https://supabase.com) (PostgreSQL) |
| **Procesamiento de Datos** | pandas, numpy, scipy, concurrent.futures |

---

## 📂 Estructura del Proyecto

```
caraquista-reflex/
├── assets/                  # Identidad de marca (logo.png, favicon, assets estáticos)
├── caraquista_reflex/       # Aplicación Reflex
│   ├── components/          # Componentes modulares (navbar, scoreboard, kpi_grid, standings)
│   ├── pages/               # Vistas (Index, Standings, Situacional, WPA, Bullpen)
│   ├── state/               # Estado reactivo y controladores (AppState)
│   ├── styles/              # Paleta de colores oficial, estilos de tarjetas y temas
│   └── caraquista_reflex.py # Punto de entrada y enrutador de la app
├── core/                    # Motores analíticos y clientes de datos
│   ├── cache.py             # Decorador de caché en memoria con TTL
│   ├── elo.py               # Motor ELO y simulador estocástico Monte Carlo
│   ├── situational.py       # Motor de tracking situacional estado por estado
│   ├── supabase_client.py   # Cliente de base de datos Supabase
│   ├── teams.py             # Mapeo oficial de los 8 equipos LVBP y CDN MLB
│   └── wpa_engine.py        # Motor RE24 de Win Expectancy y WPA
├── rxconfig.py              # Configuración del proyecto Reflex
└── requirements.txt         # Dependencias del proyecto
```

---

## ⚙️ Instalación y Configuración Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/jloreto9/caraquista-reflex.git
cd caraquista-reflex
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
SUPABASE_KEY=tu-api-key-anonima
OPENAI_API_KEY=tu-openai-key-opcional
```

### 4. Iniciar la aplicación
```bash
reflex run
```
La aplicación se compilará y estará disponible en `http://localhost:3000` (Frontend) y `http://localhost:8000` (Backend FastAPI).

---

## 🦁 Identidad y Colores Oficiales

- **Caracas Navy:** `#070B19` / `#0D152B`
- **Oro Caraquista:** `#FDB827` / `#FFC72C`
- **Texto Principal:** `#FFFFFF`
- **Texto Secundario:** `#94A3B8`

---

## 👤 Autor

**Jorge Leonardo Loreto**  
*Científico de Datos & Economista*  
- Twitter: [@JorgeLoreto](https://twitter.com/JorgeLoreto) / [@RepubCaraquista](https://twitter.com/RepubCaraquista)  
- GitHub: [@jloreto9](https://github.com/jloreto9)
