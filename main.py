from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine, SessionLocal
from app.config import settings
from app import models
from app.security import hash_password
from app.seo_data import DEFAULT_ASSETS
from app.routers import pages, auth_router, admin, api

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.SITE_NAME_EN,
    description=settings.SITE_DESCRIPTION,
    version="1.0.0",
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(auth_router.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    try:
        # ادمین پیش‌فرض
        admin_user = db.query(models.User).filter(models.User.email == settings.ADMIN_EMAIL).first()
        if not admin_user:
            db.add(models.User(
                full_name="مدیر سرمایه‌یار",
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
                plan="pro",
            ))
        # دارایی‌های پیش‌فرض
        if db.query(models.WatchedAsset).count() == 0:
            for i, a in enumerate(DEFAULT_ASSETS):
                db.add(models.WatchedAsset(
                    symbol=a["symbol"], display_name_fa=a["display_name_fa"],
                    category=a["category"], is_featured=True, sort_order=i,
                ))
        # چند مقاله نمونه برای شروع سریع سئوی محتوایی
        if db.query(models.BlogPost).count() == 0:
            sample_posts = [
                {
                    "title": "تحلیل تکنیکال چیست و چگونه کار می‌کند؟",
                    "slug": "technical-analysis-چیست",
                    "excerpt": "آشنایی با مفاهیم پایه تحلیل تکنیکال، میانگین متحرک و RSI برای شروع تحلیل بازار.",
                    "content": (
                        "تحلیل تکنیکال روشی برای بررسی حرکت گذشته قیمت است تا احتمال رفتار آینده "
                        "برآورد شود. ابزارهایی مانند میانگین متحرک، RSI و MACD به شناسایی روند و "
                        "نقاط اشباع خرید یا فروش کمک می‌کنند.\n\n"
                        "نکته مهم این است که تحلیل تکنیکال قطعیت ندارد؛ به همین دلیل سرمایه‌یار آن "
                        "را در کنار اخبار و ریسک ترکیب می‌کند تا یک تصویر کامل‌تر و احتمالاتی ارائه دهد."
                    ),
                    "meta_description": "آموزش ساده تحلیل تکنیکال بازار برای مبتدیان.",
                    "keywords": "آموزش تحلیل تکنیکال, میانگین متحرک, RSI",
                },
                {
                    "title": "مدیریت ریسک در سرمایه‌گذاری چرا مهم‌تر از پیش‌بینی قیمت است؟",
                    "slug": "modiriat-risk-sarmayegozari",
                    "excerpt": "هیچ تحلیلی بدون ارزیابی ریسک کامل نیست؛ اینجا یاد می‌گیرید چرا.",
                    "content": (
                        "بسیاری از سرمایه‌گذاران تازه‌کار تمام تمرکز خود را روی پیش‌بینی جهت قیمت "
                        "می‌گذارند، درحالی‌که مدیریت ریسک تعیین می‌کند چه مقدار سرمایه در معرض خطر باشد.\n\n"
                        "نوسان تاریخی و حداکثر افت از قله دو شاخص ساده اما قدرتمند برای سنجش ریسک "
                        "هستند که سرمایه‌یار در امتیاز نهایی هر دارایی لحاظ می‌کند."
                    ),
                    "meta_description": "چرا مدیریت ریسک از پیش‌بینی قیمت مهم‌تر است؟",
                    "keywords": "مدیریت ریسک سرمایه گذاری, نوسان بازار",
                },
            ]
            for p in sample_posts:
                from datetime import datetime as _dt
                db.add(models.BlogPost(
                    title=p["title"], slug=p["slug"], excerpt=p["excerpt"], content=p["content"],
                    meta_description=p["meta_description"], keywords=p["keywords"],
                    is_published=True, created_at=_dt.utcnow(),
                ))
        db.commit()
    finally:
        db.close()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "site": settings.SITE_NAME}
