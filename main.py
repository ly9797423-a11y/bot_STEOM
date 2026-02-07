#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام: يلا نتعلم
مطور بواسطة: Allawi04
كود كامل ومتكامل - ملف واحد فقط
"""

import os
import json
import sqlite3
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# المكتبات الأساسية
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, InputFile,
    InputMediaDocument, InputMediaVideo
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
from telegram.constants import ParseMode, ChatAction

# مكتبات PDF والمعالجة
import PyPDF2
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# مكتبات الوسائط
import mimetypes
from PIL import Image
import cv2
import numpy as np

# إعدادات التسعير والمتغيرات
TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
SUPPORT_USER = "Allawi04@"
CHANNEL_USERNAME = "FCJCV"
GEMINI_API_KEY = "AIzaSyARsl_YMXA74bPQpJduu0jJVuaku7MaHuY"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# أسعار الخدمات (قابلة للتعديل من لوحة التحكم)
SERVICE_PRICES = {
    "exemption": 1000,
    "summary": 1000,
    "qa": 1000,
    "help_student": 1000,
    "materials": 0,  # مجاني للتصفح
    "vip_subscription": 5000,  # سعر الاشتراك الشهري
}

# حالة المحادثة
(
    MAIN_MENU,
    ADMIN_PANEL,
    EXEMPTION_STEP1,
    EXEMPTION_STEP2,
    EXEMPTION_STEP3,
    UPLOAD_PDF,
    ASK_QUESTION,
    ANSWER_QUESTION,
    HELP_STUDENT_ASK,
    HELP_STUDENT_ANSWER,
    VIP_SUBSCRIPTION,
    VIP_UPLOAD_LECTURE,
    VIP_SET_PRICE,
    ADMIN_CHARGE,
    ADMIN_DEDUCT,
    ADMIN_BAN,
    ADMIN_UNBAN,
    ADMIN_SET_PRICE,
    ADMIN_ADD_MATERIAL,
    ADMIN_BROADCAST,
    ADMIN_VIP_MANAGE,
    ADMIN_VIP_WITHDRAW,
    WAITING_FOR_APPROVAL,
) = range(23)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تسجيل الخطوط العربية
try:
    pdfmetrics.registerFont(TTFont('Arabic', 'fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('ArabicBold', 'fonts/arialbd.ttf'))
except:
    # إنشاء خطوط افتراضية إذا لم تكن موجودة
    pass

class Database:
    """فئة لإدارة قاعدة البيانات"""
    
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.create_tables()
        self.create_default_admin()
    
    def create_tables(self):
        """إنشاء الجداول اللازمة"""
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
                invited_count INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول خدمات VIP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_users (
                user_id INTEGER PRIMARY KEY,
                subscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                earnings_balance INTEGER DEFAULT 0,
                total_earnings INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول محاضرات VIP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_lectures (
                lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER,
                title TEXT,
                description TEXT,
                video_path TEXT,
                price INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                purchases INTEGER DEFAULT 0,
                earnings INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 0,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول مشتريات محاضرات VIP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                lecture_id INTEGER,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amount_paid INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (lecture_id) REFERENCES vip_lectures (lecture_id)
            )
        ''')
        
        # جدول المواد التعليمية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                material_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                stage TEXT,
                file_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول أسئلة قسم ساعدوني طالب
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS help_questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_text TEXT,
                subject TEXT,
                is_approved INTEGER DEFAULT 0,
                is_answered INTEGER DEFAULT 0,
                answer_text TEXT,
                answerer_id INTEGER,
                ask_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answer_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول عمليات الشحن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول إعدادات البوت
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT
            )
        ''')
        
        # جدول الإحصائيات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                stat_date DATE PRIMARY KEY,
                new_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                transactions_count INTEGER DEFAULT 0,
                total_income INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
    def create_default_admin(self):
        """إنشاء المدير الافتراضي"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, is_admin, balance)
            VALUES (?, ?, ?, ?, ?)
        ''', (ADMIN_ID, SUPPORT_USER, "المدير", 1, 1000000))
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def create_user(self, user_id: int, username: str, first_name: str, last_name: str = "", invited_by: int = 0):
        """إنشاء مستخدم جديد"""
        cursor = self.conn.cursor()
        
        # منح هدية الترحيب
        welcome_bonus = 1000
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, balance, invited_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, welcome_bonus, invited_by))
        
        # تحديث عدد المدعوين للمدعوّ
        if invited_by > 0:
            invitation_bonus = 500  # مكافأة الدعوة
            cursor.execute('UPDATE users SET invited_count = invited_count + 1, balance = balance + ? WHERE user_id = ?',
                         (invitation_bonus, invited_by))
            
            # تسجيل العملية
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, type, description)
                VALUES (?, ?, ?, ?)
            ''', (invited_by, invitation_bonus, 'invitation_bonus', f'مكافأة دعوة للمستخدم {user_id}'))
        
        # تسجيل عملية هدية الترحيب
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, welcome_bonus, 'welcome_bonus', 'هدية ترحيب جديدة'))
        
        self.conn.commit()
        return True
    
    def update_balance(self, user_id: int, amount: int, transaction_type: str, description: str = "") -> bool:
        """تحديث رصيد المستخدم"""
        cursor = self.conn.cursor()
        
        # التحقق من وجود المستخدم
        user = self.get_user(user_id)
        if not user:
            return False
        
        # حساب الرصيد الجديد
        new_balance = user['balance'] + amount
        
        # إذا كان الرصيد سالباً بعد العملية
        if new_balance < 0:
            return False
        
        # تحديث الرصيد
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
        
        # تسجيل العملية
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, transaction_type, description))
        
        self.conn.commit()
        return True
    
    def check_service_access(self, user_id: int, service: str, price: int = None) -> Tuple[bool, str]:
        """التحقق من إمكانية الوصول للخدمة"""
        user = self.get_user(user_id)
        if not user:
            return False, "المستخدم غير موجود"
        
        if user['is_banned']:
            return False, "حسابك محظور! راسل الدعم الفني"
        
        # الحصول على سعر الخدمة
        if price is None:
            price = SERVICE_PRICES.get(service, 1000)
        
        if user['balance'] < price:
            return False, f"رصيدك غير كافي! سعر الخدمة: {price} دينار\nرصيدك الحالي: {user['balance']} دينار"
        
        return True, ""

# فئة البوت الرئيسية
class LearnBot:
    def __init__(self):
        self.db = Database()
        self.user_states = {}
        self.temp_data = {}
        
    def format_currency(self, amount: int) -> str:
        """تنسيق العملة"""
        return f"{amount:,} دينار عراقي"
    
    def reshape_arabic(self, text: str) -> str:
        """إعادة تشكيل النص العربي"""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:
            return text
    
    async def generate_gemini_response(self, prompt: str) -> str:
        """إنشاء رد باستخدام Gemini AI"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': GEMINI_API_KEY
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(GEMINI_API_KEY, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return "عذراً، حدث خطأ في معالجة الطلب. حاول مرة أخرى لاحقاً."
            
        except Exception as e:
            logger.error(f"Gemini AI Error: {e}")
            return "عذراً، خدمة الذكاء الاصطناعي غير متوفرة حالياً."
    
    async def process_pdf_summary(self, pdf_file: BytesIO) -> BytesIO:
        """معالجة وتلخيص ملف PDF"""
        try:
            # قراءة ملف PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            # استخراج النص من كل صفحة
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n\n"
            
            # استخدام الذكاء الاصطناعي للتلخيص
            summary_prompt = f"""الرجاء تلخيص النص التالي مع الحفاظ على المعلومات المهمة وحذف الزائد:
            
            {text_content[:3000]}
            
            قدم التلخيص بشكل منظم مع عناوين رئيسية."""
            
            summary = await self.generate_gemini_response(summary_prompt)
            
            # إنشاء ملف PDF جديد مع الخطوط العربية
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # إعداد الصفحة
            width, height = letter
            y_position = height - 50
            
            # عنوان التلخيص
            can.setFont("ArabicBold", 16)
            title = self.reshape_arabic("ملخص المادة التعليمية")
            can.drawString(50, y_position, title)
            y_position -= 40
            
            # نص التلخيص
            can.setFont("Arabic", 12)
            lines = summary.split('\n')
            
            for line in lines:
                if y_position < 50:
                    can.showPage()
                    y_position = height - 50
                    can.setFont("Arabic", 12)
                
                arabic_line = self.reshape_arabic(line)
                can.drawString(50, y_position, arabic_line[:100])
                y_position -= 20
            
            can.save()
            packet.seek(0)
            return packet
            
        except Exception as e:
            logger.error(f"PDF Processing Error: {e}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البدء"""
        user = update.effective_user
        user_id = user.id
        
        # التحقق من وجود المستخدم أو إنشاؤه
        if not self.db.get_user(user_id):
            invited_by = 0
            if context.args:
                try:
                    invited_by = int(context.args[0])
                except:
                    pass
            
            self.db.create_user(user_id, user.username, user.first_name, user.last_name or "", invited_by)
        
        # تحديث النشاط
        cursor = self.db.conn.cursor()
        cursor.execute('UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
        self.db.conn.commit()
        
        # عرض القائمة الرئيسية
        await self.show_main_menu(update, context)
        
        return MAIN_MENU
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض القائمة الرئيسية"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🧮 حساب درجة الإعفاء", callback_data='service_exemption')],
            [InlineKeyboardButton("📚 تلخيص الملازم (PDF)", callback_data='service_summary')],
            [InlineKeyboardButton("❓ سؤال وجواب بالذكاء الاصطناعي", callback_data='service_qa')],
            [InlineKeyboardButton("👥 ساعدوني طالب", callback_data='service_help')],
            [InlineKeyboardButton("📖 ملازمي ومرشحاتي", callback_data='service_materials')],
            [InlineKeyboardButton("🎓 محاضرات VIP", callback_data='vip_lectures')],
            [InlineKeyboardButton("⭐ اشتراك VIP", callback_data='vip_subscription')],
            [InlineKeyboardButton("💰 رصيدي", callback_data='my_balance')],
            [InlineKeyboardButton("👥 دعوة صديق", callback_data='invite_friend')],
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data='admin_panel')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
        👋 أهلاً بك {user_data['first_name']} في بوت *يلا نتعلم*!
        
        *رصيدك الحالي:* {self.format_currency(user_data['balance'])}
        
        *الخدمات المتاحة:* (جميعها مدفوعة)
        
        اختر الخدمة التي تريدها 👇
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ردود الاتصال"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        # الحالات الخاصة
        if data == 'main_menu':
            await self.show_main_menu(update, context)
            return MAIN_MENU
        
        elif data == 'admin_panel':
            if user_id == ADMIN_ID:
                await self.show_admin_panel(update, context)
                return ADMIN_PANEL
            else:
                await query.edit_message_text("⚠️ ليس لديك صلاحية الدخول إلى لوحة التحكم!")
                return MAIN_MENU
        
        # خدمات المستخدمين
        elif data.startswith('service_'):
            service = data.replace('service_', '')
            await self.handle_service_selection(update, context, service)
        
        # خدمات VIP
        elif data == 'vip_lectures':
            await self.show_vip_lectures(update, context)
        
        elif data == 'vip_subscription':
            await self.show_vip_subscription(update, context)
        
        # إدارة الرصيد
        elif data == 'my_balance':
            await self.show_balance(update, context)
        
        elif data == 'invite_friend':
            await self.show_invitation(update, context)
        
        # لوحة التحكم
        elif data.startswith('admin_'):
            await self.handle_admin_callback(update, context, data)
        
        return MAIN_MENU
    
    async def handle_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service: str):
        """معالجة اختيار الخدمة"""
        user_id = update.effective_user.id
        query = update.callback_query
        
        price = SERVICE_PRICES.get(service, 1000)
        
        # التحقق من الرصيد
        access, message = self.db.check_service_access(user_id, service, price)
        if not access:
            await query.edit_message_text(
                text=f"⚠️ {message}\n\n",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return
        
        # حفظ حالة الخدمة
        context.user_data['current_service'] = service
        context.user_data['service_price'] = price
        
        # توجيه إلى الخدمة المحددة
        if service == 'exemption':
            await self.start_exemption_calculation(update, context)
        
        elif service == 'summary':
            await query.edit_message_text(
                text="📤 *رجاءً أرسل ملف PDF المراد تلخيصه*\n\n"
                     "سيتم معالجة الملف وتلخيصه باستخدام الذكاء الاصطناعي.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
                ])
            )
            return UPLOAD_PDF
        
        elif service == 'qa':
            await query.edit_message_text(
                text="❓ *أرسل سؤالك الآن*\n\n"
                     "يمكنك إرسال نص أو صورة تحتوي على السؤال، وسأجيبك باستخدام الذكاء الاصطناعي.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
                ])
            )
            return ASK_QUESTION
        
        elif service == 'help':
            await self.show_help_student_section(update, context)
        
        elif service == 'materials':
            await self.show_materials(update, context)
    
    async def start_exemption_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء حساب درجة الإعفاء"""
        query = update.callback_query
        
        context.user_data['exemption_scores'] = []
        
        await query.edit_message_text(
            text="🧮 *حساب درجة الإعفاء*\n\n"
                 "أدخل درجة الكورس الأول (0-100):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
            ])
        )
        return EXEMPTION_STEP1
    
    async def handle_exemption_step1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة درجة الكورس الأول"""
        try:
            score = float(update.message.text)
            if 0 <= score <= 100:
                context.user_data['exemption_scores'].append(score)
                
                await update.message.reply_text(
                    text="✅ تم حفظ درجة الكورس الأول\n\n"
                         "أدخل درجة الكورس الثاني (0-100):",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
                    ])
                )
                return EXEMPTION_STEP2
            else:
                await update.message.reply_text("⚠️ الرجاء إدخال درجة بين 0 و 100")
                return EXEMPTION_STEP1
        except:
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح")
            return EXEMPTION_STEP1
    
    async def handle_exemption_step2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة درجة الكورس الثاني"""
        try:
            score = float(update.message.text)
            if 0 <= score <= 100:
                context.user_data['exemption_scores'].append(score)
                
                await update.message.reply_text(
                    text="✅ تم حفظ درجة الكورس الثاني\n\n"
                         "أدخل درجة الكورس الثالث (0-100):",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
                    ])
                )
                return EXEMPTION_STEP3
            else:
                await update.message.reply_text("⚠️ الرجاء إدخال درجة بين 0 و 100")
                return EXEMPTION_STEP2
        except:
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح")
            return EXEMPTION_STEP2
    
    async def handle_exemption_step3(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة درجة الكورس الثالث وحساب المعدل"""
        try:
            score = float(update.message.text)
            if 0 <= score <= 100:
                context.user_data['exemption_scores'].append(score)
                
                # حساب المعدل
                scores = context.user_data['exemption_scores']
                average = sum(scores) / len(scores)
                
                # خصم المبلغ
                user_id = update.effective_user.id
                price = context.user_data.get('service_price', 1000)
                
                if self.db.update_balance(user_id, -price, 'service_payment', 'حساب درجة الإعفاء'):
                    # إرسال النتيجة
                    if average >= 90:
                        result_text = f"🎉 *مبروك! أنت معفى من المادة*\n\n"
                        result_text += f"*المعدل النهائي:* {average:.2f}\n"
                        result_text += f"*الدرجات:* {scores[0]}, {scores[1]}, {scores[2]}\n\n"
                        result_text += "تهانينا على تحقيق الإعفاء! 🎊"
                    else:
                        result_text = f"⚠️ *للأسف أنت غير معفى*\n\n"
                        result_text += f"*المعدل النهائي:* {average:.2f}\n"
                        result_text += f"*الدرجات:* {scores[0]}, {scores[1]}, {scores[2]}\n\n"
                        result_text += "المعدل المطلوب للإعفاء هو 90 أو أكثر"
                    
                    keyboard = [
                        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')],
                        [InlineKeyboardButton("🔄 حساب جديد", callback_data='service_exemption')]
                    ]
                    
                    await update.message.reply_text(
                        text=result_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
                    # مسح البيانات المؤقتة
                    context.user_data.pop('exemption_scores', None)
                    context.user_data.pop('current_service', None)
                    context.user_data.pop('service_price', None)
                    
                    return MAIN_MENU
                else:
                    await update.message.reply_text(
                        "⚠️ حدث خطأ في عملية الدفع!",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                        ])
                    )
                    return MAIN_MENU
            else:
                await update.message.reply_text("⚠️ الرجاء إدخال درجة بين 0 و 100")
                return EXEMPTION_STEP3
        except:
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح")
            return EXEMPTION_STEP3
    
    async def handle_pdf_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة رفع ملف PDF"""
        user_id = update.effective_user.id
        
        if not update.message.document:
            await update.message.reply_text("⚠️ الرجاء إرسال ملف PDF فقط")
            return UPLOAD_PDF
        
        document = update.message.document
        if not document.file_name.endswith('.pdf'):
            await update.message.reply_text("⚠️ الملف يجب أن يكون بصيغة PDF")
            return UPLOAD_PDF
        
        # خصم المبلغ
        price = context.user_data.get('service_price', 1000)
        if not self.db.update_balance(user_id, -price, 'service_payment', 'تلخيص PDF'):
            await update.message.reply_text(
                "⚠️ رصيدك غير كافي لهذه الخدمة!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return MAIN_MENU
        
        # إعلام المستخدم بالبدء في المعالجة
        processing_msg = await update.message.reply_text("🔄 جاري معالجة الملف وتلخيصه...")
        
        try:
            # تحميل الملف
            file = await document.get_file()
            file_bytes = BytesIO()
            await file.download_to_memory(file_bytes)
            file_bytes.seek(0)
            
            # معالجة الملف
            summarized_pdf = await self.process_pdf_summary(file_bytes)
            
            # إرسال الملف الملخص
            await update.message.reply_document(
                document=InputFile(summarized_pdf, filename="ملخص_المادة.pdf"),
                caption="✅ *تم تلخيص الملف بنجاح*\n\n"
                       "هذا هو الملف الملخص باستخدام الذكاء الاصطناعي.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            await processing_msg.delete()
            
            keyboard = [
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')],
                [InlineKeyboardButton("📚 تلخيص ملف آخر", callback_data='service_summary')]
            ]
            
            await update.message.reply_text(
                "اختر الخطوة التالية:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # مسح البيانات المؤقتة
            context.user_data.pop('current_service', None)
            context.user_data.pop('service_price', None)
            
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"PDF Processing Error: {e}")
            
            # إعادة المبلغ في حالة الخطأ
            self.db.update_balance(user_id, price, 'refund', 'خطأ في معالجة PDF')
            
            await update.message.reply_text(
                "⚠️ حدث خطأ في معالجة الملف! تم إعادة المبلغ إلى رصيدك.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return MAIN_MENU
    
    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأسئلة بالذكاء الاصطناعي"""
        user_id = update.effective_user.id
        
        # خصم المبلغ أولاً
        price = context.user_data.get('service_price', 1000)
        if not self.db.update_balance(user_id, -price, 'service_payment', 'سؤال وجواب AI'):
            await update.message.reply_text(
                "⚠️ رصيدك غير كافي لهذه الخدمة!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return MAIN_MENU
        
        # إعلام المستخدم بالمعالجة
        processing_msg = await update.message.reply_text("🤔 جاري تحليل سؤالك وإعداد الإجابة...")
        
        # استخراج النص من الرسالة
        question_text = ""
        if update.message.text:
            question_text = update.message.text
        elif update.message.caption:
            question_text = update.message.caption
        elif update.message.photo:
            question_text = "صورة تحتوي على سؤال دراسي"
        
        # إنشاء الرد باستخدام الذكاء الاصطناعي
        prompt = f"""أجب على السؤال التالي كطالب عراقي، مع تقديم إجابة علمية دقيقة ومناسبة للمنهج العراقي:

        السؤال: {question_text}
        
        قدم الإجابة بشكل منظم ومفصل مع الأمثلة إذا لزم الأمر."""
        
        answer = await self.generate_gemini_response(prompt)
        
        await processing_msg.delete()
        
        # إرسال الإجابة
        await update.message.reply_text(
            text=f"🧠 *إجابة الذكاء الاصطناعي:*\n\n{answer}\n\n"
                 "---\n"
                 "إذا كانت الإجابة غير واضحة، يمكنك إعادة صياغة السؤال.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')],
            [InlineKeyboardButton("❓ سؤال آخر", callback_data='service_qa')]
        ]
        
        await update.message.reply_text(
            "اختر الخطوة التالية:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # مسح البيانات المؤقتة
        context.user_data.pop('current_service', None)
        context.user_data.pop('service_price', None)
        
        return MAIN_MENU
    
    async def show_help_student_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قسم ساعدوني طالب"""
        query = update.callback_query
        
        # الحصول على الأسئلة غير المجابة
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT q.question_id, q.question_text, u.first_name, q.ask_date
            FROM help_questions q
            JOIN users u ON q.user_id = u.user_id
            WHERE q.is_approved = 1 AND q.is_answered = 0
            ORDER BY q.ask_date DESC
            LIMIT 10
        ''')
        questions = cursor.fetchall()
        
        keyboard = []
        
        if questions:
            text = "👥 *قسم ساعدوني طالب*\n\n"
            text += "*الأسئلة المتاحة للإجابة:*\n\n"
            
            for i, (q_id, q_text, name, date) in enumerate(questions, 1):
                text += f"{i}. {q_text[:50]}... - {name}\n"
                keyboard.append([InlineKeyboardButton(f"✏️ جاوب على السؤال {i}", callback_data=f'answer_help_{q_id}')])
        else:
            text = "👥 *قسم ساعدوني طالب*\n\n"
            text += "لا توجد أسئلة متاحة للإجابة حالياً.\n\n"
        
        keyboard.append([InlineKeyboardButton("❓ أرسل سؤال جديد", callback_data='ask_help_question')])
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_help_question_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إرسال سؤال جديد في قسم ساعدوني طالب"""
        query = update.callback_query
        
        # التحقق من الرصيد
        user_id = update.effective_user.id
        price = SERVICE_PRICES.get('help_student', 1000)
        
        access, message = self.db.check_service_access(user_id, 'help_student', price)
        if not access:
            await query.edit_message_text(
                text=f"⚠️ {message}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return MAIN_MENU
        
        await query.edit_message_text(
            text="❓ *أرسل سؤالك الآن*\n\n"
                 "سوف يتم مراجعة السؤال من قبل الإدارة قبل نشره.\n"
                 "بعد الموافقة، سيتمكن الطلاب الآخرون من الإجابة عليه.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
            ])
        )
        
        context.user_data['awaiting_help_question'] = True
        return HELP_STUDENT_ASK
    
    async def process_help_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة استلام سؤال ساعدوني طالب"""
        user_id = update.effective_user.id
        question_text = update.message.text
        
        if not question_text or len(question_text) < 10:
            await update.message.reply_text("⚠️ الرجاء إدخال سؤال واضح ومفصل")
            return HELP_STUDENT_ASK
        
        # خصم المبلغ
        price = SERVICE_PRICES.get('help_student', 1000)
        if not self.db.update_balance(user_id, -price, 'service_payment', 'سؤال ساعدوني طالب'):
            await update.message.reply_text(
                "⚠️ حدث خطأ في عملية الدفع!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return MAIN_MENU
        
        # حفظ السؤال في قاعدة البيانات
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO help_questions (user_id, question_text, subject, is_approved, is_answered)
            VALUES (?, ?, ?, 0, 0)
        ''', (user_id, question_text, "عام",))
        question_id = cursor.lastrowid
        self.db.conn.commit()
        
        # إرسال إشعار للمدير للموافقة
        admin_text = f"📋 *سؤال جديد يحتاج موافقة*\n\n"
        admin_text += f"*المستخدم:* {update.effective_user.first_name}\n"
        admin_text += f"*السؤال:* {question_text[:200]}...\n\n"
        admin_text += f"*رقم السؤال:* {question_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ موافقة", callback_data=f'approve_help_{question_id}'),
                InlineKeyboardButton("❌ رفض", callback_data=f'reject_help_{question_id}')
            ],
            [InlineKeyboardButton("👀 عرض كامل", callback_data=f'view_help_{question_id}')]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # إعلام المستخدم
        await update.message.reply_text(
            "✅ تم استلام سؤالك!\n"
            "سيتم مراجعته من قبل الإدارة ونشره قريباً.\n\n"
            "ستصلك إشعار عند الموافقة على السؤال.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
            ])
        )
        
        context.user_data.pop('awaiting_help_question', None)
        return MAIN_MENU
    
    async def show_materials(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المواد التعليمية"""
        query = update.callback_query
        
        # الحصول على المواد
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT material_id, title, description, stage
            FROM materials
            ORDER BY stage, upload_date DESC
        ''')
        materials = cursor.fetchall()
        
        if not materials:
            text = "📖 *ملازمي ومرشحاتي*\n\n"
            text += "لا توجد مواد متاحة حالياً.\n"
            text += "سيتم إضافة مواد جديدة قريباً."
            
            keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]]
            
            await query.edit_message_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        text = "📖 *ملازمي ومرشحاتي*\n\n"
        text += "*المواد المتاحة:*\n\n"
        
        keyboard = []
        current_stage = None
        
        for material in materials:
            m_id, title, desc, stage = material
            
            if stage != current_stage:
                text += f"\n*📌 المرحلة: {stage}*\n"
                current_stage = stage
            
            text += f"• {title}\n"
            keyboard.append([InlineKeyboardButton(f"📥 تحميل: {title}", callback_data=f'download_mat_{m_id}')])
        
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_vip_lectures(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض محاضرات VIP"""
        query = update.callback_query
        
        # التحقق من اشتراك VIP
        user_id = update.effective_user.id
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM vip_users 
            WHERE user_id = ? AND is_active = 1 AND expiry_date > CURRENT_TIMESTAMP
        ''', (user_id,))
        vip_user = cursor.fetchone()
        
        if not vip_user:
            # عرض محاضرات مجانية أو عينة
            cursor.execute('''
                SELECT lecture_id, title, description, price
                FROM vip_lectures 
                WHERE is_approved = 1 AND price = 0
                ORDER BY upload_date DESC
                LIMIT 5
            ''')
            free_lectures = cursor.fetchall()
            
            text = "🎓 *محاضرات VIP*\n\n"
            text += "للوصول إلى جميع المحاضرات، يجب الاشتراك في باقة VIP.\n\n"
            
            if free_lectures:
                text += "*المحاضرات المجانية المتاحة:*\n\n"
                keyboard = []
                
                for lecture in free_lectures:
                    l_id, title, desc, price = lecture
                    text += f"• {title}\n"
                    keyboard.append([InlineKeyboardButton(f"🎬 مشاهدة: {title}", callback_data=f'view_lecture_{l_id}')])
            else:
                text += "لا توجد محاضرات مجانية حالياً.\n"
                keyboard = []
            
            keyboard.append([InlineKeyboardButton("⭐ اشتراك VIP", callback_data='vip_subscription')])
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')])
            
        else:
            # عرض جميع محاضرات VIP
            cursor.execute('''
                SELECT lecture_id, title, description, price, teacher_id
                FROM vip_lectures 
                WHERE is_approved = 1
                ORDER BY upload_date DESC
            ''')
            lectures = cursor.fetchall()
            
            text = "🎓 *محاضرات VIP*\n\n"
            text += "*جميع المحاضرات المتاحة:*\n\n"
            
            keyboard = []
            
            for lecture in lectures:
                l_id, title, desc, price, teacher_id = lecture
                price_text = "مجاني" if price == 0 else f"{self.format_currency(price)}"
                text += f"• {title} ({price_text})\n"
                
                if price == 0:
                    keyboard.append([InlineKeyboardButton(f"🎬 {title}", callback_data=f'view_lecture_{l_id}')])
                else:
                    keyboard.append([InlineKeyboardButton(f"🛒 شراء: {title}", callback_data=f'buy_lecture_{l_id}')])
            
            # إذا كان المستخدم محاضراً
            cursor.execute('SELECT * FROM vip_lectures WHERE teacher_id = ?', (user_id,))
            if cursor.fetchone():
                keyboard.append([InlineKeyboardButton("📤 رفع محاضرة جديدة", callback_data='vip_upload')])
            
            keyboard.append([InlineKeyboardButton("💰 رصيد أرباحي", callback_data='vip_earnings')])
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_vip_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض باقات الاشتراك VIP"""
        query = update.callback_query
        
        price = SERVICE_PRICES.get('vip_subscription', 5000)
        
        text = f"⭐ *اشتراك VIP*\n\n"
        text += f"*السعر الشهري:* {self.format_currency(price)}\n\n"
        text += "*المميزات:*\n"
        text += "• الوصول إلى جميع محاضرات VIP\n"
        text += "• رفع محاضرات خاصة بك\n"
        text += "• تحصيل 60% من أرباح محاضراتك\n"
        text += "• دعم فني متميز\n"
        text += "• إشعارات فورية\n\n"
        text += "*شروط الاشتراك:*\n"
        text += "• الاشتراك شهري\n"
        text += "• يمكنك رفع محاضرات حتى 100 ميجابايت\n"
        text += "• جميع المحاضرات تخضع للمراجعة\n"
        text += "• يمكن إلغاء الاشتراك في أي وقت\n\n"
        text += "هل تريد الاشتراك؟"
        
        keyboard = [
            [InlineKeyboardButton("✅ نعم، أريد الاشتراك", callback_data='vip_purchase')],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_vip_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة شراء اشتراك VIP"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        price = SERVICE_PRICES.get('vip_subscription', 5000)
        
        # التحقق من الرصيد
        access, message = self.db.check_service_access(user_id, 'vip_subscription', price)
        if not access:
            await query.edit_message_text(
                text=f"⚠️ {message}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return
        
        # خصم المبلغ
        if not self.db.update_balance(user_id, -price, 'vip_subscription', 'اشتراك VIP شهري'):
            await query.edit_message_text(
                "⚠️ حدث خطأ في عملية الدفع!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
            return
        
        # تفعيل الاشتراك
        cursor = self.db.conn.cursor()
        expiry_date = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            INSERT OR REPLACE INTO vip_users (user_id, subscription_date, expiry_date, is_active)
            VALUES (?, CURRENT_TIMESTAMP, ?, 1)
        ''', (user_id, expiry_date))
        
        self.db.conn.commit()
        
        # إرسال إشعار للمدير
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ *اشتراك VIP جديد*\n\n"
                 f"*المستخدم:* {update.effective_user.first_name}\n"
                 f"*الآيدي:* {user_id}\n"
                 f"*تاريخ الانتهاء:* {expiry_date.strftime('%Y-%m-%d')}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # إعلام المستخدم
        await query.edit_message_text(
            text="🎉 *مبروك! تم تفعيل اشتراكك VIP*\n\n"
                 "يمكنك الآن:\n"
                 "• الوصول إلى جميع محاضرات VIP\n"
                 "• رفع محاضرات خاصة بك\n"
                 "• تحصيل الأرباح من محاضراتك\n\n"
                 "اشتراكك ساري لمدة 30 يوماً.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎓 محاضرات VIP", callback_data='vip_lectures')],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
            ])
        )
    
    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض رصيد المستخدم"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        user_data = self.db.get_user(user_id)
        
        # الحصول على تاريخ انتهاء الاشتراك VIP
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT expiry_date, earnings_balance FROM vip_users 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        vip_data = cursor.fetchone()
        
        text = f"💰 *رصيدك الحالي*\n\n"
        text += f"*الرصيد الرئيسي:* {self.format_currency(user_data['balance'])}\n"
        
        if vip_data:
            expiry_date = datetime.strptime(vip_data[0], '%Y-%m-%d %H:%M:%S')
            earnings = vip_data[1] or 0
            
            text += f"*رصيد الأرباح (VIP):* {self.format_currency(earnings)}\n"
            text += f"*انتهاء الاشتراك VIP:* {expiry_date.strftime('%Y-%m-%d')}\n"
        
        text += f"\n*عدد المدعوين:* {user_data['invited_count']}\n"
        text += f"*تاريخ الانضمام:* {user_data['join_date'][:10]}"
        
        keyboard = [
            [InlineKeyboardButton("👥 دعوة صديق", callback_data='invite_friend')],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
        ]
        
        if user_id == ADMIN_ID:
            keyboard.insert(0, [InlineKeyboardButton("👑 لوحة التحكم", callback_data='admin_panel')])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_invitation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض رابط الدعوة"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        invitation_link = f"https://t.me/{BOT_USERNAME[1:]}?start={user_id}"
        bonus_amount = 500
        
        # التحقق من اشتراك VIP
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM vip_users WHERE user_id = ? AND is_active = 1', (user_id,))
        is_vip = cursor.fetchone() is not None
        
        text = f"👥 *دعوة صديق*\n\n"
        text += f"*رابط الدعوة:* `{invitation_link}`\n\n"
        
        if is_vip:
            text += f"🎯 *مميزات خاصة للمحاضرين VIP:*\n"
            text += "• رابط دعوة ترويجي خاص\n"
            text += "• مكافأة مضاعفة لكل دعوة\n"
            text += "• تقارير متقدمة للدعوات\n"
            bonus_amount = 1000
        
        text += f"\n*مكافأة الدعوة:* {self.format_currency(bonus_amount)} لكل صديق\n"
        text += "سيحصل صديقك أيضاً على 1000 دينار هدية ترحيب!"
        
        keyboard = [
            [InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={invitation_link}&text=انضم%20إلى%20بوت%20يلا%20نتعلم%20للدراسة%20والتعلم%20باستخدام%20الذكاء%20الاصطناعي!")],
            [InlineKeyboardButton("📊 إحصائيات دعواتي", callback_data='invite_stats')],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض لوحة التحكم للمدير"""
        query = update.callback_query
        
        # الحصول على الإحصائيات
        cursor = self.db.conn.cursor()
        
        # عدد المستخدمين
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # عدد المستخدمين النشطين (آخر 7 أيام)
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_active > datetime('now', '-7 days')
        ''')
        active_users = cursor.fetchone()[0]
        
        # إجمالي الأرصدة
        cursor.execute('SELECT SUM(balance) FROM users')
        total_balance = cursor.fetchone()[0] or 0
        
        # عدد مشتركي VIP
        cursor.execute('SELECT COUNT(*) FROM vip_users WHERE is_active = 1')
        vip_users = cursor.fetchone()[0]
        
        text = f"👑 *لوحة التحكم*\n\n"
        text += f"*إجمالي المستخدمين:* {total_users}\n"
        text += f"*المستخدمين النشطين:* {active_users}\n"
        text += f"*مشتركي VIP:* {vip_users}\n"
        text += f"*إجمالي الأرصدة:* {self.format_currency(total_balance)}\n\n"
        text += "*اختر القسم:*"
        
        keyboard = [
            [InlineKeyboardButton("💰 شحن رصيد", callback_data='admin_charge'),
             InlineKeyboardButton("💸 خصم رصيد", callback_data='admin_deduct')],
            [InlineKeyboardButton("🚫 حظر مستخدم", callback_data='admin_ban'),
             InlineKeyboardButton("✅ فك حظر", callback_data='admin_unban')],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data='admin_users')],
            [InlineKeyboardButton("⚙️ إدارة الخدمات", callback_data='admin_services')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("📢 إرسال إذاعة", callback_data='admin_broadcast')],
            [InlineKeyboardButton("⭐ إدارة VIP", callback_data='admin_vip')],
            [InlineKeyboardButton("📖 إدارة المواد", callback_data='admin_materials')],
            [InlineKeyboardButton("❓ الأسئلة المنتظرة", callback_data='admin_pending_questions')],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_PANEL
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """معالجة ردود الاتصال في لوحة التحكم"""
        query = update.callback_query
        
        if data == 'admin_charge':
            await query.edit_message_text(
                text="💰 *شحن رصيد*\n\n"
                     "أرسل آيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
                ])
            )
            context.user_data['admin_action'] = 'charge'
            return ADMIN_CHARGE
        
        elif data == 'admin_deduct':
            await query.edit_message_text(
                text="💸 *خصم رصيد*\n\n"
                     "أرسل آيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
                ])
            )
            context.user_data['admin_action'] = 'deduct'
            return ADMIN_DEDUCT
        
        elif data == 'admin_ban':
            await query.edit_message_text(
                text="🚫 *حظر مستخدم*\n\n"
                     "أرسل آيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
                ])
            )
            context.user_data['admin_action'] = 'ban'
            return ADMIN_BAN
        
        elif data == 'admin_unban':
            await query.edit_message_text(
                text="✅ *فك حظر مستخدم*\n\n"
                     "أرسل آيدي المستخدم:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
                ])
            )
            context.user_data['admin_action'] = 'unban'
            return ADMIN_UNBAN
        
        elif data == 'admin_users':
            await self.show_admin_users(update, context)
        
        elif data == 'admin_services':
            await self.show_admin_services(update, context)
        
        elif data == 'admin_stats':
            await self.show_admin_stats(update, context)
        
        elif data == 'admin_broadcast':
            await query.edit_message_text(
                text="📢 *إرسال إذاعة*\n\n"
                     "أرسل النص الذي تريد إذاعته:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
                ])
            )
            return ADMIN_BROADCAST
        
        elif data == 'admin_vip':
            await self.show_admin_vip(update, context)
        
        elif data == 'admin_materials':
            await self.show_admin_materials(update, context)
        
        elif data == 'admin_pending_questions':
            await self.show_pending_questions(update, context)
        
        elif data.startswith('approve_help_'):
            question_id = int(data.replace('approve_help_', ''))
            await self.approve_help_question(update, context, question_id)
        
        elif data.startswith('reject_help_'):
            question_id = int(data.replace('reject_help_', ''))
            await self.reject_help_question(update, context, question_id)
        
        elif data.startswith('answer_help_'):
            question_id = int(data.replace('answer_help_', ''))
            await self.start_answering_question(update, context, question_id)
        
        elif data.startswith('vip_approve_'):
            lecture_id = int(data.replace('vip_approve_', ''))
            await self.approve_vip_lecture(update, context, lecture_id)
        
        elif data.startswith('vip_reject_'):
            lecture_id = int(data.replace('vip_reject_', ''))
            await self.reject_vip_lecture(update, context, lecture_id)
    
    async def handle_admin_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة استلام آيدي المستخدم في لوحة التحكم"""
        user_id = update.message.text
        
        try:
            user_id_int = int(user_id)
            context.user_data['target_user_id'] = user_id_int
            
            action = context.user_data.get('admin_action')
            
            if action == 'charge':
                await update.message.reply_text(
                    "أرسل المبلغ المطلوب شحنه:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data='admin_panel')]
                    ])
                )
                return ADMIN_CHARGE + 1
            
            elif action == 'deduct':
                await update.message.reply_text(
                    "أرسل المبلغ المطلوب خصمه:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data='admin_panel')]
                    ])
                )
                return ADMIN_DEDUCT + 1
            
            elif action == 'ban':
                user_data = self.db.get_user(user_id_int)
                if user_data:
                    cursor = self.db.conn.cursor()
                    cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id_int,))
                    self.db.conn.commit()
                    
                    # إرسال إشعار للمستخدم
                    try:
                        await context.bot.send_message(
                            chat_id=user_id_int,
                            text="⚠️ *حسابك تم حظره*\n\n"
                                 "للمزيد من المعلومات، راسل الدعم الفني.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass
                    
                    await update.message.reply_text(
                        f"✅ تم حظر المستخدم {user_data['first_name']}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                        ])
                    )
                else:
                    await update.message.reply_text("⚠️ المستخدم غير موجود")
                
                return ADMIN_PANEL
            
            elif action == 'unban':
                user_data = self.db.get_user(user_id_int)
                if user_data:
                    cursor = self.db.conn.cursor()
                    cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id_int,))
                    self.db.conn.commit()
                    
                    # إرسال إشعار للمستخدم
                    try:
                        await context.bot.send_message(
                            chat_id=user_id_int,
                            text="✅ *تم فك حظر حسابك*\n\n"
                                 "يمكنك استخدام البوت مرة أخرى.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass
                    
                    await update.message.reply_text(
                        f"✅ تم فك حظر المستخدم {user_data['first_name']}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                        ])
                    )
                else:
                    await update.message.reply_text("⚠️ المستخدم غير موجود")
                
                return ADMIN_PANEL
        
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال آيدي صحيح")
            return context.user_data.get('admin_state', ADMIN_PANEL)
    
    async def handle_admin_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة استلام المبلغ في لوحة التحكم"""
        amount = update.message.text
        target_user_id = context.user_data.get('target_user_id')
        action = context.user_data.get('admin_action')
        
        try:
            amount_int = int(amount)
            
            if amount_int <= 0:
                await update.message.reply_text("⚠️ المبلغ يجب أن يكون أكبر من صفر")
                return context.user_data.get('admin_state', ADMIN_PANEL)
            
            user_data = self.db.get_user(target_user_id)
            
            if not user_data:
                await update.message.reply_text("⚠️ المستخدم غير موجود")
                return ADMIN_PANEL
            
            if action == 'charge':
                if self.db.update_balance(target_user_id, amount_int, 'admin_charge', 'شحن من المدير'):
                    # إرسال إشعار للمستخدم
                    try:
                        await context.bot.send_message(
                            chat_id=target_user_id,
                            text=f"💰 *تم شحن رصيدك*\n\n"
                                 f"*المبلغ:* {self.format_currency(amount_int)}\n"
                                 f"*الرصيد الجديد:* {self.format_currency(user_data['balance'] + amount_int)}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass
                    
                    await update.message.reply_text(
                        f"✅ تم شحن {self.format_currency(amount_int)} للمستخدم {user_data['first_name']}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                        ])
                    )
                else:
                    await update.message.reply_text("⚠️ حدث خطأ في عملية الشحن")
            
            elif action == 'deduct':
                if user_data['balance'] < amount_int:
                    await update.message.reply_text(
                        f"⚠️ رصيد المستخدم غير كافي ({self.format_currency(user_data['balance'])})"
                    )
                    return ADMIN_PANEL
                
                if self.db.update_balance(target_user_id, -amount_int, 'admin_deduct', 'خصم من المدير'):
                    # إرسال إشعار للمستخدم
                    try:
                        await context.bot.send_message(
                            chat_id=target_user_id,
                            text=f"💸 *تم خصم من رصيدك*\n\n"
                                 f"*المبلغ:* {self.format_currency(amount_int)}\n"
                                 f"*السبب:* خصم إداري",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass
                    
                    await update.message.reply_text(
                        f"✅ تم خصم {self.format_currency(amount_int)} من المستخدم {user_data['first_name']}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
                        ])
                    )
                else:
                    await update.message.reply_text("⚠️ حدث خطأ في عملية الخصم")
            
            # تنظيف البيانات المؤقتة
            context.user_data.pop('target_user_id', None)
            context.user_data.pop('admin_action', None)
            
            return ADMIN_PANEL
        
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال مبلغ صحيح")
            return context.user_data.get('admin_state', ADMIN_PANEL)
    
    async def show_admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة المستخدمين"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, balance, is_banned, last_active
            FROM users 
            ORDER BY last_active DESC
            LIMIT 50
        ''')
        users = cursor.fetchall()
        
        text = "👥 *إدارة المستخدمين*\n\n"
        text += "*آخر 50 مستخدم نشط:*\n\n"
        
        for user in users:
            user_id, username, name, balance, banned, last_active = user
            status = "🚫" if banned else "✅"
            username_display = f"@{username}" if username else "بدون"
            
            text += f"{status} {name} ({username_display})\n"
            text += f"   آيدي: {user_id} | رصيد: {self.format_currency(balance)}\n"
            text += f"   آخر نشاط: {last_active[:16]}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data='admin_search_user')],
            [InlineKeyboardButton("📊 تقرير مفصل", callback_data='admin_users_report')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_admin_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إدارة الخدمات"""
        query = update.callback_query
        
        text = "⚙️ *إدارة الخدمات*\n\n"
        text += "*الأسعار الحالية:*\n\n"
        
        for service, price in SERVICE_PRICES.items():
            service_name = {
                'exemption': 'حساب درجة الإعفاء',
                'summary': 'تلخيص الملازم',
                'qa': 'سؤال وجواب',
                'help_student': 'ساعدوني طالب',
                'vip_subscription': 'اشتراك VIP'
            }.get(service, service)
            
            text += f"• {service_name}: {self.format_currency(price)}\n"
        
        text += f"\n*مكافأة الدعوة:* {self.format_currency(500)}\n"
        text += "*هدية الترحيب:* 1000 دينار"
        
        keyboard = [
            [InlineKeyboardButton("📝 تعديل الأسعار", callback_data='admin_set_prices')],
            [InlineKeyboardButton("🚫 تعطيل خدمة", callback_data='admin_disable_service')],
            [InlineKeyboardButton("✅ تفعيل خدمة", callback_data='admin_enable_service')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الإذاعة"""
        broadcast_text = update.message.text
        
        if not broadcast_text or len(broadcast_text) < 5:
            await update.message.reply_text("⚠️ النص قصير جداً")
            return ADMIN_BROADCAST
        
        # تأكيد الإذاعة
        keyboard = [
            [InlineKeyboardButton("✅ نعم، أرسل الإذاعة", callback_data='confirm_broadcast')],
            [InlineKeyboardButton("❌ إلغاء", callback_data='admin_panel')]
        ]
        
        context.user_data['broadcast_text'] = broadcast_text
        
        await update.message.reply_text(
            f"📢 *تأكيد الإذاعة*\n\n"
            f"النص:\n{broadcast_text[:500]}...\n\n"
            f"سيتم إرسال هذه الرسالة لجميع المستخدمين.\n"
            f"هل تريد المتابعة؟",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_BROADCAST + 1
    
    async def confirm_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد وإرسال الإذاعة"""
        query = update.callback_query
        broadcast_text = context.user_data.get('broadcast_text', '')
        
        if not broadcast_text:
            await query.edit_message_text("⚠️ لم يتم العثور على نص الإذاعة")
            return ADMIN_PANEL
        
        # إعلام البدء
        await query.edit_message_text("🔄 جاري إرسال الإذاعة...")
        
        # الحصول على جميع المستخدمين
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
        users = cursor.fetchall()
        
        success_count = 0
        fail_count = 0
        
        # إرسال الإذاعة
        for (user_id,) in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 *إذاعة من إدارة البوت:*\n\n{broadcast_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
                success_count += 1
                await asyncio.sleep(0.05)  # لتجنب حظر التليجرام
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user_id}: {e}")
                fail_count += 1
        
        # عرض النتائج
        result_text = f"✅ *تم إرسال الإذاعة*\n\n"
        result_text += f"*تم الإرسال بنجاح إلى:* {success_count} مستخدم\n"
        result_text += f"*فشل الإرسال إلى:* {fail_count} مستخدم"
        
        await query.edit_message_text(
            text=result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
            ])
        )
        
        # تنظيف البيانات
        context.user_data.pop('broadcast_text', None)
        return ADMIN_PANEL
    
    async def handle_vip_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة رفع محاضرة VIP"""
        query = update.callback_query
        
        await query.edit_message_text(
            text="📤 *رفع محاضرة VIP*\n\n"
                 "أرسل الفيديو الآن (حتى 100 ميجابايت):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data='vip_lectures')]
            ])
        )
        return VIP_UPLOAD_LECTURE
    
    async def process_vip_lecture_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة استلام محاضرة VIP"""
        user_id = update.effective_user.id
        
        if not update.message.video and not update.message.document:
            await update.message.reply_text("⚠️ الرجاء إرسال ملف فيديو")
            return VIP_UPLOAD_LECTURE
        
        # التحقق من حجم الملف
        file_size = 0
        if update.message.video:
            file_size = update.message.video.file_size
            file_id = update.message.video.file_id
        elif update.message.document:
            file_size = update.message.document.file_size
            file_id = update.message.document.file_id
        
        if file_size > 100 * 1024 * 1024:  # 100 MB
            await update.message.reply_text("⚠️ حجم الملف كبير جداً! الحد الأقصى 100 ميجابايت")
            return VIP_UPLOAD_LECTURE
        
        # حفظ بيانات الملف
        context.user_data['vip_lecture_file_id'] = file_id
        
        await update.message.reply_text(
            "📝 *أدخل عنوان المحاضرة:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data='vip_lectures')]
            ])
        )
        return VIP_UPLOAD_LECTURE + 1
    
    async def process_vip_lecture_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة عنوان المحاضرة"""
        title = update.message.text
        context.user_data['vip_lecture_title'] = title
        
        await update.message.reply_text(
            "📝 *أدخل وصف المحاضرة:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data='vip_lectures')]
            ])
        )
        return VIP_UPLOAD_LECTURE + 2
    
    async def process_vip_lecture_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة وصف المحاضرة"""
        description = update.message.text
        context.user_data['vip_lecture_description'] = description
        
        keyboard = [
            [InlineKeyboardButton("💰 مدفوعة", callback_data='lecture_paid'),
             InlineKeyboardButton("🆓 مجانية", callback_data='lecture_free')],
            [InlineKeyboardButton("🔙 إلغاء", callback_data='vip_lectures')]
        ]
        
        await update.message.reply_text(
            "💰 *اختر نوع المحاضرة:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return VIP_UPLOAD_LECTURE + 3
    
    async def process_vip_lecture_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة سعر المحاضرة"""
        query = update.callback_query
        
        if query.data == 'lecture_free':
            price = 0
        else:
            await query.edit_message_text(
                "💰 *أدخل سعر المحاضرة (بالدينار العراقي):*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 إلغاء", callback_data='vip_lectures')]
                ])
            )
            context.user_data['awaiting_lecture_price'] = True
            return VIP_SET_PRICE
        
        # حفظ المحاضرة
        await self.save_vip_lecture(query, context, price)
        return MAIN_MENU
    
    async def handle_vip_lecture_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة استلام سعر المحاضرة"""
        try:
            price = int(update.message.text)
            
            if price < 0:
                await update.message.reply_text("⚠️ السعر يجب أن يكون صفر أو أكثر")
                return VIP_SET_PRICE
            
            # حفظ المحاضرة
            await self.save_vip_lecture(update, context, price)
            return MAIN_MENU
        
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح")
            return VIP_SET_PRICE
    
    async def save_vip_lecture(self, update: Any, context: ContextTypes.DEFAULT_TYPE, price: int):
        """حفظ محاضرة VIP في قاعدة البيانات"""
        user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.from_user.id
        
        # جمع البيانات
        file_id = context.user_data.get('vip_lecture_file_id')
        title = context.user_data.get('vip_lecture_title')
        description = context.user_data.get('vip_lecture_description')
        
        if not all([file_id, title, description]):
            await self.send_reply(update, "⚠️ حدث خطأ في البيانات!")
            return
        
        # حفظ في قاعدة البيانات
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO vip_lectures (teacher_id, title, description, video_path, price, is_approved)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (user_id, title, description, file_id, price))
        lecture_id = cursor.lastrowid
        self.db.conn.commit()
        
        # تنظيف البيانات
        for key in ['vip_lecture_file_id', 'vip_lecture_title', 'vip_lecture_description', 'awaiting_lecture_price']:
            context.user_data.pop(key, None)
        
        # إرسال إشعار للمدير
        admin_text = f"🎬 *محاضرة VIP جديدة تحتاج موافقة*\n\n"
        admin_text += f"*المحاضر:* {update.effective_user.first_name if hasattr(update, 'effective_user') else update.from_user.first_name}\n"
        admin_text += f"*العنوان:* {title}\n"
        admin_text += f"*السعر:* {self.format_currency(price)}\n"
        admin_text += f"*الوصف:* {description[:200]}...\n\n"
        admin_text += f"*رقم المحاضرة:* {lecture_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ موافقة", callback_data=f'vip_approve_{lecture_id}'),
                InlineKeyboardButton("❌ رفض", callback_data=f'vip_reject_{lecture_id}')
            ],
            [InlineKeyboardButton("👀 عرض المحاضرة", callback_data=f'vip_view_{lecture_id}')]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # إعلام المستخدم
        await self.send_reply(update,
            "✅ *تم رفع المحاضرة بنجاح!*\n\n"
            "سيتم مراجعتها من قبل الإدارة ونشرها قريباً.\n"
            "ستصلك إشعار عند الموافقة على المحاضرة.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎓 محاضرات VIP", callback_data='vip_lectures'),
                 InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
            ])
        )
    
    async def send_reply(self, update: Any, text: str, **kwargs):
        """إرسال رد مناسب سواء كان رسالة أو callback"""
        if hasattr(update, 'message'):
            await update.message.reply_text(text, **kwargs)
        elif hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(text, **kwargs)
        elif hasattr(update, 'edit_message_text'):
            await update.edit_message_text(text, **kwargs)
    
    async def approve_vip_lecture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: int):
        """الموافقة على محاضرة VIP"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('UPDATE vip_lectures SET is_approved = 1 WHERE lecture_id = ?', (lecture_id,))
        self.db.conn.commit()
        
        # الحصول على بيانات المحاضرة
        cursor.execute('SELECT teacher_id, title FROM vip_lectures WHERE lecture_id = ?', (lecture_id,))
        lecture = cursor.fetchone()
        
        if lecture:
            teacher_id, title = lecture
            
            # إرسال إشعار للمحاضر
            try:
                await context.bot.send_message(
                    chat_id=teacher_id,
                    text=f"✅ *تمت الموافقة على محاضرتك*\n\n"
                         f"*العنوان:* {title}\n\n"
                         f"يمكن للمستخدمين الآن مشاهدة وشراء محاضرتك.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        await query.edit_message_text(
            text="✅ تمت الموافقة على المحاضرة",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
            ])
        )
    
    async def reject_vip_lecture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: int):
        """رفض محاضرة VIP"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT teacher_id, title FROM vip_lectures WHERE lecture_id = ?', (lecture_id,))
        lecture = cursor.fetchone()
        
        if lecture:
            teacher_id, title = lecture
            
            # إرسال إشعار للمحاضر
            try:
                await context.bot.send_message(
                    chat_id=teacher_id,
                    text=f"❌ *تم رفض محاضرتك*\n\n"
                         f"*العنوان:* {title}\n\n"
                         f"للمزيد من المعلومات، راسل الدعم الفني.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        cursor.execute('DELETE FROM vip_lectures WHERE lecture_id = ?', (lecture_id,))
        self.db.conn.commit()
        
        await query.edit_message_text(
            text="❌ تم رفض المحاضرة",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data='admin_panel')]
            ])
        )
    
    async def show_pending_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الأسئلة المنتظرة للموافقة"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT q.question_id, q.question_text, u.first_name, u.user_id, q.ask_date
            FROM help_questions q
            JOIN users u ON q.user_id = u.user_id
            WHERE q.is_approved = 0
            ORDER BY q.ask_date
        ''')
        questions = cursor.fetchall()
        
        if not questions:
            text = "❓ *الأسئلة المنتظرة*\n\n"
            text += "لا توجد أسئلة تحتاج موافقة."
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]]
        else:
            text = "❓ *الأسئلة المنتظرة*\n\n"
            
            keyboard = []
            
            for q_id, q_text, name, u_id, date in questions:
                text += f"*السؤال {q_id}:*\n"
                text += f"{q_text[:100]}...\n"
                text += f"من: {name} ({u_id})\n"
                text += f"التاريخ: {date[:16]}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"✅ {q_id}", callback_data=f'approve_help_{q_id}'),
                    InlineKeyboardButton(f"❌ {q_id}", callback_data=f'reject_help_{q_id}'),
                    InlineKeyboardButton(f"👁️ {q_id}", callback_data=f'view_help_{q_id}')
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def approve_help_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int):
        """الموافقة على سؤال مساعدة"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('UPDATE help_questions SET is_approved = 1 WHERE question_id = ?', (question_id,))
        self.db.conn.commit()
        
        # الحصول على بيانات السؤال
        cursor.execute('SELECT user_id, question_text FROM help_questions WHERE question_id = ?', (question_id,))
        question = cursor.fetchone()
        
        if question:
            user_id, q_text = question
            
            # إرسال إشعار للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ *تمت الموافقة على سؤالك*\n\n"
                         f"*السؤال:* {q_text[:200]}...\n\n"
                         f"يمكن للطلاب الآن الإجابة على سؤالك.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        await query.edit_message_text(
            text="✅ تمت الموافقة على السؤال",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 الأسئلة المنتظرة", callback_data='admin_pending_questions')]
            ])
        )
    
    async def reject_help_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int):
        """رفض سؤال مساعدة"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT user_id, question_text FROM help_questions WHERE question_id = ?', (question_id,))
        question = cursor.fetchone()
        
        if question:
            user_id, q_text = question
            
            # إرسال إشعار للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ *تم رفض سؤالك*\n\n"
                         f"*السؤال:* {q_text[:200]}...\n\n"
                         f"للمزيد من المعلومات، راسل الدعم الفني.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        cursor.execute('DELETE FROM help_questions WHERE question_id = ?', (question_id,))
        self.db.conn.commit()
        
        await query.edit_message_text(
            text="❌ تم رفض السؤال",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 الأسئلة المنتظرة", callback_data='admin_pending_questions')]
            ])
        )
    
    async def start_answering_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int):
        """بدء الإجابة على سؤال"""
        query = update.callback_query
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT question_text FROM help_questions WHERE question_id = ?', (question_id,))
        question = cursor.fetchone()
        
        if not question:
            await query.edit_message_text("⚠️ السؤال غير موجود")
            return MAIN_MENU
        
        q_text = question[0]
        
        context.user_data['answering_question_id'] = question_id
        
        await query.edit_message_text(
            text=f"✏️ *الإجابة على السؤال*\n\n"
                 f"*السؤال:* {q_text}\n\n"
                 f"أرسل إجابتك الآن:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 إلغاء", callback_data='main_menu')]
            ])
        )
        return HELP_STUDENT_ANSWER
    
    async def process_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الإجابة على سؤال"""
        answer_text = update.message.text
        question_id = context.user_data.get('answering_question_id')
        
        if not question_id:
            await update.message.reply_text("⚠️ حدث خطأ في البيانات")
            return MAIN_MENU
        
        if not answer_text or len(answer_text) < 5:
            await update.message.reply_text("⚠️ الإجابة قصيرة جداً")
            return HELP_STUDENT_ANSWER
        
        # حفظ الإجابة
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE help_questions 
            SET answer_text = ?, answerer_id = ?, is_answered = 1, answer_date = CURRENT_TIMESTAMP
            WHERE question_id = ?
        ''', (answer_text, update.effective_user.id, question_id))
        self.db.conn.commit()
        
        # الحصول على بيانات السؤال
        cursor.execute('SELECT user_id, question_text FROM help_questions WHERE question_id = ?', (question_id,))
        question = cursor.fetchone()
        
        if question:
            user_id, q_text = question
            
            # إرسال الإجابة للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ *تمت الإجابة على سؤالك*\n\n"
                         f"*سؤالك:* {q_text[:200]}...\n\n"
                         f"*الإجابة:*\n{answer_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        # تنظيف البيانات
        context.user_data.pop('answering_question_id', None)
        
        await update.message.reply_text(
            "✅ تم إرسال الإجابة بنجاح!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 المزيد من الأسئلة", callback_data='service_help'),
                 InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
            ])
        )
        return MAIN_MENU
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء العملية الحالية"""
        await update.message.reply_text(
            "تم الإلغاء.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
            ])
        )
        return MAIN_MENU
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأخطاء"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update.effective_user:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="⚠️ حدث خطأ غير متوقع. تم إبلاغ الإدارة.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
                    ])
                )
        except:
            pass

# الدالة الرئيسية لتشغيل البوت
def main():
    """تشغيل البوت"""
    print("🚀 بدء تشغيل بوت يلا نتعلم...")
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # إنشاء كائن البوت
    bot = LearnBot()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("admin", bot.show_admin_panel))
    
    # إضافة معالجات ردود الاتصال
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # إضافة معالجات المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", bot.start_command)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(bot.handle_callback),
            ],
            ADMIN_PANEL: [
                CallbackQueryHandler(bot.handle_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id),
            ],
            EXEMPTION_STEP1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_exemption_step1),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            EXEMPTION_STEP2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_exemption_step2),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            EXEMPTION_STEP3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_exemption_step3),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            UPLOAD_PDF: [
                MessageHandler(filters.Document.ALL | filters.TEXT, bot.handle_pdf_upload),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            ASK_QUESTION: [
                MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, bot.handle_question),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            HELP_STUDENT_ASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.process_help_question),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            HELP_STUDENT_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.process_answer),
                CallbackQueryHandler(bot.handle_callback, pattern='^main_menu$'),
            ],
            VIP_UPLOAD_LECTURE: [
                MessageHandler(filters.VIDEO | filters.Document.ALL, bot.process_vip_lecture_upload),
                CallbackQueryHandler(bot.handle_callback, pattern='^vip_lectures$'),
            ],
            VIP_UPLOAD_LECTURE + 1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.process_vip_lecture_title),
                CallbackQueryHandler(bot.handle_callback, pattern='^vip_lectures$'),
            ],
            VIP_UPLOAD_LECTURE + 2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.process_vip_lecture_description),
                CallbackQueryHandler(bot.handle_callback, pattern='^vip_lectures$'),
            ],
            VIP_UPLOAD_LECTURE + 3: [
                CallbackQueryHandler(bot.process_vip_lecture_price),
                CallbackQueryHandler(bot.handle_callback, pattern='^vip_lectures$'),
            ],
            VIP_SET_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_vip_lecture_price),
                CallbackQueryHandler(bot.handle_callback, pattern='^vip_lectures$'),
            ],
            ADMIN_CHARGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_CHARGE + 1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_amount),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_DEDUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_DEDUCT + 1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_amount),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_BAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_UNBAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_broadcast),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
            ADMIN_BROADCAST + 1: [
                CallbackQueryHandler(bot.confirm_broadcast, pattern='^confirm_broadcast$'),
                CallbackQueryHandler(bot.handle_callback, pattern='^admin_panel$'),
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # إضافة معالج الأخطاء
    application.add_error_handler(bot.error_handler)
    
    # بدء البوت
    print("✅ البوت جاهز للتشغيل!")
    print(f"📊 اسم البوت: {BOT_USERNAME}")
    print(f"👑 المدير: {ADMIN_ID}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
