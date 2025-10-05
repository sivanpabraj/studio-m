"""
🔗 ماژول پرداخت آنلاین برای ربات استودیو ماندنی
ادغام با درگاه‌های پرداخت ایرانی (زرین‌پال، ملت، پاسارگاد)
"""

import json
import hashlib
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PaymentGateway:
    """کلاس پایه برای درگاه‌های پرداخت"""
    
    def __init__(self, merchant_id: str, sandbox: bool = False):
        self.merchant_id = merchant_id
        self.sandbox = sandbox
        
    async def create_payment(self, amount: int, description: str, 
                           callback_url: str, email: str = "", mobile: str = "") -> Dict:
        """ایجاد پرداخت جدید"""
        raise NotImplementedError
        
    async def verify_payment(self, authority: str, amount: int) -> Dict:
        """تایید پرداخت"""
        raise NotImplementedError


class ZarinpalGateway(PaymentGateway):
    """درگاه پرداخت زرین‌پال"""
    
    def __init__(self, merchant_id: str, sandbox: bool = False):
        super().__init__(merchant_id, sandbox)
        
        if sandbox:
            self.request_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
            self.verify_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
            self.start_pay_url = "https://sandbox.zarinpal.com/pg/StartPay/"
        else:
            self.request_url = "https://api.zarinpal.com/pg/v4/payment/request.json"
            self.verify_url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
            self.start_pay_url = "https://www.zarinpal.com/pg/StartPay/"
    
    async def create_payment(self, amount: int, description: str, 
                           callback_url: str, email: str = "", mobile: str = "") -> Dict:
        """ایجاد پرداخت در زرین‌پال"""
        try:
            data = {
                "merchant_id": self.merchant_id,
                "amount": amount,
                "description": description,
                "callback_url": callback_url,
                "metadata": {
                    "email": email,
                    "mobile": mobile
                }
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.request_url, data=json.dumps(data), headers=headers)
            result = response.json()
            
            if result.get('data', {}).get('code') == 100:
                authority = result['data']['authority']
                payment_url = f"{self.start_pay_url}{authority}"
                
                return {
                    'success': True,
                    'authority': authority,
                    'payment_url': payment_url,
                    'message': 'پرداخت با موفقیت ایجاد شد'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errors', {}).get('message', 'خطای نامشخص'),
                    'code': result.get('data', {}).get('code', 0)
                }
                
        except Exception as e:
            logger.error(f"خطا در ایجاد پرداخت زرین‌پال: {e}")
            return {
                'success': False,
                'error': 'خطا در اتصال به درگاه پرداخت'
            }
    
    async def verify_payment(self, authority: str, amount: int) -> Dict:
        """تایید پرداخت زرین‌پال"""
        try:
            data = {
                "merchant_id": self.merchant_id,
                "amount": amount,
                "authority": authority
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.verify_url, data=json.dumps(data), headers=headers)
            result = response.json()
            
            if result.get('data', {}).get('code') == 100:
                return {
                    'success': True,
                    'ref_id': result['data']['ref_id'],
                    'card_hash': result['data'].get('card_hash', ''),
                    'card_pan': result['data'].get('card_pan', ''),
                    'message': 'پرداخت با موفقیت تایید شد'
                }
            elif result.get('data', {}).get('code') == 101:
                return {
                    'success': True,
                    'ref_id': result['data']['ref_id'],
                    'message': 'پرداخت قبلاً تایید شده بود',
                    'already_verified': True
                }
            else:
                error_messages = {
                    -9: 'خطای اعتبارسنجی',
                    -10: 'ترمینال یافت نشد',
                    -11: 'ترمینال فعال نیست',
                    -12: 'تلاش بیش از حد',
                    -15: 'پرداخت یافت نشد',
                    -16: 'مبلغ قابل پرداخت نیست'
                }
                
                error_code = result.get('data', {}).get('code', 0)
                error_message = error_messages.get(error_code, 'پرداخت ناموفق')
                
                return {
                    'success': False,
                    'error': error_message,
                    'code': error_code
                }
                
        except Exception as e:
            logger.error(f"خطا در تایید پرداخت زرین‌پال: {e}")
            return {
                'success': False,
                'error': 'خطا در اتصال به درگاه پرداخت'
            }


class PaymentManager:
    """مدیریت پرداخت‌ها"""
    
    def __init__(self, db_manager, bot_config):
        self.db = db_manager
        self.config = bot_config
        
        # راه‌اندازی درگاه‌ها
        self.zarinpal = ZarinpalGateway(
            merchant_id=bot_config.ZARINPAL_MERCHANT_ID,
            sandbox=bot_config.PAYMENT_SANDBOX
        )
        
    def generate_payment_id(self, reservation_code: str) -> str:
        """تولید شناسه یکتا برای پرداخت"""
        timestamp = str(int(datetime.now().timestamp()))
        data = f"{reservation_code}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    async def create_payment_request(self, reservation_code: str, 
                                   gateway: str = "zarinpal") -> Dict:
        """ایجاد درخواست پرداخت"""
        try:
            # دریافت اطلاعات رزرو
            reservation = self.db.get_reservation_by_code(reservation_code)
            if not reservation:
                return {
                    'success': False,
                    'error': 'رزرو یافت نشد'
                }
            
            # محاسبه مبلغ بیعانه (30% از کل)
            total_amount = reservation['total_cost']
            deposit_amount = int(total_amount * 0.3)
            
            # تولید شناسه پرداخت
            payment_id = self.generate_payment_id(reservation_code)
            
            # آدرس بازگشت
            callback_url = f"{self.config.BOT_WEBHOOK_URL}/payment/callback/{payment_id}"
            
            # توضیحات پرداخت
            description = f"بیعانه رزرو {reservation_code} - استودیو ماندنی"
            
            # ایجاد پرداخت در درگاه
            if gateway == "zarinpal":
                payment_result = await self.zarinpal.create_payment(
                    amount=deposit_amount,
                    description=description,
                    callback_url=callback_url,
                    mobile=reservation.get('customer_phone', ''),
                    email=reservation.get('customer_email', '')
                )
            else:
                return {
                    'success': False,
                    'error': 'درگاه پرداخت پشتیبانی نمی‌شود'
                }
            
            if payment_result['success']:
                # ذخیره اطلاعات پرداخت در دیتابیس
                self.db.create_payment_record({
                    'payment_id': payment_id,
                    'reservation_code': reservation_code,
                    'gateway': gateway,
                    'authority': payment_result['authority'],
                    'amount': deposit_amount,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat()
                })
                
                return {
                    'success': True,
                    'payment_url': payment_result['payment_url'],
                    'payment_id': payment_id,
                    'amount': deposit_amount,
                    'authority': payment_result['authority']
                }
            else:
                return payment_result
                
        except Exception as e:
            logger.error(f"خطا در ایجاد درخواست پرداخت: {e}")
            return {
                'success': False,
                'error': 'خطای داخلی سرور'
            }
    
    async def verify_payment_callback(self, payment_id: str, authority: str, 
                                    status: str) -> Dict:
        """تایید پرداخت از طریق callback"""
        try:
            # دریافت اطلاعات پرداخت
            payment = self.db.get_payment_by_id(payment_id)
            if not payment:
                return {
                    'success': False,
                    'error': 'پرداخت یافت نشد'
                }
            
            if status != 'OK':
                # پرداخت لغو شده
                self.db.update_payment_status(payment_id, 'cancelled')
                return {
                    'success': False,
                    'error': 'پرداخت لغو شد',
                    'cancelled': True
                }
            
            # تایید پرداخت در درگاه
            if payment['gateway'] == 'zarinpal':
                verify_result = await self.zarinpal.verify_payment(
                    authority=authority,
                    amount=payment['amount']
                )
            else:
                return {
                    'success': False,
                    'error': 'درگاه نامشخص'
                }
            
            if verify_result['success']:
                # بروزرسانی وضعیت پرداخت
                self.db.update_payment_status(
                    payment_id, 
                    'verified',
                    ref_id=verify_result.get('ref_id', ''),
                    card_hash=verify_result.get('card_hash', '')
                )
                
                # بروزرسانی وضعیت رزرو
                self.db.update_reservation_status(
                    payment['reservation_code'],
                    'deposit_paid'
                )
                
                return {
                    'success': True,
                    'ref_id': verify_result.get('ref_id', ''),
                    'reservation_code': payment['reservation_code'],
                    'amount': payment['amount']
                }
            else:
                # پرداخت ناموفق
                self.db.update_payment_status(payment_id, 'failed')
                return verify_result
                
        except Exception as e:
            logger.error(f"خطا در تایید پرداخت: {e}")
            return {
                'success': False,
                'error': 'خطای داخلی سرور'
            }
    
    def get_payment_status_text(self, status: str) -> str:
        """دریافت متن وضعیت پرداخت"""
        status_map = {
            'pending': '⏳ در انتظار پرداخت',
            'verified': '✅ پرداخت شده',
            'failed': '❌ ناموفق',
            'cancelled': '🚫 لغو شده',
            'refunded': '↩️ بازگشت داده شده'
        }
        return status_map.get(status, '❓ نامشخص')
    
    async def refund_payment(self, payment_id: str, reason: str = "") -> Dict:
        """بازگشت پرداخت (در صورت امکان)"""
        # این بخش نیاز به پیاده‌سازی API بازگشت دارد
        # که بسته به درگاه متفاوت است
        pass


class PaymentUtils:
    """توابع کمکی پرداخت"""
    
    @staticmethod
    def format_price(amount: int) -> str:
        """فرمت کردن قیمت"""
        return f"{amount:,} تومان"
    
    @staticmethod
    def calculate_deposit(total_amount: int, percentage: int = 30) -> int:
        """محاسبه مبلغ بیعانه"""
        return int(total_amount * percentage / 100)
    
    @staticmethod
    def generate_receipt_text(payment_info: Dict) -> str:
        """تولید متن رسید"""
        return f"""
🧾 **رسید پرداخت**

📋 کد رزرو: `{payment_info['reservation_code']}`
💰 مبلغ: {PaymentUtils.format_price(payment_info['amount'])}
🔢 شماره پیگیری: `{payment_info['ref_id']}`
📅 تاریخ: {payment_info['paid_at']}
🏦 درگاه: {payment_info['gateway']}

✅ پرداخت با موفقیت انجام شد
استودیو ماندنی
        """
