"""
🤖 ربات تلگرام استودیو ماندنی
Mandani Studio Telegram Bot

ربات پیشرفته مدیریت استودیو عکاسی و فیلمبرداری
Advanced Photography & Videography Studio Management Bot
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

# telegram bot imports
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes, JobQueue
)
from telegram.constants import ParseMode

# local imports
from database import DatabaseManager
from utils import (
    CostCalculator, ReservationCodeGenerator, ValidationUtils,
    PDFGenerator, MessageFormatter, SmartRecommendations,
    PersianDateUtils, logger
)
from config import config

# Bot Configuration
BOT_TOKEN = config.BOT_TOKEN
MAIN_ADMIN_ID = config.MAIN_ADMIN_ID

# Conversation states
(WAITING_NAME, WAITING_FAMILY_NAME, WAITING_PHONE, WAITING_EMAIL, WAITING_SERVICE_TYPE,
 WAITING_BRIDE_NAME, WAITING_GUEST_COUNT, WAITING_EVENT_DATE, WAITING_LOCATION,
 WAITING_CAMERAS, WAITING_CAMERA_QUALITY, WAITING_HELISHOT, WAITING_PHOTOGRAPHERS, 
 WAITING_DURATION, WAITING_EVENT_TIME, WAITING_CUSTOM_COST, WAITING_PAYMENT_METHOD, 
 WAITING_TRANSACTION_ID, WAITING_SEARCH_QUERY, WAITING_ADMIN_USERNAME) = range(20)


class MandaniStudioBot:
    """کلاس اصلی ربات استودیو ماندنی"""
    
    def __init__(self):
        """راه‌اندازی ربات"""
        self.db = DatabaseManager()
        self.pdf_generator = PDFGenerator()
        
        # اضافه کردن ادمین اصلی
        self.db.add_admin(MAIN_ADMIN_ID, "main_admin", "ادمین اصلی", MAIN_ADMIN_ID)
        
        # ذخیره اطلاعات موقت کاربران
        self.user_data = {}
        
        logger.info("🚀 ربات استودیو ماندنی راه‌اندازی شد")
    
    def get_main_menu_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """ایجاد کیبورد منوی اصلی"""
        keyboard = [
            [
                InlineKeyboardButton("🆕 رزرو جدید", callback_data="new_reservation"),
                InlineKeyboardButton("🔍 جستجو", callback_data="search_reservation")
            ],
            [
                InlineKeyboardButton("📋 رزروهای من", callback_data="my_reservations"),
                InlineKeyboardButton("📞 تماس", callback_data="contact_admin")
            ]
        ]
        
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("👨‍💼 پنل ادمین", callback_data="admin_panel"),
                InlineKeyboardButton("📊 آمار", callback_data="statistics")
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_service_type_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد انتخاب نوع خدمت"""
        keyboard = [
            [
                InlineKeyboardButton("🎂 تولد", callback_data="service_birthday"),
                InlineKeyboardButton("💒 عروسی", callback_data="service_wedding")
            ],
            [
                InlineKeyboardButton("💍 عقد", callback_data="service_engagement"),
                InlineKeyboardButton("📸 عمومی", callback_data="service_general")
            ],
            [
                InlineKeyboardButton("🔧 سایر", callback_data="service_other"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_admin_notification(self, user_data, reservation_code, context):
        """ارسال نوتیفیکیشن به ادمین‌های مشخص شده"""
        # شناسه‌های ادمین‌هایی که باید نوتیفیکیشن دریافت کنند
        admin_usernames = ["@sivanpabarja", "@mandanistudio1"]
        admin_ids = [85431846]  # شناسه‌های عددی ادمین‌ها
        
        # تولید متن نوتیفیکیشن
        notification_text = f"""
🔔 **رزرو جدید ثبت شد!**

📋 **کد رزرو:** `{reservation_code}`
👤 **نام:** {user_data.get('name', 'نامشخص')} {user_data.get('family_name', '')}
📱 **شماره تماس:** {user_data.get('phone', 'نامشخص')}
🎯 **نوع خدمت:** {user_data.get('service_type', 'نامشخص')}
"""
        
        # اضافه کردن جزئیات بیشتر برای عروسی
        if user_data.get('service_type') == 'wedding':
            notification_text += f"""
💍 **نام عروس:** {user_data.get('bride_name', 'نامشخص')}
👥 **تعداد مهمانان:** {user_data.get('guest_count', 'نامشخص')}
"""
        
        # جزئیات عمومی
        notification_text += f"""
📅 **تاریخ مراسم:** {user_data.get('event_date', 'نامشخص')}
📍 **مکان:** {user_data.get('location', 'نامشخص')}
📷 **تعداد دوربین:** {user_data.get('cameras', 'نامشخص')}
🎥 **کیفیت دوربین:** {user_data.get('camera_quality', 'نامشخص')}
🚁 **هلی‌شات:** {'بله' if user_data.get('helishot', False) else 'خیر'}
👥 **تعداد عکاس:** {user_data.get('photographers', 'نامشخص')}

⏰ **زمان ثبت:** {PersianDateUtils.get_persian_datetime()}
"""
        
        # ارسال به ادمین‌ها
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"✅ نوتیفیکیشن به ادمین {admin_id} ارسال شد")
            except Exception as e:
                logger.error(f"❌ خطا در ارسال نوتیفیکیشن به ادمین {admin_id}: {e}")
    
    def get_yes_no_keyboard(self, yes_data: str, no_data: str) -> InlineKeyboardMarkup:
        """کیبورد بله/خیر"""
        keyboard = [
            [InlineKeyboardButton("✅ بله", callback_data=yes_data)],
            [InlineKeyboardButton("❌ خیر", callback_data=no_data)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_number_keyboard(self, min_num: int, max_num: int, prefix: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب عدد"""
        keyboard = []
        row = []
        for i in range(min_num, max_num + 1):
            row.append(InlineKeyboardButton(
                PersianDateUtils.english_to_persian_digits(str(i)),
                callback_data=f"{prefix}_{i}"
            ))
            if len(row) == 3:  # ۳ دکمه در هر ردیف
                keyboard.append(row)
                row = []
        
        if row:  # اضافه کردن ردیف باقی‌مانده
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_admin_panel_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد پنل ادمین"""
        keyboard = [
            [
                InlineKeyboardButton("📋 همه رزروها", callback_data="admin_all_reservations"),
                InlineKeyboardButton("⏳ در انتظار", callback_data="admin_pending_reservations")
            ],
            [
                InlineKeyboardButton("✅ تأیید", callback_data="admin_confirm_reservation"),
                InlineKeyboardButton("❌ لغو", callback_data="admin_cancel_reservation")
            ],
            [
                InlineKeyboardButton("👨‍💼 افزودن ادمین", callback_data="admin_add_admin"),
                InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور شروع /start"""
        user = update.effective_user
        user_id = user.id
        
        # نمایش شناسه کاربر در لاگ
        logger.info(f"👤 کاربر جدید: {user.first_name} (ID: {user_id})")
        
        # بررسی ادمین بودن
        is_admin = self.db.is_admin(user_id)
        
        # ثبت لاگ
        self.db.log_action(user_id, "start_command")
        
        welcome_text = f"""
🎬 سلام {user.first_name} عزیز!

به ربات استودیو ماندنی خوش آمدید 🎥✨

ما در استودیو ماندنی آماده ارائه خدمات حرفه‌ای عکاسی و فیلمبرداری هستیم:

📸 عکاسی تولد و جشن‌ها
💒 عکاسی و فیلمبرداری عروسی
💍 فیلمبرداری مراسم عقد
🎭 عکاسی و فیلمبرداری رویدادها

از منوی زیر می‌توانید:
🆕 رزرو جدید ایجاد کنید
🔍 رزروهای خود را جستجو کنید
📞 با ما تماس بگیرید

لطفاً گزینه مورد نظرتان را انتخاب کنید:
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.get_main_menu_keyboard(is_admin),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور راهنما /help"""
        help_text = """
📖 **راهنمای استفاده از ربات استودیو ماندنی**

**دستورات اصلی:**
/start - شروع کار با ربات
/help - نمایش این راهنما
/search - جستجوی سریع رزرو

**نحوه رزرو:**
۱. روی "رزرو جدید" کلیک کنید
۲. اطلاعات شخصی خود را وارد کنید
۳. نوع خدمت مورد نظر را انتخاب کنید
۴. جزئیات خدمت را مشخص کنید
۵. تاریخ و زمان مراسم را وارد کنید
۶. هزینه محاسبه و فاکتور ارسال می‌شود

**جستجوی رزرو:**
- با کد رزرو (مثال: ABC123)
- با نام مشتری
- با شماره تلفن

**پشتیبانی:**
در صورت نیاز به کمک از گزینه "تماس با ادمین" استفاده کنید.

🌟 استودیو ماندنی - کیفیت در خدمت شما
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور جستجو /search"""
        await update.message.reply_text(
            "🔍 لطفاً کد رزرو، نام مشتری، یا شماره تلفن را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        return WAITING_SEARCH_QUERY
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت callback های دکمه‌ها"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # بررسی محدودیت نرخ
        if not self.db.check_rate_limit(user_id, "button_click", 30, 1):
            await query.edit_message_text("⚠️ تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید.")
            return
        
        # منوی اصلی
        if data == "back_to_main":
            is_admin = self.db.is_admin(user_id)
            await query.edit_message_text(
                "🏠 منوی اصلی:",
                reply_markup=self.get_main_menu_keyboard(is_admin)
            )
        
        # رزرو جدید
        elif data == "new_reservation":
            await self.start_new_reservation(query, context)
        
        # جستجوی رزرو
        elif data == "search_reservation":
            await query.edit_message_text(
                "🔍 لطفاً کد رزرو، نام مشتری، یا شماره تلفن را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]])
            )
            return WAITING_SEARCH_QUERY
        
        # رزروهای من
        elif data == "my_reservations":
            await self.show_user_reservations(query, context)
        
        # تماس با ادمین
        elif data == "contact_admin":
            contact_text = """
📞 **راه‌های تماس با استودیو ماندنی**

📱 تلفن: ۰۹۱۸۴۰۰۴۸۹۳
📧 ایمیل: studiomandani@gmail.com
📷 اینستاگرام: @mandanistudiooo
📍 آدرس: کردستان مریوان، ده متری ورودی شهرک نوروز

⏰ **ساعات کاری:**
شنبه تا پنج‌شنبه: ۱۰:۰۰ - ۲۲:۰۰
جمعه: تعطیل

💬 همچنین می‌توانید پیام خود را در همین چت بنویسید تا در اسرع وقت پاسخ دهیم.
            """
            await query.edit_message_text(
                contact_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # انتخاب نوع خدمت
        elif data.startswith("service_"):
            service_type = data.replace("service_", "")
            self.user_data[user_id] = {"service_type": service_type}
            await self.handle_service_selection(query, context, service_type)
        
        # پنل ادمین
        elif data == "admin_panel":
            if not self.db.is_admin(user_id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید!")
                return
            
            await query.edit_message_text(
                "👨‍💼 **پنل مدیریت**\n\nلطفاً گزینه مورد نظر را انتخاب کنید:",
                reply_markup=self.get_admin_panel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # آمار
        elif data == "statistics":
            if not self.db.is_admin(user_id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید!")
                return
            
            await self.show_statistics(query, context)
        
        # عملیات ادمین
        elif data.startswith("admin_"):
            await self.handle_admin_operations(query, context, data)
        
        # سایر callback ها
        else:
            await self.handle_other_callbacks(query, context, data)
    
    async def start_new_reservation(self, query, context):
        """شروع رزرو جدید"""
        user_id = query.from_user.id
        
        # بررسی اینکه آیا کاربر قبلاً اطلاعات داده یا نه
        customer = self.db.get_customer_by_telegram_id(user_id)
        
        if customer:
            # کاربر قبلی - انتخاب نوع خدمت
            await query.edit_message_text(
                f"👋 سلام {customer['name']} عزیز!\n\n🎬 لطفاً نوع خدمت مورد نظرتان را انتخاب کنید:",
                reply_markup=self.get_service_type_keyboard()
            )
        else:
            # کاربر جدید - دریافت اطلاعات
            await query.edit_message_text(
                "🆕 **رزرو جدید**\n\nلطفاً نام کامل خود را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_NAME
    
    async def handle_service_selection(self, query, context, service_type):
        """مدیریت انتخاب نوع خدمت"""
        user_id = query.from_user.id
        
        # دریافت پیشنهادات هوشمند
        recommendations = SmartRecommendations.get_service_recommendations(service_type)
        service_name = CostCalculator.get_service_name(service_type)
        
        # ذخیره نوع خدمت
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['service_type'] = service_type
        
        # اگر عروسی است، نام عروس را بپرس
        if service_type == 'wedding':
            await query.edit_message_text(
                f"� **{service_name}**\n\n👰 لطفاً نام عروس را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_BRIDE_NAME
        else:
            # برای سایر خدمات، مستقیم به تعداد مهمان برو
            await query.edit_message_text(
                f"🎬 **{service_name}**\n\n👥 لطفاً تعداد مهمانان را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_GUEST_COUNT
    
    async def handle_admin_operations(self, query, context, data):
        """مدیریت عملیات ادمین"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ شما دسترسی ادمین ندارید!")
            return
        
        if data == "admin_all_reservations":
            await self.show_all_reservations(query, context)
        
        elif data == "admin_pending_reservations":
            await self.show_pending_reservations(query, context)
        
        elif data == "admin_backup":
            await self.create_backup(query, context)
        
        elif data == "admin_add_admin":
            await query.edit_message_text(
                "👨‍💼 **افزودن ادمین جدید**\n\nلطفاً username کاربر را وارد کنید:\n(بدون @ - مثال: username)",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_ADMIN_USERNAME
    
    async def show_statistics(self, query, context):
        """نمایش آمار"""
        stats = self.db.get_statistics()
        stats_text = MessageFormatter.format_statistics(stats)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="statistics"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_user_reservations(self, query, context):
        """نمایش رزروهای کاربر"""
        user_id = query.from_user.id
        reservations = self.db.get_user_reservations(user_id, 5)
        
        if not reservations:
            await query.edit_message_text(
                "📋 شما هنوز هیچ رزروی ندارید.\n\nبرای ایجاد رزرو جدید از منوی اصلی استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🆕 رزرو جدید", callback_data="new_reservation"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]])
            )
            return
        
        text = "📋 **رزروهای شما:**\n\n"
        keyboard = []
        
        for reservation in reservations:
            service_name = CostCalculator.get_service_name(reservation['service_type'])
            status_emoji = "⏳" if reservation['booking_status'] == 'pending' else "✅" if reservation['booking_status'] == 'confirmed' else "❌"
            
            text += f"{status_emoji} کد: `{reservation['reservation_code']}` - {service_name}\n"
            
            keyboard.append([InlineKeyboardButton(
                f"📄 {reservation['reservation_code']}",
                callback_data=f"view_reservation_{reservation['reservation_code']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت پیام‌های متنی"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # بررسی محدودیت نرخ
        if not self.db.check_rate_limit(user_id, "text_message", 10, 1):
            await update.message.reply_text("⚠️ لطفاً کمی آهسته‌تر پیام بفرستید.")
            return
        
        # بررسی state های مختلف مکالمه
        current_state = context.user_data.get('state', None)
        
        if current_state == WAITING_NAME:
            return await self.handle_name_input(update, context)
        elif current_state == WAITING_PHONE:
            return await self.handle_phone_input(update, context)
        elif current_state == WAITING_EMAIL:
            return await self.handle_email_input(update, context)
        elif current_state == WAITING_SEARCH_QUERY:
            return await self.handle_search_query(update, context)
        else:
            # پیام عادی - ارسال به ادمین‌ها
            await self.forward_to_admins(update, context)
    
    async def handle_search_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت جستجوی رزرو"""
        user_id = update.effective_user.id
        query = update.message.text.strip()
        
        # بررسی محدودیت نرخ برای جستجو
        if not self.db.check_rate_limit(user_id, "search", 5, 1):
            await update.message.reply_text("🔍 تعداد جستجوی شما بیش از حد مجاز است. لطفاً کمی صبر کنید.")
            return
        
        # ثبت لاگ
        self.db.log_action(user_id, "search_reservation", query)
        
        # جستجو در پایگاه داده
        results = self.db.search_reservations(query)
        
        if not results:
            await update.message.reply_text(
                "🔍 هیچ رزروی با این مشخصات پیدا نشد.\n\nلطفاً:\n• کد رزرو را بررسی کنید\n• نام کامل را وارد کنید\n• شماره تلفن کامل را بنویسید",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]])
            )
            return ConversationHandler.END
        
        # نمایش نتایج
        if len(results) == 1:
            # فقط یک نتیجه - نمایش جزئیات
            reservation = results[0]
            text = MessageFormatter.format_reservation_summary(reservation)
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # چندین نتیجه - نمایش لیست
            text = f"🔍 **نتایج جستجو ({len(results)} مورد):**\n\n"
            keyboard = []
            
            for i, reservation in enumerate(results[:10], 1):  # حداکثر ۱۰ نتیجه
                service_name = CostCalculator.get_service_name(reservation['service_type'])
                status_emoji = "⏳" if reservation['booking_status'] == 'pending' else "✅" if reservation['booking_status'] == 'confirmed' else "❌"
                
                text += f"{i}. {status_emoji} `{reservation['reservation_code']}` - {service_name}\n"
                text += f"   👤 {reservation.get('customer_name', 'نامشخص')}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"{i}. {reservation['reservation_code']}",
                    callback_data=f"view_reservation_{reservation['reservation_code']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    async def handle_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی نام"""
        user_id = update.effective_user.id
        name = update.message.text.strip()
        
        if len(name) < 2:
            await update.message.reply_text("❌ لطفاً نام خود را وارد کنید (حداقل ۲ کاراکتر)")
            return WAITING_NAME
        
        # ذخیره نام
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['name'] = name
        
        await update.message.reply_text(
            f"✅ نام ثبت شد: {name}\n\n👨‍👩‍👧‍👦 لطفاً نام خانوادگی خود را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        context.user_data['state'] = WAITING_FAMILY_NAME
        return WAITING_FAMILY_NAME
    
    async def handle_family_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی نام خانوادگی"""
        user_id = update.effective_user.id
        family_name = update.message.text.strip()
        
        if len(family_name) < 2:
            await update.message.reply_text("❌ لطفاً نام خانوادگی خود را وارد کنید (حداقل ۲ کاراکتر)")
            return WAITING_FAMILY_NAME
        
        self.user_data[user_id]['family_name'] = family_name
        
        await update.message.reply_text(
            f"✅ نام خانوادگی ثبت شد: {family_name}\n\n📱 لطفاً شماره تلفن خود را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        context.user_data['state'] = WAITING_PHONE
        return WAITING_PHONE
    
    async def handle_phone_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی شماره تلفن"""
        user_id = update.effective_user.id
        phone = update.message.text.strip()
        
        if not ValidationUtils.validate_phone(phone):
            await update.message.reply_text(
                "❌ شماره تلفن نامعتبر است!\n\nلطفاً شماره تلفن صحیح وارد کنید:\n• موبایل: ۰۹۱۲۳۴۵۶۷۸۹\n• تلفن ثابت: ۰۲۱۱۲۳۴۵۶۷۸"
            )
            return WAITING_PHONE
        
        self.user_data[user_id]['phone'] = phone
        
        await update.message.reply_text(
            "✅ شماره تلفن ثبت شد!\n\n📧 لطفاً ایمیل خود را وارد کنید (اختیاری - برای رد کردن /skip بنویسید):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_email"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        context.user_data['state'] = WAITING_EMAIL
        return WAITING_EMAIL
    
    async def handle_email_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی ایمیل"""
        user_id = update.effective_user.id
        email = update.message.text.strip()
        
        if email.lower() == '/skip':
            email = None
        elif not ValidationUtils.validate_email(email):
            await update.message.reply_text("❌ ایمیل نامعتبر است! لطفاً ایمیل صحیح وارد کنید یا /skip بنویسید.")
            return WAITING_EMAIL
        
        self.user_data[user_id]['email'] = email
        
        # ذخیره مشتری در پایگاه داده
        try:
            full_name = f"{self.user_data[user_id]['name']} {self.user_data[user_id]['family_name']}"
            customer_id = self.db.add_customer(
                telegram_id=user_id,
                name=full_name,
                phone=self.user_data[user_id]['phone'],
                email=email
            )
            
            await update.message.reply_text(
                f"✅ اطلاعات شما ثبت شد!\n\n🎬 حالا لطفاً نوع خدمت مورد نظرتان را انتخاب کنید:",
                reply_markup=self.get_service_type_keyboard()
            )
            
            context.user_data['state'] = None
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"خطا در ثبت مشتری: {e}")
            await update.message.reply_text("❌ خطا در ثبت اطلاعات! لطفاً دوباره تلاش کنید.")
            return ConversationHandler.END
    
    async def handle_bride_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی نام عروس"""
        user_id = update.effective_user.id
        bride_name = update.message.text.strip()
        
        if len(bride_name) < 2:
            await update.message.reply_text("❌ لطفاً نام عروس را وارد کنید (حداقل ۲ کاراکتر)")
            return WAITING_BRIDE_NAME
        
        self.user_data[user_id]['bride_name'] = bride_name
        
        await update.message.reply_text(
            f"✅ نام عروس ثبت شد: {bride_name}\n\n👥 لطفاً تعداد مهمانان را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        return WAITING_GUEST_COUNT
    
    async def handle_guest_count_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی تعداد مهمانان"""
        user_id = update.effective_user.id
        guest_count_text = update.message.text.strip()
        
        try:
            guest_count = int(guest_count_text)
            if guest_count < 1 or guest_count > 10000:
                raise ValueError("تعداد نامعتبر")
        except ValueError:
            await update.message.reply_text("❌ لطفاً تعداد مهمانان را به صورت عدد وارد کنید (مثال: 150)")
            return WAITING_GUEST_COUNT
        
        self.user_data[user_id]['guest_count'] = guest_count
        
        await update.message.reply_text(
            f"✅ تعداد مهمانان ثبت شد: {guest_count} نفر\n\n📅 لطفاً تاریخ مراسم را وارد کنید (فرمت: ۱۴۰۳/۰۸/۱۵):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        return WAITING_EVENT_DATE
    
    async def handle_event_date_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی تاریخ مراسم"""
        user_id = update.effective_user.id
        event_date = update.message.text.strip()
        
        # اعتبارسنجی ساده تاریخ
        if len(event_date) < 8:
            await update.message.reply_text("❌ لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: ۱۴۰۳/۰۸/۱۵)")
            return WAITING_EVENT_DATE
        
        self.user_data[user_id]['event_date'] = event_date
        
        await update.message.reply_text(
            f"✅ تاریخ مراسم ثبت شد: {event_date}\n\n📍 لطفاً مکان مراسم را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        return WAITING_LOCATION
    
    async def handle_location_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی مکان مراسم"""
        user_id = update.effective_user.id
        location = update.message.text.strip()
        
        if len(location) < 3:
            await update.message.reply_text("❌ لطفاً مکان مراسم را به طور کامل وارد کنید")
            return WAITING_LOCATION
        
        self.user_data[user_id]['location'] = location
        
        await update.message.reply_text(
            f"✅ مکان مراسم ثبت شد: {location}\n\n📷 لطفاً تعداد دوربین مورد نظر را انتخاب کنید:",
            reply_markup=self.get_number_keyboard(1, 5, "cameras")
        )
        
        return WAITING_CAMERAS
    
    async def handle_camera_quality_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی کیفیت دوربین"""
        user_id = update.effective_user.id
        quality = update.message.text.strip()
        
        self.user_data[user_id]['camera_quality'] = quality
        
        await update.message.reply_text(
            f"✅ کیفیت دوربین ثبت شد: {quality}\n\n🚁 آیا نیاز به هلی‌شات دارید؟",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("بله ✅", callback_data="helishot_yes"),
                InlineKeyboardButton("خیر ❌", callback_data="helishot_no")
            ]])
        )
        
        return WAITING_HELISHOT
    
    async def handle_admin_username_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی username ادمین"""
        user_id = update.effective_user.id
        username = update.message.text.strip().replace('@', '')
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ شما دسترسی ادمین ندارید!")
            return ConversationHandler.END
        
        # در پیاده‌سازی واقعی، باید telegram_id کاربر را از username پیدا کرد
        # این کار نیاز به API اضافی دارد، پس فرض می‌کنیم ادمین telegram_id را می‌دهد
        try:
            new_admin_id = int(username)  # فرض: ادمین telegram_id می‌دهد
            
            if self.db.add_admin(new_admin_id, username, None, user_id):
                await update.message.reply_text(
                    f"✅ کاربر {username} به عنوان ادمین اضافه شد!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
                    ]])
                )
            else:
                await update.message.reply_text("❌ این کاربر قبلاً ادمین است!")
                
        except ValueError:
            await update.message.reply_text("❌ لطفاً شناسه عددی کاربر (telegram_id) را وارد کنید!")
            return WAITING_ADMIN_USERNAME
        
        return ConversationHandler.END
    
    async def handle_other_callbacks(self, query, context, data):
        """مدیریت سایر callback ها"""
        user_id = query.from_user.id
        
        # انتخاب تعداد دوربین
        if data.startswith("cameras_"):
            cameras = int(data.split("_")[1])
            self.user_data[user_id]['cameras'] = cameras
            
            await query.edit_message_text(
                f"✅ تعداد دوربین: {PersianDateUtils.english_to_persian_digits(str(cameras))}\n\n🎥 لطفاً کیفیت دوربین مورد نظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("4K", callback_data="quality_4K"),
                    InlineKeyboardButton("Full HD", callback_data="quality_fullhd")
                ], [
                    InlineKeyboardButton("HD", callback_data="quality_hd"),
                    InlineKeyboardButton("سایر", callback_data="quality_other")
                ]])
            )
        
        # انتخاب کیفیت دوربین
        elif data.startswith("quality_"):
            quality = data.replace("quality_", "").replace("_", " ")
            if quality == "other":
                await query.edit_message_text(
                    "🎥 لطفاً کیفیت دلخواه خود را تایپ کنید:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                    ]])
                )
                return WAITING_CAMERA_QUALITY
            else:
                self.user_data[user_id]['camera_quality'] = quality
                await query.edit_message_text(
                    f"✅ کیفیت دوربین: {quality}\n\n🚁 آیا نیاز به هلی‌شات دارید؟",
                    reply_markup=self.get_yes_no_keyboard("helishot_yes", "helishot_no")
                )
        
        # انتخاب هلی‌شات
        elif data in ["helishot_yes", "helishot_no"]:
            self.user_data[user_id]['helishot'] = data == "helishot_yes"
            helishot_text = "بله" if data == "helishot_yes" else "خیر"
            
            await query.edit_message_text(
                f"✅ هلی‌شات: {helishot_text}\n\n👥 تعداد عکاس/فیلمبردار مورد نیاز:",
                reply_markup=self.get_number_keyboard(1, 4, "photographers")
            )
        
        # انتخاب تعداد عکاس
        elif data.startswith("photographers_"):
            photographers = int(data.split("_")[1])
            self.user_data[user_id]['photographers'] = photographers
            
            await self.calculate_and_show_cost(query, context, user_id)
        
        # نمایش جزئیات رزرو
        elif data.startswith("view_reservation_"):
            reservation_code = data.replace("view_reservation_", "")
            await self.show_reservation_details(query, context, reservation_code)
        
        # رد کردن ایمیل
        elif data == "skip_email":
            await self.handle_email_skip(query, context)
    
    async def handle_email_skip(self, query, context):
        """مدیریت رد کردن ایمیل"""
        user_id = query.from_user.id
        
        try:
            customer_id = self.db.add_customer(
                telegram_id=user_id,
                name=self.user_data[user_id]['name'],
                phone=self.user_data[user_id]['phone'],
                email=None
            )
            
            await query.edit_message_text(
                f"✅ اطلاعات شما ثبت شد!\n\n🎬 حالا لطفاً نوع خدمت مورد نظرتان را انتخاب کنید:",
                reply_markup=self.get_service_type_keyboard()
            )
            
        except Exception as e:
            logger.error(f"خطا در ثبت مشتری: {e}")
            await query.edit_message_text("❌ خطا در ثبت اطلاعات! لطفاً دوباره تلاش کنید.")
    
    async def calculate_and_show_cost(self, query, context, user_id):
        """محاسبه و نمایش هزینه"""
        user_data = self.user_data[user_id]
        
        # محاسبه هزینه
        cost_breakdown = CostCalculator.calculate_service_cost(
            user_data['service_type'],
            user_data
        )
        
        # تولید کد رزرو
        reservation_code = ReservationCodeGenerator.generate_code()
        
        # ذخیره رزرو در پایگاه داده
        try:
            reservation_id = self.db.create_reservation(
                telegram_id=user_id,
                reservation_code=reservation_code,
                service_type=user_data['service_type'],
                service_details=user_data,
                total_cost=cost_breakdown['total']
            )
            
            # نمایش هزینه و فاکتور
            cost_text = MessageFormatter.format_cost_breakdown(cost_breakdown)
            cost_text += f"\n\n📋 **کد رزرو شما: `{reservation_code}`**\n\n"
            cost_text += "💳 برای تکمیل رزرو، لطفاً بیعانه را پرداخت کنید:"
            
            keyboard = [
                [InlineKeyboardButton("💰 پرداخت بیعانه", callback_data=f"payment_{reservation_code}")],
                [InlineKeyboardButton("📄 دانلود فاکتور", callback_data=f"invoice_{reservation_code}")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main")]
            ]
            
            await query.edit_message_text(
                cost_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # ثبت لاگ
            self.db.log_action(user_id, "reservation_created", reservation_code)
            
            # ارسال نوتیفیکیشن به ادمین‌ها
            await self.send_admin_notification(user_data, reservation_code, context)
            
        except Exception as e:
            logger.error(f"خطا در ایجاد رزرو: {e}")
            await query.edit_message_text("❌ خطا در ایجاد رزرو! لطفاً دوباره تلاش کنید.")
    
    async def show_reservation_details(self, query, context, reservation_code):
        """نمایش جزئیات رزرو"""
        reservation = self.db.get_reservation_by_code(reservation_code)
        
        if not reservation:
            await query.edit_message_text("❌ رزرو پیدا نشد!")
            return
        
        # بررسی دسترسی
        user_id = query.from_user.id
        if not self.db.is_admin(user_id) and reservation['telegram_id'] != user_id:
            await query.edit_message_text("❌ شما دسترسی به این رزرو ندارید!")
            return
        
        details_text = MessageFormatter.format_reservation_summary(reservation)
        
        keyboard = [
            [InlineKeyboardButton("📄 دانلود فاکتور", callback_data=f"invoice_{reservation_code}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            details_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_all_reservations(self, query, context):
        """نمایش همه رزروها برای ادمین"""
        # در پیاده‌سازی کامل، pagination اضافه کنید
        stats = self.db.get_statistics()
        
        text = f"""
📊 **خلاصه رزروها**

📋 کل رزروها: {stats['total_reservations']}
⏳ در انتظار: {stats['pending_reservations']}
✅ تأیید شده: {stats['confirmed_reservations']}

💰 درآمد کل: {CostCalculator.format_currency(stats['total_revenue'])}
        """
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_pending_reservations(self, query, context):
        """نمایش رزروهای در انتظار"""
        # در پیاده‌سازی کامل، لیست رزروهای pending را نشان دهید
        await query.edit_message_text(
            "⏳ **رزروهای در انتظار تأیید**\n\n(این بخش در حال توسعه است)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def create_backup(self, query, context):
        """ایجاد پشتیبان گیری"""
        try:
            backup_data = self.db.backup_data()
            
            # تولید فایل JSON
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
                backup_file = f.name
            
            # ارسال فایل
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=open(backup_file, 'rb'),
                filename=f"mandani_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                caption="💾 **پشتیبان گیری کامل**\n\nاین فایل حاوی تمام اطلاعات پایگاه داده است."
            )
            
            await query.edit_message_text(
                "✅ پشتیبان گیری با موفقیت انجام شد!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
                ]])
            )
            
            # حذف فایل موقت
            os.unlink(backup_file)
            
        except Exception as e:
            logger.error(f"خطا در پشتیبان گیری: {e}")
            await query.edit_message_text("❌ خطا در پشتیبان گیری!")
    
    async def forward_to_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ارسال پیام به ادمین‌ها"""
        user = update.effective_user
        message_text = update.message.text
        
        admins = self.db.get_all_admins()
        
        if not admins:
            logger.warning("هیچ ادمینی در پایگاه داده یافت نشد")
            await update.message.reply_text(
                "⚠️ در حال حاضر ادمینی در دسترس نیست. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")
                ]])
            )
            return
        
        admin_message = f"""
💬 **پیام جدید از کاربر**

👤 نام: {user.first_name} {user.last_name or ''}
🆔 شناسه: {user.id}
🔤 نام کاربری: @{user.username or 'ندارد'}

📝 پیام:
{message_text}

---
برای پاسخ، از دستور /reply {user.id} [پیام] استفاده کنید
        """
        
        sent_count = 0
        for admin in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin['telegram_id'],
                    text=admin_message,
                    parse_mode=ParseMode.MARKDOWN
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"خطا در ارسال پیام به ادمین {admin['telegram_id']}: {e}")
        
        if sent_count > 0:
            await update.message.reply_text(
                f"✅ پیام شما به {sent_count} ادمین ارسال شد.\nدر اسرع وقت پاسخ خواهید گرفت.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")
                ]])
            )
        else:
            await update.message.reply_text(
                "❌ خطا در ارسال پیام به ادمین‌ها. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")
                ]])
            )
    
    async def reply_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاسخ ادمین به کاربر"""
        user_id = update.effective_user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ شما دسترسی ادمین ندارید!")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ فرمت صحیح: /reply [شناسه_کاربر] [پیام]")
            return
        
        try:
            target_user_id = int(context.args[0])
            reply_message = " ".join(context.args[1:])
            
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 **پاسخ از استودیو ماندنی:**\n\n{reply_message}",
                parse_mode=ParseMode.MARKDOWN
            )
            
            await update.message.reply_text("✅ پیام با موفقیت ارسال شد.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال پیام: {str(e)}")
    
    def setup_conversation_handler(self):
        """تنظیم ConversationHandler برای رزرو"""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.button_callback, pattern="^new_reservation$"),
                CommandHandler("search", self.search_command)
            ],
            states={
                WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name_input)],
                WAITING_FAMILY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_family_name_input)],
                WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_phone_input)],
                WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_email_input)],
                WAITING_BRIDE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bride_name_input)],
                WAITING_GUEST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_guest_count_input)],
                WAITING_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_event_date_input)],
                WAITING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_location_input)],
                WAITING_CAMERAS: [CallbackQueryHandler(self.handle_other_callbacks)],
                WAITING_CAMERA_QUALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_camera_quality_input)],
                WAITING_HELISHOT: [CallbackQueryHandler(self.handle_other_callbacks)],
                WAITING_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_search_query)],
                WAITING_ADMIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_username_input)],
            },
            fallbacks=[
                CallbackQueryHandler(self.button_callback, pattern="^back_to_main$"),
                CommandHandler("start", self.start_command)
            ],
            per_message=False,
            per_chat=True,
            per_user=False
        )
    
    async def setup_reminders(self, application):
        """تنظیم یادآوری‌های خودکار"""
        job_queue = application.job_queue
        
        # یادآوری روزانه برای مراسم فردا
        job_queue.run_daily(
            self.check_upcoming_events,
            time=datetime.now().time().replace(hour=9, minute=0, second=0),
            name="daily_event_reminder"
        )
        
        # یادآوری برای تحویل پروژه‌ها
        job_queue.run_daily(
            self.check_delivery_reminders,
            time=datetime.now().time().replace(hour=10, minute=0, second=0),
            name="daily_delivery_reminder"
        )
    
    async def check_upcoming_events(self, context: ContextTypes.DEFAULT_TYPE):
        """بررسی مراسم‌های فردا"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        events = self.db.get_reservations_by_date_range(
            tomorrow.strftime('%Y-%m-%d'),
            tomorrow.strftime('%Y-%m-%d')
        )
        
        for event in events:
            if event['booking_status'] == 'confirmed':
                # ارسال یادآوری به مشتری
                try:
                    reminder_text = f"""
🔔 **یادآوری مراسم**

سلام {event.get('customer_name', '')} عزیز!

مراسم شما فردا برگزار می‌شود:
📅 تاریخ: {PersianDateUtils.format_persian_date(tomorrow)}
🕐 زمان: {event.get('event_time', 'نامشخص')}
📍 مکان: {event.get('location', 'نامشخص')}

تیم ما آماده حضور و ارائه بهترین خدمات هستند.

🌟 استودیو ماندنی
                    """
                    
                    await context.bot.send_message(
                        chat_id=event['telegram_id'],
                        text=reminder_text,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"خطا در ارسال یادآوری مراسم: {e}")
    
    async def check_delivery_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """بررسی یادآوری‌های تحویل"""
        # پروژه‌هایی که ۳ روز تا تحویل دارند
        target_date = (datetime.now() + timedelta(days=3)).date()
        events = self.db.get_reservations_by_date_range(
            target_date.strftime('%Y-%m-%d'),
            target_date.strftime('%Y-%m-%d')
        )
        
        for event in events:
            if event['booking_status'] == 'confirmed' and event.get('delivery_date'):
                try:
                    reminder_text = f"""
📸 **یادآوری تحویل پروژه**

سلام {event.get('customer_name', '')} عزیز!

پروژه شما (کد: {event['reservation_code']}) ۳ روز دیگر آماده تحویل خواهد بود.

📅 تاریخ تحویل: {event['delivery_date']}

لطفاً برای هماهنگی تحویل با ما تماس بگیرید.

📞 ۰۲۱-۱۲۳۴۵۶۷۸
🌟 استودیو ماندنی
                    """
                    
                    await context.bot.send_message(
                        chat_id=event['telegram_id'],
                        text=reminder_text,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"خطا در ارسال یادآوری تحویل: {e}")
    
    def run(self):
        """اجرای ربات"""
        # ایجاد Application با JobQueue
        try:
            from telegram.ext import JobQueue
            application = Application.builder().token(BOT_TOKEN).job_queue(JobQueue()).build()
            logger.info("✅ JobQueue فعال شد")
        except ImportError:
            application = Application.builder().token(BOT_TOKEN).build()
            logger.warning("⚠️ JobQueue در دسترس نیست")
        
        # اضافه کردن handler ها
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("reply", self.reply_command))
        application.add_handler(self.setup_conversation_handler())
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # تنظیم یادآوری‌ها (اگر JobQueue موجود باشد)
        try:
            if application.job_queue:
                application.job_queue.run_daily(
                    self.check_upcoming_events,
                    time=datetime.now().time().replace(hour=9, minute=0, second=0),
                    name="daily_event_reminder"
                )
                
                application.job_queue.run_daily(
                    self.check_delivery_reminders,
                    time=datetime.now().time().replace(hour=10, minute=0, second=0),
                    name="daily_delivery_reminder"
                )
                logger.info("✅ یادآوری‌های خودکار تنظیم شد")
        except Exception as e:
            logger.warning(f"⚠️ خطا در تنظیم یادآوری‌ها: {e}")
        
        logger.info("🚀 ربات استودیو ماندنی شروع به کار کرد...")
        
        # شروع polling
        application.run_polling(drop_pending_updates=True)


def main():
    """تابع اصلی"""
    if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ لطفاً BOT_TOKEN را در متغیر محیطی تنظیم کنید!")
        sys.exit(1)
    
    bot = MandaniStudioBot()
    bot.run()


if __name__ == "__main__":
    main()
