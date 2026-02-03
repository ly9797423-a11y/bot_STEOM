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
from datetime import datetime
from typing import Dict, List, Optional
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
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode
import google.generativeai as genai

# ============= إعدادات البوت =============
TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
SUPPORT_USERNAME = "Allawi04@"
GEMINI_API_KEY = "AIzaSyAqlug21bw_eI60ocUtc1Z76NhEUc-zuzY"

# ============= إعداد التسعير =============
SERVICE_PRICES = {
    "exemption": 1000,      # حساب درجة الإعفاء
    "summarize": 1000,      # تلخيص الملازم
    "qa": 1000,             # سؤال وجواب
    "materials": 1000       # ملازمي ومرشحاتي
}
WELCOME_BONUS = 1000        # هدية الترحيب
REFERRAL_BONUS = 500        # مكافأة الدعوة

# ============= إعداد الملفات =============
DATA_FILE = "users_data.json"
MATERIALS_FILE = "materials_data.json"
ADMIN_FILE = "admin_settings.json"

# ============= تسجيل الخطوط العربية =============
def setup_arabic_fonts():
    """تسجيل الخطوط العربية والإنجليزية"""
    try:
        # تحميل خطوط عربية (يجب تثبيت الخطوط مسبقاً على السيرفر)
        pdfmetrics.registerFont(TTFont('Arabic', 'fonts/arial.ttf'))
        pdfmetrics.registerFont(TTFont('English', 'fonts/times.ttf'))
    except:
        # استخدام الخطوط الافتراضية إذا لم تكن الخطوط موجودة
        pass

# ============= إدارة البيانات =============
class DataManager:
    @staticmethod
    def load_data(filename: str, default=None):
        """تحميل البيانات من ملف JSON"""
        if default is None:
            default = {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    @staticmethod
    def save_data(filename: str, data):
        """حفظ البيانات إلى ملف JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# ============= إدارة المستخدمين =============
class UserManager:
    def __init__(self):
        self.users = DataManager.load_data(DATA_FILE, {})
        
    def get_user(self, user_id: int) -> Dict:
        """الحصول على بيانات المستخدم أو إنشاء مستخدم جديد"""
        if str(user_id) not in self.users:
            self.users[str(user_id)] = {
                "balance": WELCOME_BONUS,
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "referral_code": str(user_id),
                "invited_by": None,
                "invited_users": [],
                "transactions": [],
                "exemption_scores": [],
                "used_services": []
            }
            self.save_users()
        return self.users[str(user_id)]
    
    def update_balance(self, user_id: int, amount: int, description: str = ""):
        """تحديد رصيد المستخدم"""
        user = self.get_user(user_id)
        user["balance"] = user.get("balance", 0) + amount
        
        # تسجيل المعاملة
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "description": description,
            "balance_after": user["balance"]
        }
        user["transactions"].append(transaction)
        self.save_users()
        return user["balance"]
    
    def can_afford(self, user_id: int, service: str) -> bool:
        """التحقق مما إذا كان المستخدم يمتلك رصيداً كافياً للخدمة"""
        user = self.get_user(user_id)
        price = SERVICE_PRICES.get(service, 1000)
        return user["balance"] >= price
    
    def charge_service(self, user_id: int, service: str) -> bool:
        """خصم تكلفة الخدمة من رصيد المستخدم"""
        if self.can_afford(user_id, service):
            price = SERVICE_PRICES.get(service, 1000)
            self.update_balance(user_id, -price, f"دفع لخدمة: {service}")
            user = self.get_user(user_id)
            user["used_services"].append({
                "service": service,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cost": price
            })
            self.save_users()
            return True
        return False
    
    def save_users(self):
        """حفظ بيانات المستخدمين"""
        DataManager.save_data(DATA_FILE, self.users)

# ============= إدارة المواد التعليمية =============
class MaterialsManager:
    def __init__(self):
        self.materials = DataManager.load_data(MATERIALS_FILE, [])
    
    def get_materials_by_stage(self, stage: str) -> List[Dict]:
        """الحصول على المواد حسب المرحلة"""
        return [m for m in self.materials if m.get("stage") == stage]
    
    def get_all_stages(self) -> List[str]:
        """الحصول على جميع المراحل المتاحة"""
        stages = set(m.get("stage", "") for m in self.materials)
        return [s for s in stages if s]
    
    def add_material(self, material_data: Dict):
        """إضافة مادة جديدة"""
        material_data["id"] = len(self.materials) + 1
        material_data["added_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.materials.append(material_data)
        self.save_materials()
    
    def save_materials(self):
        """حفظ المواد"""
        DataManager.save_data(MATERIALS_FILE, self.materials)

# ============= إعداد الذكاء الاصطناعي =============
class AIService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def summarize_pdf(self, pdf_path: str) -> str:
        """تلخيص ملف PDF باستخدام الذكاء الاصطناعي"""
        try:
            # قراءة نص PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # تلخيص النص
            prompt = f"""
            قم بتلخيص النص التعليمي التالي مع الحفاظ على المعلومات المهمة:
            - احذف المعلومات غير الأساسية
            - رتب النقاط الرئيسية
            - حافظ على التسلسل المنطقي
            - استخدم اللغة العربية الفصحى
            
            النص:
            {text[:3000]}  # إرسال أول 3000 حرف فقط
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"حدث خطأ في التلخيص: {str(e)}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """استخراج النص من ملف PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            text = f"خطأ في قراءة PDF: {str(e)}"
        return text
    
    def answer_question(self, question: str, context: str = "") -> str:
        """الإجابة على الأسئلة التعليمية"""
        try:
            prompt = f"""
            أنت مساعد تعليمي للطلاب العراقيين.
            أجب على السؤال التالي بطريقة علمية ومنهجية حسب المنهج العراقي:
            
            السؤال: {question}
            
            {f'السياق: {context}' if context else ''}
            
            قدم إجابة شاملة ومفيدة مع الأمثلة إذا لزم الأمر.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"حدث خطأ في الإجابة: {str(e)}"
    
    def create_summary_pdf(self, original_text: str, summary: str, output_path: str):
        """إنشاء ملف PDF منظم للتلخيص"""
        try:
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # إضافة عنوان
            c.setFont("Arabic", 16)
            c.drawString(50, height - 50, "تلخيص الملزمة التعليمية")
            c.line(50, height - 60, width - 50, height - 60)
            
            # إضافة النص الأصلي المختصر
            c.setFont("Arabic", 12)
            y_position = height - 100
            c.drawString(50, y_position, "النص الأصلي (مختصر):")
            y_position -= 20
            
            for line in original_text[:500].split('\n'):
                if y_position < 100:
                    c.showPage()
                    y_position = height - 50
                c.drawString(50, y_position, line[:80])
                y_position -= 20
            
            # إضافة التلخيص
            y_position -= 30
            c.setFont("Arabic", 14)
            c.drawString(50, y_position, "التلخيص:")
            y_position -= 20
            c.setFont("Arabic", 12)
            
            for line in summary.split('\n'):
                if y_position < 100:
                    c.showPage()
                    y_position = height - 50
                    c.setFont("Arabic", 12)
                
                # معالجة النص العربي
                reshaped_text = arabic_reshaper.reshape(line)
                bidi_text = get_display(reshaped_text)
                c.drawString(50, y_position, bidi_text[:80])
                y_position -= 20
            
            c.save()
            return True
        except Exception as e:
            logging.error(f"Error creating PDF: {str(e)}")
            return False

# ============= واجهة المستخدم الرئيسية =============
class MainBot:
    def __init__(self):
        self.user_manager = UserManager()
        self.materials_manager = MaterialsManager()
        self.ai_service = AIService()
        self.setup_fonts()
    
    def setup_fonts(self):
        """إعداد الخطوط"""
        try:
            setup_arabic_fonts()
        except:
            pass
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء البوت"""
        user = update.effective_user
        user_data = self.user_manager.get_user(user.id)
        
        welcome_message = f"""
        🎓 مرحباً {user.first_name}!
        
        أهلاً بك في بوت "يلا نتعلم" 🤖
        
        رصيدك الحالي: {user_data['balance']} دينار عراقي
        
        💰 حصلت على هدية ترحيبية: {WELCOME_BONUS} دينار
        
        اختر الخدمة التي تريدها:
        """
        
        keyboard = [
            [InlineKeyboardButton("🧮 حساب درجة الإعفاء", callback_data="service_exemption")],
            [InlineKeyboardButton("📚 تلخيص الملازم", callback_data="service_summarize")],
            [InlineKeyboardButton("❓ سؤال وجواب", callback_data="service_qa")],
            [InlineKeyboardButton("📖 ملازمي ومرشحاتي", callback_data="service_materials")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
             InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
            [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite"),
             InlineKeyboardButton("🆘 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
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
        
        if not self.user_manager.can_afford(user_id, service):
            await query.edit_message_text(
                f"❌ رصيدك غير كافي لهذه الخدمة!\n"
                f"سعر الخدمة: {SERVICE_PRICES.get(service, 1000)} دينار\n"
                f"رصيدك الحالي: {self.user_manager.get_user(user_id)['balance']} دينار\n\n"
                f"📞 تواصل مع الدعم الفني للشحن: {SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        if service == "exemption":
            await self.show_exemption_calculator(query)
        elif service == "summarize":
            await query.edit_message_text(
                "📤 أرسل ملف PDF المراد تلخيصه\n"
                "سعر الخدمة: 1000 دينار",
                parse_mode=ParseMode.HTML
            )
            context.user_data['awaiting_pdf'] = True
        elif service == "qa":
            await query.edit_message_text(
                "❓ أرسل سؤالك أو صورة تحتوي على سؤال\n"
                "سعر الخدمة: 1000 دينار",
                parse_mode=ParseMode.HTML
            )
            context.user_data['awaiting_question'] = True
        elif service == "materials":
            await self.show_materials_menu(query)
    
    async def show_exemption_calculator(self, query):
        """عرض آلة حساب الإعفاء"""
        keyboard = [
            [InlineKeyboardButton("🏠 الرجوع للرئيسية", callback_data="back_home")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🧮 حاسبة درجة الإعفاء\n\n"
            "أدخل درجاتك لثلاثة كورسات:\n"
            "1. درجة الكورس الأول\n"
            "2. درجة الكورس الثاني\n"
            "3. درجة الكورس الثالث\n\n"
            "📝 أرسل الدرجات بهذا الشكل:\n"
            "<code>90 85 95</code>\n\n"
            "🎯 المعدل المطلوب للإعفاء: 90 فما فوق",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_exemption_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة حساب درجة الإعفاء"""
        user_id = update.effective_user.id
        
        # التحقق من الرصيد
        if not self.user_manager.charge_service(user_id, "exemption"):
            await update.message.reply_text(
                f"❌ رصيدك غير كافي!\n"
                f"رصيدك: {self.user_manager.get_user(user_id)['balance']} دينار\n"
                f"سعر الخدمة: {SERVICE_PRICES['exemption']} دينار"
            )
            return
        
        try:
            scores = list(map(float, update.message.text.split()))
            
            if len(scores) != 3:
                await update.message.reply_text("⚠️ يجب إدخال 3 درجات فقط")
                return
            
            average = sum(scores) / 3
            
            if average >= 90:
                message = f"""
                🎉 تهانينا! تم إعفاؤك من المادة 🎉
                
                📊 درجاتك:
                الكورس الأول: {scores[0]}
                الكورس الثاني: {scores[1]}  
                الكورس الثالث: {scores[2]}
                
                🧮 المعدل: {average:.2f}
                
                ✅ أنت معفي من المادة
                """
            else:
                message = f"""
                📊 درجاتك:
                الكورس الأول: {scores[0]}
                الكورس الثاني: {scores[1]}
                الكورس الثالث: {scores[2]}
                
                🧮 المعدل: {average:.2f}
                
                ⚠️ المعدل أقل من 90
                ❌ لم تحصل على الإعفاء
                """
            
            await update.message.reply_text(message)
            
            # حفظ الدرجات
            user_data = self.user_manager.get_user(user_id)
            user_data["exemption_scores"].append({
                "scores": scores,
                "average": average,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exempted": average >= 90
            })
            self.user_manager.save_users()
            
        except ValueError:
            await update.message.reply_text("⚠️ أدخل أرقاماً صحيحة فقط")
    
    async def handle_pdf_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ملف PDF للتلخيص"""
        user_id = update.effective_user.id
        
        if not context.user_data.get('awaiting_pdf'):
            return
        
        # التحقق من الرصيد
        if not self.user_manager.charge_service(user_id, "summarize"):
            await update.message.reply_text(
                f"❌ رصيدك غير كافي!\nرصيدك: {self.user_manager.get_user(user_id)['balance']} دينار"
            )
            context.user_data['awaiting_pdf'] = False
            return
        
        file = await update.message.document.get_file()
        pdf_path = f"temp_{user_id}.pdf"
        await file.download_to_drive(pdf_path)
        
        await update.message.reply_text("⏳ جاري تلخيص الملف...")
        
        try:
            # استخراج النص
            text = self.ai_service.extract_text_from_pdf(pdf_path)
            
            # تلخيص النص
            summary = self.ai_service.summarize_pdf(pdf_path)
            
            # إنشاء PDF جديد
            output_path = f"summary_{user_id}.pdf"
            success = self.ai_service.create_summary_pdf(text, summary, output_path)
            
            if success:
                await update.message.reply_document(
                    document=open(output_path, 'rb'),
                    caption="✅ تم تلخيص الملزمة بنجاح\n📄 الملف جاهز للتحميل"
                )
                
                # تنظيف الملفات المؤقتة
                os.remove(pdf_path)
                os.remove(output_path)
            else:
                await update.message.reply_text("❌ حدث خطأ في إنشاء الملف")
        
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
        
        context.user_data['awaiting_pdf'] = False
    
    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأسئلة"""
        user_id = update.effective_user.id
        
        if not context.user_data.get('awaiting_question'):
            return
        
        # التحقق من الرصيد
        if not self.user_manager.charge_service(user_id, "qa"):
            await update.message.reply_text(
                f"❌ رصيدك غير كافي!\nرصيدك: {self.user_manager.get_user(user_id)['balance']} دينار"
            )
            context.user_data['awaiting_question'] = False
            return
        
        question = update.message.text
        
        await update.message.reply_text("⏳ جاري البحث عن الإجابة...")
        
        try:
            answer = self.ai_service.answer_question(question)
            
            await update.message.reply_text(
                f"❓ السؤال:\n{question}\n\n"
                f"💡 الإجابة:\n{answer[:2000]}",  # تقليل النص إذا كان طويلاً
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
        
        context.user_data['awaiting_question'] = False
    
    async def show_materials_menu(self, query):
        """عرض قائمة المواد"""
        stages = self.materials_manager.get_all_stages()
        
        if not stages:
            keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")]]
            await query.edit_message_text(
                "📭 لا توجد مواد متاحة حالياً",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        keyboard = []
        for stage in stages:
            keyboard.append([InlineKeyboardButton(f"📘 {stage}", callback_data=f"stage_{stage}")])
        
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📖 اختر المرحلة الدراسية:",
            reply_markup=reply_markup
        )
    
    async def show_stage_materials(self, query, stage: str):
        """عرض مواد مرحلة محددة"""
        user_id = query.from_user.id
        
        # التحقق من الرصيد
        if not self.user_manager.charge_service(user_id, "materials"):
            await query.edit_message_text(
                f"❌ رصيدك غير كافي!\nرصيدك: {self.user_manager.get_user(user_id)['balance']} دينار"
            )
            return
        
        materials = self.materials_manager.get_materials_by_stage(stage)
        
        if not materials:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="service_materials")]]
            await query.edit_message_text(
                f"📭 لا توجد مواد لمرحلة {stage}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        message = f"📚 مواد مرحلة {stage}:\n\n"
        
        keyboard = []
        for material in materials:
            btn_text = f"📄 {material.get('name', 'بدون اسم')}"
            callback_data = f"material_{material['id']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
            
            message += f"📖 {material.get('name', 'بدون اسم')}\n"
            message += f"   {material.get('description', '')[:50]}...\n\n"
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="service_materials")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
    
    async def handle_balance_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض رصيد المستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        balance_text = f"""
        💰 رصيدك الحالي: {user_data['balance']} دينار عراقي
        
        📊 آخر المعاملات:
        """
        
        for trans in user_data['transactions'][-5:]:
            sign = "+" if trans['amount'] > 0 else ""
            balance_text += f"\n{trans['date']} - {sign}{trans['amount']}: {trans['description']}"
        
        keyboard = [
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")],
            [InlineKeyboardButton("📥 شحن الرصيد", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")]
        ]
        
        await query.edit_message_text(
            balance_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات المستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        stats_text = f"""
        📊 إحصائياتك الشخصية
        
        👤 المعلومات:
        - تاريخ الانضمام: {user_data['joined_date']}
        - الرصيد الحالي: {user_data['balance']} دينار
        
        📈 النشاط:
        - عدد الخدمات المستخدمة: {len(user_data['used_services'])}
        - عدد حسابات الإعفاء: {len(user_data['exemption_scores'])}
        - عدد الأصدقاء المدعوين: {len(user_data['invited_users'])}
        
        🔗 رابط الدعوة الخاص بك:
        <code>https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}</code>
        
        💸 مكافأة الدعوة: {REFERRAL_BONUS} دينار لكل صديق
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="balance")]
        ]
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات الدعوة"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        invite_text = f"""
        👥 دعوة الأصدقاء
        
        💰 احصل على {REFERRAL_BONUS} دينار لكل صديق يدخل عبر رابطك!
        
        🔗 رابط الدعوة الخاص بك:
        <code>https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}</code>
        
        📊 عدد الأصدقاء المدعوين: {len(user_data['invited_users'])}
        💵 أرباح الدعوة: {len(user_data['invited_users']) * REFERRAL_BONUS} دينار
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")],
            [InlineKeyboardButton("📤 مشاركة الرابط", switch_inline_query="انضم إلى بوت يلا نتعلم التعليمي!")]
        ]
        
        await query.edit_message_text(
            invite_text,
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
        🎓 مرحباً بعودتك {user.first_name}!
        
        رصيدك الحالي: {user_data['balance']} دينار
        
        اختر الخدمة:
        """
        
        keyboard = [
            [InlineKeyboardButton("🧮 حساب درجة الإعفاء", callback_data="service_exemption")],
            [InlineKeyboardButton("📚 تلخيص الملازم", callback_data="service_summarize")],
            [InlineKeyboardButton("❓ سؤال وجواب", callback_data="service_qa")],
            [InlineKeyboardButton("📖 ملازمي ومرشحاتي", callback_data="service_materials")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
             InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
            [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite"),
             InlineKeyboardButton("🆘 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة جميع عمليات الرد"""
        query = update.callback_query
        
        if query.data.startswith("service_"):
            await self.handle_service_selection(update, context)
        elif query.data == "balance":
            await self.handle_balance_check(update, context)
        elif query.data == "stats":
            await self.handle_stats(update, context)
        elif query.data == "invite":
            await self.handle_invite(update, context)
        elif query.data.startswith("stage_"):
            stage = query.data.replace("stage_", "")
            await self.show_stage_materials(query, stage)
        elif query.data == "back_home":
            await self.handle_back_home(update, context)
        elif query.data == "admin_panel":
            await query.answer("سيتم توجيهك إلى لوحة التحكم...")
            # ستتم معالجة هذا في لوحة التحكم
        else:
            await query.answer("⏳ جاري التحميل...")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        message_type = update.message.chat.type
        text = update.message.text
        
        if message_type == "private":
            if context.user_data.get('awaiting_pdf'):
                await update.message.reply_text("📤 أرسل ملف PDF فقط")
            elif context.user_data.get('awaiting_question'):
                await self.handle_question(update, context)
            elif text and text.replace(".", "").isdigit():
                await self.handle_exemption_calculation(update, context)
            else:
                await update.message.reply_text(
                    "استخدم الأزرار للتفاعل مع البوت 🤖\n"
                    "اكتب /start لعرض القائمة الرئيسية"
                )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأخطاء"""
        logging.error(f"حدث خطأ: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع\n"
                "🆘 تواصل مع الدعم الفني: @Allawi04"
            )
    
    def run(self):
        """تشغيل البوت"""
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        
        app = Application.builder().token(TOKEN).build()
        
        # إضافة handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(MessageHandler(filters.Document.PDF, self.handle_pdf_file))
        app.add_error_handler(self.error_handler)
        
        print("🤖 البوت يعمل الآن...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

# ============= تشغيل البوت =============
if __name__ == "__main__":
    bot = MainBot()
    bot.run()
