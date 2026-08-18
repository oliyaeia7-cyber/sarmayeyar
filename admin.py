from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from slugify import slugify

from app.database import get_db
from app.deps import get_current_user
from app import models
from app.config import settings
from app.security import verify_password, create_session_token, SESSION_COOKIE, SESSION_MAX_AGE

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def _require_admin(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        return None
    return user


def _redirect_login():
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/login")
def admin_login_get(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user and user.is_admin:
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", {
        "request": request, "settings": settings, "error": None,
        "meta": {"title": "ورود ادمین | سرمایه‌یار", "description": "", "keywords": ""},
    })


@router.post("/login")
def admin_login_post(request: Request, db: Session = Depends(get_db),
                      email: str = Form(...), password: str = Form(...)):
    user = db.query(models.User).filter(models.User.email == email.lower().strip()).first()
    if not user or not user.is_admin or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("admin/login.html", {
            "request": request, "settings": settings,
            "error": "اطلاعات ورود نادرست است یا دسترسی ادمین ندارید.",
            "meta": {"title": "ورود ادمین | سرمایه‌یار", "description": "", "keywords": ""},
        })
    token = create_session_token(user.id)
    resp = RedirectResponse(url="/admin", status_code=303)
    resp.set_cookie(SESSION_COOKIE, token, max_age=SESSION_MAX_AGE, httponly=True, samesite="lax")
    return resp


@router.get("/logout")
def admin_logout():
    resp = RedirectResponse(url="/admin/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@router.get("")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()

    since_7d = datetime.utcnow() - timedelta(days=7)
    stats = {
        "total_users": db.query(func.count(models.User.id)).scalar(),
        "pro_users": db.query(func.count(models.User.id)).filter(models.User.plan == "pro").scalar(),
        "total_analyses": db.query(func.count(models.AnalysisLog.id)).scalar(),
        "analyses_7d": db.query(func.count(models.AnalysisLog.id)).filter(
            models.AnalysisLog.created_at >= since_7d).scalar(),
        "unread_messages": db.query(func.count(models.ContactMessage.id)).filter(
            models.ContactMessage.is_read == False).scalar(),  # noqa: E712
        "blog_posts": db.query(func.count(models.BlogPost.id)).scalar(),
    }
    top_symbols = (
        db.query(models.AnalysisLog.symbol, func.count(models.AnalysisLog.id).label("c"))
        .group_by(models.AnalysisLog.symbol).order_by(func.count(models.AnalysisLog.id).desc()).limit(6).all()
    )
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "settings": settings, "admin": admin, "stats": stats,
        "top_symbols": top_symbols,
        "meta": {"title": "پنل مدیریت | سرمایه‌یار", "description": "", "keywords": ""},
        "page_key": "dashboard", "page_title": "داشبورد",
    })


# ---------------- کاربران ----------------
@router.get("/users")
def admin_users(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request, "settings": settings, "admin": admin, "users": users,
        "meta": {"title": "کاربران | پنل مدیریت", "description": "", "keywords": ""},
        "page_key": "users", "page_title": "کاربران",
    })


@router.post("/users/{user_id}/toggle-plan")
def admin_toggle_plan(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if u:
        u.plan = "free" if u.plan == "pro" else "pro"
        db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{user_id}/toggle-active")
def admin_toggle_active(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if u:
        u.is_active = not u.is_active
        db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


# ---------------- دارایی‌های ویژه ----------------
@router.get("/assets")
def admin_assets(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    assets = db.query(models.WatchedAsset).order_by(models.WatchedAsset.sort_order).all()
    return templates.TemplateResponse("admin/assets.html", {
        "request": request, "settings": settings, "admin": admin, "assets": assets,
        "meta": {"title": "دارایی‌ها | پنل مدیریت", "description": "", "keywords": ""},
        "page_key": "assets", "page_title": "دارایی‌های ویژه",
    })


@router.post("/assets/add")
def admin_assets_add(request: Request, db: Session = Depends(get_db),
                      symbol: str = Form(...), display_name_fa: str = Form(...),
                      category: str = Form(...)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    db.add(models.WatchedAsset(symbol=symbol.strip(), display_name_fa=display_name_fa.strip(),
                                category=category.strip(), is_featured=True))
    db.commit()
    return RedirectResponse(url="/admin/assets", status_code=303)


@router.post("/assets/{asset_id}/delete")
def admin_assets_delete(asset_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    a = db.query(models.WatchedAsset).filter(models.WatchedAsset.id == asset_id).first()
    if a:
        db.delete(a)
        db.commit()
    return RedirectResponse(url="/admin/assets", status_code=303)


# ---------------- وبلاگ ----------------
@router.get("/blog")
def admin_blog(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    posts = db.query(models.BlogPost).order_by(models.BlogPost.created_at.desc()).all()
    return templates.TemplateResponse("admin/blog.html", {
        "request": request, "settings": settings, "admin": admin, "posts": posts,
        "meta": {"title": "وبلاگ | پنل مدیریت", "description": "", "keywords": ""},
        "page_key": "blog", "page_title": "مدیریت وبلاگ",
    })


@router.post("/blog/add")
def admin_blog_add(request: Request, db: Session = Depends(get_db),
                    title: str = Form(...), excerpt: str = Form(""), content: str = Form(...),
                    meta_description: str = Form(""), keywords: str = Form("")):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    slug = slugify(title, allow_unicode=False) or f"post-{datetime.utcnow().timestamp():.0f}"
    base_slug, i = slug, 1
    while db.query(models.BlogPost).filter(models.BlogPost.slug == slug).first():
        i += 1
        slug = f"{base_slug}-{i}"
    db.add(models.BlogPost(title=title, slug=slug, excerpt=excerpt or content[:150],
                            content=content, meta_description=meta_description or content[:150],
                            keywords=keywords, is_published=True))
    db.commit()
    return RedirectResponse(url="/admin/blog", status_code=303)


@router.post("/blog/{post_id}/toggle")
def admin_blog_toggle(post_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    p = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if p:
        p.is_published = not p.is_published
        db.commit()
    return RedirectResponse(url="/admin/blog", status_code=303)


@router.post("/blog/{post_id}/delete")
def admin_blog_delete(post_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    p = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse(url="/admin/blog", status_code=303)


# ---------------- پیام‌های تماس ----------------
@router.get("/messages")
def admin_messages(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    messages = db.query(models.ContactMessage).order_by(models.ContactMessage.created_at.desc()).all()
    return templates.TemplateResponse("admin/messages.html", {
        "request": request, "settings": settings, "admin": admin, "messages": messages,
        "meta": {"title": "پیام‌ها | پنل مدیریت", "description": "", "keywords": ""},
        "page_key": "messages", "page_title": "پیام‌های تماس",
    })


@router.post("/messages/{msg_id}/read")
def admin_messages_read(msg_id: int, request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    m = db.query(models.ContactMessage).filter(models.ContactMessage.id == msg_id).first()
    if m:
        m.is_read = True
        db.commit()
    return RedirectResponse(url="/admin/messages", status_code=303)


# ---------------- تنظیمات سایت ----------------
@router.get("/settings")
def admin_settings(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    rows = db.query(models.SiteSetting).all()
    site_settings = {r.key: r.value for r in rows}
    return templates.TemplateResponse("admin/settings.html", {
        "request": request, "settings": settings, "admin": admin, "site_settings": site_settings,
        "meta": {"title": "تنظیمات | پنل مدیریت", "description": "", "keywords": ""},
        "page_key": "settings", "page_title": "تنظیمات سایت",
    })


@router.post("/settings")
def admin_settings_post(request: Request, db: Session = Depends(get_db),
                         ga_id: str = Form(""), site_verification: str = Form(""),
                         announcement: str = Form("")):
    admin = _require_admin(request, db)
    if not admin:
        return _redirect_login()
    for key, value in [("ga_id", ga_id), ("site_verification", site_verification),
                        ("announcement", announcement)]:
        row = db.query(models.SiteSetting).filter(models.SiteSetting.key == key).first()
        if row:
            row.value = value
        else:
            db.add(models.SiteSetting(key=key, value=value))
    db.commit()
    return RedirectResponse(url="/admin/settings", status_code=303)
