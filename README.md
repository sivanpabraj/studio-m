# 🎬 ربات تلگرام استودیو ماندنی
# Mandani Studio Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-20.0+-green.svg)](https://python-telegram-bot.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ربات تلگرام پیشرفته برای مدیریت داخلی استودیو عکاسی و فیلمبرداری مندانی

## ✨ ویژگی‌های کلیدی

### 🎯 مدیریت مشتریان و رزروها
- ✅ افزودن مشتری جدید با اطلاعات کامل
- ✅ انتخاب نوع خدمت (تولد، عروسی، عقد، عمومی، سایر)
- ✅ تنظیم جزئیات خدمت (دوربین، هلی‌شات، عکاس)
- ✅ تولید کد رزرو منحصربه‌فرد
- ✅ پیشنهادات هوشمند بر اساس نوع خدمت

### 💰 محاسبه هزینه و فاکتورسازی
- ✅ محاسبه خودکار هزینه بر اساس خدمات
- ✅ تولید فاکتور PDF با جزئیات کامل
- ✅ مدیریت بیعانه (%50) و پرداخت
- ✅ روش‌های پرداخت مختلف (نقد، کارت، کارت به کارت)

### 🔍 جستجو و پیگیری
- ✅ جستجو بر اساس کد رزرو، نام، یا شماره تلفن
- ✅ روزشمار تا تحویل پروژه
- ✅ نمایش وضعیت رزرو و پرداخت
- ✅ محدودیت نرخ درخواست برای امنیت

### 👨‍💼 پنل مدیریت ادمین
- ✅ مدیریت همه رزروها
- ✅ تأیید/لغو رزروها
- ✅ افزودن ادمین جدید
- ✅ آمار کامل (مشتریان، درآمد، رزروها)
- ✅ پشتیبان‌گیری JSON

### 🔔 یادآوری‌های هوشمند
- ✅ یادآوری 24 ساعت قبل از مراسم
- ✅ یادآوری 3 روز قبل از تحویل
- ✅ Job queue برای اجرای خودکار

### 🛡️ امنیت و لاگینگ
- ✅ احراز هویت ادمین‌ها
- ✅ لاگ تمام فعالیت‌ها
- ✅ محدودیت نرخ درخواست
- ✅ اعتبارسنجی ورودی‌ها

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها
```bash
Python 3.8+
pip (Package manager)
```

### 1. کلون کردن پروژه
```bash
git clone https://github.com/yourusername/mandanibot.git
cd mandanibot
```

### 2. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### 3. تنظیم متغیرهای محیطی
فایل `.env` ایجاد کنید:
```env
BOT_TOKEN=your_telegram_bot_token_here
MAIN_ADMIN_ID=your_telegram_user_id
```

### 4. دریافت Bot Token
1. به [@BotFather](https://t.me/BotFather) در تلگرام مراجعه کنید
2. دستور `/newbot` را ارسال کنید
3. نام ربات و username را انتخاب کنید
4. Token دریافتی را در `.env` قرار دهید

### 5. پیدا کردن Telegram User ID
1. به [@userinfobot](https://t.me/userinfobot) مراجعه کنید
2. شناسه خود را دریافت کنید
3. آن را در `MAIN_ADMIN_ID` قرار دهید

### 6. اجرای ربات
```bash
python main.py
```

## 🎮 نحوه استفاده

### برای مشتریان
1. **شروع کار**: دستور `/start` را ارسال کنید
2. **رزرو جدید**: روی "🆕 رزرو جدید" کلیک کنید
3. **ورود اطلاعات**: نام، تلفن، ایمیل خود را وارد کنید
4. **انتخاب خدمت**: نوع خدمت مورد نظر را انتخاب کنید
5. **تنظیم جزئیات**: تعداد دوربین، هلی‌شات، عکاس را مشخص کنید
6. **دریافت فاکتور**: فاکتور PDF را دانلود کنید
7. **پرداخت بیعانه**: بیعانه را پرداخت کنید

### برای ادمین‌ها
1. **پنل ادمین**: گزینه "👨‍💼 پنل ادمین" را انتخاب کنید
2. **مدیریت رزروها**: تأیید، لغو، یا مشاهده رزروها
3. **آمار**: مشاهده آمار مشتریان و درآمد
4. **پشتیبان‌گیری**: دانلود backup کامل اطلاعات

## 📱 دستورات اصلی

### دستورات عمومی
- `/start` - شروع کار با ربات
- `/help` - راهنمای استفاده
- `/search` - جستجوی سریع رزرو

### دستورات ادمین
- `/reply [user_id] [message]` - پاسخ به کاربر

## 🗂️ ساختار پروژه

```
mandanibot/
├── main.py              # فایل اصلی ربات
├── database.py          # مدیریت پایگاه داده SQLite
├── utils.py            # توابع کمکی و محاسبات
├── requirements.txt    # وابستگی‌های Python
├── README.md          # راهنمای پروژه
├── .env               # تنظیمات محیطی (ایجاد کنید)
└── mandani_studio.db  # پایگاه داده (خودکار ایجاد می‌شود)
```

## 💾 ساختار پایگاه داده

### جدول customers
```sql
id, telegram_id, name, phone, email, created_at, updated_at
```

### جدول reservations
```sql
id, customer_id, telegram_id, reservation_code, service_type,
service_details, event_date, event_time, delivery_date, location,
total_cost, deposit_amount, payment_status, booking_status,
payment_method, transaction_id, special_notes, created_at, updated_at
```

### جدول admins
```sql
id, telegram_id, username, full_name, added_by, created_at
```

### جدول logs
```sql
id, user_id, action, details, ip_address, timestamp
```

## 💰 نرخ‌های خدمات

| نوع خدمت | نرخ پایه | دوربین اضافی | عکاس اضافی | هلی‌شات |
|----------|---------|-------------|------------|---------|
| تولد | ۵۰۰,۰۰۰ | ۱۰۰,۰۰۰ | ۱۵۰,۰۰۰ | ۲۰۰,۰۰۰ |
| عروسی | ۲,۰۰۰,۰۰۰ | ۱۰۰,۰۰۰ | ۳۰۰,۰۰۰ | ۲۰۰,۰۰۰ |
| عقد | ۱,۰۰۰,۰۰۰ | ۱۰۰,۰۰۰ | ۱۵۰,۰۰۰ | ۲۰۰,۰۰۰ |
| عمومی | ۳۰۰,۰۰۰ | ۱۰۰,۰۰۰ | ۱۵۰,۰۰۰ | ۲۰۰,۰۰۰ |

*همه قیمت‌ها به تومان و شامل مالیات ۹٪ می‌باشد*

## 🌐 استقرار Production

### روی Heroku
1. فایل `Procfile` ایجاد کنید:
```
worker: python main.py
```

2. App ایجاد کرده و کد را push کنید:
```bash
heroku create your-app-name
git push heroku main
```

3. متغیرهای محیطی را تنظیم کنید:
```bash
heroku config:set BOT_TOKEN=your_token
heroku config:set MAIN_ADMIN_ID=your_id
```

### روی VPS
1. پروژه را در سرور کپی کنید
2. Virtual environment ایجاد کنید:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Service برای systemd ایجاد کنید:
```ini
[Unit]
Description=Mandani Studio Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/mandanibot
Environment=PATH=/path/to/mandanibot/venv/bin
ExecStart=/path/to/mandanibot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🔧 سفارشی‌سازی

### تغییر نرخ‌ها
فایل `utils.py` → کلاس `CostCalculator` → متغیر `BASE_RATES`

### اضافه کردن نوع خدمت جدید
1. `utils.py` → `BASE_RATES` → نرخ جدید اضافه کنید
2. `main.py` → `get_service_type_keyboard` → دکمه جدید اضافه کنید

### تغییر متن‌های پیام
فایل `utils.py` → کلاس `MessageFormatter`

## 🛠️ نکات توسعه

### اضافه کردن فونت فارسی برای PDF
```python
# در utils.py → PDFGenerator.__init__
pdfmetrics.registerFont(TTFont('Persian', 'fonts/persian_font.ttf'))
```

### ادغام با Google Calendar
```python
# نصب: pip install google-api-python-client
# کد نمونه در utils.py
```

### ارسال ایمیل فاکتور
```python
# نصب: pip install smtplib
# کد نمونه در utils.py
```

## 🐛 عیب‌یابی

### مشکلات رایج
1. **Bot Token اشتباه**: بررسی کنید token در `.env` صحیح باشد
2. **دسترسی پایگاه داده**: اطمینان حاصل کنید دایرکتری قابل نوشتن باشد
3. **خطای import**: `pip install -r requirements.txt` را اجرا کنید

### لاگ‌ها
لاگ‌ها در فایل `mandani_bot.log` ذخیره می‌شوند.

## 📞 پشتیبانی

برای سوالات یا مشکلات:
- 📧 ایمیل: info@mandanistudio.com
- 📱 تلگرام: @mandanistudio
- 🌐 وب‌سایت: www.mandanistudio.com

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر فایل [LICENSE](LICENSE) را مطالعه کنید.

## 🤝 مشارکت

از مشارکت‌های شما استقبال می‌کنیم! لطفاً:
1. Fork کنید
2. Feature branch ایجاد کنید
3. تغییرات را commit کنید
4. Pull request ارسال کنید

## 🎯 TODO / Roadmap

- [ ] ادغام با Google Calendar
- [ ] ارسال ایمیل خودکار
- [ ] پنل وب ادمین
- [ ] ربات وب اپلیکیشن
- [ ] پرداخت آنلاین
- [ ] سیستم نظردهی مشتریان
- [ ] گزارش‌های پیشرفته
- [ ] API خارجی برای اپلیکیشن موبایل

---

<div align="center">

**🌟 ساخته شده با ❤️ برای استودیو مندانی**

[تلگرام](https://t.me/mandanistudio) • [وب‌سایت](https://mandanistudio.com) • [Instagram](https://instagram.com/mandanistudio)

</div>
