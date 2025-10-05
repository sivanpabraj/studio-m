"""
⚙️ ماژول پیکربندی ربات استودیو ماندنی
Configuration module for Mandani Studio Bot

این ماژول تمام تنظیمات ربات را از متغیرهای محیطی خوانده و مدیریت می‌کند
"""

import os
from typing import Optional
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()


class Config:
    """کلاس پیکربندی ربات"""
    
    # ========================================
    # 🤖 تنظیمات اصلی ربات
    # ========================================
    
    # توکن ربات تلگرام
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # شناسه ادمین اصلی
    MAIN_ADMIN_ID: int = int(os.getenv('MAIN_ADMIN_ID', '0'))
    
    # ========================================
    # 🗄️ تنظیمات پایگاه داده
    # ========================================
    
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'mandani_studio.db')
    AUTO_BACKUP_INTERVAL: int = int(os.getenv('AUTO_BACKUP_INTERVAL', '24'))
    
    # ========================================
    # 💰 تنظیمات مالی
    # ========================================
    
    DEPOSIT_PERCENTAGE: int = int(os.getenv('DEPOSIT_PERCENTAGE', '50'))
    TAX_RATE: float = float(os.getenv('TAX_RATE', '9')) / 100  # تبدیل به اعشار
    CURRENCY: str = os.getenv('CURRENCY', 'تومان')
    
    # ========================================
    # 🏪 اطلاعات استودیو
    # ========================================
    
    STUDIO_NAME: str = os.getenv('STUDIO_NAME', 'استودیو ماندنی')
    STUDIO_PHONE: str = os.getenv('STUDIO_PHONE', '09184004893')
    STUDIO_EMAIL: str = os.getenv('STUDIO_EMAIL', 'studiomandani@gmail.com')
    STUDIO_WEBSITE: str = os.getenv('STUDIO_WEBSITE', '@mandanistudiooo')
    STUDIO_ADDRESS: str = os.getenv('STUDIO_ADDRESS', 'کردستان مریوان، ده متری ورودی شهرک نوروز')
    STUDIO_CARD_NUMBER: str = os.getenv('STUDIO_CARD_NUMBER', '1234-5678-9012-3456')
    STUDIO_CARD_HOLDER: str = os.getenv('STUDIO_CARD_HOLDER', 'استودیو ماندنی')
    
    # ========================================
    # 🔔 تنظیمات یادآوری
    # ========================================
    
    EVENT_REMINDER_HOUR: int = int(os.getenv('EVENT_REMINDER_HOUR', '9'))
    DELIVERY_REMINDER_HOUR: int = int(os.getenv('DELIVERY_REMINDER_HOUR', '10'))
    DELIVERY_REMINDER_DAYS: int = int(os.getenv('DELIVERY_REMINDER_DAYS', '3'))
    
    # ========================================
    # 🛡️ تنظیمات امنیتی
    # ========================================
    
    RATE_LIMIT_GENERAL: int = int(os.getenv('RATE_LIMIT_GENERAL', '10'))
    RATE_LIMIT_SEARCH: int = int(os.getenv('RATE_LIMIT_SEARCH', '5'))
    RATE_LIMIT_BUTTON: int = int(os.getenv('RATE_LIMIT_BUTTON', '30'))
    
    # ========================================
    # 📧 تنظیمات ایمیل
    # ========================================
    
    EMAIL_ENABLED: bool = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_EMAIL: str = os.getenv('SMTP_EMAIL', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')
    
    # ========================================
    # 📊 تنظیمات لاگ
    # ========================================
    
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'mandani_bot.log')
    LOG_MAX_SIZE: int = int(os.getenv('LOG_MAX_SIZE', '10'))  # مگابایت
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ========================================
    # 🌍 تنظیمات منطقه زمانی
    # ========================================
    
    TIMEZONE: str = os.getenv('TIMEZONE', 'Asia/Tehran')
    DATE_FORMAT: str = os.getenv('DATE_FORMAT', '%Y-%m-%d')
    TIME_FORMAT: str = os.getenv('TIME_FORMAT', '%H:%M')
    
    # ========================================
    # 🚀 تنظیمات استقرار
    # ========================================
    
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    WEBHOOK_URL: Optional[str] = os.getenv('WEBHOOK_URL')
    WEBHOOK_PORT: int = int(os.getenv('WEBHOOK_PORT', '8443'))
    
    # ========================================
    # 🔗 تنظیمات API های خارجی
    # ========================================
    
    GOOGLE_CALENDAR_API_KEY: Optional[str] = os.getenv('GOOGLE_CALENDAR_API_KEY')
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    PAYMENT_API_KEY: Optional[str] = os.getenv('PAYMENT_API_KEY')
    
    @classmethod
    def validate(cls) -> bool:
        """اعتبارسنجی تنظیمات ضروری"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN الزامی است")
        
        if cls.MAIN_ADMIN_ID == 0:
            errors.append("MAIN_ADMIN_ID باید تنظیم شود")
        
        if errors:
            print("❌ خطاهای پیکربندی:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def get_contact_info(cls) -> str:
        """دریافت اطلاعات تماس استودیو"""
        return f"""
📞 **راه‌های تماس با {cls.STUDIO_NAME}**

📱 تلفن: {cls.STUDIO_PHONE}
📧 ایمیل: {cls.STUDIO_EMAIL}
🌐 وب‌سایت: {cls.STUDIO_WEBSITE}
📍 آدرس: {cls.STUDIO_ADDRESS}

💳 **اطلاعات پرداخت**
شماره کارت: {cls.STUDIO_CARD_NUMBER}
نام صاحب کارت: {cls.STUDIO_CARD_HOLDER}
        """.strip()
    
    @classmethod
    def get_business_hours(cls) -> str:
        """ساعات کاری استودیو"""
        return """
⏰ **ساعات کاری**

شنبه تا پنج‌شنبه: ۱۰:۰۰ - ۲۲:۰۰
جمعه: تعطیل

📞 پاسخگویی تلفنی در ساعات کاری
💬 پاسخ به پیام‌های ربات: ۲۴ ساعته
        """.strip()


# نمونه سینگلتون برای دسترسی آسان
config = Config()

# اعتبارسنجی تنظیمات هنگام import
if not config.validate():
    import sys
    print("⚠️ لطفاً فایل .env را بررسی کنید و تنظیمات ضروری را وارد کنید")
    sys.exit(1)
