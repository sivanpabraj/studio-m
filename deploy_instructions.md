# 🚀 راهنمای استقرار ربات استودیو مندانی

## گزینه‌های استقرار

### 1. 🆓 Heroku (رایگان تا حدی)
```bash
# نصب Heroku CLI
brew install heroku/brew/heroku

# ورود به Heroku
heroku login

# ایجاد پروژه جدید
heroku create mandani-studio-bot

# تنظیم متغیرهای محیطی
heroku config:set BOT_TOKEN=8235154120:AAEq7odbW7pRI8K8oQ6gzyH1YeLePaeQcyI
heroku config:set MAIN_ADMIN_ID=85431846

# استقرار
git push heroku main
```

### 2. 🌊 DigitalOcean (ماهانه ~5 دلار)
```bash
# ایجاد droplet با Ubuntu
# نصب Python و requirements
# کپی فایل‌ها و اجرای ربات با systemd
```

### 3. ☁️ Railway.app (آسان و سریع)
```bash
# اتصال GitHub repository
# تنظیم متغیرهای محیطی در dashboard
# استقرار خودکار
```

### 4. 🐳 Docker (برای هر سرور)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## تنظیمات مورد نیاز

### متغیرهای محیطی:
- `BOT_TOKEN`: 8235154120:AAEq7odbW7pRI8K8oQ6gzyH1YeLePaeQcyI
- `MAIN_ADMIN_ID`: 85431846
- `STUDIO_PHONE`: 09184004893
- `STUDIO_EMAIL`: studiomandani@gmail.com

### فایل‌های ضروری:
- main.py
- database.py
- utils.py
- config.py
- requirements.txt
- .env (با اطلاعات واقعی)

## 🔧 راه‌حل سریع: Railway

1. برو به railway.app
2. اکانت GitHub وصل کن
3. Repository رو انتخاب کن
4. متغیرهای محیطی رو تنظیم کن
5. Deploy بزن

## 💻 راه‌حل موقت: اجرای پس‌زمینه روی مک

```bash
# اجرای ربات در پس‌زمینه
nohup python main.py > bot.log 2>&1 &

# چک کردن وضعیت
ps aux | grep python

# خاموش کردن
pkill -f "python main.py"
```

## 🔋 راه‌حل محلی: جلوگیری از خواب مک

```bash
# جلوگیری از خواب مک (موقت)
caffeinate -d

# اجرای ربات همراه با جلوگیری از خواب
caffeinate -d python main.py
```
