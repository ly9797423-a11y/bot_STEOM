#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت "يلا نتعلم" - البوت التعليمي للطلاب العراقيين
المطور: Allawi04@
"""

import logging
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import PyPDF2
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
from telegram.constants import ParseMode
import google.generativeai as genai

# ============= إعدادات البوت =============
TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
SUPPORT_USERNAME = "Allawi04"
GEMINI_API_KEY = "AIzaSyAqlug21bw_eI60ocUtc1Z76NhEUc-zuzY"

# ============= حالات المحادثة =============
(
    ADMIN_MENU, CHARGE_USER, CHARGE_AMOUNT, PRICE_CHANGE, 
    MATERIAL_FILE, MATERIAL_DESC, MATERIAL_STAGE, 
    QUESTION_DETAILS, QUESTION_ANSWER, BAN_USER,
    CHANGE_CHANNEL
) = range(11)

# ============= إعداد التسعير =============
SERVICE_PRICES = {
    "exemption": 1000,      # حساب درجة الإعفاء
    "summarize": 1000,      # تلخيص الملازم
    "qa": 1000,             # سؤال وجواب
    "materials": 1000,      # ملازمي ومرشحاتي
    "help_student": 250     # ساعدوني طلاب (جديد)
}
WELCOME_BONUS = 1000        # هدية الترحيب
REFERRAL_BONUS = 500        # مكافأة الدعوة
ANSWER_REWARD = 100         # مكافأة الإجابة على سؤال طالب

# ============= إعداد الملفات =============
DATA_FILE = "users_data.json"
MATERIALS_FILE = "materials_data.json"
ADMIN_FILE = "admin_settings.json"
QUESTIONS_FILE = "questions_data.json"
BANNED_FILE = "banned_users.json"
CHANNEL_FILE = "channel_info.json"

# ============= إعداد التسجيل =============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= إدارة البيانات =============
class DataManager:
    @staticmethod
    def load_data(filename: str, default=None):
        """تحميل البيانات من ملف JSON"""
        if default is None:
            default = {}
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return default
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return default

    @staticmethod
    def save_data(filename: str, data):
        """حفظ البيانات إلى ملف JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")

# ============= إدارة المستخدمين =============
class UserManager:
    def __init__(self):
        self.users = DataManager.load_data(DATA_FILE, {})
        self.banned_users = DataManager.load_data(BANNED_FILE, {})
        
    def get_user(self, user_id: int) -> Dict:
        """الحصول على بيانات المستخدم أو إنشاء مستخدم جديد"""
        user_id_str = str(user_id)
        
        # التحقق من الحظر
        if user_id_str in self.banned_users:
            return self.banned_users[user_id_str]
        
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                "balance": WELCOME_BONUS,
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "referral_code": str(user_id),
                "invited_by": None,
                "invited_users": [],
                "transactions": [],
                "exemption_scores": [],
                "used_services": [],
                "pending_scores": [],
                "questions_asked": 0,
                "questions_answered": 0,
                "total_earned": 0,
                "last_question_time": None,
                "pending_purchase": None  # تخزين عملية شراء معلقة
            }
            self.save_users()
            logger.info(f"New user created: {user_id}")
        return self.users[user_id_str]
    
    def can_ask_question(self, user_id: int) -> bool:
        """التحقق إذا كان يمكن للمستخدم طرح سؤال (مرة كل 24 ساعة)"""
        user = self.get_user(user_id)
        last_question = user.get("last_question_time")
        
        if not last_question:
            return True
        
        try:
            last_time = datetime.strptime(last_question, "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_time
            return time_diff.total_seconds() >= 86400  # 24 ساعة
        except:
            return True
    
    def update_question_time(self, user_id: int):
        """تحديث وقت آخر سؤال"""
        user = self.get_user(user_id)
        user["last_question_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_users()
    
    def update_balance(self, user_id: int, amount: int, description: str = "") -> int:
        """تحديد رصيد المستخدم"""
        user = self.get_user(user_id)
        user["balance"] = user.get("balance", 0) + amount
        
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "description": description,
            "balance_after": user["balance"]
        }
        user.setdefault("transactions", []).append(transaction)
        
        # تحديث إجمالي الأرباح إذا كان المبلغ موجباً
        if amount > 0:
            user["total_earned"] = user.get("total_earned", 0) + amount
        
        self.save_users()
        logger.info(f"Updated balance for user {user_id}: +{amount} = {user['balance']}")
        return user["balance"]
    
    def set_pending_purchase(self, user_id: int, service: str, price: int):
        """تعيين عملية شراء معلقة"""
        user = self.get_user(user_id)
        user["pending_purchase"] = {
            "service": service,
            "price": price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_users()
    
    def complete_purchase(self, user_id: int):
        """إكمال عملية الشراء"""
        user = self.get_user(user_id)
        if user.get("pending_purchase"):
            purchase = user["pending_purchase"]
            # تسجيل الخدمة المستخدمة
            user.setdefault("used_services", []).append({
                "service": purchase["service"],
                "date": purchase["timestamp"],
                "cost": purchase["price"]
            })
            user["pending_purchase"] = None
            self.save_users()
            return True
        return False
    
    def cancel_purchase(self, user_id: int):
        """إلغاء عملية الشراء"""
        user = self.get_user(user_id)
        if user.get("pending_purchase"):
            # استرجاع المبلغ
            purchase = user["pending_purchase"]
            self.update_balance(user_id, purchase["price"], f"استرجاع رصيد لخدمة: {purchase['service']}")
            user["pending_purchase"] = None
            self.save_users()
            return True
        return False
    
    def save_users(self):
        """حفظ بيانات المستخدمين"""
        DataManager.save_data(DATA_FILE, self.users)

# ============= إدارة القناة =============
class ChannelManager:
    def __init__(self):
        self.channel_info = DataManager.load_data(CHANNEL_FILE, {
            "channel_link": "https://t.me/FCJCV",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def get_channel_link(self) -> str:
        """الحصول على رابط القناة"""
        return self.channel_info.get("channel_link", "https://t.me/FCJCV")
    
    def update_channel_link(self, new_link: str):
        """تحديث رابط القناة"""
        self.channel_info["channel_link"] = new_link
        self.channel_info["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_channel_info()
    
    def save_channel_info(self):
        """حفظ معلومات القناة"""
        DataManager.save_data(CHANNEL_FILE, self.channel_info)

# ============= الفئة الرئيسية للبوت =============
class YallaNataalamBot:
    def __init__(self):
        self.user_manager = UserManager()
        self.channel_manager = ChannelManager()
        self.settings = DataManager.load_data(ADMIN_FILE, {
            "maintenance": False,
            "prices": SERVICE_PRICES.copy(),
            "welcome_bonus": WELCOME_BONUS,
            "referral_bonus": REFERRAL_BONUS,
            "answer_reward": ANSWER_REWARD,
            "notify_new_users": True
        })
        logger.info("Bot initialized successfully")
        
        # إعداد الذكاء الاصطناعي
        self.setup_ai()
    
    def setup_ai(self):
        """إعداد الذكاء الاصطناعي مع تحسينات"""
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # تجربة نماذج مختلفة
            models_to_try = [
                'gemini-1.5-pro-latest',
                'gemini-1.0-pro-latest',
                'gemini-pro',
                'models/gemini-pro'
            ]
            
            self.model = None
            for model_name in models_to_try:
                try:
                    logger.info(f"Trying model: {model_name}")
                    self.model = genai.GenerativeModel(model_name)
                    # اختبار النموذج
                    test_response = self.model.generate_content("Test")
                    logger.info(f"Successfully configured model: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Failed with model {model_name}: {e}")
                    continue
            
            if not self.model:
                logger.error("All AI models failed to initialize")
                self.model = None
                
        except Exception as e:
            logger.error(f"Failed to configure Gemini AI: {e}")
            self.model = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء البوت"""
        user = update.effective_user
        user_data = self.user_manager.get_user(user.id)
        
        # إظهار ID المستخدم في الترحيب
        welcome_message = f"""
🎓 <b>مرحباً {user.first_name}!</b>

أهلاً بك في بوت "يلا نتعلم" 🤖

🆔 <b>رقم حسابك:</b> <code>{user.id}</code>
💰 <b>رصيدك الحالي:</b> {user_data['balance']} دينار عراقي

🎁 <b>هدية ترحيبية:</b> {self.settings['welcome_bonus']} دينار

📝 <b>ملاحظة:</b> يمكنك نسخ رقم حسابك أعلاه واستخدامه للشحن

اختر الخدمة التي تريدها:
"""
        
        keyboard = [
            [InlineKeyboardButton("🧮 حساب درجة الإعفاء", callback_data="service_exemption")],
            [InlineKeyboardButton("📚 تلخيص الملازم", callback_data="service_summarize")],
            [InlineKeyboardButton("❓ سؤال وجواب بالذكاء", callback_data="service_qa")],
            [InlineKeyboardButton("📖 ملازمي ومرشحاتي", callback_data="service_materials")],
            [InlineKeyboardButton("🤝 ساعدوني طلاب (250 دينار)", callback_data="service_help_student")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
             InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
            [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite"),
             InlineKeyboardButton("📢 قناة البوت", url=self.channel_manager.get_channel_link())],
            [InlineKeyboardButton("🆘 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME}")],
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار الخدمة"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        service = query.data.replace("service_", "")
        
        # التحقق من الرصيد فقط دون خصم
        user_data = self.user_manager.get_user(user_id)
        price = SERVICE_PRICES.get(service, 1000)
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي لهذه الخدمة!</b>\n\n"
                f"💰 سعر الخدمة: {price} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>\n\n"
                f"📞 تواصل مع الدعم الفني للشحن: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        if service == "exemption":
            # تعيين عملية شراء معلقة
            self.user_manager.set_pending_purchase(user_id, service, price)
            await self.show_exemption_calculator(query)
        
        elif service == "summarize":
            self.user_manager.set_pending_purchase(user_id, service, price)
            await query.edit_message_text(
                "📤 <b>أرسل ملف PDF المراد تلخيصه</b>\n\n"
                f"💰 سعر الخدمة: {price} دينار\n"
                "⏳ قد تستغرق العملية بضع دقائق\n\n"
                "⚠️ <b>سيتم خصم المبلغ بعد إتمام الخدمة</b>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['awaiting_pdf'] = True
        
        elif service == "qa":
            self.user_manager.set_pending_purchase(user_id, service, price)
            await query.edit_message_text(
                "❓ <b>أرسل سؤالك الآن</b>\n\n"
                f"💰 سعر الخدمة: {price} دينار\n"
                "⏳ جاهز للإجابة على أسئلتك\n\n"
                "⚠️ <b>سيتم خصم المبلغ بعد إتمام الخدمة</b>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['awaiting_question'] = True
        
        elif service == "materials":
            await self.show_materials_menu(query)
        
        elif service == "help_student":
            await self.handle_help_student(query, context)
    
    async def handle_exemption_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة حساب درجة الإعفاء"""
        user_id = update.effective_user.id
        
        try:
            text = update.message.text.strip()
            
            if len(text.split()) >= 3:
                scores = list(map(float, text.split()[:3]))
                
                # حساب النتيجة
                average = sum(scores) / 3
                
                if average >= 90:
                    message = f"""
🎉 <b>تهانينا! تم إعفاؤك من المادة</b> 🎉

📊 <b>درجاتك:</b>
الكورس الأول: {scores[0]}
الكورس الثاني: {scores[1]}  
الكورس الثالث: {scores[2]}

🧮 <b>المعدل:</b> {average:.2f}

✅ <b>أنت معفي من المادة</b>
"""
                else:
                    message = f"""
📊 <b>درجاتك:</b>
الكورس الأول: {scores[0]}
الكورس الثاني: {scores[1]}
الكورس الثالث: {scores[2]}

🧮 <b>المعدل:</b> {average:.2f}

⚠️ <b>المعدل أقل من 90</b>
❌ <b>لم تحصل على الإعفاء</b>
"""
                
                # إكمال عملية الشراء
                self.user_manager.complete_purchase(user_id)
                user_data = self.user_manager.get_user(user_id)
                
                message += f"\n💰 تم خصم: {SERVICE_PRICES['exemption']} دينار"
                message += f"\n💳 رصيدك المتبقي: {user_data['balance']} دينار"
                
                await update.message.reply_text(message, parse_mode=ParseMode.HTML)
                
                # حفظ الدرجات
                user_data.setdefault("exemption_scores", []).append({
                    "scores": scores,
                    "average": average,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "exempted": average >= 90
                })
                self.user_manager.save_users()
                
            else:
                await update.message.reply_text("⚠️ يجب إدخال 3 درجات")
                
        except ValueError:
            await update.message.reply_text("⚠️ أدخل أرقاماً صحيحة فقط")
        except Exception as e:
            logger.error(f"Error in exemption calculation: {e}")
            await update.message.reply_text("❌ حدث خطأ في الحساب. حاول مرة أخرى")
            # إلغاء الشراء في حالة الخطأ
            self.user_manager.cancel_purchase(user_id)
    
    async def handle_pdf_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ملف PDF للتلخيص بالذكاء الاصطناعي"""
        user_id = update.effective_user.id
        
        if not context.user_data.get('awaiting_pdf'):
            return
        
        document = update.message.document
        if not document.mime_type == 'application/pdf':
            await update.message.reply_text("❌ يرجى إرسال ملف PDF فقط")
            return
        
        await update.message.reply_text("⏳ جاري تحميل الملف...")
        
        try:
            # تحميل الملف
            file = await document.get_file()
            pdf_path = f"temp_{user_id}.pdf"
            await file.download_to_drive(pdf_path)
            
            await update.message.reply_text("📖 جاري قراءة الملف وتلخيصه...")
            
            # استخراج النص
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if len(text) < 100:
                await update.message.reply_text("❌ الملف فارغ أو لا يحتوي على نص قابل للقراءة")
                os.remove(pdf_path)
                context.user_data['awaiting_pdf'] = False
                self.user_manager.cancel_purchase(user_id)
                return
            
            # استخدام الذكاء الاصطناعي للتلخيص
            if self.model:
                await update.message.reply_text("🤖 جاري التلخيص بالذكاء الاصطناعي...")
                
                try:
                    prompt = f"""
                    قم بتلخيص النص التعليمي التالي بشكل احترافي:
                    
                    {text[:3000]}
                    
                    التلخيص يجب أن يكون:
                    1. باللغة العربية الفصحى
                    2. يركز على النقاط الرئيسية
                    3. منظم في نقاط واضحة
                    4. يحافظ على المعلومات المهمة
                    """
                    
                    response = self.model.generate_content(prompt)
                    summary = response.text
                    
                except Exception as e:
                    logger.error(f"AI summarization error: {e}")
                    summary = "❌ حدث خطأ في خدمة الذكاء الاصطناعي. تم استرجاع المبلغ."
                    self.user_manager.cancel_purchase(user_id)
            else:
                summary = "❌ خدمة الذكاء الاصطناعي غير متاحة حالياً. تم استرجاع المبلغ."
                self.user_manager.cancel_purchase(user_id)
            
            # إنشاء ملف PDF جديد
            await update.message.reply_text("📄 جاري إنشاء ملف PDF جديد...")
            
            output_path = f"summary_{user_id}.pdf"
            success = False
            
            try:
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "تلخيص الملزمة التعليمية")
                
                c.setFont("Helvetica", 12)
                y_position = height - 100
                
                # تقطيع التلخيص
                summary_lines = summary.split('\n')
                for line in summary_lines:
                    if y_position < 100:
                        c.showPage()
                        y_position = height - 50
                        c.setFont("Helvetica", 12)
                    
                    # معالجة النص العربي
                    try:
                        reshaped_text = arabic_reshaper.reshape(line)
                        bidi_text = get_display(reshaped_text)
                        display_text = bidi_text[:80]
                    except:
                        display_text = line[:80]
                    
                    c.drawString(50, y_position, display_text)
                    y_position -= 20
                
                c.save()
                success = True
                
            except Exception as e:
                logger.error(f"PDF creation error: {e}")
                success = False
            
            if success and not summary.startswith("❌"):
                # إكمال عملية الشراء
                self.user_manager.complete_purchase(user_id)
                user_data = self.user_manager.get_user(user_id)
                
                await update.message.reply_document(
                    document=open(output_path, 'rb'),
                    caption=f"✅ <b>تم تلخيص الملزمة بنجاح</b>\n\n"
                           f"💰 تم خصم: {SERVICE_PRICES['summarize']} دينار\n"
                           f"💳 رصيدك المتبقي: {user_data['balance']} دينار",
                    parse_mode=ParseMode.HTML
                )
                
                os.remove(pdf_path)
                os.remove(output_path)
            else:
                await update.message.reply_text(
                    f"📝 <b>ملخص النص:</b>\n\n{summary[:1500]}\n\n"
                    f"⚠️ <b>ملاحظة:</b> لم يتم خصم أي مبلغ بسبب مشكلة تقنية",
                    parse_mode=ParseMode.HTML
                )
                os.remove(pdf_path)
        
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            await update.message.reply_text(f"❌ حدث خطأ في معالجة الملف")
            self.user_manager.cancel_purchase(user_id)
        
        context.user_data['awaiting_pdf'] = False
    
    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأسئلة بالذكاء الاصطناعي"""
        user_id = update.effective_user.id
        
        if not context.user_data.get('awaiting_question'):
            return
        
        question = update.message.text.strip()
        
        if len(question) < 5:
            await update.message.reply_text("❌ السؤال قصير جداً. يرجى كتابة سؤال مفصل")
            return
        
        await update.message.reply_text("🤖 جاري البحث عن الإجابة...")
        
        try:
            # استخدام الذكاء الاصطناعي
            answer = "❌ خدمة الذكاء الاصطناعي غير متاحة حالياً"
            
            if self.model:
                try:
                    prompt = f"""
                    أنت مساعد تعليمي للطلاب العراقيين. أجب على السؤال التالي:
                    
                    السؤال: {question}
                    
                    المتطلبات:
                    1. قدم إجابة شاملة ومفيدة
                    2. استخدم أمثلة إذا لزم الأمر
                    3. كن واضحاً ودقيقاً
                    4. استخدم اللغة العربية الفصحى
                    """
                    
                    response = self.model.generate_content(prompt)
                    answer = response.text
                    
                    # إكمال عملية الشراء
                    self.user_manager.complete_purchase(user_id)
                    user_data = self.user_manager.get_user(user_id)
                    
                except Exception as e:
                    logger.error(f"AI question answering error: {e}")
                    answer = "❌ حدث خطأ في خدمة الذكاء الاصطناعي"
                    self.user_manager.cancel_purchase(user_id)
            else:
                self.user_manager.cancel_purchase(user_id)
            
            if answer.startswith("❌"):
                await update.message.reply_text(
                    f"{answer}\n\n⚠️ <b>تم استرجاع المبلغ</b>",
                    parse_mode=ParseMode.HTML
                )
            else:
                user_data = self.user_manager.get_user(user_id)
                await update.message.reply_text(
                    f"❓ <b>سؤالك:</b>\n{question}\n\n"
                    f"💡 <b>الإجابة:</b>\n{answer[:3000]}\n\n"
                    f"💰 تم خصم: {SERVICE_PRICES['qa']} دينار\n"
                    f"💳 رصيدك المتبقي: {user_data['balance']} دينار",
                    parse_mode=ParseMode.HTML
                )
        
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            await update.message.reply_text(f"❌ حدث خطأ في الإجابة")
            self.user_manager.cancel_purchase(user_id)
        
        context.user_data['awaiting_question'] = False
    
    async def handle_help_student(self, query, context: ContextTypes.DEFAULT_TYPE):
        """معالجة خدمة ساعدوني طلاب"""
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        # التحقق إذا كان يمكن طرح سؤال (مرة كل 24 ساعة)
        if not self.user_manager.can_ask_question(user_id):
            last_time = user_data.get("last_question_time", "غير معروف")
            await query.edit_message_text(
                f"⏳ <b>لا يمكنك طرح سؤال جديد الآن</b>\n\n"
                f"📅 <b>آخر سؤال:</b> {last_time}\n"
                f"⏰ <b>المتبقي:</b> يمكنك طرح سؤال جديد بعد 24 ساعة من آخر سؤال\n\n"
                f"💡 <b>نصيحة:</b> يمكنك الإجابة على أسئلة الآخرين وكسب 100 نقطة",
                parse_mode=ParseMode.HTML
            )
            return
        
        price = SERVICE_PRICES['help_student']
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي!</b>\n\n"
                f"💰 سعر الخدمة: {price} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # تعيين عملية شراء معلقة
        self.user_manager.set_pending_purchase(user_id, "help_student", price)
        
        await query.edit_message_text(
            "🤝 <b>ساعدوني طلاب</b>\n\n"
            f"💰 سعر الخدمة: {price} دينار\n"
            f"💳 رصيدك الحالي: {user_data['balance']} دينار\n\n"
            "📝 <b>أرسل سؤالك الآن:</b>\n"
            "• يمكنك إرسال نص فقط\n"
            "• السؤال يجب أن يكون متعلقاً بالدراسة\n"
            "• سوف يتم خصم المبلغ بعد إرسال السؤال\n\n"
            "⚠️ <b>ملاحظة:</b> يمكنك طرح سؤال واحد كل 24 ساعة",
            parse_mode=ParseMode.HTML
        )
        
        context.user_data['awaiting_help_question'] = True
    
    async def handle_help_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة سؤال خدمة ساعدوني طلاب"""
        user_id = update.effective_user.id
        
        if not context.user_data.get('awaiting_help_question'):
            return
        
        question_text = update.message.text.strip()
        
        if len(question_text) < 10:
            await update.message.reply_text("❌ السؤال قصير جداً. يرجى كتابة سؤال مفصل")
            return
        
        # إكمال عملية الشراء
        self.user_manager.complete_purchase(user_id)
        
        # تحديث وقت آخر سؤال
        self.user_manager.update_question_time(user_id)
        
        # حفظ السؤال
        questions = DataManager.load_data(QUESTIONS_FILE, [])
        question_id = len(questions) + 1
        
        questions.append({
            "id": question_id,
            "user_id": user_id,
            "question": question_text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "answers": [],
            "answered": False
        })
        
        DataManager.save_data(QUESTIONS_FILE, questions)
        
        user_data = self.user_manager.get_user(user_id)
        
        await update.message.reply_text(
            f"✅ <b>تم إضافة سؤالك بنجاح!</b>\n\n"
            f"🆔 <b>رقم السؤال:</b> {question_id}\n"
            f"💰 <b>تم خصم:</b> {SERVICE_PRICES['help_student']} دينار\n"
            f"💳 <b>رصيدك المتبقي:</b> {user_data['balance']} دينار\n\n"
            f"⏳ <b>الحالة:</b> في انتظار الإجابة\n"
            f"🎯 <b>المكافأة للمجيب:</b> {ANSWER_REWARD} نقطة\n\n"
            f"💡 سوف تتلقى إشعاراً عندما يتم الرد على سؤالك",
            parse_mode=ParseMode.HTML
        )
        
        context.user_data['awaiting_help_question'] = False
        
        # عرض زر للعودة للقائمة
        keyboard = [[InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="back_home")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔍 <b>يمكنك الآن:</b>\n"
            "• العودة للقائمة الرئيسية\n"
            "• أو انتظار الإجابة على سؤالك",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    # ============= لوحة التحكم =============
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فتح لوحة التحكم"""
        if isinstance(update, Update) and update.message:
            user = update.effective_user
            message = update.message
        else:
            query = update.callback_query
            await query.answer()
            user = query.from_user
            message = query
        
        if user.id != ADMIN_ID:
            if hasattr(message, 'edit_message_text'):
                await message.edit_message_text("⛔ <b>غير مسموح لك بالدخول!</b>", parse_mode=ParseMode.HTML)
            else:
                await message.reply_text("⛔ <b>غير مسموح لك بالدخول!</b>", parse_mode=ParseMode.HTML)
            return
        
        total_users = len(self.user_manager.users)
        total_balance = sum(user.get("balance", 0) for user in self.user_manager.users.values())
        
        panel_text = f"""
👑 <b>لوحة التحكم الإدارية</b>

📊 <b>إحصائيات البوت:</b>
- عدد المستخدمين: {total_users}
- إجمالي الرصيد: {total_balance:,} دينار
- حالة البوت: {"🟢 نشط" if not self.settings['maintenance'] else "🔴 صيانة"}
- رابط القناة: {self.channel_manager.get_channel_link()}

⚙️ <b>اختر الإجراء:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("💰 شحن الرصيد", callback_data="admin_charge")],
            [InlineKeyboardButton("⚙️ تغيير الأسعار", callback_data="admin_prices")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("🛠️ إعدادات البوت", callback_data="admin_settings")],
            [InlineKeyboardButton("📢 تغيير رابط القناة", callback_data="admin_change_channel")],
            [InlineKeyboardButton("🔙 رجوع للبوت", callback_data="back_home")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message, 'edit_message_text'):
            await message.edit_message_text(panel_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(panel_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def handle_admin_change_channel(self, query, context: ContextTypes.DEFAULT_TYPE):
        """بدء تغيير رابط القناة"""
        await query.edit_message_text(
            "📢 <b>تغيير رابط قناة البوت</b>\n\n"
            f"الرابط الحالي: {self.channel_manager.get_channel_link()}\n\n"
            "🔗 <b>أرسل الرابط الجديد:</b>\n"
            "• يجب أن يبدأ بـ https://t.me/\n"
            "• مثال: https://t.me/FCJCV\n\n"
            "⚠️ سيتم تحديث الرابط فوراً",
            parse_mode=ParseMode.HTML
        )
        return CHANGE_CHANNEL
    
    async def handle_change_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال رابط القناة الجديد"""
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        new_link = update.message.text.strip()
        
        # التحقق من صحة الرابط
        if not new_link.startswith("https://t.me/"):
            await update.message.reply_text(
                "❌ <b>رابط غير صحيح!</b>\n\n"
                "🔗 يجب أن يبدأ الرابط بـ: https://t.me/\n"
                "📝 مثال صحيح: https://t.me/FCJCV\n\n"
                "أعد إرسال الرابط:",
                parse_mode=ParseMode.HTML
            )
            return CHANGE_CHANNEL
        
        # تحديث رابط القناة
        self.channel_manager.update_channel_link(new_link)
        
        await update.message.reply_text(
            f"✅ <b>تم تغيير رابط القناة بنجاح!</b>\n\n"
            f"📢 <b>الرابط الجديد:</b> {new_link}\n\n"
            f"🔗 سيظهر الرابط الجديد في واجهة المستخدم مباشرة",
            parse_mode=ParseMode.HTML
        )
        
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    async def handle_admin_charge(self, query):
        """عرض قائمة الشحن"""
        keyboard = [
            [InlineKeyboardButton("💰 شحن مستخدم", callback_data="admin_charge_user")],
            [InlineKeyboardButton("💸 خصم من مستخدم", callback_data="admin_deduct_user")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            "💰 <b>إدارة الشحن والرصيد</b>\n\n"
            "اختر نوع المعاملة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_admin_charge_user(self, query, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية شحن مستخدم"""
        await query.edit_message_text(
            "💰 <b>شحن مستخدم</b>\n\n"
            "🔢 <b>أرسل ID المستخدم:</b>\n"
            "<code>123456789</code>\n\n"
            "💡 <b>ملاحظة:</b> ID المستخدم هو الرقم الذي يظهر في واجهته",
            parse_mode=ParseMode.HTML
        )
        context.user_data['admin_action'] = 'charge_user'
        return CHARGE_USER
    
    async def handle_admin_deduct_user(self, query, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية خصم من مستخدم"""
        await query.edit_message_text(
            "💸 <b>خصم من مستخدم</b>\n\n"
            "🔢 <b>أرسل ID المستخدم:</b>\n"
            "<code>123456789</code>\n\n"
            "⚠️ <b>تحذير:</b> تأكد من صحة ID المستخدم قبل الخصم",
            parse_mode=ParseMode.HTML
        )
        context.user_data['admin_action'] = 'deduct_user'
        return CHARGE_USER
    
    async def handle_charge_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال ID المستخدم للشحن/الخصم"""
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text("❌ <b>أدخل ID صحيح</b>", parse_mode=ParseMode.HTML)
            return CHARGE_USER
        
        target_id = int(text)
        
        # التحقق من وجود المستخدم
        if str(target_id) not in self.user_manager.users:
            await update.message.reply_text(
                f"❌ <b>المستخدم غير موجود!</b>\n\n"
                f"🆔 ID: {target_id}\n\n"
                "📝 تأكد من:\n"
                "• أن المستخدم استخدم البوت من قبل\n"
                "• صحة ID المستخدم\n"
                "• يمكنك التحقق من قائمة المستخدمين",
                parse_mode=ParseMode.HTML
            )
            return CHARGE_USER
        
        context.user_data['charge_target'] = target_id
        
        action = context.user_data.get('admin_action', '')
        
        if action == 'charge_user':
            user_data = self.user_manager.get_user(target_id)
            await update.message.reply_text(
                f"✅ <b>تم تحديد المستخدم</b>\n\n"
                f"👤 المستخدم: {target_id}\n"
                f"💰 الرصيد الحالي: {user_data.get('balance', 0):,} دينار\n\n"
                f"💵 <b>أرسل المبلغ للشحن:</b>\n"
                f"<code>5000</code>",
                parse_mode=ParseMode.HTML
            )
        elif action == 'deduct_user':
            user_data = self.user_manager.get_user(target_id)
            await update.message.reply_text(
                f"✅ <b>تم تحديد المستخدم</b>\n\n"
                f"👤 المستخدم: {target_id}\n"
                f"💰 الرصيد الحالي: {user_data.get('balance', 0):,} دينار\n\n"
                f"💸 <b>أرسل المبلغ للخصم:</b>\n"
                f"<code>1000</code>",
                parse_mode=ParseMode.HTML
            )
        
        return CHARGE_AMOUNT
    
    async def handle_charge_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال المبلغ للشحن/الخصم"""
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text("❌ <b>أدخل مبلغاً صحيحاً</b>", parse_mode=ParseMode.HTML)
            return CHARGE_AMOUNT
        
        amount = int(text)
        target_id = context.user_data.get('charge_target')
        action = context.user_data.get('admin_action', '')
        
        if action == 'charge_user':
            if self.user_manager.update_balance(target_id, amount, "شحن من المدير"):
                user_data = self.user_manager.get_user(target_id)
                
                await update.message.reply_text(
                    f"✅ <b>تم الشحن بنجاح!</b>\n\n"
                    f"👤 المستخدم: {target_id}\n"
                    f"💰 المبلغ: {amount:,} دينار\n"
                    f"💳 الرصيد الجديد: {user_data.get('balance', 0):,} دينار",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text("❌ <b>فشل في الشحن</b>", parse_mode=ParseMode.HTML)
        
        elif action == 'deduct_user':
            user_data = self.user_manager.get_user(target_id)
            current_balance = user_data.get("balance", 0)
            
            if current_balance < amount:
                await update.message.reply_text(
                    f"❌ <b>رصيد المستخدم غير كافي!</b>\n\n"
                    f"💰 رصيد المستخدم: {current_balance:,} دينار\n"
                    f"💸 المبلغ المطلوب: {amount:,} دينار",
                    parse_mode=ParseMode.HTML
                )
                return CHARGE_AMOUNT
            
            if self.user_manager.update_balance(target_id, -amount, "خصم من المدير"):
                user_data = self.user_manager.get_user(target_id)
                
                await update.message.reply_text(
                    f"✅ <b>تم الخصم بنجاح!</b>\n\n"
                    f"👤 المستخدم: {target_id}\n"
                    f"💸 المبلغ: {amount:,} دينار\n"
                    f"💳 الرصيد الجديد: {user_data.get('balance', 0):,} دينار",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text("❌ <b>فشل في الخصم</b>", parse_mode=ParseMode.HTML)
        
        context.user_data.pop('admin_action', None)
        context.user_data.pop('charge_target', None)
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة جميع عمليات الرد"""
        query = update.callback_query
        
        try:
            await query.answer()
            
            if query.data == "admin_panel":
                await self.admin_panel(update, context)
            
            elif query.data == "admin_charge":
                await self.handle_admin_charge(query)
            
            elif query.data == "admin_charge_user":
                await self.handle_admin_charge_user(query, context)
                return CHARGE_USER
            
            elif query.data == "admin_deduct_user":
                await self.handle_admin_deduct_user(query, context)
                return CHARGE_USER
            
            elif query.data == "admin_change_channel":
                await self.handle_admin_change_channel(query, context)
                return CHANGE_CHANNEL
            
            elif query.data == "back_home":
                await self.handle_back_home(update, context)
            
            elif query.data.startswith("service_"):
                await self.handle_service_selection(update, context)
            
            elif query.data == "balance":
                await self.handle_balance_check(update, context)
            
            elif query.data == "stats":
                await self.handle_stats(update, context)
            
            elif query.data == "invite":
                await self.handle_invite(update, context)
            
            else:
                await query.answer("⏳ جاري التحميل...")
        
        except Exception as e:
            logger.error(f"Error in callback handler: {e}")
            await query.answer("❌ حدث خطأ. حاول مرة أخرى")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        user = update.effective_user
        
        if update.message.document and context.user_data.get('awaiting_pdf'):
            await self.handle_pdf_file(update, context)
        
        elif update.message.text and context.user_data.get('awaiting_question'):
            await self.handle_question(update, context)
        
        elif update.message.text and context.user_data.get('awaiting_help_question'):
            await self.handle_help_question(update, context)
        
        elif update.message.text and context.user_data.get('admin_action'):
            # معالجة رسائل المدير
            action = context.user_data.get('admin_action')
            
            if action in ['charge_user', 'deduct_user']:
                await self.handle_charge_user_id(update, context)
            
            elif action == 'change_channel':
                await self.handle_change_channel(update, context)
        
        elif update.message.text:
            # معالجة حساب الإعفاء
            text = update.message.text.strip()
            if text.replace('.', '', 1).isdigit() or (text.count(' ') >= 2 and all(part.replace('.', '', 1).isdigit() for part in text.split()[:3])):
                await self.handle_exemption_calculation(update, context)
            else:
                await update.message.reply_text(
                    "🤖 <b>استخدم الأزرار للتفاعل مع البوت</b>\n\n"
                    "📝 اكتب /start لعرض القائمة الرئيسية",
                    parse_mode=ParseMode.HTML
                )
    
    async def handle_balance_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض رصيد المستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        balance_text = f"""
💰 <b>رصيدك الحالي:</b> {user_data['balance']} دينار عراقي

🆔 <b>رقم حسابك:</b> <code>{user_id}</code>

📊 <b>آخر المعاملات:</b>
"""
        
        transactions = user_data.get('transactions', [])[-3:]
        if transactions:
            for trans in transactions:
                sign = "+" if trans['amount'] > 0 else ""
                date = trans['date'].split()[0]
                balance_text += f"\n{date}: {sign}{trans['amount']} - {trans['description'][:30]}"
        else:
            balance_text += "\nلا توجد معاملات سابقة"
        
        keyboard = [
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")],
            [InlineKeyboardButton("📥 شحن الرصيد", url=f"https://t.me/{SUPPORT_USERNAME}")]
        ]
        
        await query.edit_message_text(
            balance_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_back_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """العودة للصفحة الرئيسية"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        user_data = self.user_manager.get_user(user.id)
        
        welcome_message = f"""
🎓 <b>مرحباً بعودتك {user.first_name}!</b>

🆔 <b>رقم حسابك:</b> <code>{user.id}</code>
💰 <b>رصيدك الحالي:</b> {user_data['balance']} دينار

اختر الخدمة:
"""
        
        keyboard = [
            [InlineKeyboardButton("🧮 حساب درجة الإعفاء", callback_data="service_exemption")],
            [InlineKeyboardButton("📚 تلخيص الملازم", callback_data="service_summarize")],
            [InlineKeyboardButton("❓ سؤال وجواب بالذكاء", callback_data="service_qa")],
            [InlineKeyboardButton("📖 ملازمي ومرشحاتي", callback_data="service_materials")],
            [InlineKeyboardButton("🤝 ساعدوني طلاب (250 دينار)", callback_data="service_help_student")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
             InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
            [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite"),
             InlineKeyboardButton("📢 قناة البوت", url=self.channel_manager.get_channel_link())],
            [InlineKeyboardButton("🆘 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME}")],
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء العملية"""
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        await update.message.reply_text("❌ <b>تم إلغاء العملية</b>", parse_mode=ParseMode.HTML)
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    def run(self):
        """تشغيل البوت"""
        print("🤖 البوت يعمل الآن...")
        print(f"👑 المدير: {ADMIN_ID}")
        print(f"🆘 الدعم: @{SUPPORT_USERNAME}")
        print(f"📢 القناة: {self.channel_manager.get_channel_link()}")
        print(f"💎 الهدية الترحيبية: {self.settings['welcome_bonus']} دينار")
        
        app = Application.builder().token(TOKEN).build()
        
        # إنشاء ConversationHandler للوحة التحكم
        admin_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.handle_callback)],
            states={
                CHARGE_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_charge_user_id),
                    CallbackQueryHandler(self.handle_callback)
                ],
                CHARGE_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_charge_amount),
                    CallbackQueryHandler(self.handle_callback)
                ],
                CHANGE_CHANNEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_change_channel),
                    CallbackQueryHandler(self.handle_callback)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.handle_callback, pattern="^back_home$|^admin_panel$")
            ]
        )
        
        # إضافة handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("admin", self.admin_panel))
        app.add_handler(admin_conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(MessageHandler(filters.Document.PDF, self.handle_pdf_file))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# ============= تشغيل البوت =============
if __name__ == "__main__":
    bot = YallaNataalamBot()
    bot.run()
