from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from caraquista_api.routers import health, elo, wpa, cards

app = FastAPI(
    title="República Caraquista • API Backend Sabermétrica",
    description=(
        "Servicio REST en Python de alto rendimiento que expone los motores analíticos, "
        "simulaciones Monte Carlo (5,000 iteraciones), matrices Tango RE24, Win Expectancy y "
        "generador de tarjetas gráficas HD a 300 DPI para consumo desacoplado por el frontend en Vercel."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuración de CORS segura para frontend en Vercel y desarrollo local
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://caraquista.srv929207.hstgr.cloud",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montaje de Routers
app.include_router(health.router)
app.include_router(elo.router)
app.include_router(wpa.router)
app.include_router(cards.router)

@app.get("/")
def root():
    return {
        "message": "República Caraquista Sabermetrics API v1",
        "docs": "/docs",
        "status": "online",
    }
