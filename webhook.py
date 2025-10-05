#!/usr/bin/env python3
"""
🌐 Webhook Handler برای ربات استودیو مندانی
Mandani Studio Bot Webhook Handler for Web Hosting

این فایل برای دریافت webhook های تلگرام در محیط hosting استفاده می‌شود
"""

import os
import sys
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

# اضافه کردن مسیر پروژه
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import ربات
try:
    from main import MandaniStudioBot
    from config import Config
except ImportError as e:
    print(f"❌ خطا در import: {e}")
    sys.exit(1)

# تنظیم logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebhookHandler(BaseHTTPRequestHandler):
    """Handler برای webhook های تلگرام"""
    
    def __init__(self, *args, bot_instance=None, **kwargs):
        self.bot = bot_instance
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """پردازش POST request های webhook"""
        try:
            # بررسی مسیر
            if self.path != '/webhook':
                self.send_response(404)
                self.end_headers()
                return
            
            # خواندن داده‌ها
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON
            update_data = json.loads(post_data.decode('utf-8'))
            
            # پردازش update در ربات
            if self.bot:
                # در اینجا باید update را به ربات ارسال کنیم
                # این کار نیاز به async processing دارد
                logger.info(f"دریافت update: {update_data.get('update_id', 'unknown')}")
            
            # پاسخ موفق
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            
        except Exception as e:
            logger.error(f"خطا در پردازش webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """پردازش GET request ها"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "bot": "mandani_studio"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override logging"""
        logger.info(f"{self.address_string()} - {format % args}")

def create_webhook_server(bot_instance, port=8443):
    """ایجاد سرور webhook"""
    
    def handler(*args, **kwargs):
        return WebhookHandler(*args, bot_instance=bot_instance, **kwargs)
    
    server = HTTPServer(('', port), handler)
    
    # تنظیم SSL (در صورت نیاز)
    # ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # ssl_context.load_cert_chain('cert.pem', 'key.pem')
    # server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
    
    return server

def main():
    """تابع اصلی webhook handler"""
    try:
        # تنظیم config
        if not Config.validate():
            logger.error("❌ خطا در تنظیمات")
            sys.exit(1)
        
        # ایجاد instance ربات
        bot = MandaniStudioBot()
        
        # تنظیم port
        port = int(os.getenv('WEBHOOK_PORT', 8443))
        
        # ایجاد سرور
        server = create_webhook_server(bot, port)
        
        logger.info(f"🌐 Webhook server شروع شد در پورت {port}")
        logger.info("📱 ربات آماده دریافت webhook ها...")
        
        # اجرای سرور
        server.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("⏹️ سرور توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای webhook server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
