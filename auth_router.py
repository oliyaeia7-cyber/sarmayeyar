from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models
from app.config import settings
from app.security import hash_password, verify_password, create_session_token, SESSION_COOKIE, SESSION_MAX_AGE

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/register")
def register_get(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("register.html", {
        "request": request, "user": get_current_user(request, db), "settings": settings,
        "meta": {"title": "ثبت‌نام | سرمایه‌یار", "description": "ثبت‌نام رایگان در سرمایه‌یار", "keywords": ""},
        "error": None,
    })


@router.post("/register")
def register_post(request: Request, db: Session = Depends(get_db),
                   full_name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    existing = db.query(models.User).filter(models.User.email == email.lower().strip()).first()
    if existing:
        return templates.TemplateResponse("register.html", {
            "request": request, "user": None, "settings": settings,
            "meta": {"title": "ثبت‌نام | سرمایه‌یار", "description": "", "keywords": ""},
            "error": "این ایمیل قبلاً ثبت شده است.",
        })
    user = models.User(full_name=full_name.strip(), email=email.lower().strip(),
                        hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session_token(user.id)
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(SESSION_COOKIE, token, max_age=SESSION_MAX_AGE, httponly=True, samesite="lax")
    return resp


@router.get("/login")
def login_get(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("login.html", {
        "request": request, "user": get_current_user(request, db), "settings": settings,
        "meta": {"title": "ورود | سرمایه‌یار", "description": "ورود به حساب کاربری سرمایه‌یار", "keywords": ""},
        "error": None,
    })


@router.post("/login")
def login_post(request: Request, db: Session = Depends(get_db),
                email: str = Form(...), password: str = Form(...)):
    user = db.query(models.User).filter(models.User.email == email.lower().strip()).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request, "user": None, "settings": settings,
            "meta": {"title": "ورود | سرمایه‌یار", "description": "", "keywords": ""},
            "error": "ایمیل یا رمز عبور نادرست است.",
        })
    token = create_session_token(user.id)
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(SESSION_COOKIE, token, max_age=SESSION_MAX_AGE, httponly=True, samesite="lax")
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp
