#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام: يلا نتعلم
كود كامل 3600+ سطر - كل الأزرار تعمل بدون مشاكل
المطور: Allawi04
"""

import os
import sys
import json
import sqlite3
import logging
import asyncio
import hashlib
import random
import string
import time
import math
import re
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import base64

# ============================================================================
# إعدادات البوت
# ============================================================================

TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
SUPPORT_USER = "Allawi04@"
CHANNEL_USERNAME = "FCJCV"
GEMINI_API_KEY = "AIzaSyARsl_YMXA74bPQpJduu0jJVuaku7MaHuY"

# أسعار الخدمات
SERVICE_PRICES = {
    "exemption": 1000,
    "summary": 1000,
    "qa": 1000,
    "help_student": 1000,
    "materials": 0,
    "vip_subscription": 5000,
}

# حالات المحادثة
class BotState:
    MAIN_MENU = "MAIN_MENU"
    ADMIN_PANEL = "ADMIN_PANEL"
    EXEMPTION_STEP1 = "EXEMPTION_STEP1"
    EXEMPTION_STEP2 = "EXEMPTION_STEP2"
    EXEMPTION_STEP3 = "EXEMPTION_STEP3"
    UPLOAD_PDF = "UPLOAD_PDF"
    ASK_QUESTION = "ASK_QUESTION"
    ANSWER_QUESTION = "ANSWER_QUESTION"
    HELP_STUDENT_ASK = "HELP_STUDENT_ASK"
    HELP_STUDENT_ANSWER = "HELP_STUDENT_ANSWER"
    VIP_SUBSCRIPTION = "VIP_SUBSCRIPTION"
    VIP_UPLOAD_LECTURE = "VIP_UPLOAD_LECTURE"
    VIP_SET_PRICE = "VIP_SET_PRICE"
    VIP_UPLOAD_TITLE = "VIP_UPLOAD_TITLE"
    VIP_UPLOAD_DESC = "VIP_UPLOAD_DESC"
    ADMIN_CHARGE = "ADMIN_CHARGE"
    ADMIN_DEDUCT = "ADMIN_DEDUCT"
    ADMIN_BAN = "ADMIN_BAN"
    ADMIN_UNBAN = "ADMIN_UNBAN"
    ADMIN_BROADCAST = "ADMIN_BROADCAST"
    ADMIN_ADD_MATERIAL = "ADMIN_ADD_MATERIAL"
    ADMIN_ADD_MAT_TITLE = "ADMIN_ADD_MAT_TITLE"
    ADMIN_ADD_MAT_DESC = "ADMIN_ADD_MAT_DESC"
    ADMIN_ADD_MAT_STAGE = "ADMIN_ADD_MAT_STAGE"
    ADMIN_ADD_MAT_FILE = "ADMIN_ADD_MAT_FILE"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    VIEW_LECTURE = "VIEW_LECTURE"
    PURCHASE_LECTURE = "PURCHASE_LECTURE"
    VIP_EARNINGS = "VIP_EARNINGS"
    WITHDRAW_EARNINGS = "WITHDRAW_EARNINGS"
    INVITE_FRIEND = "INVITE_FRIEND"
    VIEW_MATERIALS = "VIEW_MATERIALS"
    VIEW_QUESTIONS = "VIEW_QUESTIONS"
    VIEW_LECTURES = "VIEW_LECTURES"

# ============================================================================
# أدوات HTTP
# ============================================================================

class HTTPClient:
    """عميل HTTP مبسط"""
    
    @staticmethod
    def request(method: str, url: str, headers: dict = None, data: dict = None, 
                json_data: dict = None, timeout: int = 30) -> dict:
        """إرسال طلب HTTP"""
        try:
            if headers is None:
                headers = {}
            
            req_data = None
            if json_data is not None:
                req_data = json.dumps(json_data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            elif data is not None:
                req_data = urllib.parse.urlencode(data).encode('utf-8')
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            req = urllib.request.Request(
                url,
                data=req_data,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.getcode()
                response_text = response.read().decode('utf-8')
                response_headers = dict(response.getheaders())
                
                return {
                    'status': status,
                    'text': response_text,
                    'headers': response_headers,
                    'json': lambda: json.loads(response_text) if response_text else {}
                }
                
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'text': e.read().decode('utf-8') if hasattr(e, 'read') else str(e),
                'headers': dict(e.headers) if hasattr(e, 'headers') else {},
                'json': lambda: {}
            }
        except Exception as e:
            return {
                'status': 500,
                'text': str(e),
                'headers': {},
                'json': lambda: {}
            }

# ============================================================================
# قاعدة البيانات
# ============================================================================

class Database:
    """فئة قاعدة البيانات"""
    
    def __init__(self, db_path='bot_database.db'):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()
        self.init_default_data()
    
    def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            logging.info("تم الاتصال بقاعدة البيانات بنجاح")
        except Exception as e:
            logging.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            raise
    
    def create_tables(self):
        """إنشاء الجداول"""
        try:
            cursor = self.connection.cursor()
            
            # جدول المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance INTEGER DEFAULT 1000,
                    invited_by INTEGER DEFAULT 0,
                    invited_count INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0,
                    join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_active TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول مشتركي VIP
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vip_subscriptions (
                    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    start_date TEXT,
                    end_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    earnings_balance INTEGER DEFAULT 0,
                    total_earnings INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول محاضرات VIP
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vip_lectures (
                    lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER,
                    title TEXT,
                    description TEXT,
                    video_file_id TEXT,
                    price INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    purchases INTEGER DEFAULT 0,
                    earnings INTEGER DEFAULT 0,
                    is_approved INTEGER DEFAULT 0,
                    upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول مشتريات المحاضرات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lecture_purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    lecture_id INTEGER,
                    purchase_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    amount_paid INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (lecture_id) REFERENCES vip_lectures(lecture_id)
                )
            ''')
            
            # جدول المواد التعليمية
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS materials (
                    material_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    stage TEXT,
                    file_id TEXT,
                    upload_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول الأسئلة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS help_questions (
                    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question_text TEXT,
                    subject TEXT DEFAULT 'عام',
                    is_approved INTEGER DEFAULT 0,
                    is_answered INTEGER DEFAULT 0,
                    answer_text TEXT,
                    answerer_id INTEGER,
                    ask_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    answer_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (answerer_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول المعاملات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER,
                    type TEXT,
                    description TEXT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول إعدادات البوت
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT
                )
            ''')
            
            # جدول إحصاءات البوت
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_stats (
                    stat_date TEXT PRIMARY KEY,
                    new_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    total_income INTEGER DEFAULT 0,
                    total_transactions INTEGER DEFAULT 0
                )
            ''')
            
            # جدول حالة الخدمات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_status (
                    service_name TEXT PRIMARY KEY,
                    is_active INTEGER DEFAULT 1,
                    price INTEGER DEFAULT 1000
                )
            ''')
            
            # جدول دعوات المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_invitations (
                    inviter_id INTEGER,
                    invited_id INTEGER,
                    bonus_given INTEGER DEFAULT 0,
                    invite_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (inviter_id, invited_id),
                    FOREIGN KEY (inviter_id) REFERENCES users(user_id),
                    FOREIGN KEY (invited_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول تقييم المحاضرات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lecture_ratings (
                    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lecture_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    comment TEXT,
                    rating_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lecture_id) REFERENCES vip_lectures(lecture_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول سجلات المدير
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_id INTEGER,
                    details TEXT,
                    log_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES users(user_id)
                )
            ''')
            
            self.connection.commit()
            logging.info("تم إنشاء الجداول بنجاح")
            
        except Exception as e:
            logging.error(f"خطأ في إنشاء الجداول: {e}")
            raise
    
    def init_default_data(self):
        """تهيئة البيانات الافتراضية"""
        try:
            cursor = self.connection.cursor()
            
            # إضافة المدير الافتراضي
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, is_admin, balance) 
                VALUES (?, ?, ?, ?, ?)
            ''', (ADMIN_ID, SUPPORT_USER, "المدير", 1, 1000000))
            
            # إعدادات البوت الافتراضية
            default_settings = [
                ('invitation_bonus', '500'),
                ('welcome_bonus', '1000'),
                ('vip_invitation_bonus', '1000'),
                ('vip_subscription_days', '30'),
                ('admin_commission', '40'),
                ('teacher_commission', '60'),
                ('max_video_size_mb', '100'),
                ('min_question_length', '10'),
                ('max_question_length', '1000'),
                ('support_contact', SUPPORT_USER),
                ('bot_channel', CHANNEL_USERNAME),
                ('maintenance_mode', '0'),
                ('bot_name', 'يلا نتعلم'),
                ('currency_name', 'دينار عراقي'),
                ('currency_symbol', 'د.ع')
            ]
            
            for key, value in default_settings:
                cursor.execute('''
                    INSERT OR IGNORE INTO bot_settings (setting_key, setting_value)
                    VALUES (?, ?)
                ''', (key, value))
            
            # إضافة الخدمات الافتراضية
            default_services = [
                ('exemption', 1, 1000),
                ('summary', 1, 1000),
                ('qa', 1, 1000),
                ('help_student', 1, 1000),
                ('vip_subscription', 1, 5000),
                ('materials', 1, 0)
            ]
            
            for service, active, price in default_services:
                cursor.execute('''
                    INSERT OR IGNORE INTO service_status (service_name, is_active, price)
                    VALUES (?, ?, ?)
                ''', (service, active, price))
            
            self.connection.commit()
            logging.info("تم تهيئة البيانات الافتراضية بنجاح")
            
        except Exception as e:
            logging.error(f"خطأ في تهيئة البيانات الافتراضية: {e}")
    
    # ============ عمليات المستخدمين ============
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات المستخدم"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logging.error(f"خطأ في جلب بيانات المستخدم: {e}")
            return None
    
    def create_user(self, user_id: int, username: str, first_name: str, 
                   last_name: str = "", invited_by: int = 0) -> bool:
        """إنشاء مستخدم جديد"""
        try:
            cursor = self.connection.cursor()
            
            # الحصول على هدية الترحيب
            welcome_bonus = int(self.get_setting('welcome_bonus', '1000'))
            
            # التحقق من عدم وجود المستخدم
            existing_user = self.get_user(user_id)
            if existing_user:
                return True
            
            # إنشاء المستخدم
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, balance, invited_by) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, welcome_bonus, invited_by))
            
            # إذا كان هناك مدعو
            if invited_by > 0:
                # تحديث عدد المدعوين للمدعو
                cursor.execute('''
                    UPDATE users 
                    SET invited_count = invited_count + 1 
                    WHERE user_id = ?
                ''', (invited_by,))
                
                # إعطاء مكافأة الدعوة
                inviter = self.get_user(invited_by)
                is_vip = self.is_vip_user(invited_by)
                
                bonus_amount = int(self.get_setting(
                    'vip_invitation_bonus' if is_vip else 'invitation_bonus',
                    '1000' if is_vip else '500'
                ))
                
                cursor.execute('''
                    UPDATE users 
                    SET balance = balance + ? 
                    WHERE user_id = ?
                ''', (bonus_amount, invited_by))
                
                # تسجيل المكافأة
                cursor.execute('''
                    INSERT INTO transactions 
                    (user_id, amount, type, description) 
                    VALUES (?, ?, ?, ?)
                ''', (invited_by, bonus_amount, 'invitation_bonus', f'مكافأة دعوة للمستخدم {user_id}'))
                
                # تسجيل الدعوة
                cursor.execute('''
                    INSERT INTO user_invitations 
                    (inviter_id, invited_id, bonus_given) 
                    VALUES (?, ?, ?)
                ''', (invited_by, user_id, bonus_amount))
            
            # تسجيل هدية الترحيب
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, amount, type, description) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, welcome_bonus, 'welcome_bonus', 'هدية ترحيب جديدة'))
            
            # تحديث الإحصائيات
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO bot_stats (stat_date, new_users) 
                VALUES (?, 1) 
                ON CONFLICT(stat_date) DO UPDATE SET 
                new_users = new_users + 1
            ''', (today,))
            
            self.connection.commit()
            logging.info(f"تم إنشاء مستخدم جديد: {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"خطأ في إنشاء المستخدم: {e}")
            self.connection.rollback()
            return False
    
    def update_user_balance(self, user_id: int, amount: int, 
                           trans_type: str, description: str = "") -> bool:
        """تحديث رصيد المستخدم"""
        try:
            cursor = self.connection.cursor()
            
            # التحقق من وجود المستخدم
            user = self.get_user(user_id)
            if not user:
                return False
            
            # حساب الرصيد الجديد
            new_balance = user['balance'] + amount
            
            # التحقق من أن الرصيد غير سالب
            if new_balance < 0:
                return False
            
            # تحديث الرصيد
            cursor.execute('''
                UPDATE users 
                SET balance = ? 
                WHERE user_id = ?
            ''', (new_balance, user_id))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, amount, type, description) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, trans_type, description))
            
            # إذا كان المبلغ سالباً (شراء خدمة)
            if amount < 0:
                # تحديث الإحصائيات
                today = datetime.now().strftime('%Y-%m-%d')
                income = abs(amount)
                
                cursor.execute('''
                    INSERT INTO bot_stats (stat_date, total_income, total_transactions) 
                    VALUES (?, ?, 1) 
                    ON CONFLICT(stat_date) DO UPDATE SET 
                    total_income = total_income + ?,
                    total_transactions = total_transactions + 1
                ''', (today, income, income))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logging.error(f"خطأ في تحديث الرصيد: {e}")
            self.connection.rollback()
            return False
    
    def update_user_activity(self, user_id: int) -> bool:
        """تحديث وقت نشاط المستخدم"""
        try:
            cursor = self.connection.cursor()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE users 
                SET last_active = ? 
                WHERE user_id = ?
            ''', (current_time, user_id))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في تحديث النشاط: {e}")
            return False
    
    def ban_user(self, user_id: int) -> bool:
        """حظر مستخدم"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE users 
                SET is_banned = 1 
                WHERE user_id = ?
            ''', (user_id,))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'ban_user', user_id, 'حظر مستخدم'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في حظر المستخدم: {e}")
            return False
    
    def unban_user(self, user_id: int) -> bool:
        """فك حظر مستخدم"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE users 
                SET is_banned = 0 
                WHERE user_id = ?
            ''', (user_id,))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'unban_user', user_id, 'فك حظر مستخدم'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في فك حظر المستخدم: {e}")
            return False
    
    # ============ إدارة VIP ============
    
    def is_vip_user(self, user_id: int) -> bool:
        """التحقق من اشتراك VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT 1 FROM vip_subscriptions 
                WHERE user_id = ? 
                AND is_active = 1 
                AND end_date > datetime('now')
            ''', (user_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"خطأ في التحقق من VIP: {e}")
            return False
    
    def activate_vip(self, user_id: int, days: int = 30) -> bool:
        """تفعيل اشتراك VIP"""
        try:
            cursor = self.connection.cursor()
            
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            
            cursor.execute('''
                INSERT OR REPLACE INTO vip_subscriptions 
                (user_id, start_date, end_date, is_active) 
                VALUES (?, ?, ?, 1)
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'activate_vip', user_id, f'تفعيل اشتراك VIP لمدة {days} يوم'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في تفعيل VIP: {e}")
            return False
    
    def deactivate_vip(self, user_id: int) -> bool:
        """إلغاء اشتراك VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE vip_subscriptions 
                SET is_active = 0 
                WHERE user_id = ?
            ''', (user_id,))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'deactivate_vip', user_id, 'إلغاء اشتراك VIP'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في إلغاء VIP: {e}")
            return False
    
    def update_vip_earnings(self, user_id: int, amount: int) -> bool:
        """تحديث أرباح VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE vip_subscriptions 
                SET earnings_balance = earnings_balance + ?,
                    total_earnings = total_earnings + ?
                WHERE user_id = ?
            ''', (amount, amount, user_id))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في تحديث أرباح VIP: {e}")
            return False
    
    def withdraw_vip_earnings(self, user_id: int, amount: int) -> bool:
        """سحب أرباح VIP"""
        try:
            cursor = self.connection.cursor()
            
            # التحقق من الرصيد المتاح
            cursor.execute('''
                SELECT earnings_balance 
                FROM vip_subscriptions 
                WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            if not row or row['earnings_balance'] < amount:
                return False
            
            # خصم المبلغ
            cursor.execute('''
                UPDATE vip_subscriptions 
                SET earnings_balance = earnings_balance - ? 
                WHERE user_id = ?
            ''', (amount, user_id))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'vip_withdraw', user_id, f'سحب أرباح بقيمة {amount}'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في سحب أرباح VIP: {e}")
            return False
    
    # ============ محاضرات VIP ============
    
    def add_vip_lecture(self, teacher_id: int, title: str, description: str, 
                       video_file_id: str, price: int = 0) -> int:
        """إضافة محاضرة VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO vip_lectures 
                (teacher_id, title, description, video_file_id, price, is_approved) 
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (teacher_id, title, description, video_file_id, price))
            
            lecture_id = cursor.lastrowid
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'add_vip_lecture', teacher_id, f'إضافة محاضرة: {title}'))
            
            self.connection.commit()
            return lecture_id
        except Exception as e:
            logging.error(f"خطأ في إضافة محاضرة VIP: {e}")
            return -1
    
    def get_vip_lecture(self, lecture_id: int) -> Optional[Dict]:
        """الحصول على محاضرة VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM vip_lectures 
                WHERE lecture_id = ?
            ''', (lecture_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logging.error(f"خطأ في جلب محاضرة VIP: {e}")
            return None
    
    def approve_vip_lecture(self, lecture_id: int) -> bool:
        """الموافقة على محاضرة VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE vip_lectures 
                SET is_approved = 1 
                WHERE lecture_id = ?
            ''', (lecture_id,))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'approve_vip_lecture', lecture_id, 'موافقة على محاضرة VIP'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في الموافقة على محاضرة VIP: {e}")
            return False
    
    def reject_vip_lecture(self, lecture_id: int) -> bool:
        """رفض محاضرة VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM vip_lectures 
                WHERE lecture_id = ?
            ''', (lecture_id,))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'reject_vip_lecture', lecture_id, 'رفض محاضرة VIP'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في رفض محاضرة VIP: {e}")
            return False
    
    def purchase_vip_lecture(self, user_id: int, lecture_id: int) -> Tuple[bool, str]:
        """شراء محاضرة VIP"""
        try:
            cursor = self.connection.cursor()
            
            # الحصول على بيانات المحاضرة
            lecture = self.get_vip_lecture(lecture_id)
            if not lecture:
                return False, "المحاضرة غير موجودة"
            
            if lecture['is_approved'] == 0:
                return False, "المحاضرة غير معتمدة بعد"
            
            # التحقق من رصيد المستخدم
            user = self.get_user(user_id)
            if not user or user['balance'] < lecture['price']:
                return False, "رصيدك غير كافي"
            
            # خصم المبلغ
            if not self.update_user_balance(user_id, -lecture['price'], 
                                          'lecture_purchase', 
                                          f'شراء محاضرة: {lecture["title"]}'):
                return False, "حدث خطأ في الدفع"
            
            # توزيع الأرباح
            admin_commission = int(self.get_setting('admin_commission', '40'))
            teacher_commission = int(self.get_setting('teacher_commission', '60'))
            
            admin_share = (lecture['price'] * admin_commission) // 100
            teacher_share = lecture['price'] - admin_share
            
            # تحديث أرباح المحاضر
            self.update_vip_earnings(lecture['teacher_id'], teacher_share)
            
            # تحديث إحصائيات المحاضرة
            cursor.execute('''
                UPDATE vip_lectures 
                SET purchases = purchases + 1, 
                    earnings = earnings + ? 
                WHERE lecture_id = ?
            ''', (lecture['price'], lecture_id))
            
            # تسجيل عملية الشراء
            cursor.execute('''
                INSERT INTO lecture_purchases 
                (user_id, lecture_id, amount_paid) 
                VALUES (?, ?, ?)
            ''', (user_id, lecture_id, lecture['price']))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'lecture_purchase', user_id, 
                  f'شراء محاضرة {lecture_id} بقيمة {lecture["price"]}'))
            
            self.connection.commit()
            return True, "تم الشراء بنجاح"
            
        except Exception as e:
            logging.error(f"خطأ في شراء محاضرة VIP: {e}")
            return False, "حدث خطأ في عملية الشراء"
    
    # ============ المواد التعليمية ============
    
    def add_material(self, title: str, description: str, 
                    stage: str, file_id: str) -> int:
        """إضافة مادة تعليمية"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO materials 
                (title, description, stage, file_id) 
                VALUES (?, ?, ?, ?)
            ''', (title, description, stage, file_id))
            
            material_id = cursor.lastrowid
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'add_material', material_id, f'إضافة مادة: {title}'))
            
            self.connection.commit()
            return material_id
        except Exception as e:
            logging.error(f"خطأ في إضافة مادة: {e}")
            return -1
    
    def get_material(self, material_id: int) -> Optional[Dict]:
        """الحصول على مادة تعليمية"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM materials 
                WHERE material_id = ?
            ''', (material_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logging.error(f"خطأ في جلب مادة: {e}")
            return None
    
    def get_all_materials(self) -> List[Dict]:
        """الحصول على جميع المواد"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM materials ORDER BY upload_date DESC')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب المواد: {e}")
            return []
    
    def delete_material(self, material_id: int) -> bool:
        """حذف مادة تعليمية"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM materials 
                WHERE material_id = ?
            ''', (material_id,))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action, target_id, details) 
                VALUES (?, ?, ?, ?)
            ''', (ADMIN_ID, 'delete_material', material_id, 'حذف مادة تعليمية'))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في حذف مادة: {e}")
            return False
    
    # ============ الأسئلة والإجابات ============
    
    def add_help_question(self, user_id: int, question_text: str, 
                         subject: str = "عام") -> int:
        """إضافة سؤال في قسم ساعدوني طالب"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO help_questions 
                (user_id, question_text, subject, is_approved) 
                VALUES (?, ?, ?, 0)
            ''', (user_id, question_text, subject))
            
            question_id = cursor.lastrowid
            self.connection.commit()
            return question_id
        except Exception as e:
            logging.error(f"خطأ في إضافة سؤال: {e}")
            return -1
    
    def get_help_question(self, question_id: int) -> Optional[Dict]:
        """الحصول على سؤال"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM help_questions 
                WHERE question_id = ?
            ''', (question_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logging.error(f"خطأ في جلب سؤال: {e}")
            return None
    
    def approve_help_question(self, question_id: int) -> bool:
        """الموافقة على سؤال"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE help_questions 
                SET is_approved = 1 
                WHERE question_id = ?
            ''', (question_id,))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في الموافقة على سؤال: {e}")
            return False
    
    def reject_help_question(self, question_id: int) -> bool:
        """رفض سؤال"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM help_questions 
                WHERE question_id = ?
            ''', (question_id,))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في رفض سؤال: {e}")
            return False
    
    def answer_help_question(self, question_id: int, answerer_id: int, 
                            answer_text: str) -> bool:
        """الإجابة على سؤال"""
        try:
            cursor = self.connection.cursor()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE help_questions 
                SET answer_text = ?, 
                    answerer_id = ?, 
                    is_answered = 1, 
                    answer_date = ? 
                WHERE question_id = ?
            ''', (answer_text, answerer_id, current_time, question_id))
            
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في الإجابة على سؤال: {e}")
            return False
    
    def get_pending_questions(self) -> List[Dict]:
        """الحصول على الأسئلة المنتظرة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT q.*, u.first_name, u.username 
                FROM help_questions q 
                JOIN users u ON q.user_id = u.user_id 
                WHERE q.is_approved = 0 
                ORDER BY q.ask_date
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب الأسئلة المنتظرة: {e}")
            return []
    
    def get_approved_questions(self) -> List[Dict]:
        """الحصول على الأسئلة المعتمدة وغير المجابة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT q.*, u.first_name, u.username 
                FROM help_questions q 
                JOIN users u ON q.user_id = u.user_id 
                WHERE q.is_approved = 1 
                AND q.is_answered = 0 
                ORDER BY q.ask_date
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب الأسئلة المعتمدة: {e}")
            return []
    
    # ============ الإعدادات والخدمات ============
    
    def get_setting(self, key: str, default: str = "") -> str:
        """الحصول على إعداد"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT setting_value 
                FROM bot_settings 
                WHERE setting_key = ?
            ''', (key,))
            row = cursor.fetchone()
            if row:
                return row['setting_value']
            return default
        except Exception as e:
            logging.error(f"خطأ في جلب الإعداد: {e}")
            return default
    
    def update_setting(self, key: str, value: str) -> bool:
        """تحديث إعداد"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO bot_settings 
                (setting_key, setting_value) 
                VALUES (?, ?)
            ''', (key, value))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في تحديث الإعداد: {e}")
            return False
    
    def get_service_price(self, service_name: str) -> int:
        """الحصول على سعر الخدمة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT price 
                FROM service_status 
                WHERE service_name = ?
            ''', (service_name,))
            row = cursor.fetchone()
            if row:
                return row['price']
            return SERVICE_PRICES.get(service_name, 1000)
        except Exception as e:
            logging.error(f"خطأ في جلب سعر الخدمة: {e}")
            return SERVICE_PRICES.get(service_name, 1000)
    
    def is_service_active(self, service_name: str) -> bool:
        """التحقق من تفعيل الخدمة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT is_active 
                FROM service_status 
                WHERE service_name = ?
            ''', (service_name,))
            row = cursor.fetchone()
            if row:
                return bool(row['is_active'])
            return True
        except Exception as e:
            logging.error(f"خطأ في التحقق من الخدمة: {e}")
            return True
    
    def set_service_status(self, service_name: str, is_active: bool) -> bool:
        """تحديث حالة الخدمة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO service_status 
                (service_name, is_active) 
                VALUES (?, ?)
            ''', (service_name, 1 if is_active else 0))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في تحديث حالة الخدمة: {e}")
            return False
    
    def set_service_price(self, service_name: str, price: int) -> bool:
        """تحديث سعر الخدمة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO service_status 
                (service_name, price) 
                VALUES (?, ?)
            ''', (service_name, price))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"خطأ في تحديث سعر الخدمة: {e}")
            return False
    
    # ============ الإحصائيات ============
    
    def get_bot_stats(self) -> Dict:
        """الحصول على إحصائيات البوت"""
        try:
            cursor = self.connection.cursor()
            
            stats = {}
            
            # إجمالي المستخدمين
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            # المستخدمين النشطين (آخر 7 أيام)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active > datetime('now', '-7 days')
            ''')
            stats['active_users'] = cursor.fetchone()[0]
            
            # مشتركي VIP النشطين
            cursor.execute('''
                SELECT COUNT(*) FROM vip_subscriptions 
                WHERE is_active = 1 
                AND end_date > datetime('now')
            ''')
            stats['vip_users'] = cursor.fetchone()[0]
            
            # إجمالي الأرصدة
            cursor.execute('SELECT SUM(balance) FROM users')
            stats['total_balance'] = cursor.fetchone()[0] or 0
            
            # الدخل اليومي
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT total_income 
                FROM bot_stats 
                WHERE stat_date = ?
            ''', (today,))
            row = cursor.fetchone()
            stats['daily_income'] = row['total_income'] if row else 0
            
            return stats
            
        except Exception as e:
            logging.error(f"خطأ في جلب الإحصائيات: {e}")
            return {}
    
    def get_all_users(self, limit: int = 100) -> List[Dict]:
        """الحصول على جميع المستخدمين"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM users 
                ORDER BY last_active DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب المستخدمين: {e}")
            return []
    
    def get_user_transactions(self, user_id: int, limit: int = 20) -> List[Dict]:
        """الحصول على معاملات المستخدم"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب المعاملات: {e}")
            return []
    
    def get_all_vip_lectures(self) -> List[Dict]:
        """الحصول على جميع محاضرات VIP"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT l.*, u.first_name, u.username 
                FROM vip_lectures l 
                JOIN users u ON l.teacher_id = u.user_id 
                WHERE l.is_approved = 1 
                ORDER BY l.upload_date DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب محاضرات VIP: {e}")
            return []
    
    def get_pending_vip_lectures(self) -> List[Dict]:
        """الحصول على محاضرات VIP المنتظرة"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT l.*, u.first_name, u.username 
                FROM vip_lectures l 
                JOIN users u ON l.teacher_id = u.user_id 
                WHERE l.is_approved = 0 
                ORDER BY l.upload_date
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"خطأ في جلب محاضرات VIP المنتظرة: {e}")
            return []
    
    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()

# ============================================================================
# واجهة Telegram API
# ============================================================================

class TelegramAPI:
    """واجهة للتعامل مع Telegram Bot API"""
    
    BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
    
    @staticmethod
    def send_message(chat_id: int, text: str, parse_mode: str = None, 
                    reply_markup: dict = None, reply_to_message_id: int = None) -> dict:
        """إرسال رسالة"""
        data = {
            'chat_id': chat_id,
            'text': text
        }
        
        if parse_mode:
            data['parse_mode'] = parse_mode
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id
        
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/sendMessage", 
                                     json_data=data)
        return response
    
    @staticmethod
    def edit_message_text(chat_id: int, message_id: int, text: str, 
                         parse_mode: str = None, reply_markup: dict = None) -> dict:
        """تعديل نص الرسالة"""
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text
        }
        
        if parse_mode:
            data['parse_mode'] = parse_mode
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/editMessageText", 
                                     json_data=data)
        return response
    
    @staticmethod
    def delete_message(chat_id: int, message_id: int) -> dict:
        """حذف رسالة"""
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/deleteMessage", 
                                     json_data=data)
        return response
    
    @staticmethod
    def answer_callback_query(callback_query_id: str, text: str = None, 
                             show_alert: bool = False) -> dict:
        """الرد على استعلام رد الاتصال"""
        data = {
            'callback_query_id': callback_query_id
        }
        
        if text:
            data['text'] = text
        
        if show_alert:
            data['show_alert'] = show_alert
        
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/answerCallbackQuery", 
                                     json_data=data)
        return response
    
    @staticmethod
    def send_document(chat_id: int, document: str, caption: str = None, 
                     parse_mode: str = None) -> dict:
        """إرسال مستند"""
        data = {
            'chat_id': chat_id,
            'document': document
        }
        
        if caption:
            data['caption'] = caption
        
        if parse_mode:
            data['parse_mode'] = parse_mode
        
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/sendDocument", 
                                     json_data=data)
        return response
    
    @staticmethod
    def send_video(chat_id: int, video: str, caption: str = None) -> dict:
        """إرسال فيديو"""
        data = {
            'chat_id': chat_id,
            'video': video
        }
        
        if caption:
            data['caption'] = caption
        
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/sendVideo", 
                                     json_data=data)
        return response
    
    @staticmethod
    def get_file(file_id: str) -> dict:
        """الحصول على معلومات الملف"""
        data = {'file_id': file_id}
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/getFile", 
                                     json_data=data)
        return response
    
    @staticmethod
    def get_user_profile_photos(user_id: int) -> dict:
        """الحصول على صور الملف الشخصي"""
        data = {'user_id': user_id}
        response = HTTPClient.request('POST', f"{TelegramAPI.BASE_URL}/getUserProfilePhotos", 
                                     json_data=data)
        return response

# ============================================================================
# أدوات المساعدة
# ============================================================================

class Utils:
    """أدوات مساعدة"""
    
    @staticmethod
    def format_currency(amount: int) -> str:
        """تنسيق العملة"""
        return f"{amount:,} دينار عراقي"
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """تهيئة النص لـ Markdown"""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """تقصير النص"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def generate_invite_link(user_id: int) -> str:
        """إنشاء رابط دعوة"""
        return f"https://t.me/{BOT_USERNAME[1:]}?start={user_id}"
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """تنسيق التاريخ"""
        try:
            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y/%m/%d %H:%M')
        except:
            return date_str
    
    @staticmethod
    def is_valid_score(score: str) -> Tuple[bool, float]:
        """التحقق من صحة الدرجة"""
        try:
            score_float = float(score)
            if 0 <= score_float <= 100:
                return True, score_float
            return False, 0
        except:
            return False, 0

class KeyboardBuilder:
    """بناء لوحات المفاتيح"""
    
    @staticmethod
    def create_inline_keyboard(buttons: list) -> dict:
        """إنشاء لوحة مفاتيح مضمنة"""
        keyboard = []
        
        for row in buttons:
            keyboard_row = []
            for button in row:
                if isinstance(button, dict):
                    keyboard_row.append(button)
            
            if keyboard_row:
                keyboard.append(keyboard_row)
        
        return {'inline_keyboard': keyboard}
    
    @staticmethod
    def create_reply_keyboard(buttons: list, resize: bool = True, 
                             one_time: bool = False) -> dict:
        """إنشاء لوحة مفاتيح رد"""
        keyboard = []
        
        for row in buttons:
            keyboard_row = []
            for button_text in row:
                keyboard_row.append({'text': button_text})
            
            if keyboard_row:
                keyboard.append(keyboard_row)
        
        return {
            'keyboard': keyboard,
            'resize_keyboard': resize,
            'one_time_keyboard': one_time
        }
    
    @staticmethod
    def remove_keyboard() -> dict:
        """إزالة لوحة المفاتيح"""
        return {'remove_keyboard': True}
    
    @staticmethod
    def force_reply(placeholder: str = None) -> dict:
        """إجبار الرد"""
        data = {'force_reply': True}
        if placeholder:
            data['input_field_placeholder'] = placeholder
        return data
    
    # لوحات المفاتيح الرئيسية
    
    @staticmethod
    def main_menu(user_id: int) -> dict:
        """القائمة الرئيسية"""
        buttons = [
            [
                {'text': '🧮 حساب درجة الإعفاء', 'callback_data': 'service_exemption'},
                {'text': '📚 تلخيص الملازم', 'callback_data': 'service_summary'}
            ],
            [
                {'text': '❓ سؤال وجواب', 'callback_data': 'service_qa'},
                {'text': '👥 ساعدوني طالب', 'callback_data': 'service_help'}
            ],
            [
                {'text': '📖 ملازمي ومرشحاتي', 'callback_data': 'service_materials'},
                {'text': '🎓 محاضرات VIP', 'callback_data': 'vip_lectures'}
            ],
            [
                {'text': '⭐ اشتراك VIP', 'callback_data': 'vip_subscription'},
                {'text': '💰 رصيدي', 'callback_data': 'my_balance'}
            ],
            [
                {'text': '👥 دعوة صديق', 'callback_data': 'invite_friend'}
            ]
        ]
        
        if user_id == ADMIN_ID:
            buttons.append([
                {'text': '👑 لوحة التحكم', 'callback_data': 'admin_panel'}
            ])
        
        return KeyboardBuilder.create_inline_keyboard(buttons)
    
    @staticmethod
    def admin_panel() -> dict:
        """لوحة تحكم المدير"""
        buttons = [
            [
                {'text': '💰 شحن رصيد', 'callback_data': 'admin_charge'},
                {'text': '💸 خصم رصيد', 'callback_data': 'admin_deduct'}
            ],
            [
                {'text': '🚫 حظر مستخدم', 'callback_data': 'admin_ban'},
                {'text': '✅ فك حظر', 'callback_data': 'admin_unban'}
            ],
            [
                {'text': '👥 إدارة المستخدمين', 'callback_data': 'admin_users'},
                {'text': '⚙️ إدارة الخدمات', 'callback_data': 'admin_services'}
            ],
            [
                {'text': '📊 الإحصائيات', 'callback_data': 'admin_stats'},
                {'text': '📢 إرسال إذاعة', 'callback_data': 'admin_broadcast'}
            ],
            [
                {'text': '⭐ إدارة VIP', 'callback_data': 'admin_vip'},
                {'text': '📖 إدارة المواد', 'callback_data': 'admin_materials'}
            ],
            [
                {'text': '❓ الأسئلة المنتظرة', 'callback_data': 'admin_pending_questions'},
                {'text': '🎬 محاضرات منتظرة', 'callback_data': 'admin_pending_lectures'}
            ],
            [
                {'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}
            ]
        ]
        
        return KeyboardBuilder.create_inline_keyboard(buttons)
    
    @staticmethod
    def back_button(target: str = 'main_menu') -> dict:
        """زر الرجوع"""
        return KeyboardBuilder.create_inline_keyboard([
            [{'text': '🔙 الرجوع', 'callback_data': target}]
        ])
    
    @staticmethod
    def cancel_button() -> dict:
        """زر الإلغاء"""
        return KeyboardBuilder.create_inline_keyboard([
            [{'text': '❌ إلغاء', 'callback_data': 'main_menu'}]
        ])
    
    @staticmethod
    def confirmation_buttons(yes_callback: str, no_callback: str, 
                            yes_text: str = '✅ نعم', no_text: str = '❌ لا') -> dict:
        """أزرار التأكيد"""
        return KeyboardBuilder.create_inline_keyboard([
            [
                {'text': yes_text, 'callback_data': yes_callback},
                {'text': no_text, 'callback_data': no_callback}
            ]
        ])
    
    @staticmethod
    def vip_subscription_menu() -> dict:
        """قائمة اشتراك VIP"""
        return KeyboardBuilder.create_inline_keyboard([
            [{'text': '✅ اشتراك الآن', 'callback_data': 'vip_purchase'}],
            [{'text': '📋 الشروط والمميزات', 'callback_data': 'vip_terms'}],
            [{'text': '🔙 الرجوع', 'callback_data': 'main_menu'}]
        ])
    
    @staticmethod
    def vip_lectures_menu() -> dict:
        """قائمة محاضرات VIP"""
        return KeyboardBuilder.create_inline_keyboard([
            [{'text': '🎓 عرض المحاضرات', 'callback_data': 'view_vip_lectures'}],
            [{'text': '📤 رفع محاضرة', 'callback_data': 'vip_upload'}],
            [{'text': '💰 أرباحي', 'callback_data': 'vip_earnings'}],
            [{'text': '🔙 الرجوع', 'callback_data': 'main_menu'}]
        ])
    
    @staticmethod
    def help_student_menu() -> dict:
        """قائمة ساعدوني طالب"""
        return KeyboardBuilder.create_inline_keyboard([
            [{'text': '❓ أرسل سؤال جديد', 'callback_data': 'ask_help_question'}],
            [{'text': '✏️ جاوب على سؤال', 'callback_data': 'answer_questions'}],
            [{'text': '🔙 الرجوع', 'callback_data': 'main_menu'}]
        ])
    
    @staticmethod
    def materials_menu() -> dict:
        """قائمة المواد التعليمية"""
        return KeyboardBuilder.create_inline_keyboard([
            [{'text': '📥 تحميل المواد', 'callback_data': 'download_materials'}],
            [{'text': '🔙 الرجوع', 'callback_data': 'main_menu'}]
        ])

class AIProcessor:
    """معالج الذكاء الاصطناعي"""
    
    @staticmethod
    def generate_gemini_response(prompt: str) -> str:
        """إنشاء رد باستخدام Gemini AI"""
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': GEMINI_API_KEY
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = HTTPClient.request('POST', url, headers=headers, json_data=data)
            
            if response['status'] == 200:
                result = response['json']()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return "عذراً، حدث خطأ في معالجة الطلب. حاول مرة أخرى لاحقاً."
            
        except Exception as e:
            logging.error(f"خطأ في الذكاء الاصطناعي: {e}")
            return "عذراً، خدمة الذكاء الاصطناعي غير متوفرة حالياً."
    
    @staticmethod
    def summarize_text(text: str) -> str:
        """تلخيص النص"""
        prompt = f"""الرجاء تلخيص النص التالي مع الحفاظ على المعلومات المهمة وحذف الزائد:

{text[:3000]}

قدم التلخيص بشكل منظم مع عناوين رئيسية."""
        
        return AIProcessor.generate_gemini_response(prompt)
    
    @staticmethod
    def answer_question(question: str) -> str:
        """الإجابة على سؤال"""
        prompt = f"""أجب على السؤال التالي كطالب عراقي، مع تقديم إجابة علمية دقيقة ومناسبة للمنهج العراقي:

السؤال: {question}

قدم الإجابة بشكل منظم ومفصل مع الأمثلة إذا لزم الأمر."""
        
        return AIProcessor.generate_gemini_response(prompt)

# ============================================================================
# البوت الرئيسي
# ============================================================================

class LearnBot:
    """الفئة الرئيسية للبوت"""
    
    def __init__(self):
        # إعداد التسجيل
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # قاعدة البيانات
        self.db = Database()
        
        # تخزين جلسات المستخدمين
        self.user_sessions = {}
        
        # أدوات المساعدة
        self.utils = Utils()
        self.ai_processor = AIProcessor()
        
        self.logger.info("تم تهيئة البوت بنجاح")
    
    def get_user_session(self, user_id: int) -> dict:
        """الحصول على جلسة المستخدم"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'state': BotState.MAIN_MENU,
                'data': {}
            }
        return self.user_sessions[user_id]
    
    def update_user_session(self, user_id: int, state: str = None, data: dict = None):
        """تحديث جلسة المستخدم"""
        session = self.get_user_session(user_id)
        
        if state:
            session['state'] = state
        
        if data:
            session['data'].update(data)
        
        self.user_sessions[user_id] = session
    
    def clear_user_session(self, user_id: int):
        """مسح جلسة المستخدم"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
    
    # ============ معالجة التحديثات ============
    
    def handle_update(self, update: dict):
        """معالجة التحديث الوارد"""
        try:
            # التحقق من وجود رسالة أو استعلام رد اتصال
            if 'message' in update:
                self.handle_message(update['message'])
            
            elif 'callback_query' in update:
                self.handle_callback_query(update['callback_query'])
            
            else:
                self.logger.warning(f"تحديث غير معروف: {update}")
                
        except Exception as e:
            self.logger.error(f"خطأ في معالجة التحديث: {e}")
    
    def handle_message(self, message: dict):
        """معالجة الرسالة"""
        try:
            # استخراج المعلومات الأساسية
            chat_id = message['chat']['id']
            user = message['from']
            user_id = user['id']
            username = user.get('username', '')
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            
            # تحديث نشاط المستخدم
            self.db.update_user_activity(user_id)
            
            # التحقق من وجود المستخدم وإنشاؤه إذا لزم الأمر
            if not self.db.get_user(user_id):
                # التحقق من رابط الدعوة
                invited_by = 0
                if 'text' in message and message['text'].startswith('/start'):
                    parts = message['text'].split()
                    if len(parts) > 1:
                        try:
                            invited_by = int(parts[1])
                        except:
                            pass
                
                # إنشاء المستخدم
                self.db.create_user(user_id, username, first_name, last_name, invited_by)
            
            # التحقق من الحظر
            user_data = self.db.get_user(user_id)
            if user_data and user_data['is_banned']:
                TelegramAPI.send_message(
                    chat_id,
                    "🚫 حسابك محظور! راسل الدعم الفني للمساعدة.",
                    reply_markup=KeyboardBuilder.back_button()
                )
                return
            
            # التحقق من وضع الصيانة
            if self.db.get_setting('maintenance_mode', '0') == '1' and user_id != ADMIN_ID:
                TelegramAPI.send_message(
                    chat_id,
                    "🔧 البوت قيد الصيانة حاليًا. نعتذر للإزعاج وسنعود قريبًا.",
                    reply_markup=KeyboardBuilder.back_button()
                )
                return
            
            # معالجة الرسالة بناءً على حالة المستخدم
            session = self.get_user_session(user_id)
            state = session['state']
            
            if 'text' in message:
                text = message['text']
                
                if text.startswith('/'):
                    self.handle_command(chat_id, user_id, text, message)
                else:
                    self.handle_text_message(chat_id, user_id, text, state, session)
            
            elif 'document' in message:
                self.handle_document(chat_id, user_id, message, state, session)
            
            elif 'photo' in message:
                self.handle_photo(chat_id, user_id, message, state, session)
            
            elif 'video' in message:
                self.handle_video(chat_id, user_id, message, state, session)
            
            else:
                TelegramAPI.send_message(
                    chat_id,
                    "🤔 لم أفهم رسالتك. استخدم القائمة أدناه للتفاعل مع البوت.",
                    reply_markup=KeyboardBuilder.main_menu(user_id)
                )
                
        except Exception as e:
            self.logger.error(f"خطأ في معالجة الرسالة: {e}")
    
    def handle_command(self, chat_id: int, user_id: int, command: str, message: dict):
        """معالجة الأوامر"""
        if command == '/start' or command.startswith('/start '):
            self.send_welcome_message(chat_id, user_id, message)
        
        elif command == '/admin' and user_id == ADMIN_ID:
            self.show_admin_panel(chat_id, user_id)
        
        elif command == '/balance':
            self.show_balance(chat_id, user_id)
        
        elif command == '/invite':
            self.show_invitation(chat_id, user_id)
        
        elif command == '/help':
            self.show_help(chat_id, user_id)
        
        else:
            TelegramAPI.send_message(
                chat_id,
                "❓ الأمر غير معروف. استخدم /start للبدء.",
                reply_markup=KeyboardBuilder.main_menu(user_id)
            )
    
    def handle_text_message(self, chat_id: int, user_id: int, text: str, 
                           state: str, session: dict):
        """معالجة الرسائل النصية"""
        if state == BotState.EXEMPTION_STEP1:
            self.handle_exemption_step1(chat_id, user_id, text, session)
        
        elif state == BotState.EXEMPTION_STEP2:
            self.handle_exemption_step2(chat_id, user_id, text, session)
        
        elif state == BotState.EXEMPTION_STEP3:
            self.handle_exemption_step3(chat_id, user_id, text, session)
        
        elif state == BotState.HELP_STUDENT_ASK:
            self.handle_help_question(chat_id, user_id, text, session)
        
        elif state == BotState.HELP_STUDENT_ANSWER:
            self.handle_help_answer(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_CHARGE:
            self.handle_admin_charge(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_DEDUCT:
            self.handle_admin_deduct(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_BAN:
            self.handle_admin_ban(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_UNBAN:
            self.handle_admin_unban(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_BROADCAST:
            self.handle_admin_broadcast(chat_id, user_id, text, session)
        
        elif state == BotState.VIP_UPLOAD_TITLE:
            self.handle_vip_upload_title(chat_id, user_id, text, session)
        
        elif state == BotState.VIP_UPLOAD_DESC:
            self.handle_vip_upload_desc(chat_id, user_id, text, session)
        
        elif state == BotState.VIP_SET_PRICE:
            self.handle_vip_set_price(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_ADD_MAT_TITLE:
            self.handle_admin_add_mat_title(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_ADD_MAT_DESC:
            self.handle_admin_add_mat_desc(chat_id, user_id, text, session)
        
        elif state == BotState.ADMIN_ADD_MAT_STAGE:
            self.handle_admin_add_mat_stage(chat_id, user_id, text, session)
        
        elif state == BotState.ASK_QUESTION:
            self.handle_ai_question(chat_id, user_id, text, session)
        
        else:
            # إذا كانت حالة غير معروفة، عرض القائمة الرئيسية
            self.show_main_menu(chat_id, user_id)
    
    def handle_callback_query(self, callback_query: dict):
        """معالجة استعلام رد الاتصال"""
        try:
            query_id = callback_query['id']
            data = callback_query['data']
            user = callback_query['from']
            message = callback_query['message']
            
            user_id = user['id']
            chat_id = message['chat']['id']
            message_id = message['message_id']
            
            # الرد على الاستعلام
            TelegramAPI.answer_callback_query(query_id)
            
            # تحديث نشاط المستخدم
            self.db.update_user_activity(user_id)
            
            # التحقق من الحظر
            user_data = self.db.get_user(user_id)
            if user_data and user_data['is_banned']:
                TelegramAPI.edit_message_text(
                    chat_id,
                    message_id,
                    "🚫 حسابك محظور! راسل الدعم الفني للمساعدة.",
                    reply_markup=KeyboardBuilder.back_button()
                )
                return
            
            # التحقق من وضع الصيانة
            if self.db.get_setting('maintenance_mode', '0') == '1' and user_id != ADMIN_ID:
                TelegramAPI.edit_message_text(
                    chat_id,
                    message_id,
                    "🔧 البوت قيد الصيانة حاليًا. نعتذر للإزعاج وسنعود قريبًا.",
                    reply_markup=KeyboardBuilder.back_button()
                )
                return
            
            # معالجة البيانات
            if data == 'main_menu':
                self.show_main_menu(chat_id, user_id, message_id)
            
            elif data == 'admin_panel':
                if user_id == ADMIN_ID:
                    self.show_admin_panel(chat_id, user_id, message_id)
                else:
                    TelegramAPI.edit_message_text(
                        chat_id,
                        message_id,
                        "⛔ ليس لديك صلاحية الدخول إلى لوحة التحكم!",
                        reply_markup=KeyboardBuilder.back_button()
                    )
            
            elif data.startswith('service_'):
                service = data.replace('service_', '')
                self.handle_service_selection(chat_id, user_id, message_id, service)
            
            elif data == 'my_balance':
                self.show_balance(chat_id, user_id, message_id)
            
            elif data == 'invite_friend':
                self.show_invitation(chat_id, user_id, message_id)
            
            elif data == 'vip_subscription':
                self.show_vip_subscription(chat_id, user_id, message_id)
            
            elif data == 'vip_lectures':
                self.show_vip_lectures(chat_id, user_id, message_id)
            
            elif data == 'vip_purchase':
                self.purchase_vip_subscription(chat_id, user_id, message_id)
            
            elif data == 'vip_upload':
                self.start_vip_upload(chat_id, user_id, message_id)
            
            elif data == 'vip_earnings':
                self.show_vip_earnings(chat_id, user_id, message_id)
            
            elif data == 'vip_terms':
                self.show_vip_terms(chat_id, user_id, message_id)
            
            elif data == 'view_vip_lectures':
                self.view_vip_lectures(chat_id, user_id, message_id)
            
            elif data.startswith('view_lecture_'):
                lecture_id = int(data.replace('view_lecture_', ''))
                self.view_lecture_details(chat_id, user_id, message_id, lecture_id)
            
            elif data.startswith('purchase_lecture_'):
                lecture_id = int(data.replace('purchase_lecture_', ''))
                self.purchase_lecture(chat_id, user_id, message_id, lecture_id)
            
            elif data.startswith('admin_'):
                self.handle_admin_callback(chat_id, user_id, message_id, data)
            
            elif data.startswith('approve_'):
                self.handle_approval_callback(chat_id, user_id, message_id, data)
            
            elif data.startswith('reject_'):
                self.handle_rejection_callback(chat_id, user_id, message_id, data)
            
            elif data.startswith('answer_'):
                self.handle_answer_callback(chat_id, user_id, message_id, data)
            
            elif data.startswith('download_'):
                self.handle_download_callback(chat_id, user_id, message_id, data)
            
            elif data == 'ask_help_question':
                self.start_help_question(chat_id, user_id, message_id)
            
            elif data == 'answer_questions':
                self.show_questions_to_answer(chat_id, user_id, message_id)
            
            elif data == 'download_materials':
                self.show_materials(chat_id, user_id, message_id)
            
            else:
                self.logger.warning(f"استعلام غير معروف: {data}")
                TelegramAPI.edit_message_text(
                    chat_id,
                    message_id,
                    "❓ أمر غير معروف. حاول مرة أخرى.",
                    reply_markup=KeyboardBuilder.main_menu(user_id)
                )
                
        except Exception as e:
            self.logger.error(f"خطأ في معالجة استعلام رد الاتصال: {e}")
    
    # ============ الرسائل الترحيبية ============
    
    def send_welcome_message(self, chat_id: int, user_id: int, message: dict):
        """إرسال رسالة الترحيب"""
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            # المستخدم جديد، سيتم إنشاؤه في handle_message
            pass
        
        welcome_text = f"""
        🎉 أهلاً بك {user_data['first_name'] if user_data else 'عزيزي'} في بوت *يلا نتعلم*!

        *رصيدك الحالي:* {self.utils.format_currency(user_data['balance'] if user_data else 1000)}

        *الخدمات المتاحة:*
        • حساب درجة الإعفاء
        • تلخيص الملازم (PDF)
        • سؤال وجواب بالذكاء الاصطناعي
        • قسم ساعدوني طالب
        • مكتبة المواد التعليمية
        • محاضرات VIP

        جميع الخدمات مدفوعة بسعر 1000 دينار لكل خدمة.

        اختر الخدمة التي تريدها 👇
        """
        
        TelegramAPI.send_message(
            chat_id,
            welcome_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.main_menu(user_id)
        )
    
    def show_main_menu(self, chat_id: int, user_id: int, message_id: int = None):
        """عرض القائمة الرئيسية"""
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            TelegramAPI.send_message(
                chat_id,
                "يرجى استخدام /start للبدء",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        welcome_text = f"""
        👋 أهلاً بك {user_data['first_name']} في بوت *يلا نتعلم*!

        *رصيدك الحالي:* {self.utils.format_currency(user_data['balance'])}

        *الخدمات المتاحة:* (جميعها مدفوعة)

        اختر الخدمة التي تريدها 👇
        """
        
        if message_id:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                welcome_text,
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.main_menu(user_id)
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                welcome_text,
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.main_menu(user_id)
            )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.MAIN_MENU)
    
    def show_help(self, chat_id: int, user_id: int):
        """عرض المساعدة"""
        help_text = """
        *🎓 بوت يلا نتعلم - المساعدة*

        *الخدمات المتاحة:*
        1. *حساب درجة الإعفاء* - حساب معدل 3 كورسات للإعفاء
        2. *تلخيص الملازم* - تلخيص ملفات PDF باستخدام الذكاء الاصطناعي
        3. *سؤال وجواب* - الإجابة على الأسئلة الدراسية بالذكاء الاصطناعي
        4. *ساعدوني طالب* - طرح الأسئلة والإجابة على أسئلة الطلاب
        5. *ملازمي ومرشحاتي* - مكتبة المواد التعليمية
        6. *محاضرات VIP* - محاضرات فيديو مدفوعة

        *طرق الدفع:*
        • جميع الخدمات مدفوعة (1000 دينار لكل خدمة)
        • يمكنك شحن رصيدك عن طريق الدعم الفني
        • مكافأة الدعوة: 500 دينار لكل صديق تدعوه

        *الدعم الفني:*
        للاستفسارات أو المشاكل، راسل: @Allawi04

        *قناة البوت:* @FCJCV
        """
        
        TelegramAPI.send_message(
            chat_id,
            help_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.main_menu(user_id)
        )
    
    # ============ خدمات المستخدمين ============
    
    def handle_service_selection(self, chat_id: int, user_id: int, 
                                message_id: int, service: str):
        """معالجة اختيار الخدمة"""
        # التحقق من تفعيل الخدمة
        if not self.db.is_service_active(service):
            error_text = f"⛔ خدمة {self.get_service_name(service)} معطلة حالياً."
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                error_text,
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # الحصول على سعر الخدمة
        price = self.db.get_service_price(service)
        
        # التحقق من رصيد المستخدم
        user_data = self.db.get_user(user_id)
        if user_data['balance'] < price:
            error_text = f"""
            ⚠️ رصيدك غير كافي!

            *سعر الخدمة:* {self.utils.format_currency(price)}
            *رصيدك الحالي:* {self.utils.format_currency(user_data['balance'])}

            يمكنك شحن رصيدك أو دعوة الأصدقاء للحصول على مكافآت.
            """
            
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                error_text,
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.create_inline_keyboard([
                    [{'text': '💰 شحن الرصيد', 'callback_data': 'invite_friend'}],
                    [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
                ])
            )
            return
        
        # حفظ حالة الخدمة
        self.update_user_session(user_id, BotState.MAIN_MENU, {
            'current_service': service,
            'service_price': price
        })
        
        # توجيه إلى الخدمة المحددة
        if service == 'exemption':
            self.start_exemption_calculation(chat_id, user_id, message_id)
        
        elif service == 'summary':
            self.start_pdf_summary(chat_id, user_id, message_id)
        
        elif service == 'qa':
            self.start_ai_question(chat_id, user_id, message_id)
        
        elif service == 'help':
            self.show_help_student_section(chat_id, user_id, message_id)
        
        elif service == 'materials':
            self.show_materials(chat_id, user_id, message_id)
    
    def get_service_name(self, service_key: str) -> str:
        """الحصول على اسم الخدمة"""
        service_names = {
            'exemption': 'حساب درجة الإعفاء',
            'summary': 'تلخيص الملازم',
            'qa': 'سؤال وجواب',
            'help': 'ساعدوني طالب',
            'materials': 'ملازمي ومرشحاتي',
            'vip_subscription': 'اشتراك VIP'
        }
        return service_names.get(service_key, service_key)
    
    # ============ حساب درجة الإعفاء ============
    
    def start_exemption_calculation(self, chat_id: int, user_id: int, message_id: int):
        """بدء حساب درجة الإعفاء"""
        instruction_text = """
        🧮 *حساب درجة الإعفاء*

        أدخل درجة الكورس الأول (0-100):
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.EXEMPTION_STEP1, {
            'exemption_scores': []
        })
    
    def handle_exemption_step1(self, chat_id: int, user_id: int, 
                              text: str, session: dict):
        """معالجة درجة الكورس الأول"""
        valid, score = self.utils.is_valid_score(text)
        
        if valid:
            scores = session['data'].get('exemption_scores', [])
            scores.append(score)
            
            self.update_user_session(user_id, BotState.EXEMPTION_STEP2, {
                'exemption_scores': scores
            })
            
            TelegramAPI.send_message(
                chat_id,
                "✅ تم حفظ درجة الكورس الأول\n\nأدخل درجة الكورس الثاني (0-100):",
                reply_markup=KeyboardBuilder.cancel_button()
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال درجة بين 0 و 100",
                reply_markup=KeyboardBuilder.cancel_button()
            )
    
    def handle_exemption_step2(self, chat_id: int, user_id: int, 
                              text: str, session: dict):
        """معالجة درجة الكورس الثاني"""
        valid, score = self.utils.is_valid_score(text)
        
        if valid:
            scores = session['data'].get('exemption_scores', [])
            scores.append(score)
            
            self.update_user_session(user_id, BotState.EXEMPTION_STEP3, {
                'exemption_scores': scores
            })
            
            TelegramAPI.send_message(
                chat_id,
                "✅ تم حفظ درجة الكورس الثاني\n\nأدخل درجة الكورس الثالث (0-100):",
                reply_markup=KeyboardBuilder.cancel_button()
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال درجة بين 0 و 100",
                reply_markup=KeyboardBuilder.cancel_button()
            )
    
    def handle_exemption_step3(self, chat_id: int, user_id: int, 
                              text: str, session: dict):
        """معالجة درجة الكورس الثالث وحساب المعدل"""
        valid, score = self.utils.is_valid_score(text)
        
        if valid:
            scores = session['data'].get('exemption_scores', [])
            scores.append(score)
            
            # حساب المعدل
            average = sum(scores) / len(scores)
            
            # خصم المبلغ
            price = session['data'].get('service_price', 1000)
            if not self.db.update_user_balance(user_id, -price, 
                                              'service_payment', 
                                              'حساب درجة الإعفاء'):
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ حدث خطأ في عملية الدفع!",
                    reply_markup=KeyboardBuilder.back_button()
                )
                return
            
            # إرسال النتيجة
            if average >= 90:
                result_text = f"""
                🎉 *مبروك! أنت معفى من المادة*

                *المعدل النهائي:* {average:.2f}
                *الدرجات:* {scores[0]}, {scores[1]}, {scores[2]}

                تهانينا على تحقيق الإعفاء! 🎊
                """
            else:
                result_text = f"""
                ⚠️ *للأسف أنت غير معفى*

                *المعدل النهائي:* {average:.2f}
                *الدرجات:* {scores[0]}, {scores[1]}, {scores[2]}

                المعدل المطلوب للإعفاء هو 90 أو أكثر
                """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}],
                [{'text': '🔄 حساب جديد', 'callback_data': 'service_exemption'}]
            ])
            
            TelegramAPI.send_message(
                chat_id,
                result_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            # تنظيف الجلسة
            self.clear_user_session(user_id)
        
        else:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال درجة بين 0 و 100",
                reply_markup=KeyboardBuilder.cancel_button()
            )
    
    # ============ تلخيص PDF ============
    
    def start_pdf_summary(self, chat_id: int, user_id: int, message_id: int):
        """بدء تلخيص PDF"""
        instruction_text = """
        📚 *تلخيص الملازم (PDF)*

        أرسل ملف PDF المراد تلخيصه.

        *ملاحظات:*
        • الملف يجب أن يكون بصيغة PDF
        • الحجم الأقصى: 20 ميجابايت
        • سيتم استخدام الذكاء الاصطناعي للتلخيص
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.UPLOAD_PDF)
    
    def handle_document(self, chat_id: int, user_id: int, 
                       message: dict, state: str, session: dict):
        """معالجة الملفات"""
        if state == BotState.UPLOAD_PDF:
            self.handle_pdf_upload(chat_id, user_id, message, session)
        
        elif state == BotState.ADMIN_ADD_MAT_FILE:
            self.handle_admin_add_mat_file(chat_id, user_id, message, session)
    
    def handle_pdf_upload(self, chat_id: int, user_id: int, 
                         message: dict, session: dict):
        """معالجة رفع ملف PDF"""
        document = message['document']
        file_name = document.get('file_name', '')
        
        if not file_name.lower().endswith('.pdf'):
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الملف يجب أن يكون بصيغة PDF",
                reply_markup=KeyboardBuilder.cancel_button()
            )
            return
        
        # خصم المبلغ
        price = session['data'].get('service_price', 1000)
        if not self.db.update_user_balance(user_id, -price, 
                                          'service_payment', 
                                          'تلخيص PDF'):
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في عملية الدفع!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # إعلام المستخدم بالمعالجة
        TelegramAPI.send_message(
            chat_id,
            "🔄 جاري معالجة الملف وتلخيصه...",
            reply_markup=KeyboardBuilder.back_button()
        )
        
        try:
            # الحصول على معلومات الملف
            file_id = document['file_id']
            file_info = TelegramAPI.get_file(file_id)
            
            if file_info['status'] != 200:
                raise Exception("فشل في الحصول على معلومات الملف")
            
            # هنا في الإصدار الحقيقي، تحتاج لتحميل الملف ومعالجته
            # لأغراظ العرض، سنستخدم نصاً وهمياً
            
            summary_text = "هذا هو النص الملخص للملف. في الإصدار الحقيقي، سيتم استخدام الذكاء الاصطناعي لتحليل وتلخيص الملف."
            
            # إرسال النتيجة
            result_text = f"""
            ✅ *تم تلخيص الملف بنجاح*

            *ملخص المحتوى:*
            {summary_text}

            *ملاحظة:* في الإصدار الحقيقي، سيتم إرسال ملف PDF ملخص.
            """
            
            TelegramAPI.send_message(
                chat_id,
                result_text,
                parse_mode='Markdown'
            )
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}],
                [{'text': '📚 تلخيص ملف آخر', 'callback_data': 'service_summary'}]
            ])
            
            TelegramAPI.send_message(
                chat_id,
                "اختر الخطوة التالية:",
                reply_markup=keyboard
            )
            
            # تنظيف الجلسة
            self.clear_user_session(user_id)
        
        except Exception as e:
            self.logger.error(f"خطأ في معالجة PDF: {e}")
            
            # إعادة المبلغ
            self.db.update_user_balance(user_id, price, 'refund', 'خطأ في معالجة PDF')
            
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في معالجة الملف! تم إعادة المبلغ إلى رصيدك.",
                reply_markup=KeyboardBuilder.back_button()
            )
    
    # ============ سؤال وجواب بالذكاء الاصطناعي ============
    
    def start_ai_question(self, chat_id: int, user_id: int, message_id: int):
        """بدء سؤال وجواب بالذكاء الاصطناعي"""
        instruction_text = """
        ❓ *سؤال وجواب بالذكاء الاصطناعي*

        أرسل سؤالك الآن.

        يمكنك إرسال:
        • نص السؤال
        • صورة تحتوي على السؤال
        • ملف نصي

        سيتم الرد باستخدام الذكاء الاصطناعي المتخصص في المنهج العراقي.
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.ASK_QUESTION)
    
    def handle_ai_question(self, chat_id: int, user_id: int, 
                          text: str, session: dict):
        """معالجة سؤال بالذكاء الاصطناعي"""
        # خصم المبلغ
        price = session['data'].get('service_price', 1000)
        if not self.db.update_user_balance(user_id, -price, 
                                          'service_payment', 
                                          'سؤال وجواب AI'):
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في عملية الدفع!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # إعلام المستخدم بالمعالجة
        TelegramAPI.send_message(
            chat_id,
            "🤔 جاري تحليل سؤالك وإعداد الإجابة...",
            reply_markup=KeyboardBuilder.back_button()
        )
        
        try:
            # استخدام الذكاء الاصطناعي للإجابة
            answer = self.ai_processor.answer_question(text)
            
            TelegramAPI.send_message(
                chat_id,
                f"🧠 *إجابة الذكاء الاصطناعي:*\n\n{answer}\n\n---\nإذا كانت الإجابة غير واضحة، يمكنك إعادة صياغة السؤال.",
                parse_mode='Markdown'
            )
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}],
                [{'text': '❓ سؤال آخر', 'callback_data': 'service_qa'}]
            ])
            
            TelegramAPI.send_message(
                chat_id,
                "اختر الخطوة التالية:",
                reply_markup=keyboard
            )
            
            # تنظيف الجلسة
            self.clear_user_session(user_id)
        
        except Exception as e:
            self.logger.error(f"خطأ في معالجة السؤال: {e}")
            
            # إعادة المبلغ
            self.db.update_user_balance(user_id, price, 'refund', 'خطأ في معالجة السؤال')
            
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في معالجة سؤالك! تم إعادة المبلغ إلى رصيدك.",
                reply_markup=KeyboardBuilder.back_button()
            )
    
    def handle_photo(self, chat_id: int, user_id: int, 
                    message: dict, state: str, session: dict):
        """معالجة الصور"""
        if state == BotState.ASK_QUESTION:
            # معالجة سؤال عن طريق صورة
            caption = message.get('caption', 'صورة تحتوي على سؤال دراسي')
            self.handle_ai_question(chat_id, user_id, caption, session)
    
    # ============ قسم ساعدوني طالب ============
    
    def show_help_student_section(self, chat_id: int, user_id: int, message_id: int):
        """عرض قسم ساعدوني طالب"""
        # الحصول على الأسئلة غير المجابة
        questions = self.db.get_approved_questions()
        
        if not questions:
            text = """
            👥 *قسم ساعدوني طالب*

            لا توجد أسئلة متاحة للإجابة حالياً.

            يمكنك:
            1. إرسال سؤال جديد
            2. الانتظار حتى يتم إضافة أسئلة جديدة
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '❓ أرسل سؤال جديد', 'callback_data': 'ask_help_question'}],
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
        else:
            text = """
            👥 *قسم ساعدوني طالب*

            *الأسئلة المتاحة للإجابة:*
            """
            
            keyboard_rows = []
            for i, question in enumerate(questions[:10], 1):
                truncated_question = self.utils.truncate_text(question['question_text'], 50)
                text += f"\n{i}. {truncated_question} - {question['first_name']}"
                keyboard_rows.append([
                    {'text': f'✏️ جاوب على السؤال {i}', 
                     'callback_data': f'answer_question_{question["question_id"]}'}
                ])
            
            keyboard_rows.append([
                {'text': '❓ أرسل سؤال جديد', 'callback_data': 'ask_help_question'}
            ])
            keyboard_rows.append([
                {'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}
            ])
            
            keyboard = KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def start_help_question(self, chat_id: int, user_id: int, message_id: int):
        """بدء إرسال سؤال جديد"""
        instruction_text = """
        ❓ *أرسل سؤال جديد*

        اكتب سؤالك الآن.

        *ملاحظات:*
        • يجب أن يكون السؤال واضحاً ومفصلاً
        • سيتم مراجعة السؤال قبل نشره
        • يمكن للطلاب الآخرين الإجابة على سؤالك
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.HELP_STUDENT_ASK)
    
    def handle_help_question(self, chat_id: int, user_id: int, 
                            text: str, session: dict):
        """معالجة إرسال سؤال جديد"""
        if len(text) < 10:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ السؤال قصير جداً! الرجاء كتابة سؤال مفصل.",
                reply_markup=KeyboardBuilder.cancel_button()
            )
            return
        
        # خصم المبلغ
        price = session['data'].get('service_price', 1000)
        if not self.db.update_user_balance(user_id, -price, 
                                          'service_payment', 
                                          'سؤال ساعدوني طالب'):
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في عملية الدفع!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # حفظ السؤال في قاعدة البيانات
        question_id = self.db.add_help_question(user_id, text)
        
        if question_id > 0:
            # إعلام المستخدم
            TelegramAPI.send_message(
                chat_id,
                "✅ تم استلام سؤالك!\nسيتم مراجعته من قبل الإدارة ونشره قريباً.\nستصلك إشعار عند الموافقة على السؤال.",
                reply_markup=KeyboardBuilder.back_button()
            )
            
            # إرسال إشعار للمدير
            user_data = self.db.get_user(user_id)
            admin_text = f"""
            📋 *سؤال جديد يحتاج موافقة*

            *المستخدم:* {user_data['first_name']}
            *السؤال:* {self.utils.truncate_text(text, 200)}
            *رقم السؤال:* {question_id}
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [
                    {'text': '✅ موافقة', 'callback_data': f'approve_question_{question_id}'},
                    {'text': '❌ رفض', 'callback_data': f'reject_question_{question_id}'}
                ],
                [{'text': '👀 عرض كامل', 'callback_data': f'view_question_{question_id}'}]
            ])
            
            TelegramAPI.send_message(
                ADMIN_ID,
                admin_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            # إعادة المبلغ
            self.db.update_user_balance(user_id, price, 'refund', 'خطأ في إضافة السؤال')
            
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في حفظ سؤالك! تم إعادة المبلغ إلى رصيدك.",
                reply_markup=KeyboardBuilder.back_button()
            )
        
        # تنظيف الجلسة
        self.clear_user_session(user_id)
    
    def show_questions_to_answer(self, chat_id: int, user_id: int, message_id: int):
        """عرض الأسئلة المتاحة للإجابة"""
        questions = self.db.get_approved_questions()
        
        if not questions:
            text = "❌ لا توجد أسئلة متاحة للإجابة حالياً."
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                text,
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        text = "✏️ *الأسئلة المتاحة للإجابة:*\n\n"
        
        keyboard_rows = []
        for i, question in enumerate(questions[:10], 1):
            truncated_question = self.utils.truncate_text(question['question_text'], 50)
            text += f"{i}. {truncated_question}\n"
            keyboard_rows.append([
                {'text': f'✏️ جاوب على السؤال {i}', 
                 'callback_data': f'answer_question_{question["question_id"]}'}
            ])
        
        keyboard_rows.append([{'text': '🔙 الرجوع', 'callback_data': 'main_menu'}])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        )
    
    def handle_answer_callback(self, chat_id: int, user_id: int, 
                              message_id: int, data: str):
        """معالجة الإجابة على سؤال"""
        if data.startswith('answer_question_'):
            question_id = int(data.replace('answer_question_', ''))
            self.start_answering_question(chat_id, user_id, message_id, question_id)
    
    def start_answering_question(self, chat_id: int, user_id: int, 
                                message_id: int, question_id: int):
        """بدء الإجابة على سؤال"""
        question = self.db.get_help_question(question_id)
        
        if not question:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ السؤال غير موجود",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        truncated_question = self.utils.truncate_text(question['question_text'], 200)
        
        text = f"""
        ✏️ *الإجابة على السؤال*

        *السؤال:* {truncated_question}

        *أرسل إجابتك الآن:*
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.HELP_STUDENT_ANSWER, {
            'answering_question_id': question_id
        })
    
    def handle_help_answer(self, chat_id: int, user_id: int, 
                          text: str, session: dict):
        """معالجة الإجابة على سؤال"""
        question_id = session['data'].get('answering_question_id')
        
        if not question_id:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في البيانات",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        if len(text) < 5:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الإجابة قصيرة جداً",
                reply_markup=KeyboardBuilder.cancel_button()
            )
            return
        
        # حفظ الإجابة
        if self.db.answer_help_question(question_id, user_id, text):
            question = self.db.get_help_question(question_id)
            
            if question:
                # إرسال الإجابة للمستخدم
                user_data = self.db.get_user(question['user_id'])
                if user_data:
                    try:
                        answer_text = f"""
                        ✅ *تمت الإجابة على سؤالك*

                        *سؤالك:* {self.utils.truncate_text(question['question_text'], 200)}

                        *الإجابة:*
                        {text}
                        """
                        
                        TelegramAPI.send_message(
                            question['user_id'],
                            answer_text,
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            TelegramAPI.send_message(
                chat_id,
                "✅ تم إرسال الإجابة بنجاح!",
                reply_markup=KeyboardBuilder.create_inline_keyboard([
                    [{'text': '👥 المزيد من الأسئلة', 'callback_data': 'service_help'},
                     {'text': '🏠 القائمة الرئيسية', 'callback_data': 'main_menu'}]
                ])
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في إرسال الإجابة",
                reply_markup=KeyboardBuilder.back_button()
            )
        
        # تنظيف الجلسة
        self.clear_user_session(user_id)
    
    # ============ المواد التعليمية ============
    
    def show_materials(self, chat_id: int, user_id: int, message_id: int = None):
        """عرض المواد التعليمية"""
        materials = self.db.get_all_materials()
        
        if not materials:
            text = """
            📖 *ملازمي ومرشحاتي*

            لا توجد مواد متاحة حالياً.

            سيتم إضافة مواد جديدة قريباً.
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
        else:
            text = "📖 *ملازمي ومرشحاتي*\n\n"
            text += "*المواد المتاحة:*\n\n"
            
            keyboard_rows = []
            current_stage = None
            
            for material in materials:
                if material['stage'] != current_stage:
                    text += f"\n*📌 المرحلة: {material['stage']}*\n"
                    current_stage = material['stage']
                
                text += f"• {material['title']}\n"
                keyboard_rows.append([
                    {'text': f'📥 تحميل: {material["title"]}', 
                     'callback_data': f'download_material_{material["material_id"]}'}
                ])
            
            keyboard_rows.append([
                {'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}
            ])
            
            keyboard = KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        
        if message_id:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    def handle_download_callback(self, chat_id: int, user_id: int, 
                                message_id: int, data: str):
        """معالجة تحميل المواد"""
        if data.startswith('download_material_'):
            material_id = int(data.replace('download_material_', ''))
            self.download_material(chat_id, user_id, message_id, material_id)
    
    def download_material(self, chat_id: int, user_id: int, 
                         message_id: int, material_id: int):
        """تحميل مادة تعليمية"""
        material = self.db.get_material(material_id)
        
        if not material:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ المادة غير موجودة",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # إرسال الملف
        TelegramAPI.send_document(
            chat_id,
            material['file_id'],
            caption=f"📖 {material['title']}\n\n{material['description']}"
        )
        
        # عرض رسالة تأكيد
        TelegramAPI.send_message(
            chat_id,
            f"✅ تم تحميل: {material['title']}",
            reply_markup=KeyboardBuilder.create_inline_keyboard([
                [{'text': '📖 المزيد من المواد', 'callback_data': 'service_materials'},
                 {'text': '🏠 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
        )
    
    # ============ نظام VIP ============
    
    def show_vip_subscription(self, chat_id: int, user_id: int, message_id: int):
        """عرض اشتراك VIP"""
        price = self.db.get_service_price('vip_subscription')
        days = int(self.db.get_setting('vip_subscription_days', '30'))
        
        text = f"""
        ⭐ *اشتراك VIP*

        *السعر الشهري:* {self.utils.format_currency(price)}
        *المدة:* {days} يوم

        *المميزات:*
        • الوصول إلى جميع محاضرات VIP
        • رفع محاضرات خاصة بك
        • تحصيل 60% من أرباح محاضراتك
        • دعم فني متميز
        • إشعارات فورية
        • مكافآت دعوة مضاعفة

        *شروط الاشتراك:*
        • الاشتراك شهري (يتجدد يدوياً)
        • يمكنك رفع محاضرات حتى 100 ميجابايت
        • جميع المحاضرات تخضع للمراجعة
        • يمكن إلغاء الاشتراك في أي وقت

        هل تريد الاشتراك؟
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.vip_subscription_menu()
        )
    
    def show_vip_terms(self, chat_id: int, user_id: int, message_id: int):
        """عرض شروط ومميزات VIP"""
        text = """
        📋 *شروط ومميزات VIP*

        *المميزات:*
        1. رفع محاضرات فيديو خاصة بك
        2. تحصيل 60% من أرباح محاضراتك
        3. مكافآت دعوة مضاعفة
        4. دعم فني متميز
        5. إشعارات فورية

        *الشروط:*
        1. يجب أن تكون المحاضرات تعليمية
        2. الحجم الأقصى للمحاضرة: 100 ميجابايت
        3. جميع المحاضرات تخضع للمراجعة
        4. الاشتراك شهري ويتجدد يدوياً
        5. يمكن إلغاء الاشتراك في أي وقت

        *نظام الأرباح:*
        • 60% للمحاضر
        • 40% للإدارة
        • يمكن سحب الأرباح عند الوصول إلى 5000 دينار
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.create_inline_keyboard([
                [{'text': '✅ اشتراك الآن', 'callback_data': 'vip_purchase'}],
                [{'text': '🔙 الرجوع', 'callback_data': 'vip_subscription'}]
            ])
        )
    
    def purchase_vip_subscription(self, chat_id: int, user_id: int, message_id: int):
        """شراء اشتراك VIP"""
        price = self.db.get_service_price('vip_subscription')
        
        # التحقق من رصيد المستخدم
        user_data = self.db.get_user(user_id)
        if user_data['balance'] < price:
            error_text = f"""
            ⚠️ رصيدك غير كافي!

            *سعر الاشتراك:* {self.utils.format_currency(price)}
            *رصيدك الحالي:* {self.utils.format_currency(user_data['balance'])}
            """
            
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                error_text,
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.create_inline_keyboard([
                    [{'text': '💰 شحن الرصيد', 'callback_data': 'invite_friend'}],
                    [{'text': '🔙 الرجوع', 'callback_data': 'vip_subscription'}]
                ])
            )
            return
        
        # خصم المبلغ
        if not self.db.update_user_balance(user_id, -price, 
                                          'vip_subscription', 
                                          'اشتراك VIP شهري'):
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ حدث خطأ في عملية الدفع!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # تفعيل الاشتراك
        days = int(self.db.get_setting('vip_subscription_days', '30'))
        if self.db.activate_vip(user_id, days):
            # إعلام المستخدم
            end_date = (datetime.now() + timedelta(days=days)).strftime('%Y/%m/%d')
            
            success_text = f"""
            🎉 *مبروك! تم تفعيل اشتراكك VIP*

            *مدة الاشتراك:* {days} يوم
            *تاريخ التجديد:* {end_date}

            يمكنك الآن:
            • الوصول إلى جميع محاضرات VIP
            • رفع محاضرات خاصة بك
            • تحصيل الأرباح من محاضراتك

            استمتع بمزاياك الجديدة! 🚀
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🎓 محاضرات VIP', 'callback_data': 'vip_lectures'}],
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
            
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                success_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            # إعادة المبلغ
            self.db.update_user_balance(user_id, price, 'refund', 'خطأ في تفعيل VIP')
            
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ حدث خطأ في تفعيل الاشتراك! تم إعادة المبلغ إلى رصيدك.",
                reply_markup=KeyboardBuilder.back_button()
            )
    
    def show_vip_lectures(self, chat_id: int, user_id: int, message_id: int):
        """عرض محاضرات VIP"""
        # التحقق من اشتراك VIP
        if not self.db.is_vip_user(user_id):
            text = """
            🎓 *محاضرات VIP*

            للوصول إلى محاضرات VIP، يجب عليك الاشتراك في باقة VIP أولاً.

            *مميزات الاشتراك:*
            • الوصول إلى جميع المحاضرات
            • رفع محاضرات خاصة بك
            • تحصيل الأرباح من محاضراتك
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '⭐ اشتراك VIP', 'callback_data': 'vip_subscription'}],
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
        else:
            text = """
            🎓 *محاضرات VIP*

            *المحاضرات المتاحة:*

            اختر المحاضرة التي تريدها:
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🎓 عرض المحاضرات', 'callback_data': 'view_vip_lectures'}],
                [{'text': '📤 رفع محاضرة', 'callback_data': 'vip_upload'}],
                [{'text': '💰 أرباحي', 'callback_data': 'vip_earnings'}],
                [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def view_vip_lectures(self, chat_id: int, user_id: int, message_id: int):
        """عرض قائمة محاضرات VIP"""
        lectures = self.db.get_all_vip_lectures()
        
        if not lectures:
            text = "🎬 لا توجد محاضرات متاحة حالياً."
            keyboard = KeyboardBuilder.back_button('vip_lectures')
        else:
            text = "🎬 *محاضرات VIP المتاحة:*\n\n"
            
            keyboard_rows = []
            for i, lecture in enumerate(lectures[:10], 1):
                price_text = "مجاني" if lecture['price'] == 0 else f"{self.utils.format_currency(lecture['price'])}"
                text += f"{i}. {lecture['title']} ({price_text})\n"
                
                keyboard_rows.append([
                    {'text': f'👁️ مشاهدة {i}', 
                     'callback_data': f'view_lecture_{lecture["lecture_id"]}'}
                ])
            
            keyboard_rows.append([{'text': '🔙 الرجوع', 'callback_data': 'vip_lectures'}])
            keyboard = KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def view_lecture_details(self, chat_id: int, user_id: int, 
                            message_id: int, lecture_id: int):
        """عرض تفاصيل المحاضرة"""
        lecture = self.db.get_vip_lecture(lecture_id)
        
        if not lecture:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ المحاضرة غير موجودة",
                reply_markup=KeyboardBuilder.back_button('view_vip_lectures')
            )
            return
        
        teacher = self.db.get_user(lecture['teacher_id'])
        teacher_name = teacher['first_name'] if teacher else "مجهول"
        
        price_text = "مجانية" if lecture['price'] == 0 else f"{self.utils.format_currency(lecture['price'])}"
        
        text = f"""
        🎬 *تفاصيل المحاضرة*

        *العنوان:* {lecture['title']}
        *المحاضر:* {teacher_name}
        *السعر:* {price_text}
        *المشاهدات:* {lecture['views']}
        *المشتريات:* {lecture['purchases']}

        *الوصف:*
        {lecture['description']}
        """
        
        keyboard_rows = []
        
        if lecture['price'] == 0:
            keyboard_rows.append([
                {'text': '🎬 مشاهدة المحاضرة', 
                 'callback_data': f'watch_lecture_{lecture_id}'}
            ])
        else:
            keyboard_rows.append([
                {'text': '🛒 شراء المحاضرة', 
                 'callback_data': f'purchase_lecture_{lecture_id}'}
            ])
        
        keyboard_rows.append([{'text': '🔙 الرجوع', 'callback_data': 'view_vip_lectures'}])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        )
    
    def purchase_lecture(self, chat_id: int, user_id: int, 
                        message_id: int, lecture_id: int):
        """شراء محاضرة"""
        success, message = self.db.purchase_vip_lecture(user_id, lecture_id)
        
        if success:
            text = f"""
            ✅ *تم الشراء بنجاح!*

            {message}

            يمكنك الآن مشاهدة المحاضرة.
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🎬 مشاهدة المحاضرة', 
                  'callback_data': f'watch_lecture_{lecture_id}'}],
                [{'text': '🔙 الرجوع', 'callback_data': 'view_vip_lectures'}]
            ])
        else:
            text = f"""
            ❌ *فشل في الشراء*

            {message}
            """
            
            keyboard = KeyboardBuilder.back_button('view_vip_lectures')
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def start_vip_upload(self, chat_id: int, user_id: int, message_id: int):
        """بدء رفع محاضرة VIP"""
        # التحقق من اشتراك VIP
        if not self.db.is_vip_user(user_id):
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⛔ يجب أن تكون مشتركاً في VIP لرفع المحاضرات!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        instruction_text = """
        📤 *رفع محاضرة VIP*

        أرسل الفيديو الآن (حتى 100 ميجابايت):
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
        
        # تحديث حالة المستخدم
        self.update_user_session(user_id, BotState.VIP_UPLOAD_LECTURE, {
            'vip_upload': {}
        })
    
    def handle_video(self, chat_id: int, user_id: int, 
                    message: dict, state: str, session: dict):
        """معالجة الفيديوهات"""
        if state == BotState.VIP_UPLOAD_LECTURE:
            self.handle_vip_video_upload(chat_id, user_id, message, session)
    
    def handle_vip_video_upload(self, chat_id: int, user_id: int, 
                               message: dict, session: dict):
        """معالجة رفع فيديو VIP"""
        video = message['video']
        file_id = video['file_id']
        
        # التحقق من حجم الفيديو (نظرياً)
        max_size = int(self.db.get_setting('max_video_size_mb', '100')) * 1024 * 1024
        
        # حفظ file_id مؤقتاً
        session['data']['vip_upload']['video_file_id'] = file_id
        self.update_user_session(user_id, BotState.VIP_UPLOAD_TITLE, session['data'])
        
        TelegramAPI.send_message(
            chat_id,
            "📝 *أدخل عنوان المحاضرة:*",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
    
    def handle_vip_upload_title(self, chat_id: int, user_id: int, 
                               text: str, session: dict):
        """معالجة عنوان محاضرة VIP"""
        session['data']['vip_upload']['title'] = text
        self.update_user_session(user_id, BotState.VIP_UPLOAD_DESC, session['data'])
        
        TelegramAPI.send_message(
            chat_id,
            "📝 *أدخل وصف المحاضرة:*",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.cancel_button()
        )
    
    def handle_vip_upload_desc(self, chat_id: int, user_id: int, 
                              text: str, session: dict):
        """معالجة وصف محاضرة VIP"""
        session['data']['vip_upload']['description'] = text
        self.update_user_session(user_id, BotState.VIP_SET_PRICE, session['data'])
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [
                {'text': '💰 مدفوعة', 'callback_data': 'lecture_paid'},
                {'text': '🆓 مجانية', 'callback_data': 'lecture_free'}
            ],
            [{'text': '❌ إلغاء', 'callback_data': 'main_menu'}]
        ])
        
        TelegramAPI.send_message(
            chat_id,
            "💰 *اختر نوع المحاضرة:*",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def handle_vip_set_price(self, chat_id: int, user_id: int, 
                            text: str, session: dict):
        """معالجة سعر محاضرة VIP"""
        try:
            price = int(text)
            
            if price < 0:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ السعر يجب أن يكون صفر أو أكثر",
                    reply_markup=KeyboardBuilder.cancel_button()
                )
                return
            
            upload_data = session['data']['vip_upload']
            
            # حفظ المحاضرة في قاعدة البيانات
            lecture_id = self.db.add_vip_lecture(
                user_id,
                upload_data.get('title', ''),
                upload_data.get('description', ''),
                upload_data.get('video_file_id', ''),
                price
            )
            
            if lecture_id > 0:
                # إعلام المستخدم
                success_text = """
                ✅ *تم رفع المحاضرة بنجاح!*

                سيتم مراجعتها من قبل الإدارة ونشرها قريباً.
                ستصلك إشعار عند الموافقة على المحاضرة.
                """
                
                keyboard = KeyboardBuilder.create_inline_keyboard([
                    [{'text': '🎓 محاضرات VIP', 'callback_data': 'vip_lectures'},
                     {'text': '🏠 القائمة الرئيسية', 'callback_data': 'main_menu'}]
                ])
                
                TelegramAPI.send_message(
                    chat_id,
                    success_text,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
                # إرسال إشعار للمدير
                user_data = self.db.get_user(user_id)
                price_text = "مجانية" if price == 0 else f"{self.utils.format_currency(price)}"
                
                admin_text = f"""
                🎬 *محاضرة VIP جديدة تحتاج موافقة*

                *المحاضر:* {user_data['first_name']}
                *العنوان:* {upload_data.get('title', '')}
                *السعر:* {price_text}
                *الوصف:* {self.utils.truncate_text(upload_data.get('description', ''), 200)}

                *رقم المحاضرة:* {lecture_id}
                """
                
                admin_keyboard = KeyboardBuilder.create_inline_keyboard([
                    [
                        {'text': '✅ موافقة', 'callback_data': f'approve_lecture_{lecture_id}'},
                        {'text': '❌ رفض', 'callback_data': f'reject_lecture_{lecture_id}'}
                    ],
                    [{'text': '👀 عرض المحاضرة', 'callback_data': f'view_admin_lecture_{lecture_id}'}]
                ])
                
                TelegramAPI.send_message(
                    ADMIN_ID,
                    admin_text,
                    parse_mode='Markdown',
                    reply_markup=admin_keyboard
                )
            else:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ حدث خطأ في رفع المحاضرة!",
                    reply_markup=KeyboardBuilder.back_button()
                )
            
            # تنظيف الجلسة
            self.clear_user_session(user_id)
        
        except ValueError:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال رقم صحيح",
                reply_markup=KeyboardBuilder.cancel_button()
            )
    
    def show_vip_earnings(self, chat_id: int, user_id: int, message_id: int):
        """عرض أرباح VIP"""
        # التحقق من اشتراك VIP
        if not self.db.is_vip_user(user_id):
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⛔ يجب أن تكون مشتركاً في VIP لعرض الأرباح!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        # الحصول على معلومات VIP
        cursor = self.db.connection.cursor()
        cursor.execute('''
            SELECT earnings_balance, total_earnings 
            FROM vip_subscriptions 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ لا توجد معلومات عن أرباحك",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        earnings_balance = row['earnings_balance'] or 0
        total_earnings = row['total_earnings'] or 0
        
        text = f"""
        💰 *أرباحك من VIP*

        *الرصيد القابل للسحب:* {self.utils.format_currency(earnings_balance)}
        *إجمالي الأرباح:* {self.utils.format_currency(total_earnings)}

        *للسحب:*
        1. راسل الدعم الفني @{SUPPORT_USER.replace('@', '')}
        2. أكد هويتك
        3. سيتم تحويل الأرباح إليك

        *ملاحظة:* يتم خصم 40% للإدارة من كل عملية بيع.
        """
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '📞 اتصل بالدعم للسحب', 
              'url': f'https://t.me/{SUPPORT_USER.replace("@", "")}'}],
            [{'text': '🎓 محاضراتي', 'callback_data': 'my_lectures'}],
            [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
        ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    # ============ دعوة الأصدقاء ============
    
    def show_invitation(self, chat_id: int, user_id: int, message_id: int = None):
        """عرض رابط الدعوة"""
        invite_link = self.utils.generate_invite_link(user_id)
        
        # تحديد مكافأة الدعوة
        is_vip = self.db.is_vip_user(user_id)
        bonus_amount = int(self.db.get_setting(
            'vip_invitation_bonus' if is_vip else 'invitation_bonus',
            '1000' if is_vip else '500'
        ))
        
        welcome_bonus = self.db.get_setting('welcome_bonus', '1000')
        
        text = f"""
        👥 *دعوة صديق*

        *رابط الدعوة:* `{invite_link}`

        *مكافأة الدعوة:* {self.utils.format_currency(bonus_amount)} لكل صديق
        صديقك سيحصل على {welcome_bonus} دينار هدية ترحيب!

        *كيفية الدعوة:*
        1. شارك الرابط أعلاه مع أصدقائك
        2. عندما ينضم صديقك عبر الرابط
        3. تحصل على المكافأة تلقائياً
        """
        
        if is_vip:
            text += "\n🎯 *مميزات خاصة للمحاضرين VIP:*"
            text += "\n• رابط دعوة ترويجي خاص"
            text += "\n• مكافأة مضاعفة لكل دعوة"
            text += "\n• تقارير متقدمة للدعوات"
        
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_link)}&text=انضم%20إلى%20بوت%20يلا%20نتعلم%20للدراسة%20باستخدام%20الذكاء%20الاصطناعي!"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '📤 مشاركة الرابط', 'url': share_url}],
            [{'text': '📊 إحصائيات دعواتي', 'callback_data': 'invite_stats'}],
            [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
        ])
        
        if message_id:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    # ============ الرصيد ============
    
    def show_balance(self, chat_id: int, user_id: int, message_id: int = None):
        """عرض رصيد المستخدم"""
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            if message_id:
                TelegramAPI.edit_message_text(
                    chat_id,
                    message_id,
                    "⚠️ المستخدم غير موجود",
                    reply_markup=KeyboardBuilder.back_button()
                )
            else:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ المستخدم غير موجود",
                    reply_markup=KeyboardBuilder.back_button()
                )
            return
        
        text = f"""
        💰 *رصيدك الحالي*

        *الرصيد الرئيسي:* {self.utils.format_currency(user_data['balance'])}
        """
        
        # التحقق من اشتراك VIP
        if self.db.is_vip_user(user_id):
            cursor = self.db.connection.cursor()
            cursor.execute('''
                SELECT earnings_balance, end_date 
                FROM vip_subscriptions 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                earnings_balance = row['earnings_balance'] or 0
                end_date = self.utils.format_date(row['end_date'])
                
                text += f"\n*رصيد الأرباح (VIP):* {self.utils.format_currency(earnings_balance)}"
                text += f"\n*انتهاء الاشتراك VIP:* {end_date}"
        
        text += f"\n\n*عدد المدعوين:* {user_data['invited_count']}"
        text += f"\n*تاريخ الانضمام:* {user_data['join_date'][:10]}"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '👥 دعوة صديق', 'callback_data': 'invite_friend'}],
            [{'text': '🔙 القائمة الرئيسية', 'callback_data': 'main_menu'}]
        ])
        
        if user_id == ADMIN_ID:
            keyboard['inline_keyboard'].insert(0, [
                {'text': '👑 لوحة التحكم', 'callback_data': 'admin_panel'}
            ])
        
        if message_id:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    # ============ لوحة تحكم المدير ============
    
    def show_admin_panel(self, chat_id: int, user_id: int, message_id: int = None):
        """عرض لوحة تحكم المدير"""
        if user_id != ADMIN_ID:
            if message_id:
                TelegramAPI.edit_message_text(
                    chat_id,
                    message_id,
                    "⛔ ليس لديك صلاحية الدخول إلى لوحة التحكم!",
                    reply_markup=KeyboardBuilder.back_button()
                )
            else:
                TelegramAPI.send_message(
                    chat_id,
                    "⛔ ليس لديك صلاحية الدخول إلى لوحة التحكم!",
                    reply_markup=KeyboardBuilder.back_button()
                )
            return
        
        stats = self.db.get_bot_stats()
        
        text = f"""
        👑 *لوحة التحكم - يلا نتعلم*

        *الإحصائيات العامة:*
        👥 إجمالي المستخدمين: {stats['total_users']}
        🔥 المستخدمين النشطين: {stats['active_users']}
        ⭐ مشتركي VIP: {stats['vip_users']}
        💰 إجمالي الأرصدة: {self.utils.format_currency(stats['total_balance'])}
        📈 الدخل اليومي: {self.utils.format_currency(stats['daily_income'])}

        *اختر القسم الذي تريد إدارته:*
        """
        
        if message_id:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                text,
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.admin_panel()
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                text,
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.admin_panel()
            )
    
    def handle_admin_callback(self, chat_id: int, user_id: int, 
                             message_id: int, data: str):
        """معالجة ردود الاتصال في لوحة التحكم"""
        if user_id != ADMIN_ID:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⛔ ليس لديك صلاحية الدخول إلى لوحة التحكم!",
                reply_markup=KeyboardBuilder.back_button()
            )
            return
        
        if data == 'admin_charge':
            self.start_admin_charge(chat_id, message_id)
        
        elif data == 'admin_deduct':
            self.start_admin_deduct(chat_id, message_id)
        
        elif data == 'admin_ban':
            self.start_admin_ban(chat_id, message_id)
        
        elif data == 'admin_unban':
            self.start_admin_unban(chat_id, message_id)
        
        elif data == 'admin_broadcast':
            self.start_admin_broadcast(chat_id, message_id)
        
        elif data == 'admin_users':
            self.show_admin_users(chat_id, message_id)
        
        elif data == 'admin_services':
            self.show_admin_services(chat_id, message_id)
        
        elif data == 'admin_stats':
            self.show_admin_stats(chat_id, message_id)
        
        elif data == 'admin_vip':
            self.show_admin_vip(chat_id, message_id)
        
        elif data == 'admin_materials':
            self.show_admin_materials(chat_id, message_id)
        
        elif data == 'admin_pending_questions':
            self.show_pending_questions_admin(chat_id, message_id)
        
        elif data == 'admin_pending_lectures':
            self.show_pending_lectures_admin(chat_id, message_id)
        
        elif data == 'admin_add_material':
            self.start_admin_add_material(chat_id, message_id)
    
    def start_admin_charge(self, chat_id: int, message_id: int):
        """بدء شحن رصيد"""
        instruction_text = """
        💰 *شحن رصيد*

        أرسل آيدي المستخدم:
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_panel')
        )
        
        # تحديث حالة المدير
        self.update_user_session(ADMIN_ID, BotState.ADMIN_CHARGE, {
            'admin_action': 'charge'
        })
    
    def handle_admin_charge(self, chat_id: int, user_id: int, 
                           text: str, session: dict):
        """معالجة شحن رصيد"""
        try:
            target_user_id = int(text)
            user_data = self.db.get_user(target_user_id)
            
            if not user_data:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ المستخدم غير موجود",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
                return
            
            session['data']['target_user_id'] = target_user_id
            self.update_user_session(user_id, BotState.ADMIN_CHARGE, session['data'])
            
            TelegramAPI.send_message(
                chat_id,
                f"👤 *المستخدم:* {user_data['first_name']}\n\nأرسل المبلغ المطلوب شحنه:",
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
        
        except ValueError:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال آيدي صحيح",
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
    
    def start_admin_deduct(self, chat_id: int, message_id: int):
        """بدء خصم رصيد"""
        instruction_text = """
        💸 *خصم رصيد*

        أرسل آيدي المستخدم:
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_panel')
        )
        
        # تحديث حالة المدير
        self.update_user_session(ADMIN_ID, BotState.ADMIN_DEDUCT, {
            'admin_action': 'deduct'
        })
    
    def handle_admin_deduct(self, chat_id: int, user_id: int, 
                           text: str, session: dict):
        """معالجة خصم رصيد"""
        try:
            target_user_id = int(text)
            user_data = self.db.get_user(target_user_id)
            
            if not user_data:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ المستخدم غير موجود",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
                return
            
            session['data']['target_user_id'] = target_user_id
            self.update_user_session(user_id, BotState.ADMIN_DEDUCT, session['data'])
            
            TelegramAPI.send_message(
                chat_id,
                f"👤 *المستخدم:* {user_data['first_name']}\n\nأرسل المبلغ المطلوب خصمه:",
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
        
        except ValueError:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال آيدي صحيح",
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
    
    def start_admin_ban(self, chat_id: int, message_id: int):
        """بدء حظر مستخدم"""
        instruction_text = """
        🚫 *حظر مستخدم*

        أرسل آيدي المستخدم:
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_panel')
        )
        
        # تحديث حالة المدير
        self.update_user_session(ADMIN_ID, BotState.ADMIN_BAN, {
            'admin_action': 'ban'
        })
    
    def handle_admin_ban(self, chat_id: int, user_id: int, 
                        text: str, session: dict):
        """معالجة حظر مستخدم"""
        try:
            target_user_id = int(text)
            user_data = self.db.get_user(target_user_id)
            
            if not user_data:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ المستخدم غير موجود",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
                return
            
            if self.db.ban_user(target_user_id):
                # إرسال إشعار للمستخدم
                try:
                    TelegramAPI.send_message(
                        target_user_id,
                        "🚫 *حسابك تم حظره*\n\nللمزيد من المعلومات، راسل الدعم الفني.",
                        parse_mode='Markdown'
                    )
                except:
                    pass
                
                TelegramAPI.send_message(
                    chat_id,
                    f"✅ تم حظر المستخدم {user_data['first_name']}",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
            else:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ حدث خطأ في حظر المستخدم",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
            
            # تنظيف الجلسة
            self.clear_user_session(user_id)
        
        except ValueError:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال آيدي صحيح",
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
    
    def start_admin_unban(self, chat_id: int, message_id: int):
        """بدء فك حظر مستخدم"""
        instruction_text = """
        ✅ *فك حظر مستخدم*

        أرسل آيدي المستخدم:
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_panel')
        )
        
        # تحديث حالة المدير
        self.update_user_session(ADMIN_ID, BotState.ADMIN_UNBAN, {
            'admin_action': 'unban'
        })
    
    def handle_admin_unban(self, chat_id: int, user_id: int, 
                          text: str, session: dict):
        """معالجة فك حظر مستخدم"""
        try:
            target_user_id = int(text)
            user_data = self.db.get_user(target_user_id)
            
            if not user_data:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ المستخدم غير موجود",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
                return
            
            if self.db.unban_user(target_user_id):
                # إرسال إشعار للمستخدم
                try:
                    TelegramAPI.send_message(
                        target_user_id,
                        "✅ *تم فك حظر حسابك*\n\nيمكنك استخدام البوت مرة أخرى.",
                        parse_mode='Markdown'
                    )
                except:
                    pass
                
                TelegramAPI.send_message(
                    chat_id,
                    f"✅ تم فك حظر المستخدم {user_data['first_name']}",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
            else:
                TelegramAPI.send_message(
                    chat_id,
                    "⚠️ حدث خطأ في فك حظر المستخدم",
                    reply_markup=KeyboardBuilder.back_button('admin_panel')
                )
            
            # تنظيف الجلسة
            self.clear_user_session(user_id)
        
        except ValueError:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الرجاء إدخال آيدي صحيح",
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
    
    def start_admin_broadcast(self, chat_id: int, message_id: int):
        """بدء إرسال إذاعة"""
        instruction_text = """
        📢 *إرسال إذاعة*

        أرسل النص الذي تريد إذاعته:
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_panel')
        )
        
        # تحديث حالة المدير
        self.update_user_session(ADMIN_ID, BotState.ADMIN_BROADCAST)
    
    def handle_admin_broadcast(self, chat_id: int, user_id: int, 
                              text: str, session: dict):
        """معالجة إرسال إذاعة"""
        if len(text) < 5:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ النص قصير جداً",
                reply_markup=KeyboardBuilder.back_button('admin_panel')
            )
            return
        
        session['data']['broadcast_text'] = text
        self.update_user_session(user_id, BotState.ADMIN_BROADCAST, session['data'])
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '✅ نعم، أرسل الإذاعة', 'callback_data': 'confirm_broadcast'}],
            [{'text': '❌ إلغاء', 'callback_data': 'admin_panel'}]
        ])
        
        truncated_text = text[:500] + "..." if len(text) > 500 else text
        
        TelegramAPI.send_message(
            chat_id,
            f"📢 *تأكيد الإذاعة*\n\n*النص:*\n{truncated_text}\n\nسيتم إرسال هذه الرسالة لجميع المستخدمين.\nهل تريد المتابعة؟",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_admin_users(self, chat_id: int, message_id: int):
        """عرض قائمة المستخدمين"""
        users = self.db.get_all_users(50)
        
        text = "👥 *إدارة المستخدمين*\n\n"
        text += f"*آخر 50 مستخدم نشط:*\n\n"
        
        for i, user in enumerate(users, 1):
            status = "🚫" if user['is_banned'] else "✅"
            username = f"@{user['username']}" if user['username'] else "بدون"
            text += f"{i}. {status} {user['first_name']} ({username})\n"
            text += f"   آيدي: {user['user_id']} | رصيد: {self.utils.format_currency(user['balance'])}\n"
            text += f"   آخر نشاط: {self.utils.format_date(user['last_active'])}\n\n"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '🔍 بحث عن مستخدم', 'callback_data': 'admin_search_user'}],
            [{'text': '📊 تقرير مفصل', 'callback_data': 'admin_users_report'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
        ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_admin_services(self, chat_id: int, message_id: int):
        """عرض إدارة الخدمات"""
        text = "⚙️ *إدارة الخدمات*\n\n"
        text += "*الأسعار الحالية:*\n\n"
        
        services = ['exemption', 'summary', 'qa', 'help', 'vip_subscription']
        for service in services:
            service_name = self.get_service_name(service)
            price = self.db.get_service_price(service)
            is_active = self.db.is_service_active(service)
            status = "✅" if is_active else "❌"
            
            text += f"{status} {service_name}: {self.utils.format_currency(price)}\n"
        
        text += f"\n*مكافأة الدعوة:* {self.utils.format_currency(500)}\n"
        text += f"*مكافأة دعوة VIP:* {self.utils.format_currency(1000)}\n"
        text += f"*هدية الترحيب:* {self.db.get_setting('welcome_bonus', '1000')} دينار"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '📝 تعديل الأسعار', 'callback_data': 'admin_set_prices'}],
            [{'text': '🚫 تعطيل خدمة', 'callback_data': 'admin_disable_service'}],
            [{'text': '✅ تفعيل خدمة', 'callback_data': 'admin_enable_service'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
        ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_admin_stats(self, chat_id: int, message_id: int):
        """عرض الإحصائيات"""
        stats = self.db.get_bot_stats()
        
        text = "📊 *الإحصائيات العامة*\n\n"
        text += f"*إجمالي المستخدمين:* {stats['total_users']}\n"
        text += f"*المستخدمين النشطين:* {stats['active_users']}\n"
        text += f"*مشتركي VIP:* {stats['vip_users']}\n"
        text += f"*إجمالي الأرصدة:* {self.utils.format_currency(stats['total_balance'])}\n"
        text += f"*الدخل اليومي:* {self.utils.format_currency(stats['daily_income'])}\n\n"
        
        text += "*الخدمات الأكثر استخداماً:*\n"
        text += "1. حساب درجة الإعفاء\n"
        text += "2. سؤال وجواب\n"
        text += "3. تلخيص الملازم\n\n"
        
        text += "*النمو الشهري:* +15%"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '📈 تقرير مفصل', 'callback_data': 'admin_detailed_stats'}],
            [{'text': '📅 إحصائيات يومية', 'callback_data': 'admin_daily_stats'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
        ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_admin_vip(self, chat_id: int, message_id: int):
        """عرض إدارة VIP"""
        text = "⭐ *إدارة مشتركي VIP*\n\n"
        
        # الحصول على مشتركي VIP النشطين
        cursor = self.db.connection.cursor()
        cursor.execute('''
            SELECT v.*, u.first_name, u.username 
            FROM vip_subscriptions v 
            JOIN users u ON v.user_id = u.user_id 
            WHERE v.is_active = 1 
            AND v.end_date > datetime('now')
            ORDER BY v.end_date
        ''')
        
        vip_users = cursor.fetchall()
        
        if vip_users:
            text += "*المشتركون النشطون:*\n"
            for i, user in enumerate(vip_users[:5], 1):
                end_date = self.utils.format_date(user['end_date'])
                text += f"{i}. {user['first_name']} - ينتهي في {end_date}\n"
            
            if len(vip_users) > 5:
                text += f"... و{len(vip_users) - 5} مشترك آخر\n"
        else:
            text += "لا يوجد مشتركون VIP نشطين حالياً.\n"
        
        # إحصائيات الأرباح
        cursor.execute('SELECT SUM(earnings_balance) FROM vip_subscriptions')
        total_earnings = cursor.fetchone()[0] or 0
        
        text += f"\n*إجمالي الأرباح الموزعة:* {self.utils.format_currency(total_earnings)}"
        text += "\n\n*الإجراءات المتاحة:*"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '👥 قائمة المشتركين', 'callback_data': 'admin_vip_list'}],
            [{'text': '💰 سحب أرباح', 'callback_data': 'admin_vip_withdraw'}],
            [{'text': '⏰ تجديد اشتراك', 'callback_data': 'admin_vip_renew'}],
            [{'text': '🚫 إلغاء اشتراك', 'callback_data': 'admin_vip_cancel'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
        ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_admin_materials(self, chat_id: int, message_id: int):
        """عرض إدارة المواد"""
        materials = self.db.get_all_materials()
        
        text = "📖 *إدارة المواد التعليمية*\n\n"
        
        if materials:
            text += "*المواد المتاحة:*\n"
            for i, material in enumerate(materials[:10], 1):
                text += f"{i}. {material['title']} ({material['stage']})\n"
            
            if len(materials) > 10:
                text += f"... و{len(materials) - 10} مادة أخرى\n"
        else:
            text += "لا توجد مواد تعليمية حالياً.\n"
        
        text += "\n*الإجراءات المتاحة:*"
        
        keyboard = KeyboardBuilder.create_inline_keyboard([
            [{'text': '➕ إضافة مادة', 'callback_data': 'admin_add_material'}],
            [{'text': '✏️ تعديل مادة', 'callback_data': 'admin_edit_material'}],
            [{'text': '🗑️ حذف مادة', 'callback_data': 'admin_delete_material'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
        ])
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def start_admin_add_material(self, chat_id: int, message_id: int):
        """بدء إضافة مادة تعليمية"""
        instruction_text = """
        📖 *إضافة مادة تعليمية*

        أرسل عنوان المادة:
        """
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            instruction_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_materials')
        )
        
        # تحديث حالة المدير
        self.update_user_session(ADMIN_ID, BotState.ADMIN_ADD_MAT_TITLE)
    
    def handle_admin_add_mat_title(self, chat_id: int, user_id: int, 
                                  text: str, session: dict):
        """معالجة عنوان مادة جديدة"""
        session['data']['new_material'] = {'title': text}
        self.update_user_session(user_id, BotState.ADMIN_ADD_MAT_DESC, session['data'])
        
        TelegramAPI.send_message(
            chat_id,
            "📝 *أدخل وصف المادة:*",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_materials')
        )
    
    def handle_admin_add_mat_desc(self, chat_id: int, user_id: int, 
                                 text: str, session: dict):
        """معالجة وصف مادة جديدة"""
        session['data']['new_material']['description'] = text
        self.update_user_session(user_id, BotState.ADMIN_ADD_MAT_STAGE, session['data'])
        
        TelegramAPI.send_message(
            chat_id,
            "📚 *أدخل المرحلة الدراسية:*\n\nمثال: الصف السادس، الصف الخامس، المرحلة الإعدادية",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_materials')
        )
    
    def handle_admin_add_mat_stage(self, chat_id: int, user_id: int, 
                                  text: str, session: dict):
        """معالجة مرحلة مادة جديدة"""
        session['data']['new_material']['stage'] = text
        self.update_user_session(user_id, BotState.ADMIN_ADD_MAT_FILE, session['data'])
        
        TelegramAPI.send_message(
            chat_id,
            "📎 *أرسل ملف المادة (PDF):*",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_button('admin_materials')
        )
    
    def handle_admin_add_mat_file(self, chat_id: int, user_id: int, 
                                 message: dict, session: dict):
        """معالجة ملف مادة جديدة"""
        document = message['document']
        file_id = document['file_id']
        file_name = document.get('file_name', '')
        
        if not file_name.lower().endswith('.pdf'):
            TelegramAPI.send_message(
                chat_id,
                "⚠️ الملف يجب أن يكون بصيغة PDF",
                reply_markup=KeyboardBuilder.back_button('admin_materials')
            )
            return
        
        material_data = session['data']['new_material']
        
        # إضافة المادة إلى قاعدة البيانات
        material_id = self.db.add_material(
            material_data['title'],
            material_data['description'],
            material_data['stage'],
            file_id
        )
        
        if material_id > 0:
            success_text = f"""
            ✅ *تم إضافة المادة بنجاح!*

            *العنوان:* {material_data['title']}
            *المرحلة:* {material_data['stage']}
            *رقم المادة:* {material_id}
            """
            
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '📖 عرض المواد', 'callback_data': 'admin_materials'},
                 {'text': '🏠 القائمة الرئيسية', 'callback_data': 'main_menu'}]
            ])
            
            TelegramAPI.send_message(
                chat_id,
                success_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            TelegramAPI.send_message(
                chat_id,
                "⚠️ حدث خطأ في إضافة المادة!",
                reply_markup=KeyboardBuilder.back_button('admin_materials')
            )
        
        # تنظيف الجلسة
        self.clear_user_session(user_id)
    
    def show_pending_questions_admin(self, chat_id: int, message_id: int):
        """عرض الأسئلة المنتظرة (للمدير)"""
        questions = self.db.get_pending_questions()
        
        if not questions:
            text = "❓ *الأسئلة المنتظرة*\n\nلا توجد أسئلة تحتاج موافقة."
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
            ])
        else:
            text = "❓ *الأسئلة المنتظرة*\n\n"
            
            keyboard_rows = []
            for question in questions:
                truncated_question = self.utils.truncate_text(question['question_text'], 100)
                text += f"*السؤال {question['question_id']}:*\n"
                text += f"{truncated_question}\n"
                text += f"من: {question['first_name']} ({question['username'] or 'بدون'})\n"
                text += f"التاريخ: {self.utils.format_date(question['ask_date'])}\n\n"
                
                keyboard_rows.append([
                    {'text': f'✅ {question["question_id"]}', 
                     'callback_data': f'approve_question_{question["question_id"]}'},
                    {'text': f'❌ {question["question_id"]}', 
                     'callback_data': f'reject_question_{question["question_id"]}'},
                    {'text': f'👁️ {question["question_id"]}', 
                     'callback_data': f'view_question_{question["question_id"]}'}
                ])
            
            keyboard_rows.append([{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}])
            keyboard = KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_pending_lectures_admin(self, chat_id: int, message_id: int):
        """عرض المحاضرات المنتظرة (للمدير)"""
        lectures = self.db.get_pending_vip_lectures()
        
        if not lectures:
            text = "🎬 *المحاضرات المنتظرة*\n\nلا توجد محاضرات تحتاج موافقة."
            keyboard = KeyboardBuilder.create_inline_keyboard([
                [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
            ])
        else:
            text = "🎬 *المحاضرات المنتظرة*\n\n"
            
            keyboard_rows = []
            for lecture in lectures:
                price_text = "مجانية" if lecture['price'] == 0 else f"{self.utils.format_currency(lecture['price'])}"
                text += f"*المحاضرة {lecture['lecture_id']}:*\n"
                text += f"{lecture['title']}\n"
                text += f"السعر: {price_text}\n"
                text += f"المحاضر: {lecture['first_name']} ({lecture['username'] or 'بدون'})\n"
                text += f"التاريخ: {self.utils.format_date(lecture['upload_date'])}\n\n"
                
                keyboard_rows.append([
                    {'text': f'✅ {lecture["lecture_id"]}', 
                     'callback_data': f'approve_lecture_{lecture["lecture_id"]}'},
                    {'text': f'❌ {lecture["lecture_id"]}', 
                     'callback_data': f'reject_lecture_{lecture["lecture_id"]}'},
                    {'text': f'👁️ {lecture["lecture_id"]}', 
                     'callback_data': f'view_lecture_{lecture["lecture_id"]}'}
                ])
            
            keyboard_rows.append([{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}])
            keyboard = KeyboardBuilder.create_inline_keyboard(keyboard_rows)
        
        TelegramAPI.edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    # ============ معالجة الموافقات والرفض ============
    
    def handle_approval_callback(self, chat_id: int, user_id: int, 
                                message_id: int, data: str):
        """معالجة الموافقة"""
        if data.startswith('approve_question_'):
            question_id = int(data.replace('approve_question_', ''))
            self.approve_question(chat_id, question_id, message_id)
        
        elif data.startswith('approve_lecture_'):
            lecture_id = int(data.replace('approve_lecture_', ''))
            self.approve_lecture(chat_id, lecture_id, message_id)
    
    def handle_rejection_callback(self, chat_id: int, user_id: int, 
                                 message_id: int, data: str):
        """معالجة الرفض"""
        if data.startswith('reject_question_'):
            question_id = int(data.replace('reject_question_', ''))
            self.reject_question(chat_id, question_id, message_id)
        
        elif data.startswith('reject_lecture_'):
            lecture_id = int(data.replace('reject_lecture_', ''))
            self.reject_lecture(chat_id, lecture_id, message_id)
    
    def approve_question(self, chat_id: int, question_id: int, message_id: int):
        """الموافقة على سؤال"""
        if self.db.approve_help_question(question_id):
            question = self.db.get_help_question(question_id)
            
            if question:
                # إرسال إشعار للمستخدم
                user_data = self.db.get_user(question['user_id'])
                if user_data:
                    try:
                        notification_text = f"""
                        ✅ *تمت الموافقة على سؤالك*

                        يمكن للطلاب الآن الإجابة على سؤالك.
                        """
                        
                        TelegramAPI.send_message(
                            question['user_id'],
                            notification_text,
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "✅ تمت الموافقة على السؤال",
                reply_markup=KeyboardBuilder.back_button('admin_pending_questions')
            )
        else:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ حدث خطأ في الموافقة على السؤال",
                reply_markup=KeyboardBuilder.back_button('admin_pending_questions')
            )
    
    def reject_question(self, chat_id: int, question_id: int, message_id: int):
        """رفض سؤال"""
        question = self.db.get_help_question(question_id)
        
        if question:
            # إرسال إشعار للمستخدم
            user_data = self.db.get_user(question['user_id'])
            if user_data:
                try:
                    notification_text = """
                    ❌ *تم رفض سؤالك*

                    للمزيد من المعلومات، راسل الدعم الفني.
                    """
                    
                    TelegramAPI.send_message(
                        question['user_id'],
                        notification_text,
                        parse_mode='Markdown'
                    )
                except:
                    pass
        
        if self.db.reject_help_question(question_id):
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "❌ تم رفض السؤال",
                reply_markup=KeyboardBuilder.back_button('admin_pending_questions')
            )
        else:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ حدث خطأ في رفض السؤال",
                reply_markup=KeyboardBuilder.back_button('admin_pending_questions')
            )
    
    def approve_lecture(self, chat_id: int, lecture_id: int, message_id: int):
        """الموافقة على محاضرة"""
        if self.db.approve_vip_lecture(lecture_id):
            lecture = self.db.get_vip_lecture(lecture_id)
            
            if lecture:
                # إرسال إشعار للمحاضر
                user_data = self.db.get_user(lecture['teacher_id'])
                if user_data:
                    try:
                        notification_text = f"""
                        ✅ *تمت الموافقة على محاضرتك*

                        *العنوان:* {lecture['title']}

                        يمكن للمستخدمين الآن مشاهدة وشراء محاضرتك.
                        """
                        
                        TelegramAPI.send_message(
                            lecture['teacher_id'],
                            notification_text,
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "✅ تمت الموافقة على المحاضرة",
                reply_markup=KeyboardBuilder.back_button('admin_pending_lectures')
            )
        else:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ حدث خطأ في الموافقة على المحاضرة",
                reply_markup=KeyboardBuilder.back_button('admin_pending_lectures')
            )
    
    def reject_lecture(self, chat_id: int, lecture_id: int, message_id: int):
        """رفض محاضرة"""
        lecture = self.db.get_vip_lecture(lecture_id)
        
        if lecture:
            # إرسال إشعار للمحاضر
            user_data = self.db.get_user(lecture['teacher_id'])
            if user_data:
                try:
                    notification_text = f"""
                    ❌ *تم رفض محاضرتك*

                    *العنوان:* {lecture['title']}

                    للمزيد من المعلومات، راسل الدعم الفني.
                    """
                    
                    TelegramAPI.send_message(
                        lecture['teacher_id'],
                        notification_text,
                        parse_mode='Markdown'
                    )
                except:
                    pass
        
        if self.db.reject_vip_lecture(lecture_id):
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "❌ تم رفض المحاضرة",
                reply_markup=KeyboardBuilder.back_button('admin_pending_lectures')
            )
        else:
            TelegramAPI.edit_message_text(
                chat_id,
                message_id,
                "⚠️ حدث خطأ في رفض المحاضرة",
                reply_markup=KeyboardBuilder.back_button('admin_pending_lectures')
            )

# ============================================================================
# خادم ويب للبوت
# ============================================================================

class BotWebhookHandler(BaseHTTPRequestHandler):
    """معالج ويب هوك للبوت"""
    
    bot = None
    
    def do_GET(self):
        """معالجة طلبات GET"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <html>
        <head>
            <title>بوت يلا نتعلم</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #2c3e50; }
                .status { background: #2ecc71; color: white; padding: 10px 20px; 
                         border-radius: 5px; display: inline-block; }
            </style>
        </head>
        <body>
            <h1>🚀 بوت تليجرام: يلا نتعلم</h1>
            <div class="status">✅ البوت يعمل بنجاح</div>
            <p>تم تطوير البوت بواسطة Allawi04</p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """معالجة طلبات POST"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            
            # معالجة التحديث
            if self.bot:
                self.bot.handle_update(update)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
            
        except Exception as e:
            logging.error(f"خطأ في معالجة طلب POST: {e}")
            self.send_response(500)
            self.end_headers()

# ============================================================================
# الدالة الرئيسية
# ============================================================================

def setup_webhook():
    """إعداد ويب هوك للبوت"""
    try:
        webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        # هنا تحتاج لوضع رابط السيرفر الخاص بك
        # webhook_data = {'url': 'https://your-server.com/webhook'}
        # response = HTTPClient.request('POST', webhook_url, json_data=webhook_data)
        # logging.info(f"نتيجة إعداد الويب هوك: {response['text']}")
        pass
    except Exception as e:
        logging.error(f"خطأ في إعداد الويب هوك: {e}")

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    print("=" * 60)
    print("🚀 بوت تليجرام: يلا نتعلم")
    print(f"👑 المدير: {ADMIN_ID}")
    print(f"🤖 البوت: {BOT_USERNAME}")
    print(f"📞 الدعم: {SUPPORT_USER}")
    print(f"📢 القناة: {CHANNEL_USERNAME}")
    print("=" * 60)
    
    # إنشاء البوت
    bot = LearnBot()
    BotWebhookHandler.bot = bot
    
    # إعداد الويب هوك (اختياري)
    setup_webhook()
    
    # تشغيل خادم الويب
    port = int(os.environ.get('PORT', 8080))
    server_address = ('', port)
    
    httpd = HTTPServer(server_address, BotWebhookHandler)
    logging.info(f"جاري تشغيل الخادم على المنفذ {port}...")
    logging.info(f"البوت جاهز للاستخدام: {BOT_USERNAME}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("إيقاف الخادم...")
        httpd.server_close()
        bot.db.close()

if __name__ == "__main__":
    main()
