from fastapi import APIRouter, HTTPException, Query, Response
from typing import Dict, Any, Optional
import io
from PIL import Image

router = APIRouter(prefix="/api/v1/cards", tags=["HD Graphic Cards (300 DPI)"])

@router.get("/health")
def cards_health():
    return {"status": "ok", "module": "cards", "dpi": 300}

@router.post("/matchup")
def generate_matchup_card(payload: Dict[str, Any]):
    """
    Genera una tarjeta panorámica descargable Matchup 360 Head-to-Head
    en PNG HD a 300 DPI con avatares, radar y desglose sabermétrico.
    """
    try:
        from core.matchup_card import build_matchup_image

        p1_data = payload.get("p1", {})
        p2_data = payload.get("p2", {})
        category = payload.get("category", "bateo")

        img: Image.Image = build_matchup_image(p1_data, p2_data, category=category)

        buf = io.BytesIO()
        img.save(buf, format="PNG", dpi=(300, 300))
        png_bytes = buf.getvalue()

        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={"Content-Disposition": 'inline; filename="matchup_360.png"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando tarjeta Matchup 360: {str(e)}")
