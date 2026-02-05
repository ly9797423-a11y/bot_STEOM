#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام "يلا نتعلم" - النسخة الكاملة
مطور: Allawi04
آيدي المدير: 6130994941
توكن البوت: 8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI
"""

import asyncio
import sqlite3
import logging
import json
import os
import io
import base64
import re
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputFile
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
import PyPDF2
from PIL import Image
import requests

# ===================== إعدادات البوت =====================
API_TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
ADMIN_ID = 6130994941
SUPPORT_USERNAME = "@Allawi04"
CHANNEL_USERNAME = "https://t.me/FCJCV"
BOT_USERNAME = "FC4Xbot"
GEMINI_API_KEY = "AIzaSyARsl_YMXA74bPQpJduu0jJVuaku7MaHuY"

# إعداد الذكاء الاصطناعي
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# إعداد التسعير الافتراضي
DEFAULT_PRICES = {
    "exemption": 1000,
    "summarize": 1000,
    "qna": 1000,
    "help_student": 1000,
    "vip_subscription": 5000,
    "vip_lecture": 3000
}

# إعداد الخطوط العربية
FONT_ARABIC = "fonts/Amiri-Regular.ttf"
FONT_ENGLISH = "fonts/DejaVuSans.ttf"

# إنشاء مجلدات التخزين
Path("fonts").mkdir(exist_ok=True)
Path("lectures").mkdir(exist_ok=True)
Path("materials").mkdir(exist_ok=True)
Path("summaries").mkdir(exist_ok=True)

# ===================== إعداد قاعدة البيانات =====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('database.db', check_same_thread=False)
        self.create_tables()
    
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
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                vip_expiry DATE,
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_spent INTEGER DEFAULT 0
            )
        ''')
        
        # جدول العمليات المالية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول الخدمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                price INTEGER,
                is_active INTEGER DEFAULT 1,
                category TEXT
            )
        ''')
        
        # جدول المواد التعليمية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                grade TEXT,
                file_id TEXT,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(added_by) REFERENCES users(user_id)
            )
        ''')
        
        # جدول أسئلة ساعدوني طالب
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS help_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question TEXT,
                is_approved INTEGER DEFAULT 0,
                is_answered INTEGER DEFAULT 0,
                answer TEXT,
                answered_by INTEGER,
                price_paid INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(answered_by) REFERENCES users(user_id)
            )
        ''')
        
        # جدول محاضرات VIP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_lectures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER,
                title TEXT,
                description TEXT,
                subject TEXT,
                file_id TEXT,
                price INTEGER DEFAULT 3000,
                is_approved INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                purchases INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(teacher_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول مشتريات محاضرات VIP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                lecture_id INTEGER,
                amount_paid INTEGER,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(lecture_id) REFERENCES vip_lectures(id)
            )
        ''')
        
        # جدول أرباح المحاضرين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER,
                lecture_id INTEGER,
                amount INTEGER,
                percentage INTEGER DEFAULT 60,
                status TEXT DEFAULT 'pending',
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_date TIMESTAMP,
                FOREIGN KEY(teacher_id) REFERENCES users(user_id),
                FOREIGN KEY(lecture_id) REFERENCES vip_lectures(id)
            )
        ''')
        
        # جدول تقييمات المحاضرات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                lecture_id INTEGER,
                rating INTEGER,
                comment TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(lecture_id) REFERENCES vip_lectures(id)
            )
        ''')
        
        # جدول الإعدادات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # إدخال الخدمات الافتراضية
        default_services = [
            ('exemption', 1000, 1, 'educational'),
            ('summarize', 1000, 1, 'educational'),
            ('qna', 1000, 1, 'educational'),
            ('help_student', 1000, 1, 'community'),
            ('vip_subscription', 5000, 1, 'vip'),
            ('vip_lecture', 3000, 1, 'vip')
        ]
        
        for service in default_services:
            cursor.execute('''
                INSERT OR IGNORE INTO services (name, price, is_active, category)
                VALUES (?, ?, ?, ?)
            ''', service)
        
        # إدخال الإعدادات الافتراضية
        default_settings = [
            ('maintenance_mode', '0'),
            ('referral_bonus', '500'),
            ('min_withdrawal', '15000'),
            ('admin_username', '@Allawi04'),
            ('channel_username', '@FC4Xbot'),
            ('welcome_bonus', '1000')
        ]
        
        for setting in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            ''', setting)
        
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        referral_code = f"REF{user_id}"
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, referral_code, balance)
            VALUES (?, ?, ?, ?, ?, 1000)
        ''', (user_id, username, first_name, last_name, referral_code))
        self.conn.commit()
        
        # إضافة هدية الترحيب كعملية
        if cursor.rowcount > 0:
            self.add_transaction(user_id, 1000, 'welcome_bonus', 'هدية ترحيب')
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def update_balance(self, user_id, amount, operation='add'):
        cursor = self.conn.cursor()
        user = self.get_user(user_id)
        if user:
            new_balance = user[4] + amount if operation == 'add' else user[4] - amount
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
            self.conn.commit()
            return new_balance
        return None
    
    def add_transaction(self, user_id, amount, trans_type, description):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, trans_type, description))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_service_price(self, service_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT price FROM services WHERE name = ?', (service_name,))
        result = cursor.fetchone()
        return result[0] if result else 1000
    
    def update_service_price(self, service_name, new_price):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE services SET price = ? WHERE name = ?', (new_price, service_name))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def toggle_service(self, service_name, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE services SET is_active = ? WHERE name = ?', (status, service_name))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_active_services(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM services WHERE is_active = 1')
        return [row[0] for row in cursor.fetchall()]
    
    def add_material(self, name, description, grade, file_id, added_by):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO materials (name, description, grade, file_id, added_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, grade, file_id, added_by))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_materials_by_grade(self, grade):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM materials WHERE grade = ?', (grade,))
        return cursor.fetchall()
    
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY join_date DESC')
        return cursor.fetchall()
    
    def get_vip_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_vip = 1')
        return cursor.fetchall()
    
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
    
    def make_admin(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def add_vip_lecture(self, teacher_id, title, description, subject, file_id, price):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO vip_lectures (teacher_id, title, description, subject, file_id, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher_id, title, description, subject, file_id, price))
        self.conn.commit()
        return cursor.lastrowid
    
    def approve_lecture(self, lecture_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE vip_lectures SET is_approved = 1 WHERE id = ?', (lecture_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reject_lecture(self, lecture_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM vip_lectures WHERE id = ?', (lecture_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_pending_lectures(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM vip_lectures WHERE is_approved = 0')
        return cursor.fetchall()
    
    def get_approved_lectures(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM vip_lectures WHERE is_approved = 1')
        return cursor.fetchall()
    
    def purchase_lecture(self, user_id, lecture_id, amount):
        cursor = self.conn.cursor()
        
        # تسجيل الشراء
        cursor.execute('''
            INSERT INTO lecture_purchases (user_id, lecture_id, amount_paid)
            VALUES (?, ?, ?)
        ''', (user_id, lecture_id, amount))
        
        # تحديث إحصائيات المحاضرة
        cursor.execute('''
            UPDATE vip_lectures 
            SET purchases = purchases + 1 
            WHERE id = ?
        ''', (lecture_id,))
        
        # حساب أرباح المحاضر (60%)
        teacher_share = int(amount * 0.6)
        cursor.execute('SELECT teacher_id FROM vip_lectures WHERE id = ?', (lecture_id,))
        teacher_id = cursor.fetchone()[0]
        
        # إضافة أرباح المحاضر
        cursor.execute('''
            INSERT INTO teacher_earnings (teacher_id, lecture_id, amount, percentage)
            VALUES (?, ?, ?, ?)
        ''', (teacher_id, lecture_id, teacher_share, 60))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_teacher_earnings(self, teacher_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT SUM(amount) 
            FROM teacher_earnings 
            WHERE teacher_id = ? AND status = 'pending'
        ''', (teacher_id,))
        result = cursor.fetchone()
        return result[0] if result[0] else 0
    
    def withdraw_earnings(self, teacher_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE teacher_earnings 
            SET status = 'withdrawn', paid_date = CURRENT_TIMESTAMP 
            WHERE teacher_id = ? AND status = 'pending'
        ''', (teacher_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def add_help_question(self, user_id, question, price_paid):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO help_questions (user_id, question, price_paid)
            VALUES (?, ?, ?)
        ''', (user_id, question, price_paid))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_questions(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM help_questions WHERE is_approved = 0')
        return cursor.fetchall()
    
    def approve_question(self, question_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE help_questions SET is_approved = 1 WHERE id = ?', (question_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def answer_question(self, question_id, answer, answered_by):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE help_questions 
            SET is_answered = 1, answer = ?, answered_by = ? 
            WHERE id = ?
        ''', (answer, answered_by, question_id))
        self.conn.commit()
        
        # مكافأة المجيب 100 دينار
        cursor.execute('SELECT answered_by FROM help_questions WHERE id = ?', (question_id,))
        answerer_id = cursor.fetchone()[0]
        self.update_balance(answerer_id, 100, 'add')
        self.add_transaction(answerer_id, 100, 'answer_reward', 'مكافأة الإجابة على سؤال')
        
        return cursor.rowcount > 0
    
    def get_statistics(self):
        cursor = self.conn.cursor()
        
        # إجمالي المستخدمين
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # المستخدمين النشطين اليوم
        cursor.execute('SELECT COUNT(*) FROM users WHERE join_date >= datetime("now", "-1 day")')
        active_today = cursor.fetchone()[0]
        
        # المستخدمين VIP
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_vip = 1')
        vip_users = cursor.fetchone()[0]
        
        # إجمالي الرصيد
        cursor.execute('SELECT SUM(balance) FROM users')
        total_balance = cursor.fetchone()[0] or 0
        
        # إجمالي الإيرادات
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE type IN ("service_purchase", "vip_subscription", "lecture_purchase")')
        total_revenue = cursor.fetchone()[0] or 0
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'vip_users': vip_users,
            'total_balance': total_balance,
            'total_revenue': total_revenue
        }
    
    def get_setting(self, key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def update_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()
        return cursor.rowcount > 0

# ===================== تهيئة قاعدة البيانات =====================
db = Database()

# ===================== حالات FSM =====================
class Form(StatesGroup):
    # حالات لوحة التحكم
    admin_main = State()
    admin_charge = State()
    admin_deduct = State()
    admin_ban = State()
    admin_unban = State()
    admin_make_admin = State()
    admin_change_price = State()
    admin_add_material = State()
    admin_add_material_name = State()
    admin_add_material_grade = State()
    admin_add_material_file = State()
    admin_broadcast = State()
    admin_withdraw_request = State()
    
    # حالات الخدمات
    exemption_course1 = State()
    exemption_course2 = State()
    exemption_course3 = State()
    
    summarize_pdf = State()
    
    qna_text = State()
    qna_image = State()
    
    help_question = State()
    help_answer = State()
    
    # حالات VIP
    vip_subscribe = State()
    vip_add_lecture_title = State()
    vip_add_lecture_desc = State()
    vip_add_lecture_subject = State()
    vip_add_lecture_file = State()
    vip_add_lecture_price = State()
    
    # حالات الشراء
    purchase_lecture = State()

# ===================== إعداد البوت =====================
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ===================== وظائف مساعدة =====================
async def download_fonts():
    """تحميل الخطوط إذا لم تكن موجودة"""
    fonts_dir = Path("fonts")
    
    # تحميل خط عربي (Amiri)
    arabic_font = fonts_dir / "Amiri-Regular.ttf"
    if not arabic_font.exists():
        url = "https://github.com/Aliftype/Amiri/releases/download/0.117/Amiri-0.117.zip"
        # هنا يمكن إضافة كود لتحميل الخط (سيتم تنزيله يدوياً في الإنتاج)
        pass
    
    # تحميل خط إنجليزي (DejaVu)
    english_font = fonts_dir / "DejaVuSans.ttf"
    if not english_font.exists():
        # استخدام خط بديل إذا لم يوجد
        pass

async def check_access(user_id: int, service_name: str) -> Tuple[bool, str]:
    """التحقق من صلاحية الوصول للخدمة"""
    user = db.get_user(user_id)
    
    if not user:
        return False, "المستخدم غير مسجل"
    
    if user[5] == 1:  # is_banned
        return False, "⚠️ حسابك محظور. راجع الدعم الفني."
    
    # التحقق من وضع الصيانة
    if service_name != "maintenance_bypass":
        maintenance = db.get_setting('maintenance_mode')
        if maintenance == '1' and user[6] == 0:  # ليس مدير
            return False, "🔧 البوت قيد الصيانة. الرجاء المحاولة لاحقاً."
    
    # التحقق من تفعيل الخدمة
    cursor = db.conn.cursor()
    cursor.execute('SELECT is_active FROM services WHERE name = ?', (service_name,))
    service = cursor.fetchone()
    
    if not service or service[0] == 0:
        return False, "⏸️ هذه الخدمة معطلة حالياً."
    
    # التحقق من الرصيد
    price = db.get_service_price(service_name)
    if user[4] < price and service_name != "balance":
        return False, f"💰 رصيدك غير كافي. السعر: {price} دينار"
    
    return True, ""

async def deduct_balance(user_id: int, service_name: str) -> bool:
    """خصم ثمن الخدمة من رصيد المستخدم"""
    price = db.get_service_price(service_name)
    new_balance = db.update_balance(user_id, -price, 'deduct')
    
    if new_balance is not None:
        db.add_transaction(user_id, -price, 'service_purchase', f'شراء خدمة {service_name}')
        return True
    return False

async def format_arabic_text(text: str) -> str:
    """تنسيق النص العربي للعرض في PDF"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

async def create_pdf_from_text(text: str, filename: str) -> str:
    """إنشاء ملف PDF من النص"""
    try:
        # إنشاء ملف PDF
        pdf_path = f"summaries/{filename}.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # تحميل الخطوط
        try:
            pdfmetrics.registerFont(TTFont('Arabic', FONT_ARABIC))
            pdfmetrics.registerFont(TTFont('English', FONT_ENGLISH))
        except:
            pass
        
        # تقسيم النص إلى سطور
        lines = []
        current_line = ""
        words = text.split()
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if len(test_line) < 80:  # طول السطر المسموح
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # كتابة النص في PDF
        y_position = height - 50
        for line in lines:
            if y_position < 50:  # صفحة جديدة إذا نفذ المكان
                c.showPage()
                y_position = height - 50
            
            # تحديد إذا كان النص عربي أو إنجليزي
            if any('\u0600' <= char <= '\u06FF' for char in line):
                line = await format_arabic_text(line)
                c.setFont("Arabic", 12)
            else:
                c.setFont("English", 12)
            
            c.drawString(50, y_position, line)
            y_position -= 20
        
        c.save()
        return pdf_path
    except Exception as e:
        logging.error(f"خطأ في إنشاء PDF: {e}")
        return None

async def extract_text_from_pdf(pdf_file) -> str:
    """استخراج النص من ملف PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text[:5000]  # تحديد النص لأول 5000 حرف
    except Exception as e:
        logging.error(f"خطأ في استخراج النص من PDF: {e}")
        return ""

async def summarize_with_ai(text: str) -> str:
    """تلخيص النص باستخدام الذكاء الاصطناعي"""
    try:
        prompt = f"""
        قم بتلخيص النص التالي بطريقة علمية ومنظمة مع الحفاظ على المعلومات المهمة:
        
        {text}
        
        ملاحظات:
        1. احذف المعلومات غير المهمة
        2. رتب المعلومات بشكل منطقي
        3. استخدم عناوين رئيسية وفرعية
        4. حافظ على اللغة العربية الفصحى
        5. اجعل التلخيص واضحاً وسهلاً للفهم
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"خطأ في التلخيص بالذكاء الاصطناعي: {e}")
        return "عذراً، حدث خطأ في التلخيص. الرجاء المحاولة لاحقاً."

async def answer_question_with_ai(question: str, image_url: str = None) -> str:
    """الإجابة على الأسئلة باستخدام الذكاء الاصطناعي"""
    try:
        if image_url:
            # معالجة الصور (إذا كان هناك دعم للصور)
            prompt = f"أجب على السؤال التالي بناءً على الصورة والمعلومات العلمية حسب المنهج العراقي: {question}"
        else:
            prompt = f"""
            أجب على السؤال التالي بطريقة علمية ومنظمة حسب المنهج العراقي:
            
            السؤال: {question}
            
            متطلبات الإجابة:
            1. كن دقيقاً علمياً
            2. رتب الإجابة بشكل منطقي
            3. استخدم مصطلحات علمية صحيحة
            4. اجعل الإجابة مفصلة وكافية
            5. تأكد من المعلومة قبل تقديمها
            """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"خطأ في الإجابة بالذكاء الاصطناعي: {e}")
        return "عذراً، حدث خطأ في الإجابة. الرجاء المحاولة لاحقاً."

# ===================== لوحة التحكم =====================
async def admin_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """لوحة تحكم المدير"""
    if user_id != ADMIN_ID:
        return None
    
    keyboard = [
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الشحن والخصم", callback_data="admin_balance")],
        [InlineKeyboardButton(text="⚠️ الحظر والرفع", callback_data="admin_ban")],
        [InlineKeyboardButton(text="🛠️ إدارة الخدمات", callback_data="admin_services")],
        [InlineKeyboardButton(text="📢 الإذاعة", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔧 وضع الصيانة", callback_data="admin_maintenance")],
        [InlineKeyboardButton(text="🎬 محاضرات VIP", callback_data="admin_vip_lectures")],
        [InlineKeyboardButton(text="❓ أسئلة ساعدوني", callback_data="admin_help_questions")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def admin_users_keyboard() -> InlineKeyboardMarkup:
    """قائمة المستخدمين للمدير"""
    keyboard = [
        [InlineKeyboardButton(text="🔍 عرض مستخدم", callback_data="admin_view_user")],
        [InlineKeyboardButton(text="⛔ حظر مستخدم", callback_data="admin_ban_user")],
        [InlineKeyboardButton(text="✅ رفع الحظر", callback_data="admin_unban_user")],
        [InlineKeyboardButton(text="👑 رفع مشرف", callback_data="admin_make_admin")],
        [InlineKeyboardButton(text="👥 عرض VIP", callback_data="admin_view_vip")],
        [InlineKeyboardButton(text="📋 كل المستخدمين", callback_data="admin_all_users")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def admin_balance_keyboard() -> InlineKeyboardMarkup:
    """قائمة الشحن والخصم"""
    keyboard = [
        [InlineKeyboardButton(text="➕ شحن رصيد", callback_data="admin_charge")],
        [InlineKeyboardButton(text="➖ خصم رصيد", callback_data="admin_deduct")],
        [InlineKeyboardButton(text="💳 سحب أرباح", callback_data="admin_withdraw")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def admin_services_keyboard() -> InlineKeyboardMarkup:
    """إدارة الخدمات"""
    keyboard = [
        [InlineKeyboardButton(text="💵 تغيير الأسعار", callback_data="admin_change_prices")],
        [InlineKeyboardButton(text="🚫 تعطيل خدمة", callback_data="admin_disable_service")],
        [InlineKeyboardButton(text="📚 إضافة مادة", callback_data="admin_add_material")],
        [InlineKeyboardButton(text="🗑️ حذف مادة", callback_data="admin_delete_material")],
        [InlineKeyboardButton(text="🎬 إدارة محاضرات", callback_data="admin_manage_lectures")],
        [InlineKeyboardButton(text="🎓 إدارة اشتراكات", callback_data="admin_manage_subscriptions")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def services_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """لوحة الخدمات الرئيسية مع إخفاء الخدمات المعطلة"""
    keyboard = []
    
    # الحصول على الخدمات النشطة
    active_services = db.get_active_services()
    
    if 'exemption' in active_services:
        keyboard.append([InlineKeyboardButton(text="🧮 حساب درجة الإعفاء (1000 دينار)", callback_data="service_exemption")])
    
    if 'summarize' in active_services:
        keyboard.append([InlineKeyboardButton(text="📄 تلخيص الملازم (1000 دينار)", callback_data="service_summarize")])
    
    if 'qna' in active_services:
        keyboard.append([InlineKeyboardButton(text="❓ سؤال وجواب (1000 دينار)", callback_data="service_qna")])
    
    if 'help_student' in active_services:
        keyboard.append([InlineKeyboardButton(text="🙋 ساعدوني طالب (1000 دينار)", callback_data="service_help_student")])
    
    keyboard.append([InlineKeyboardButton(text="📚 ملازمي ومرشحاتي (مجاناً)", callback_data="service_materials")])
    
    if 'vip_lecture' in active_services:
        keyboard.append([InlineKeyboardButton(text="🎬 محاضرات VIP", callback_data="vip_lectures")])
    
    if 'vip_subscription' in active_services:
        keyboard.append([InlineKeyboardButton(text="👑 اشتراك VIP", callback_data="vip_subscribe")])
    
    keyboard.append([InlineKeyboardButton(text="💰 رصيدي", callback_data="my_balance")])
    
    # إضافة أزرار القناة والدعم
    keyboard.append([
        InlineKeyboardButton(text="📢 قناة البوت", url=CHANNEL_USERNAME),
        InlineKeyboardButton(text="🆘 الدعم الفني", url=SUPPORT_USERNAME)
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def balance_keyboard() -> InlineKeyboardMarkup:
    """لوحة الرصيد"""
    keyboard = [
        [InlineKeyboardButton(text="💳 رصيدي الحالي", callback_data="balance_current")],
        [InlineKeyboardButton(text="📊 سجل العمليات", callback_data="balance_history")],
        [InlineKeyboardButton(text="👥 دعوة أصدقاء", callback_data="balance_referral")],
        [InlineKeyboardButton(text="💬 الدعم الفني", url=SUPPORT_USERNAME)],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def exemption_keyboard() -> InlineKeyboardMarkup:
    """لوحة حساب الإعفاء"""
    keyboard = [
        [InlineKeyboardButton(text="📊 احسب إعفائي", callback_data="exemption_calculate")],
        [InlineKeyboardButton(text="📖 كيفية الحساب؟", callback_data="exemption_howto")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def summarize_keyboard() -> InlineKeyboardMarkup:
    """لوحة تلخيص الملازم"""
    keyboard = [
        [InlineKeyboardButton(text="📤 ارسل ملف PDF", callback_data="summarize_upload")],
        [InlineKeyboardButton(text="ℹ️ كيفية التلخيص؟", callback_data="summarize_howto")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def qna_keyboard() -> InlineKeyboardMarkup:
    """لوحة سؤال وجواب"""
    keyboard = [
        [InlineKeyboardButton(text="✍️ اكتب سؤالك", callback_data="qna_text_input")],
        [InlineKeyboardButton(text="📸 ارسل صورة", callback_data="qna_image_input")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def help_student_keyboard() -> InlineKeyboardMarkup:
    """لوحة ساعدوني طالب"""
    keyboard = [
        [InlineKeyboardButton(text="💬 اطرح سؤالاً", callback_data="help_ask_question")],
        [InlineKeyboardButton(text="👁️ عرض الأسئلة", callback_data="help_view_questions")],
        [InlineKeyboardButton(text="💡 جاوب على سؤال", callback_data="help_answer_question")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def materials_keyboard() -> InlineKeyboardMarkup:
    """لوحة الملازم والمرشحات"""
    keyboard = [
        [InlineKeyboardButton(text="🏫 المرحلة الأولى", callback_data="materials_grade1")],
        [InlineKeyboardButton(text="🏫 المرحلة الثانية", callback_data="materials_grade2")],
        [InlineKeyboardButton(text="🏫 المرحلة الثالثة", callback_data="materials_grade3")],
        [InlineKeyboardButton(text="🏫 المرحلة الرابعة", callback_data="materials_grade4")],
        [InlineKeyboardButton(text="🔍 بحث عن مادة", callback_data="materials_search")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def vip_lectures_keyboard() -> InlineKeyboardMarkup:
    """لوحة محاضرات VIP"""
    keyboard = [
        [InlineKeyboardButton(text="🎥 عرض المحاضرات", callback_data="vip_view_lectures")],
        [InlineKeyboardButton(text="🔍 بحث محاضرة", callback_data="vip_search_lecture")],
        [InlineKeyboardButton(text="⭐ الأعلى تقييماً", callback_data="vip_top_rated")],
        [InlineKeyboardButton(text="👨‍🏫 محاضراتي المشتراة", callback_data="vip_my_purchases")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def vip_subscribe_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """لوحة اشتراك VIP"""
    user = db.get_user(user_id)
    is_vip = user[7] if user else 0  # is_vip
    
    keyboard = []
    
    if is_vip:
        keyboard.append([InlineKeyboardButton(text="🎬 محاضراتي", callback_data="vip_my_lectures")])
        keyboard.append([InlineKeyboardButton(text="💸 أرباحي", callback_data="vip_my_earnings")])
        keyboard.append([InlineKeyboardButton(text="📝 تعديل بياناتي", callback_data="vip_edit_profile")])
    else:
        keyboard.append([InlineKeyboardButton(text="👑 اشترك الآن", callback_data="vip_subscribe_now")])
    
    keyboard.append([InlineKeyboardButton(text="📋 شروط الاشتراك", callback_data="vip_terms")])
    keyboard.append([InlineKeyboardButton(text="💰 أسعار الاشتراك", callback_data="vip_prices")])
    keyboard.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ===================== معالجة الأوامر =====================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """معالجة أمر /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # إضافة المستخدم إذا لم يكن موجوداً
    db.add_user(user_id, username, first_name, last_name)
    
    # التحقق من الحظر
    user = db.get_user(user_id)
    if user and user[5] == 1:  # is_banned
        await message.answer("⚠️ حسابك محظور. راجع الدعم الفني.")
        return
    
    # عرض رسالة الترحيب
    welcome_text = f"""
    🎓 أهلاً بك في بوت *يلا نتعلم*!
    
    *خدمات البوت التعليمية:*
    • حساب درجة الإعفاء
    • تلخيص الملازم بالذكاء الاصطناعي
    • سؤال وجواب حسب المنهج العراقي
    • قسم ساعدوني طالب
    • مكتبة الملازم والمرشحات
    • محاضرات VIP للمحاضرين
    
    *رصيدك الحالي:* {user[4] if user else 1000} دينار
    *هدية الترحيب:* 1000 دينار ✓
    
    اختر الخدمة التي تريدها من القائمة:
    """
    
    keyboard = await services_keyboard(user_id)
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """لوحة تحكم المدير"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.answer("⛔ ليس لديك صلاحية الوصول.")
        return
    
    keyboard = await admin_panel_keyboard(user_id)
    await message.answer("👑 *لوحة تحكم المدير*", reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    """عرض الرصيد"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("⚠️ الرجاء استخدام /start أولاً")
        return
    
    if user[5] == 1:  # is_banned
        await message.answer("⚠️ حسابك محظور. راجع الدعم الفني.")
        return
    
    balance_text = f"""
    💰 *معلومات الرصيد*
    
    *الرصيد الحالي:* {user[4]} دينار
    *إجمالي المصروف:* {user[12] if len(user) > 12 else 0} دينار
    
    اختر الخدمة:
    """
    
    keyboard = await balance_keyboard()
    await message.answer(balance_text, reply_markup=keyboard, parse_mode="Markdown")

# ===================== معالجة Callback Queries =====================
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback_query: CallbackQuery):
    """العودة للقائمة الرئيسية"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback_query.answer("الرجاء استخدام /start أولاً")
        return
    
    if user[5] == 1:  # is_banned
        await callback_query.answer("حسابك محظور")
        return
    
    welcome_text = f"""
    🎓 *مرحباً بك مجدداً في يلا نتعلم!*
    
    *رصيدك الحالي:* {user[4]} دينار
    
    اختر الخدمة التي تريدها:
    """
    
    keyboard = await services_keyboard(user_id)
    await callback_query.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

# ===================== معالجة الخدمات =====================
@dp.callback_query(lambda c: c.data == "service_exemption")
async def service_exemption(callback_query: CallbackQuery):
    """خدمة حساب الإعفاء"""
    user_id = callback_query.from_user.id
    
    # التحقق من الوصول
    access, message = await check_access(user_id, "exemption")
    if not access:
        await callback_query.answer(message)
        return
    
    # خصم المبلغ
    if await deduct_balance(user_id, "exemption"):
        text = """
        🧮 *حساب درجة الإعفاء الفردي*
        
        أدخل درجات الكورسات الثلاثة:
        • الكورس الأول
        • الكورس الثاني  
        • الكورس الثالث
        
        *شرط الإعفاء:* المعدل ≥ 90
        
        اضغط على *احسب إعفائي* للبدء:
        """
        
        keyboard = await exemption_keyboard()
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback_query.answer("❌ فشل في خصم المبلغ")

@dp.callback_query(lambda c: c.data == "exemption_calculate")
async def exemption_calculate(callback_query: CallbackQuery, state: FSMContext):
    """بدء عملية حساب الإعفاء"""
    await state.set_state(Form.exemption_course1)
    
    text = """
    *الخطوة 1/3*
    
    أدخل درجة الكورس الأول (0-100):
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.exemption_course1)
async def process_course1(message: Message, state: FSMContext):
    """معالجة درجة الكورس الأول"""
    try:
        grade = float(message.text)
        if 0 <= grade <= 100:
            await state.update_data(course1=grade)
            await state.set_state(Form.exemption_course2)
            
            text = """
            *الخطوة 2/3*
            
            أدخل درجة الكورس الثاني (0-100):
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_to_main")]
            ])
            
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer("❌ الرجاء إدخال درجة بين 0 و 100")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Form.exemption_course2)
async def process_course2(message: Message, state: FSMContext):
    """معالجة درجة الكورس الثاني"""
    try:
        grade = float(message.text)
        if 0 <= grade <= 100:
            await state.update_data(course2=grade)
            await state.set_state(Form.exemption_course3)
            
            text = """
            *الخطوة 3/3*
            
            أدخل درجة الكورس الثالث (0-100):
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_to_main")]
            ])
            
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer("❌ الرجاء إدخال درجة بين 0 و 100")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Form.exemption_course3)
async def process_course3(message: Message, state: FSMContext):
    """معالجة درجة الكورس الثالث وحساب المعدل"""
    try:
        grade = float(message.text)
        if 0 <= grade <= 100:
            data = await state.get_data()
            course1 = data.get('course1', 0)
            course2 = data.get('course2', 0)
            course3 = grade
            
            # حساب المعدل
            average = (course1 + course2 + course3) / 3
            
            # تحديد الإعفاء
            if average >= 90:
                result = "🎉 *مبروك! أنت معفي من المادة*"
                emoji = "✅"
            else:
                result = "❌ *أنت غير معفي من المادة*"
                emoji = "⚠️"
            
            text = f"""
            {emoji} *نتيجة حساب الإعفاء*
            
            *الدرجات المدخلة:*
            • الكورس الأول: {course1}
            • الكورس الثاني: {course2}
            • الكورس الثالث: {course3}
            
            *المعدل النهائي:* {average:.2f}
            
            {result}
            
            *شرط الإعفاء:* المعدل ≥ 90
            """
            
            await state.clear()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_to_main")]
            ])
            
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer("❌ الرجاء إدخال درجة بين 0 و 100")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.callback_query(lambda c: c.data == "service_summarize")
async def service_summarize(callback_query: CallbackQuery):
    """خدمة تلخيص الملازم"""
    user_id = callback_query.from_user.id
    
    # التحقق من الوصول
    access, message = await check_access(user_id, "summarize")
    if not access:
        await callback_query.answer(message)
        return
    
    # خصم المبلغ
    if await deduct_balance(user_id, "summarize"):
        text = """
        📄 *تلخيص الملازم بالذكاء الاصطناعي*
        
        *المميزات:*
        • تلخيص احترافي للملازم
        • حذف المعلومات غير المهمة
        • تنظيم النص بشكل منطقي
        • خطوط عربية وإنجليزية منظمة
        • إخراج PDF مرتب
        
        اضغط على *ارسل ملف PDF* لبدء التلخيص:
        """
        
        keyboard = await summarize_keyboard()
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback_query.answer("❌ فشل في خصم المبلغ")

@dp.callback_query(lambda c: c.data == "summarize_upload")
async def summarize_upload(callback_query: CallbackQuery, state: FSMContext):
    """طلب رفع ملف PDF"""
    await state.set_state(Form.summarize_pdf)
    
    text = """
    *رفع ملف PDF للتلخيص*
    
    *الشروط:*
    1. الملف بصيغة PDF فقط
    2. حجم الملف لا يتعدى 20MB
    3. النص داخل الملف واضح
    4. الملف غير محمي بكلمة سر
    
    قم بإرسال ملف PDF الآن:
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.summarize_pdf)
async def process_pdf_summary(message: Message, state: FSMContext):
    """معالجة ملف PDF والتلخيص"""
    if not message.document:
        await message.answer("❌ الرجاء إرسال ملف PDF")
        return
    
    if not message.document.file_name.endswith('.pdf'):
        await message.answer("❌ الملف يجب أن يكون بصيغة PDF")
        return
    
    # إرسال رسالة الانتظار
    wait_msg = await message.answer("⏳ جاري معالجة الملف وتلخيصه...")
    
    try:
        # تحميل الملف
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        
        # استخراج النص من PDF
        text = await extract_text_from_pdf(io.BytesIO(await bot.download_file(file_path)))
        
        if not text or len(text) < 50:
            await wait_msg.delete()
            await message.answer("❌ لا يمكن قراءة النص من الملف. تأكد أن الملف يحتوي على نص قابل للقراءة.")
            await state.clear()
            return
        
        # تلخيص النص باستخدام الذكاء الاصطناعي
        summary = await summarize_with_ai(text)
        
        if not summary:
            await wait_msg.delete()
            await message.answer("❌ حدث خطأ في التلخيص. الرجاء المحاولة لاحقاً.")
            await state.clear()
            return
        
        # إنشاء ملف PDF من التلخيص
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"summary_{message.from_user.id}_{timestamp}"
        pdf_path = await create_pdf_from_text(summary, pdf_filename)
        
        if not pdf_path:
            await wait_msg.delete()
            await message.answer("❌ حدث خطأ في إنشاء ملف PDF.")
            await state.clear()
            return
        
        await wait_msg.delete()
        
        # إرسال الملف
        with open(pdf_path, 'rb') as pdf_file:
            await message.answer_document(
                InputFile(pdf_file, filename=f"ملخص_{timestamp}.pdf"),
                caption="✅ *تم تلخيص الملف بنجاح*\n\n📄 الملف جاهز للتحميل",
                parse_mode="Markdown"
            )
        
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_to_main")]
        ])
        
        await message.answer("📄 تم إرسال الملف الملخص. هل تريد خدمة أخرى؟", reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في تلخيص PDF: {e}")
        await wait_msg.delete()
        await message.answer("❌ حدث خطأ غير متوقع. الرجاء المحاولة لاحقاً.")
        await state.clear()

@dp.callback_query(lambda c: c.data == "service_qna")
async def service_qna(callback_query: CallbackQuery):
    """خدمة سؤال وجواب"""
    user_id = callback_query.from_user.id
    
    # التحقق من الوصول
    access, message = await check_access(user_id, "qna")
    if not access:
        await callback_query.answer(message)
        return
    
    # خصم المبلغ
    if await deduct_balance(user_id, "qna"):
        text = """
        ❓ *سؤال وجواب بالذكاء الاصطناعي*
        
        *المميزات:*
        • إجابات علمية دقيقة
        • حسب المنهج العراقي
        • دعم النصوص والصور
        • إجابات مفصلة ومنظمة
        
        اختر طريقة إدخال السؤال:
        """
        
        keyboard = await qna_keyboard()
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback_query.answer("❌ فشل في خصم المبلغ")

@dp.callback_query(lambda c: c.data == "qna_text_input")
async def qna_text_input(callback_query: CallbackQuery, state: FSMContext):
    """إدخال سؤال نصي"""
    await state.set_state(Form.qna_text)
    
    text = """
    *إدخال السؤال النصي*
    
    اكتب سؤالك العلمي واضغط إرسال:
    
    *ملاحظة:* يجب أن يكون السؤال واضحاً ومحدداً للحصول على إجابة أفضل.
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.qna_text)
async def process_qna_text(message: Message, state: FSMContext):
    """معالجة السؤال النصي"""
    question = message.text
    
    if len(question) < 5:
        await message.answer("❌ السؤال قصير جداً. الرجاء كتابة سؤال مفصّل.")
        return
    
    # إرسال رسالة الانتظار
    wait_msg = await message.answer("⏳ جاري البحث عن الإجابة...")
    
    try:
        # الحصول على الإجابة من الذكاء الاصطناعي
        answer = await answer_question_with_ai(question)
        
        await wait_msg.delete()
        
        if not answer:
            await message.answer("❌ لم أتمكن من العثور على إجابة مناسبة.")
            await state.clear()
            return
        
        # تقليم الإجابة إذا كانت طويلة جداً
        if len(answer) > 4000:
            answer = answer[:4000] + "\n\n... (تم تقليم الإجابة بسبب الطول)"
        
        text = f"""
        ❓ *السؤال:*
        {question}
        
        💡 *الإجابة:*
        {answer}
        
        *ملاحظة:* هذه الإجابة مقدمة بواسطة الذكاء الاصطناعي بناءً على المعلومات المتاحة.
        """
        
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_to_main")]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"خطأ في الإجابة على السؤال: {e}")
        await wait_msg.delete()
        await message.answer("❌ حدث خطأ في معالجة السؤال. الرجاء المحاولة لاحقاً.")
        await state.clear()

@dp.callback_query(lambda c: c.data == "service_help_student")
async def service_help_student(callback_query: CallbackQuery):
    """خدمة ساعدوني طالب"""
    user_id = callback_query.from_user.id
    
    # التحقق من الوصول
    access, message = await check_access(user_id, "help_student")
    if not access:
        await callback_query.answer(message)
        return
    
    text = """
    🙋 *ساعدوني طالب*
    
    *فكرة الخدمة:*
    • اطرح سؤالاً وادفع 1000 دينار
    • السؤال يعرض على الطلاب الآخرين
    • من يجيب يحصل على 100 دينار مكافأة
    • الإجابة ترسل لك مباشرة
    
    *ملاحظة:* السؤال يحتاج موافقة الإدارة قبل النشر.
    """
    
    keyboard = await help_student_keyboard()
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "help_ask_question")
async def help_ask_question(callback_query: CallbackQuery, state: FSMContext):
    """طرح سؤال في ساعدوني طالب"""
    user_id = callback_query.from_user.id
    
    # التحقق من الرصيد
    access, message = await check_access(user_id, "help_student")
    if not access:
        await callback_query.answer(message)
        return
    
    # خصم المبلغ
    if await deduct_balance(user_id, "help_student"):
        await state.set_state(Form.help_question)
        
        text = """
        *طرح سؤال جديد*
        
        اكتب سؤالك واضغط إرسال:
        
        *شروط النشر:*
        1. يجب أن يكون السؤال علمياً
        2. لا يحتوي على إساءة أو ألفاظ غير لائقة
        3. واضح ومحدد
        4. متعلق بالمنهج الدراسي
        
        *مكافأة المجيب:* 100 دينار
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_to_main")]
        ])
        
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback_query.answer("❌ فشل في خصم المبلغ")

@dp.message(Form.help_question)
async def process_help_question(message: Message, state: FSMContext):
    """معالجة سؤال ساعدوني طالب"""
    question = message.text
    
    if len(question) < 10:
        await message.answer("❌ السؤال قصير جداً. الرجاء كتابة سؤال مفصّل.")
        return
    
    # حفظ السؤال في قاعدة البيانات
    question_id = db.add_help_question(message.from_user.id, question, 1000)
    
    text = f"""
    ✅ *تم إرسال سؤالك*
    
    *رقم السؤال:* #{question_id}
    *حالة السؤال:* قيد المراجعة
    
    *ملاحظة:* سوف يتم مراجعة سؤالك من قبل الإدارة قبل النشر.
    عند الموافقة، سيعرض السؤال للطلاب الآخرين للإجابة.
    
    ستحصل على إجابة مباشرة عندما يجيب أحد الطلاب.
    """
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_to_main")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # إرسال إشعار للمدير
    admin_text = f"""
    📋 *سؤال جديد يحتاج موافقة*
    
    *رقم السؤال:* #{question_id}
    *المستخدم:* @{message.from_user.username or 'بدون يوزر'}
    *الاسم:* {message.from_user.first_name}
    *الآيدي:* {message.from_user.id}
    
    *السؤال:*
    {question}
    
    *للموافقة:* /approve_question {question_id}
    *للرفض:* /reject_question {question_id}
    """
    
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "service_materials")
async def service_materials(callback_query: CallbackQuery):
    """خدمة الملازم والمرشحات"""
    text = """
    📚 *ملازمي ومرشحاتي*
    
    *مكتبة المواد التعليمية المجانية:*
    • ملازم دراسية
    • مرشحات الامتحانات
    • نماذج حلول
    • كتب مساعدة
    
    اختر المرحلة الدراسية:
    """
    
    keyboard = await materials_keyboard()
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("materials_grade"))
async def materials_grade(callback_query: CallbackQuery):
    """عرض مواد مرحلة معينة"""
    grade_map = {
        "materials_grade1": "المرحلة الأولى",
        "materials_grade2": "المرحلة الثانية",
        "materials_grade3": "المرحلة الثالثة",
        "materials_grade4": "المرحلة الرابعة"
    }
    
    grade_key = callback_query.data
    grade_name = grade_map.get(grade_key, "غير معروف")
    
    # الحصول على المواد من قاعدة البيانات
    materials = db.get_materials_by_grade(grade_name)
    
    if not materials:
        text = f"""
        📭 *{grade_name}*
        
        لا توجد مواد متاحة لهذه المرحلة حالياً.
        
        سيتم إضافة مواد قريباً.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="service_materials")]
        ])
        
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    text = f"""
    📚 *{grade_name}*
    
    *المواد المتاحة ({len(materials)}) :*
    """
    
    keyboard_buttons = []
    
    for i, material in enumerate(materials[:10], 1):
        material_id, name, description, grade, file_id, added_by, added_date = material
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"{i}. {name}", callback_data=f"material_{material_id}")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data="service_materials")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("material_"))
async def material_detail(callback_query: CallbackQuery):
    """عرض تفاصيل مادة معينة"""
    material_id = int(callback_query.data.split("_")[1])
    
    # TODO: جلب تفاصيل المادة من قاعدة البيانات وإرسال الملف
    
    await callback_query.answer("سيتم إرسال الملف قريباً...")

@dp.callback_query(lambda c: c.data == "vip_lectures")
async def vip_lectures(callback_query: CallbackQuery):
    """قسم محاضرات VIP"""
    user_id = callback_query.from_user.id
    
    # التحقق من الوصول
    access, message = await check_access(user_id, "vip_lecture")
    if not access:
        await callback_query.answer(message)
        return
    
    text = """
    🎬 *محاضرات VIP*
    
    *مكتبة المحاضرات المميزة:*
    • محاضرات فيديو متقدمة
    • شرح مفصل للمواد
    • أساتذة متخصصون
    • تقييمات ومتابعة
    
    *ملاحظة:* كل محاضرة لها سعر خاص.
    """
    
    keyboard = await vip_lectures_keyboard()
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "vip_view_lectures")
async def vip_view_lectures(callback_query: CallbackQuery):
    """عرض محاضرات VIP"""
    # الحصول على المحاضرات المعتمدة
    lectures = db.get_approved_lectures()
    
    if not lectures:
        text = """
        📭 *محاضرات VIP*
        
        لا توجد محاضرات متاحة حالياً.
        
        سيتم إضافة محاضرات قريباً.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="vip_lectures")]
        ])
        
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    text = f"""
    🎬 *محاضرات VIP المتاحة*
    
    *عدد المحاضرات:* {len(lectures)}
    
    *القائمة:*
    """
    
    keyboard_buttons = []
    
    for i, lecture in enumerate(lectures[:10], 1):
        lecture_id, teacher_id, title, description, subject, file_id, price, is_approved, views, purchases, rating, total_ratings, upload_date = lecture
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"{i}. {title} ({price} دينار)", callback_data=f"lecture_{lecture_id}")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data="vip_lectures")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("lecture_"))
async def lecture_detail(callback_query: CallbackQuery, state: FSMContext):
    """عرض تفاصيل محاضرة"""
    lecture_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    
    # TODO: جلب تفاصيل المحاضرة من قاعدة البيانات
    
    text = f"""
    🎬 *محاضرة #{lecture_id}
    
    *السعر:* 3000 دينار
    *المشاهدات:* 150
    *التقييم:* ⭐⭐⭐⭐⭐ (4.8)
    
    *وصف المحاضرة:*
    هذه محاضرة متقدمة في مادة الرياضيات تشرح المواضيع الصعبة بطريقة مبسطة.
    
    *لشراء المحاضرة:* اضغط على زر الشراء
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 شراء المحاضرة (3000 دينار)", callback_data=f"buy_lecture_{lecture_id}")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="vip_view_lectures")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("buy_lecture_"))
async def buy_lecture(callback_query: CallbackQuery, state: FSMContext):
    """شراء محاضرة"""
    lecture_id = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id
    
    # التحقق من الرصيد
    price = db.get_service_price("vip_lecture")
    user = db.get_user(user_id)
    
    if user[4] < price:
        await callback_query.answer(f"❌ رصيدك غير كافي. السعر: {price} دينار")
        return
    
    # خصم المبلغ وتسجيل الشراء
    if await deduct_balance(user_id, "vip_lecture"):
        # TODO: تسجيل الشراء في قاعدة البيانات
        # TODO: إرسال المحاضرة للمستخدم
        
        text = f"""
        ✅ *تم شراء المحاضرة بنجاح*
        
        *رقم المحاضرة:* #{lecture_id}
        *المبلغ المدفوع:* {price} دينار
        *الرصيد المتبقي:* {user[4] - price} دينار
        
        *سيتم إرسال المحاضرة إليك قريباً.*
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_to_main")]
        ])
        
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        
        # إرسال إشعار للمحاضر
        # TODO: إرسال إشعار للمحاسبين
    else:
        await callback_query.answer("❌ فشل في عملية الشراء")

@dp.callback_query(lambda c: c.data == "vip_subscribe")
async def vip_subscribe(callback_query: CallbackQuery):
    """قسم اشتراك VIP"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    is_vip = user[7] if user else 0
    
    if is_vip:
        text = f"""
        👑 *اشتراك VIP - نشط*
        
        *حالة اشتراكك:* ✅ نشط
        *تاريخ الانتهاء:* {user[8] if user[8] else 'غير محدد'}
        
        *مميزات الاشتراك:*
        • رفع محاضرات VIP
        • تحصيل أرباح من المبيعات
        • لوحة تحكم خاصة
        • دعم فني مميز
        
        اختر الخدمة:
        """
    else:
        text = """
        👑 *اشتراك VIP*
        
        *انضم كمعلم VIP واحصل على:*
        • رفع محاضرات فيديو
        • أرباح 60% من مبيعات محاضراتك
        • لوحة تحكم متكاملة
        • دعم فني مميز
        • شهر اشتراك مجاني للتجربة
        
        *سعر الاشتراك الشهري:* 5000 دينار
        
        اختر الخدمة:
        """
    
    keyboard = await vip_subscribe_keyboard(user_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "vip_subscribe_now")
async def vip_subscribe_now(callback_query: CallbackQuery):
    """اشتراك VIP"""
    user_id = callback_query.from_user.id
    
    # التحقق من الوصول
    access, message = await check_access(user_id, "vip_subscription")
    if not access:
        await callback_query.answer(message)
        return
    
    # خصم المبلغ
    if await deduct_balance(user_id, "vip_subscription"):
        # تحديث حالة VIP للمستخدم
        expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        cursor = db.conn.cursor()
        cursor.execute('UPDATE users SET is_vip = 1, vip_expiry = ? WHERE user_id = ?', (expiry_date, user_id))
        db.conn.commit()
        
        text = f"""
        ✅ *تم الاشتراك في VIP بنجاح*
        
        *مدة الاشتراك:* 30 يوم
        *تاريخ الانتهاء:* {expiry_date}
        *المبلغ المدفوع:* 5000 دينار
        
        *مميزاتك الجديدة:*
        • ✓ رفع محاضرات VIP
        • ✓ تحصيل أرباح 60%
        • ✓ لوحة تحكم خاصة
        • ✓ دعم فني مميز
        
        *لبدء رفع المحاضرات:* اضغط على زر "محاضراتي"
        """
        
        keyboard = await vip_subscribe_keyboard(user_id)
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback_query.answer("❌ فشل في عملية الاشتراك")

@dp.callback_query(lambda c: c.data == "vip_my_lectures")
async def vip_my_lectures(callback_query: CallbackQuery):
    """محاضراتي (للمحاضر VIP)"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    if not user or user[7] == 0:  # ليس VIP
        await callback_query.answer("⛔ هذه الخدمة للمشتركين في VIP فقط")
        return
    
    text = """
    🎬 *محاضراتي - لوحة المحاضر*
    
    *اختر الإجراء:*
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ رفع محاضرة جديدة", callback_data="vip_add_lecture")],
        [InlineKeyboardButton(text="🗑️ حذف محاضرة", callback_data="vip_delete_lecture")],
        [InlineKeyboardButton(text="📊 إحصائيات محاضراتي", callback_data="vip_lecture_stats")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="vip_subscribe")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "vip_add_lecture")
async def vip_add_lecture(callback_query: CallbackQuery, state: FSMContext):
    """بدء عملية رفع محاضرة جديدة"""
    await state.set_state(Form.vip_add_lecture_title)
    
    text = """
    *رفع محاضرة جديدة - الخطوة 1/5*
    
    *أدخل عنوان المحاضرة:*
    
    *مثال:* "شرح التفاضل والتكامل - الجزء الأول"
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="vip_my_lectures")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.vip_add_lecture_title)
async def process_vip_title(message: Message, state: FSMContext):
    """معالجة عنوان المحاضرة"""
    title = message.text
    
    if len(title) < 5:
        await message.answer("❌ العنوان قصير جداً. الرجاء إدخال عنوان واضح.")
        return
    
    await state.update_data(title=title)
    await state.set_state(Form.vip_add_lecture_desc)
    
    text = """
    *رفع محاضرة جديدة - الخطوة 2/5*
    
    *أدخل وصف المحاضرة:*
    
    *مثال:* "هذه المحاضرة تغطي أساسيات التفاضل والتكامل مع أمثلة تطبيقية"
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="vip_my_lectures")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.vip_add_lecture_desc)
async def process_vip_desc(message: Message, state: FSMContext):
    """معالجة وصف المحاضرة"""
    description = message.text
    
    if len(description) < 10:
        await message.answer("❌ الوصف قصير جداً. الرجاء إدخال وصف مفصل.")
        return
    
    await state.update_data(description=description)
    await state.set_state(Form.vip_add_lecture_subject)
    
    text = """
    *رفع محاضرة جديدة - الخطوة 3/5*
    
    *أدخل اسم المادة:*
    
    *مثال:* "الرياضيات", "الفيزياء", "الكيمياء"
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="vip_my_lectures")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.vip_add_lecture_subject)
async def process_vip_subject(message: Message, state: FSMContext):
    """معالجة اسم المادة"""
    subject = message.text
    
    await state.update_data(subject=subject)
    await state.set_state(Form.vip_add_lecture_price)
    
    text = """
    *رفع محاضرة جديدة - الخطوة 4/5*
    
    *أدخل سعر المحاضرة (بالدينار العراقي):*
    
    *الحد الأدنى:* 1000 دينار
    *الحد الأقصى:* 10000 دينار
    
    *ملاحظة:* ستحصل على 60% من سعر البيع.
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="vip_my_lectures")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.vip_add_lecture_price)
async def process_vip_price(message: Message, state: FSMContext):
    """معالجة سعر المحاضرة"""
    try:
        price = int(message.text)
        
        if price < 1000 or price > 10000:
            await message.answer("❌ السعر يجب أن يكون بين 1000 و 10000 دينار")
            return
        
        await state.update_data(price=price)
        await state.set_state(Form.vip_add_lecture_file)
        
        text = """
        *رفع محاضرة جديدة - الخطوة 5/5*
        
        *قم بإرسال ملف الفيديو:*
        
        *الشروط:*
        1. الملف بصيغة MP4
        2. حجم الملف لا يتعدى 50MB
        3. جودة واضحة
        4. بدون حقوق نشر
        
        *ملاحظة:* المحاضرة تحتاج موافقة الإدارة قبل النشر.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 إلغاء", callback_data="vip_my_lectures")]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Form.vip_add_lecture_file)
async def process_vip_file(message: Message, state: FSMContext):
    """معالجة ملف المحاضرة"""
    if not message.video and not message.document:
        await message.answer("❌ الرجاء إرسال ملف فيديو")
        return
    
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        if not message.document.file_name.endswith('.mp4'):
            await message.answer("❌ الملف يجب أن يكون بصيغة MP4")
            return
        file_id = message.document.file_id
    
    data = await state.get_data()
    
    # حفظ المحاضرة في قاعدة البيانات
    lecture_id = db.add_vip_lecture(
        message.from_user.id,
        data['title'],
        data['description'],
        data['subject'],
        file_id,
        data['price']
    )
    
    text = f"""
    ✅ *تم رفع المحاضرة بنجاح*
    
    *رقم المحاضرة:* #{lecture_id}
    *العنوان:* {data['title']}
    *المادة:* {data['subject']}
    *السعر:* {data['price']} دينار
    
    *حالة المحاضرة:* ⏳ قيد المراجعة
    
    *ملاحظة:* سوف يتم مراجعة محاضرتك من قبل الإدارة قبل النشر.
    ستتلقى إشعاراً عند الموافقة أو الرفض.
    """
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_to_main")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # إرسال إشعار للمدير
    admin_text = f"""
    🎬 *محاضرة VIP جديدة تحتاج موافقة*
    
    *رقم المحاضرة:* #{lecture_id}
    *المحاضر:* @{message.from_user.username or 'بدون يوزر'}
    *الاسم:* {message.from_user.first_name}
    *الآيدي:* {message.from_user.id}
    
    *العنوان:* {data['title']}
    *المادة:* {data['subject']}
    *السعر:* {data['price']} دينار
    
    *الوصف:*
    {data['description']}
    
    *للموافقة:* /approve_lecture {lecture_id}
    *للرفض:* /reject_lecture {lecture_id}
    """
    
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "vip_my_earnings")
async def vip_my_earnings(callback_query: CallbackQuery):
    """أرباحي (للمحاضر VIP)"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    if not user or user[7] == 0:  # ليس VIP
        await callback_query.answer("⛔ هذه الخدمة للمشتركين في VIP فقط")
        return
    
    # حساب الأرباح
    earnings = db.get_teacher_earnings(user_id)
    min_withdrawal = int(db.get_setting('min_withdrawal') or 15000)
    
    text = f"""
    💰 *أرباحي - لوحة المحاضر*
    
    *الأرباح المعلقة:* {earnings} دينار
    *الحد الأدنى للسحب:* {min_withdrawal} دينار
    
    *نظام الأرباح:*
    • تحصل على 60% من سعر بيع كل محاضرة
    • يمكن سحب الأرباح عند الوصول للحد الأدنى
    • عملية السحب تتم خلال 24 ساعة
    """
    
    keyboard_buttons = []
    
    if earnings >= min_withdrawal:
        keyboard_buttons.append([
            InlineKeyboardButton(text="💳 طلب سحب الأرباح", callback_data="vip_withdraw_earnings")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="📊 تفاصيل الأرباح", callback_data="vip_earnings_details")
    ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data="vip_subscribe")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ===================== معالجة الرصيد =====================
@dp.callback_query(lambda c: c.data == "my_balance")
async def my_balance(callback_query: CallbackQuery):
    """عرض الرصيد"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback_query.answer("الرجاء استخدام /start أولاً")
        return
    
    text = f"""
    💰 *معلومات الرصيد*
    
    *الرصيد الحالي:* {user[4]} دينار
    *إجمالي المصروف:* {user[12] if len(user) > 12 else 0} دينار
    
    *اختر الخدمة:*
    """
    
    keyboard = await balance_keyboard()
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "balance_current")
async def balance_current(callback_query: CallbackQuery):
    """عرض الرصيد الحالي"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    text = f"""
    💰 *الرصيد الحالي*
    
    *المبلغ:* {user[4]} دينار
    
    *لشحن الرصيد:* تواصل مع الدعم الفني
    @Allawi04
    
    *أو استخدم دعوة الأصدقاء لكسب نقاط مجانية.*
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 دعوة أصدقاء", callback_data="balance_referral")],
        [InlineKeyboardButton(text="💬 الدعم الفني", url=SUPPORT_USERNAME)],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="my_balance")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "balance_referral")
async def balance_referral(callback_query: CallbackQuery):
    """دعوة الأصدقاء"""
    user_id = callback_query.from_user.id
    user = db.get_user(user_id)
    
    referral_bonus = int(db.get_setting('referral_bonus') or 500)
    referral_code = user[9] if user and len(user) > 9 else f"REF{user_id}"
    
    text = f"""
    👥 *دعوة الأصدقاء*
    
    *كود دعوتك:* `{referral_code}`
    
    *طريقة العمل:*
    1. أرسل كود الدعوة لأصدقائك
    2. عند تسجيلهم، يستخدمون كود الدعوة
    3. تحصل على {referral_bonus} دينار لكل صديق
    4. صديقك يحصل على {referral_bonus} دينار هدية
    
    *رابط الدعوة:* https://t.me/{BOT_USERNAME.replace('@', '')}?start={referral_code}
    
    *عدد الأصدقاء المدعوين:* 0
    *إجمالي المكافآت:* 0 دينار
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 مشاركة الرابط", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME.replace('@', '')}?start={referral_code}&text=انضم%20إلى%20بوت%20يلا%20نتعلم%20للخدمات%20التعليمية%20المميزة")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="my_balance")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ===================== أوامر المدير =====================
@dp.message(Command("approve_question"))
async def cmd_approve_question(message: Message, command: CommandObject):
    """موافقة على سؤال"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if not command.args:
        await message.answer("❌ الرجاء إضافة رقم السؤال\n\nمثال: /approve_question 123")
        return
    
    try:
        question_id = int(command.args)
        if db.approve_question(question_id):
            await message.answer(f"✅ تمت الموافقة على السؤال #{question_id}")
            
            # TODO: إرسال إشعار للمستخدم
            # TODO: نشر السؤال في قسم الأسئلة
        else:
            await message.answer("❌ لم يتم العثور على السؤال")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Command("reject_question"))
async def cmd_reject_question(message: Message, command: CommandObject):
    """رفض سؤال"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if not command.args:
        await message.answer("❌ الرجاء إضافة رقم السؤال\n\nمثال: /reject_question 123")
        return
    
    try:
        question_id = int(command.args)
        # TODO: حذف السؤال من قاعدة البيانات
        await message.answer(f"✅ تم رفض السؤال #{question_id}")
        
        # TODO: إرسال إشعار للمستخدم
        # TODO: إعادة الرصيد للمستخدم
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Command("approve_lecture"))
async def cmd_approve_lecture(message: Message, command: CommandObject):
    """موافقة على محاضرة"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if not command.args:
        await message.answer("❌ الرجاء إضافة رقم المحاضرة\n\nمثال: /approve_lecture 123")
        return
    
    try:
        lecture_id = int(command.args)
        if db.approve_lecture(lecture_id):
            await message.answer(f"✅ تمت الموافقة على المحاضرة #{lecture_id}")
            
            # TODO: إرسال إشعار للمحاضر
        else:
            await message.answer("❌ لم يتم العثور على المحاضرة")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Command("reject_lecture"))
async def cmd_reject_lecture(message: Message, command: CommandObject):
    """رفض محاضرة"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if not command.args:
        await message.answer("❌ الرجاء إضافة رقم المحاضرة\n\nمثال: /reject_lecture 123")
        return
    
    try:
        lecture_id = int(command.args)
        if db.reject_lecture(lecture_id):
            await message.answer(f"✅ تم رفض المحاضرة #{lecture_id}")
            
            # TODO: إرسال إشعار للمحاضر
        else:
            await message.answer("❌ لم يتم العثور على المحاضرة")
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

@dp.message(Command("charge"))
async def cmd_charge(message: Message, command: CommandObject):
    """شحن رصيد (للمدير)"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if not command.args:
        await message.answer("❌ الصيغة: /charge <user_id> <amount>")
        return
    
    try:
        args = command.args.split()
        if len(args) != 2:
            await message.answer("❌ الصيغة: /charge <user_id> <amount>")
            return
        
        user_id = int(args[0])
        amount = int(args[1])
        
        new_balance = db.update_balance(user_id, amount, 'add')
        if new_balance is not None:
            db.add_transaction(user_id, amount, 'admin_charge', 'شحن من المدير')
            
            await message.answer(f"""
            ✅ تم شحن الرصيد بنجاح
            
            *المستخدم:* {user_id}
            *المبلغ:* {amount} دينار
            *الرصيد الجديد:* {new_balance} دينار
            """, parse_mode="Markdown")
            
            # إرسال إشعار للمستخدم
            try:
                await bot.send_message(user_id, f"""
                💰 *تم شحن رصيدك*
                
                *المبلغ:* {amount} دينار
                *الرصيد الجديد:* {new_balance} دينار
                *السبب:* شحن من الإدارة
                """, parse_mode="Markdown")
            except:
                pass
        else:
            await message.answer("❌ لم يتم العثور على المستخدم")
    except ValueError:
        await message.answer("❌ الرجاء إدخال أرقام صحيحة")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """إحصائيات البوت"""
    if message.from_user.id != ADMIN_ID:
        return
    
    stats = db.get_statistics()
    
    text = f"""
    📊 *إحصائيات البوت*
    
    *المستخدمين:*
    • إجمالي المستخدمين: {stats['total_users']}
    • نشط اليوم: {stats['active_today']}
    • مشتركين VIP: {stats['vip_users']}
    
    *المالية:*
    • إجمالي الرصيد: {stats['total_balance']} دينار
    • إجمالي الإيرادات: {stats['total_revenue']} دينار
    
    *الخدمات:*
    • الخدمات النشطة: {len(db.get_active_services())}
    • الخدمات المعطلة: {6 - len(db.get_active_services())}
    
    *النظام:*
    • وضع الصيانة: {'✅ مفعل' if db.get_setting('maintenance_mode') == '1' else '❌ معطل'}
    """
    
    await message.answer(text, parse_mode="Markdown")

# ===================== Callback Queries للمدير =====================
@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback_query: CallbackQuery):
    """إحصائيات البوت للمدير"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("⛔ ليس لديك صلاحية")
        return
    
    stats = db.get_statistics()
    
    text = f"""
    📊 *إحصائيات البوت - المدير*
    
    *المستخدمين:*
    • إجمالي المستخدمين: {stats['total_users']}
    • نشط اليوم: {stats['active_today']}
    • مشتركين VIP: {stats['vip_users']}
    • محظورين: {len([u for u in db.get_all_users() if u[5] == 1])}
    
    *المالية:*
    • إجمالي الرصيد: {stats['total_balance']} دينار
    • إجمالي الإيرادات: {stats['total_revenue']} دينار
    • متوسط الإنفاق: {stats['total_revenue'] // max(stats['total_users'], 1)} دينار/مستخدم
    
    *الخدمات:*
    • الخدمات النشطة: {len(db.get_active_services())}
    • الخدمات المعطلة: {6 - len(db.get_active_services())}
    
    *النظام:*
    • وضع الصيانة: {'✅ مفعل' if db.get_setting('maintenance_mode') == '1' else '❌ معطل'}
    • عدد المحاضرات: {len(db.get_approved_lectures())}
    • الأسئلة المعلقة: {len(db.get_pending_questions())}
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 تحديث", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📈 تفاصيل مالية", callback_data="admin_financial_stats")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback_query: CallbackQuery):
    """إدارة المستخدمين للمدير"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("⛔ ليس لديك صلاحية")
        return
    
    keyboard = await admin_users_keyboard()
    await callback_query.message.edit_text("👥 *إدارة المستخدمين*", reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "admin_balance")
async def admin_balance_menu(callback_query: CallbackQuery):
    """إدارة الرصيد للمدير"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("⛔ ليس لديك صلاحية")
        return
    
    keyboard = await admin_balance_keyboard()
    await callback_query.message.edit_text("💰 *إدارة الرصيد*", reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "admin_services")
async def admin_services_menu(callback_query: CallbackQuery):
    """إدارة الخدمات للمدير"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("⛔ ليس لديك صلاحية")
        return
    
    keyboard = await admin_services_keyboard()
    await callback_query.message.edit_text("🛠️ *إدارة الخدمات*", reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "admin_charge")
async def admin_charge_start(callback_query: CallbackQuery, state: FSMContext):
    """بدء عملية الشحن للمدير"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("⛔ ليس لديك صلاحية")
        return
    
    await state.set_state(Form.admin_charge)
    
    text = """
    *شحن رصيد - المدير*
    
    *أدخل آيدي المستخدم:*
    
    *ملاحظة:* سوف تطلب منك إدخال المبلغ في الخطوة التالية.
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Form.admin_charge)
async def process_admin_charge(message: Message, state: FSMContext):
    """معالجة شحن الرصيد"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text)
        user = db.get_user(user_id)
        
        if not user:
            await message.answer("❌ لم يتم العثور على المستخدم")
            await state.clear()
            return
        
        await state.update_data(charge_user_id=user_id)
        await state.set_state(Form.admin_charge)
        
        text = f"""
        *شحن رصيد - الخطوة 2*
        
        *المستخدم:* {user_id}
        *الاسم:* {user[2]} {user[3] or ''}
        *الرصيد الحالي:* {user[4]} دينار
        
        *أدخل المبلغ للشحن (بالدينار):*
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 إلغاء", callback_data="admin_back")]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except ValueError:
        await message.answer("❌ الرجاء إدخال آيدي صحيح")

# TODO: استكمال باقي وظائف المدير...

@dp.callback_query(lambda c: c.data == "admin_back")
async def admin_back(callback_query: CallbackQuery):
    """العودة للوحة تحكم المدير"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("⛔ ليس لديك صلاحية")
        return
    
    keyboard = await admin_panel_keyboard(callback_query.from_user.id)
    await callback_query.message.edit_text("👑 *لوحة تحكم المدير*", reply_markup=keyboard, parse_mode="Markdown")

# ===================== وظائف الصيانة =====================
async def check_maintenance():
    """فحص وضع الصيانة"""
    maintenance = db.get_setting('maintenance_mode')
    return maintenance == '1'

async def send_maintenance_message(chat_id: int):
    """إرسال رسالة الصيانة"""
    text = """
    🔧 *البوت قيد الصيانة*
    
    نعمل حالياً على تحسين الخدمة وإضافة مميزات جديدة.
    
    *مدة الصيانة:* غير محددة
    *وقت العودة:* قريباً إن شاء الله
    
    نشكر صبركم وتفهمكم.
    """
    
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# ===================== وظائف الخلفية =====================
async def check_vip_expiry():
    """فحص انتهاء صلاحية اشتراكات VIP"""
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT user_id, vip_expiry 
        FROM users 
        WHERE is_vip = 1 AND vip_expiry IS NOT NULL
    ''')
    
    users = cursor.fetchall()
    today = datetime.now().strftime("%Y-%m-%d")
    
    for user_id, expiry_date in users:
        if expiry_date < today:
            cursor.execute('UPDATE users SET is_vip = 0 WHERE user_id = ?', (user_id,))
            
            try:
                await bot.send_message(user_id, """
                ⏰ *انتهاء اشتراك VIP*
                
                انتهت فترة اشتراكك في VIP.
                
                لاستعادة المميزات، يمكنك تجديد الاشتراك من قسم VIP.
                
                شكراً لاستخدامك خدماتنا.
                """, parse_mode="Markdown")
            except:
                pass
    
    db.conn.commit()

async def scheduled_tasks():
    """المهام المجدولة"""
    while True:
        try:
            await check_vip_expiry()
            await asyncio.sleep(3600)  # كل ساعة
        except Exception as e:
            logging.error(f"خطأ في المهام المجدولة: {e}")
            await asyncio.sleep(300)

# ===================== التشغيل الرئيسي =====================
async def main():
    """الدالة الرئيسية"""
    logging.basicConfig(level=logging.INFO)
    
    # تحميل الخطوط
    await download_fonts()
    
    # بدء المهام المجدولة
    asyncio.create_task(scheduled_tasks())
    
    # بدء البوت
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
