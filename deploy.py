#!/usr/bin/env python3
"""
🚀 Deployment Script برای هاست Parspack
Mandani Studio Bot Deployment

این فایل برای اجرای ربات روی هاست تنظیم شده است
"""

import os
import sys
import logging
from pathlib import Path

# اضافه کردن مسیر پروژه به Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# تنظیم logging برای production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mandani_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """تنظیم محیط production"""
    try:
        # بررسی وجود فایل .env
        env_file = current_dir / '.env'
        if not env_file.exists():
            logger.error("❌ فایل .env یافت نشد!")
            return False
        
        # Import پکیج‌های مورد نیاز
        try:
            import telegram
            import sqlite3
            import reportlab
            logger.info("✅ تمام پکیج‌های مورد نیاز موجود هستند")
        except ImportError as e:
            logger.error(f"❌ پکیج مورد نیاز یافت نشد: {e}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ خطا در تنظیم محیط: {e}")
        return False

def main():
    """تابع اصلی deployment"""
    logger.info("🚀 شروع deployment ربات استودیو مندانی...")
    
    # تنظیم محیط
    if not setup_environment():
        logger.error("❌ خطا در تنظیم محیط")
        sys.exit(1)
    
    try:
        # Import ربات اصلی
        from main import main as bot_main
        
        logger.info("✅ ربات با موفقیت راه‌اندازی شد")
        logger.info("📱 ربات در حال اجرا...")
        
        # اجرای ربات
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("⏹️ ربات توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای ربات: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
