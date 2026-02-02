#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام للتعليم - يلا نتعلم
مطور بواسطة: Allawi
الدعم الفني: @Allawi04
"""

import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import string
import hashlib
from pathlib import Path

# المكتبات الأساسية
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, 
    ConversationHandler, filters
)
from telegram.constants import ParseMode

# مكتبات الذكاء الاصطناعي والتعامل مع PDF
import google.generativeai as genai
from PyPDF2 import PdfReader
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image
import io
import pytesseract
from deep_translator import GoogleTranslator

# مكتبات إضافية
import sqlite3
import threading
from functools import wraps
import re

# ============================================
# إعدادات التكوين
# ============================================

# توكن البوت
TOKEN = "8481569753:AAHTdbWwu0BHmoo_iHPsye8RkTptWzfiQWU"

# إعدادات الذكاء الاصطناعي
GEMINI_API_KEY = "AIzaSyAqlug21bw_eI60ocUtc1Z76NhEUc-zuzY"

# إعدادات المطور
ADMIN_ID = 6130994941  # آيدي المطور
ADMIN_USERNAME = "@Allawi04"  # يوزر المطور

# إعدادات البوت
BOT_USERNAME = "@FC4Xbot"
BOT_NAME = "يلا نتعلم"

# إعدادات العملة
CURRENCY = "دينار عراقي"
MIN_SERVICE_PRICE = 1000
WELCOME_BONUS = 1000

# تسعيرات الخدمات (قابلة للتعديل من لوحة التحكم)
SERVICE_PRICES = {
    "عفوية": 1000,  # حساب درجة العفو
    "تلخيص": 1000,  # تلخيص الملازم
    "أسئلة": 1000,  # أسئلة وأجوبة
    "ملازم": 1000   # قسم الملازم
}

# حالات المحادثة
CALCULATE, COURSE1, COURSE2, COURSE3, WAITING_PDF, PROCESSING_PDF = range(6)
ASK_QUESTION, WAITING_ANSWER, ADMIN_PANEL, CHARGE_USER, ADD_POINTS = range(6, 11)
BROADCAST, ADD_MATERIAL, MATERIAL_NAME, MATERIAL_DESC, MATERIAL_FILE = range(11, 16)
SET_PRICE, MAINTENANCE, INVITE_SETTINGS = range(16, 19)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تسجيل الخطوط العربية
def setup_arabic_fonts():
    """تسجيل الخطوط العربية للاستخدام في ملفات PDF"""
    try:
        # استخدام خط افتراضي (يجب تثبيت خط عربي على النظام)
        arabic_font_path = "/usr/share/fonts/truetype/arabic/arial.ttf"
        if os.path.exists(arabic_font_path):
            pdfmetrics.registerFont(TTFont('Arabic', arabic_font_path))
        else:
            # استخدام خط بديل إذا لم يوجد
            pdfmetrics.registerFont(TTFont('Arabic', 'DejaVuSans'))
        
        pdfmetrics.registerFont(TTFont('English', 'Helvetica'))
        return True
    except Exception as e:
        logger.error(f"خطأ في تسجيل الخطوط: {e}")
        return False

# إعداد الذكاء الاصطناعي
def setup_ai():
    """تهيئة نموذج الذكاء الاصطناعي"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # إنشاء النموذج
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        return model
    except Exception as e:
        logger.error(f"خطأ في تهيئة الذكاء الاصطناعي: {e}")
        return None

# ============================================
# قاعدة البيانات
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_database()
    
    def init_database(self):
        """تهيئة جداول قاعدة البيانات"""
        # جدول المستخدمين
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance INTEGER DEFAULT 0,
                invite_code TEXT UNIQUE,
                invited_by INTEGER,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                banned INTEGER DEFAULT 0
            )
        ''')
        
        # جدول العمليات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الخدمات المستخدمة
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_type TEXT,
                cost INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المواد التعليمية
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                file_id TEXT,
                stage TEXT,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الإعدادات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # إضافة الإعدادات الافتراضية
        default_settings = [
            ('maintenance', '0'),
            ('invite_bonus', '500'),
            ('channel_link', 'https://t.me/+channel'),
            ('support_username', '@Allawi04')
        ]
        
        for key, value in default_settings:
            self.cursor.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        
        self.conn.commit()
    
    # ============ إدارة المستخدمين ============
    def add_user(self, user_id, username, first_name, last_name):
        """إضافة مستخدم جديد"""
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        self.cursor.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, username, first_name, last_name, balance, invite_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, WELCOME_BONUS, invite_code))
        
        # تسجيل عملية المكافأة الترحيبية
        if self.cursor.rowcount > 0:
            self.add_transaction(user_id, WELCOME_BONUS, 'welcome_bonus', 'مكافأة ترحيبية')
        
        self.conn.commit()
        return invite_code
    
    def get_user(self, user_id):
        """الحصول على بيانات مستخدم"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = self.cursor.fetchone()
        
        if user:
            columns = [description[0] for description in self.cursor.description]
            return dict(zip(columns, user))
        return None
    
    def update_balance(self, user_id, amount):
        """تحديث رصيد المستخدم"""
        self.cursor.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?',
            (amount, user_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_balance(self, user_id):
        """الحصول على رصيد المستخدم"""
        self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        self.cursor.execute('SELECT * FROM users ORDER BY join_date DESC')
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def ban_user(self, user_id):
        """حظر مستخدم"""
        self.cursor.execute(
            'UPDATE users SET banned = 1 WHERE user_id = ?',
            (user_id,)
        )
        self.conn.commit()
    
    def unban_user(self, user_id):
        """إلغاء حظر مستخدم"""
        self.cursor.execute(
            'UPDATE users SET banned = 0 WHERE user_id = ?',
            (user_id,)
        )
        self.conn.commit()
    
    # ============ إدارة العمليات ============
    def add_transaction(self, user_id, amount, trans_type, description):
        """إضافة عملية مالية"""
        self.cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, trans_type, description))
        self.conn.commit()
    
    def get_user_transactions(self, user_id, limit=10):
        """الحصول على عمليات مستخدم"""
        self.cursor.execute('''
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    # ============ إدارة الخدمات ============
    def add_service_usage(self, user_id, service_type, cost):
        """تسجيل استخدام خدمة"""
        self.cursor.execute('''
            INSERT INTO services (user_id, service_type, cost)
            VALUES (?, ?, ?)
        ''', (user_id, service_type, cost))
        self.conn.commit()
    
    def get_service_stats(self):
        """إحصائيات الخدمات"""
        self.cursor.execute('''
            SELECT service_type, COUNT(*) as count, SUM(cost) as total 
            FROM services 
            GROUP BY service_type
        ''')
        
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    # ============ إدارة المواد ============
    def add_material(self, name, description, file_id, stage, added_by):
        """إضافة مادة تعليمية"""
        self.cursor.execute('''
            INSERT INTO materials (name, description, file_id, stage, added_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, file_id, stage, added_by))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_materials(self, stage=None):
        """الحصول على المواد التعليمية"""
        if stage:
            self.cursor.execute(
                'SELECT * FROM materials WHERE stage = ? ORDER BY added_date DESC',
                (stage,)
            )
        else:
            self.cursor.execute('SELECT * FROM materials ORDER BY added_date DESC')
        
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def delete_material(self, material_id):
        """حذف مادة تعليمية"""
        self.cursor.execute('DELETE FROM materials WHERE id = ?', (material_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    # ============ إدارة الإعدادات ============
    def get_setting(self, key):
        """الحصول على إعداد"""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def update_setting(self, key, value):
        """تحديث إعداد"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()
    
    def get_service_price(self, service_type):
        """الحصول على سعر الخدمة"""
        price = self.get_setting(f'price_{service_type}')
        return int(price) if price else SERVICE_PRICES.get(service_type, MIN_SERVICE_PRICE)
    
    def update_service_price(self, service_type, price):
        """تحديث سعر الخدمة"""
        self.update_setting(f'price_{service_type}', str(price))
    
    def get_invite_bonus(self):
        """الحصول على مكافأة الدعوة"""
        bonus = self.get_setting('invite_bonus')
        return int(bonus) if bonus else 500
    
    def update_invite_bonus(self, bonus):
        """تحديث مكافأة الدعوة"""
        self.update_setting('invite_bonus', str(bonus))
    
    def get_maintenance_mode(self):
        """الحصول على حالة الصيانة"""
        mode = self.get_setting('maintenance')
        return mode == '1'
    
    def set_maintenance_mode(self, enabled):
        """تحديث حالة الصيانة"""
        self.update_setting('maintenance', '1' if enabled else '0')
    
    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        self.conn.close()

# إنشاء كائن قاعدة البيانات
db = Database()

# ============================================
# أدوات مساعدة
# ============================================

def admin_only(func):
    """ديكوراتور للتحقق من صلاحيات المشرف"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text(
                "⛔️ هذا الأمر مخصص للمشرفين فقط!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def check_balance(price):
    """ديكوراتور للتحقق من الرصيد"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            user_balance = db.get_balance(user_id)
            
            if user_balance < price:
                await update.message.reply_text(
                    f"💰 رصيدك غير كاف!\n"
                    f"سعر الخدمة: {price} {CURRENCY}\n"
                    f"رصيدك الحالي: {user_balance} {CURRENCY}\n\n"
                    f"لشحن الرصيد تواصل مع الدعم الفني: {ADMIN_USERNAME}",
                    reply_markup=main_menu_keyboard()
                )
                return
            
            # خصم المبلغ
            db.update_balance(user_id, -price)
            db.add_transaction(user_id, -price, 'service_payment', f'دفع مقابل خدمة: {func.__name__}')
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def check_maintenance(func):
    """ديكوراتور للتحقق من وضع الصيانة"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if db.get_maintenance_mode() and update.effective_user.id != ADMIN_ID:
            await update.message.reply_text(
                "🔧 البوت قيد الصيانة حالياً...\n"
                "نأسف للإزعاج، سنعود قريباً!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def format_arabic_text(text):
    """تنسيق النص العربي للعرض"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except:
        return text

# ============================================
# لوحات المفاتيح
# ============================================

def main_menu_keyboard():
    """لوحة المفاتيح الرئيسية"""
    keyboard = [
        ["📊 حساب درجة العفوية"],
        ["📄 تلخيص الملازم بالذكاء الاصطناعي"],
        ["❓ أسئلة وأجوبة بالذكاء الاصطناعي"],
        ["📚 ملازمي ومرشحاتي"],
        ["💰 رصيدي", "📤 دعوة أصدقاء"],
        ["ℹ️ معلومات", "👨‍💻 الدعم الفني"]
    ]
    
    # إضافة زر لوحة التحكم للمشرف فقط
    if threading.current_thread() == threading.main_thread():
        # في التطبيق الفعلي سيتم التحقق من خلال context
        pass
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_keyboard():
    """لوحة مفاتيح المشرف"""
    keyboard = [
        ["📊 إحصائيات", "👥 إدارة المستخدمين"],
        ["💰 شحن رصيد", "⚙️ تغيير الأسعار"],
        ["📚 إدارة المواد", "🎁 إعدادات الدعوة"],
        ["🔧 وضع الصيانة", "📢 إرسال إشعار"],
        ["🏠 العودة للقائمة الرئيسية"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_to_main_keyboard():
    """زر العودة للقائمة الرئيسية"""
    return ReplyKeyboardMarkup([["🏠 العودة للقائمة الرئيسية"]], resize_keyboard=True)

def stages_keyboard():
    """لوحة مفاتيح المراحل الدراسية"""
    keyboard = [
        ["المرحلة الأولى", "المرحلة الثانية"],
        ["المرحلة الثالثة", "المرحلة الرابعة"],
        ["🏠 العودة للقائمة الرئيسية"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ============================================
# معالجات الأوامر الرئيسية
# ============================================

@check_maintenance
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء استخدام البوت"""
    user = update.effective_user
    user_id = user.id
    
    # إضافة المستخدم إلى قاعدة البيانات
    invite_code = db.add_user(
        user_id, 
        user.username, 
        user.first_name, 
        user.last_name
    )
    
    # التحقق إذا كان المستخدم مدعو
    if context.args:
        inviter_code = context.args[0]
        # البحث عن المستخدم الذي دعا
        db.cursor.execute('SELECT user_id FROM users WHERE invite_code = ?', (inviter_code,))
        inviter = db.cursor.fetchone()
        
        if inviter:
            inviter_id = inviter[0]
            bonus = db.get_invite_bonus()
            
            # منح المكافأة للمدعو
            db.update_balance(user_id, bonus)
            db.add_transaction(user_id, bonus, 'invite_bonus', 'مكافأة دعوة صديق')
            
            # منح المكافأة للمدعو إليه
            db.update_balance(inviter_id, bonus)
            db.add_transaction(inviter_id, bonus, 'invite_bonus', 'مكافأة لدعوة صديق')
            
            # إرسال إشعار للمدعو إليه
            try:
                await context.bot.send_message(
                    inviter_id,
                    f"🎉 تم تسجيل صديقك عن طريق رابط دعوتك!\n"
                    f"حصلت على {bonus} {CURRENCY} مكافأة!"
                )
            except:
                pass
    
    # رسالة الترحيب
    welcome_text = f"""
    🎓 أهلاً بك {user.first_name} في بوت {BOT_NAME}!

    🎁 **مكافأة ترحيبية:** {WELCOME_BONUS} {CURRENCY}

    **الخدمات المتاحة:**
    1️⃣ حساب درجة العفوية - {db.get_service_price('عفوية')} {CURRENCY}
    2️⃣ تلخيص الملازم بالذكاء الاصطناعي - {db.get_service_price('تلخيص')} {CURRENCY}
    3️⃣ أسئلة وأجوبة بالذكاء الاصطناعي - {db.get_service_price('أسئلة')} {CURRENCY}
    4️⃣ ملازمي ومرشحاتي - {db.get_service_price('ملازم')} {CURRENCY}

    💰 **رصيدك الحالي:** {db.get_balance(user_id)} {CURRENCY}

    📤 **دعوة أصدقاء:** احصل على {db.get_invite_bonus()} {CURRENCY} لكل صديق!
    رابط دعوتك: https://t.me/{BOT_USERNAME.replace('@', '')}?start={invite_code}

    👨‍💻 **الدعم الفني:** {db.get_setting('support_username') or ADMIN_USERNAME}
    """
    
    await update.message.reply_text(
        format_arabic_text(welcome_text),
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@check_maintenance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رصيد المستخدم"""
    user_id = update.effective_user.id
    user_balance = db.get_balance(user_id)
    
    # الحصول على رابط الدعوة
    db.cursor.execute('SELECT invite_code FROM users WHERE user_id = ?', (user_id,))
    invite_code = db.cursor.fetchone()[0]
    invite_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={invite_code}"
    
    balance_text = f"""
    💰 **رصيدك الحالي:** {user_balance} {CURRENCY}

    📤 **دعوة أصدقاء:**
    احصل على {db.get_invite_bonus()} {CURRENCY} لكل صديق يدخل عبر رابطك!

    🔗 **رابط دعوتك:**
    `{invite_link}`

    💳 **لشحن الرصيد:**
    تواصل مع الدعم الفني: {db.get_setting('support_username') or ADMIN_USERNAME}
    """
    
    await update.message.reply_text(
        format_arabic_text(balance_text),
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@check_maintenance
async def invite_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات الدعوة"""
    user_id = update.effective_user.id
    
    # الحصول على رابط الدعوة
    db.cursor.execute('SELECT invite_code FROM users WHERE user_id = ?', (user_id,))
    invite_code = db.cursor.fetchone()[0]
    invite_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={invite_code}"
    
    # عدد الأشخاص الذين دعاهم
    db.cursor.execute('SELECT COUNT(*) FROM users WHERE invited_by = ?', (user_id,))
    invited_count = db.cursor.fetchone()[0]
    
    invite_text = f"""
    📤 **برنامج الدعوة:**

    🎁 **المكافأة:** {db.get_invite_bonus()} {CURRENCY} لكل صديق

    👥 **عدد الأصدقاء الذين دعيتهم:** {invited_count}

    💰 **إجمالي المكافآت:** {invited_count * db.get_invite_bonus()} {CURRENCY}

    🔗 **رابط دعوتك:**
    `{invite_link}`

    **طريقة الاستخدام:**
    1. أرسل الرابط لصديقك
    2. عندما ينقر عليه ويبدأ باستخدام البوت
    3. تحصل أنت وصديقك على المكافأة تلقائياً!
    """
    
    await update.message.reply_text(
        format_arabic_text(invite_text),
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@check_maintenance
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات البوت"""
    total_users = len(db.get_all_users())
    
    info_text = f"""
    ℹ️ **معلومات البوت:**

    **اسم البوت:** {BOT_NAME}
    **يوزر البوت:** {BOT_USERNAME}

    **👥 عدد المستخدمين:** {total_users}
    **💰 العملة:** {CURRENCY}

    **📢 قناة البوت:** {db.get_setting('channel_link') or 'غير مضبوط'}
    **👨‍💻 الدعم الفني:** {db.get_setting('support_username') or ADMIN_USERNAME}

    **الخدمات المتاحة:**
    1. حساب درجة العفوية
    2. تلخيص الملازم بالذكاء الاصطناعي
    3. أسئلة وأجوبة بالذكاء الاصطناعي
    4. ملازمي ومرشحاتي

    **المطور:** {ADMIN_USERNAME}
    """
    
    await update.message.reply_text(
        format_arabic_text(info_text),
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@check_maintenance
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الاتصال بالدعم الفني"""
    support_text = f"""
    👨‍💻 **الدعم الفني:**

    **يوزر الدعم:** {db.get_setting('support_username') or ADMIN_USERNAME}
    **أيدي المطور:** {ADMIN_ID}

    **طرق التواصل:**
    1. مراسلة الدعم الفني مباشرة
    2. للإبلاغ عن مشاكل في البوت
    3. لشحن الرصيد والاستفسارات المالية
    4. لاقتراح تحسينات جديدة

    **⏰ وقت الاستجابة:** خلال 24 ساعة
    """
    
    await update.message.reply_text(
        format_arabic_text(support_text),
        reply_markup=main_menu_keyboard()
    )

# ============================================
# الخدمة 1: حساب درجة العفوية
# ============================================

@check_maintenance
@check_balance(db.get_service_price('عفوية'))
async def calculate_exemption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية حساب درجة العفوية"""
    user_id = update.effective_user.id
    
    # تسجيل استخدام الخدمة
    db.add_service_usage(user_id, 'عفوية', db.get_service_price('عفوية'))
    
    await update.message.reply_text(
        format_arabic_text("""
        📊 **حساب درجة العفوية**

        أدخل درجات الكورسات الثلاثة (كل درجة بين 0-100)

        **شرط العفو:** المعدل ≥ 90

        **أرسل درجة الكورس الأول:**
        """),
        reply_markup=back_to_main_keyboard()
    )
    
    return COURSE1

async def get_course1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على درجة الكورس الأول"""
    try:
        grade1 = float(update.message.text)
        
        if 0 <= grade1 <= 100:
            context.user_data['grade1'] = grade1
            
            await update.message.reply_text(
                format_arabic_text("✅ تم حفظ درجة الكورس الأول\n\nأرسل درجة الكورس الثاني:"),
                reply_markup=back_to_main_keyboard()
            )
            return COURSE2
        else:
            await update.message.reply_text(
                format_arabic_text("⚠️ الرجاء إدخال درجة بين 0 و 100:"),
                reply_markup=back_to_main_keyboard()
            )
            return COURSE1
    except ValueError:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إدخال رقم صحيح:"),
            reply_markup=back_to_main_keyboard()
        )
        return COURSE1

async def get_course2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على درجة الكورس الثاني"""
    try:
        grade2 = float(update.message.text)
        
        if 0 <= grade2 <= 100:
            context.user_data['grade2'] = grade2
            
            await update.message.reply_text(
                format_arabic_text("✅ تم حفظ درجة الكورس الثاني\n\nأرسل درجة الكورس الثالث:"),
                reply_markup=back_to_main_keyboard()
            )
            return COURSE3
        else:
            await update.message.reply_text(
                format_arabic_text("⚠️ الرجاء إدخال درجة بين 0 و 100:"),
                reply_markup=back_to_main_keyboard()
            )
            return COURSE2
    except ValueError:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إدخال رقم صحيح:"),
            reply_markup=back_to_main_keyboard()
        )
        return COURSE2

async def get_course3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على درجة الكورس الثالث وحساب المعدل"""
    try:
        grade3 = float(update.message.text)
        
        if 0 <= grade3 <= 100:
            grade1 = context.user_data.get('grade1', 0)
            grade2 = context.user_data.get('grade2', 0)
            
            # حساب المعدل
            average = (grade1 + grade2 + grade3) / 3
            
            # التحقق من العفو
            if average >= 90:
                result = "🎉 **مبروك! أنت معفي من المادة** 🎉"
                emoji = "✅"
            else:
                result = "❌ **للأسف، أنت غير معفي من المادة**"
                emoji = "❌"
            
            result_text = f"""
            {emoji} **نتيجة حساب درجة العفوية**

            **الدرجات المدخلة:**
            • الكورس الأول: {grade1:.2f}
            • الكورس الثاني: {grade2:.2f}
            • الكورس الثالث: {grade3:.2f}

            **المعدل النهائي:** {average:.2f}

            **النتيجة:** {result}

            **ملاحظة:** الحد الأدنى للعفو هو 90
            """
            
            await update.message.reply_text(
                format_arabic_text(result_text),
                reply_markup=main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # مسح البيانات المؤقتة
            context.user_data.clear()
            
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                format_arabic_text("⚠️ الرجاء إدخال درجة بين 0 و 100:"),
                reply_markup=back_to_main_keyboard()
            )
            return COURSE3
    except ValueError:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إدخال رقم صحيح:"),
            reply_markup=back_to_main_keyboard()
        )
        return COURSE3

# ============================================
# الخدمة 2: تلخيص الملازم بالذكاء الاصطناعي
# ============================================

@check_maintenance
@check_balance(db.get_service_price('تلخيص'))
async def summarize_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية تلخيص PDF"""
    user_id = update.effective_user.id
    
    # تسجيل استخدام الخدمة
    db.add_service_usage(user_id, 'تلخيص', db.get_service_price('تلخيص'))
    
    await update.message.reply_text(
        format_arabic_text("""
        📄 **تلخيص الملازم بالذكاء الاصطناعي**

        **الخطوات:**
        1. أرسل ملف PDF المراد تلخيصه
        2. انتظر قليلاً لمعالجة الملف
        3. ستحصل على ملف PDF مخرص

        **ملاحظات:**
        • يجب أن يكون الملف بصيغة PDF
        • حجم الملف الأقصى: 20MB
        • قد تستغرق العملية بضع دقائق

        **أرسل ملف PDF الآن:**
        """),
        reply_markup=back_to_main_keyboard()
    )
    
    return WAITING_PDF

async def process_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ملف PDF"""
    if not update.message.document:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إرسال ملف PDF:"),
            reply_markup=back_to_main_keyboard()
        )
        return WAITING_PDF
    
    document = update.message.document
    
    if not document.file_name.endswith('.pdf'):
        await update.message.reply_text(
            format_arabic_text("⚠️ الملف يجب أن يكون بصيغة PDF:"),
            reply_markup=back_to_main_keyboard()
        )
        return WAITING_PDF
    
    # تحميل الملف
    await update.message.reply_text(
        format_arabic_text("📥 جاري تحميل الملف..."),
        reply_markup=back_to_main_keyboard()
    )
    
    file = await context.bot.get_file(document.file_id)
    
    # حفظ الملف مؤقتاً
    temp_file = f"temp_{update.effective_user.id}_{datetime.now().timestamp()}.pdf"
    
    try:
        await file.download_to_drive(temp_file)
        
        await update.message.reply_text(
            format_arabic_text("🔍 جاري قراءة الملف واستخراج النص..."),
            reply_markup=back_to_main_keyboard()
        )
        
        # قراءة PDF واستخراج النص
        text = ""
        with open(temp_file, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        if not text.strip():
            await update.message.reply_text(
                format_arabic_text("⚠️ لا يمكن قراءة النص من الملف. تأكد أن الملف يحتوي على نص."),
                reply_markup=back_to_main_keyboard()
            )
            os.remove(temp_file)
            return WAITING_PDF
        
        await update.message.reply_text(
            format_arabic_text("🤖 جاري تلخيص النص بالذكاء الاصطناعي..."),
            reply_markup=back_to_main_keyboard()
        )
        
        # استخدام الذكاء الاصطناعي للتلخيص
        model = setup_ai()
        if model:
            prompt = f"""
            قم بتلخيص النص التالي بأسلوب علمي أكاديمي مع التركيز على:
            1. النقاط الرئيسية
            2. التعريفات المهمة
            3. القوانين والمعادلات
            4. الاستنتاجات
            
            التلخيص يجب أن يكون باللغة العربية وبشكل منظم.
            
            النص:
            {text[:3000]}  # إرسال أول 3000 حرف فقط
            
            قدم التلخيص في نقاط واضحة ومفهومة.
            """
            
            response = model.generate_content(prompt)
            summary = response.text
            
            # إنشاء PDF مخرص
            await update.message.reply_text(
                format_arabic_text("📝 جاري إنشاء ملف PDF مخرص..."),
                reply_markup=back_to_main_keyboard()
            )
            
            summary_pdf = create_summary_pdf(summary, document.file_name)
            
            # إرسال الملف المخرص
            with open(summary_pdf, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption=format_arabic_text(f"""
                    ✅ **تم تلخيص الملف بنجاح!**

                    **الملف الأصلي:** {document.file_name}
                    **تم الإنشاء:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

                    **ملاحظة:** تم استخدام الذكاء الاصطناعي لتلخيص المحتوى
                    """),
                    reply_markup=main_menu_keyboard()
                )
            
            # حذف الملفات المؤقتة
            os.remove(temp_file)
            os.remove(summary_pdf)
            
        else:
            await update.message.reply_text(
                format_arabic_text("⚠️ حدث خطأ في خدمة الذكاء الاصطناعي. الرجاء المحاولة لاحقاً."),
                reply_markup=main_menu_keyboard()
            )
    
    except Exception as e:
        logger.error(f"خطأ في معالجة PDF: {e}")
        await update.message.reply_text(
            format_arabic_text(f"⚠️ حدث خطأ في معالجة الملف: {str(e)}"),
            reply_markup=main_menu_keyboard()
        )
        
        # حذف الملفات المؤقتة إن وجدت
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    return ConversationHandler.END

def create_summary_pdf(summary_text, original_filename):
    """إنشاء ملف PDF مخرص"""
    # إعداد اسم الملف
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"ملخص_{original_filename.replace('.pdf', '')}_{timestamp}.pdf"
    
    # إنشاء PDF
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # أنماط النص
    styles = getSampleStyleSheet()
    
    # نمط للعنوان
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='Arabic',
        fontSize=16,
        spaceAfter=30,
        alignment=1  # محاذاة وسط
    )
    
    # نمط للنص العربي
    arabic_style = ParagraphStyle(
        'ArabicText',
        parent=styles['Normal'],
        fontName='Arabic',
        fontSize=12,
        spaceAfter=12,
        alignment=0  # محاذاة يمين
    )
    
    # إعداد المحتوى
    story = []
    
    # العنوان
    title = format_arabic_text(f"ملخص: {original_filename}")
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # التاريخ
    date_text = format_arabic_text(f"تاريخ التلخيص: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    story.append(Paragraph(date_text, arabic_style))
    story.append(Spacer(1, 24))
    
    # التلخيص
    summary_paragraphs = summary_text.split('\n')
    for para in summary_paragraphs:
        if para.strip():
            formatted_para = format_arabic_text(para)
            story.append(Paragraph(formatted_para, arabic_style))
            story.append(Spacer(1, 8))
    
    # تذييل الصفحة
    story.append(Spacer(1, 50))
    footer = format_arabic_text(f"تم التلخيص بواسطة بوت {BOT_NAME} باستخدام الذكاء الاصطناعي")
    story.append(Paragraph(footer, arabic_style))
    
    # بناء PDF
    doc.build(story)
    
    return output_filename

# ============================================
# الخدمة 3: أسئلة وأجوبة بالذكاء الاصطناعي
# ============================================

@check_maintenance
@check_balance(db.get_service_price('أسئلة'))
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء خدمة الأسئلة والأجوبة"""
    user_id = update.effective_user.id
    
    # تسجيل استخدام الخدمة
    db.add_service_usage(user_id, 'أسئلة', db.get_service_price('أسئلة'))
    
    await update.message.reply_text(
        format_arabic_text("""
        ❓ **أسئلة وأجوبة بالذكاء الاصطناعي**

        يمكنك الآن:
        1. إرسال سؤال نصي عن أي مادة
        2. إرسال صورة تحتوي على سؤال
        3. الاستفسار عن أي مفهوم علمي

        **المجالات المتاحة:**
        • جميع المواد الدراسية العراقية
        • المسائل الرياضية والفيزيائية
        • التعريفات والنظريات العلمية
        • شرح المفاهيم المعقدة

        **أرسل سؤالك الآن:**
        """),
        reply_markup=back_to_main_keyboard()
    )
    
    return WAITING_ANSWER

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الإجابة على الأسئلة"""
    user_id = update.effective_user.id
    
    # التحقق من نوع المحتوى
    if update.message.text:
        question = update.message.text
        await process_text_question(update, context, question)
    
    elif update.message.photo:
        await process_image_question(update, context)
    
    else:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إرسال سؤال نصي أو صورة:"),
            reply_markup=back_to_main_keyboard()
        )
        return WAITING_ANSWER
    
    return ConversationHandler.END

async def process_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    """معالجة السؤال النصي"""
    await update.message.reply_text(
        format_arabic_text("🤖 جاري البحث عن الإجابة..."),
        reply_markup=back_to_main_keyboard()
    )
    
    try:
        model = setup_ai()
        if model:
            prompt = f"""
            أنت معلم عراقي متخصص في المناهج الدراسية العراقية.
            أجب على السؤال التالي بإجابة علمية دقيقة ومناسبة للمنهج العراقي.
            
            **توجيهات:**
            1. قدم الإجابة باللغة العربية الفصحى
            2. ركز على المنهج العراقي إن أمكن
            3. اذكر المصطلحات العلمية بالعربية والإنجليزية
            4. قدم أمثلة توضيحية إذا لزم الأمر
            5. نظم الإجابة في نقاط واضحة
            
            **السؤال:**
            {question}
            
            **ملاحظة:** كن دقيقاً علمياً ومباشراً في الإجابة.
            """
            
            response = model.generate_content(prompt)
            answer = response.text
            
            # تنسيق الإجابة
            formatted_answer = format_arabic_text(f"""
            **السؤال:** {question}

            **الإجابة:**
            {answer}

            ---
            *تمت الإجابة باستخدام الذكاء الاصطناعي المتخصص في المناهج العراقية*
            """)
            
            await update.message.reply_text(
                formatted_answer,
                reply_markup=main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            raise Exception("لا يمكن الوصول إلى خدمة الذكاء الاصطناعي")
    
    except Exception as e:
        logger.error(f"خطأ في الإجابة على السؤال: {e}")
        await update.message.reply_text(
            format_arabic_text("⚠️ حدث خطأ في معالجة سؤالك. الرجاء المحاولة لاحقاً."),
            reply_markup=main_menu_keyboard()
        )

async def process_image_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة السؤال بالصورة"""
    await update.message.reply_text(
        format_arabic_text("📷 جاري تحليل الصورة..."),
        reply_markup=back_to_main_keyboard()
    )
    
    try:
        # تحميل الصورة
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # حفظ الصورة مؤقتاً
        temp_image = f"temp_image_{update.effective_user.id}.jpg"
        await file.download_to_drive(temp_image)
        
        # استخراج النص من الصورة
        text = pytesseract.image_to_string(Image.open(temp_image), lang='ara+eng')
        
        if not text.strip():
            # إذا لم يتم التعرف على نص، اطلب من المستخدم كتابته
            await update.message.reply_text(
                format_arabic_text("""
                ⚠️ لم أستطع قراءة النص من الصورة.

                الرجاء كتابة السؤال نصياً:
                """),
                reply_markup=back_to_main_keyboard()
            )
            os.remove(temp_image)
            return WAITING_ANSWER
        
        # استخدام الذكاء الاصطناعي للإجابة
        await update.message.reply_text(
            format_arabic_text("🔍 تم قراءة السؤال، جاري البحث عن الإجابة..."),
            reply_markup=back_to_main_keyboard()
        )
        
        model = setup_ai()
        if model:
            prompt = f"""
            هذا نص تم استخراجه من صورة لسؤال تعليمي.
            أجب على السؤال التالي بإجابة علمية دقيقة.
            
            **النص المستخرج من الصورة:**
            {text}
            
            **توجيهات الإجابة:**
            1. أجب باللغة العربية الفصحى
            2. ركز على الجانب التعليمي
            3. قدم خطوات الحل إن كان سؤالاً رياضياً
            4. اشرح المفاهيم العلمية بوضوح
            """
            
            response = model.generate_content(prompt)
            answer = response.text
            
            formatted_answer = format_arabic_text(f"""
            **السؤال (من الصورة):**
            {text[:200]}...

            **الإجابة:**
            {answer}

            ---
            *تمت قراءة السؤال من الصورة والإجابة باستخدام الذكاء الاصطناعي*
            """)
            
            await update.message.reply_text(
                formatted_answer,
                reply_markup=main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # حذف الصورة المؤقتة
        os.remove(temp_image)
        
    except Exception as e:
        logger.error(f"خطأ في معالجة صورة السؤال: {e}")
        await update.message.reply_text(
            format_arabic_text("⚠️ حدث خطأ في معالجة الصورة. الرجاء المحاولة لاحقاً."),
            reply_markup=main_menu_keyboard()
        )

# ============================================
# الخدمة 4: ملازمي ومرشحاتي
# ============================================

@check_maintenance
@check_balance(db.get_service_price('ملازم'))
async def show_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المواد التعليمية"""
    user_id = update.effective_user.id
    
    # تسجيل استخدام الخدمة
    db.add_service_usage(user_id, 'ملازم', db.get_service_price('ملازم'))
    
    await update.message.reply_text(
        format_arabic_text("""
        📚 **ملازمي ومرشحاتي**

        اختر المرحلة الدراسية:
        """),
        reply_markup=stages_keyboard()
    )
    
    return

async def handle_stage_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار المرحلة"""
    stage = update.message.text
    
    # تحويل اسم المرحلة إلى كود
    stage_map = {
        "المرحلة الأولى": "first",
        "المرحلة الثانية": "second",
        "المرحلة الثالثة": "third",
        "المرحلة الرابعة": "fourth"
    }
    
    stage_code = stage_map.get(stage)
    
    if not stage_code:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء اختيار مرحلة صحيحة:"),
            reply_markup=stages_keyboard()
        )
        return
    
    # الحصول على المواد الخاصة بالمرحلة
    materials = db.get_materials(stage_code)
    
    if not materials:
        await update.message.reply_text(
            format_arabic_text(f"""
            📭 **لا توجد مواد متاحة للمرحلة {stage}**

            سيتم إضافة مواد قريباً لهذه المرحلة.

            للعودة للقائمة الرئيسية، اضغط:
            """),
            reply_markup=main_menu_keyboard()
        )
        return
    
    # عرض المواد
    materials_text = format_arabic_text(f"""
    📚 **المواد المتاحة للمرحلة {stage}:**

    """)
    
    for material in materials[:10]:  # عرض أول 10 مواد فقط
        materials_text += f"""
        • **{material['name']}**
          📝 {material['description'][:100]}...
          📅 {material['added_date'][:10]}
        """
    
    materials_text += f"\n\n**إجمالي المواد:** {len(materials)}"
    
    await update.message.reply_text(
        materials_text,
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # إرسال كل مادة كملف منفصل
    for material in materials[:5]:  # إرسال أول 5 مواد فقط لتجنب التحميل الزائد
        try:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=material['file_id'],
                caption=format_arabic_text(f"""
                **{material['name']}**
                
                {material['description']}
                
                **المرحلة:** {stage}
                **تاريخ الإضافة:** {material['added_date'][:10]}
                """)
            )
            await asyncio.sleep(1)  # تأخير بين الإرسالات
        except Exception as e:
            logger.error(f"خطأ في إرسال الملف {material['name']}: {e}")
            continue

# ============================================
# لوحة التحكم للمشرف
# ============================================

@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المشرف"""
    await update.message.reply_text(
        format_arabic_text("""
        👑 **لوحة تحكم المشرف**

        **اختر القسم المطلوب:**
        """),
        reply_markup=admin_keyboard()
    )
    
    return ADMIN_PANEL

@admin_only
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات البوت"""
    # إحصائيات المستخدمين
    users = db.get_all_users()
    total_users = len(users)
    active_today = 0
    total_balance = 0
    
    today = datetime.now().date()
    for user in users:
        total_balance += user['balance']
        join_date = datetime.strptime(user['join_date'][:10], '%Y-%m-%d').date()
        if join_date == today:
            active_today += 1
    
    # إحصائيات الخدمات
    service_stats = db.get_service_stats()
    services_text = ""
    total_income = 0
    
    for stat in service_stats:
        services_text += f"\n• {stat['service_type']}: {stat['count']} استخدام ({stat['total']} {CURRENCY})"
        total_income += stat['total']
    
    # إحصائيات المواد
    materials = db.get_materials()
    total_materials = len(materials)
    
    stats_text = f"""
    📊 **إحصائيات البوت:**

    **👥 المستخدمين:**
    • إجمالي المستخدمين: {total_users}
    • مسجلين اليوم: {active_today}
    • إجمالي الأرصدة: {total_balance} {CURRENCY}

    **💰 الإيرادات:**
    • إجمالي الدخل: {total_income} {CURRENCY}
    • الخدمات:{services_text}

    **📚 المواد التعليمية:**
    • إجمالي المواد: {total_materials}

    **⚙️ الإعدادات:**
    • وضع الصيانة: {'مفعل' if db.get_maintenance_mode() else 'معطل'}
    • مكافأة الدعوة: {db.get_invite_bonus()} {CURRENCY}
    """
    
    await update.message.reply_text(
        format_arabic_text(stats_text),
        reply_markup=admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@admin_only
async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة المستخدمين"""
    users = db.get_all_users()[:50]  # عرض أول 50 مستخدم فقط
    
    if not users:
        await update.message.reply_text(
            format_arabic_text("📭 لا يوجد مستخدمين بعد."),
            reply_markup=admin_keyboard()
        )
        return
    
    users_text = "👥 **المستخدمين (أحدث 50):**\n\n"
    
    for i, user in enumerate(users[:10], 1):  # عرض أول 10 في الرسالة الأولى
        status = "🚫 محظور" if user['banned'] else "✅ نشط"
        users_text += f"""
        **{i}. {user['first_name']} {user['last_name'] or ''}**
        • الأيدي: `{user['user_id']}`
        • اليوزر: @{user['username'] or 'بدون'}
        • الرصيد: {user['balance']} {CURRENCY}
        • الحالة: {status}
        • تاريخ التسجيل: {user['join_date'][:10]}
        """
    
    # إنشاء زرين لكل مستخدم للإدارة
    keyboard = []
    for user in users[:5]:  # إضافة أزرار لأول 5 مستخدمين
        keyboard.append([
            InlineKeyboardButton(
                f"🚫 حظر {user['user_id']}",
                callback_data=f"ban_{user['user_id']}"
            ),
            InlineKeyboardButton(
                f"💰 شحن {user['user_id']}",
                callback_data=f"charge_{user['user_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")])
    
    await update.message.reply_text(
        format_arabic_text(users_text),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@admin_only
async def charge_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية شحن رصيد مستخدم"""
    await update.message.reply_text(
        format_arabic_text("💰 **شحن رصيد مستخدم**\n\nأرسل أيدي المستخدم:"),
        reply_markup=back_to_main_keyboard()
    )
    
    return CHARGE_USER

@admin_only
async def get_user_id_for_charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على أيدي المستخدم للشحن"""
    try:
        user_id = int(update.message.text)
        user = db.get_user(user_id)
        
        if not user:
            await update.message.reply_text(
                format_arabic_text("⚠️ المستخدم غير موجود. أرسل أيدي صحيح:"),
                reply_markup=back_to_main_keyboard()
            )
            return CHARGE_USER
        
        context.user_data['charge_user_id'] = user_id
        context.user_data['charge_user_name'] = f"{user['first_name']} {user['last_name'] or ''}"
        
        await update.message.reply_text(
            format_arabic_text(f"""
            ✅ **تم العثور على المستخدم:**
            الاسم: {user['first_name']} {user['last_name'] or ''}
            الرصيد الحالي: {user['balance']} {CURRENCY}

            **أرسل المبلغ للشحن:**
            """),
            reply_markup=back_to_main_keyboard()
        )
        
        return ADD_POINTS
    
    except ValueError:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إرسال أيدي صحيح (أرقام فقط):"),
            reply_markup=back_to_main_keyboard()
        )
        return CHARGE_USER

@admin_only
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة النقاط للمستخدم"""
    try:
        amount = int(update.message.text)
        user_id = context.user_data.get('charge_user_id')
        user_name = context.user_data.get('charge_user_name')
        
        if amount <= 0:
            await update.message.reply_text(
                format_arabic_text("⚠️ المبلغ يجب أن يكون أكبر من صفر:"),
                reply_markup=back_to_main_keyboard()
            )
            return ADD_POINTS
        
        # شحن الرصيد
        db.update_balance(user_id, amount)
        db.add_transaction(user_id, amount, 'admin_charge', f'شحن بواسطة المشرف')
        
        # الحصول على الرصيد الجديد
        new_balance = db.get_balance(user_id)
        
        # إرسال إشعار للمستخدم
        try:
            await context.bot.send_message(
                user_id,
                format_arabic_text(f"""
                💰 **تم شحن رصيدك!**

                **المبلغ المضاف:** {amount} {CURRENCY}
                **الرصيد الجديد:** {new_balance} {CURRENCY}
                **بواسطة:** المشرف

                شكراً لاستخدامك بوت {BOT_NAME}!
                """)
            )
        except:
            pass
        
        await update.message.reply_text(
            format_arabic_text(f"""
            ✅ **تم الشحن بنجاح!**

            **المستخدم:** {user_name}
            **المبلغ المضاف:** {amount} {CURRENCY}
            **الرصيد الجديد:** {new_balance} {CURRENCY}

            **تم إرسال إشعار للمستخدم.**
            """),
            reply_markup=admin_keyboard()
        )
        
        # مسح البيانات المؤقتة
        context.user_data.clear()
        
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إرسال مبلغ صحيح (أرقام فقط):"),
            reply_markup=back_to_main_keyboard()
        )
        return ADD_POINTS

@admin_only
async def change_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغيير أسعار الخدمات"""
    current_prices = {
        "عفوية": db.get_service_price("عفوية"),
        "تلخيص": db.get_service_price("تلخيص"),
        "أسئلة": db.get_service_price("أسئلة"),
        "ملازم": db.get_service_price("ملازم")
    }
    
    prices_text = "💰 **الأسعار الحالية:**\n\n"
    for service, price in current_prices.items():
        prices_text += f"• {service}: {price} {CURRENCY}\n"
    
    prices_text += f"\n**أدنى سعر مسموح:** {MIN_SERVICE_PRICE} {CURRENCY}"
    prices_text += "\n\n**أرسل السعر الجديد بالصيغة:**\nاسم_الخدمة:المبلغ\nمثال: عفوية:1500"
    
    await update.message.reply_text(
        format_arabic_text(prices_text),
        reply_markup=back_to_main_keyboard()
    )
    
    return SET_PRICE

@admin_only
async def set_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعيين سعر جديد للخدمة"""
    try:
        input_text = update.message.text
        if ':' not in input_text:
            raise ValueError
        
        service_name, price_str = input_text.split(':', 1)
        service_name = service_name.strip()
        price = int(price_str.strip())
        
        # التحقق من صحة اسم الخدمة
        valid_services = ["عفوية", "تلخيص", "أسئلة", "ملازم"]
        if service_name not in valid_services:
            await update.message.reply_text(
                format_arabic_text(f"""
                ⚠️ اسم الخدمة غير صحيح!
                
                **الخدمات المتاحة:**
                {', '.join(valid_services)}
                
                أرسل بالصيغة الصحيحة:
                """),
                reply_markup=back_to_main_keyboard()
            )
            return SET_PRICE
        
        # التحقق من الحد الأدنى للسعر
        if price < MIN_SERVICE_PRICE:
            await update.message.reply_text(
                format_arabic_text(f"⚠️ السعر يجب أن يكون على الأقل {MIN_SERVICE_PRICE} {CURRENCY}:"),
                reply_markup=back_to_main_keyboard()
            )
            return SET_PRICE
        
        # تحديث السعر
        db.update_service_price(service_name, price)
        
        await update.message.reply_text(
            format_arabic_text(f"""
            ✅ **تم تحديث السعر بنجاح!**

            **الخدمة:** {service_name}
            **السعر الجديد:** {price} {CURRENCY}

            **سيتم تطبيق السعر الجديد على جميع المستخدمين.**
            """),
            reply_markup=admin_keyboard()
        )
        
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text(
            format_arabic_text("⚠️ الصيغة غير صحيحة. الرجاء استخدام:\nاسم_الخدمة:المبلغ\nمثال: عفوية:1500"),
            reply_markup=back_to_main_keyboard()
        )
        return SET_PRICE

@admin_only
async def manage_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة المواد التعليمية"""
    keyboard = [
        [
            InlineKeyboardButton("📤 إضافة مادة", callback_data="add_material"),
            InlineKeyboardButton("🗑️ حذف مادة", callback_data="delete_material")
        ],
        [
            InlineKeyboardButton("📋 عرض المواد", callback_data="view_materials"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")
        ]
    ]
    
    await update.message.reply_text(
        format_arabic_text("📚 **إدارة المواد التعليمية**\n\nاختر الإجراء المطلوب:"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@admin_only
async def add_material_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة مادة جديدة"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text=format_arabic_text("📤 **إضافة مادة جديدة**\n\nأرسل اسم المادة:"),
        reply_markup=back_to_main_keyboard()
    )
    
    return MATERIAL_NAME

@admin_only
async def get_material_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على اسم المادة"""
    context.user_data['material_name'] = update.message.text
    
    await update.message.reply_text(
        format_arabic_text("✅ تم حفظ اسم المادة.\n\nأرسل وصف المادة:"),
        reply_markup=back_to_main_keyboard()
    )
    
    return MATERIAL_DESC

@admin_only
async def get_material_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على وصف المادة"""
    context.user_data['material_desc'] = update.message.text
    
    # عرض اختيار المرحلة
    keyboard = [
        ["المرحلة الأولى", "المرحلة الثانية"],
        ["المرحلة الثالثة", "المرحلة الرابعة"],
        ["🏠 العودة للقائمة الرئيسية"]
    ]
    
    await update.message.reply_text(
        format_arabic_text("✅ تم حفظ وصف المادة.\n\nاختر المرحلة:"),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return MATERIAL_FILE

@admin_only
async def get_material_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على ملف المادة"""
    stage = update.message.text
    
    # تحويل اسم المرحلة إلى كود
    stage_map = {
        "المرحلة الأولى": "first",
        "المرحلة الثانية": "second", 
        "المرحلة الثالثة": "third",
        "المرحلة الرابعة": "fourth"
    }
    
    stage_code = stage_map.get(stage)
    
    if not stage_code:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء اختيار مرحلة صحيحة:"),
            reply_markup=back_to_main_keyboard()
        )
        return MATERIAL_FILE
    
    context.user_data['material_stage'] = stage_code
    
    await update.message.reply_text(
        format_arabic_text("✅ تم حفظ المرحلة.\n\nأرسل ملف PDF للمادة:"),
        reply_markup=back_to_main_keyboard()
    )
    
    # هنا يجب الانتقال إلى حالة انتظار الملف
    # لكن للتبسيط سنطلب من المشرف إرسال الملف في نفس الرسالة
    
    return ConversationHandler.END

@admin_only
async def handle_material_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ملف المادة"""
    if not update.message.document:
        await update.message.reply_text(
            format_arabic_text("⚠️ الرجاء إرسال ملف PDF:"),
            reply_markup=back_to_main_keyboard()
        )
        return
    
    document = update.message.document
    
    if not document.file_name.endswith('.pdf'):
        await update.message.reply_text(
            format_arabic_text("⚠️ الملف يجب أن يكون بصيغة PDF:"),
            reply_markup=back_to_main_keyboard()
        )
        return
    
    # إضافة المادة إلى قاعدة البيانات
    material_id = db.add_material(
        name=context.user_data.get('material_name'),
        description=context.user_data.get('material_desc'),
        file_id=document.file_id,
        stage=context.user_data.get('material_stage'),
        added_by=update.effective_user.id
    )
    
    if material_id:
        await update.message.reply_text(
            format_arabic_text(f"""
            ✅ **تم إضافة المادة بنجاح!**

            **الاسم:** {context.user_data.get('material_name')}
            **المرحلة:** {context.user_data.get('material_stage')}
            **رقم المادة:** {material_id}

            **سيتمكن المستخدمون من الوصول إليها فوراً.**
            """),
            reply_markup=admin_keyboard()
        )
    else:
        await update.message.reply_text(
            format_arabic_text("⚠️ حدث خطأ في إضافة المادة. الرجاء المحاولة لاحقاً."),
            reply_markup=admin_keyboard()
        )
    
    # مسح البيانات المؤقتة
    context.user_data.clear()

@admin_only
async def invite_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعدادات برنامج الدعوة"""
    current_bonus = db.get_invite_bonus()
    
    keyboard = [
        [
            InlineKeyboardButton(f"تغيير المكافأة ({current_bonus} دينار)", callback_data="change_bonus")
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")
        ]
    ]
    
    await update.message.reply_text(
        format_arabic_text(f"""
        🎁 **إعدادات برنامج الدعوة**

        **المكافأة الحالية:** {current_bonus} {CURRENCY}
        
        **اختر الإجراء المطلوب:**
        """),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return INVITE_SETTINGS

@admin_only
async def change_invite_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغيير مكافأة الدعوة"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text=format_arabic_text(f"""
        💰 **تغيير مكافأة الدعوة**
        
        المكافأة الحالية: {db.get_invite_bonus()} {CURRENCY}
        
        **أرسل المبلغ الجديد:**
        """),
        reply_markup=back_to_main_keyboard()
    )
    
    # هنا يجب الانتقال إلى حالة انتظار المبلغ الجديد
    # لكن للتبسيط سنعود للوحة التحكم

@admin_only
async def maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تفعيل/تعطيل وضع الصيانة"""
    current_mode = db.get_maintenance_mode()
    new_mode = not current_mode
    
    db.set_maintenance_mode(new_mode)
    
    status = "مفعل" if new_mode else "معطل"
    emoji = "🔧" if new_mode else "✅"
    
    await update.message.reply_text(
        format_arabic_text(f"""
        {emoji} **وضع الصيانة**
        
        **الحالة:** {status}
        
        **التأثير:**
        • المستخدمون العاديون: {"لا يمكنهم استخدام البوت" if new_mode else "يمكنهم استخدام البوت"}
        • المشرف: يمكنه استخدام البوت دائماً
        """),
        reply_markup=admin_keyboard()
    )

@admin_only
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية البث للمستخدمين"""
    await update.message.reply_text(
        format_arabic_text("""
        📢 **إرسال إشعار للمستخدمين**
        
        **أرسل الرسالة التي تريد بثها:**
        (يمكن أن تحتوي على نص، صور، أو ملفات)
        """),
        reply_markup=back_to_main_keyboard()
    )
    
    return BROADCAST

@admin_only
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال البث للمستخدمين"""
    users = db.get_all_users()
    total_users = len(users)
    successful = 0
    failed = 0
    
    # إرسال رسالة بدء البث
    progress_msg = await update.message.reply_text(
        format_arabic_text(f"📤 جاري الإرسال... 0/{total_users}")
    )
    
    for i, user in enumerate(users):
        try:
            # إعادة إرسال نفس المحتوى الذي أرسله المشرف
            if update.message.text:
                await context.bot.send_message(
                    user['user_id'],
                    format_arabic_text(f"""
                    📢 **إشعار من إدارة البوت:**
                    
                    {update.message.text}
                    
                    ---
                    *هذا إشعار عام لجميع المستخدمين*
                    """),
                    parse_mode=ParseMode.MARKDOWN
                )
            elif update.message.photo:
                await context.bot.send_photo(
                    user['user_id'],
                    update.message.photo[-1].file_id,
                    caption=format_arabic_text("📢 إشعار من إدارة البوت")
                )
            elif update.message.document:
                await context.bot.send_document(
                    user['user_id'],
                    update.message.document.file_id,
                    caption=format_arabic_text("📢 إشعار من إدارة البوت")
                )
            
            successful += 1
            
            # تحديث الرسالة كل 10 مستخدمين
            if i % 10 == 0:
                await progress_msg.edit_text(
                    format_arabic_text(f"📤 جاري الإرسال... {i+1}/{total_users}")
                )
            
            await asyncio.sleep(0.1)  # تأخير لتجنب حظر تليجرام
        
        except Exception as e:
            failed += 1
            logger.error(f"خطأ في إرسال للمستخدم {user['user_id']}: {e}")
            continue
    
    # إرسال نتيجة البث
    await progress_msg.edit_text(
        format_arabic_text(f"""
        ✅ **تم الانتهاء من البث!**
        
        **الإحصائيات:**
        • إجمالي المستخدمين: {total_users}
        • تم الإرسال بنجاح: {successful}
        • فشل الإرسال: {failed}
        • النسبة: {(successful/total_users*100):.1f}%
        
        **ملاحظة:** المستخدمون المحظورون أو الذين حذفوا المحادثة لن تصلهم الرسائل.
        """),
        reply_markup=admin_keyboard()
    )
    
    return ConversationHandler.END

# ============================================
# معالجات استدعاء الأزرار
# ============================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات الأزرار"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("ban_"):
        # حظر مستخدم
        user_id = int(data.split("_")[1])
        db.ban_user(user_id)
        
        await query.edit_message_text(
            text=format_arabic_text(f"✅ تم حظر المستخدم {user_id}"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]])
        )
    
    elif data.startswith("charge_"):
        # شحن رصيد مستخدم
        user_id = int(data.split("_")[1])
        context.user_data['charge_user_id'] = user_id
        
        await query.edit_message_text(
            text=format_arabic_text(f"💰 شحن رصيد للمستخدم {user_id}\n\nأرسل المبلغ:"),
            reply_markup=back_to_main_keyboard()
        )
        
        return ADD_POINTS
    
    elif data == "back_to_admin":
        # العودة للوحة التحكم
        await query.edit_message_text(
            text=format_arabic_text("👑 **لوحة تحكم المشرف**\n\nاختر القسم المطلوب:"),
            reply_markup=admin_keyboard()
        )
    
    elif data == "add_material":
        # إضافة مادة
        await add_material_start(update, context)
    
    elif data == "view_materials":
        # عرض المواد
        materials = db.get_materials()
        
        if not materials:
            await query.edit_message_text(
                text=format_arabic_text("📭 لا توجد مواد متاحة."),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]])
            )
            return
        
        materials_text = "📚 **المواد المتاحة:**\n\n"
        for i, material in enumerate(materials[:15], 1):
            materials_text += f"{i}. {material['name']} - {material['stage']}\n"
        
        await query.edit_message_text(
            text=format_arabic_text(materials_text),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]])
        )

# ============================================
# معالجات الرسائل العامة
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    message_text = update.message.text
    
    if message_text == "📊 حساب درجة العفوية":
        return await calculate_exemption(update, context)
    
    elif message_text == "📄 تلخيص الملازم بالذكاء الاصطناعي":
        return await summarize_pdf(update, context)
    
    elif message_text == "❓ أسئلة وأجوبة بالذكاء الاصطناعي":
        return await ask_question(update, context)
    
    elif message_text == "📚 ملازمي ومرشحاتي":
        return await show_materials(update, context)
    
    elif message_text == "💰 رصيدي":
        return await balance(update, context)
    
    elif message_text == "📤 دعوة أصدقاء":
        return await invite_info(update, context)
    
    elif message_text == "ℹ️ معلومات":
        return await info(update, context)
    
    elif message_text == "👨‍💻 الدعم الفني":
        return await support(update, context)
    
    elif message_text == "🏠 العودة للقائمة الرئيسية":
        await update.message.reply_text(
            format_arabic_text("🏠 **القائمة الرئيسية**"),
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    elif message_text == "📊 إحصائيات":
        return await show_stats(update, context)
    
    elif message_text == "👥 إدارة المستخدمين":
        return await manage_users(update, context)
    
    elif message_text == "💰 شحن رصيد":
        return await charge_user_start(update, context)
    
    elif message_text == "⚙️ تغيير الأسعار":
        return await change_prices(update, context)
    
    elif message_text == "📚 إدارة المواد":
        return await manage_materials(update, context)
    
    elif message_text == "🎁 إعدادات الدعوة":
        return await invite_settings(update, context)
    
    elif message_text == "🔧 وضع الصيانة":
        return await maintenance_mode(update, context)
    
    elif message_text == "📢 إرسال إشعار":
        return await broadcast_message(update, context)
    
    elif message_text in ["المرحلة الأولى", "المرحلة الثانية", "المرحلة الثالثة", "المرحلة الرابعة"]:
        return await handle_stage_selection(update, context)
    
    else:
        # إذا كان المستخدم مشرفاً ورسالته قد تكون رداً على عملية ما
        if update.effective_user.id == ADMIN_ID:
            # التحقق من الحالات النشطة
            if 'charge_user_id' in context.user_data:
                return await add_points(update, context)
            elif 'material_name' in context.user_data:
                if 'material_desc' not in context.user_data:
                    return await get_material_desc(update, context)
                elif 'material_stage' not in context.user_data:
                    context.user_data['material_stage'] = message_text
                    await update.message.reply_text(
                        format_arabic_text("✅ تم حفظ المرحلة.\n\nأرسل ملف PDF للمادة:"),
                        reply_markup=back_to_main_keyboard()
                    )
                    return
        
        # إذا لم تكن أي من الحالات السابقة
        await update.message.reply_text(
            format_arabic_text("""
            🤔 لم أفهم طلبك!
            
            **الرجاء استخدام الأزرار الموجودة في القائمة الرئيسية.**
            """),
            reply_markup=main_menu_keyboard()
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة الحالية"""
    await update.message.reply_text(
        format_arabic_text("تم الإلغاء. العودة للقائمة الرئيسية."),
        reply_markup=main_menu_keyboard()
    )
    
    # مسح البيانات المؤقتة
    context.user_data.clear()
    
    return ConversationHandler.END

# ============================================
# الدالة الرئيسية لتشغيل البوت
# ============================================

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    # إعداد الخطوط العربية
    setup_arabic_fonts()
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة معالج الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # محادثة حساب درجة العفوية
    calc_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 حساب درجة العفوية$"), calculate_exemption)],
        states={
            COURSE1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course1)],
            COURSE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course2)],
            COURSE3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course3)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(calc_conv_handler)
    
    # محادثة تلخيص PDF
    pdf_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📄 تلخيص الملازم بالذكاء الاصطناعي$"), summarize_pdf)],
        states={
            WAITING_PDF: [
                MessageHandler(filters.Document.PDF, process_pdf),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("⚠️ الرجاء إرسال ملف PDF:"))
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(pdf_conv_handler)
    
    # محادثة الأسئلة والأجوبة
    qa_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❓ أسئلة وأجوبة بالذكاء الاصطناعي$"), ask_question)],
        states={
            WAITING_ANSWER: [
                MessageHandler(filters.TEXT | filters.PHOTO, answer_question)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(qa_conv_handler)
    
    # محادثة شحن الرصيد من قبل المشرف
    charge_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 شحن رصيد$"), charge_user_start)],
        states={
            CHARGE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_id_for_charge)],
            ADD_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_points)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={ConversationHandler.END: ADMIN_PANEL}
    )
    application.add_handler(charge_conv_handler)
    
    # محادثة تغيير الأسعار
    price_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚙️ تغيير الأسعار$"), change_prices)],
        states={
            SET_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={ConversationHandler.END: ADMIN_PANEL}
    )
    application.add_handler(price_conv_handler)
    
    # محادثة إضافة المواد
    material_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_material_start, pattern="^add_material$")],
        states={
            MATERIAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_material_name)],
            MATERIAL_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_material_desc)],
            MATERIAL_FILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_material_file)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={ConversationHandler.END: ADMIN_PANEL}
    )
    application.add_handler(material_conv_handler)
    
    # محادثة البث للمستخدمين
    broadcast_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 إرسال إشعار$"), broadcast_message)],
        states={
            BROADCAST: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, send_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={ConversationHandler.END: ADMIN_PANEL}
    )
    application.add_handler(broadcast_conv_handler)
    
    # معالج أزرار الاستدعاء
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # معالج الرسائل العامة
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الملفات (لإضافة المواد)
    application.add_handler(MessageHandler(filters.Document.PDF, handle_material_file))
    
    # بدء البوت
    print("🚀 بدأ تشغيل البوت...")
    print(f"🤖 اسم البوت: {BOT_NAME}")
    print(f"👑 أيدي المشرف: {ADMIN_ID}")
    print(f"🔗 يوزر البوت: {BOT_USERNAME}")
    print("⏳ جاري الاستعداد...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
