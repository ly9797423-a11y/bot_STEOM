#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام: يلا نتعلم - الإصدار المحسّن
مطور البوت: @Allawi04
"""

# ====================== المكتبات المطلوبة ======================
import os
import sys
import json
import sqlite3
import logging
import tempfile
import hashlib
import time
import datetime
import re
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
import requests
from io import BytesIO
import base64
import random
import string
import asyncio
import traceback

# مكتبات تليجرام
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, InputFile,
    InputMediaDocument, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import TelegramError, BadRequest

# مكتبات معالجة PDF
try:
    import pypdf as PyPDF2
    PYPDF2_SUPPORT = True
except ImportError:
    try:
        import PyPDF2
        PYPDF2_SUPPORT = True
    except ImportError:
        PYPDF2_SUPPORT = False

import io
import textwrap

# ====================== إعدادات البوت ======================
BOT_TOKEN = "8279341291:AAGet-xHKrmSg1RuBYaaNuzmaqv1LgwUM6E"
ADMIN_ID = 6130994941
BOT_USERNAME = "SSDDFmakBOT"
SUPPORT_USERNAME = "@Allawi04"
CHANNEL_USERNAME = "@FCJCV"

# إعدادات API الذكاء الاصطناعي
GEMINI_API_KEY = "AIzaSyARsl_YMXA74bPQpJduu0jJVuaku7MaHuY"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# إعدادات المحادثة
CALC_GRADE1, CALC_GRADE2, CALC_GRADE3 = range(3)
PDF_SUMMARY = 1
ASK_QUESTION, ANSWER_QUESTION = range(2, 4)
VIP_LECTURE_TITLE, VIP_LECTURE_DESC, VIP_LECTURE_PRICE, VIP_LECTURE_FILE = range(4, 8)
ADMIN_CHARGE_USER, ADMIN_CHARGE_AMOUNT = range(8, 10)
ADMIN_DEDUCT_USER, ADMIN_DEDUCT_AMOUNT = range(10, 12)
ADMIN_VIP_DEDUCT_USER, ADMIN_VIP_DEDUCT_AMOUNT = range(12, 14)
ADMIN_CHANGE_PRICE = 14
ADMIN_BROADCAST = 15
ADMIN_ADD_MATERIAL_TITLE, ADMIN_ADD_MATERIAL_DESC, ADMIN_ADD_MATERIAL_STAGE, ADMIN_ADD_MATERIAL_FILE = range(16, 20)
ADMIN_UPDATE_INVITE_REWARD = 20
ADMIN_UPDATE_SERVICE_PRICE = 21
ADMIN_VIEW_QUESTIONS = 22
ADMIN_ANSWER_QUESTION = 23

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_logs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ====================== قاعدة البيانات المحسنة ======================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('yalla_nt3lm.db', check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.init_default_data()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance INTEGER DEFAULT 1000,
            invited_by INTEGER DEFAULT 0,
            invite_code TEXT UNIQUE,
            is_banned INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_vip INTEGER DEFAULT 0,
            vip_expiry TIMESTAMP,
            total_invites INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول العمليات المالية
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            service TEXT,
            description TEXT,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول درجات الإعفاء
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS exemption_grades (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            grade1 REAL,
            grade2 REAL,
            grade3 REAL,
            average REAL,
            is_exempt INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول الأسئلة (ساعدوني طالب)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_text TEXT,
            question_image TEXT,
            price_paid INTEGER,
            is_approved INTEGER DEFAULT 0,
            is_answered INTEGER DEFAULT 0,
            answer_text TEXT,
            answered_by INTEGER,
            answered_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول المواد التعليمية
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_materials (
            material_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            stage TEXT,
            file_id TEXT,
            file_type TEXT,
            added_by INTEGER,
            is_active INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول المشتركين VIP
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_subscribers (
            vip_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            subscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_date TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            auto_renew INTEGER DEFAULT 0
        )
        ''')
        
        # جدول محاضرات VIP
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_lectures (
            lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            file_id TEXT,
            title TEXT,
            description TEXT,
            price INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            views INTEGER DEFAULT 0,
            purchases INTEGER DEFAULT 0,
            rating_total REAL DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            approved_at TIMESTAMP
        )
        ''')
        
        # جدول مبيعات محاضرات VIP
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER,
            student_id INTEGER,
            teacher_id INTEGER,
            price INTEGER,
            teacher_earnings INTEGER,
            admin_earnings INTEGER,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول أرباح المدرسين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_earnings (
            teacher_id INTEGER PRIMARY KEY,
            total_earnings INTEGER DEFAULT 0,
            available_balance INTEGER DEFAULT 0,
            withdrawn_balance INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول أرباح الإدارة
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_earnings (
            earning_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            amount INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول إعدادات البوت
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
        ''')
        
        # جدول خدمات البوت
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT UNIQUE,
            display_name TEXT,
            is_active INTEGER DEFAULT 1,
            price INTEGER DEFAULT 1000,
            description TEXT
        )
        ''')
        
        # جدول إحصائيات البوت
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_stats (
            stat_date DATE PRIMARY KEY,
            new_users INTEGER DEFAULT 0,
            active_users INTEGER DEFAULT 0,
            total_income INTEGER DEFAULT 0,
            vip_subscriptions INTEGER DEFAULT 0,
            lecture_sales INTEGER DEFAULT 0
        )
        ''')
        
        # جدول PDF المحاضرات للمشتركين VIP
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_pdf_lectures (
            pdf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            file_id TEXT,
            title TEXT,
            description TEXT,
            price INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            views INTEGER DEFAULT 0,
            purchases INTEGER DEFAULT 0,
            rating_total REAL DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            approved_at TIMESTAMP
        )
        ''')
        
        # جدول مبيعات PDF المحاضرات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_pdf_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id INTEGER,
            student_id INTEGER,
            teacher_id INTEGER,
            price INTEGER,
            teacher_earnings INTEGER,
            admin_earnings INTEGER,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
    
    def init_default_data(self):
        cursor = self.conn.cursor()
        
        # الإعدادات الافتراضية
        default_settings = [
            ('invite_reward', '500'),
            ('maintenance_mode', '0'),
            ('welcome_message', 'مرحباً بك في بوت "يلا نتعلم"! 🎓'),
            ('support_text', f'للتواصل والدعم الفني: {SUPPORT_USERNAME}'),
            ('channel_text', f'قناة البوت: {CHANNEL_USERNAME}'),
            ('vip_subscription_price', '5000'),
            ('min_service_price', '1000'),
            ('admin_notifications', '1'),
            ('auto_approve_questions', '0'),
            ('auto_approve_lectures', '0'),
        ]
        
        for key, value in default_settings:
            cursor.execute('''
            INSERT OR IGNORE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)
            ''', (key, value))
        
        # الخدمات الافتراضية
        default_services = [
            ('exemption_calc', '🎓 حساب درجة الإعفاء', 1, 1000, 'احسب معدلك ومعرفة إذا كنت معفياً'),
            ('pdf_summary', '📚 تلخيص الملازم', 1, 1000, 'أرسل ملف PDF وسألخصه لك باستخدام الذكاء الاصطناعي'),
            ('qna', '❓ سؤال وجواب بالذكاء الاصطناعي', 1, 1000, 'اسأل أي سؤال في أي مادة وسأجيبك باستخدام الذكاء الاصطناعي'),
            ('help_student', '👨‍🎓 ساعدوني طالب', 1, 1000, 'ادفع لطرح سوال ويتم الرد عليه من قبل الطلاب'),
            ('study_materials', '📖 ملازمي ومرشحاتي', 1, 0, 'مجموعة من الملازم والمرشحات المجانية'),
            ('vip_lectures', '🎬 محاضرات VIP', 1, 0, 'محاضرات مدفوعة من مدرسين متميزين'),
            ('vip_subscribe', '👨‍🏫 اشتراك VIP', 1, 5000, 'اشترك كـ VIP لرفع محاضراتك وكسب الأرباح'),
            ('vip_pdf_lectures', '📚 محاضرات PDF VIP', 1, 0, 'محاضرات PDF مدفوعة من مدرسين متميزين'),
        ]
        
        for service_name, display_name, is_active, price, description in default_services:
            cursor.execute('''
            INSERT OR IGNORE INTO bot_services (service_name, display_name, is_active, price, description)
            VALUES (?, ?, ?, ?, ?)
            ''', (service_name, display_name, is_active, price, description))
        
        # إضافة المشرف الرئيسي
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, balance, is_admin, is_vip)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ADMIN_ID, 'Allawi04', 'المشرف', 'الرئيسي', 0, 1, 1))
        
        self.conn.commit()

    # ====================== دوال المستخدمين ======================
    def add_user(self, user_id, username, first_name, last_name, invited_by=0):
        cursor = self.conn.cursor()
        
        # التحقق من وجود المستخدم
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # تحديث بيانات المستخدم الحالي
            cursor.execute('''
            UPDATE users SET 
                username = ?, 
                first_name = ?, 
                last_name = ?,
                last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
            ''', (username, first_name, last_name, user_id))
            return existing_user['invite_code']
        
        # إنشاء كود دعوة جديد
        invite_code = hashlib.md5(f"{user_id}{time.time()}{random.random()}".encode()).hexdigest()[:10]
        
        # إدخال مستخدم جديد
        cursor.execute('''
        INSERT INTO users (
            user_id, username, first_name, last_name, 
            invited_by, invite_code, balance, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 1000, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name, invited_by, invite_code))
        
        # إضافة عملية الشحن التلقائي (1000 دينار هدية)
        if invited_by > 0:
            invite_reward = self.get_setting('invite_reward')
            if invite_reward:
                reward_amount = int(invite_reward)
                self.add_balance(invited_by, reward_amount)
                cursor.execute('''
                INSERT INTO transactions (user_id, amount, type, service, description)
                VALUES (?, ?, ?, ?, ?)
                ''', (invited_by, reward_amount, 'charge', 'invite', f'مكافأة دعوة للمستخدم {user_id}'))
                
                cursor.execute('''
                UPDATE users SET total_invites = total_invites + 1 WHERE user_id = ?
                ''', (invited_by,))
        
        self.conn.commit()
        self.update_daily_stats('new_users', 1)
        return invite_code
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    
    def update_user_activity(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
        self.conn.commit()
        self.update_daily_stats('active_users', 1, increment=True)
    
    def get_user_balance(self, user_id):
        user = self.get_user(user_id)
        return user['balance'] if user else 0
    
    def add_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()
        return True
    
    def deduct_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result and result['balance'] >= amount:
            cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
            self.conn.commit()
            return True
        return False
    
    def get_user_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users')
        return cursor.fetchone()['count']
    
    def get_active_users_count(self, days=7):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT COUNT(DISTINCT user_id) as count FROM transactions 
                         WHERE created_at > datetime('now', ?)''', (f'-{days} days',))
        return cursor.fetchone()['count']
    
    def get_all_users(self, limit=50, offset=0):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY user_id DESC LIMIT ? OFFSET ?', (limit, offset))
        users = cursor.fetchall()
        return [dict(user) for user in users]
    
    def search_users(self, search_term):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM users 
        WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
        ORDER BY user_id DESC LIMIT 20
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        users = cursor.fetchall()
        return [dict(user) for user in users]
    
    def ban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def unban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def promote_to_admin(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def demote_admin(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_admin = 0 WHERE user_id = ? AND user_id != ?', (user_id, ADMIN_ID))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ====================== دوال العمليات المالية ======================
    def add_transaction(self, user_id, amount, type_, service, description="", admin_id=0):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO transactions (user_id, amount, type, service, description, admin_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, type_, service, description, admin_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_transactions(self, user_id, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        ''', (user_id, limit))
        transactions = cursor.fetchall()
        return [dict(t) for t in transactions]
    
    def get_all_transactions(self, limit=50, offset=0):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT t.*, u.username, u.first_name 
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY t.created_at DESC 
        LIMIT ? OFFSET ?
        ''', (limit, offset))
        transactions = cursor.fetchall()
        return [dict(t) for t in transactions]
    
    # ====================== دوال الخدمات ======================
    def get_service(self, service_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM bot_services WHERE service_name = ?', (service_name,))
        service = cursor.fetchone()
        return dict(service) if service else None
    
    def get_all_services(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM bot_services ORDER BY service_id')
        services = cursor.fetchall()
        return [dict(s) for s in services]
    
    def get_active_services(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM bot_services WHERE is_active = 1 ORDER BY service_id')
        services = cursor.fetchall()
        return [dict(s) for s in services]
    
    def toggle_service(self, service_name, is_active):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE bot_services SET is_active = ? WHERE service_name = ?', 
                      (is_active, service_name))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_service_price(self, service_name, price):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE bot_services SET price = ? WHERE service_name = ?', 
                      (price, service_name))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_service_price(self, service_name):
        service = self.get_service(service_name)
        if service:
            return service['price']
        return 1000
    
    def is_service_active(self, service_name):
        service = self.get_service(service_name)
        if service:
            return service['is_active'] == 1
        return True
    
    # ====================== دوال VIP ======================
    def add_vip_subscriber(self, user_id, duration_days=30):
        cursor = self.conn.cursor()
        
        subscription_date = datetime.datetime.now()
        expiry_date = subscription_date + datetime.timedelta(days=duration_days)
        
        cursor.execute('''
        INSERT OR REPLACE INTO vip_subscribers (user_id, subscription_date, expiry_date, is_active)
        VALUES (?, ?, ?, 1)
        ''', (user_id, subscription_date, expiry_date))
        
        cursor.execute('UPDATE users SET is_vip = 1, vip_expiry = ? WHERE user_id = ?', 
                      (expiry_date, user_id))
        
        self.conn.commit()
        self.update_daily_stats('vip_subscriptions', 1)
        return True
    
    def is_vip_subscriber(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM vip_subscribers 
        WHERE user_id = ? AND is_active = 1 AND expiry_date > CURRENT_TIMESTAMP
        ''', (user_id,))
        return cursor.fetchone() is not None
    
    def get_vip_subscriber(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM vip_subscribers WHERE user_id = ?', (user_id,))
        vip = cursor.fetchone()
        return dict(vip) if vip else None
    
    def get_all_vip_subscribers(self, active_only=True):
        cursor = self.conn.cursor()
        
        if active_only:
            cursor.execute('''
            SELECT vs.*, u.username, u.first_name, u.last_name 
            FROM vip_subscribers vs
            JOIN users u ON vs.user_id = u.user_id
            WHERE vs.is_active = 1 AND vs.expiry_date > CURRENT_TIMESTAMP
            ORDER BY vs.expiry_date DESC
            ''')
        else:
            cursor.execute('''
            SELECT vs.*, u.username, u.first_name, u.last_name 
            FROM vip_subscribers vs
            JOIN users u ON vs.user_id = u.user_id
            ORDER BY vs.expiry_date DESC
            ''')
        
        subscribers = cursor.fetchall()
        return [dict(s) for s in subscribers]
    
    def cancel_vip_subscription(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE vip_subscribers SET is_active = 0 WHERE user_id = ?', (user_id,))
        cursor.execute('UPDATE users SET is_vip = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def renew_vip_subscription(self, user_id, duration_days=30):
        cursor = self.conn.cursor()
        expiry_date = datetime.datetime.now() + datetime.timedelta(days=duration_days)
        cursor.execute('''
        UPDATE vip_subscribers 
        SET is_active = 1, expiry_date = ?, subscription_date = CURRENT_TIMESTAMP
        WHERE user_id = ?
        ''', (expiry_date, user_id))
        
        cursor.execute('UPDATE users SET is_vip = 1, vip_expiry = ? WHERE user_id = ?', 
                      (expiry_date, user_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_expiring_vip_subscriptions(self, days=3):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vs.*, u.username, u.first_name 
        FROM vip_subscribers vs
        JOIN users u ON vs.user_id = u.user_id
        WHERE vs.is_active = 1 
        AND vs.expiry_date BETWEEN CURRENT_TIMESTAMP AND datetime(CURRENT_TIMESTAMP, ?)
        ORDER BY vs.expiry_date ASC
        ''', (f'+{days} days',))
        subscribers = cursor.fetchall()
        return [dict(s) for s in subscribers]
    
    # ====================== دوال أرباح VIP ======================
    def get_vip_earnings(self, teacher_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM vip_earnings WHERE teacher_id = ?', (teacher_id,))
        earnings = cursor.fetchone()
        return dict(earnings) if earnings else None
    
    def update_vip_earnings(self, teacher_id, amount):
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM vip_earnings WHERE teacher_id = ?', (teacher_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
            UPDATE vip_earnings 
            SET total_earnings = total_earnings + ?, 
                available_balance = available_balance + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE teacher_id = ?
            ''', (amount, amount, teacher_id))
        else:
            cursor.execute('''
            INSERT INTO vip_earnings (teacher_id, total_earnings, available_balance)
            VALUES (?, ?, ?)
            ''', (teacher_id, amount, amount))
        
        self.conn.commit()
        return True
    
    def deduct_vip_earnings(self, teacher_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_earnings 
        SET available_balance = available_balance - ?, 
            withdrawn_balance = withdrawn_balance + ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE teacher_id = ? AND available_balance >= ?
        ''', (amount, amount, teacher_id, amount))
        success = cursor.rowcount > 0
        self.conn.commit()
        return success
    
    def get_all_vip_earnings(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT ve.*, u.username, u.first_name, u.last_name
        FROM vip_earnings ve
        JOIN users u ON ve.teacher_id = u.user_id
        ORDER BY ve.available_balance DESC
        ''')
        earnings = cursor.fetchall()
        return [dict(e) for e in earnings]
    
    # ====================== دوال الإعدادات ======================
    def get_setting(self, key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT setting_value FROM bot_settings WHERE setting_key = ?', (key,))
        result = cursor.fetchone()
        return result['setting_value'] if result else None
    
    def update_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO bot_settings (setting_key, setting_value)
        VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()
        return True
    
    def get_maintenance_mode(self):
        mode = self.get_setting('maintenance_mode')
        return mode == '1' if mode else False
    
    def set_maintenance_mode(self, enabled):
        return self.update_setting('maintenance_mode', '1' if enabled else '0')
    
    def get_invite_reward(self):
        reward = self.get_setting('invite_reward')
        return int(reward) if reward else 500
    
    def set_invite_reward(self, amount):
        return self.update_setting('invite_reward', str(amount))
    
    def get_vip_subscription_price(self):
        price = self.get_setting('vip_subscription_price')
        return int(price) if price else 5000
    
    def set_vip_subscription_price(self, price):
        return self.update_setting('vip_subscription_price', str(price))
    
    # ====================== دوال الإحصائيات ======================
    def update_daily_stats(self, stat_type, value=1, increment=False):
        cursor = self.conn.cursor()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('SELECT * FROM bot_stats WHERE stat_date = ?', (today,))
        existing = cursor.fetchone()
        
        if existing:
            if increment:
                cursor.execute(f'''
                UPDATE bot_stats SET {stat_type} = {stat_type} + ? WHERE stat_date = ?
                ''', (value, today))
            else:
                cursor.execute(f'''
                UPDATE bot_stats SET {stat_type} = ? WHERE stat_date = ?
                ''', (value, today))
        else:
            cursor.execute(f'''
            INSERT INTO bot_stats (stat_date, {stat_type}) VALUES (?, ?)
            ''', (today, value))
        
        self.conn.commit()
        return True
    
    def get_daily_stats(self, date=None):
        cursor = self.conn.cursor()
        
        if date:
            cursor.execute('SELECT * FROM bot_stats WHERE stat_date = ?', (date,))
        else:
            cursor.execute('SELECT * FROM bot_stats ORDER BY stat_date DESC LIMIT 7')
        
        stats = cursor.fetchall()
        return [dict(s) for s in stats]
    
    def get_overall_stats(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN is_vip = 1 THEN 1 ELSE 0 END) as vip_users,
            SUM(CASE WHEN is_banned = 1 THEN 1 ELSE 0 END) as banned_users,
            SUM(balance) as total_balance
        FROM users
        ''')
        user_stats = cursor.fetchone()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as today_users,
            SUM(CASE WHEN is_vip = 1 THEN 1 ELSE 0 END) as today_vip
        FROM users 
        WHERE DATE(created_at) = DATE('now')
        ''')
        today_stats = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) as active_vip FROM vip_subscribers WHERE is_active = 1')
        vip_stats = cursor.fetchone()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as total_sales,
            SUM(price) as total_revenue,
            SUM(teacher_earnings) as total_teacher_earnings,
            SUM(admin_earnings) as total_admin_earnings
        FROM vip_sales
        ''')
        sales_stats = cursor.fetchone()
        
        return {
            'users': dict(user_stats) if user_stats else {},
            'today': dict(today_stats) if today_stats else {},
            'vip': dict(vip_stats) if vip_stats else {},
            'sales': dict(sales_stats) if sales_stats else {}
        }
    
    def get_financial_stats(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT 
            SUM(CASE WHEN type = 'charge' THEN amount ELSE 0 END) as total_charged,
            SUM(CASE WHEN type = 'payment' THEN amount ELSE 0 END) as total_payments,
            SUM(CASE WHEN type = 'deduct' THEN amount ELSE 0 END) as total_deducted,
            SUM(CASE WHEN type = 'refund' THEN amount ELSE 0 END) as total_refunds,
            COUNT(*) as total_transactions
        FROM transactions
        ''')
        
        stats = cursor.fetchone()
        
        cursor.execute('''
        SELECT 
            service,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM transactions 
        WHERE type = 'payment'
        GROUP BY service
        ORDER BY total_amount DESC
        ''')
        
        service_stats = cursor.fetchall()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as today_transactions,
            SUM(CASE WHEN type = 'payment' THEN amount ELSE 0 END) as today_income
        FROM transactions 
        WHERE DATE(created_at) = DATE('now')
        ''')
        
        today_stats = cursor.fetchone()
        
        return {
            'overall': dict(stats) if stats else {},
            'services': [dict(s) for s in service_stats],
            'today': dict(today_stats) if today_stats else {}
        }
    
    # ====================== دوال المواد التعليمية ======================
    def add_study_material(self, title, description, stage, file_id, file_type, added_by):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO study_materials (title, description, stage, file_id, file_type, added_by)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, stage, file_id, file_type, added_by))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_study_materials(self, stage=None, active_only=True):
        cursor = self.conn.cursor()
        
        if stage:
            if active_only:
                cursor.execute('''
                SELECT * FROM study_materials 
                WHERE stage = ? AND is_active = 1
                ORDER BY added_at DESC
                ''', (stage,))
            else:
                cursor.execute('''
                SELECT * FROM study_materials 
                WHERE stage = ?
                ORDER BY added_at DESC
                ''', (stage,))
        else:
            if active_only:
                cursor.execute('SELECT * FROM study_materials WHERE is_active = 1 ORDER BY added_at DESC')
            else:
                cursor.execute('SELECT * FROM study_materials ORDER BY added_at DESC')
        
        materials = cursor.fetchall()
        return [dict(m) for m in materials]
    
    def toggle_study_material(self, material_id, is_active):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE study_materials SET is_active = ? WHERE material_id = ?', 
                      (is_active, material_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_study_material(self, material_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM study_materials WHERE material_id = ?', (material_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ====================== دوال الأسئلة ======================
    def add_student_question(self, user_id, question_text, question_image, price_paid):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO student_questions (user_id, question_text, question_image, price_paid)
        VALUES (?, ?, ?, ?)
        ''', (user_id, question_text, question_image, price_paid))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_questions(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT sq.*, u.username, u.first_name 
        FROM student_questions sq
        JOIN users u ON sq.user_id = u.user_id
        WHERE sq.is_approved = 0 AND sq.is_answered = 0
        ORDER BY sq.created_at DESC
        ''')
        questions = cursor.fetchall()
        return [dict(q) for q in questions]
    
    def get_approved_questions(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT sq.*, u.username, u.first_name 
        FROM student_questions sq
        JOIN users u ON sq.user_id = u.user_id
        WHERE sq.is_approved = 1 AND sq.is_answered = 0
        ORDER BY sq.created_at DESC
        ''')
        questions = cursor.fetchall()
        return [dict(q) for q in questions]
    
    def get_all_questions(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT sq.*, u.username, u.first_name 
        FROM student_questions sq
        JOIN users u ON sq.user_id = u.user_id
        ORDER BY sq.created_at DESC
        ''')
        questions = cursor.fetchall()
        return [dict(q) for q in questions]
    
    def get_question_by_id(self, question_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT sq.*, u.username, u.first_name 
        FROM student_questions sq
        JOIN users u ON sq.user_id = u.user_id
        WHERE sq.question_id = ?
        ''', (question_id,))
        question = cursor.fetchone()
        return dict(question) if question else None
    
    def approve_question(self, question_id, admin_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE student_questions 
        SET is_approved = 1 
        WHERE question_id = ?
        ''', (question_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reject_question(self, question_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM student_questions WHERE question_id = ?', (question_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def answer_question(self, question_id, answer_text, answered_by):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE student_questions 
        SET is_answered = 1, answer_text = ?, answered_by = ?, answered_at = CURRENT_TIMESTAMP
        WHERE question_id = ?
        ''', (answer_text, answered_by, question_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ====================== دوال حساب الإعفاء ======================
    def save_exemption_grade(self, user_id, grade1, grade2, grade3):
        cursor = self.conn.cursor()
        average = (grade1 + grade2 + grade3) / 3
        is_exempt = 1 if average >= 90 else 0
        
        cursor.execute('''
        INSERT INTO exemption_grades (user_id, grade1, grade2, grade3, average, is_exempt)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, grade1, grade2, grade3, average, is_exempt))
        self.conn.commit()
        return average, is_exempt
    
    def get_user_exemptions(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM exemption_grades 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        ''', (user_id,))
        exemptions = cursor.fetchall()
        return [dict(e) for e in exemptions]
    
    # ====================== دوال محاضرات VIP ======================
    def add_vip_lecture(self, teacher_id, file_id, title, description, price):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO vip_lectures (teacher_id, file_id, title, description, price, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (teacher_id, file_id, title, description, price))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_lectures(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vl.*, u.username, u.first_name 
        FROM vip_lectures vl
        JOIN users u ON vl.teacher_id = u.user_id
        WHERE vl.status = 'pending'
        ORDER BY vl.created_at DESC
        ''')
        lectures = cursor.fetchall()
        return [dict(l) for l in lectures]
    
    def get_approved_lectures(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vl.*, u.username, u.first_name
        FROM vip_lectures vl
        JOIN users u ON vl.teacher_id = u.user_id
        WHERE vl.status = 'approved'
        ORDER BY vl.created_at DESC
        LIMIT ?
        ''', (limit,))
        lectures = cursor.fetchall()
        return [dict(l) for l in lectures]
    
    def get_teacher_lectures(self, teacher_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM vip_lectures 
        WHERE teacher_id = ? AND status != 'deleted'
        ORDER BY created_at DESC
        ''', (teacher_id,))
        lectures = cursor.fetchall()
        return [dict(l) for l in lectures]
    
    def get_lecture_by_id(self, lecture_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vl.*, u.username, u.first_name 
        FROM vip_lectures vl
        JOIN users u ON vl.teacher_id = u.user_id
        WHERE vl.lecture_id = ?
        ''', (lecture_id,))
        lecture = cursor.fetchone()
        return dict(lecture) if lecture else None
    
    def approve_lecture(self, lecture_id, admin_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_lectures 
        SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
        WHERE lecture_id = ?
        ''', (admin_id, lecture_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reject_lecture(self, lecture_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_lectures 
        SET status = 'rejected' 
        WHERE lecture_id = ?
        ''', (lecture_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_lecture(self, lecture_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_lectures 
        SET status = 'deleted' 
        WHERE lecture_id = ?
        ''', (lecture_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_lecture_stats(self, lecture_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_lectures 
        SET views = views + 1 
        WHERE lecture_id = ?
        ''', (lecture_id,))
        self.conn.commit()
    
    def add_vip_sale(self, lecture_id, student_id, price):
        cursor = self.conn.cursor()
        
        lecture = self.get_lecture_by_id(lecture_id)
        if not lecture:
            return False
        
        teacher_id = lecture['teacher_id']
        teacher_earnings = int(price * 0.6)
        admin_earnings = int(price * 0.4)
        
        cursor.execute('''
        INSERT INTO vip_sales (lecture_id, student_id, teacher_id, price, teacher_earnings, admin_earnings)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (lecture_id, student_id, teacher_id, price, teacher_earnings, admin_earnings))
        
        cursor.execute('''
        UPDATE vip_lectures 
        SET purchases = purchases + 1 
        WHERE lecture_id = ?
        ''', (lecture_id,))
        
        self.update_vip_earnings(teacher_id, teacher_earnings)
        
        cursor.execute('''
        INSERT INTO admin_earnings (source, amount, description)
        VALUES (?, ?, ?)
        ''', ('vip_lecture', admin_earnings, f'بيع محاضرة #{lecture_id}'))
        
        self.update_daily_stats('lecture_sales', 1)
        
        self.conn.commit()
        return True
    
    # ====================== دوال PDF محاضرات VIP ======================
    def add_vip_pdf_lecture(self, teacher_id, file_id, title, description, price):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO vip_pdf_lectures (teacher_id, file_id, title, description, price, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (teacher_id, file_id, title, description, price))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_pdf_lectures(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vpl.*, u.username, u.first_name 
        FROM vip_pdf_lectures vpl
        JOIN users u ON vpl.teacher_id = u.user_id
        WHERE vpl.status = 'pending'
        ORDER BY vpl.created_at DESC
        ''')
        lectures = cursor.fetchall()
        return [dict(l) for l in lectures]
    
    def get_approved_pdf_lectures(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vpl.*, u.username, u.first_name
        FROM vip_pdf_lectures vpl
        JOIN users u ON vpl.teacher_id = u.user_id
        WHERE vpl.status = 'approved'
        ORDER BY vpl.created_at DESC
        LIMIT ?
        ''', (limit,))
        lectures = cursor.fetchall()
        return [dict(l) for l in lectures]
    
    def get_teacher_pdf_lectures(self, teacher_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM vip_pdf_lectures 
        WHERE teacher_id = ? AND status != 'deleted'
        ORDER BY created_at DESC
        ''', (teacher_id,))
        lectures = cursor.fetchall()
        return [dict(l) for l in lectures]
    
    def get_pdf_lecture_by_id(self, pdf_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT vpl.*, u.username, u.first_name 
        FROM vip_pdf_lectures vpl
        JOIN users u ON vpl.teacher_id = u.user_id
        WHERE vpl.pdf_id = ?
        ''', (pdf_id,))
        lecture = cursor.fetchone()
        return dict(lecture) if lecture else None
    
    def approve_pdf_lecture(self, pdf_id, admin_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_pdf_lectures 
        SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
        WHERE pdf_id = ?
        ''', (admin_id, pdf_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reject_pdf_lecture(self, pdf_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE vip_pdf_lectures 
        SET status = 'rejected' 
        WHERE pdf_id = ?
        ''', (pdf_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def add_vip_pdf_sale(self, pdf_id, student_id, price):
        cursor = self.conn.cursor()
        
        lecture = self.get_pdf_lecture_by_id(pdf_id)
        if not lecture:
            return False
        
        teacher_id = lecture['teacher_id']
        teacher_earnings = int(price * 0.6)
        admin_earnings = int(price * 0.4)
        
        cursor.execute('''
        INSERT INTO vip_pdf_sales (pdf_id, student_id, teacher_id, price, teacher_earnings, admin_earnings)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (pdf_id, student_id, teacher_id, price, teacher_earnings, admin_earnings))
        
        cursor.execute('''
        UPDATE vip_pdf_lectures 
        SET purchases = purchases + 1 
        WHERE pdf_id = ?
        ''', (pdf_id,))
        
        self.update_vip_earnings(teacher_id, teacher_earnings)
        
        cursor.execute('''
        INSERT INTO admin_earnings (source, amount, description)
        VALUES (?, ?, ?)
        ''', ('vip_pdf_lecture', admin_earnings, f'بيع محاضرة PDF #{pdf_id}'))
        
        self.update_daily_stats('lecture_sales', 1)
        
        self.conn.commit()
        return True

# ====================== تهيئة قاعدة البيانات ======================
db = Database()

# ====================== دوال المساعدة العامة ======================
def is_admin(user_id):
    user_data = db.get_user(user_id)
    return user_data and (user_data['is_admin'] == 1 or user_id == ADMIN_ID)

def format_currency(amount):
    return f"{amount:,} دينار عراقي"

def format_date(dt):
    if dt is None:
        return "غير معروف"
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M")

def format_time_ago(dt):
    if dt is None:
        return "غير معروف"
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return "منذ فترة"
    
    now = datetime.datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365} سنة"
    elif diff.days > 30:
        return f"{diff.days // 30} شهر"
    elif diff.days > 0:
        return f"{diff.days} يوم"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} ساعة"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} دقيقة"
    else:
        return "الآن"

def generate_invite_link(user_id):
    return f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}"

async def send_admin_notification(context, message):
    try:
        await context.bot.send_message(
            ADMIN_ID,
            message,
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass

# ====================== دوال الذكاء الاصطناعي ======================
async def generate_gemini_response(prompt):
    headers = {'Content-Type': 'application/json'}
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
        return "عذراً، لم أتمكن من توليد إجابة مناسبة."
    except:
        return "عذراً، حدث خطأ في الخادم. يرجى المحاولة لاحقاً."

async def summarize_pdf_with_gemini(pdf_text):
    prompt = f"""
    قم بتلخيص النص التالي مع الحفاظ على الأفكار الرئيسية:
    - احذف المعلومات غير المهمة
    - احتفظ بالمفاهيم الأساسية
    - نظم المعلومات بطريقة منطقية
    - استخدم لغة عربية سليمة وواضحة
    
    النص:
    {pdf_text[:3000]}
    """
    return await generate_gemini_response(prompt)

async def answer_question_with_gemini(question, context=""):
    prompt = f"""
    أنت مساعد تعليمي متخصص في المناهج العراقية.
    أجب على السؤال التالي بطريقة علمية ومنهجية:
    
    السؤال: {question}
    
    {f'السياق: {context}' if context else ''}
    
    قدم إجابة شاملة وواضحة مع أمثلة إذا لزم الأمر.
    """
    return await generate_gemini_response(prompt)

# ====================== دوال معالجة PDF ======================
def extract_text_from_pdf(file_bytes):
    if not PYPDF2_SUPPORT:
        return "مكتبة PyPDF2 غير مثبتة."
    
    try:
        pdf_file = BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text
    except:
        return "حدث خطأ في استخراج النص من PDF"

# ====================== دوال لوحة التحكم ======================
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("💰 الشحن والخصم", callback_data="admin_finance")],
        [InlineKeyboardButton("⚙️ إدارة الخدمات", callback_data="admin_services")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("🎬 إدارة VIP", callback_data="admin_vip")],
        [InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔧 الإعدادات", callback_data="admin_settings")],
        [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_users_management_keyboard():
    keyboard = [
        [InlineKeyboardButton("👁️ عرض المستخدمين", callback_data="admin_users_list_1")],
        [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="admin_search_user")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user")],
        [InlineKeyboardButton("✅ فك حظر مستخدم", callback_data="admin_unban_user")],
        [InlineKeyboardButton("👑 رفع مشرف", callback_data="admin_promote_user")],
        [InlineKeyboardButton("❓ إدارة الأسئلة", callback_data="admin_manage_questions")],
        [InlineKeyboardButton("📋 سجل المعاملات", callback_data="admin_transactions_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_finance_management_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 شحن رصيد", callback_data="admin_charge")],
        [InlineKeyboardButton("💸 خصم رصيد", callback_data="admin_deduct")],
        [InlineKeyboardButton("💳 خصم أرباح مدرس", callback_data="admin_deduct_vip")],
        [InlineKeyboardButton("📈 إحصائيات مالية", callback_data="admin_finance_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_vip_management_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 المشتركون VIP", callback_data="admin_vip_subscribers_1")],
        [InlineKeyboardButton("⏳ المشتركون المنتهية", callback_data="admin_vip_expiring")],
        [InlineKeyboardButton("🎬 المحاضرات المنتظرة", callback_data="admin_vip_pending")],
        [InlineKeyboardButton("📚 PDFs المنتظرة", callback_data="admin_pdf_pending")],
        [InlineKeyboardButton("📊 إحصائيات VIP", callback_data="admin_vip_stats")],
        [InlineKeyboardButton("💰 أرباح المدرسين", callback_data="admin_vip_earnings")],
        [InlineKeyboardButton("🔧 إعدادات VIP", callback_data="admin_vip_settings")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_services_management_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎓 حساب الإعفاء", callback_data="admin_service_exemption")],
        [InlineKeyboardButton("📚 تلخيص الملازم", callback_data="admin_service_summary")],
        [InlineKeyboardButton("❓ سؤال وجواب", callback_data="admin_service_qna")],
        [InlineKeyboardButton("👨‍🎓 ساعدوني طالب", callback_data="admin_service_help")],
        [InlineKeyboardButton("📖 إدارة الملازم", callback_data="admin_manage_materials")],
        [InlineKeyboardButton("🔄 تفعيل/تعطيل خدمات", callback_data="admin_toggle_services")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard(user_id):
    keyboard = []
    
    active_services = db.get_active_services()
    
    for service in active_services:
        if service['service_name'] == 'exemption_calc':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="service_exemption")])
        elif service['service_name'] == 'pdf_summary':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="service_summary")])
        elif service['service_name'] == 'qna':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="service_qna")])
        elif service['service_name'] == 'help_student':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="service_help")])
        elif service['service_name'] == 'study_materials':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="service_materials")])
        elif service['service_name'] == 'vip_lectures':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="vip_lectures")])
        elif service['service_name'] == 'vip_subscribe':
            keyboard.append([InlineKeyboardButton(service['display_name'], callback_data="vip_subscribe")])
    
    if db.is_vip_subscriber(user_id):
        vip_buttons = [
            ("💰 رصيد أرباحي", "vip_my_earnings"),
            ("📤 رفع محاضرة", "vip_upload_lecture"),
            ("📚 رفع PDF", "vip_upload_pdf"),
            ("🎓 محاضراتي", "vip_my_lectures"),
            ("📄 PDFs محاضراتي", "vip_my_pdfs"),
        ]
        for text, callback in vip_buttons:
            keyboard.append([InlineKeyboardButton(text, callback_data=callback)])
    
    help_buttons = [
        [InlineKeyboardButton("💰 رصيدي", callback_data="my_balance"),
         InlineKeyboardButton("👥 دعوة صديق", callback_data="invite_friend")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
         InlineKeyboardButton("📞 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("📢 قناة البوت", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]
    ]
    keyboard.extend(help_buttons)
    
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🛠️ لوحة التحكم", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

# ====================== معالجات الأوامر الرئيسية ======================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        
        if db.get_maintenance_mode() and not is_admin(user.id):
            await update.message.reply_text("⚙️ البوت في وضع الصيانة حالياً. يرجى المحاولة لاحقاً.")
            return
        
        invited_by = 0
        if context.args and len(context.args) > 0:
            try:
                invited_by = int(context.args[0])
            except:
                invited_by = 0
        
        invite_code = db.add_user(
            user.id,
            user.username,
            user.first_name or "",
            user.last_name or "",
            invited_by
        )
        
        db.update_user_activity(user.id)
        
        user_data = db.get_user(user.id)
        if user_data and user_data['is_banned']:
            await update.message.reply_text("🚫 حسابك محظور. يرجى التواصل مع الدعم الفني.")
            return
        
        welcome_msg = db.get_setting('welcome_message') or "مرحباً بك في بوت 'يلا نتعلم'! 🎓"
        
        message = f"""
        {welcome_msg}
        
        👤 أهلاً {user.first_name or 'عزيزي'}!
        🎁 رصيدك الحالي: {format_currency(user_data['balance'])}
        
        اختر الخدمة التي تريدها:
        """
        
        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(user.id),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")

async def handle_callback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user = query.from_user
        
        if db.get_maintenance_mode() and not is_admin(user.id):
            await query.edit_message_text("⚙️ البوت في وضع الصيانة حالياً. يرجى المحاولة لاحقاً.")
            return
        
        db.update_user_activity(user.id)
        
        user_data = db.get_user(user.id)
        if user_data and user_data['is_banned']:
            await query.edit_message_text("🚫 حسابك محظور. يرجى التواصل مع الدعم الفني.")
            return
        
        welcome_msg = db.get_setting('welcome_message') or "مرحباً بك في بوت 'يلا نتعلم'! 🎓"
        
        message = f"""
        {welcome_msg}
        
        👤 أهلاً {user.first_name or 'عزيزي'}!
        🎁 رصيدك الحالي: {format_currency(user_data['balance'])}
        
        اختر الخدمة التي تريدها:
        """
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(user.id),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in handle_callback_start: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        help_text = f"""
        📚 *دليل استخدام بوت "يلا نتعلم"*
        
        *الخدمات التعليمية:*
        
        🎓 *حساب درجة الإعفاء*
        - احسب معدلك ومعرفة إذا كنت معفياً
        
        📚 *تلخيص الملازم*
        - أرسل ملف PDF وسألخصه لك
        
        ❓ *سؤال وجواب بالذكاء الاصطناعي*
        - اسأل أي سؤال في أي مادة
        
        👨‍🎓 *ساعدوني طالب*
        - ادفع لطرح سوال ويتم الرد عليه
        
        📖 *ملازمي ومرشحاتي*
        - مجموعة من الملازم والمرشحات المجانية
        
        🎬 *محاضرات VIP*
        - محاضرات مدفوعة من مدرسين متميزين
        
        👨‍🏫 *اشتراك VIP*
        - اشترك كـ VIP لرفع محاضراتك وكسب الأرباح
        
        *معلومات الدفع:*
        💰 العملة: الدينار العراقي
        💵 أقل سعر: 1000 دينار
        🏦 للشحن: راسل {SUPPORT_USERNAME}
        
        *روابط مهمة:*
        📞 الدعم الفني: {SUPPORT_USERNAME}
        📢 قناة البوت: {CHANNEL_USERNAME}
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard(update.effective_user.id)
        )
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")

# ====================== معالجات الخدمات ======================
async def service_exemption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not db.is_service_active('exemption_calc'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        service_price = db.get_service_price('exemption_calc')
        if user_data['balance'] < service_price:
            await query.edit_message_text(
                f"❌ رصيدك غير كافي.\n\n💰 سعر الخدمة: {format_currency(service_price)}\n🏦 رصيدك: {format_currency(user_data['balance'])}",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        instructions = f"""
        🎓 *حساب درجة الإعفاء*
        
        سأطلب منك إدخال 3 درجات:
        
        1. درجة الكورس الأول
        2. درجة الكورس الثاني  
        3. درجة الكورس الأخير
        
        *المعدل المطلوب للإعفاء:* 90 فأعلى
        
        ⚠️ سيتم خصم {format_currency(service_price)}
        
        *أرسل الآن درجة الكورس الأول (رقم فقط):*
        """
        
        context.user_data['exemption_service'] = True
        context.user_data['exemption_price'] = service_price
        
        await query.edit_message_text(
            instructions,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return CALC_GRADE1
    except Exception as e:
        logger.error(f"Error in service_exemption: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")
        return ConversationHandler.END

async def process_grade1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        grade1 = float(update.message.text)
        if grade1 < 0 or grade1 > 100:
            await update.message.reply_text("❌ الدرجة يجب أن تكون بين 0 و 100:")
            return CALC_GRADE1
        
        context.user_data['grade1'] = grade1
        await update.message.reply_text("✅ تم حفظ الدرجة الأولى.\n*أرسل درجة الكورس الثاني:*", parse_mode=ParseMode.MARKDOWN)
        return CALC_GRADE2
    except ValueError:
        await update.message.reply_text("❌ الرجاء إدخال رقم صحيح:")
        return CALC_GRADE1
    except Exception as e:
        logger.error(f"Error in process_grade1: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_grade2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        grade2 = float(update.message.text)
        if grade2 < 0 or grade2 > 100:
            await update.message.reply_text("❌ الدرجة يجب أن تكون بين 0 و 100:")
            return CALC_GRADE2
        
        context.user_data['grade2'] = grade2
        await update.message.reply_text("✅ تم حفظ الدرجة الثانية.\n*أرسل درجة الكورس الأخير:*", parse_mode=ParseMode.MARKDOWN)
        return CALC_GRADE3
    except ValueError:
        await update.message.reply_text("❌ الرجاء إدخال رقم صحيح:")
        return CALC_GRADE2
    except Exception as e:
        logger.error(f"Error in process_grade2: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_grade3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        grade3 = float(update.message.text)
        if grade3 < 0 or grade3 > 100:
            await update.message.reply_text("❌ الدرجة يجب أن تكون بين 0 و 100:")
            return CALC_GRADE3
        
        user_id = update.effective_user.id
        grade1 = context.user_data.get('grade1')
        grade2 = context.user_data.get('grade2')
        service_price = context.user_data.get('exemption_price')
        
        if db.deduct_balance(user_id, service_price):
            db.add_transaction(user_id, -service_price, 'payment', 'exemption_calc', 'حساب درجة الإعفاء')
            
            average, is_exempt = db.save_exemption_grade(user_id, grade1, grade2, grade3)
            
            if is_exempt:
                result_msg = "🎉 *مبروك! أنت معفي من المادة* 🎉"
                emoji = "✅"
            else:
                result_msg = "❌ *للأسف، لست معفياً من المادة*"
                emoji = "❌"
            
            final_msg = f"""
            {result_msg}
            
            {emoji} *النتيجة:*
            • درجة الكورس الأول: {grade1}
            • درجة الكورس الثاني: {grade2}
            • درجة الكورس الأخير: {grade3}
            • *المعدل النهائي:* {average:.2f}
            
            💰 *تم خصم:* {format_currency(service_price)}
            🏦 *رصيدك المتبقي:* {format_currency(db.get_user_balance(user_id))}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 حساب مرة أخرى", callback_data="service_exemption")],
                [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
            ]
            
            await update.message.reply_text(
                final_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("❌ فشل في عملية الخصم.")
        
        context.user_data.pop('grade1', None)
        context.user_data.pop('grade2', None)
        context.user_data.pop('exemption_service', None)
        context.user_data.pop('exemption_price', None)
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ الرجاء إدخال رقم صحيح:")
        return CALC_GRADE3
    except Exception as e:
        logger.error(f"Error in process_grade3: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def service_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not db.is_service_active('pdf_summary'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        if not PYPDF2_SUPPORT:
            await query.edit_message_text(
                "❌ هذه الخدمة غير متاحة حالياً.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        service_price = db.get_service_price('pdf_summary')
        if user_data['balance'] < service_price:
            await query.edit_message_text(
                f"❌ رصيدك غير كافي.\n\n💰 سعر الخدمة: {format_currency(service_price)}\n🏦 رصيدك: {format_currency(user_data['balance'])}",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        instructions = f"""
        📚 *تلخيص الملازم*
        
        أرسل لي ملف PDF وسأقوم بتلخيصه لك.
        
        ⚠️ *ملاحظات:*
        1. الملف يجب أن يكون بصيغة PDF
        2. الحد الأقصى للحجم: 20MB
        
        💰 *سعر الخدمة:* {format_currency(service_price)}
        
        *أرسل ملف PDF الآن:*
        """
        
        context.user_data['summary_service'] = True
        context.user_data['summary_price'] = service_price
        
        await query.edit_message_text(
            instructions,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return PDF_SUMMARY
    except Exception as e:
        logger.error(f"Error in service_summary: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_pdf_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        if not update.message.document:
            await update.message.reply_text("❌ يرجى إرسال ملف PDF فقط:")
            return PDF_SUMMARY
        
        file_name = update.message.document.file_name or ""
        if not file_name.lower().endswith('.pdf'):
            await update.message.reply_text("❌ الملف يجب أن يكون بصيغة PDF:")
            return PDF_SUMMARY
        
        await update.message.reply_text("⏳ جارٍ تحميل الملف...")
        file = await update.message.document.get_file()
        file_bytes = await file.download_as_bytearray()
        
        await update.message.reply_text("✅ تم تحميل الملف. جارٍ استخراج النص...")
        
        pdf_text = extract_text_from_pdf(file_bytes)
        
        if not pdf_text or len(pdf_text.strip()) < 50:
            await update.message.reply_text("❌ لم أتمكن من استخراج نص كافٍ من الملف.")
            return PDF_SUMMARY
        
        await update.message.reply_text("✅ تم استخراج النص. جارٍ التلخيص...")
        
        service_price = context.user_data.get('summary_price', db.get_service_price('pdf_summary'))
        
        if not db.deduct_balance(user_id, service_price):
            await update.message.reply_text("❌ رصيدك غير كافي.")
            return ConversationHandler.END
        
        db.add_transaction(user_id, -service_price, 'payment', 'pdf_summary', 'تلخيص PDF')
        
        summary = await summarize_pdf_with_gemini(pdf_text)
        
        result_msg = f"""
        ✅ *تم تلخيص الملف بنجاح*
        
        📄 *الملف الأصلي:* {file_name}
        💰 *سعر الخدمة:* {format_currency(service_price)}
        🏦 *رصيدك المتبقي:* {format_currency(db.get_user_balance(user_id))}
        
        📝 *الملخص:*
        {summary[:3000]}
        """
        
        await update.message.reply_text(result_msg, parse_mode=ParseMode.MARKDOWN)
        
        context.user_data.pop('summary_service', None)
        context.user_data.pop('summary_price', None)
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"PDF summary error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة الملف.")
        return ConversationHandler.END

async def service_qna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not db.is_service_active('qna'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        service_price = db.get_service_price('qna')
        if user_data['balance'] < service_price:
            await query.edit_message_text(
                f"❌ رصيدك غير كافي.\n\n💰 سعر الخدمة: {format_currency(service_price)}\n🏦 رصيدك: {format_currency(user_data['balance'])}",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        instructions = f"""
        ❓ *سؤال وجواب بالذكاء الاصطناعي*
        
        اسألني أي سؤال في أي مادة وسأجيبك.
        
        ⚠️ سيتم خصم {format_currency(service_price)}
        
        *أرسل سؤالك الآن:*
        """
        
        context.user_data['qna_service'] = True
        context.user_data['qna_price'] = service_price
        
        await query.edit_message_text(
            instructions,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ASK_QUESTION
    except Exception as e:
        logger.error(f"Error in service_qna: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        service_price = context.user_data.get('qna_price', db.get_service_price('qna'))
        
        if not db.deduct_balance(user_id, service_price):
            await update.message.reply_text("❌ رصيدك غير كافي.")
            return ConversationHandler.END
        
        db.add_transaction(user_id, -service_price, 'payment', 'qna', 'سؤال وجواب')
        
        question_text = ""
        if update.message.text:
            question_text = update.message.text
        elif update.message.caption:
            question_text = update.message.caption
        else:
            question_text = "سؤال بدون نص"
        
        await update.message.reply_text("🤔 جارٍ البحث عن إجابة...")
        
        try:
            answer = await answer_question_with_gemini(question_text)
            
            response_msg = f"""
            ✅ *تمت الإجابة على سؤالك*
            
            ❓ *سؤالك:* {question_text[:200]}
            
            💡 *الإجابة:*
            {answer}
            
            💰 *تم خصم:* {format_currency(service_price)}
            🏦 *رصيدك المتبقي:* {format_currency(db.get_user_balance(user_id))}
            """
            
            await update.message.reply_text(response_msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"QnA error: {e}")
            await update.message.reply_text("❌ حدث خطأ أثناء معالجة سؤالك.")
            db.add_balance(user_id, service_price)
            db.add_transaction(user_id, service_price, 'refund', 'qna', 'استرجاع رصيد')
        
        context.user_data.pop('qna_service', None)
        context.user_data.pop('qna_price', None)
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in process_question: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def service_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not db.is_service_active('help_student'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        service_price = db.get_service_price('help_student')
        if user_data['balance'] < service_price:
            await query.edit_message_text(
                f"❌ رصيدك غير كافي.\n\n💰 سعر الخدمة: {format_currency(service_price)}\n🏦 رصيدك: {format_currency(user_data['balance'])}",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        instructions = f"""
        👨‍🎓 *ساعدوني طالب*
        
        ادفع لطرح سؤال وسيتم نشره في قسم الأسئلة.
        
        ⚠️ سيتم خصم {format_currency(service_price)}
        
        *أرسل سؤالك الآن:*
        """
        
        context.user_data['help_service'] = True
        context.user_data['help_price'] = service_price
        
        await query.edit_message_text(
            instructions,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ASK_QUESTION
    except Exception as e:
        logger.error(f"Error in service_help: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_help_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        service_price = context.user_data.get('help_price', db.get_service_price('help_student'))
        
        if not db.deduct_balance(user_id, service_price):
            await update.message.reply_text("❌ رصيدك غير كافي.")
            return ConversationHandler.END
        
        db.add_transaction(user_id, -service_price, 'payment', 'help_student', 'سؤال ساعدوني طالب')
        
        question_text = ""
        question_image = None
        
        if update.message.text:
            question_text = update.message.text
        elif update.message.caption:
            question_text = update.message.caption
        
        if update.message.photo:
            question_image = update.message.photo[-1].file_id
        
        question_id = db.add_student_question(user_id, question_text, question_image, service_price)
        
        await update.message.reply_text(f"""
        ✅ *تم استلام سؤالك بنجاح*
        
        📝 *رقم سؤالك:* #{question_id}
        💰 *تم خصم:* {format_currency(service_price)}
        🏦 *رصيدك المتبقي:* {format_currency(db.get_user_balance(user_id))}
        
        ⏳ *جاري مراجعة السؤال...*
        """, parse_mode=ParseMode.MARKDOWN)
        
        if is_admin(ADMIN_ID):
            approve_keyboard = [
                [
                    InlineKeyboardButton("✅ الموافقة", callback_data=f"admin_approve_question_{question_id}"),
                    InlineKeyboardButton("❌ الرفض", callback_data=f"admin_reject_question_{question_id}")
                ]
            ]
            
            admin_msg = f"""
            ❓ *سؤال جديد يحتاج موافقة*
            
            👤 المستخدم: {update.effective_user.first_name} (ID: {user_id})
            📝 السؤال: {question_text[:200]}
            💰 السعر المدفوع: {format_currency(service_price)}
            
            #سؤال_{question_id}
            """
            
            if question_image:
                await context.bot.send_photo(
                    ADMIN_ID,
                    photo=question_image,
                    caption=admin_msg,
                    reply_markup=InlineKeyboardMarkup(approve_keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await context.bot.send_message(
                    ADMIN_ID,
                    admin_msg,
                    reply_markup=InlineKeyboardMarkup(approve_keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
        
        context.user_data.pop('help_service', None)
        context.user_data.pop('help_price', None)
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in process_help_question: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def service_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_service_active('study_materials'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        materials = db.get_study_materials()
        
        if not materials:
            await query.edit_message_text(
                "📭 لا توجد مواد متاحة حالياً.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        stages = {}
        for material in materials:
            stage = material['stage'] or 'غير مصنف'
            if stage not in stages:
                stages[stage] = []
            stages[stage].append(material)
        
        keyboard = []
        for stage in sorted(stages.keys()):
            keyboard.append([InlineKeyboardButton(f"📚 {stage} ({len(stages[stage])})", 
                           callback_data=f"materials_stage_{stage}")])
        
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="start")])
        
        await query.edit_message_text(
            "📖 *ملازمي ومرشحاتي*\n\nاختر المرحلة التعليمية:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in service_materials: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def show_stage_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data.replace("materials_stage_", "")
        stage = data
        
        materials = db.get_study_materials(stage=stage)
        
        if not materials:
            await query.edit_message_text(
                f"📭 لا توجد مواد متاحة لمرحلة {stage}.",
                reply_markup=get_main_menu_keyboard(query.from_user.id)
            )
            return
        
        context.user_data['material_index'] = 0
        context.user_data['current_stage'] = stage
        context.user_data['current_materials'] = materials
        
        await show_material_page(update, context)
    except Exception as e:
        logger.error(f"Error in show_stage_materials: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def show_material_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        idx = context.user_data.get('material_index', 0)
        materials = context.user_data.get('current_materials', [])
        stage = context.user_data.get('current_stage', '')
        
        if not materials or idx >= len(materials):
            await query.edit_message_text(
                "❌ لا توجد مواد لعرضها.",
                reply_markup=get_main_menu_keyboard(query.from_user.id)
            )
            return
        
        material = materials[idx]
        
        keyboard = []
        
        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="material_prev"))
        
        nav_buttons.append(InlineKeyboardButton(f"{idx+1}/{len(materials)}", callback_data="noop"))
        
        if idx < len(materials) - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="material_next"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("📥 تحميل الملف", callback_data=f"download_material_{material['material_id']}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="service_materials")])
        
        material_text = f"""
        📖 *{material['title']}*
        
        📝 *الوصف:*
        {material['description']}
        
        🎓 *المرحلة:* {stage}
        📅 *تاريخ الإضافة:* {format_date(material['added_at'])}
        """
        
        await query.edit_message_text(
            material_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_material_page: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def navigate_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "material_prev":
            context.user_data['material_index'] -= 1
        elif query.data == "material_next":
            context.user_data['material_index'] += 1
        
        await show_material_page(update, context)
    except Exception as e:
        logger.error(f"Error in navigate_materials: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def download_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        material_id = int(query.data.replace("download_material_", ""))
        materials = context.user_data.get('current_materials', [])
        
        material = next((m for m in materials if m['material_id'] == material_id), None)
        
        if not material:
            await query.edit_message_text("❌ الملف غير متوفر.")
            return
        
        try:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=material['file_id'],
                caption=f"📥 {material['title']}"
            )
            
            await query.edit_message_text(
                f"✅ *تم إرسال الملف بنجاح*\n\n{material['title']}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            await query.edit_message_text("❌ حدث خطأ أثناء إرسال الملف.")
    except Exception as e:
        logger.error(f"Error in download_material: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

# ====================== نظام VIP ======================
async def vip_lectures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_service_active('vip_lectures'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        lectures = db.get_approved_lectures(limit=50)
        
        if not lectures:
            await query.edit_message_text(
                "🎬 *محاضرات VIP*\n\n📭 لا توجد محاضرات متاحة حالياً.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        if 'lecture_index' not in context.user_data:
            context.user_data['lecture_index'] = 0
            context.user_data['current_lectures'] = lectures
        
        idx = context.user_data['lecture_index']
        lecture = context.user_data['current_lectures'][idx]
        
        keyboard = []
        
        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="lecture_prev"))
        
        nav_buttons.append(InlineKeyboardButton(f"{idx+1}/{len(lectures)}", callback_data="noop"))
        
        if idx < len(lectures) - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="lecture_next"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        if lecture['price'] > 0:
            price_text = f"💵 {format_currency(lecture['price'])}"
            keyboard.append([InlineKeyboardButton(f"🛒 شراء المحاضرة ({price_text})", 
                           callback_data=f"buy_lecture_{lecture['lecture_id']}")])
        else:
            keyboard.append([InlineKeyboardButton("📥 تحميل مجاني", 
                           callback_data=f"download_lecture_{lecture['lecture_id']}")])
        
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="start")])
        
        avg_rating = 0
        if lecture['rating_count'] > 0:
            avg_rating = lecture['rating_total'] / lecture['rating_count']
        
        lecture_text = f"""
        🎬 *{lecture['title']}*
        
        👨‍🏫 *المدرس:* {lecture['first_name']}
        
        📝 *الوصف:*
        {lecture['description']}
        
        💰 *السعر:* {format_currency(lecture['price']) if lecture['price'] > 0 else 'مجاني'}
        👁️ *المشاهدات:* {lecture['views']:,}
        🛒 *المبيعات:* {lecture['purchases']:,}
        ⭐ *التقييم:* {avg_rating:.1f}/5
        📅 *تاريخ النشر:* {format_date(lecture['created_at'])}
        """
        
        await query.edit_message_text(
            lecture_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in vip_lectures: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def navigate_lectures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "lecture_prev":
            context.user_data['lecture_index'] -= 1
        elif query.data == "lecture_next":
            context.user_data['lecture_index'] += 1
        
        await vip_lectures(update, context)
    except Exception as e:
        logger.error(f"Error in navigate_lectures: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def download_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        lecture_id = int(query.data.replace("download_lecture_", ""))
        user_id = query.from_user.id
        
        lecture = db.get_lecture_by_id(lecture_id)
        if not lecture:
            await query.edit_message_text("❌ المحاضرة غير متاحة.")
            return
        
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=lecture['file_id'],
                caption=f"🎬 *{lecture['title']}*"
            )
            
            db.update_lecture_stats(lecture_id)
            
            await query.edit_message_text(
                f"✅ *تم تحميل المحاضرة بنجاح*\n\n{lecture['title']}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard(user_id)
            )
        except:
            await query.edit_message_text("❌ حدث خطأ أثناء إرسال المحاضرة.")
    except Exception as e:
        logger.error(f"Error in download_lecture: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def buy_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        lecture_id = int(query.data.replace("buy_lecture_", ""))
        user_id = query.from_user.id
        
        lecture = db.get_lecture_by_id(lecture_id)
        if not lecture:
            await query.edit_message_text("❌ المحاضرة غير متاحة.")
            return
        
        user_balance = db.get_user_balance(user_id)
        if user_balance < lecture['price']:
            await query.edit_message_text(
                f"❌ رصيدك غير كافي.\n\n💰 سعر المحاضرة: {format_currency(lecture['price'])}\n🏦 رصيدك: {format_currency(user_balance)}",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        if not db.deduct_balance(user_id, lecture['price']):
            await query.edit_message_text("❌ فشل في عملية الشراء.")
            return
        
        if db.add_vip_sale(lecture_id, user_id, lecture['price']):
            try:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=lecture['file_id'],
                    caption=f"✅ *تم شراء المحاضرة بنجاح*\n\n🎬 *{lecture['title']}*"
                )
                
                await query.edit_message_text(
                    f"""
                    ✅ *تم شراء المحاضرة بنجاح*
                    
                    🎬 {lecture['title']}
                    💰 السعر: {format_currency(lecture['price'])}
                    🏦 رصيدك المتبقي: {format_currency(db.get_user_balance(user_id))}
                    """,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_menu_keyboard(user_id)
                )
                
            except:
                await query.edit_message_text("❌ حدث خطأ أثناء إرسال الملف.")
                db.add_balance(user_id, lecture['price'])
        else:
            await query.edit_message_text("❌ فشل في عملية الشراء.")
            db.add_balance(user_id, lecture['price'])
    except Exception as e:
        logger.error(f"Error in buy_lecture: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def vip_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_service_active('vip_subscribe'):
            await query.edit_message_text(
                "⏸️ هذه الخدمة معطلة مؤقتاً من قبل الإدارة.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        if db.is_vip_subscriber(user_id):
            vip_info = db.get_vip_subscriber(user_id)
            expiry_date = datetime.datetime.fromisoformat(vip_info['expiry_date'].replace('Z', '+00:00'))
            
            await query.edit_message_text(
                f"""
                👑 *أنت مشترك في VIP بالفعل*
                
                📅 تاريخ الاشتراك: {format_date(vip_info['subscription_date'])}
                ⏳ تاريخ الانتهاء: {format_date(expiry_date)}
                📅 المتبقي: {(expiry_date - datetime.datetime.now()).days} يوم
                """,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        subscription_price = db.get_vip_subscription_price()
        
        keyboard = [
            [InlineKeyboardButton(f"💳 اشتراك شهري ({format_currency(subscription_price)})", 
             callback_data="confirm_vip_subscription")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
        ]
        
        subscription_text = f"""
        👑 *اشتراك VIP للمدرسين*
        
        *المميزات:*
        ✅ رفع محاضرات فيديو
        ✅ رفع محاضرات PDF
        ✅ تحديد سعر المحاضرة
        ✅ كسب 60% من المبيعات
        
        *معلومات الدفع:*
        💰 السعر الشهري: {format_currency(subscription_price)}
        ⏳ المدة: 30 يوم
        """
        
        await query.edit_message_text(
            subscription_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in vip_subscribe: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def confirm_vip_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        subscription_price = db.get_vip_subscription_price()
        
        user_balance = db.get_user_balance(user_id)
        if user_balance < subscription_price:
            await query.edit_message_text(
                f"❌ رصيدك غير كافي.\n\n💰 سعر الاشتراك: {format_currency(subscription_price)}\n🏦 رصيدك: {format_currency(user_balance)}",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        if not db.deduct_balance(user_id, subscription_price):
            await query.edit_message_text("❌ فشل في عملية الاشتراك.")
            return
        
        db.add_vip_subscriber(user_id, 30)
        db.add_transaction(user_id, -subscription_price, 'payment', 'vip_subscription', 'اشتراك VIP شهري')
        
        await query.edit_message_text(
            f"""
            ✅ *تم الاشتراك في VIP بنجاح*
            
            👑 *مبروك! أنت الآن مدرس VIP*
            
            📅 تاريخ الاشتراك: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
            ⏳ تاريخ الانتهاء: {(datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M')}
            💰 السعر: {format_currency(subscription_price)}
            🏦 رصيدك المتبقي: {format_currency(db.get_user_balance(user_id))}
            
            🎬 *يمكنك الآن:*
            1. 📤 رفع محاضرة فيديو
            2. 📚 رفع محاضرة PDF
            3. 💰 كسب الأرباح (60% من المبيعات)
            """,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error in confirm_vip_subscription: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def vip_upload_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_vip_subscriber(user_id):
            await query.edit_message_text(
                "❌ هذه الميزة للمشتركين في VIP فقط.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        instructions = """
        📤 *رفع محاضرة جديدة*
        
        *خطوات رفع المحاضرة:*
        1. أرسل ملف الفيديو
        2. أدخل عنوان المحاضرة
        3. أدخل وصف المحاضرة
        4. أدخل السعر (أو 0 للمجانية)
        
        *ملاحظات:*
        ⚠️ سيتم مراجعة المحاضرة قبل النشر
        ⚠️ المحتوى يجب أن يكون تعليمياً
        
        *أرسل ملف الفيديو الآن:*
        """
        
        context.user_data['uploading_lecture'] = True
        
        await query.edit_message_text(
            instructions,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return VIP_LECTURE_FILE
    except Exception as e:
        logger.error(f"Error in vip_upload_lecture: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_lecture_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        if not update.message.video and not update.message.document:
            await update.message.reply_text("❌ يرجى إرسال ملف فيديو:")
            return VIP_LECTURE_FILE
        
        file_id = None
        
        if update.message.video:
            file_id = update.message.video.file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        
        context.user_data['lecture_file_id'] = file_id
        
        await update.message.reply_text("✅ تم استلام الملف.\n*أدخل عنوان المحاضرة:*", parse_mode=ParseMode.MARKDOWN)
        return VIP_LECTURE_TITLE
    except Exception as e:
        logger.error(f"Error in process_vip_lecture_file: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_lecture_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['lecture_title'] = update.message.text
        await update.message.reply_text("✅ تم حفظ العنوان.\n*أدخل وصف المحاضرة:*")
        return VIP_LECTURE_DESC
    except Exception as e:
        logger.error(f"Error in process_vip_lecture_title: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_lecture_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['lecture_desc'] = update.message.text
        await update.message.reply_text("✅ تم حفظ الوصف.\n*أدخل سعر المحاضرة (أو 0 للمجانية):*")
        return VIP_LECTURE_PRICE
    except Exception as e:
        logger.error(f"Error in process_vip_lecture_desc: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_lecture_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        if price < 0:
            await update.message.reply_text("❌ السعر يجب أن يكون صفر أو أكثر:")
            return VIP_LECTURE_PRICE
        
        user_id = update.effective_user.id
        
        file_id = context.user_data.get('lecture_file_id')
        title = context.user_data.get('lecture_title')
        description = context.user_data.get('lecture_desc')
        
        lecture_id = db.add_vip_lecture(user_id, file_id, title, description, price)
        
        context.user_data.pop('uploading_lecture', None)
        context.user_data.pop('lecture_file_id', None)
        context.user_data.pop('lecture_title', None)
        context.user_data.pop('lecture_desc', None)
        
        await update.message.reply_text(f"""
        ✅ *تم رفع المحاضرة بنجاح*
        
        🎬 *العنوان:* {title}
        💰 *السعر:* {format_currency(price) if price > 0 else 'مجاني'}
        📝 *رقم المحاضرة:* #{lecture_id}
        
        ⏳ *جاري مراجعة المحاضرة...*
        """, parse_mode=ParseMode.MARKDOWN)
        
        if is_admin(ADMIN_ID):
            approve_keyboard = [
                [
                    InlineKeyboardButton("✅ الموافقة", callback_data=f"admin_approve_lecture_{lecture_id}"),
                    InlineKeyboardButton("❌ الرفض", callback_data=f"admin_reject_lecture_{lecture_id}")
                ]
            ]
            
            admin_msg = f"""
            🎬 *محاضرة جديدة تحتاج موافقة*
            
            👨‍🏫 المدرس: {update.effective_user.first_name} (ID: {user_id})
            🎬 العنوان: {title}
            💰 السعر: {format_currency(price) if price > 0 else 'مجاني'}
            
            #محاضرة_{lecture_id}
            """
            
            try:
                await context.bot.send_video(
                    ADMIN_ID,
                    video=file_id,
                    caption=admin_msg,
                    reply_markup=InlineKeyboardMarkup(approve_keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                await context.bot.send_message(
                    ADMIN_ID,
                    admin_msg,
                    reply_markup=InlineKeyboardMarkup(approve_keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح:")
        return VIP_LECTURE_PRICE
    except Exception as e:
        logger.error(f"Error in process_vip_lecture_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def vip_upload_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_vip_subscriber(user_id):
            await query.edit_message_text(
                "❌ هذه الميزة للمشتركين في VIP فقط.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        instructions = """
        📚 *رفع محاضرة PDF جديدة*
        
        *خطوات رفع المحاضرة:*
        1. أرسل ملف PDF
        2. أدخل عنوان المحاضرة
        3. أدخل وصف المحاضرة
        4. أدخل السعر (أو 0 للمجانية)
        
        *ملاحظات:*
        ⚠️ سيتم مراجعة المحاضرة قبل النشر
        ⚠️ المحتوى يجب أن يكون تعليمياً
        
        *أرسل ملف PDF الآن:*
        """
        
        context.user_data['uploading_pdf'] = True
        
        await query.edit_message_text(
            instructions,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "PDF_LECTURE_FILE"
    except Exception as e:
        logger.error(f"Error in vip_upload_pdf: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        if not update.message.document:
            await update.message.reply_text("❌ يرجى إرسال ملف PDF:")
            return "PDF_LECTURE_FILE"
        
        file_name = update.message.document.file_name or ""
        if not file_name.lower().endswith('.pdf'):
            await update.message.reply_text("❌ الملف يجب أن يكون بصيغة PDF:")
            return "PDF_LECTURE_FILE"
        
        file_id = update.message.document.file_id
        context.user_data['pdf_file_id'] = file_id
        
        await update.message.reply_text("✅ تم استلام الملف.\n*أدخل عنوان المحاضرة:*", parse_mode=ParseMode.MARKDOWN)
        return "PDF_LECTURE_TITLE"
    except Exception as e:
        logger.error(f"Error in process_vip_pdf_file: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_pdf_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['pdf_title'] = update.message.text
        await update.message.reply_text("✅ تم حفظ العنوان.\n*أدخل وصف المحاضرة:*")
        return "PDF_LECTURE_DESC"
    except Exception as e:
        logger.error(f"Error in process_vip_pdf_title: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_pdf_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['pdf_desc'] = update.message.text
        await update.message.reply_text("✅ تم حفظ الوصف.\n*أدخل سعر المحاضرة (أو 0 للمجانية):*")
        return "PDF_LECTURE_PRICE"
    except Exception as e:
        logger.error(f"Error in process_vip_pdf_desc: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_pdf_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        if price < 0:
            await update.message.reply_text("❌ السعر يجب أن يكون صفر أو أكثر:")
            return "PDF_LECTURE_PRICE"
        
        user_id = update.effective_user.id
        
        file_id = context.user_data.get('pdf_file_id')
        title = context.user_data.get('pdf_title')
        description = context.user_data.get('pdf_desc')
        
        pdf_id = db.add_vip_pdf_lecture(user_id, file_id, title, description, price)
        
        context.user_data.pop('uploading_pdf', None)
        context.user_data.pop('pdf_file_id', None)
        context.user_data.pop('pdf_title', None)
        context.user_data.pop('pdf_desc', None)
        
        await update.message.reply_text(f"""
        ✅ *تم رفع المحاضرة PDF بنجاح*
        
        📚 *العنوان:* {title}
        💰 *السعر:* {format_currency(price) if price > 0 else 'مجاني'}
        📝 *رقم المحاضرة:* #{pdf_id}
        
        ⏳ *جاري مراجعة المحاضرة...*
        """, parse_mode=ParseMode.MARKDOWN)
        
        if is_admin(ADMIN_ID):
            approve_keyboard = [
                [
                    InlineKeyboardButton("✅ الموافقة", callback_data=f"admin_approve_pdf_{pdf_id}"),
                    InlineKeyboardButton("❌ الرفض", callback_data=f"admin_reject_pdf_{pdf_id}")
                ]
            ]
            
            admin_msg = f"""
            📚 *محاضرة PDF جديدة تحتاج موافقة*
            
            👨‍🏫 المدرس: {update.effective_user.first_name} (ID: {user_id})
            📚 العنوان: {title}
            💰 السعر: {format_currency(price) if price > 0 else 'مجاني'}
            
            #pdf_محاضرة_{pdf_id}
            """
            
            await context.bot.send_document(
                ADMIN_ID,
                document=file_id,
                caption=admin_msg,
                reply_markup=InlineKeyboardMarkup(approve_keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح:")
        return "PDF_LECTURE_PRICE"
    except Exception as e:
        logger.error(f"Error in process_vip_pdf_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def vip_my_lectures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_vip_subscriber(user_id):
            await query.edit_message_text(
                "❌ هذه الميزة للمشتركين في VIP فقط.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        lectures = db.get_teacher_lectures(user_id)
        pdf_lectures = db.get_teacher_pdf_lectures(user_id)
        
        if not lectures and not pdf_lectures:
            await query.edit_message_text(
                "📭 لم تقم برفع أي محاضرات بعد.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        lectures_text = "🎬 *محاضراتي*\n\n"
        
        if lectures:
            lectures_text += "*محاضرات الفيديو:*\n"
            for lecture in lectures:
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌',
                    'deleted': '🗑️'
                }.get(lecture['status'], '❓')
                
                price_text = format_currency(lecture['price']) if lecture['price'] > 0 else 'مجاني'
                
                lectures_text += f"""
                {status_emoji} *{lecture['title']}* #{lecture['lecture_id']}
                💰 السعر: {price_text}
                📊 الحالة: {lecture['status']}
                
                """
        
        if pdf_lectures:
            lectures_text += "\n*محاضرات PDF:*\n"
            for lecture in pdf_lectures:
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌',
                    'deleted': '🗑️'
                }.get(lecture['status'], '❓')
                
                price_text = format_currency(lecture['price']) if lecture['price'] > 0 else 'مجاني'
                
                lectures_text += f"""
                {status_emoji} *{lecture['title']}* #{lecture['pdf_id']}
                💰 السعر: {price_text}
                📊 الحالة: {lecture['status']}
                
                """
        
        keyboard = [
            [InlineKeyboardButton("📤 رفع محاضرة فيديو", callback_data="vip_upload_lecture"),
             InlineKeyboardButton("📚 رفع محاضرة PDF", callback_data="vip_upload_pdf")],
            [InlineKeyboardButton("💰 رصيد أرباحي", callback_data="vip_my_earnings")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
        ]
        
        await query.edit_message_text(
            lectures_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in vip_my_lectures: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def vip_my_pdfs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_vip_subscriber(user_id):
            await query.edit_message_text(
                "❌ هذه الميزة للمشتركين في VIP فقط.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        pdf_lectures = db.get_teacher_pdf_lectures(user_id)
        
        if not pdf_lectures:
            await query.edit_message_text(
                "📭 لم تقم برفع أي محاضرات PDF بعد.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        pdfs_text = "📚 *محاضراتي PDF*\n\n"
        
        for lecture in pdf_lectures:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌',
                'deleted': '🗑️'
            }.get(lecture['status'], '❓')
            
            price_text = format_currency(lecture['price']) if lecture['price'] > 0 else 'مجاني'
            
            pdfs_text += f"""
            {status_emoji} *{lecture['title']}* #{lecture['pdf_id']}
            💰 السعر: {price_text}
            📊 الحالة: {lecture['status']}
            👁️ المشاهدات: {lecture['views']:,}
            🛒 المبيعات: {lecture['purchases']:,}
            
            """
        
        keyboard = [
            [InlineKeyboardButton("📚 رفع محاضرة PDF جديدة", callback_data="vip_upload_pdf")],
            [InlineKeyboardButton("🎬 محاضرات الفيديو", callback_data="vip_my_lectures")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
        ]
        
        await query.edit_message_text(
            pdfs_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in vip_my_pdfs: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def vip_my_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not db.is_vip_subscriber(user_id):
            await query.edit_message_text(
                "❌ هذه الميزة للمشتركين في VIP فقط.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        earnings = db.get_vip_earnings(user_id)
        
        if not earnings:
            earnings_text = """
            💰 *أرباحي*
            
            📭 لا توجد أرباح حالياً.
            
            🎬 ارفع محاضرات وابدأ بيعها لكسب الأرباح.
            💵 ستحصل على 60% من سعر كل محاضرة تباع.
            """
        else:
            earnings_text = f"""
            💰 *أرباحي*
            
            💵 *إجمالي الأرباح:* {format_currency(earnings['total_earnings'])}
            🏦 *الرصيد المتاح للسحب:* {format_currency(earnings['available_balance'])}
            💸 *المسحوب سابقاً:* {format_currency(earnings['withdrawn_balance'])}
            
            *ملاحظات:*
            • تحصل على 60% من سعر كل محاضرة تباع
            • يمكنك سحب الأرباح عبر التواصل مع الدعم الفني
            """
        
        keyboard = [
            [InlineKeyboardButton("🎬 محاضراتي", callback_data="vip_my_lectures")],
            [InlineKeyboardButton("📤 رفع محاضرة", callback_data="vip_upload_lecture")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
        ]
        
        await query.edit_message_text(
            earnings_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in vip_my_earnings: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

# ====================== معالجات المساعدة العامة ======================
async def invite_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        invite_reward = db.get_invite_reward()
        invite_link = generate_invite_link(user_id)
        
        invite_text = f"""
        👥 *دعوة صديق*
        
        🔗 *رابط الدعوة الخاص بك:*
        `{invite_link}`
        
        🎁 *مكافأة الدعوة:*
        • أنت: {format_currency(invite_reward)} لكل صديق يسجل
        • صديقك: 1000 دينار هدية ترحيبية
        
        📊 *عدد المدعوين:* {user_data['total_invites']} صديق
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 نسخ الرابط", callback_data="copy_invite_link")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="start")]
        ]
        
        await query.edit_message_text(
            invite_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in invite_friend: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def copy_invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📋 تم نسخ الرابط", show_alert=True)
    
    try:
        user_id = query.from_user.id
        invite_link = generate_invite_link(user_id)
        
        await query.edit_message_text(
            f"🔗 *رابط الدعوة:*\n\n`{invite_link}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error in copy_invite_link: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        transactions = db.get_user_transactions(user_id, limit=5)
        exemptions = db.get_user_exemptions(user_id)
        
        stats_text = f"""
        📊 *إحصائياتي*
        
        👤 *المعلومات الشخصية:*
        • الاسم: {user_data['first_name']} {user_data['last_name'] or ''}
        • الرصيد: {format_currency(user_data['balance'])}
        • تاريخ التسجيل: {format_date(user_data['created_at'])}
        
        📈 *النشاط:*
        • عدد عمليات حساب الإعفاء: {len(exemptions)}
        • عدد المدعوين: {user_data['total_invites']}
        
        💰 *آخر العمليات:*
        """
        
        if transactions:
            for trans in transactions:
                emoji = "➕" if trans['amount'] > 0 else "➖"
                amount = abs(trans['amount'])
                stats_text += f"\n{emoji} {format_currency(amount)} - {trans['description'][:30]}"
        else:
            stats_text += "\n📭 لا توجد عمليات سابقة."
        
        stats_text += f"\n\n📞 الدعم الفني: {SUPPORT_USERNAME}"
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error in my_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def my_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            await query.edit_message_text("❌ حسابك غير مسجل.")
            return
        
        balance_msg = f"""
        💰 *رصيدك الحالي*
        
        🏦 الرصيد: {format_currency(user_data['balance'])}
        
        🔗 رابط الدعوة الخاص بك:
        `{generate_invite_link(user_id)}`
        
        🎁 مكافأة الدعوة: {format_currency(db.get_invite_reward())}
        """
        
        await query.edit_message_text(
            balance_msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error in my_balance: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

# ====================== لوحة التحكم ======================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        
        if not is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية للوصول إلى لوحة التحكم.")
            return
        
        admin_text = """
        🛠️ *لوحة التحكم - المشرف*
        
        *الإحصائيات السريعة:*
        """
        
        total_users = db.get_user_count()
        active_users = db.get_active_users_count(7)
        vip_subscribers = len(db.get_all_vip_subscribers())
        pending_lectures = len(db.get_pending_lectures())
        pending_questions = len(db.get_pending_questions())
        
        admin_text += f"""
        👥 المستخدمين: {total_users:,}
        📱 النشطين (أسبوع): {active_users:,}
        👑 مشتركي VIP: {vip_subscribers:,}
        ⏳ محاضرات منتظرة: {pending_lectures}
        ❓ أسئلة منتظرة: {pending_questions}
        
        *اختر القسم الذي تريد إدارته:*
        """
        
        await query.edit_message_text(
            admin_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

# ====================== إدارة المستخدمين ======================
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "👥 *إدارة المستخدمين*\n\nاختر الإجراء المطلوب:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_users_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_users: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("admin_users_list_", "")
        page = int(data) if data.isdigit() else 1
        
        limit = 10
        offset = (page - 1) * limit
        
        users = db.get_all_users(limit=limit, offset=offset)
        
        if not users:
            await query.edit_message_text("📭 لا يوجد مستخدمين في هذه الصفحة.")
            return
        
        users_text = f"👥 *المستخدمين - الصفحة {page}*\n\n"
        
        for user in users:
            status = "🚫 محظور" if user['is_banned'] else "✅ نشط"
            vip_status = "👑 VIP" if user['is_vip'] else "👤 عادي"
            
            users_text += f"""
            👤 {user['first_name']} {user['last_name'] or ''}
            🆔 {user['user_id']} | @{user['username'] or 'بدون'}
            💰 {format_currency(user['balance'])} | {status} | {vip_status}
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = []
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_users_list_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"صفحة {page}", callback_data="noop"))
        
        total_users = db.get_user_count()
        if offset + limit < total_users:
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"admin_users_list_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([
            InlineKeyboardButton("🚫 حظر", callback_data=f"admin_ban_user_page_{page}"),
            InlineKeyboardButton("✅ فك حظر", callback_data=f"admin_unban_user_page_{page}")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")])
        
        await query.edit_message_text(
            users_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_users_list: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("admin_ban_user_page_", "")
        page = int(data) if data.isdigit() else 0
        
        if page > 0:
            await query.edit_message_text(
                f"🚫 *حظر مستخدم - الصفحة {page}*\n\nأرسل أيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['ban_page'] = page
        else:
            await query.edit_message_text(
                "🚫 *حظر مستخدم*\n\nأرسل أيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN
            )
        
        return "BAN_USER"
    except Exception as e:
        logger.error(f"Error in admin_ban_user: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ المستخدم غير موجود:")
            return "BAN_USER"
        
        if user_id == ADMIN_ID:
            await update.message.reply_text("❌ لا يمكن حظر المشرف الرئيسي.")
            return "BAN_USER"
        
        if user_data['is_banned']:
            await update.message.reply_text("⚠️ هذا المستخدم محظور بالفعل.")
            return "BAN_USER"
        
        db.ban_user(user_id)
        
        try:
            await update.message.bot.send_message(
                user_id,
                "🚫 *حسابك تم حظره*",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        
        page = context.user_data.get('ban_page', 0)
        if page > 0:
            await update.message.reply_text(
                f"✅ تم حظر المستخدم {user_data['first_name']} (ID: {user_id})",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة", 
                callback_data=f"admin_users_list_{page}")]])
            )
        else:
            await update.message.reply_text(
                f"✅ تم حظر المستخدم {user_data['first_name']} (ID: {user_id})",
                reply_markup=get_admin_keyboard()
            )
        
        context.user_data.pop('ban_page', None)
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return "BAN_USER"
    except Exception as e:
        logger.error(f"Error in process_ban_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("admin_unban_user_page_", "")
        page = int(data) if data.isdigit() else 0
        
        if page > 0:
            await query.edit_message_text(
                f"✅ *فك حظر مستخدم - الصفحة {page}*\n\nأرسل أيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['unban_page'] = page
        else:
            await query.edit_message_text(
                "✅ *فك حظر مستخدم*\n\nأرسل أيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN
            )
        
        return "UNBAN_USER"
    except Exception as e:
        logger.error(f"Error in admin_unban_user: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ المستخدم غير موجود:")
            return "UNBAN_USER"
        
        if not user_data['is_banned']:
            await update.message.reply_text("⚠️ هذا المستخدم غير محظور.")
            return "UNBAN_USER"
        
        db.unban_user(user_id)
        
        try:
            await update.message.bot.send_message(
                user_id,
                "✅ *تم فك حظر حسابك*",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        
        page = context.user_data.get('unban_page', 0)
        if page > 0:
            await update.message.reply_text(
                f"✅ تم فك حظر المستخدم {user_data['first_name']} (ID: {user_id})",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة", 
                callback_data=f"admin_users_list_{page}")]])
            )
        else:
            await update.message.reply_text(
                f"✅ تم فك حظر المستخدم {user_data['first_name']} (ID: {user_id})",
                reply_markup=get_admin_keyboard()
            )
        
        context.user_data.pop('unban_page', None)
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return "UNBAN_USER"
    except Exception as e:
        logger.error(f"Error in process_unban_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "🔍 *بحث عن مستخدم*\n\nأرسل أيدي المستخدم أو اسمه:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "SEARCH_USER"
    except Exception as e:
        logger.error(f"Error in admin_search_user: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        search_term = update.message.text
        
        users = db.search_users(search_term)
        
        if not users:
            await update.message.reply_text("❌ لم يتم العثور على مستخدمين.")
            return ConversationHandler.END
        
        users_text = "🔍 *نتائج البحث*\n\n"
        
        for user in users:
            status = "🚫 محظور" if user['is_banned'] else "✅ نشط"
            vip_status = "👑 VIP" if user['is_vip'] else "👤 عادي"
            
            users_text += f"""
            👤 {user['first_name']} {user['last_name'] or ''}
            🆔 {user['user_id']} | @{user['username'] or 'بدون'}
            💰 {format_currency(user['balance'])} | {status} | {vip_status}
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = [
            [InlineKeyboardButton("🚫 حظر", callback_data="admin_ban_user"),
             InlineKeyboardButton("✅ فك حظر", callback_data="admin_unban_user")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")]
        ]
        
        await update.message.reply_text(
            users_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in process_search_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "👑 *رفع مستخدم إلى مشرف*\n\nأرسل أيدي المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "PROMOTE_USER"
    except Exception as e:
        logger.error(f"Error in admin_promote_user: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ المستخدم غير موجود:")
            return "PROMOTE_USER"
        
        if user_data['is_admin']:
            await update.message.reply_text("⚠️ هذا المستخدم مشرف بالفعل.")
            return "PROMOTE_USER"
        
        db.promote_to_admin(user_id)
        
        try:
            await update.message.bot.send_message(
                user_id,
                "👑 *مبروك! تم رفعك إلى مشرف*",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        
        await update.message.reply_text(
            f"✅ تم رفع المستخدم {user_data['first_name']} (ID: {user_id}) إلى مشرف",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return "PROMOTE_USER"
    except Exception as e:
        logger.error(f"Error in process_promote_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("admin_transactions_", "")
        page = int(data) if data.isdigit() else 1
        
        limit = 10
        offset = (page - 1) * limit
        
        transactions = db.get_all_transactions(limit=limit, offset=offset)
        
        if not transactions:
            await query.edit_message_text("📭 لا توجد معاملات في هذه الصفحة.")
            return
        
        transactions_text = f"📋 *سجل المعاملات - الصفحة {page}*\n\n"
        
        for trans in transactions:
            user_name = trans['username'] or trans['first_name'] or f"المستخدم {trans['user_id']}"
            amount = trans['amount']
            type_icon = "➕" if amount > 0 else "➖"
            
            transactions_text += f"""
            {type_icon} *{user_name}*
            💰 {format_currency(abs(amount))} - {trans['type']}
            📅 {format_date(trans['created_at'])}
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = []
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_transactions_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"صفحة {page}", callback_data="noop"))
        
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"admin_transactions_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")])
        
        await query.edit_message_text(
            transactions_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_transactions: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_manage_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        questions = db.get_pending_questions()
        
        if not questions:
            await query.edit_message_text("✅ لا توجد أسئلة منتظرة.")
            return
        
        if 'question_index' not in context.user_data:
            context.user_data['question_index'] = 0
            context.user_data['current_questions'] = questions
        
        idx = context.user_data['question_index']
        question = context.user_data['current_questions'][idx]
        
        keyboard = []
        
        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="question_prev"))
        
        nav_buttons.append(InlineKeyboardButton(f"{idx+1}/{len(questions)}", callback_data="noop"))
        
        if idx < len(questions) - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="question_next"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([
            InlineKeyboardButton("✅ الموافقة", callback_data=f"admin_approve_question_{question['question_id']}"),
            InlineKeyboardButton("❌ الرفض", callback_data=f"admin_reject_question_{question['question_id']}")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")])
        
        question_text = f"""
        ❓ *سؤال منتظر* #{question['question_id']}
        
        👤 *الطالب:* {question['first_name']}
        
        📝 *السؤال:*
        {question['question_text'][:300]}
        """
        
        await query.edit_message_text(
            question_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_manage_questions: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def navigate_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "question_prev":
            context.user_data['question_index'] -= 1
        elif query.data == "question_next":
            context.user_data['question_index'] += 1
        
        await admin_manage_questions(update, context)
    except Exception as e:
        logger.error(f"Error in navigate_questions: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_approve_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        question_id = int(query.data.replace("admin_approve_question_", ""))
        
        if db.approve_question(question_id, query.from_user.id):
            question = db.get_question_by_id(question_id)
            
            if question:
                try:
                    student_msg = f"""
                    ✅ *تمت الموافقة على سؤالك*
                    
                    ❓ سؤالك: {question['question_text'][:100]}
                    """
                    await context.bot.send_message(question['user_id'], student_msg, parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ تمت الموافقة على السؤال #{question_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في الموافقة على السؤال #{question_id}",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in admin_approve_question: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_reject_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        question_id = int(query.data.replace("admin_reject_question_", ""))
        
        question = db.get_question_by_id(question_id)
        
        if db.reject_question(question_id):
            if question:
                try:
                    student_msg = f"""
                    ❌ *تم رفض سؤالك*
                    
                    ❓ سؤالك: {question['question_text'][:100]}
                    """
                    await context.bot.send_message(question['user_id'], student_msg, parse_mode=ParseMode.MARKDOWN)
                    
                    db.add_balance(question['user_id'], question['price_paid'])
                    db.add_transaction(question['user_id'], question['price_paid'], 'refund', 'help_student', 'استرجاع رصيد')
                except:
                    pass
            
            await query.edit_message_text(
                f"❌ تم رفض السؤال #{question_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في رفض السؤال #{question_id}",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in admin_reject_question: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

# ====================== إدارة الشحن والخصم ======================
async def admin_finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "💰 *إدارة الشحن والخصم*\n\nاختر الإجراء المطلوب:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_finance_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_finance: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "💰 *شحن رصيد*\n\nأرسل أيدي المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_CHARGE_USER
    except Exception as e:
        logger.error(f"Error in admin_charge: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_charge_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ المستخدم غير موجود:")
            return ADMIN_CHARGE_USER
        
        context.user_data['charge_user_id'] = user_id
        context.user_data['charge_user_name'] = user_data['first_name']
        
        await update.message.reply_text(
            f"👤 المستخدم: {user_data['first_name']} (ID: {user_id})\n"
            f"🏦 الرصيد الحالي: {format_currency(user_data['balance'])}\n\n"
            f"💵 أرسل المبلغ:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_CHARGE_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return ADMIN_CHARGE_USER
    except Exception as e:
        logger.error(f"Error in process_charge_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_charge_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ المبلغ يجب أن يكون أكبر من صفر:")
            return ADMIN_CHARGE_AMOUNT
        
        user_id = context.user_data.get('charge_user_id')
        user_name = context.user_data.get('charge_user_name')
        admin_id = update.effective_user.id
        
        db.add_balance(user_id, amount)
        db.add_transaction(user_id, amount, 'charge', 'admin', 
                          f'شحن من المشرف {admin_id}', admin_id)
        
        try:
            await update.message.bot.send_message(
                user_id,
                f"💰 *تم شحن رصيدك*\n\n"
                f"✅ المبلغ: {format_currency(amount)}\n"
                f"🏦 الرصيد الجديد: {format_currency(db.get_user_balance(user_id))}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        
        await update.message.reply_text(
            f"✅ تم شحن {format_currency(amount)} للمستخدم {user_name} (ID: {user_id})",
            reply_markup=get_admin_keyboard()
        )
        
        context.user_data.pop('charge_user_id', None)
        context.user_data.pop('charge_user_name', None)
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال مبلغ صحيح:")
        return ADMIN_CHARGE_AMOUNT
    except Exception as e:
        logger.error(f"Error in process_charge_amount: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_deduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "💸 *خصم رصيد*\n\nأرسل أيدي المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_DEDUCT_USER
    except Exception as e:
        logger.error(f"Error in admin_deduct: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_deduct_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ المستخدم غير موجود:")
            return ADMIN_DEDUCT_USER
        
        context.user_data['deduct_user_id'] = user_id
        context.user_data['deduct_user_name'] = user_data['first_name']
        context.user_data['deduct_user_balance'] = user_data['balance']
        
        await update.message.reply_text(
            f"👤 المستخدم: {user_data['first_name']} (ID: {user_id})\n"
            f"🏦 الرصيد الحالي: {format_currency(user_data['balance'])}\n\n"
            f"💵 أرسل المبلغ:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_DEDUCT_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return ADMIN_DEDUCT_USER
    except Exception as e:
        logger.error(f"Error in process_deduct_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_deduct_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ المبلغ يجب أن يكون أكبر من صفر:")
            return ADMIN_DEDUCT_AMOUNT
        
        user_id = context.user_data.get('deduct_user_id')
        user_name = context.user_data.get('deduct_user_name')
        user_balance = context.user_data.get('deduct_user_balance')
        admin_id = update.effective_user.id
        
        if amount > user_balance:
            await update.message.reply_text(
                f"❌ المبلغ يتجاوز الرصيد المتاح.\n"
                f"🏦 الرصيد الحالي: {format_currency(user_balance)}\n\n"
                f"💵 أرسل مبلغاً أقل:"
            )
            return ADMIN_DEDUCT_AMOUNT
        
        if db.deduct_balance(user_id, amount):
            db.add_transaction(user_id, -amount, 'deduct', 'admin', 
                              f'خصم من المشرف {admin_id}', admin_id)
            
            try:
                await update.message.bot.send_message(
                    user_id,
                    f"💸 *تم خصم من رصيدك*\n\n"
                    f"❌ المبلغ: {format_currency(amount)}\n"
                    f"🏦 الرصيد الجديد: {format_currency(db.get_user_balance(user_id))}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
            
            await update.message.reply_text(
                f"✅ تم خصم {format_currency(amount)} من المستخدم {user_name} (ID: {user_id})",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text("❌ فشل في عملية الخصم.")
        
        context.user_data.pop('deduct_user_id', None)
        context.user_data.pop('deduct_user_name', None)
        context.user_data.pop('deduct_user_balance', None)
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال مبلغ صحيح:")
        return ADMIN_DEDUCT_AMOUNT
    except Exception as e:
        logger.error(f"Error in process_deduct_amount: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_finance_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        stats = db.get_financial_stats()
        
        stats_text = """
        📈 *الإحصائيات المالية*
        
        *إحصائيات شاملة:*
        """
        
        overall = stats.get('overall', {})
        today = stats.get('today', {})
        
        stats_text += f"""
        💰 إجمالي الشحنات: {format_currency(overall.get('total_charged', 0))}
        💸 إجمالي المدفوعات: {format_currency(overall.get('total_payments', 0))}
        🔄 إجمالي الخصومات: {format_currency(overall.get('total_deducted', 0))}
        ↩️ إجمالي الاسترجاعات: {format_currency(overall.get('total_refunds', 0))}
        
        *إحصائيات اليوم:*
        📅 المعاملات اليوم: {today.get('today_transactions', 0)}
        💰 الدخل اليوم: {format_currency(today.get('today_income', 0))}
        """
        
        services = stats.get('services', [])
        if services:
            stats_text += "\n\n*إحصائيات الخدمات:*"
            for service in services:
                stats_text += f"\n• {service['service']}: {service['count']:,} عملية - {format_currency(service['total_amount'])}"
        
        keyboard = [
            [InlineKeyboardButton("💰 شحن رصيد", callback_data="admin_charge"),
             InlineKeyboardButton("💸 خصم رصيد", callback_data="admin_deduct")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_finance")]
        ]
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_finance_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_deduct_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "💸 *خصم أرباح مدرس VIP*\n\nأرسل أيدي المدرس:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_VIP_DEDUCT_USER
    except Exception as e:
        logger.error(f"Error in admin_deduct_vip: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_deduct_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        
        if not db.is_vip_subscriber(user_id):
            await update.message.reply_text("❌ هذا المستخدم ليس مشتركاً في VIP:")
            return ADMIN_VIP_DEDUCT_USER
        
        earnings = db.get_vip_earnings(user_id)
        if not earnings or earnings['available_balance'] <= 0:
            await update.message.reply_text("❌ هذا المدرس لا يمتلك أرباحاً.")
            return ADMIN_VIP_DEDUCT_USER
        
        context.user_data['vip_deduct_user_id'] = user_id
        context.user_data['vip_deduct_balance'] = earnings['available_balance']
        
        await update.message.reply_text(
            f"👨‍🏫 المدرس: ID {user_id}\n"
            f"💰 الأرباح المتاحة: {format_currency(earnings['available_balance'])}\n\n"
            f"💵 أرسل المبلغ:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_VIP_DEDUCT_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return ADMIN_VIP_DEDUCT_USER
    except Exception as e:
        logger.error(f"Error in process_vip_deduct_user: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_vip_deduct_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ المبلغ يجب أن يكون أكبر من صفر:")
            return ADMIN_VIP_DEDUCT_AMOUNT
        
        user_id = context.user_data.get('vip_deduct_user_id')
        available_balance = context.user_data.get('vip_deduct_balance')
        
        if amount > available_balance:
            await update.message.reply_text(
                f"❌ المبلغ يتجاوز الأرباح المتاحة.\n"
                f"💰 الأرباح المتاحة: {format_currency(available_balance)}\n\n"
                f"💵 أرسل مبلغاً أقل:"
            )
            return ADMIN_VIP_DEDUCT_AMOUNT
        
        if db.deduct_vip_earnings(user_id, amount):
            try:
                teacher_msg = f"""
                💸 *تم سحب من أرباحك*
                
                ❌ المبلغ: {format_currency(amount)}
                🏦 الأرباح المتبقية: {format_currency(available_balance - amount)}
                """
                await update.message.bot.send_message(user_id, teacher_msg, parse_mode=ParseMode.MARKDOWN)
            except:
                pass
            
            await update.message.reply_text(
                f"✅ تم خصم {format_currency(amount)} من أرباح المدرس {user_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text("❌ فشل في عملية الخصم.")
        
        context.user_data.pop('vip_deduct_user_id', None)
        context.user_data.pop('vip_deduct_balance', None)
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال مبلغ صحيح:")
        return ADMIN_VIP_DEDUCT_AMOUNT
    except Exception as e:
        logger.error(f"Error in process_vip_deduct_amount: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

# ====================== إدارة VIP ======================
async def admin_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "👑 *إدارة نظام VIP*\n\nاختر القسم الذي تريد إدارته:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_vip_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_vip: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_vip_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("admin_vip_subscribers_", "")
        page = int(data) if data.isdigit() else 1
        
        subscribers = db.get_all_vip_subscribers()
        
        if not subscribers:
            await query.edit_message_text("📭 لا يوجد مشتركين في VIP حالياً.")
            return
        
        limit = 10
        offset = (page - 1) * limit
        page_subscribers = subscribers[offset:offset + limit]
        
        subscribers_text = f"👑 *المشتركون في VIP - الصفحة {page}*\n\n"
        
        for sub in page_subscribers:
            expiry_date = datetime.datetime.fromisoformat(sub['expiry_date'].replace('Z', '+00:00'))
            days_left = (expiry_date - datetime.datetime.now()).days
            
            subscribers_text += f"""
            👤 {sub['first_name']} {sub['last_name'] or ''}
            🆔 {sub['user_id']}
            📅 الانتهاء: {format_date(expiry_date)} ({days_left} يوم)
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = []
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_vip_subscribers_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"صفحة {page}", callback_data="noop"))
        
        if offset + limit < len(subscribers):
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"admin_vip_subscribers_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([
            InlineKeyboardButton("🚫 إلغاء اشتراك", callback_data="admin_cancel_vip"),
            InlineKeyboardButton("🔄 تجديد اشتراك", callback_data="admin_renew_vip")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")])
        
        await query.edit_message_text(
            subscribers_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_vip_subscribers: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_cancel_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "🚫 *إلغاء اشتراك VIP*\n\nأرسل أيدي المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "CANCEL_VIP"
    except Exception as e:
        logger.error(f"Error in admin_cancel_vip: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_cancel_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        
        if not db.is_vip_subscriber(user_id):
            await update.message.reply_text("❌ هذا المستخدم ليس مشتركاً في VIP:")
            return "CANCEL_VIP"
        
        if db.cancel_vip_subscription(user_id):
            try:
                await update.message.bot.send_message(
                    user_id,
                    "🚫 *تم إلغاء اشتراكك في VIP*",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
            
            await update.message.reply_text(
                f"✅ تم إلغاء اشتراك المستخدم {user_id} في VIP",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text("❌ فشل في إلغاء الاشتراك.")
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return "CANCEL_VIP"
    except Exception as e:
        logger.error(f"Error in process_cancel_vip: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_renew_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "🔄 *تجديد اشتراك VIP*\n\nأرسل أيدي المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "RENEW_VIP"
    except Exception as e:
        logger.error(f"Error in admin_renew_vip: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_renew_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
        
        if db.renew_vip_subscription(user_id, 30):
            try:
                await update.message.bot.send_message(
                    user_id,
                    "🔄 *تم تجديد اشتراكك في VIP*",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
            
            await update.message.reply_text(
                f"✅ تم تجديد اشتراك المستخدم {user_id} في VIP لمدة 30 يوم",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text("❌ فشل في تجديد الاشتراك.")
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال أيدي صحيح:")
        return "RENEW_VIP"
    except Exception as e:
        logger.error(f"Error in process_renew_vip: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_vip_expiring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        subscribers = db.get_expiring_vip_subscriptions(7)
        
        if not subscribers:
            await query.edit_message_text("✅ لا توجد اشتراكات VIP تنتهي قريباً.")
            return
        
        subscribers_text = "⏳ *اشتراكات VIP تنتهي قريباً*\n\n"
        
        for sub in subscribers:
            expiry_date = datetime.datetime.fromisoformat(sub['expiry_date'].replace('Z', '+00:00'))
            days_left = (expiry_date - datetime.datetime.now()).days
            
            subscribers_text += f"""
            👤 {sub['first_name']} {sub['last_name'] or ''}
            🆔 {sub['user_id']}
            ⏳ تنتهي بعد: {days_left} يوم
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = [
            [InlineKeyboardButton("🔄 تجديد اشتراك", callback_data="admin_renew_vip")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")]
        ]
        
        await query.edit_message_text(
            subscribers_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_vip_expiring: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_vip_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        lectures = db.get_pending_lectures()
        
        if not lectures:
            await query.edit_message_text("✅ لا توجد محاضرات منتظرة.")
            return
        
        if 'pending_lecture_index' not in context.user_data:
            context.user_data['pending_lecture_index'] = 0
            context.user_data['pending_lectures'] = lectures
        
        idx = context.user_data['pending_lecture_index']
        lecture = context.user_data['pending_lectures'][idx]
        
        keyboard = []
        
        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="pending_lecture_prev"))
        
        nav_buttons.append(InlineKeyboardButton(f"{idx+1}/{len(lectures)}", callback_data="noop"))
        
        if idx < len(lectures) - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="pending_lecture_next"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([
            InlineKeyboardButton("✅ الموافقة", callback_data=f"admin_approve_lecture_{lecture['lecture_id']}"),
            InlineKeyboardButton("❌ الرفض", callback_data=f"admin_reject_lecture_{lecture['lecture_id']}")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")])
        
        lecture_text = f"""
        ⏳ *محاضرة منتظرة* #{lecture['lecture_id']}
        
        👨‍🏫 *المدرس:* {lecture['first_name']}
        🎬 *العنوان:* {lecture['title']}
        💰 *السعر:* {format_currency(lecture['price']) if lecture['price'] > 0 else 'مجاني'}
        """
        
        await query.edit_message_text(
            lecture_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_vip_pending: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def navigate_pending_lectures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "pending_lecture_prev":
            context.user_data['pending_lecture_index'] -= 1
        elif query.data == "pending_lecture_next":
            context.user_data['pending_lecture_index'] += 1
        
        await admin_vip_pending(update, context)
    except Exception as e:
        logger.error(f"Error in navigate_pending_lectures: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_pdf_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        lectures = db.get_pending_pdf_lectures()
        
        if not lectures:
            await query.edit_message_text("✅ لا توجد محاضرات PDF منتظرة.")
            return
        
        if 'pending_pdf_index' not in context.user_data:
            context.user_data['pending_pdf_index'] = 0
            context.user_data['pending_pdfs'] = lectures
        
        idx = context.user_data['pending_pdf_index']
        lecture = context.user_data['pending_pdfs'][idx]
        
        keyboard = []
        
        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="pending_pdf_prev"))
        
        nav_buttons.append(InlineKeyboardButton(f"{idx+1}/{len(lectures)}", callback_data="noop"))
        
        if idx < len(lectures) - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="pending_pdf_next"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([
            InlineKeyboardButton("✅ الموافقة", callback_data=f"admin_approve_pdf_{lecture['pdf_id']}"),
            InlineKeyboardButton("❌ الرفض", callback_data=f"admin_reject_pdf_{lecture['pdf_id']}")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")])
        
        lecture_text = f"""
        📚 *محاضرة PDF منتظرة* #{lecture['pdf_id']}
        
        👨‍🏫 *المدرس:* {lecture['first_name']}
        📚 *العنوان:* {lecture['title']}
        💰 *السعر:* {format_currency(lecture['price']) if lecture['price'] > 0 else 'مجاني'}
        """
        
        await query.edit_message_text(
            lecture_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_pdf_pending: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def navigate_pending_pdfs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "pending_pdf_prev":
            context.user_data['pending_pdf_index'] -= 1
        elif query.data == "pending_pdf_next":
            context.user_data['pending_pdf_index'] += 1
        
        await admin_pdf_pending(update, context)
    except Exception as e:
        logger.error(f"Error in navigate_pending_pdfs: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_approve_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        lecture_id = int(query.data.replace("admin_approve_lecture_", ""))
        
        if db.approve_lecture(lecture_id, query.from_user.id):
            lecture = db.get_lecture_by_id(lecture_id)
            
            if lecture:
                try:
                    teacher_msg = f"""
                    ✅ *تمت الموافقة على محاضرتك*
                    
                    🎬 {lecture['title']}
                    """
                    await context.bot.send_message(lecture['teacher_id'], teacher_msg, parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ تمت الموافقة على المحاضرة #{lecture_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في الموافقة على المحاضرة #{lecture_id}",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in admin_approve_lecture: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_reject_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        lecture_id = int(query.data.replace("admin_reject_lecture_", ""))
        
        if db.reject_lecture(lecture_id):
            lecture = db.get_lecture_by_id(lecture_id)
            
            if lecture:
                try:
                    teacher_msg = f"""
                    ❌ *تم رفض محاضرتك*
                    
                    🎬 {lecture['title']}
                    """
                    await context.bot.send_message(lecture['teacher_id'], teacher_msg, parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
            
            await query.edit_message_text(
                f"❌ تم رفض المحاضرة #{lecture_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في رفض المحاضرة #{lecture_id}",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in admin_reject_lecture: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_approve_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        pdf_id = int(query.data.replace("admin_approve_pdf_", ""))
        
        if db.approve_pdf_lecture(pdf_id, query.from_user.id):
            lecture = db.get_pdf_lecture_by_id(pdf_id)
            
            if lecture:
                try:
                    teacher_msg = f"""
                    ✅ *تمت الموافقة على محاضرتك PDF*
                    
                    📚 {lecture['title']}
                    """
                    await context.bot.send_message(lecture['teacher_id'], teacher_msg, parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ تمت الموافقة على المحاضرة PDF #{pdf_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في الموافقة على المحاضرة PDF #{pdf_id}",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in admin_approve_pdf: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_reject_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        pdf_id = int(query.data.replace("admin_reject_pdf_", ""))
        
        if db.reject_pdf_lecture(pdf_id):
            lecture = db.get_pdf_lecture_by_id(pdf_id)
            
            if lecture:
                try:
                    teacher_msg = f"""
                    ❌ *تم رفض محاضرتك PDF*
                    
                    📚 {lecture['title']}
                    """
                    await context.bot.send_message(lecture['teacher_id'], teacher_msg, parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
            
            await query.edit_message_text(
                f"❌ تم رفض المحاضرة PDF #{pdf_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في رفض المحاضرة PDF #{pdf_id}",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in admin_reject_pdf: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_vip_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        stats = db.get_overall_stats()
        
        stats_text = """
        📊 *إحصائيات نظام VIP*
        
        *إحصائيات المستخدمين:*
        """
        
        users = stats.get('users', {})
        vip = stats.get('vip', {})
        sales = stats.get('sales', {})
        
        stats_text += f"""
        👥 إجمالي المستخدمين: {users.get('total_users', 0):,}
        👑 مستخدمين VIP: {users.get('vip_users', 0):,}
        
        *إحصائيات المبيعات:*
        🛒 إجمالي المبيعات: {sales.get('total_sales', 0):,}
        💰 إجمالي الإيرادات: {format_currency(sales.get('total_revenue', 0))}
        
        *إحصائيات المشتركين:*
        👑 مشتركين نشطين: {vip.get('active_vip', 0):,}
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 أرباح المدرسين", callback_data="admin_vip_earnings")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")]
        ]
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_vip_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_vip_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        earnings = db.get_all_vip_earnings()
        
        if not earnings:
            await query.edit_message_text("📭 لا توجد أرباح للمدرسين.")
            return
        
        earnings_text = "💰 *أرباح المدرسين*\n\n"
        
        for i, earning in enumerate(earnings, 1):
            earnings_text += f"""
            {i}. {earning['first_name']} {earning['last_name'] or ''}
            🆔 {earning['teacher_id']}
            💰 إجمالي الأرباح: {format_currency(earning['total_earnings'])}
            🏦 متاح للسحب: {format_currency(earning['available_balance'])}
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = [
            [InlineKeyboardButton("💳 خصم أرباح", callback_data="admin_deduct_vip")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")]
        ]
        
        await query.edit_message_text(
            earnings_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_vip_earnings: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_vip_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        vip_price = db.get_vip_subscription_price()
        
        keyboard = [
            [InlineKeyboardButton(f"💰 تحديث سعر الاشتراك ({format_currency(vip_price)})", 
             callback_data="admin_update_vip_price")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip")]
        ]
        
        settings_text = f"""
        🔧 *إعدادات VIP*
        
        *الإعدادات الحالية:*
        💰 سعر الاشتراك الشهري: {format_currency(vip_price)}
        """
        
        await query.edit_message_text(
            settings_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_vip_settings: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_update_vip_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_price = db.get_vip_subscription_price()
        
        await query.edit_message_text(
            f"💰 *تحديث سعر اشتراك VIP*\n\nالسعر الحالي: {format_currency(current_price)}\n\nأرسل السعر الجديد:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "UPDATE_VIP_PRICE"
    except Exception as e:
        logger.error(f"Error in admin_update_vip_price: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_update_vip_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_price = int(update.message.text)
        if new_price < 1000:
            await update.message.reply_text("❌ السعر يجب أن يكون 1000 دينار على الأقل:")
            return "UPDATE_VIP_PRICE"
        
        db.set_vip_subscription_price(new_price)
        
        await update.message.reply_text(
            f"✅ تم تحديث سعر اشتراك VIP إلى {format_currency(new_price)}",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال سعر صحيح:")
        return "UPDATE_VIP_PRICE"
    except Exception as e:
        logger.error(f"Error in process_update_vip_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

# ====================== إدارة الخدمات ======================
async def admin_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "⚙️ *إدارة الخدمات*\n\nاختر الخدمة التي تريد إدارتها:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_services_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_services: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_toggle_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        services = db.get_all_services()
        
        keyboard = []
        for service in services:
            service_name = service['service_name']
            display_name = service['display_name']
            is_active = service['is_active'] == 1
            
            status_icon = "✅" if is_active else "⏸️"
            action = "تعطيل" if is_active else "تفعيل"
            callback_data = f"toggle_service_{service_name}_{0 if is_active else 1}"
            button_text = f"{status_icon} {display_name} ({action})"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
        
        await query.edit_message_text(
            "🔄 *تفعيل/تعطيل الخدمات*\n\nاختر الخدمة:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_toggle_services: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def toggle_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("toggle_service_", "")
        parts = data.split("_")
        
        if len(parts) >= 2:
            service_name = parts[0]
            new_status = int(parts[1])
            
            if db.toggle_service(service_name, new_status):
                status_text = "مفعلة" if new_status == 1 else "معطلة"
                
                services = db.get_all_services()
                keyboard = []
                
                for service in services:
                    s_name = service['service_name']
                    display_name = service['display_name']
                    is_active = service['is_active'] == 1
                    
                    status_icon = "✅" if is_active else "⏸️"
                    action = "تعطيل" if is_active else "تفعيل"
                    callback_data = f"toggle_service_{s_name}_{0 if is_active else 1}"
                    button_text = f"{status_icon} {display_name} ({action})"
                    
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
                
                await query.edit_message_text(
                    f"✅ تم {status_text} الخدمة بنجاح.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.edit_message_text(
                    "❌ فشل في تحديث حالة الخدمة.",
                    reply_markup=get_admin_keyboard()
                )
        else:
            await query.edit_message_text(
                "❌ بيانات غير صالحة.",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in toggle_service_callback: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_service_exemption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_price = db.get_service_price('exemption_calc')
        
        await query.edit_message_text(
            f"🎓 *تعديل سعر حساب الإعفاء*\n\nالسعر الحالي: {format_currency(current_price)}\n\nأرسل السعر الجديد:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "UPDATE_EXEMPTION_PRICE"
    except Exception as e:
        logger.error(f"Error in admin_service_exemption: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_update_exemption_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_price = int(update.message.text)
        if new_price < 1000:
            await update.message.reply_text("❌ السعر يجب أن يكون 1000 دينار على الأقل:")
            return "UPDATE_EXEMPTION_PRICE"
        
        db.update_service_price('exemption_calc', new_price)
        
        await update.message.reply_text(
            f"✅ تم تحديث سعر حساب الإعفاء إلى {format_currency(new_price)}",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال سعر صحيح:")
        return "UPDATE_EXEMPTION_PRICE"
    except Exception as e:
        logger.error(f"Error in process_update_exemption_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_service_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_price = db.get_service_price('pdf_summary')
        
        await query.edit_message_text(
            f"📚 *تعديل سعر تلخيص الملازم*\n\nالسعر الحالي: {format_currency(current_price)}\n\nأرسل السعر الجديد:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "UPDATE_SUMMARY_PRICE"
    except Exception as e:
        logger.error(f"Error in admin_service_summary: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_update_summary_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_price = int(update.message.text)
        if new_price < 1000:
            await update.message.reply_text("❌ السعر يجب أن يكون 1000 دينار على الأقل:")
            return "UPDATE_SUMMARY_PRICE"
        
        db.update_service_price('pdf_summary', new_price)
        
        await update.message.reply_text(
            f"✅ تم تحديث سعر تلخيص الملازم إلى {format_currency(new_price)}",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال سعر صحيح:")
        return "UPDATE_SUMMARY_PRICE"
    except Exception as e:
        logger.error(f"Error in process_update_summary_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_service_qna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_price = db.get_service_price('qna')
        
        await query.edit_message_text(
            f"❓ *تعديل سعر سؤال وجواب*\n\nالسعر الحالي: {format_currency(current_price)}\n\nأرسل السعر الجديد:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "UPDATE_QNA_PRICE"
    except Exception as e:
        logger.error(f"Error in admin_service_qna: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_update_qna_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_price = int(update.message.text)
        if new_price < 1000:
            await update.message.reply_text("❌ السعر يجب أن يكون 1000 دينار على الأقل:")
            return "UPDATE_QNA_PRICE"
        
        db.update_service_price('qna', new_price)
        
        await update.message.reply_text(
            f"✅ تم تحديث سعر سؤال وجواب إلى {format_currency(new_price)}",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال سعر صحيح:")
        return "UPDATE_QNA_PRICE"
    except Exception as e:
        logger.error(f"Error in process_update_qna_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_service_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_price = db.get_service_price('help_student')
        
        await query.edit_message_text(
            f"👨‍🎓 *تعديل سعر ساعدوني طالب*\n\nالسعر الحالي: {format_currency(current_price)}\n\nأرسل السعر الجديد:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return "UPDATE_HELP_PRICE"
    except Exception as e:
        logger.error(f"Error in admin_service_help: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_update_help_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_price = int(update.message.text)
        if new_price < 1000:
            await update.message.reply_text("❌ السعر يجب أن يكون 1000 دينار على الأقل:")
            return "UPDATE_HELP_PRICE"
        
        db.update_service_price('help_student', new_price)
        
        await update.message.reply_text(
            f"✅ تم تحديث سعر ساعدوني طالب إلى {format_currency(new_price)}",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال سعر صحيح:")
        return "UPDATE_HELP_PRICE"
    except Exception as e:
        logger.error(f"Error in process_update_help_price: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def admin_manage_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        materials = db.get_study_materials(active_only=False)
        
        if not materials:
            await query.edit_message_text("📭 لا توجد مواد تعليمية.")
            return
        
        keyboard = []
        
        for material in materials:
            status_icon = "✅" if material['is_active'] == 1 else "⏸️"
            button_text = f"{status_icon} {material['title'][:30]}"
            callback_data = f"manage_material_{material['material_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([
            InlineKeyboardButton("➕ إضافة مادة", callback_data="admin_add_material"),
            InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")
        ])
        
        await query.edit_message_text(
            "📖 *إدارة المواد التعليمية*\n\nاختر المادة:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_manage_materials: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def manage_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        material_id = int(query.data.replace("manage_material_", ""))
        material = next((m for m in db.get_study_materials(active_only=False) if m['material_id'] == material_id), None)
        
        if not material:
            await query.edit_message_text("❌ المادة غير موجودة.")
            return
        
        status_text = "مفعلة" if material['is_active'] == 1 else "معطلة"
        action_text = "تعطيل" if material['is_active'] == 1 else "تفعيل"
        
        keyboard = [
            [InlineKeyboardButton(f"{action_text} المادة", callback_data=f"toggle_material_{material_id}_{0 if material['is_active'] == 1 else 1}")],
            [InlineKeyboardButton("🗑️ حذف المادة", callback_data=f"delete_material_{material_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_manage_materials")]
        ]
        
        material_text = f"""
        📖 *إدارة المادة: {material['title']}*
        
        📝 *الوصف:* {material['description']}
        🎓 *المرحلة:* {material['stage']}
        📊 *الحالة:* {status_text}
        
        *اختر الإجراء:*
        """
        
        await query.edit_message_text(
            material_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in manage_material: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def toggle_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        data = query.data.replace("toggle_material_", "")
        parts = data.split("_")
        
        if len(parts) >= 2:
            material_id = int(parts[0])
            new_status = int(parts[1])
            
            if db.toggle_study_material(material_id, new_status):
                status_text = "مفعلة" if new_status == 1 else "معطلة"
                await query.edit_message_text(
                    f"✅ تم {status_text} المادة بنجاح.",
                    reply_markup=get_admin_keyboard()
                )
            else:
                await query.edit_message_text(
                    "❌ فشل في تحديث حالة المادة.",
                    reply_markup=get_admin_keyboard()
                )
    except Exception as e:
        logger.error(f"Error in toggle_material: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def delete_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        material_id = int(query.data.replace("delete_material_", ""))
        
        if db.delete_study_material(material_id):
            await query.edit_message_text(
                f"✅ تم حذف المادة #{material_id} بنجاح.",
                reply_markup=get_admin_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ فشل في حذف المادة #{material_id}.",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in delete_material: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_add_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "➕ *إضافة مادة جديدة*\n\nأرسل عنوان المادة:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_ADD_MATERIAL_TITLE
    except Exception as e:
        logger.error(f"Error in admin_add_material: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_material_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['material_title'] = update.message.text
        await update.message.reply_text("✅ تم حفظ العنوان.\nأرسل وصف المادة:")
        return ADMIN_ADD_MATERIAL_DESC
    except Exception as e:
        logger.error(f"Error in process_material_title: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_material_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['material_desc'] = update.message.text
        await update.message.reply_text("✅ تم حفظ الوصف.\nأرسل المرحلة:")
        return ADMIN_ADD_MATERIAL_STAGE
    except Exception as e:
        logger.error(f"Error in process_material_desc: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_material_stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['material_stage'] = update.message.text
        await update.message.reply_text("✅ تم حفظ المرحلة.\nأرسل ملف المادة:")
        return ADMIN_ADD_MATERIAL_FILE
    except Exception as e:
        logger.error(f"Error in process_material_stage: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_material_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.document:
            await update.message.reply_text("❌ يرجى إرسال ملف:")
            return ADMIN_ADD_MATERIAL_FILE
        
        file_id = update.message.document.file_id
        file_type = update.message.document.mime_type or 'application/octet-stream'
        
        title = context.user_data.get('material_title')
        description = context.user_data.get('material_desc')
        stage = context.user_data.get('material_stage')
        user_id = update.effective_user.id
        
        material_id = db.add_study_material(title, description, stage, file_id, file_type, user_id)
        
        context.user_data.pop('material_title', None)
        context.user_data.pop('material_desc', None)
        context.user_data.pop('material_stage', None)
        
        await update.message.reply_text(
            f"✅ تم إضافة المادة بنجاح (#{material_id})",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in process_material_file: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

# ====================== الإحصائيات ======================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        stats = db.get_overall_stats()
        
        stats_text = """
        📊 *الإحصائيات الكاملة*
        
        *إحصائيات المستخدمين:*
        """
        
        users = stats.get('users', {})
        today = stats.get('today', {})
        
        stats_text += f"""
        👥 إجمالي المستخدمين: {users.get('total_users', 0):,}
        👑 مستخدمين VIP: {users.get('vip_users', 0):,}
        🚫 مستخدمين محظورين: {users.get('banned_users', 0):,}
        
        *إحصائيات اليوم:*
        👤 مستخدمين جدد: {today.get('today_users', 0)}
        👑 VIP جدد: {today.get('today_vip', 0)}
        
        *إحصائيات المبيعات:*
        """
        
        sales = stats.get('sales', {})
        
        stats_text += f"""
        🛒 إجمالي المبيعات: {sales.get('total_sales', 0):,}
        💰 إجمالي الإيرادات: {format_currency(sales.get('total_revenue', 0))}
        """
        
        finance_stats = db.get_financial_stats()
        overall = finance_stats.get('overall', {})
        
        stats_text += f"""
        
        *إحصائيات مالية:*
        💰 إجمالي الشحنات: {format_currency(overall.get('total_charged', 0))}
        💸 إجمالي المدفوعات: {format_currency(overall.get('total_payments', 0))}
        """
        
        keyboard = [
            [InlineKeyboardButton("📈 إحصائيات مالية", callback_data="admin_finance_stats"),
             InlineKeyboardButton("👑 إحصائيات VIP", callback_data="admin_vip_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def admin_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        daily_stats = db.get_daily_stats()
        
        if not daily_stats:
            await query.edit_message_text("📭 لا توجد إحصائيات يومية.")
            return
        
        stats_text = "📅 *الإحصائيات اليومية*\n\n"
        
        for stat in daily_stats:
            date = stat['stat_date']
            new_users = stat['new_users']
            active_users = stat['active_users']
            total_income = stat['total_income']
            
            stats_text += f"""
            📅 *{date}:*
            👤 مستخدمين جدد: {new_users}
            📱 مستخدمين نشطين: {active_users}
            💰 الدخل: {format_currency(total_income)}
            ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            """
        
        keyboard = [
            [InlineKeyboardButton("📊 إحصائيات كاملة", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_daily_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

# ====================== الإذاعة ======================
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        await query.edit_message_text(
            "📢 *الإذاعة للمستخدمين*\n\nأرسل النص:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_BROADCAST
    except Exception as e:
        logger.error(f"Error in admin_broadcast: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        broadcast_text = update.message.text
        
        if not broadcast_text or len(broadcast_text.strip()) < 5:
            await update.message.reply_text("❌ النص قصير جداً.")
            return ADMIN_BROADCAST
        
        users = db.get_all_users()
        total_users = len(users)
        
        await update.message.reply_text(f"📤 جارٍ إرسال الإذاعة لـ {total_users:,} مستخدم...")
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                if user['is_banned']:
                    continue
                
                await context.bot.send_message(
                    user['user_id'],
                    f"📢 *إشعار من إدارة البوت:*\n\n{broadcast_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
                success_count += 1
                
                await asyncio.sleep(0.05)
                
            except:
                fail_count += 1
        
        result_text = f"""
        ✅ *تم إرسال الإذاعة*
        
        📊 *النتائج:*
        👥 إجمالي المستخدمين: {total_users:,}
        ✅ الناجحة: {success_count:,}
        ❌ الفاشلة: {fail_count:,}
        """
        
        await update.message.reply_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in process_broadcast: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

# ====================== الإعدادات ======================
async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        maintenance_mode = db.get_maintenance_mode()
        invite_reward = db.get_invite_reward()
        vip_price = db.get_vip_subscription_price()
        
        keyboard = [
            [InlineKeyboardButton(f"🔧 وضع الصيانة: {'✅ مفعل' if maintenance_mode else '❌ معطل'}", 
             callback_data="toggle_maintenance")],
            [InlineKeyboardButton(f"💰 تحديث مكافأة الدعوة ({format_currency(invite_reward)})", 
             callback_data="update_invite_reward")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        settings_text = f"""
        🔧 *إعدادات البوت*
        
        *الإعدادات الحالية:*
        ⚙️ وضع الصيانة: {'✅ مفعل' if maintenance_mode else '❌ معطل'}
        🎁 مكافأة الدعوة: {format_currency(invite_reward)}
        👑 سعر اشتراك VIP: {format_currency(vip_price)}
        """
        
        await query.edit_message_text(
            settings_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_settings: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_mode = db.get_maintenance_mode()
        new_mode = not current_mode
        
        db.set_maintenance_mode(new_mode)
        
        status_text = "مفعل" if new_mode else "معطل"
        
        await query.edit_message_text(
            f"✅ تم {status_text} وضع الصيانة.",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in toggle_maintenance: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")

async def update_invite_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if not is_admin(query.from_user.id):
            return
        
        current_reward = db.get_invite_reward()
        
        await query.edit_message_text(
            f"💰 *تحديث مكافأة الدعوة*\n\nالمكافأة الحالية: {format_currency(current_reward)}\n\nأرسل المكافأة الجديدة:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_UPDATE_INVITE_REWARD
    except Exception as e:
        logger.error(f"Error in update_invite_reward: {e}")
        await query.edit_message_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def process_update_invite_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_reward = int(update.message.text)
        if new_reward < 0:
            await update.message.reply_text("❌ المكافأة يجب أن تكون صفر أو أكثر:")
            return ADMIN_UPDATE_INVITE_REWARD
        
        db.set_invite_reward(new_reward)
        
        await update.message.reply_text(
            f"✅ تم تحديث مكافأة الدعوة إلى {format_currency(new_reward)}",
            reply_markup=get_admin_keyboard()
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ يرجى إرسال مكافأة صحيحة:")
        return ADMIN_UPDATE_INVITE_REWARD
    except Exception as e:
        logger.error(f"Error in process_update_invite_reward: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

# ====================== معالجات إضافية ======================
async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "❌ تم إلغاء العملية.",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ غير معالج: {context.error}")
    
    error_traceback = traceback.format_exc()
    logger.error(f"تفاصيل الخطأ:\n{error_traceback}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
            )
        except:
            pass
    
    try:
        error_msg = f"""
        ⚠️ *خطأ في البوت*
        
        📍 الخطأ: {str(context.error)[:200]}
        """
        await context.bot.send_message(ADMIN_ID, error_msg, parse_mode=ParseMode.MARKDOWN)
    except:
        pass

# ====================== الدالة الرئيسية ======================
def main():
    print("=" * 60)
    print("🚀 بدء تشغيل بوت 'يلا نتعلم' - الإصدار المحسّن")
    print("=" * 60)
    
    try:
        import telegram
        bot = telegram.Bot(token=BOT_TOKEN)
        bot.delete_webhook()
        print("✅ تم حذف Webhook السابق")
    except:
        print("⚠️  لم يتمكن من حذف Webhook")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # معالجات المحادثة
    exemption_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(service_exemption, pattern='^service_exemption$')],
        states={
            CALC_GRADE1: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_grade1)],
            CALC_GRADE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_grade2)],
            CALC_GRADE3: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_grade3)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    pdf_summary_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(service_summary, pattern='^service_summary$')],
        states={
            PDF_SUMMARY: [MessageHandler(filters.Document.PDF, process_pdf_summary)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    qna_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(service_qna, pattern='^service_qna$')],
        states={
            ASK_QUESTION: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, process_question)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    help_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(service_help, pattern='^service_help$')],
        states={
            ASK_QUESTION: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, process_help_question)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    vip_upload_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(vip_upload_lecture, pattern='^vip_upload_lecture$')],
        states={
            VIP_LECTURE_FILE: [MessageHandler(filters.VIDEO | filters.Document.ALL, process_vip_lecture_file)],
            VIP_LECTURE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_lecture_title)],
            VIP_LECTURE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_lecture_desc)],
            VIP_LECTURE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_lecture_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    pdf_upload_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(vip_upload_pdf, pattern='^vip_upload_pdf$')],
        states={
            "PDF_LECTURE_FILE": [MessageHandler(filters.Document.ALL, process_vip_pdf_file)],
            "PDF_LECTURE_TITLE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_pdf_title)],
            "PDF_LECTURE_DESC": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_pdf_desc)],
            "PDF_LECTURE_PRICE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_pdf_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    # معالجات لوحة التحكم
    charge_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_charge, pattern='^admin_charge$')],
        states={
            ADMIN_CHARGE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_charge_user)],
            ADMIN_CHARGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_charge_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    deduct_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_deduct, pattern='^admin_deduct$')],
        states={
            ADMIN_DEDUCT_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deduct_user)],
            ADMIN_DEDUCT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deduct_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    vip_deduct_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_deduct_vip, pattern='^admin_deduct_vip$')],
        states={
            ADMIN_VIP_DEDUCT_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_deduct_user)],
            ADMIN_VIP_DEDUCT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vip_deduct_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    ban_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_ban_user, pattern='^admin_ban_user$')],
        states={
            "BAN_USER": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ban_user)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    unban_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_unban_user, pattern='^admin_unban_user$')],
        states={
            "UNBAN_USER": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_unban_user)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    search_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_search_user, pattern='^admin_search_user$')],
        states={
            "SEARCH_USER": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_user)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    promote_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_promote_user, pattern='^admin_promote_user$')],
        states={
            "PROMOTE_USER": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_promote_user)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast, pattern='^admin_broadcast$')],
        states={
            ADMIN_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    update_vip_price_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_update_vip_price, pattern='^admin_update_vip_price$')],
        states={
            "UPDATE_VIP_PRICE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_update_vip_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    update_invite_reward_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_invite_reward, pattern='^update_invite_reward$')],
        states={
            ADMIN_UPDATE_INVITE_REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_update_invite_reward)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    update_exemption_price_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_service_exemption, pattern='^admin_service_exemption$')],
        states={
            "UPDATE_EXEMPTION_PRICE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_update_exemption_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    update_summary_price_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_service_summary, pattern='^admin_service_summary$')],
        states={
            "UPDATE_SUMMARY_PRICE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_update_summary_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    update_qna_price_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_service_qna, pattern='^admin_service_qna$')],
        states={
            "UPDATE_QNA_PRICE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_update_qna_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    update_help_price_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_service_help, pattern='^admin_service_help$')],
        states={
            "UPDATE_HELP_PRICE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_update_help_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    add_material_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_material, pattern='^admin_add_material$')],
        states={
            ADMIN_ADD_MATERIAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_material_title)],
            ADMIN_ADD_MATERIAL_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_material_desc)],
            ADMIN_ADD_MATERIAL_STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_material_stage)],
            ADMIN_ADD_MATERIAL_FILE: [MessageHandler(filters.Document.ALL, process_material_file)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    cancel_vip_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_cancel_vip, pattern='^admin_cancel_vip$')],
        states={
            "CANCEL_VIP": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_cancel_vip)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    renew_vip_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_renew_vip, pattern='^admin_renew_vip$')],
        states={
            "RENEW_VIP": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_renew_vip)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    # إضافة جميع المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # معالجات الخدمات
    application.add_handler(exemption_conv_handler)
    application.add_handler(pdf_summary_conv_handler)
    application.add_handler(qna_conv_handler)
    application.add_handler(help_conv_handler)
    application.add_handler(vip_upload_conv_handler)
    application.add_handler(pdf_upload_conv_handler)
    
    # معالجات لوحة التحكم
    application.add_handler(charge_conv_handler)
    application.add_handler(deduct_conv_handler)
    application.add_handler(vip_deduct_conv_handler)
    application.add_handler(ban_conv_handler)
    application.add_handler(unban_conv_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(promote_conv_handler)
    application.add_handler(broadcast_conv_handler)
    application.add_handler(update_vip_price_conv_handler)
    application.add_handler(update_invite_reward_conv_handler)
    application.add_handler(update_exemption_price_conv_handler)
    application.add_handler(update_summary_price_conv_handler)
    application.add_handler(update_qna_price_conv_handler)
    application.add_handler(update_help_price_conv_handler)
    application.add_handler(add_material_conv_handler)
    application.add_handler(cancel_vip_conv_handler)
    application.add_handler(renew_vip_conv_handler)
    
    # معالجات الكاليد باك
    application.add_handler(CallbackQueryHandler(service_materials, pattern='^service_materials$'))
    application.add_handler(CallbackQueryHandler(vip_lectures, pattern='^vip_lectures$'))
    application.add_handler(CallbackQueryHandler(vip_subscribe, pattern='^vip_subscribe$'))
    application.add_handler(CallbackQueryHandler(confirm_vip_subscription, pattern='^confirm_vip_subscription$'))
    application.add_handler(CallbackQueryHandler(vip_my_lectures, pattern='^vip_my_lectures$'))
    application.add_handler(CallbackQueryHandler(vip_my_pdfs, pattern='^vip_my_pdfs$'))
    application.add_handler(CallbackQueryHandler(vip_my_earnings, pattern='^vip_my_earnings$'))
    application.add_handler(CallbackQueryHandler(download_lecture, pattern='^download_lecture_'))
    application.add_handler(CallbackQueryHandler(buy_lecture, pattern='^buy_lecture_'))
    
    # أزرار المساعدة
    application.add_handler(CallbackQueryHandler(invite_friend, pattern='^invite_friend$'))
    application.add_handler(CallbackQueryHandler(copy_invite_link, pattern='^copy_invite_link$'))
    application.add_handler(CallbackQueryHandler(my_stats, pattern='^my_stats$'))
    application.add_handler(CallbackQueryHandler(my_balance, pattern='^my_balance$'))
    
    # التنقل
    application.add_handler(CallbackQueryHandler(show_stage_materials, pattern='^materials_stage_'))
    application.add_handler(CallbackQueryHandler(navigate_materials, pattern='^(material_prev|material_next)$'))
    application.add_handler(CallbackQueryHandler(download_material, pattern='^download_material_'))
    application.add_handler(CallbackQueryHandler(navigate_lectures, pattern='^(lecture_prev|lecture_next)$'))
    application.add_handler(CallbackQueryHandler(navigate_pending_lectures, pattern='^(pending_lecture_prev|pending_lecture_next)$'))
    application.add_handler(CallbackQueryHandler(navigate_pending_pdfs, pattern='^(pending_pdf_prev|pending_pdf_next)$'))
    application.add_handler(CallbackQueryHandler(navigate_questions, pattern='^(question_prev|question_next)$'))
    
    # معالجات الموافقة
    application.add_handler(CallbackQueryHandler(admin_approve_lecture, pattern='^admin_approve_lecture_'))
    application.add_handler(CallbackQueryHandler(admin_reject_lecture, pattern='^admin_reject_lecture_'))
    application.add_handler(CallbackQueryHandler(admin_approve_pdf, pattern='^admin_approve_pdf_'))
    application.add_handler(CallbackQueryHandler(admin_reject_pdf, pattern='^admin_reject_pdf_'))
    application.add_handler(CallbackQueryHandler(admin_approve_question, pattern='^admin_approve_question_'))
    application.add_handler(CallbackQueryHandler(admin_reject_question, pattern='^admin_reject_question_'))
    
    # معالجات إدارة المواد
    application.add_handler(CallbackQueryHandler(manage_material, pattern='^manage_material_'))
    application.add_handler(CallbackQueryHandler(toggle_material, pattern='^toggle_material_'))
    application.add_handler(CallbackQueryHandler(delete_material, pattern='^delete_material_'))
    
    # معالجات لوحة التحكم
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_users, pattern='^admin_users$'))
    application.add_handler(CallbackQueryHandler(admin_users_list, pattern='^admin_users_list_'))
    application.add_handler(CallbackQueryHandler(admin_transactions, pattern='^admin_transactions_'))
    application.add_handler(CallbackQueryHandler(admin_finance, pattern='^admin_finance$'))
    application.add_handler(CallbackQueryHandler(admin_finance_stats, pattern='^admin_finance_stats$'))
    application.add_handler(CallbackQueryHandler(admin_vip, pattern='^admin_vip$'))
    application.add_handler(CallbackQueryHandler(admin_vip_subscribers, pattern='^admin_vip_subscribers_'))
    application.add_handler(CallbackQueryHandler(admin_vip_expiring, pattern='^admin_vip_expiring$'))
    application.add_handler(CallbackQueryHandler(admin_vip_pending, pattern='^admin_vip_pending$'))
    application.add_handler(CallbackQueryHandler(admin_pdf_pending, pattern='^admin_pdf_pending$'))
    application.add_handler(CallbackQueryHandler(admin_vip_stats, pattern='^admin_vip_stats$'))
    application.add_handler(CallbackQueryHandler(admin_vip_earnings, pattern='^admin_vip_earnings$'))
    application.add_handler(CallbackQueryHandler(admin_vip_settings, pattern='^admin_vip_settings$'))
    application.add_handler(CallbackQueryHandler(admin_services, pattern='^admin_services$'))
    application.add_handler(CallbackQueryHandler(admin_toggle_services, pattern='^admin_toggle_services$'))
    application.add_handler(CallbackQueryHandler(toggle_service_callback, pattern='^toggle_service_'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(admin_daily_stats, pattern='^admin_daily_stats$'))
    application.add_handler(CallbackQueryHandler(admin_settings, pattern='^admin_settings$'))
    application.add_handler(CallbackQueryHandler(toggle_maintenance, pattern='^toggle_maintenance$'))
    application.add_handler(CallbackQueryHandler(admin_manage_questions, pattern='^admin_manage_questions$'))
    application.add_handler(CallbackQueryHandler(admin_manage_materials, pattern='^admin_manage_materials$'))
    
    # الزر الرئيسي
    application.add_handler(CallbackQueryHandler(handle_callback_start, pattern='^start$'))
    application.add_handler(CallbackQueryHandler(noop, pattern='^noop$'))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    print("\n" + "=" * 60)
    print("🤖 البوت يعمل الآن! اضغط Ctrl+C لإيقافه")
    print("=" * 60 + "\n")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=0.5
        )
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت.")
    except Exception as e:
        print(f"\n❌ حدث خطأ: {e}")

if __name__ == '__main__':
    main()
