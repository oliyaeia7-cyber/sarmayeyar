from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.scoring_engine import analyze

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/analysis/{symbol}", response_model=schemas.AnalysisResponse)
def api_analysis(symbol: str, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    """
    نقطه ورود API برای مشترکین حرفه‌ای/توسعه‌دهندگان.
    در نسخه تولیدی، x_api_key باید در برابر جدول کلیدهای فعال اعتبارسنجی شود.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="کلید API ارسال نشده است (هدر X-API-Key).")
    try:
        result = analyze(symbol.strip())
    except Exception:
        raise HTTPException(status_code=400, detail="تحلیل این نماد ممکن نشد.")
    return schemas.AnalysisResponse(
        symbol=result.symbol, is_demo=result.is_demo, last_price=result.last_price,
        daily_change=result.daily_change, technical_score=result.technical_score,
        sentiment_score=result.sentiment_score, risk_score=result.risk_score,
        final_score=result.final_score, scenario_bullish=result.scenario_bullish,
        scenario_neutral=result.scenario_neutral, scenario_bearish=result.scenario_bearish,
        risk_label=result.risk_label, verdict_label=result.verdict_label,
        disclaimer=result.disclaimer,
    )


@router.get("/assets")
def api_assets(db: Session = Depends(get_db)):
    assets = db.query(models.WatchedAsset).all()
    return [{"symbol": a.symbol, "name": a.display_name_fa, "category": a.category} for a in assets]
