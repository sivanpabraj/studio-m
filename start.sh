#!/bin/bash
# 🚀 Startup Script برای ربات استودیو مندانی
# Mandani Studio Bot Startup Script for Parspack Hosting

echo "🚀 راه‌اندازی ربات استودیو مندانی..."

# تنظیم متغیرهای محیط
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export LANG=fa_IR.UTF-8
export LC_ALL=fa_IR.UTF-8

# بررسی وجود Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 یافت نشد!"
    exit 1
fi

echo "✅ Python3 موجود است"

# بررسی وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 یافت نشد!"
    exit 1
fi

echo "✅ pip3 موجود است"

# نصب پکیج‌های مورد نیاز
echo "📦 نصب پکیج‌های مورد نیاز..."
pip3 install -r requirements.txt --user

if [ $? -ne 0 ]; then
    echo "❌ خطا در نصب پکیج‌ها"
    exit 1
fi

echo "✅ پکیج‌ها با موفقیت نصب شدند"

# بررسی وجود فایل .env
if [ ! -f ".env" ]; then
    echo "❌ فایل .env یافت نشد!"
    echo "لطفاً فایل .env را ایجاد کنید و متغیرهای مورد نیاز را تنظیم کنید"
    exit 1
fi

echo "✅ فایل .env موجود است"

# ایجاد دایرکتوری logs در صورت عدم وجود
mkdir -p logs

# اجرای ربات
echo "🤖 شروع ربات..."
python3 deploy.py

echo "⏹️ ربات متوقف شد"
