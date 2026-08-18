from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.deps import get_current_user
from app import models
from app.config import settings
from app.seo_data import PAGE_META, DEFAULT_ASSETS, PRIMARY_KEYWORDS
from app.services.scoring_engine import analyze

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def base_ctx(request: Request, db: Session, page_key: str):
    meta = PAGE_META.get(page_key, PAGE_META["home"])
    return {
        "request": request,
        "user": get_current_user(request, db),
        "settings": settings,
        "meta": meta,
        "page_key": page_key,
    }


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    ctx = base_ctx(request, db, "home")
    featured = db.query(models.WatchedAsset).filter(
        models.WatchedAsset.is_featured == True  # noqa: E712
    ).order_by(models.WatchedAsset.sort_order).all()
    if not featured:
        featured = [models.WatchedAsset(**a) for a in DEFAULT_ASSETS]
    posts = db.query(models.BlogPost).filter(
        models.BlogPost.is_published == True  # noqa: E712
    ).order_by(models.BlogPost.created_at.desc()).limit(3).all()
    ctx.update({"featured_assets": featured, "recent_posts": posts,
                "keywords_cloud": PRIMARY_KEYWORDS})
    return templates.TemplateResponse("index.html", ctx)


@router.get("/analysis")
def analysis_form(request: Request, symbol: str | None = None, db: Session = Depends(get_db)):
    ctx = base_ctx(request, db, "home")
    ctx["meta"] = {
        "title": f"تحلیل {symbol} | سرمایه‌یار" if symbol else "تحلیل دارایی | سرمایه‌یار",
        "description": "تحلیل احتمالاتی، تکنیکال، اخبار و ریسک دارایی موردنظر شما.",
        "keywords": "تحلیل بورس, تحلیل رمزارز, تحلیل تکنیکال",
    }
    result = None
    error = None
    if symbol:
        user = ctx["user"]
        if not user:
            today_count = None
        else:
            if user.plan == "free":
                from datetime import datetime, timedelta
                since = datetime.utcnow() - timedelta(days=1)
                today_count = db.query(func.count(models.AnalysisLog.id)).filter(
                    models.AnalysisLog.user_id == user.id,
                    models.AnalysisLog.created_at >= since,
                ).scalar()
                if today_count and today_count >= settings.FREE_DAILY_ANALYSIS_LIMIT:
                    error = (f"شما به سقف {settings.FREE_DAILY_ANALYSIS_LIMIT} تحلیل رایگان امروز رسیده‌اید. "
                              "برای تحلیل نامحدود، اشتراک حرفه‌ای تهیه کنید.")
        if not error:
            try:
                result = analyze(symbol.strip())
                log = models.AnalysisLog(
                    user_id=user.id if user else None,
                    symbol=result.symbol,
                    score=result.final_score,
                )
                db.add(log)
                db.commit()
            except Exception as e:
                error = "دریافت داده برای این نماد ممکن نشد. نماد را بررسی و دوباره تلاش کنید."
    ctx.update({"symbol": symbol, "result": result, "error": error,
                "default_assets": DEFAULT_ASSETS})
    return templates.TemplateResponse("analysis.html", ctx)


@router.get("/pricing")
def pricing(request: Request, db: Session = Depends(get_db)):
    ctx = base_ctx(request, db, "pricing")
    return templates.TemplateResponse("pricing.html", ctx)


@router.get("/about")
def about(request: Request, db: Session = Depends(get_db)):
    ctx = base_ctx(request, db, "about")
    return templates.TemplateResponse("about.html", ctx)


@router.get("/contact")
def contact_get(request: Request, db: Session = Depends(get_db)):
    ctx = base_ctx(request, db, "contact")
    ctx["sent"] = False
    return templates.TemplateResponse("contact.html", ctx)


@router.post("/contact")
def contact_post(request: Request, db: Session = Depends(get_db),
                  name: str = Form(...), email: str = Form(...), message: str = Form(...)):
    db.add(models.ContactMessage(name=name, email=email, message=message))
    db.commit()
    ctx = base_ctx(request, db, "contact")
    ctx["sent"] = True
    return templates.TemplateResponse("contact.html", ctx)


@router.get("/blog")
def blog_index(request: Request, db: Session = Depends(get_db)):
    ctx = base_ctx(request, db, "blog")
    posts = db.query(models.BlogPost).filter(
        models.BlogPost.is_published == True  # noqa: E712
    ).order_by(models.BlogPost.created_at.desc()).all()
    ctx["posts"] = posts
    return templates.TemplateResponse("blog/index.html", ctx)


@router.get("/blog/{slug}")
def blog_post(slug: str, request: Request, db: Session = Depends(get_db)):
    post = db.query(models.BlogPost).filter(models.BlogPost.slug == slug).first()
    ctx = base_ctx(request, db, "blog")
    if post:
        ctx["meta"] = {
            "title": f"{post.title} | سرمایه‌یار",
            "description": post.meta_description or post.excerpt,
            "keywords": post.keywords or "",
        }
    ctx["post"] = post
    return templates.TemplateResponse("blog/post.html", ctx)


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {settings.SITE_URL}/sitemap.xml\n"
    )


@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    urls = ["/", "/pricing", "/about", "/contact", "/blog"]
    posts = db.query(models.BlogPost).filter(
        models.BlogPost.is_published == True  # noqa: E712
    ).all()
    for p in posts:
        urls.append(f"/blog/{p.slug}")
    for a in DEFAULT_ASSETS:
        urls.append(f"/analysis?symbol={a['symbol']}")

    body = "".join(
        f"<url><loc>{settings.SITE_URL}{u}</loc></url>" for u in urls
    )
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
    return PlainTextResponse(xml, media_type="application/xml")
