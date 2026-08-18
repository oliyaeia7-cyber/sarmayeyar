from fastapi import Request, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import SESSION_COOKIE, read_session_token
from app import models


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    user_id = read_session_token(token)
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()  # noqa: E712


def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user and user.is_admin:
        return user
    return None
