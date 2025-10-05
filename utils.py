"""
🛠️ ماژول توابع کمکی ربات استودیو ماندنی
Utility functions for Mandani Studio Bot

این ماژول شامل توابع کمکی برای محاسبه هزینه، تولید PDF، مدیریت تاریخ و غیره است
"""

import random
import string
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import json
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io


class PersianDateUtils:
    """کلاس کمکی برای کار با تاریخ فارسی"""
    
    PERSIAN_MONTHS = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]
    
    PERSIAN_WEEKDAYS = [
        'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه'
    ]
    
    @staticmethod
    def persian_to_english_digits(text: str) -> str:
        """تبدیل اعداد فارسی به انگلیسی"""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        
        for persian, english in zip(persian_digits, english_digits):
            text = text.replace(persian, english)
        return text
    
    @staticmethod
    def english_to_persian_digits(text: str) -> str:
        """تبدیل اعداد انگلیسی به فارسی"""
        english_digits = '0123456789'
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        
        for english, persian in zip(english_digits, persian_digits):
            text = text.replace(english, persian)
        return text
    
    @staticmethod
    def format_persian_date(date_obj: date) -> str:
        """فرمت کردن تاریخ به شمسی (ساده)"""
        # برای سادگی، از تاریخ میلادی استفاده می‌کنیم
        # در پیاده‌سازی واقعی می‌توان از کتابخانه jdatetime استفاده کرد
        return PersianDateUtils.english_to_persian_digits(
            date_obj.strftime('%Y/%m/%d')
        )
    
    @staticmethod
    def calculate_days_until(target_date: str) -> int:
        """محاسبه روزهای باقی‌مانده تا تاریخ مشخص"""
        try:
            target = datetime.strptime(target_date, '%Y-%m-%d').date()
            today = date.today()
            return (target - today).days
        except:
            return 0


class CostCalculator:
    """کلاس محاسبه هزینه خدمات"""
    
    # نرخ‌های پایه خدمات (تومان)
    BASE_RATES = {
        'birthday': 500000,      # عکاسی تولد
        'wedding': 2000000,      # عروسی
        'engagement': 1000000,   # عقد
        'general': 300000,       # عمومی
        'other': 0              # سایر (نرخ سفارشی)
    }
    
    # هزینه‌های اضافی
    EXTRA_COSTS = {
        'extra_camera': 100000,     # دوربین اضافی
        'helishot': 200000,         # هلی‌شات
        'extra_photographer': 150000, # عکاس اضافی
        'wedding_extra_photographer': 300000  # عکاس اضافی برای عروسی
    }
    
    # مالیات
    TAX_RATE = 0.09  # 9%
    
    @classmethod
    def calculate_service_cost(cls, service_type: str, details: Dict) -> Dict:
        """
        محاسبه هزینه خدمت بر اساس جزئیات
        
        Args:
            service_type: نوع خدمت
            details: جزئیات خدمت
        
        Returns:
            Dict شامل breakdown هزینه‌ها
        """
        base_cost = cls.BASE_RATES.get(service_type.lower(), 0)
        
        # اگر نوع خدمت "سایر" است، از هزینه سفارشی استفاده کن
        if service_type.lower() == 'other' and 'custom_cost' in details:
            base_cost = details.get('custom_cost', 0)
        
        breakdown = {
            'base_service': {
                'description': f'خدمت پایه - {cls.get_service_name(service_type)}',
                'amount': base_cost
            },
            'extras': [],
            'subtotal': base_cost,
            'tax': 0,
            'discount': 0,
            'total': 0
        }
        
        # محاسبه هزینه‌های اضافی
        cameras = details.get('cameras', 2)
        if cameras > 2:  # بیش از 2 دوربین
            extra_cameras = cameras - 2
            extra_cost = extra_cameras * cls.EXTRA_COSTS['extra_camera']
            breakdown['extras'].append({
                'description': f'دوربین اضافی ({extra_cameras} عدد)',
                'amount': extra_cost
            })
            breakdown['subtotal'] += extra_cost
        
        # هلی‌شات
        if details.get('helishot', False):
            helishot_cost = cls.EXTRA_COSTS['helishot']
            breakdown['extras'].append({
                'description': 'هلی‌شات',
                'amount': helishot_cost
            })
            breakdown['subtotal'] += helishot_cost
        
        # عکاس/فیلمبردار اضافی
        photographers = details.get('photographers', 1)
        base_photographers = 2 if service_type.lower() == 'wedding' else 1
        
        if photographers > base_photographers:
            extra_photographers = photographers - base_photographers
            cost_per_photographer = (
                cls.EXTRA_COSTS['wedding_extra_photographer'] 
                if service_type.lower() == 'wedding' 
                else cls.EXTRA_COSTS['extra_photographer']
            )
            extra_cost = extra_photographers * cost_per_photographer
            breakdown['extras'].append({
                'description': f'عکاس/فیلمبردار اضافی ({extra_photographers} نفر)',
                'amount': extra_cost
            })
            breakdown['subtotal'] += extra_cost
        
        # تخفیف
        discount_percent = details.get('discount_percent', 0)
        if discount_percent > 0:
            breakdown['discount'] = breakdown['subtotal'] * (discount_percent / 100)
        
        # محاسبه مالیات
        taxable_amount = breakdown['subtotal'] - breakdown['discount']
        breakdown['tax'] = taxable_amount * cls.TAX_RATE
        
        # محاسبه کل
        breakdown['total'] = taxable_amount + breakdown['tax']
        
        return breakdown
    
    @staticmethod
    def get_service_name(service_type: str) -> str:
        """تبدیل نوع خدمت به نام فارسی"""
        names = {
            'birthday': 'عکاسی تولد',
            'wedding': 'عکاسی عروسی',
            'engagement': 'فیلمبرداری عقد',
            'general': 'عکاسی/فیلمبرداری عمومی',
            'other': 'سایر خدمات'
        }
        return names.get(service_type.lower(), 'خدمت نامشخص')
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """فرمت کردن مبلغ به فرمت تومان"""
        return PersianDateUtils.english_to_persian_digits(
            f"{amount:,.0f} تومان"
        )


class ReservationCodeGenerator:
    """تولید کد رزرو منحصربه‌فرد"""
    
    @staticmethod
    def generate_code(length: int = 6) -> str:
        """تولید کد رزرو تصادفی"""
        characters = string.ascii_uppercase + string.digits
        # حذف کاراکترهای مشکل‌ساز
        characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1')
        return ''.join(random.choices(characters, k=length))


class ValidationUtils:
    """توابع اعتبارسنجی"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """اعتبارسنجی شماره تلفن ایرانی"""
        # حذف فاصله و خط تیره
        phone = re.sub(r'[\s\-]', '', phone)
        
        # الگوهای معتبر شماره تلفن ایرانی
        patterns = [
            r'^09\d{9}$',           # موبایل: 09xxxxxxxxx
            r'^(\+98|0098)9\d{9}$', # موبایل با کد کشور
            r'^0\d{10}$',           # تلفن ثابت: 0xxxxxxxxxx
        ]
        
        return any(re.match(pattern, phone) for pattern in patterns)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """اعتبارسنجی ایمیل"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """اعتبارسنجی تاریخ (فرمت ۱۴۰۳/۰۸/۱۵)"""
        try:
            # تبدیل اعداد فارسی به انگلیسی
            persian_digits = '۰۱۲۳۴۵۶۷۸۹'
            english_digits = '0123456789'
            trans_table = str.maketrans(persian_digits, english_digits)
            date_str_eng = date_str.translate(trans_table)
            
            # بررسی فرمت کلی
            if not re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_str_eng):
                return False
            
            parts = date_str_eng.split('/')
            if len(parts) != 3:
                return False
            
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            
            # بررسی محدوده سال (1400-1410)
            if not (1400 <= year <= 1410):
                return False
            
            # بررسی محدوده ماه
            if not (1 <= month <= 12):
                return False
            
            # بررسی محدوده روز
            if not (1 <= day <= 31):
                return False
            
            # بررسی روزهای ماه (ساده)
            if month in [7, 8, 9, 10, 11] and day > 30:  # ماه‌های 30 روزه
                return False
            if month == 12 and day > 29:  # اسفند
                return False
            
            return True
        except:
            return False
    
    @staticmethod
    def validate_time(time_str: str) -> bool:
        """اعتبارسنجی زمان (فرمت ۱۸:۳۰ یا ۶ عصر)"""
        try:
            # تبدیل اعداد فارسی به انگلیسی
            persian_digits = '۰۱۲۳۴۵۶۷۸۹'
            english_digits = '0123456789'
            trans_table = str.maketrans(persian_digits, english_digits)
            time_str_eng = time_str.translate(trans_table).strip()
            
            # بررسی فرمت 24 ساعته (مثل 18:30)
            if re.match(r'^\d{1,2}:\d{2}$', time_str_eng):
                parts = time_str_eng.split(':')
                hour, minute = int(parts[0]), int(parts[1])
                return 0 <= hour <= 23 and 0 <= minute <= 59
            
            # بررسی فرمت 12 ساعته فارسی
            patterns = [
                r'^\d{1,2}\s*(صبح|ظهر|عصر|شب|بعدازظهر)$',
                r'^\d{1,2}:\d{2}\s*(صبح|ظهر|عصر|شب|بعدازظهر)$'
            ]
            
            for pattern in patterns:
                if re.match(pattern, time_str_eng):
                    return True
            
            return False
        except:
            return False
    
    @staticmethod
    def validate_persian_text(text: str, min_length: int = 2, max_length: int = 100) -> bool:
        """اعتبارسنجی متن فارسی"""
        try:
            if not text or len(text.strip()) < min_length:
                return False
            
            if len(text.strip()) > max_length:
                return False
            
            # بررسی وجود حروف فارسی یا انگلیسی
            persian_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z\s]'
            if not re.search(persian_pattern, text):
                return False
            
            return True
        except:
            return False


class PDFGenerator:
    """تولید فاکتور PDF"""
    
    def __init__(self):
        """راه‌اندازی تولید PDF"""
        self.setup_fonts()
    
    def setup_fonts(self):
        """تنظیم فونت‌های فارسی"""
        # در پیاده‌سازی واقعی، فونت فارسی را اضافه کنید
        # pdfmetrics.registerFont(TTFont('Persian', 'path/to/persian_font.ttf'))
        pass
    
    def generate_invoice_pdf(self, reservation_data: Dict, cost_breakdown: Dict) -> io.BytesIO:
        """
        تولید فاکتور PDF
        
        Args:
            reservation_data: اطلاعات رزرو
            cost_breakdown: تفکیک هزینه‌ها
        
        Returns:
            BytesIO object حاوی PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # استایل‌ها
        styles = getSampleStyleSheet()
        
        # استایل فارسی (راست‌چین)
        persian_style = ParagraphStyle(
            'Persian',
            parent=styles['Normal'],
            fontName='Helvetica',  # در پیاده‌سازی واقعی از فونت فارسی استفاده کنید
            fontSize=12,
            alignment=TA_RIGHT,
            leading=16
        )
        
        title_style = ParagraphStyle(
            'PersianTitle',
            parent=persian_style,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # محتویات فاکتور
        story = []
        
        # عنوان
        story.append(Paragraph("فاکتور خدمات استودیو ماندنی", title_style))
        story.append(Spacer(1, 20))
        
        # اطلاعات مشتری
        customer_info = f"""
        نام مشتری: {reservation_data.get('customer_name', 'نامشخص')}<br/>
        کد رزرو: {reservation_data.get('reservation_code', '')}<br/>
        نوع خدمت: {CostCalculator.get_service_name(reservation_data.get('service_type', ''))}<br/>
        تاریخ مراسم: {reservation_data.get('event_date', 'نامشخص')}<br/>
        تاریخ تحویل: {reservation_data.get('delivery_date', 'نامشخص')}
        """
        story.append(Paragraph(customer_info, persian_style))
        story.append(Spacer(1, 20))
        
        # جدول هزینه‌ها
        table_data = [
            ['مبلغ (تومان)', 'شرح خدمات']
        ]
        
        # خدمت پایه
        table_data.append([
            CostCalculator.format_currency(cost_breakdown['base_service']['amount']),
            cost_breakdown['base_service']['description']
        ])
        
        # خدمات اضافی
        for extra in cost_breakdown['extras']:
            table_data.append([
                CostCalculator.format_currency(extra['amount']),
                extra['description']
            ])
        
        # جمع فرعی
        table_data.append([
            CostCalculator.format_currency(cost_breakdown['subtotal']),
            'جمع فرعی'
        ])
        
        # تخفیف
        if cost_breakdown['discount'] > 0:
            table_data.append([
                f"-{CostCalculator.format_currency(cost_breakdown['discount'])}",
                'تخفیف'
            ])
        
        # مالیات
        table_data.append([
            CostCalculator.format_currency(cost_breakdown['tax']),
            'مالیات (%۹)'
        ])
        
        # جمع کل
        table_data.append([
            CostCalculator.format_currency(cost_breakdown['total']),
            'جمع کل'
        ])
        
        # ایجاد جدول
        table = Table(table_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # اطلاعات پرداخت
        payment_info = f"""
        مبلغ بیعانه (۵۰٪): {CostCalculator.format_currency(cost_breakdown['total'] * 0.5)}<br/>
        مبلغ باقی‌مانده: {CostCalculator.format_currency(cost_breakdown['total'] * 0.5)}<br/>
        <br/>
        شماره کارت: ۱۲۳۴-۵۶۷۸-۹۰۱۲-۳۴۵۶<br/>
        نام صاحب کارت: استودیو ماندنی
        """
        story.append(Paragraph(payment_info, persian_style))
        
        # تاریخ صدور
        issue_date = PersianDateUtils.format_persian_date(date.today())
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"تاریخ صدور: {issue_date}", persian_style))
        
        # ساخت PDF
        doc.build(story)
        buffer.seek(0)
        return buffer


class MessageFormatter:
    """کلاس فرمت کردن پیام‌ها"""
    
    @staticmethod
    def format_reservation_summary(reservation: Dict) -> str:
        """فرمت کردن خلاصه رزرو"""
        service_name = CostCalculator.get_service_name(reservation['service_type'])
        
        # محاسبه روزهای باقی‌مانده
        days_left = PersianDateUtils.calculate_days_until(reservation.get('delivery_date', ''))
        
        if reservation['booking_status'] == 'canceled':
            status_text = "این رزرو لغو شده است ❌"
        elif days_left < 0:
            status_text = "پروژه آماده تحویل است 📸"
        elif days_left == 0:
            status_text = "امروز روز تحویل است! 🎯"
        else:
            days_left_persian = PersianDateUtils.english_to_persian_digits(str(days_left))
            status_text = f"تا تحویل پروژه {days_left_persian} روز باقی مانده 🕒"
        
        event_date = reservation.get('event_date', 'نامشخص')
        if event_date and event_date != 'نامشخص':
            event_date = PersianDateUtils.english_to_persian_digits(event_date)
        
        delivery_date = reservation.get('delivery_date', 'نامشخص')
        if delivery_date and delivery_date != 'نامشخص':
            delivery_date = PersianDateUtils.english_to_persian_digits(delivery_date)
        
        return f"""
📋 **جزئیات رزرو**

🔹 کد رزرو: `{reservation['reservation_code']}`
🔹 نوع خدمت: {service_name}
🔹 نام مشتری: {reservation.get('customer_name', 'نامشخص')}
🔹 تاریخ مراسم: {event_date}
🔹 تاریخ تحویل: {delivery_date}
🔹 وضعیت: {reservation['booking_status']}
🔹 وضعیت پرداخت: {reservation['payment_status']}

{status_text}
        """.strip()
    
    @staticmethod
    def format_cost_breakdown(cost_breakdown: Dict) -> str:
        """فرمت کردن تفکیک هزینه‌ها"""
        text = "💰 **تفکیک هزینه‌ها**\n\n"
        
        # خدمت پایه
        text += f"🔹 {cost_breakdown['base_service']['description']}: "
        text += f"{CostCalculator.format_currency(cost_breakdown['base_service']['amount'])}\n"
        
        # خدمات اضافی
        for extra in cost_breakdown['extras']:
            text += f"🔹 {extra['description']}: "
            text += f"{CostCalculator.format_currency(extra['amount'])}\n"
        
        text += f"\n📊 جمع فرعی: {CostCalculator.format_currency(cost_breakdown['subtotal'])}\n"
        
        # تخفیف
        if cost_breakdown['discount'] > 0:
            text += f"🎁 تخفیف: -{CostCalculator.format_currency(cost_breakdown['discount'])}\n"
        
        # مالیات
        text += f"📋 مالیات (۹٪): {CostCalculator.format_currency(cost_breakdown['tax'])}\n"
        
        # جمع کل
        text += f"\n💵 **جمع کل: {CostCalculator.format_currency(cost_breakdown['total'])}**\n"
        
        # بیعانه
        deposit = cost_breakdown['total'] * 0.5
        text += f"💳 بیعانه مورد نیاز (۵۰٪): {CostCalculator.format_currency(deposit)}"
        
        return text
    
    @staticmethod
    def format_statistics(stats: Dict) -> str:
        """فرمت کردن آمار"""
        return f"""
📊 **آمار استودیو**

👥 تعداد مشتریان: {PersianDateUtils.english_to_persian_digits(str(stats['total_customers']))}
📋 کل رزروها: {PersianDateUtils.english_to_persian_digits(str(stats['total_reservations']))}
⏳ رزروهای در انتظار: {PersianDateUtils.english_to_persian_digits(str(stats['pending_reservations']))}
✅ رزروهای تأیید شده: {PersianDateUtils.english_to_persian_digits(str(stats['confirmed_reservations']))}

💰 **درآمد**
📈 کل درآمد: {CostCalculator.format_currency(stats['total_revenue'])}
📅 درآمد ماه جاری: {CostCalculator.format_currency(stats['monthly_revenue'])}
        """.strip()


class SmartRecommendations:
    """سیستم پیشنهادات هوشمند"""
    
    @staticmethod
    def get_service_recommendations(service_type: str) -> Dict:
        """پیشنهادات برای نوع خدمت"""
        recommendations = {
            'wedding': {
                'cameras': 3,
                'photographers': 2,
                'helishot': True,
                'duration': 8,
                'description': 'برای عروسی پیشنهاد می‌شود: ۳ دوربین، ۲ عکاس، و استفاده از هلی‌شات'
            },
            'engagement': {
                'cameras': 2,
                'photographers': 2,
                'helishot': False,
                'duration': 4,
                'description': 'برای عقد پیشنهاد می‌شود: ۲ دوربین و ۲ عکاس'
            },
            'birthday': {
                'cameras': 2,
                'photographers': 1,
                'helishot': False,
                'duration': 3,
                'description': 'برای تولد پیشنهاد می‌شود: ۲ دوربین و ۱ عکاس'
            },
            'general': {
                'cameras': 1,
                'photographers': 1,
                'helishot': False,
                'duration': 2,
                'description': 'برای مراسم عمومی پیشنهاد می‌شود: ۱ دوربین و ۱ عکاس'
            }
        }
        
        return recommendations.get(service_type.lower(), {
            'cameras': 1,
            'photographers': 1,
            'helishot': False,
            'duration': 2,
            'description': 'تنظیمات پیش‌فرض'
        })


def setup_logging():
    """تنظیم سیستم لاگ"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mandani_bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


# تنظیم logger
logger = setup_logging()
