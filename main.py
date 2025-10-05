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
 WAITING_BRIDE_NAME, WAITING_GUEST_COUNT, WAITING_EVENT_DATE, WAITING_EVENT_TIME, WAITING_LOCATION,
 WAITING_DURATION, WAITING_SPECIAL_REQUESTS, WAITING_CAMERAS, WAITING_CAMERA_QUALITY, 
 WAITING_HELISHOT, WAITING_PHOTOGRAPHERS, WAITING_CUSTOM_COST, WAITING_PAYMENT_METHOD, 
 WAITING_TRANSACTION_ID, WAITING_SEARCH_QUERY, WAITING_ADMIN_USERNAME) = range(21)


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
        self.reservation_drafts = {}  # ذخیره پیش‌نویس رزروها
        
        logger.info("🚀 ربات استودیو ماندنی راه‌اندازی شد")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """مدیریت خطاهای ربات"""
        logger.error("خطا در ربات:", exc_info=context.error)
        
        # ارسال پیام خطا به کاربر (اگر update موجود باشد)
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ متأسفانه خطایی رخ داده. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
            except Exception:
                pass  # اگر نتوان پیام ارسال کرد، نادیده بگیر
    
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
� **زمان شروع:** {user_data.get('event_time', 'نامشخص')}
�📍 **مکان:** {user_data.get('location', 'نامشخص')}
⏱️ **مدت زمان:** {user_data.get('duration', 'نامشخص')}
📝 **درخواست‌های خاص:** {user_data.get('special_requests', 'ندارد')}
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
        
        # انتخاب نوع خدمت - فقط در conversation state
        elif data.startswith("service_") and context.user_data.get('state') == WAITING_SERVICE_TYPE:
            service_type = data.replace("service_", "")
            service_name = CostCalculator.get_service_name(service_type)
            
            # ذخیره نوع خدمت
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            self.user_data[user_id]['service_type'] = service_type
            
            # اگر عروسی است، نام عروس را بپرس
            if service_type == 'wedding':
                await query.edit_message_text(
                    f"{self.get_progress_indicator('event_details')}\n"
                    f"💒 **{service_name}**\n\n👰 لطفاً نام عروس را وارد کنید:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                    ]]),
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['state'] = WAITING_BRIDE_NAME
                return WAITING_BRIDE_NAME
            else:
                # برای سایر خدمات، مستقیم به تاریخ مراسم برو
                await query.edit_message_text(
                    f"{self.get_progress_indicator('event_details')}\n"
                    f"🎬 **{service_name}**\n\n📅 لطفاً تاریخ مراسم را وارد کنید (فرمت: ۱۴۰۳/۰۸/۱۵):",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                    ]]),
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['state'] = WAITING_EVENT_DATE
                return WAITING_EVENT_DATE
        
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
    
    def get_progress_indicator(self, current_step: str) -> str:
        """نمایش progress indicator برای کاربر"""
        steps = {
            'personal_info': '1️⃣ اطلاعات شخصی',
            'service_type': '2️⃣ انتخاب سرویس', 
            'event_details': '3️⃣ جزئیات مراسم',
            'technical_specs': '4️⃣ مشخصات فنی',
            'confirmation': '5️⃣ تایید نهایی'
        }
        
        progress_map = {
            'personal_info': '🔵⚪⚪⚪⚪',
            'service_type': '✅🔵⚪⚪⚪',
            'event_details': '✅✅🔵⚪⚪',
            'technical_specs': '✅✅✅🔵⚪',
            'confirmation': '✅✅✅✅🔵'
        }
        
        return f"{progress_map.get(current_step, '')}\n{steps.get(current_step, '')}\n"

    def get_navigation_keyboard(self, show_back: bool = True, show_skip: bool = False, skip_callback: str = "") -> InlineKeyboardMarkup:
        """ایجاد کیبورد navigation با دکمه‌های مختلف"""
        buttons = []
        
        if show_skip and skip_callback:
            buttons.append([InlineKeyboardButton("⏭️ رد کردن", callback_data=skip_callback)])
        
        if show_back:
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        
        return InlineKeyboardMarkup(buttons) if buttons else None

    def get_help_text(self, step: str) -> str:
        """دریافت متن راهنما برای هر مرحله"""
        help_texts = {
            'date_format': """
📅 **راهنمای تاریخ:**
• فرمت صحیح: ۱۴۰۳/۰۸/۱۵
• از اعداد فارسی استفاده کنید
• سال/ماه/روز
• مثال: ۱۴۰۳/۱۲/۲۹
            """,
            'time_format': """
🕐 **راهنمای زمان:**
• فرمت صحیح: ۱۸:۳۰ یا ۶:۳۰ عصر
• از اعداد فارسی استفاده کنید
• ۲۴ ساعته یا ۱۲ ساعته
• مثال: ۱۴:۰۰ یا ۲ بعدازظهر
            """,
            'phone_format': """
📱 **راهنمای شماره تماس:**
• موبایل: ۰۹۱۲۳۴۵۶۷۸۹
• تلفن ثابت: ۰۲۱۱۲۳۴۵۶۷۸
• شامل کد شهر/اپراتور
• بدون فاصله یا خط تیره
            """
        }
        return help_texts.get(step, "")

    def save_reservation_draft(self, user_id: int, current_state: int):
        """ذخیره پیش‌نویس رزرو"""
        if user_id in self.user_data:
            self.reservation_drafts[user_id] = {
                'data': self.user_data[user_id].copy(),
                'state': current_state,
                'timestamp': datetime.now().isoformat()
            }
    
    def load_reservation_draft(self, user_id: int) -> tuple:
        """بارگیری پیش‌نویس رزرو"""
        if user_id in self.reservation_drafts:
            draft = self.reservation_drafts[user_id]
            # بررسی اینکه پیش‌نویس جدید باشد (کمتر از 24 ساعت)
            draft_time = datetime.fromisoformat(draft['timestamp'])
            if (datetime.now() - draft_time).hours < 24:
                return draft['data'], draft['state']
            else:
                # حذف پیش‌نویس قدیمی
                del self.reservation_drafts[user_id]
        return None, None

    async def resume_from_state(self, query, context, user_id: int, state: int):
        """ادامه رزرو از state مشخص"""
        # بر اساس state، کاربر را به نقطه مناسب هدایت کن
        if state == WAITING_EVENT_DATE:
            await query.edit_message_text(
                f"{self.get_progress_indicator('event_details')}\n"
                "📅 لطفاً تاریخ مراسم را وارد کنید (فرمت: ۱۴۰۳/۰۸/۱۵):",
                reply_markup=self.get_navigation_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_EVENT_DATE
        elif state == WAITING_EVENT_TIME:
            await query.edit_message_text(
                f"{self.get_progress_indicator('event_details')}\n"
                "🕐 لطفاً ساعت شروع مراسم را وارد کنید (مثال: ۱۸:۳۰):",
                reply_markup=self.get_navigation_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_EVENT_TIME
        elif state == WAITING_LOCATION:
            await query.edit_message_text(
                f"{self.get_progress_indicator('event_details')}\n"
                "📍 لطفاً مکان مراسم را وارد کنید:",
                reply_markup=self.get_navigation_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_LOCATION
        # برای سایر state ها می‌توان اضافه کرد
        else:
            await self.start_fresh_reservation(query, context)
    
    async def start_fresh_reservation(self, query, context):
        """شروع رزرو تازه بدون draft"""
        user_id = query.from_user.id
        customer = self.db.get_customer_by_telegram_id(user_id)
        
        if customer:
            # کاربر قبلی - انتخاب نوع خدمت
            await query.edit_message_text(
                f"{self.get_progress_indicator('service_type')}\n"
                f"👋 سلام {customer['name']} عزیز!\n\n🎬 لطفاً نوع خدمت مورد نظرتان را انتخاب کنید:",
                reply_markup=self.get_service_type_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['state'] = WAITING_SERVICE_TYPE
            return WAITING_SERVICE_TYPE
        else:
            # کاربر جدید - دریافت اطلاعات
            await query.edit_message_text(
                f"{self.get_progress_indicator('personal_info')}\n"
                "🆕 **رزرو جدید**\n\nلطفاً نام کامل خود را وارد کنید:",
                reply_markup=self.get_navigation_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['state'] = WAITING_NAME
            return WAITING_NAME

    async def start_new_reservation(self, query, context):
        """شروع رزرو جدید"""
        user_id = query.from_user.id
        
        # بررسی وجود پیش‌نویس
        draft_data, draft_state = self.load_reservation_draft(user_id)
        
        if draft_data:
            await query.edit_message_text(
                "📄 **پیش‌نویس موجود**\n\n"
                "رزرو ناتمامی از شما پیدا شد. می‌خواهید ادامه دهید یا از اول شروع کنید؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("▶️ ادامه پیش‌نویس", callback_data="continue_draft")],
                    [InlineKeyboardButton("🆕 شروع از اول", callback_data="new_reservation_fresh")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # بررسی اینکه آیا کاربر قبلاً اطلاعات داده یا نه
        customer = self.db.get_customer_by_telegram_id(user_id)
        
        if customer:
            # کاربر قبلی - انتخاب نوع خدمت
            await query.edit_message_text(
                f"{self.get_progress_indicator('service_type')}\n"
                f"👋 سلام {customer['name']} عزیز!\n\n🎬 لطفاً نوع خدمت مورد نظرتان را انتخاب کنید:",
                reply_markup=self.get_service_type_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # کاربر جدید - دریافت اطلاعات
            await query.edit_message_text(
                f"{self.get_progress_indicator('personal_info')}\n"
                "🆕 **رزرو جدید**\n\nلطفاً نام کامل خود را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_NAME
    
    # REMOVED: handle_service_selection - moved to button_callback
    async def _deprecated_handle_service_selection(self, query, context, service_type):
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
        
        # اعتبارسنجی نام
        if len(name) < 2:
            await update.message.reply_text(
                "❌ نام باید حداقل ۲ کاراکتر باشد.\n📝 مثال: علی، فاطمه",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 انصراف", callback_data="back_to_main")
                ]])
            )
            return WAITING_NAME
        
        if len(name) > 50:
            await update.message.reply_text(
                "❌ نام نمی‌تواند بیشتر از ۵۰ کاراکتر باشد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 انصراف", callback_data="back_to_main")
                ]])
            )
            return WAITING_NAME
        
        # ذخیره نام
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['name'] = name
        
        # ذخیره پیش‌نویس
        self.save_reservation_draft(user_id, WAITING_FAMILY_NAME)
        
        await update.message.reply_text(
            f"✅ نام ثبت شد: **{name}**\n\n👨‍👩‍👧‍👦 لطفاً نام خانوادگی خود را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="back_to_main")
            ]]),
            parse_mode=ParseMode.MARKDOWN
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
                f"{self.get_progress_indicator('service_type')}\n"
                f"✅ اطلاعات شما ثبت شد!\n\n🎬 حالا لطفاً نوع خدمت مورد نظرتان را انتخاب کنید:",
                reply_markup=self.get_service_type_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            context.user_data['state'] = WAITING_SERVICE_TYPE
            return WAITING_SERVICE_TYPE
            
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
            f"✅ تاریخ مراسم ثبت شد: {event_date}\n\n� لطفاً ساعت شروع مراسم را وارد کنید (مثال: ۱۸:۳۰):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        
        return WAITING_EVENT_TIME
    
    async def handle_event_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی زمان مراسم"""
        user_id = update.effective_user.id
        event_time = update.message.text.strip()
        
        # اعتبارسنجی ساده زمان
        if not ValidationUtils.validate_time(event_time):
            await update.message.reply_text(
                "❌ زمان نامعتبر است!\n\nلطفاً زمان را به فرمت صحیح وارد کنید:\n• مثال: ۱۸:۳۰ یا ۶:۳۰ عصر"
            )
            return WAITING_EVENT_TIME
        
        self.user_data[user_id]['event_time'] = event_time
        
        await update.message.reply_text(
            f"✅ زمان شروع مراسم ثبت شد: {event_time}\n\n📍 لطفاً مکان مراسم را وارد کنید:",
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
            f"✅ مکان مراسم ثبت شد: {location}\n\n⏱️ لطفاً مدت زمان مراسم را وارد کنید (مثال: ۴ ساعت):",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("۲ ساعت", callback_data="duration_2"),
                    InlineKeyboardButton("۳ ساعت", callback_data="duration_3")
                ],
                [
                    InlineKeyboardButton("۴ ساعت", callback_data="duration_4"),
                    InlineKeyboardButton("۵ ساعت", callback_data="duration_5")
                ],
                [
                    InlineKeyboardButton("۶ ساعت", callback_data="duration_6"),
                    InlineKeyboardButton("تمام روز", callback_data="duration_full")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
            ])
        )
        
        return WAITING_DURATION
    
    async def handle_duration_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی مدت زمان مراسم"""
        user_id = update.effective_user.id
        duration = update.message.text.strip()
        
        # اگر کاربر متن وارد کرده، اعتبارسنجی کن
        if len(duration) < 2:
            await update.message.reply_text("❌ لطفاً مدت زمان مراسم را وارد کنید (مثال: ۴ ساعت)")
            return WAITING_DURATION
        
        self.user_data[user_id]['duration'] = duration
        
        await update.message.reply_text(
            f"✅ مدت زمان مراسم ثبت شد: {duration}\n\n📝 آیا درخواست یا نیاز خاصی دارید؟ (اختیاری)",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_special_requests"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]
            ])
        )
        
        return WAITING_SPECIAL_REQUESTS
    
    async def handle_special_requests_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت ورودی درخواست‌های خاص"""
        user_id = update.effective_user.id
        special_requests = update.message.text.strip()
        
        self.user_data[user_id]['special_requests'] = special_requests
        
        await update.message.reply_text(
            f"✅ درخواست‌های خاص ثبت شد: {special_requests}\n\n📷 لطفاً تعداد دوربین مورد نظر را انتخاب کنید:",
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
        
        # انتخاب مدت زمان مراسم
        if data.startswith("duration_"):
            duration_value = data.split("_")[1]
            if duration_value == "full":
                duration = "تمام روز"
            else:
                duration = f"{duration_value} ساعت"
                
            self.user_data[user_id]['duration'] = duration
            
            await query.edit_message_text(
                f"✅ مدت زمان مراسم ثبت شد: {duration}\n\n📝 آیا درخواست یا نیاز خاصی دارید؟ (اختیاری)",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_special_requests"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                    ]
                ])
            )
            return WAITING_SPECIAL_REQUESTS
            
        # رد کردن درخواست‌های خاص
        elif data == "skip_special_requests":
            self.user_data[user_id]['special_requests'] = None
            
            await query.edit_message_text(
                "📷 لطفاً تعداد دوربین مورد نظر را انتخاب کنید:",
                reply_markup=self.get_number_keyboard(1, 5, "cameras")
            )
            return WAITING_CAMERAS
        
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
            
            # نمایش خلاصه اطلاعات برای تایید
            await self.show_reservation_summary(query, context, user_id)
        
        # نمایش جزئیات رزرو
        elif data.startswith("view_reservation_"):
            reservation_code = data.replace("view_reservation_", "")
            await self.show_reservation_details(query, context, reservation_code)
        
        # رد کردن ایمیل
        elif data == "skip_email":
            await self.handle_email_skip(query, context)
            
        # تایید نهایی رزرو
        elif data == "confirm_reservation":
            await self.calculate_and_show_cost(query, context, user_id)
            
        # ویرایش اطلاعات
        elif data == "edit_reservation_info":
            await query.edit_message_text(
                "⚠️ برای ویرایش اطلاعات، لطفاً رزرو جدیدی شروع کنید.\n\nاز منوی اصلی گزینه 'رزرو جدید' را انتخاب کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main")
                ]])
            )
        
        # ادامه پیش‌نویس
        elif data == "continue_draft":
            draft_data, draft_state = self.load_reservation_draft(user_id)
            if draft_data:
                self.user_data[user_id] = draft_data
                # برگشت به state مناسب
                await self.resume_from_state(query, context, user_id, draft_state)
            else:
                await query.edit_message_text("❌ پیش‌نویس یافت نشد. لطفاً رزرو جدید شروع کنید.")
        
        # شروع رزرو تازه (پاک کردن draft)
        elif data == "new_reservation_fresh":
            if user_id in self.reservation_drafts:
                del self.reservation_drafts[user_id]
            if user_id in self.user_data:
                del self.user_data[user_id]
            await self.start_fresh_reservation(query, context)
    
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
    
    async def show_reservation_summary(self, query, context, user_id):
        """نمایش خلاصه اطلاعات رزرو برای تایید"""
        user_data = self.user_data[user_id]
        
        # ایجاد متن خلاصه
        summary_text = "📋 **خلاصه اطلاعات رزرو شما:**\n\n"
        
        # اطلاعات شخصی
        summary_text += f"👤 **نام:** {user_data.get('name', '')} {user_data.get('family_name', '')}\n"
        summary_text += f"📱 **شماره تماس:** {user_data.get('phone', '')}\n"
        if user_data.get('email'):
            summary_text += f"📧 **ایمیل:** {user_data.get('email', '')}\n"
        
        # نوع خدمت
        service_name = CostCalculator.get_service_name(user_data.get('service_type', ''))
        summary_text += f"\n🎬 **نوع خدمت:** {service_name}\n"
        
        # اطلاعات خاص عروسی
        if user_data.get('service_type') == 'wedding':
            summary_text += f"💍 **نام عروس:** {user_data.get('bride_name', '')}\n"
            summary_text += f"👥 **تعداد مهمانان:** {user_data.get('guest_count', '')} نفر\n"
        
        # اطلاعات مراسم
        summary_text += f"\n📅 **تاریخ مراسم:** {user_data.get('event_date', '')}\n"
        summary_text += f"🕐 **زمان شروع:** {user_data.get('event_time', '')}\n"
        summary_text += f"📍 **مکان:** {user_data.get('location', '')}\n"
        summary_text += f"⏱️ **مدت زمان:** {user_data.get('duration', '')}\n"
        
        if user_data.get('special_requests'):
            summary_text += f"📝 **درخواست‌های خاص:** {user_data.get('special_requests', '')}\n"
        
        # مشخصات فنی
        summary_text += f"\n📷 **تعداد دوربین:** {PersianDateUtils.english_to_persian_digits(str(user_data.get('cameras', '')))}\n"
        summary_text += f"🎥 **کیفیت دوربین:** {user_data.get('camera_quality', '')}\n"
        summary_text += f"🚁 **هلی‌شات:** {'بله' if user_data.get('helishot', False) else 'خیر'}\n"
        summary_text += f"👥 **تعداد عکاس:** {PersianDateUtils.english_to_persian_digits(str(user_data.get('photographers', '')))}\n"
        
        summary_text += "\n❓ **آیا اطلاعات فوق صحیح است؟**"
        
        keyboard = [
            [InlineKeyboardButton("✅ تایید و ادامه", callback_data="confirm_reservation")],
            [InlineKeyboardButton("✏️ ویرایش", callback_data="edit_reservation_info")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            summary_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
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
                event_date=user_data.get('event_date'),
                event_time=user_data.get('event_time'),
                location=user_data.get('location'),
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
                WAITING_SERVICE_TYPE: [CallbackQueryHandler(self.button_callback)],
                WAITING_BRIDE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bride_name_input)],
                WAITING_GUEST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_guest_count_input)],
                WAITING_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_event_date_input)],
                WAITING_EVENT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_event_time_input)],
                WAITING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_location_input)],
                WAITING_DURATION: [
                    CallbackQueryHandler(self.handle_other_callbacks),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_duration_input)
                ],
                WAITING_SPECIAL_REQUESTS: [
                    CallbackQueryHandler(self.handle_other_callbacks),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_special_requests_input)
                ],
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
        
        # اضافه کردن error handler
        application.add_error_handler(self.error_handler)
        
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
