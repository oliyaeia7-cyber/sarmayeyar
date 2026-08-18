import itsdangerous
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
signer = itsdangerous.TimestampSigner(settings.SECRET_KEY)

SESSION_COOKIE = "sy_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14  # ۱۴ روز


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_session_token(user_id: int) -> str:
    return signer.sign(str(user_id).encode()).decode()


def read_session_token(token: str, max_age: int = SESSION_MAX_AGE):
    try:
        raw = signer.unsign(token, max_age=max_age)
        return int(raw.decode())
    except Exception:
        return None
