"""
🎥 ماژول پایگاه داده ربات استودیو مندانی
Database module for Mandani Studio Bot

این ماژول شامل تمام عملیات پایگاه داده SQLite برای ربات است
"""

import sqlite3
import json
import datetime
from typing import Optional, List, Dict, Any
import logging


class DatabaseManager:
    """مدیر پایگاه داده برای ربات استودیو"""
    
    def __init__(self, db_path: str = "mandani_studio.db"):
        """
        راه‌اندازی پایگاه داده
        
        Args:
            db_path: مسیر فایل پایگاه داده
        """
        self.db_path = db_path
        self.init_database()
        
    def get_connection(self):
        """ایجاد اتصال به پایگاه داده"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # برای دسترسی آسان به ستون‌ها
        return conn
    
    def init_database(self):
        """ایجاد جداول پایگاه داده"""
        with self.get_connection() as conn:
            # جدول مشتریان
            conn.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول رزروها
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    telegram_id INTEGER NOT NULL,
                    reservation_code TEXT UNIQUE NOT NULL,
                    service_type TEXT NOT NULL,
                    service_details TEXT, -- JSON string
                    event_date DATE,
                    event_time TIME,
                    delivery_date DATE,
                    location TEXT,
                    total_cost REAL DEFAULT 0,
                    deposit_amount REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'pending', -- pending, partial, paid
                    booking_status TEXT DEFAULT 'pending', -- pending, confirmed, canceled
                    payment_method TEXT,
                    transaction_id TEXT,
                    special_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''')
            
            # جدول ادمین‌ها
            conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    added_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (added_by) REFERENCES admins(telegram_id)
                )
            ''')
            
            # جدول لاگ‌ها
            conn.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول نرخ محدودیت
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, action_type)
                )
            ''')
            
            # ایندکس‌گذاری برای عملکرد بهتر
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reservations_telegram_id ON reservations(telegram_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reservations_code ON reservations(reservation_code)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customers_telegram_id ON customers(telegram_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_user_action ON rate_limits(user_id, action_type)')
            
            conn.commit()

    def add_customer(self, telegram_id: int, name: str, phone: str, email: str = None) -> int:
        """
        افزودن مشتری جدید
        
        Args:
            telegram_id: شناسه تلگرام کاربر
            name: نام مشتری
            phone: شماره تلفن
            email: ایمیل (اختیاری)
        
        Returns:
            شناسه مشتری در پایگاه داده
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO customers (telegram_id, name, phone, email)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, name, phone, email))
            conn.commit()
            return cursor.lastrowid

    def get_customer_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """جستجوی مشتری بر اساس شناسه تلگرام"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM customers WHERE telegram_id = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (telegram_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def create_reservation(self, telegram_id: int, reservation_code: str, 
                          service_type: str, service_details: Dict,
                          event_date: str = None, event_time: str = None,
                          delivery_date: str = None, location: str = None,
                          total_cost: float = 0) -> int:
        """
        ایجاد رزرو جدید
        
        Args:
            telegram_id: شناسه تلگرام کاربر
            reservation_code: کد رزرو منحصربه‌فرد
            service_type: نوع خدمت
            service_details: جزئیات خدمت (dict)
            event_date: تاریخ مراسم
            event_time: زمان مراسم
            delivery_date: تاریخ تحویل
            location: مکان مراسم
            total_cost: هزینه کل
        
        Returns:
            شناسه رزرو در پایگاه داده
        """
        customer = self.get_customer_by_telegram_id(telegram_id)
        customer_id = customer['id'] if customer else None
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO reservations (
                    customer_id, telegram_id, reservation_code, service_type,
                    service_details, event_date, event_time, delivery_date,
                    location, total_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, telegram_id, reservation_code, service_type,
                  json.dumps(service_details, ensure_ascii=False), 
                  event_date, event_time, delivery_date, location, total_cost))
            conn.commit()
            return cursor.lastrowid

    def get_reservation_by_code(self, reservation_code: str) -> Optional[Dict]:
        """جستجوی رزرو بر اساس کد رزرو"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT r.*, c.name as customer_name, c.phone as customer_phone
                FROM reservations r
                LEFT JOIN customers c ON r.customer_id = c.id
                WHERE r.reservation_code = ?
            ''', (reservation_code,))
            result = cursor.fetchone()
            if result:
                result = dict(result)
                if result['service_details']:
                    result['service_details'] = json.loads(result['service_details'])
                return result
            return None

    def get_user_reservations(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """دریافت رزروهای کاربر"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT r.*, c.name as customer_name
                FROM reservations r
                LEFT JOIN customers c ON r.customer_id = c.id
                WHERE r.telegram_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
            ''', (telegram_id, limit))
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result['service_details']:
                    result['service_details'] = json.loads(result['service_details'])
                results.append(result)
            return results

    def search_reservations(self, query: str, search_type: str = 'all') -> List[Dict]:
        """
        جستجوی رزروها
        
        Args:
            query: متن جستجو
            search_type: نوع جستجو (code, name, phone, all)
        """
        with self.get_connection() as conn:
            if search_type == 'code':
                sql = '''
                    SELECT r.*, c.name as customer_name, c.phone as customer_phone
                    FROM reservations r
                    LEFT JOIN customers c ON r.customer_id = c.id
                    WHERE r.reservation_code LIKE ?
                '''
                params = (f'%{query}%',)
            elif search_type == 'name':
                sql = '''
                    SELECT r.*, c.name as customer_name, c.phone as customer_phone
                    FROM reservations r
                    LEFT JOIN customers c ON r.customer_id = c.id
                    WHERE c.name LIKE ?
                '''
                params = (f'%{query}%',)
            elif search_type == 'phone':
                sql = '''
                    SELECT r.*, c.name as customer_name, c.phone as customer_phone
                    FROM reservations r
                    LEFT JOIN customers c ON r.customer_id = c.id
                    WHERE c.phone LIKE ?
                '''
                params = (f'%{query}%',)
            else:  # all
                sql = '''
                    SELECT r.*, c.name as customer_name, c.phone as customer_phone
                    FROM reservations r
                    LEFT JOIN customers c ON r.customer_id = c.id
                    WHERE r.reservation_code LIKE ? OR c.name LIKE ? OR c.phone LIKE ?
                '''
                params = (f'%{query}%', f'%{query}%', f'%{query}%')
            
            cursor = conn.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result['service_details']:
                    result['service_details'] = json.loads(result['service_details'])
                results.append(result)
            return results

    def update_reservation_status(self, reservation_code: str, booking_status: str = None, 
                                payment_status: str = None) -> bool:
        """به‌روزرسانی وضعیت رزرو"""
        updates = []
        params = []
        
        if booking_status:
            updates.append("booking_status = ?")
            params.append(booking_status)
        
        if payment_status:
            updates.append("payment_status = ?")
            params.append(payment_status)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(reservation_code)
        
        sql = f"UPDATE reservations SET {', '.join(updates)} WHERE reservation_code = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0

    def update_payment_info(self, reservation_code: str, payment_method: str,
                           transaction_id: str = None, deposit_amount: float = None) -> bool:
        """به‌روزرسانی اطلاعات پرداخت"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE reservations 
                SET payment_method = ?, transaction_id = ?, deposit_amount = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE reservation_code = ?
            ''', (payment_method, transaction_id, deposit_amount, reservation_code))
            conn.commit()
            return cursor.rowcount > 0

    def is_admin(self, telegram_id: int) -> bool:
        """بررسی ادمین بودن کاربر"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT 1 FROM admins WHERE telegram_id = ?', (telegram_id,))
            return cursor.fetchone() is not None

    def add_admin(self, telegram_id: int, username: str = None, 
                  full_name: str = None, added_by: int = None) -> bool:
        """افزودن ادمین جدید"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO admins (telegram_id, username, full_name, added_by)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, username, full_name, added_by))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # کاربر قبلاً ادمین است

    def get_all_admins(self) -> List[Dict]:
        """دریافت لیست تمام ادمین‌ها"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM admins ORDER BY created_at')
            return [dict(row) for row in cursor.fetchall()]

    def log_action(self, user_id: int, action: str, details: str = None):
        """ثبت لاگ فعالیت"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO logs (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))
            conn.commit()

    def check_rate_limit(self, user_id: int, action_type: str, limit: int, window_minutes: int = 1) -> bool:
        """
        بررسی محدودیت نرخ درخواست
        
        Args:
            user_id: شناسه کاربر
            action_type: نوع عمل
            limit: حد مجاز درخواست
            window_minutes: بازه زمانی (دقیقه)
        
        Returns:
            True اگر در حد مجاز باشد
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=window_minutes)
        
        with self.get_connection() as conn:
            # حذف رکوردهای قدیمی
            conn.execute('''
                DELETE FROM rate_limits 
                WHERE window_start < ? AND user_id = ? AND action_type = ?
            ''', (cutoff_time, user_id, action_type))
            
            # بررسی تعداد درخواست‌های جاری
            cursor = conn.execute('''
                SELECT count FROM rate_limits 
                WHERE user_id = ? AND action_type = ?
            ''', (user_id, action_type))
            
            result = cursor.fetchone()
            
            if result is None:
                # اولین درخواست
                conn.execute('''
                    INSERT INTO rate_limits (user_id, action_type, count)
                    VALUES (?, ?, 1)
                ''', (user_id, action_type))
                conn.commit()
                return True
            elif result['count'] < limit:
                # افزایش تعداد درخواست
                conn.execute('''
                    UPDATE rate_limits 
                    SET count = count + 1 
                    WHERE user_id = ? AND action_type = ?
                ''', (user_id, action_type))
                conn.commit()
                return True
            else:
                # بیش از حد مجاز
                return False

    def get_statistics(self) -> Dict:
        """دریافت آمار کلی"""
        with self.get_connection() as conn:
            stats = {}
            
            # تعداد کل مشتریان
            cursor = conn.execute('SELECT COUNT(*) as count FROM customers')
            stats['total_customers'] = cursor.fetchone()['count']
            
            # تعداد کل رزروها
            cursor = conn.execute('SELECT COUNT(*) as count FROM reservations')
            stats['total_reservations'] = cursor.fetchone()['count']
            
            # رزروهای در انتظار
            cursor = conn.execute("SELECT COUNT(*) as count FROM reservations WHERE booking_status = 'pending'")
            stats['pending_reservations'] = cursor.fetchone()['count']
            
            # رزروهای تأیید شده
            cursor = conn.execute("SELECT COUNT(*) as count FROM reservations WHERE booking_status = 'confirmed'")
            stats['confirmed_reservations'] = cursor.fetchone()['count']
            
            # درآمد کل
            cursor = conn.execute("SELECT SUM(total_cost) as total FROM reservations WHERE payment_status = 'paid'")
            result = cursor.fetchone()
            stats['total_revenue'] = result['total'] if result['total'] else 0
            
            # درآمد ماه جاری
            current_month = datetime.datetime.now().strftime('%Y-%m')
            cursor = conn.execute('''
                SELECT SUM(total_cost) as total FROM reservations 
                WHERE payment_status = 'paid' AND created_at LIKE ?
            ''', (f'{current_month}%',))
            result = cursor.fetchone()
            stats['monthly_revenue'] = result['total'] if result['total'] else 0
            
            return stats

    def backup_data(self) -> Dict:
        """پشتیبان‌گیری از داده‌ها به فرمت JSON"""
        with self.get_connection() as conn:
            backup = {}
            
            # مشتریان
            cursor = conn.execute('SELECT * FROM customers')
            backup['customers'] = [dict(row) for row in cursor.fetchall()]
            
            # رزروها
            cursor = conn.execute('SELECT * FROM reservations')
            reservations = []
            for row in cursor.fetchall():
                reservation = dict(row)
                if reservation['service_details']:
                    reservation['service_details'] = json.loads(reservation['service_details'])
                reservations.append(reservation)
            backup['reservations'] = reservations
            
            # ادمین‌ها
            cursor = conn.execute('SELECT * FROM admins')
            backup['admins'] = [dict(row) for row in cursor.fetchall()]
            
            # اضافه کردن تاریخ پشتیبان‌گیری
            backup['backup_date'] = datetime.datetime.now().isoformat()
            
            return backup

    def get_reservations_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """دریافت رزروهای بازه زمانی مشخص"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT r.*, c.name as customer_name, c.phone as customer_phone
                FROM reservations r
                LEFT JOIN customers c ON r.customer_id = c.id
                WHERE r.event_date BETWEEN ? AND ?
                ORDER BY r.event_date, r.event_time
            ''', (start_date, end_date))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result['service_details']:
                    result['service_details'] = json.loads(result['service_details'])
                results.append(result)
            return results

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict]:
        """دریافت مراسم‌های آتی"""
        from datetime import date, timedelta
        
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        return self.get_reservations_by_date_range(
            today.strftime('%Y-%m-%d'),
            future_date.strftime('%Y-%m-%d')
        )
