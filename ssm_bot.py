#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام "يلا نتعلم" - بوت تعليمي للطلاب يعمل بالذكاء الاصطناعي
المطور: Allawi04@
ايدي المدير: 6130994941
"""

import os
import json
import logging
import asyncio
import datetime
import random
import string
import re
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# مكتبات تليجرام
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode, ChatAction

# مكتبات الذكاء الاصطناعي ومعالجة الملفات
import google.generativeai as genai
from PIL import Image
import io
import PyPDF2
import pdfkit
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import arabic_reshaper
from bidi.algorithm import get_display

# مكتبات إضافية
import requests
from uuid import uuid4
from datetime import timedelta
import sqlite3
import hashlib
import time

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== إعدادات البوت ==========
TOKEN = "8481569753:AAHTdbWwu0BHmoo_iHPsye8RkTptWzfiQWU"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
SUPPORT_USERNAME = "Allawi04@"
GEMINI_API_KEY = "AIzaSyAqlug21bw_eI60ocUtc1Z76NhEUc-zuzY"

# ========== إعدادات قاعدة البيانات ==========
DB_NAME = "yalla_nt3lem.db"

# ========== إعداد الذكاء الاصطناعي ==========
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
vision_model = genai.GenerativeModel('gemini-pro-vision')

# ========== إعداد الخطوط العربية ==========
def setup_arabic_fonts():
    """إعداد الخطوط العربية لإنشاء ملفات PDF"""
    try:
        # تحميل خط عربي (يجب تثبيت الخط مسبقاً على النظام)
        arabic_font_path = "fonts/arabic.ttf"
        if os.path.exists(arabic_font_path):
            pdfmetrics.registerFont(TTFont('Arabic', arabic_font_path))
        else:
            # استخدام خط افتراضي إذا لم يوجد الخط العربي
            pdfmetrics.registerFont(TTFont('Arabic', 'arial.ttf'))
    except:
        pass

# ========== فئات الأسعار والخدمات ==========
class Pricing:
    """فئة لإدارة أسعار الخدمات"""
    SERVICES = {
        "عفواً": 1000,  # خدمة حساب درجة العفو
        "تلخيص": 1000,  # خدمة تلخيص الملازم
        "سؤال": 1000,   # خدمة سؤال وجواب
        "ملازم": 0,     # خدمة عرض الملازم (مجانية)
    }
    
    REFERRAL_BONUS = 500  # مكافأة الإحالة
    WELCOME_BONUS = 1000  # هدية ترحيبية

# ========== فئة قاعدة البيانات ==========
class Database:
    """فئة لإدارة قاعدة البيانات"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
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
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0
            )
        ''')
        
        # جدول المعاملات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول الملازم
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                file_id TEXT,
                stage TEXT,
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
        
        # إعدادات افتراضية
        default_settings = [
            ('maintenance', 'false'),
            ('bot_channel', ''),
            ('referral_bonus', str(Pricing.REFERRAL_BONUS)),
            ('welcome_bonus', str(Pricing.WELCOME_BONUS))
        ]
        
        for key, value in default_settings:
            self.cursor.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        
        # إضافة أسعار الخدمات إلى الإعدادات
        for service, price in Pricing.SERVICES.items():
            self.cursor.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (f'price_{service}', str(price))
            )
        
        self.conn.commit()
    
    # ========== دوال المستخدمين ==========
    def add_user(self, user_id, username, first_name, last_name):
        """إضافة مستخدم جديد"""
        referral_code = self.generate_referral_code()
        self.cursor.execute(
            '''INSERT OR IGNORE INTO users 
            (user_id, username, first_name, last_name, referral_code) 
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, username, first_name, last_name, referral_code)
        )
        self.conn.commit()
        return referral_code
    
    def get_user(self, user_id):
        """الحصول على بيانات المستخدم"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = self.cursor.fetchone()
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'balance': user[4],
                'referral_code': user[5],
                'referred_by': user[6],
                'join_date': user[7],
                'is_banned': user[8],
                'is_premium': user[9],
                'total_spent': user[10]
            }
        return None
    
    def update_balance(self, user_id, amount):
        """تحديث رصيد المستخدم"""
        self.cursor.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?',
            (amount, user_id)
        )
        self.conn.commit()
    
    def add_transaction(self, user_id, amount, trans_type, description):
        """إضافة معاملة"""
        self.cursor.execute(
            '''INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)''',
            (user_id, amount, trans_type, description)
        )
        self.conn.commit()
    
    # ========== دوال الإدارة ==========
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        self.cursor.execute('SELECT * FROM users ORDER BY join_date DESC')
        return self.cursor.fetchall()
    
    def get_user_count(self):
        """عدد المستخدمين"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        return self.cursor.fetchone()[0]
    
    def get_total_balance(self):
        """إجمالي الأرصدة"""
        self.cursor.execute('SELECT SUM(balance) FROM users')
        return self.cursor.fetchone()[0] or 0
    
    def ban_user(self, user_id):
        """حظر مستخدم"""
        self.cursor.execute(
            'UPDATE users SET is_banned = 1 WHERE user_id = ?',
            (user_id,)
        )
        self.conn.commit()
    
    def unban_user(self, user_id):
        """فك حظر مستخدم"""
        self.cursor.execute(
            'UPDATE users SET is_banned = 0 WHERE user_id = ?',
            (user_id,)
        )
        self.conn.commit()
    
    # ========== دوال الإعدادات ==========
    def get_setting(self, key, default=None):
        """الحصول على إعداد"""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = self.cursor.fetchone()
        return result[0] if result else default
    
    def update_setting(self, key, value):
        """تحديث إعداد"""
        self.cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        self.conn.commit()
    
    def get_service_price(self, service):
        """الحصول على سعر الخدمة"""
        return int(self.get_setting(f'price_{service}', Pricing.SERVICES.get(service, 1000)))
    
    def update_service_price(self, service, price):
        """تحديث سعر الخدمة"""
        self.update_setting(f'price_{service}', str(price))
    
    # ========== دوال المساعدة ==========
    def generate_referral_code(self):
        """إنشاء رمز إحالة فريد"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.cursor.execute('SELECT COUNT(*) FROM users WHERE referral_code = ?', (code,))
            if self.cursor.fetchone()[0] == 0:
                return code
    
    def check_referral(self, code):
        """التحقق من صحة رمز الإحالة"""
        self.cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (code,))
        return self.cursor.fetchone()
    
    def add_referral(self, user_id, referrer_code):
        """إضافة إحالة"""
        referrer = self.check_referral(referrer_code)
        if referrer:
            referrer_id = referrer[0]
            self.cursor.execute(
                'UPDATE users SET referred_by = ? WHERE user_id = ?',
                (referrer_code, user_id)
            )
            
            # منح مكافأة للمحيل
            bonus = int(self.get_setting('referral_bonus', Pricing.REFERRAL_BONUS))
            self.update_balance(referrer_id, bonus)
            self.add_transaction(referrer_id, bonus, 'referral', f'مكافأة إحالة للمستخدم {user_id}')
            
            # منح مكافأة للمستخدم الجديد
            welcome_bonus = int(self.get_setting('welcome_bonus', Pricing.WELCOME_BONUS))
            self.update_balance(user_id, welcome_bonus)
            self.add_transaction(user_id, welcome_bonus, 'welcome', 'هدية ترحيبية')
            
            self.conn.commit()
            return True, referrer_id, bonus, welcome_bonus
        return False, None, 0, 0

# ========== تهيئة قاعدة البيانات ==========
db = Database()

# ========== فئة إدارة البوت ==========
class YallaNt3lemBot:
    """الفئة الرئيسية للبوت"""
    
    def __init__(self):
        self.user_sessions = {}  # لتخزين جلسات المستخدمين
        self.admin_commands = {}  # أوامر المدير
        
    # ========== دوال المساعدة ==========
    async def send_typing(self, update: Update):
        """إرسال مؤشر الكتابة"""
        try:
            await update.message.chat.send_action(action=ChatAction.TYPING)
        except:
            pass
    
    async def is_admin(self, user_id):
        """التحقق إذا كان المستخدم مديراً"""
        return user_id == ADMIN_ID
    
    async def check_maintenance(self):
        """التحقق من وضع الصيانة"""
        return db.get_setting('maintenance', 'false') == 'true'
    
    async def check_balance(self, user_id, service):
        """التحقق من رصيد المستخدم للخدمة"""
        price = db.get_service_price(service)
        user = db.get_user(user_id)
        return user['balance'] >= price if user else False, price
    
    async def deduct_balance(self, user_id, service, description=""):
        """خصم المبلغ من رصيد المستخدم"""
        price = db.get_service_price(service)
        db.update_balance(user_id, -price)
        db.add_transaction(user_id, -price, 'service', f'{service}: {description}')
        return price
    
    async def format_arabic_text(self, text):
        """تنسيق النص العربي للعرض في التليجرام"""
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    
    # ========== دوال القوائم الرئيسية ==========
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دالة البداية"""
        user = update.effective_user
        user_id = user.id
        
        # التحقق من وضع الصيانة
        if await self.check_maintenance() and not await self.is_admin(user_id):
            await update.message.reply_text(
                await self.format_arabic_text("⛔ البوت تحت الصيانة حالياً. الرجاء المحاولة لاحقاً.")
            )
            return
        
        # التحقق من الحظر
        user_data = db.get_user(user_id)
        if user_data and user_data['is_banned']:
            await update.message.reply_text(
                await self.format_arabic_text("⛔ حسابك محظور. الرجاء التواصل مع الدعم.")
            )
            return
        
        # إضافة المستخدم إذا كان جديداً
        if not user_data:
            referral_code = db.add_user(user_id, user.username, user.first_name, user.last_name)
            
            # التحقق من رمز الإحالة
            if context.args and len(context.args) > 0:
                ref_code = context.args[0]
                success, referrer_id, ref_bonus, welcome_bonus = db.add_referral(user_id, ref_code)
                if success:
                    try:
                        await context.bot.send_message(
                            referrer_id,
                            await self.format_arabic_text(
                                f"🎉 تمت إحالة مستخدم جديد! \n"
                                f"المستخدم: {user.first_name}\n"
                                f"المكافأة: {ref_bonus} دينار"
                            )
                        )
                    except:
                        pass
        
        # عرض القائمة الرئيسية
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض القائمة الرئيسية"""
        user_id = update.effective_user.id
        user_data = db.get_user(user_id)
        
        # تنسيق النص العربي
        welcome_text = await self.format_arabic_text(
            f"مرحباً {user_data['first_name'] if user_data else 'عزيزي'}! 👋\n"
            f"أهلاً بك في بوت 'يلا نتعلم' 🤖\n"
            f"الرصيد الحالي: {user_data['balance'] if user_data else 0} دينار عراقي 💰\n\n"
            f"اختر الخدمة التي تريدها:"
        )
        
        # إنشاء الأزرار
        keyboard = [
            [InlineKeyboardButton("📊 حساب درجة العفو", callback_data='service_excuse')],
            [InlineKeyboardButton("📝 تلخيص الملازم", callback_data='service_summary')],
            [InlineKeyboardButton("❓ سؤال وجواب", callback_data='service_qa')],
            [InlineKeyboardButton("📚 الملازم والمرشحات", callback_data='materials')],
            [InlineKeyboardButton("💰 شحن الرصيد", callback_data='charge_balance'),
             InlineKeyboardButton("👤 رصيدي", callback_data='my_balance')],
            [InlineKeyboardButton("📊 إحصائياتي", callback_data='my_stats'),
             InlineKeyboardButton("👥 دعوة أصدقاء", callback_data='invite_friends')],
            [InlineKeyboardButton("ℹ️ المساعدة", callback_data='help'),
             InlineKeyboardButton("🛠 الدعم الفني", callback_data='support')]
        ]
        
        # إضافة زر لوحة التحكم للمدير
        if await self.is_admin(user_id):
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data='admin_panel')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال الرسالة
        if update.callback_query:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    # ========== دوال الخدمات ==========
    async def handle_excuse_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة خدمة حساب درجة العفو"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # التحقق من الرصيد
        has_balance, price = await self.check_balance(user_id, "عفواً")
        if not has_balance:
            await query.edit_message_text(
                await self.format_arabic_text(
                    f"رصيدك غير كافٍ لهذه الخدمة! 💸\n"
                    f"سعر الخدمة: {price} دينار\n"
                    f"الرجاء شحن رصيدك."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 شحن الرصيد", callback_data='charge_balance')],
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        # بدء خدمة حساب العفو
        self.user_sessions[user_id] = {'service': 'excuse', 'scores': []}
        
        await query.edit_message_text(
            await self.format_arabic_text(
                f"حساب درجة العفو الفردي 📊\n"
                f"سعر الخدمة: {price} دينار\n\n"
                f"أدخل درجة الكورس الأول (0-100):"
            )
        )
    
    async def handle_excuse_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة درجات العفو"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions or self.user_sessions[user_id]['service'] != 'excuse':
            await self.show_main_menu(update, context)
            return
        
        try:
            score = float(update.message.text)
            if score < 0 or score > 100:
                raise ValueError
        except:
            await update.message.reply_text(
                await self.format_arabic_text("الرجاء إدخال درجة صحيحة بين 0 و 100:")
            )
            return
        
        session = self.user_sessions[user_id]
        session['scores'].append(score)
        
        if len(session['scores']) == 1:
            await update.message.reply_text(
                await self.format_arabic_text("أدخل درجة الكورس الثاني (0-100):")
            )
        elif len(session['scores']) == 2:
            await update.message.reply_text(
                await self.format_arabic_text("أدخل درجة الكورس الثالث (0-100):")
            )
        else:
            # حساب المعدل
            average = sum(session['scores']) / 3
            result_text = ""
            
            if average >= 90:
                result_text = await self.format_arabic_text(
                    f"🎉 مبروك! أنت معفى من المادة!\n"
                    f"المعدل النهائي: {average:.2f}\n\n"
                    f"الدرجات:\n"
                    f"الكورس الأول: {session['scores'][0]}\n"
                    f"الكورس الثاني: {session['scores'][1]}\n"
                    f"الكورس الثالث: {session['scores'][2]}"
                )
            else:
                result_text = await self.format_arabic_text(
                    f"⚠️ للأسف، أنت غير معفى من المادة.\n"
                    f"المعدل النهائي: {average:.2f}\n\n"
                    f"الدرجات:\n"
                    f"الكورس الأول: {session['scores'][0]}\n"
                    f"الكورس الثاني: {session['scores'][1]}\n"
                    f"الكورس الثالث: {session['scores'][2]}\n\n"
                    f"تحتاج إلى تحقيق معدل 90 أو أعلى للإعفاء."
                )
            
            # خصم المبلغ
            price = await self.deduct_balance(user_id, "عفواً", f"حساب درجة العفو - المعدل: {average:.2f}")
            
            # إرسال النتيجة
            await update.message.reply_text(
                result_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 العودة للقائمة", callback_data='back_to_menu')]
                ])
            )
            
            # حذف الجلسة
            del self.user_sessions[user_id]
    
    async def handle_summary_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة خدمة تلخيص الملازم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # التحقق من الرصيد
        has_balance, price = await self.check_balance(user_id, "تلخيص")
        if not has_balance:
            await query.edit_message_text(
                await self.format_arabic_text(
                    f"رصيدك غير كافٍ لهذه الخدمة! 💸\n"
                    f"سعر الخدمة: {price} دينار\n"
                    f"الرجاء شحن رصيدك."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 شحن الرصيد", callback_data='charge_balance')],
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        await query.edit_message_text(
            await self.format_arabic_text(
                f"خدمة تلخيص الملازم 📝\n"
                f"سعر الخدمة: {price} دينار\n\n"
                f"الرجاء إرسال ملف PDF المراد تلخيصه.\n\n"
                f"ملاحظة: قد يستغرق التلخيص بعض الوقت حسب حجم الملف."
            )
        )
        
        # حفظ حالة المستخدم
        self.user_sessions[user_id] = {'service': 'summary', 'waiting_for_file': True}
    
    async def handle_pdf_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ملف PDF للتلخيص"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('waiting_for_file'):
            return
        
        if not update.message.document or not update.message.document.file_name.endswith('.pdf'):
            await update.message.reply_text(
                await self.format_arabic_text("الرجاء إرسال ملف PDF صالح.")
            )
            return
        
        await self.send_typing(update)
        
        try:
            # تحميل الملف
            file = await update.message.document.get_file()
            file_bytes = await file.download_as_bytearray()
            
            # استخراج النص من PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if len(text) < 100:
                await update.message.reply_text(
                    await self.format_arabic_text("لم يتم العثور على نص كافٍ في الملف.")
                )
                return
            
            # استخدام الذكاء الاصطناعي للتلخيص
            prompt = f"""
            قم بتلخيص النص التالي بشكل احترافي مع التركيز على النقاط الرئيسية:
            
            {text[:3000]}  # إرسال جزء من النص لتجنب تجاوز الحدود
            
            قدم التلخيص باللغة العربية مع:
            1. النقاط الرئيسية
            2. الأفكار المهمة
            3. الاستنتاجات
            4. المصطلحات الأساسية
            
            اجعل التلخيص واضحاً ومنظماً ومناسباً للطلاب.
            """
            
            response = model.generate_content(prompt)
            summary = response.text
            
            # إنشاء ملف PDF جديد مع التلخيص
            pdf_buffer = await self.create_summary_pdf(summary, update.message.document.file_name)
            
            # خصم المبلغ
            price = await self.deduct_balance(user_id, "تلخيص", f"تلخيص ملف: {update.message.document.file_name}")
            
            # إرسال الملف
            await update.message.reply_document(
                document=pdf_buffer,
                filename=f"ملخص_{update.message.document.file_name}",
                caption=await self.format_arabic_text(
                    f"✅ تم تلخيص الملف بنجاح!\n"
                    f"تم خصم: {price} دينار\n"
                    f"رصيدك المتبقي: {db.get_user(user_id)['balance']} دينار"
                )
            )
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            await update.message.reply_text(
                await self.format_arabic_text("حدث خطأ أثناء معالجة الملف. الرجاء المحاولة مرة أخرى.")
            )
        
        # تنظيف الجلسة
        del self.user_sessions[user_id]
        await self.show_main_menu(update, context)
    
    async def create_summary_pdf(self, summary_text, original_filename):
        """إنشاء ملف PDF للتلخيص"""
        buffer = io.BytesIO()
        
        # إعداد الخطوط
        setup_arabic_fonts()
        
        # إنشاء مستند PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # الأنماط
        styles = getSampleStyleSheet()
        arabic_style = ParagraphStyle(
            'ArabicStyle',
            parent=styles['Normal'],
            fontName='Arabic',
            fontSize=12,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontName='Arabic',
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=24
        )
        
        # المحتوى
        content = []
        
        # العنوان
        title = Paragraph(await self.format_arabic_text(f"ملخص: {original_filename}"), title_style)
        content.append(title)
        content.append(Spacer(1, 12))
        
        # التاريخ
        date_text = Paragraph(
            await self.format_arabic_text(f"تاريخ التلخيص: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"),
            arabic_style
        )
        content.append(date_text)
        content.append(Spacer(1, 24))
        
        # التلخيص
        summary_paragraphs = summary_text.split('\n')
        for para in summary_paragraphs:
            if para.strip():
                content.append(Paragraph(await self.format_arabic_text(para.strip()), arabic_style))
                content.append(Spacer(1, 8))
        
        # إنشاء PDF
        doc.build(content)
        
        buffer.seek(0)
        return buffer
    
    async def handle_qa_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة خدمة سؤال وجواب"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # التحقق من الرصيد
        has_balance, price = await self.check_balance(user_id, "سؤال")
        if not has_balance:
            await query.edit_message_text(
                await self.format_arabic_text(
                    f"رصيدك غير كافٍ لهذه الخدمة! 💸\n"
                    f"سعر الخدمة: {price} دينار\n"
                    f"الرجاء شحن رصيدك."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 شحن الرصيد", callback_data='charge_balance')],
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        await query.edit_message_text(
            await self.format_arabic_text(
                f"خدمة سؤال وجواب ❓\n"
                f"سعر الخدمة: {price} دينار\n\n"
                f"يمكنك الآن:\n"
                f"1. إرسال سؤال نصي\n"
                f"2. إرسال صورة تحتوي على سؤال\n\n"
                f"سأجيبك بإجابة علمية حسب المنهج العراقي."
            )
        )
        
        # حفظ حالة المستخدم
        self.user_sessions[user_id] = {'service': 'qa', 'waiting_for_question': True}
    
    async def handle_qa_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة سؤال وجواب"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('waiting_for_question'):
            return
        
        await self.send_typing(update)
        
        try:
            question = ""
            
            # معالجة النص
            if update.message.text:
                question = update.message.text
            # معالجة الصور
            elif update.message.photo:
                # تحميل الصورة
                photo = update.message.photo[-1]
                file = await photo.get_file()
                image_bytes = await file.download_as_bytearray()
                
                # استخدام نموذج الرؤية
                image = Image.open(io.BytesIO(image_bytes))
                response = vision_model.generate_content(["ما هو السؤال أو النص في هذه الصورة؟ أجب باللغة العربية", image])
                question = response.text
            
            if not question:
                await update.message.reply_text(
                    await self.format_arabic_text("لم أتمكن من فهم السؤال. الرجاء إعادة المحاولة.")
                )
                return
            
            # استخدام الذكاء الاصطناعي للإجابة
            prompt = f"""
            أجب على السؤال التالي بشكل علمي ومناسب للمنهج العراقي:
            
            السؤال: {question}
            
            المتطلبات:
            1. الرد باللغة العربية الفصحى
            2. الإجابة العلمية الدقيقة
            3. التنسيق المناسب للطلاب
            4. الإشارة للمنهج العراقي إذا لزم الأمر
            5. تقسيم الإجابة إذا كانت طويلة
            
            قدم الإجابة بشكل واضح ومنظم.
            """
            
            response = model.generate_content(prompt)
            answer = response.text
            
            # خصم المبلغ
            price = await self.deduct_balance(user_id, "سؤال", f"سؤال وجواب: {question[:50]}...")
            
            # إرسال الإجابة
            await update.message.reply_text(
                await self.format_arabic_text(
                    f"🧠 الإجابة:\n\n{answer}\n\n"
                    f"💸 تم خصم: {price} دينار\n"
                    f"💰 رصيدك المتبقي: {db.get_user(user_id)['balance']} دينار"
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 العودة للقائمة", callback_data='back_to_menu')]
                ])
            )
            
        except Exception as e:
            logger.error(f"Error in QA service: {e}")
            await update.message.reply_text(
                await self.format_arabic_text("حدث خطأ أثناء معالجة سؤالك. الرجاء المحاولة مرة أخرى.")
            )
        
        # تنظيف الجلسة
        del self.user_sessions[user_id]
    
    # ========== دوال الملازم ==========
    async def show_materials(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الملازم والمرشحات"""
        query = update.callback_query
        await query.answer()
        
        # جلب الملازم من قاعدة البيانات
        db.cursor.execute('SELECT * FROM materials ORDER BY stage, name')
        materials = db.cursor.fetchall()
        
        if not materials:
            await query.edit_message_text(
                await self.format_arabic_text("لا توجد ملازم متاحة حالياً."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        # تجميع الملازم حسب المرحلة
        materials_by_stage = {}
        for material in materials:
            stage = material[4]  # عمود المرحلة
            if stage not in materials_by_stage:
                materials_by_stage[stage] = []
            materials_by_stage[stage].append(material)
        
        # إنشاء القوائم
        keyboard = []
        for stage, mats in materials_by_stage.items():
            keyboard.append([InlineKeyboardButton(f"📂 {stage}", callback_data=f'stage_{stage}')])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            await self.format_arabic_text("اختر المرحلة:"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_stage_materials(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض ملازم مرحلة معينة"""
        query = update.callback_query
        await query.answer()
        
        stage = query.data.replace('stage_', '')
        
        db.cursor.execute('SELECT * FROM materials WHERE stage = ? ORDER BY name', (stage,))
        materials = db.cursor.fetchall()
        
        if not materials:
            await query.edit_message_text(
                await self.format_arabic_text(f"لا توجد ملازم للمرحلة {stage}."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='materials')]
                ])
            )
            return
        
        keyboard = []
        for material in materials:
            name = material[1]
            desc = material[2]
            file_id = material[3]
            btn_text = f"{name}"
            if desc:
                btn_text += f" - {desc[:20]}..."
            
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f'mat_{material[0]}')])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='materials')])
        
        await query.edit_message_text(
            await self.format_arabic_text(f"ملازم المرحلة: {stage}\nاختر المادة:"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def send_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إرسال مادة معينة"""
        query = update.callback_query
        await query.answer()
        
        mat_id = int(query.data.replace('mat_', ''))
        
        db.cursor.execute('SELECT * FROM materials WHERE id = ?', (mat_id,))
        material = db.cursor.fetchone()
        
        if not material:
            await query.edit_message_text(
                await self.format_arabic_text("المادة غير موجودة."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='materials')]
                ])
            )
            return
        
        name, desc, file_id, stage = material[1], material[2], material[3], material[4]
        
        caption = await self.format_arabic_text(
            f"📚 {name}\n"
            f"📖 {desc}\n"
            f"🏫 المرحلة: {stage}"
        )
        
        try:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=file_id,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data=f'stage_{stage}')]
                ])
            )
        except:
            await query.edit_message_text(
                await self.format_arabic_text("عذراً، حدث خطأ في إرسال الملف."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='materials')]
                ])
            )
    
    # ========== دوال الرصيد والإحالة ==========
    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض رصيد المستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            await query.edit_message_text(
                await self.format_arabic_text("لم يتم العثور على حسابك."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        # جلب آخر المعاملات
        db.cursor.execute(
            'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5',
            (user_id,)
        )
        transactions = db.cursor.fetchall()
        
        trans_text = ""
        for trans in transactions:
            amount = trans[2]
            trans_type = trans[3]
            desc = trans[4]
            date = trans[5]
            
            sign = "+" if amount > 0 else "-"
            trans_text += f"{sign} {abs(amount)} دينار - {desc} ({date[:10]})\n"
        
        balance_text = await self.format_arabic_text(
            f"💰 رصيدك الحالي: {user_data['balance']} دينار عراقي\n\n"
            f"📊 آخر المعاملات:\n{trans_text if trans_text else 'لا توجد معاملات سابقة'}\n"
            f"📅 تاريخ الانضمام: {user_data['join_date'][:10]}"
        )
        
        await query.edit_message_text(
            balance_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 شحن الرصيد", callback_data='charge_balance')],
                [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data='invite_friends')],
                [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
            ])
        )
    
    async def show_charge_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض خيارات شحن الرصيد"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        charge_text = await self.format_arabic_text(
            f"💰 شحن الرصيد\n\n"
            f"رصيدك الحالي: {user_data['balance']} دينار\n\n"
            f"طرق الشحن:\n"
            f"1. التواصل مع الدعم الفني: {SUPPORT_USERNAME}\n"
            f"2. دعوة الأصدقاء (مكافأة: {db.get_setting('referral_bonus', Pricing.REFERRAL_BONUS)} دينار لكل صديق)\n\n"
            f"لشحن الرصيد، قم بالتواصل مع الدعم وأرسل إيديك:\n"
            f"`{user_id}`"
        )
        
        await query.edit_message_text(
            charge_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data='invite_friends')],
                [InlineKeyboardButton("🛠 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
            ])
        )
    
    async def show_invite_friends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض رابط الدعوة"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data or not user_data['referral_code']:
            await query.edit_message_text(
                await self.format_arabic_text("حدث خطأ في إنشاء رابط الدعوة."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        invite_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_data['referral_code']}"
        bonus = db.get_setting('referral_bonus', Pricing.REFERRAL_BONUS)
        
        invite_text = await self.format_arabic_text(
            f"👥 دعوة الأصدقاء\n\n"
            f"📊 المكافأة: {bonus} دينار لكل صديق\n"
            f"💰 رصيدك الحالي: {user_data['balance']} دينار\n\n"
            f"🔗 رابط الدعوة:\n"
            f"`{invite_link}`\n\n"
            f"📝 كيفية الاستخدام:\n"
            f"1. أرسل الرابط لصديقك\n"
            f"2. عندما ينضم صديقك عبر الرابط\n"
            f"3. تحصل على {bonus} دينار تلقائياً\n\n"
            f"🎁 صديقك يحصل على {db.get_setting('welcome_bonus', Pricing.WELCOME_BONUS)} دينار هدية ترحيبية!"
        )
        
        await query.edit_message_text(
            invite_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={invite_link}&text=انضم%20إلى%20بوت%20يلا%20نتعلم%20للطلاب!")],
                [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
            ])
        )
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات المستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            await query.edit_message_text(
                await self.format_arabic_text("لم يتم العثور على حسابك."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
                ])
            )
            return
        
        # حساب عدد الإحالات
        db.cursor.execute(
            'SELECT COUNT(*) FROM users WHERE referred_by = ?',
            (user_data['referral_code'],)
        )
        referral_count = db.cursor.fetchone()[0]
        
        # حساب إجمالي الإنفاق
        total_spent = user_data['total_spent']
        
        stats_text = await self.format_arabic_text(
            f"📊 إحصائياتك\n\n"
            f"👤 الاسم: {user_data['first_name']} {user_data['last_name'] or ''}\n"
            f"🆔 المعرف: {user_data['user_id']}\n"
            f"💰 الرصيد: {user_data['balance']} دينار\n"
            f"💸 إجمالي الإنفاق: {total_spent} دينار\n"
            f"👥 عدد الإحالات: {referral_count}\n"
            f"📅 تاريخ الانضمام: {user_data['join_date'][:10]}\n"
            f"🔗 كود الإحالة: {user_data['referral_code']}"
        )
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data='invite_friends')],
                [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
            ])
        )
    
    # ========== دوال الدعم والمساعدة ==========
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات المساعدة"""
        query = update.callback_query
        await query.answer()
        
        help_text = await self.format_arabic_text(
            f"ℹ️ مساعدة واستفسارات\n\n"
            f"📚 كيفية استخدام البوت:\n"
            f"1. اختر الخدمة المطلوبة من القائمة\n"
            f"2. اتبع التعليمات الظاهرة\n"
            f"3. ستحتاج إلى رصيد كافٍ للخدمات المدفوعة\n\n"
            f"💰 خدمات البوت:\n"
            f"• حساب درجة العفو: حساب المعدل للإعفاء\n"
            f"• تلخيص الملازم: تلخيص ملفات PDF باستخدام الذكاء الاصطناعي\n"
            f"• سؤال وجواب: الإجابة على الأسئلة العلمية\n"
            f"• الملازم والمرشحات: مواد دراسية مجانية\n\n"
            f"💸 أسعار الخدمات:\n"
            f"• حساب درجة العفو: {db.get_service_price('عفواً')} دينار\n"
            f"• تلخيص الملازم: {db.get_service_price('تلخيص')} دينار\n"
            f"• سؤال وجواب: {db.get_service_price('سؤال')} دينار\n\n"
            f"🛠 للدعم الفني: {SUPPORT_USERNAME}"
        )
        
        await query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
            ])
        )
    
    async def show_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات الدعم"""
        query = update.callback_query
        await query.answer()
        
        bot_channel = db.get_setting('bot_channel', '')
        channel_text = f"\n📢 قناة البوت: {bot_channel}" if bot_channel else ""
        
        support_text = await self.format_arabic_text(
            f"🛠 الدعم الفني\n\n"
            f"للشحن أو الاستفسارات أو المشاكل الفنية:\n"
            f"👤 الدعم: {SUPPORT_USERNAME}\n"
            f"{channel_text}\n\n"
            f"⏰ وقت الاستجابة:\n"
            f"• أيام الأسبوع: 9 صباحاً - 10 مساءً\n"
            f"• الجمعة: 2 ظهراً - 10 مساءً\n\n"
            f"💡 نصائح:\n"
            f"• تأكد من إرسال إيديك عند التواصل\n"
            f"• اشرح مشكلتك بوضوح\n"
            f"• أرفق صوراً إذا لزم الأمر"
        )
        
        keyboard = []
        if bot_channel:
            keyboard.append([InlineKeyboardButton("📢 قناة البوت", url=bot_channel)])
        keyboard.append([InlineKeyboardButton("👤 التواصل مع الدعم", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            support_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ========== دوال لوحة التحكم (للمدير فقط) ==========
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض لوحة التحكم للمدير"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            await query.answer("⛔ غير مصرح لك بالدخول!", show_alert=True)
            return
        
        await query.answer()
        
        # إحصائيات البوت
        total_users = db.get_user_count()
        total_balance = db.get_total_balance()
        maintenance_mode = db.get_setting('maintenance', 'false') == 'true'
        
        admin_text = await self.format_arabic_text(
            f"👑 لوحة التحكم\n\n"
            f"📊 إحصائيات البوت:\n"
            f"• إجمالي المستخدمين: {total_users}\n"
            f"• إجمالي الأرصدة: {total_balance} دينار\n"
            f"• وضع الصيانة: {'✅ مفعل' if maintenance_mode else '❌ غير مفعل'}\n\n"
            f"اختر القسم المطلوب:"
        )
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data='admin_users')],
            [InlineKeyboardButton("💰 إدارة الشحن", callback_data='admin_charge')],
            [InlineKeyboardButton("⚙️ إدارة الخدمات", callback_data='admin_services')],
            [InlineKeyboardButton("📚 إدارة الملازم", callback_data='admin_materials')],
            [InlineKeyboardButton("🔧 إعدادات البوت", callback_data='admin_settings')],
            [InlineKeyboardButton("📊 إحصائيات مفصلة", callback_data='admin_stats')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
        ]
        
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_manage_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة المستخدمين"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        admin_text = await self.format_arabic_text(
            f"👥 إدارة المستخدمين\n\n"
            f"اختر الإجراء المطلوب:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data='admin_list_users')],
            [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data='admin_search_user')],
            [InlineKeyboardButton("⛔ حظر مستخدم", callback_data='admin_ban_user')],
            [InlineKeyboardButton("✅ فك حظر مستخدم", callback_data='admin_unban_user')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض جميع المستخدمين"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        users = db.get_all_users()
        
        if not users:
            await query.edit_message_text(
                await self.format_arabic_text("لا يوجد مستخدمين بعد."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='admin_users')]
                ])
            )
            return
        
        # عرض أول 10 مستخدمين
        users_text = await self.format_arabic_text("📋 آخر 10 مستخدمين:\n\n")
        
        for i, user in enumerate(users[:10]):
            users_text += await self.format_arabic_text(
                f"{i+1}. {user[2]} {user[3] or ''} (@{user[1] or 'بدون'})\n"
                f"   🆔: {user[0]} | 💰: {user[4]} دينار\n"
                f"   📅: {user[7][:10]} | {'⛔ محظور' if user[8] else '✅ نشط'}\n\n"
            )
        
        keyboard = []
        if len(users) > 10:
            keyboard.append([InlineKeyboardButton("📄 الصفحة التالية", callback_data='admin_users_page_2')])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_users')])
        
        await query.edit_message_text(
            users_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_charge_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة الشحن"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        admin_text = await self.format_arabic_text(
            f"💰 إدارة الشحن\n\n"
            f"اختر الإجراء المطلوب:"
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ شحن رصيد مستخدم", callback_data='admin_add_balance')],
            [InlineKeyboardButton("➖ خصم رصيد مستخدم", callback_data='admin_deduct_balance')],
            [InlineKeyboardButton("💰 تغيير مكافأة الإحالة", callback_data='admin_change_referral_bonus')],
            [InlineKeyboardButton("🎁 تغيير الهدية الترحيبية", callback_data='admin_change_welcome_bonus')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_add_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شحن رصيد مستخدم"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        self.admin_commands[user_id] = 'add_balance_user'
        
        await query.edit_message_text(
            await self.format_arabic_text(
                "➕ شحن رصيد مستخدم\n\n"
                "أرسل إيدي المستخدم المراد شحن رصيده:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data='admin_charge')]
            ])
        )
    
    async def admin_handle_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة شحن الرصيد"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_commands:
            return
        
        command = self.admin_commands[user_id]
        
        if command == 'add_balance_user':
            try:
                target_user_id = int(update.message.text)
                self.admin_commands[user_id] = {'action': 'add_balance_amount', 'target': target_user_id}
                
                await update.message.reply_text(
                    await self.format_arabic_text("أرسل المبلغ المراد إضافته:")
                )
            except:
                await update.message.reply_text(
                    await self.format_arabic_text("إيدي غير صحيح. الرجاء المحاولة مرة أخرى.")
                )
        
        elif isinstance(command, dict) and command.get('action') == 'add_balance_amount':
            try:
                amount = int(update.message.text)
                target_user_id = command['target']
                
                # تحديث الرصيد
                db.update_balance(target_user_id, amount)
                db.add_transaction(target_user_id, amount, 'admin_charge', 'شحن من المدير')
                
                # إرسال إشعار للمستخدم
                try:
                    await context.bot.send_message(
                        target_user_id,
                        await self.format_arabic_text(
                            f"🎉 تم شحن رصيدك!\n"
                            f"المبلغ: {amount} دينار\n"
                            f"الرصيد الجديد: {db.get_user(target_user_id)['balance']} دينار"
                        )
                    )
                except:
                    pass
                
                await update.message.reply_text(
                    await self.format_arabic_text(
                        f"✅ تم شحن {amount} دينار للمستخدم {target_user_id}\n"
                        f"الرصيد الجديد: {db.get_user(target_user_id)['balance']} دينار"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                    ])
                )
                
                # تنظيف الأمر
                del self.admin_commands[user_id]
                
            except:
                await update.message.reply_text(
                    await self.format_arabic_text("مبلغ غير صحيح. الرجاء المحاولة مرة أخرى.")
                )
    
    async def admin_manage_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة الخدمات"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        # جلب أسعار الخدمات الحالية
        services_prices = ""
        for service in ['عفواً', 'تلخيص', 'سؤال']:
            price = db.get_service_price(service)
            services_prices += f"• {service}: {price} دينار\n"
        
        admin_text = await self.format_arabic_text(
            f"⚙️ إدارة الخدمات\n\n"
            f"الأسعار الحالية:\n{services_prices}\n"
            f"اختر الإجراء المطلوب:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 تغيير سعر حساب العفو", callback_data='admin_change_price_excuse')],
            [InlineKeyboardButton("🔄 تغيير سعر تلخيص الملازم", callback_data='admin_change_price_summary')],
            [InlineKeyboardButton("🔄 تغيير سعر سؤال وجواب", callback_data='admin_change_price_qa')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_change_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغيير سعر خدمة"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        service_map = {
            'admin_change_price_excuse': 'عفواً',
            'admin_change_price_summary': 'تلخيص',
            'admin_change_price_qa': 'سؤال'
        }
        
        service_name = service_map.get(query.data)
        if not service_name:
            return
        
        self.admin_commands[user_id] = {'action': 'change_price', 'service': service_name}
        
        current_price = db.get_service_price(service_name)
        
        await query.edit_message_text(
            await self.format_arabic_text(
                f"🔄 تغيير سعر خدمة: {service_name}\n"
                f"السعر الحالي: {current_price} دينار\n\n"
                f"أرسل السعر الجديد (دينار عراقي):"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data='admin_services')]
            ])
        )
    
    async def admin_handle_price_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تغيير السعر"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_commands:
            return
        
        command = self.admin_commands[user_id]
        
        if isinstance(command, dict) and command.get('action') == 'change_price':
            try:
                new_price = int(update.message.text)
                service_name = command['service']
                
                if new_price < 0:
                    await update.message.reply_text(
                        await self.format_arabic_text("السعر يجب أن يكون عدداً صحيحاً موجباً.")
                    )
                    return
                
                # تحديث السعر
                db.update_service_price(service_name, new_price)
                
                await update.message.reply_text(
                    await self.format_arabic_text(
                        f"✅ تم تغيير سعر خدمة '{service_name}' إلى {new_price} دينار"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                    ])
                )
                
                # تنظيف الأمر
                del self.admin_commands[user_id]
                
            except:
                await update.message.reply_text(
                    await self.format_arabic_text("سعر غير صحيح. الرجاء المحاولة مرة أخرى.")
                )
    
    async def admin_manage_materials(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة الملازم"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        admin_text = await self.format_arabic_text(
            f"📚 إدارة الملازم\n\n"
            f"اختر الإجراء المطلوب:"
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مادة جديدة", callback_data='admin_add_material')],
            [InlineKeyboardButton("🗑 حذف مادة", callback_data='admin_delete_material')],
            [InlineKeyboardButton("📋 عرض جميع المواد", callback_data='admin_list_materials')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_add_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إضافة مادة جديدة"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        self.admin_commands[user_id] = 'add_material_name'
        
        await query.edit_message_text(
            await self.format_arabic_text(
                "➕ إضافة مادة جديدة\n\n"
                "أرسل اسم المادة:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data='admin_materials')]
            ])
        )
    
    async def admin_handle_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إضافة مادة"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_commands:
            return
        
        command = self.admin_commands[user_id]
        
        if command == 'add_material_name':
            self.admin_commands[user_id] = {
                'action': 'add_material_desc',
                'name': update.message.text
            }
            
            await update.message.reply_text(
                await self.format_arabic_text("أرسل وصف المادة:")
            )
        
        elif isinstance(command, dict) and command.get('action') == 'add_material_desc':
            self.admin_commands[user_id] = {
                'action': 'add_material_stage',
                'name': command['name'],
                'desc': update.message.text
            }
            
            await update.message.reply_text(
                await self.format_arabic_text("أرسل المرحلة الدراسية (مثال: الصف السادس, المرحلة الإعدادية):")
            )
        
        elif isinstance(command, dict) and command.get('action') == 'add_material_stage':
            self.admin_commands[user_id] = {
                'action': 'add_material_file',
                'name': command['name'],
                'desc': command['desc'],
                'stage': update.message.text
            }
            
            await update.message.reply_text(
                await self.format_arabic_text("أرسل ملف PDF الخاص بالمادة:")
            )
        
        elif isinstance(command, dict) and command.get('action') == 'add_material_file':
            if not update.message.document or not update.message.document.file_name.endswith('.pdf'):
                await update.message.reply_text(
                    await self.format_arabic_text("الرجاء إرسال ملف PDF صالح.")
                )
                return
            
            try:
                # حفظ الملف في قاعدة البيانات
                file_id = update.message.document.file_id
                
                db.cursor.execute(
                    'INSERT INTO materials (name, description, file_id, stage) VALUES (?, ?, ?, ?)',
                    (command['name'], command['desc'], file_id, command['stage'])
                )
                db.conn.commit()
                
                await update.message.reply_text(
                    await self.format_arabic_text(
                        f"✅ تمت إضافة المادة بنجاح!\n"
                        f"الاسم: {command['name']}\n"
                        f"المرحلة: {command['stage']}"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                    ])
                )
                
                # تنظيف الأمر
                del self.admin_commands[user_id]
                
            except Exception as e:
                logger.error(f"Error adding material: {e}")
                await update.message.reply_text(
                    await self.format_arabic_text("حدث خطأ أثناء إضافة المادة. الرجاء المحاولة مرة أخرى.")
                )
    
    async def admin_manage_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إعدادات البوت"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        maintenance = db.get_setting('maintenance', 'false') == 'true'
        bot_channel = db.get_setting('bot_channel', '')
        
        admin_text = await self.format_arabic_text(
            f"🔧 إعدادات البوت\n\n"
            f"الإعدادات الحالية:\n"
            f"• وضع الصيانة: {'✅ مفعل' if maintenance else '❌ غير مفعل'}\n"
            f"• قناة البوت: {bot_channel if bot_channel else 'غير مضبوطة'}\n\n"
            f"اختر الإجراء المطلوب:"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"{'❌ تعطيل' if maintenance else '✅ تفعيل'} وضع الصيانة", 
             callback_data='admin_toggle_maintenance')],
            [InlineKeyboardButton("📢 تغيير قناة البوت", callback_data='admin_change_channel')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_toggle_maintenance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تفعيل/تعطيل وضع الصيانة"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        current = db.get_setting('maintenance', 'false')
        new_value = 'false' if current == 'true' else 'true'
        
        db.update_setting('maintenance', new_value)
        
        status = "✅ تم تفعيل وضع الصيانة" if new_value == 'true' else "❌ تم تعطيل وضع الصيانة"
        
        await query.edit_message_text(
            await self.format_arabic_text(status),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إعدادات البوت", callback_data='admin_settings')]
            ])
        )
    
    async def admin_change_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغيير قناة البوت"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        self.admin_commands[user_id] = 'change_channel'
        
        current_channel = db.get_setting('bot_channel', '')
        
        await query.edit_message_text(
            await self.format_arabic_text(
                f"📢 تغيير قناة البوت\n\n"
                f"القناة الحالية: {current_channel if current_channel else 'غير مضبوطة'}\n\n"
                f"أرسل رابط القناة الجديدة (أو 'إلغاء' للعودة):"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data='admin_settings')]
            ])
        )
    
    async def admin_handle_channel_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تغيير القناة"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_commands or self.admin_commands[user_id] != 'change_channel':
            return
        
        new_channel = update.message.text
        
        if new_channel.lower() == 'إلغاء':
            del self.admin_commands[user_id]
            await self.show_admin_panel(update, context)
            return
        
        db.update_setting('bot_channel', new_channel)
        
        await update.message.reply_text(
            await self.format_arabic_text(f"✅ تم تحديث قناة البوت إلى: {new_channel}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
            ])
        )
        
        del self.admin_commands[user_id]
    
    async def admin_show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات مفصلة"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not await self.is_admin(user_id):
            return
        
        await query.answer()
        
        # إحصائيات متقدمة
        total_users = db.get_user_count()
        total_balance = db.get_total_balance()
        
        # عدد المستخدمين النشطين (انضموا خلال آخر 7 أيام)
        db.cursor.execute(
            'SELECT COUNT(*) FROM users WHERE date(join_date) >= date("now", "-7 days")'
        )
        active_users = db.cursor.fetchone()[0]
        
        # إجمالي المعاملات
        db.cursor.execute('SELECT SUM(amount) FROM transactions WHERE amount < 0')
        total_spent = abs(db.cursor.fetchone()[0] or 0)
        
        # عدد الإحالات
        db.cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL')
        total_referrals = db.cursor.fetchone()[0]
        
        stats_text = await self.format_arabic_text(
            f"📊 إحصائيات مفصلة\n\n"
            f"👥 المستخدمين:\n"
            f"• إجمالي المستخدمين: {total_users}\n"
            f"• مستخدمين نشطين (7 أيام): {active_users}\n"
            f"• إجمالي الإحالات: {total_referrals}\n\n"
            f"💰 الأموال:\n"
            f"• إجمالي الأرصدة: {total_balance} دينار\n"
            f"• إجمالي الإنفاق: {total_spent} دينار\n\n"
            f"📈 النشاط:\n"
        )
        
        # إحصائيات الخدمات
        for service in ['عفواً', 'تلخيص', 'سؤال']:
            db.cursor.execute(
                'SELECT COUNT(*) FROM transactions WHERE description LIKE ? AND amount < 0',
                (f'{service}%',)
            )
            count = db.cursor.fetchone()[0]
            price = db.get_service_price(service)
            total = count * price
            stats_text += await self.format_arabic_text(f"• {service}: {count} مرة ({total} دينار)\n")
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
            ])
        )
    
    # ========== دوال معالجة الرسائل العامة ==========
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية العامة"""
        user_id = update.effective_user.id
        
        # التحقق من وضع الصيانة
        if await self.check_maintenance() and not await self.is_admin(user_id):
            await update.message.reply_text(
                await self.format_arabic_text("⛔ البوت تحت الصيانة حالياً. الرجاء المحاولة لاحقاً.")
            )
            return
        
        # التحقق من الحظر
        user_data = db.get_user(user_id)
        if user_data and user_data['is_banned']:
            await update.message.reply_text(
                await self.format_arabic_text("⛔ حسابك محظور. الرجاء التواصل مع الدعم.")
            )
            return
        
        # التحقق من الأوامر الإدارية
        if user_id in self.admin_commands:
            if self.admin_commands[user_id] == 'change_channel':
                await self.admin_handle_channel_change(update, context)
                return
            elif isinstance(self.admin_commands[user_id], dict) or self.admin_commands[user_id] in ['add_balance_user', 'add_material_name']:
                await self.admin_handle_balance(update, context)
                return
        
        # التحقق من جلسات الخدمات
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            
            if session['service'] == 'excuse':
                await self.handle_excuse_score(update, context)
                return
            elif session['service'] == 'qa' and session.get('waiting_for_question'):
                await self.handle_qa_question(update, context)
                return
        
        # إذا لم تكن رسالة خاصة، عرض القائمة الرئيسية
        await self.show_main_menu(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الضغطات على الأزرار"""
        query = update.callback_query
        callback_data = query.data
        
        # معالجة الأزرار الرئيسية
        if callback_data == 'back_to_menu':
            await self.show_main_menu(update, context)
        
        # الخدمات
        elif callback_data == 'service_excuse':
            await self.handle_excuse_service(update, context)
        elif callback_data == 'service_summary':
            await self.handle_summary_service(update, context)
        elif callback_data == 'service_qa':
            await self.handle_qa_service(update, context)
        
        # الملازم
        elif callback_data == 'materials':
            await self.show_materials(update, context)
        elif callback_data.startswith('stage_'):
            await self.show_stage_materials(update, context)
        elif callback_data.startswith('mat_'):
            await self.send_material(update, context)
        
        # الرصيد والإحالة
        elif callback_data == 'my_balance':
            await self.show_balance(update, context)
        elif callback_data == 'charge_balance':
            await self.show_charge_options(update, context)
        elif callback_data == 'invite_friends':
            await self.show_invite_friends(update, context)
        elif callback_data == 'my_stats':
            await self.show_stats(update, context)
        
        # الدعم والمساعدة
        elif callback_data == 'help':
            await self.show_help(update, context)
        elif callback_data == 'support':
            await self.show_support(update, context)
        
        # لوحة التحكم
        elif callback_data == 'admin_panel':
            await self.show_admin_panel(update, context)
        elif callback_data == 'admin_users':
            await self.admin_manage_users(update, context)
        elif callback_data == 'admin_charge':
            await self.admin_charge_management(update, context)
        elif callback_data == 'admin_services':
            await self.admin_manage_services(update, context)
        elif callback_data == 'admin_materials':
            await self.admin_manage_materials(update, context)
        elif callback_data == 'admin_settings':
            await self.admin_manage_settings(update, context)
        elif callback_data == 'admin_stats':
            await self.admin_show_stats(update, context)
        
        # إدارة المستخدمين
        elif callback_data == 'admin_list_users':
            await self.admin_list_users(update, context)
        elif callback_data == 'admin_add_balance':
            await self.admin_add_balance(update, context)
        
        # تغيير الأسعار
        elif callback_data in ['admin_change_price_excuse', 'admin_change_price_summary', 'admin_change_price_qa']:
            await self.admin_change_price(update, context)
        
        # إدارة الملازم
        elif callback_data == 'admin_add_material':
            await self.admin_add_material(update, context)
        
        # الإعدادات
        elif callback_data == 'admin_toggle_maintenance':
            await self.admin_toggle_maintenance(update, context)
        elif callback_data == 'admin_change_channel':
            await self.admin_change_channel(update, context)
        
        else:
            await query.answer("⚠️ هذا الزر غير مفعل حالياً", show_alert=True)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الملفات المرسلة"""
        user_id = update.effective_user.id
        
        # التحقق من وضع الصيانة
        if await self.check_maintenance() and not await self.is_admin(user_id):
            await update.message.reply_text(
                await self.format_arabic_text("⛔ البوت تحت الصيانة حالياً. الرجاء المحاولة لاحقاً.")
            )
            return
        
        # التحقق إذا كان المستخدم ينتظر ملف PDF للتلخيص
        if user_id in self.user_sessions and self.user_sessions[user_id].get('waiting_for_file'):
            await self.handle_pdf_file(update, context)
            return
        
        # التحقق إذا كان المدير يرسل ملفاً للملازم
        if user_id in self.admin_commands and isinstance(self.admin_commands[user_id], dict) and self.admin_commands[user_id].get('action') == 'add_material_file':
            await self.admin_handle_material(update, context)
            return
        
        # إذا لم تكن حالة خاصة، عرض القائمة
        await self.show_main_menu(update, context)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الصور المرسلة"""
        user_id = update.effective_user.id
        
        # التحقق من وضع الصيانة
        if await self.check_maintenance() and not await self.is_admin(user_id):
            await update.message.reply_text(
                await self.format_arabic_text("⛔ البوت تحت الصيانة حالياً. الرجاء المحاولة لاحقاً.")
            )
            return
        
        # التحقق إذا كان المستخدم يرسل صورة لخدمة سؤال وجواب
        if user_id in self.user_sessions and self.user_sessions[user_id].get('waiting_for_question'):
            await self.handle_qa_question(update, context)
            return
        
        # إذا لم تكن حالة خاصة، عرض القائمة
        await self.show_main_menu(update, context)
    
    # ========== دالة التشغيل الرئيسية ==========
    async def run(self):
        """تشغيل البوت"""
        # إنشاء تطبيق البوت
        app = Application.builder().token(TOKEN).build()
        
        # إضافة المعالجات
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("menu", self.show_main_menu))
        
        # معالجات الرسائل
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # معالجات الأزرار
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # بدء البوت
        logger.info("✅ بدأ تشغيل البوت...")
        print("=" * 50)
        print("🎓 بوت 'يلا نتعلم' يعمل بنجاح!")
        print(f"👤 المدير: {ADMIN_ID}")
        print(f"🆔 يوزر البوت: {BOT_USERNAME}")
        print(f"🛠 الدعم: {SUPPORT_USERNAME}")
        print("=" * 50)
        
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        # الحفاظ على البوت قيد التشغيل
        await asyncio.Event().wait()

# ========== الدالة الرئيسية ==========
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    bot = YallaNt3lemBot()
    
    # تشغيل البوت
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot.run())
    except KeyboardInterrupt:
        logger.info("⏹ إيقاف البوت...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
