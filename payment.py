"""
لایه پرداخت/اشتراک (Stub).
برای فعال‌سازی واقعی:
  ۱) یک حساب پذیرنده در زرین‌پال (یا هر درگاه دیگر) بسازید.
  ۲) ZARINPAL_MERCHANT_ID را در متغیرهای محیطی قرار دهید.
  ۳) توابع زیر را طبق مستندات درگاه تکمیل کنید (درخواست پرداخت + وریفای).
این فایل به‌عمد ساده نگه داشته شده تا معماری روشن بماند.
"""
from app.config import settings


def create_payment_request(user_email: str, amount_toman: int, description: str) -> dict:
    if not settings.ZARINPAL_MERCHANT_ID:
        return {
            "ok": False,
            "message": "درگاه پرداخت هنوز پیکربندی نشده است. ZARINPAL_MERCHANT_ID را تنظیم کنید.",
        }
    # TODO: فراخوانی واقعی API زرین‌پال (PaymentRequest.json) در اینجا انجام شود.
    return {"ok": True, "payment_url": "#", "message": "در حالت نمونه؛ درگاه واقعی متصل نشده است."}


def verify_payment(authority: str) -> dict:
    # TODO: فراخوانی واقعی API زرین‌پال (PaymentVerification.json)
    return {"ok": False, "message": "تایید پرداخت پیاده‌سازی نشده است (نمونه اولیه)."}
