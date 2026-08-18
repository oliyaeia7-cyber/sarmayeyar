"""
تنظیمات کلی سایت سرمایه‌یار
همه مقادیر حساس از متغیرهای محیطی (Environment Variables) خوانده می‌شوند.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SITE_NAME: str = "سرمایه‌یار"
    SITE_NAME_EN: str = "SarmayeYar"
    SITE_DESCRIPTION: str = (
        "سرمایه‌یار، دستیار هوشمند سرمایه‌گذاری؛ تحلیل احتمالاتی بازار بورس، "
        "ارز دیجیتال، طلا و ارز با هوش مصنوعی. به‌جای سیگنال قطعی خرید یا فروش، "
        "امتیاز و درصد احتمال به شما می‌دهیم."
    )
    SITE_URL: str = os.getenv("SITE_URL", "https://sarmayeyar.example.com")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sarmayeyar.db")

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@sarmayeyar.local")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")

    # درگاه پرداخت (به‌صورت نمونه - قبل از انتشار مقادیر واقعی را در env قرار دهید)
    ZARINPAL_MERCHANT_ID: str = os.getenv("ZARINPAL_MERCHANT_ID", "")

    # سرویس اخبار / RSS منابع فارسی و انگلیسی برای تحلیل احساسات اخبار
    NEWS_RSS_FEEDS: list = [
        "https://news.google.com/rss/search?q=%D8%A8%D9%88%D8%B1%D8%B3&hl=fa&gl=IR&ceid=IR:fa",
        "https://news.google.com/rss/search?q=cryptocurrency&hl=en-US&gl=US&ceid=US:en",
    ]

    # کلید API اختیاری برای اتصال به مدل‌های زبانی (تحلیل عمیق‌تر اخبار) - اختیاری
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")

    # پلن‌های اشتراک
    FREE_DAILY_ANALYSIS_LIMIT: int = 5
    PRO_PRICE_TOMAN: int = 249000

    GOOGLE_ANALYTICS_ID: str = os.getenv("GOOGLE_ANALYTICS_ID", "")
    GOOGLE_SITE_VERIFICATION: str = os.getenv("GOOGLE_SITE_VERIFICATION", "")


settings = Settings()
