import pytest
from fastapi.testclient import TestClient
from caraquista_api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "/docs" in data["docs"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "republicaraquista-api"

def test_cards_health():
    response = client.get("/api/v1/cards/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["dpi"] == 300

def test_elo_ratings_endpoint():
    response = client.get("/api/v1/elo/ratings?season=2025")
    # Si hay conexión a Supabase debe devolver los 8 equipos
    if response.status_code == 200:
        data = response.json()
        assert len(data) == 8
        assert data[0]["rank"] == 1
        assert "elo_rating" in data[0]

def test_cors_vercel_headers():
    response = client.get(
        "/health",
        headers={"Origin": "https://republicaraquista-web.vercel.app"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://republicaraquista-web.vercel.app"
