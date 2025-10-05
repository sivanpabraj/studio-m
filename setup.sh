#!/bin/bash

# 🚀 اسکریپت راه‌اندازی سریع ربات استودیو مندانی
# Quick setup script for Mandani Studio Bot

set -e  # توقف در صورت خطا

echo "🎬 ربات استودیو مندانی - راه‌اندازی سریع"
echo "=============================================="
echo ""

# بررسی نسخه Python
echo "🔍 بررسی Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 یافت نشد! لطفاً Python 3.8+ نصب کنید"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION یافت شد"

# بررسی pip
echo "🔍 بررسی pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 یافت نشد! لطفاً pip نصب کنید"
    exit 1
fi
echo "✅ pip آماده است"

# ایجاد virtual environment
echo "📦 ایجاد virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment ایجاد شد"
else
    echo "ℹ️  Virtual environment از قبل موجود است"
fi

# فعال‌سازی virtual environment
echo "🔧 فعال‌سازی virtual environment..."
source venv/bin/activate

# به‌روزرسانی pip
echo "⬆️  به‌روزرسانی pip..."
pip install --upgrade pip

# نصب وابستگی‌ها
echo "📚 نصب وابستگی‌های Python..."
pip install -r requirements.txt

# بررسی فایل .env
echo "⚙️  بررسی تنظیمات..."
if [ ! -f ".env" ]; then
    echo "⚠️  فایل .env یافت نشد!"
    echo "📝 کپی کردن فایل نمونه..."
    cp .env.example .env
    echo ""
    echo "🔧 لطفاً فایل .env را ویرایش کنید و تنظیمات زیر را وارد کنید:"
    echo "   - BOT_TOKEN: توکن ربات از @BotFather"
    echo "   - MAIN_ADMIN_ID: شناسه تلگرام شما از @userinfobot"
    echo ""
    echo "سپس دوباره این اسکریپت را اجرا کنید"
    exit 1
fi

# بررسی متغیرهای ضروری
echo "🔐 بررسی متغیرهای محیطی..."
source .env

if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo "❌ BOT_TOKEN تنظیم نشده! لطفاً فایل .env را ویرایش کنید"
    exit 1
fi

if [ -z "$MAIN_ADMIN_ID" ] || [ "$MAIN_ADMIN_ID" = "123456789" ]; then
    echo "❌ MAIN_ADMIN_ID تنظیم نشده! لطفاً فایل .env را ویرایش کنید"
    exit 1
fi

echo "✅ تنظیمات معتبر است"

# تست اتصال
echo "🧪 تست اتصال..."
python3 -c "
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('BOT_TOKEN')

try:
    response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
    if response.status_code == 200:
        bot_info = response.json()['result']
        print(f'✅ اتصال موفق! ربات: {bot_info[\"first_name\"]} (@{bot_info[\"username\"]})')
    else:
        print(f'❌ خطا در اتصال: {response.status_code}')
        exit(1)
except Exception as e:
    print(f'❌ خطا در تست اتصال: {e}')
    exit(1)
"

# ایجاد اسکریپت اجرا
echo "📄 ایجاد اسکریپت اجرا..."
cat > run.sh << 'EOF'
#!/bin/bash
# اسکریپت اجرای ربات استودیو مندانی

echo "🚀 شروع ربات استودیو مندانی..."
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF

chmod +x run.sh
echo "✅ اسکریپت run.sh ایجاد شد"

# ایجاد اسکریپت توقف
echo "📄 ایجاد اسکریپت توقف..."
cat > stop.sh << 'EOF'
#!/bin/bash
# اسکریپت توقف ربات استودیو مندانی

echo "🛑 توقف ربات استودیو مندانی..."
pkill -f "python main.py" || echo "ربات در حال اجرا نیست"
echo "✅ ربات متوقف شد"
EOF

chmod +x stop.sh
echo "✅ اسکریپت stop.sh ایجاد شد"

echo ""
echo "🎉 راه‌اندازی کامل شد!"
echo "=============================================="
echo ""
echo "📋 دستورات مفید:"
echo "   ./run.sh          - اجرای ربات"
echo "   ./stop.sh         - توقف ربات"
echo "   source venv/bin/activate - فعال‌سازی محیط مجازی"
echo ""
echo "📖 برای اطلاعات بیشتر README.md را مطالعه کنید"
echo ""
echo "🚀 برای شروع ربات دستور زیر را اجرا کنید:"
echo "   ./run.sh"
echo ""
