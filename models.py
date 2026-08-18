from datetime import datetime
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Text,
                         Float, ForeignKey)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    plan = Column(String(20), default="free")  # free | pro
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("AnalysisLog", back_populates="user")


class AnalysisLog(Base):
    """ثبت هر بار تحلیلی که یک کاربر درخواست می‌دهد (برای محدودیت پلن رایگان و آمار)"""
    __tablename__ = "analysis_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symbol = Column(String(30), index=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")


class WatchedAsset(Base):
    """دارایی‌های ویژه/پیشنهادی که در صفحه اصلی و پنل ادمین قابل مدیریت هستند"""
    __tablename__ = "watched_assets"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), unique=True, index=True)
    display_name_fa = Column(String(150))
    category = Column(String(30))  # crypto | stock | forex | gold
    is_featured = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)


class BlogPost(Base):
    """مقالات وبلاگ برای تقویت سئو و بازاریابی محتوایی"""
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250))
    slug = Column(String(250), unique=True, index=True)
    excerpt = Column(String(400))
    content = Column(Text)
    meta_description = Column(String(300))
    keywords = Column(String(300))
    cover_image = Column(String(300), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150))
    email = Column(String(150))
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SiteSetting(Base):
    """تنظیمات قابل ویرایش از پنل ادمین (بدون نیاز به تغییر کد)"""
    __tablename__ = "site_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(Text)
