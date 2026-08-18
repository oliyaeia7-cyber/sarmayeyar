from pydantic import BaseModel, EmailStr


class AnalysisResponse(BaseModel):
    symbol: str
    is_demo: bool
    last_price: float
    daily_change: float
    technical_score: float
    sentiment_score: float
    risk_score: float
    final_score: float
    scenario_bullish: float
    scenario_neutral: float
    scenario_bearish: float
    risk_label: str
    verdict_label: str
    disclaimer: str


class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ContactIn(BaseModel):
    name: str
    email: EmailStr
    message: str
