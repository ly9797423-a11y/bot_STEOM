#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت "يلا نتعلم" - بوت تعليمي للطلاب العراقيين
مطور بواسطة: Allawi04@
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
import io
import hashlib
from pathlib import Path

# المكتبات الأساسية
import aiohttp
import aiofiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types import InputFile, InputMediaDocument, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

# مكتبات PDF والمعالجة
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
import PyPDF2
from PIL import Image

# مكتبة الذكاء الاصطناعي Gemini
import google.generativeai as genai

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات الإعداد
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAqlug21bw_eI60ocUtc1Z76NhEUc-zuzY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 6130994941))
BOT_USERNAME = "@FC4Xbot"
SUPPORT_USERNAME = "Allawi04@"

# تهيئة الذكاء الاصطناعي Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    gemini_vision_model = genai.GenerativeModel('gemini-pro-vision')
    logger.info("✅ تم تهيئة Gemini API بنجاح")
except Exception as e:
    logger.error(f"❌ فشل تهيئة Gemini API: {e}")
    gemini_model = None
    gemini_vision_model = None

# تهيئة البوت
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# حالات FSM
class UserStates(StatesGroup):
    waiting_for_course1 = State()
    waiting_for_course2 = State()
    waiting_for_course3 = State()
    waiting_for_pdf = State()
    waiting_for_question = State()
    waiting_for_image = State()
    admin_waiting_user_id = State()
    admin_waiting_amount = State()
    admin_waiting_price_service = State()
    admin_waiting_material_name = State()
    admin_waiting_material_desc = State()
    admin_waiting_material_stage = State()
    admin_waiting_material_file = State()
    admin_waiting_invite_reward = State()
    admin_waiting_channel_link = State()

# فئات البيانات
class User:
    def __init__(self, user_id: int, username: str = "", first_name: str = ""):
        self.user_id = user_id
        self.username = username or f"user_{user_id}"
        self.first_name = first_name or "مستخدم"
        self.balance = 1000  # هدية ترحيبية
        self.is_admin = (user_id == ADMIN_ID)
        self.is_blocked = False
        self.join_date = datetime.now()
        self.last_active = datetime.now()
        self.invite_code = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
        self.invited_by = None
        self.invited_count = 0
        self.total_spent = 0
        
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'balance': self.balance,
            'is_admin': self.is_admin,
            'is_blocked': self.is_blocked,
            'join_date': self.join_date.isoformat(),
            'last_active': self.last_active.isoformat(),
            'invite_code': self.invite_code,
            'invited_by': self.invited_by,
            'invited_count': self.invited_count,
            'total_spent': self.total_spent
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        user = cls(data['user_id'], data.get('username', ''), data.get('first_name', ''))
        user.balance = data.get('balance', 1000)
        user.is_admin = data.get('is_admin', False)
        user.is_blocked = data.get('is_blocked', False)
        user.join_date = datetime.fromisoformat(data.get('join_date', datetime.now().isoformat()))
        user.last_active = datetime.fromisoformat(data.get('last_active', datetime.now().isoformat()))
        user.invite_code = data.get('invite_code', '')
        user.invited_by = data.get('invited_by')
        user.invited_count = data.get('invited_count', 0)
        user.total_spent = data.get('total_spent', 0)
        return user

class Material:
    def __init__(self, material_id: int, name: str, description: str, stage: str, file_id: str):
        self.material_id = material_id
        self.name = name
        self.description = description
        self.stage = stage
        self.file_id = file_id
        self.add_date = datetime.now()
        
    def to_dict(self):
        return {
            'material_id': self.material_id,
            'name': self.name,
            'description': self.description,
            'stage': self.stage,
            'file_id': self.file_id,
            'add_date': self.add_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        material = cls(
            data['material_id'],
            data['name'],
            data['description'],
            data['stage'],
            data['file_id']
        )
        material.add_date = datetime.fromisoformat(data.get('add_date', datetime.now().isoformat()))
        return material

class BotDatabase:
    def __init__(self):
        self.users_file = "data/users.json"
        self.materials_file = "data/materials.json"
        self.settings_file = "data/settings.json"
        self.stats_file = "data/stats.json"
        
        # إنشاء المجلدات
        os.makedirs("data", exist_ok=True)
        
        # تحميل البيانات
        self.users = self._load_users()
        self.materials = self._load_materials()
        self.settings = self._load_settings()
        self.stats = self._load_stats()
        
        # إعدادات افتراضية
        default_settings = {
            'service_prices': {
                'exemption': 1000,
                'summarize': 1000,
                'qa': 1000,
                'materials': 1000
            },
            'invite_reward': 500,
            'maintenance': False,
            'channel_link': "https://t.me/+",
            'support_username': SUPPORT_USERNAME
        }
        
        for key, value in default_settings.items():
            if key not in self.settings:
                self.settings[key] = value
        
        self.save_settings()
        
    def _load_users(self) -> Dict[int, User]:
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {int(k): User.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المستخدمين: {e}")
        return {}
    
    def _load_materials(self):
        try:
            if os.path.exists(self.materials_file):
                with open(self.materials_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {int(k): Material.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المواد: {e}")
        return {}
    
    def _load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الإعدادات: {e}")
        return {}
    
    def _load_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الإحصائيات: {e}")
        return {
            'total_users': 0,
            'active_today': 0,
            'total_services': 0,
            'total_revenue': 0,
            'today_date': datetime.now().date().isoformat()
        }
    
    def save_users(self):
        try:
            data = {str(k): v.to_dict() for k, v in self.users.items()}
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ المستخدمين: {e}")
    
    def save_materials(self):
        try:
            data = {str(k): v.to_dict() for k, v in self.materials.items()}
            with open(self.materials_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ المواد: {e}")
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الإعدادات: {e}")
    
    def save_stats(self):
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الإحصائيات: {e}")
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)
    
    def add_user(self, user: User):
        self.users[user.user_id] = user
        self.save_users()
        
        # تحديث الإحصائيات
        today = datetime.now().date().isoformat()
        if self.stats.get('today_date') != today:
            self.stats['today_date'] = today
            self.stats['active_today'] = 0
        
        self.stats['total_users'] = len(self.users)
        self.stats['active_today'] = self.stats.get('active_today', 0) + 1
        self.save_stats()
        logger.info(f"✅ تم إضافة مستخدم جديد: {user.user_id}")
    
    def update_user(self, user: User):
        self.users[user.user_id] = user
        self.save_users()
    
    def get_material(self, material_id: int) -> Optional[Material]:
        return self.materials.get(material_id)
    
    def add_material(self, material: Material):
        self.materials[material.material_id] = material
        self.save_materials()
    
    def delete_material(self, material_id: int):
        if material_id in self.materials:
            del self.materials[material_id]
            self.save_materials()
            return True
        return False
    
    def get_all_materials(self) -> List[Material]:
        return list(self.materials.values())
    
    def get_materials_by_stage(self, stage: str) -> List[Material]:
        return [m for m in self.materials.values() if m.stage == stage]
    
    def get_next_material_id(self) -> int:
        if not self.materials:
            return 1
        return max(self.materials.keys()) + 1

# إنشاء قاعدة البيانات
db = BotDatabase()

# دوال مساعدة
def format_arabic(text: str) -> str:
    """تنسيق النص العربي"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text

def format_number(num: int) -> str:
    """تنسيق الأرقام"""
    return f"{num:,}".replace(",", "،")

def create_main_menu(user_id: int) -> InlineKeyboardMarkup:
    """إنشاء القائمة الرئيسية"""
    user = db.get_user(user_id)
    if not user:
        user = User(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 حساب درجة الإعفاء الفردي", callback_data="service_exemption"),
            InlineKeyboardButton(text="📄 تلخيص الملازم", callback_data="service_summarize")
        ],
        [
            InlineKeyboardButton(text="❓ سؤال وجواب", callback_data="service_qa"),
            InlineKeyboardButton(text="📚 ملازمي ومرشحاتي", callback_data="service_materials")
        ],
        [
            InlineKeyboardButton(text=f"💰 رصيدي: {format_number(user.balance)} دينار", callback_data="show_balance"),
            InlineKeyboardButton(text="👥 دعوة أصدقاء", callback_data="invite_friends")
        ],
        [
            InlineKeyboardButton(text="📞 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"),
            InlineKeyboardButton(text="📢 قناة البوت", url=db.settings['channel_link'])
        ]
    ])
    
    if user.is_admin:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="👑 لوحة التحكم", callback_data="admin_panel")
        ])
    
    return keyboard

def create_admin_panel() -> InlineKeyboardMarkup:
    """لوحة تحكم المدير"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 إدارة المستخدمين", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="💰 نظام الشحن", callback_data="admin_charge"),
            InlineKeyboardButton(text="💵 تعديل الأسعار", callback_data="admin_prices")
        ],
        [
            InlineKeyboardButton(text="🔧 وضع الصيانة", callback_data="admin_maintenance"),
            InlineKeyboardButton(text="📚 إدارة الملازم", callback_data="admin_materials")
        ],
        [
            InlineKeyboardButton(text="🎁 تعديل مكافأة الدعوة", callback_data="admin_invite_reward"),
            InlineKeyboardButton(text="🔗 تحديث رابط القناة", callback_data="admin_update_channel")
        ],
        [
            InlineKeyboardButton(text="↩️ العودة للقائمة", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def check_maintenance(user_id: int) -> bool:
    """التحقق من وضع الصيانة"""
    if db.settings.get('maintenance', False):
        user = db.get_user(user_id)
        if not user or not user.is_admin:
            return True
    return False

async def send_notification(user_id: int, message: str):
    """إرسال إشعار للمستخدم"""
    try:
        await bot.send_message(user_id, message)
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الإشعار: {e}")
        return False

# ========== معالجات الأوامر ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """معالج أمر /start"""
    user_id = message.from_user.id
    
    # التحقق من الصيانة
    if check_maintenance(user_id):
        await message.answer("⚙️ البوت قيد الصيانة حالياً. نعتذر للإزعاج وسنعود قريباً.")
        return
    
    # التحقق من رابط الدعوة
    args = message.text.split()
    invite_code = args[1] if len(args) > 1 else None
    
    # تسجيل أو تحديث المستخدم
    if user_id not in db.users:
        user = User(
            user_id,
            message.from_user.username or "",
            message.from_user.first_name or ""
        )
        
        # تطبيق مكافأة الدعوة
        if invite_code:
            for existing_user in db.users.values():
                if existing_user.invite_code == invite_code and existing_user.user_id != user_id:
                    existing_user.balance += db.settings['invite_reward']
                    existing_user.invited_count += 1
                    db.update_user(existing_user)
                    user.invited_by = existing_user.user_id
                    
                    # إشعار للمدعو
                    await send_notification(existing_user.user_id,
                        f"🎉 حصلت على مكافأة دعوة! تم إضافة {format_number(db.settings['invite_reward'])} دينار لرصيدك.")
                    break
        
        db.add_user(user)
        
        # رسالة ترحيب
        welcome_msg = format_arabic(f"""
🎉 أهلاً وسهلاً بك {user.first_name} في بوت "يلا نتعلم"!

🎁 لقد حصلت على هدية ترحيبية: 1,000 دينار عراقي

💰 رصيدك الحالي: {format_number(user.balance)} دينار

📚 يمكنك استخدام الخدمات التعليمية المتاحة:

1. حساب درجة الإعفاء الفردي
2. تلخيص الملازم بالذكاء الاصطناعي
3. أسئلة وأجوبة بالذكاء الاصطناعي
4. قسم الملازم والمرشحات

كل خدمة بسعر {format_number(db.settings['service_prices']['exemption'])} دينار
        """)
        
        await message.answer(welcome_msg, reply_markup=create_main_menu(user_id))
        
        # إشعار للمدير
        try:
            await bot.send_message(
                ADMIN_ID,
                format_arabic(f"""
📊 مستخدم جديد انضم للبوت:

👤 الاسم: {user.first_name}
🆔 الايدي: {user_id}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👥 إجمالي المستخدمين: {db.stats['total_users']}
                """)
            )
        except:
            pass
    else:
        user = db.users[user_id]
        user.last_active = datetime.now()
        user.username = message.from_user.username or user.username
        user.first_name = message.from_user.first_name or user.first_name
        db.update_user(user)
        
        await message.answer(
            format_arabic(f"أهلاً بعودتك {user.first_name}! 👋\n\n💰 رصيدك: {format_number(user.balance)} دينار"),
            reply_markup=create_main_menu(user_id)
        )

@dp.message(Command("panel"))
async def cmd_panel(message: Message):
    """لوحة تحكم المدير"""
    user = db.get_user(message.from_user.id)
    if user and user.is_admin:
        await message.answer("👑 لوحة تحكم المدير", reply_markup=create_admin_panel())
    else:
        await message.answer("⚠️ ليس لديك صلاحية الوصول")

# ========== معالجة Callback Queries ==========

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """العودة للقائمة"""
    await callback.answer()
    await callback.message.edit_text(
        "🏠 القائمة الرئيسية",
        reply_markup=create_main_menu(callback.from_user.id)
    )

@dp.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: CallbackQuery):
    """فتح لوحة التحكم"""
    await callback.answer()
    user = db.get_user(callback.from_user.id)
    if user and user.is_admin:
        await callback.message.edit_text(
            "👑 لوحة تحكم المدير",
            reply_markup=create_admin_panel()
        )
    else:
        await callback.answer("⚠️ ليس لديك صلاحية الوصول", show_alert=True)

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    """عرض الإحصائيات"""
    await callback.answer()
    
    stats = db.stats
    total_balance = sum(u.balance for u in db.users.values())
    total_revenue = stats.get('total_revenue', 0)
    
    stats_msg = format_arabic(f"""
📊 إحصائيات البوت:

👥 إجمالي المستخدمين: {format_number(stats.get('total_users', 0))}
📅 المستخدمين النشطين اليوم: {format_number(stats.get('active_today', 0))}

💰 إجمالي الأرصدة: {format_number(total_balance)} دينار
💵 إجمالي الإيرادات: {format_number(total_revenue)} دينار

🛒 إجمالي الخدمات المباعة: {format_number(stats.get('total_services', 0))}

📈 أسعار الخدمات:
• حساب الإعفاء: {format_number(db.settings['service_prices']['exemption'])} دينار
• تلخيص PDF: {format_number(db.settings['service_prices']['summarize'])} دينار
• سؤال وجواب: {format_number(db.settings['service_prices']['qa'])} دينار
• قسم الملازم: {format_number(db.settings['service_prices']['materials'])} دينار

🎁 مكافأة الدعوة: {format_number(db.settings['invite_reward'])} دينار
⚙️ وضع الصيانة: {'مفعل' if db.settings.get('maintenance') else 'معطل'}
    """)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ العودة", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(stats_msg, reply_markup=keyboard)

@dp.callback_query(F.data == "admin_charge")
async def admin_charge_handler(callback: CallbackQuery, state: FSMContext):
    """بدء عملية الشحن"""
    await callback.answer()
    await state.set_state(UserStates.admin_waiting_user_id)
    await callback.message.answer("🆔 أرسل ايدي المستخدم للشحن:")

@dp.callback_query(F.data == "admin_prices")
async def admin_prices_handler(callback: CallbackQuery):
    """عرض أسعار الخدمات"""
    await callback.answer()
    
    prices = db.settings['service_prices']
    prices_msg = format_arabic(f"""
💵 أسعار الخدمات الحالية:

1. حساب درجة الإعفاء الفردي: {format_number(prices['exemption'])} دينار
2. تلخيص الملازم: {format_number(prices['summarize'])} دينار
3. سؤال وجواب: {format_number(prices['qa'])} دينار
4. قسم الملازم: {format_number(prices['materials'])} دينار

اختر الخدمة لتعديل سعرها:
    """)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1. حساب الإعفاء", callback_data="admin_price_exemption"),
            InlineKeyboardButton(text="2. تلخيص PDF", callback_data="admin_price_summarize")
        ],
        [
            InlineKeyboardButton(text="3. سؤال وجواب", callback_data="admin_price_qa"),
            InlineKeyboardButton(text="4. قسم الملازم", callback_data="admin_price_materials")
        ],
        [InlineKeyboardButton(text="↩️ العودة", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(prices_msg, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("admin_price_"))
async def admin_update_price_handler(callback: CallbackQuery, state: FSMContext):
    """بدء تحديث سعر خدمة"""
    await callback.answer()
    service = callback.data.replace("admin_price_", "")
    await state.update_data(service_to_update=service)
    await state.set_state(UserStates.admin_waiting_price_service)
    
    service_names = {
        'exemption': 'حساب درجة الإعفاء الفردي',
        'summarize': 'تلخيص الملازم',
        'qa': 'سؤال وجواب',
        'materials': 'قسم الملازم'
    }
    
    current_price = db.settings['service_prices'][service]
    
    await callback.message.answer(
        format_arabic(f"""
💵 تحديث سعر خدمة '{service_names.get(service, service)}'

السعر الحالي: {format_number(current_price)} دينار

أدخل السعر الجديد (بالدينار العراقي):
        """)
    )

@dp.callback_query(F.data == "admin_maintenance")
async def admin_maintenance_handler(callback: CallbackQuery):
    """تفعيل/تعطيل الصيانة"""
    await callback.answer()
    
    current = db.settings.get('maintenance', False)
    db.settings['maintenance'] = not current
    db.save_settings()
    
    status = "مفعل" if not current else "معطل"
    await callback.message.answer(f"⚙️ تم {status} وضع الصيانة")
    
    # إشعار للمستخدمين
    if not current:  # إذا تم تفعيل الصيانة
        for user_id in db.users:
            if user_id != ADMIN_ID:
                await send_notification(user_id, "⚠️ البوت قيد الصيانة حالياً. نعتذر للإزعاج وسنعود قريباً.")

@dp.callback_query(F.data == "admin_materials")
async def admin_materials_handler(callback: CallbackQuery):
    """إدارة الملازم"""
    await callback.answer()
    
    materials = db.get_all_materials()
    materials_msg = format_arabic(f"""
📚 إدارة الملازم والمرشحات

إجمالي الملازم: {len(materials)}

اختر الإجراء المطلوب:
    """)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة ملزمة جديدة", callback_data="admin_add_material")],
        [InlineKeyboardButton(text="🗑️ حذف ملزمة", callback_data="admin_delete_material")],
        [InlineKeyboardButton(text="📋 عرض جميع الملازم", callback_data="admin_view_materials")],
        [InlineKeyboardButton(text="↩️ العودة", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(materials_msg, reply_markup=keyboard)

@dp.callback_query(F.data == "admin_invite_reward")
async def admin_invite_reward_handler(callback: CallbackQuery, state: FSMContext):
    """تعديل مكافأة الدعوة"""
    await callback.answer()
    await state.set_state(UserStates.admin_waiting_invite_reward)
    current = db.settings['invite_reward']
    await callback.message.answer(
        f"🎁 المكافأة الحالية: {format_number(current)} دينار\n\nأدخل المكافأة الجديدة:"
    )

@dp.callback_query(F.data == "admin_update_channel")
async def admin_update_channel_handler(callback: CallbackQuery, state: FSMContext):
    """تحديث رابط القناة"""
    await callback.answer()
    await state.set_state(UserStates.admin_waiting_channel_link)
    current = db.settings.get('channel_link', 'غير محدد')
    await callback.message.answer(f"🔗 الرابط الحالي: {current}\n\nأرسل الرابط الجديد:")

# ========== معالجة الرسائل النصية ==========

@dp.message(UserStates.admin_waiting_user_id)
async def process_user_id(message: Message, state: FSMContext):
    """معالجة ايدي المستخدم للشحن"""
    try:
        user_id = int(message.text)
        await state.update_data(target_user_id=user_id)
        await state.set_state(UserStates.admin_waiting_amount)
        await message.answer("💵 أدخل المبلغ المطلوب شحنه:")
    except:
        await message.answer("⚠️ الرجاء إدخال ايدي صحيح")

@dp.message(UserStates.admin_waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    """معالجة مبلغ الشحن"""
    try:
        amount = int(message.text)
        data = await state.get_data()
        user_id = data['target_user_id']
        
        user = db.get_user(user_id)
        if user:
            user.balance += amount
            db.update_user(user)
            
            await message.answer(f"✅ تم شحن {format_number(amount)} دينار للمستخدم {user_id}")
            
            # إشعار للمستخدم
            await send_notification(user_id, 
                f"💰 تم إضافة {format_number(amount)} دينار لرصيدك\nرصيدك الجديد: {format_number(user.balance)} دينار")
        else:
            await message.answer("⚠️ المستخدم غير موجود")
        
        await state.clear()
    except:
        await message.answer("⚠️ الرجاء إدخال مبلغ صحيح")

@dp.message(UserStates.admin_waiting_price_service)
async def process_new_price(message: Message, state: FSMContext):
    """معالجة السعر الجديد"""
    try:
        price = int(message.text)
        data = await state.get_data()
        service = data['service_to_update']
        
        db.settings['service_prices'][service] = price
        db.save_settings()
        
        service_names = {
            'exemption': 'حساب درجة الإعفاء الفردي',
            'summarize': 'تلخيص الملازم',
            'qa': 'سؤال وجواب',
            'materials': 'قسم الملازم'
        }
        
        await message.answer(
            f"✅ تم تحديث سعر '{service_names.get(service, service)}' إلى {format_number(price)} دينار",
            reply_markup=create_admin_panel()
        )
        await state.clear()
    except:
        await message.answer("⚠️ الرجاء إدخال سعر صحيح")

@dp.message(UserStates.admin_waiting_invite_reward)
async def process_invite_reward(message: Message, state: FSMContext):
    """معالجة مكافأة الدعوة الجديدة"""
    try:
        reward = int(message.text)
        if reward >= 0:
            db.settings['invite_reward'] = reward
            db.save_settings()
            await message.answer(f"✅ تم تحديث مكافأة الدعوة إلى {format_number(reward)} دينار")
        else:
            await message.answer("⚠️ يرجى إدخال قيمة موجبة")
    except:
        await message.answer("⚠️ يرجى إدخال رقم صحيح")
    await state.clear()

@dp.message(UserStates.admin_waiting_channel_link)
async def process_channel_link(message: Message, state: FSMContext):
    """معالجة رابط القناة الجديد"""
    link = message.text
    if link.startswith("http"):
        db.settings['channel_link'] = link
        db.save_settings()
        await message.answer(f"✅ تم تحديث رابط القناة إلى:\n{link}")
    else:
        await message.answer("⚠️ يرجى إرسال رابط يبدأ بـ http أو https")
    await state.clear()

# ========== معالجة خدمات المستخدمين ==========

@dp.callback_query(F.data.startswith("service_"))
async def handle_service_request(callback: CallbackQuery, state: FSMContext):
    """معالجة طلب خدمة"""
    await callback.answer()
    
    user_id = callback.from_user.id
    service_type = callback.data.replace("service_", "")
    
    if check_maintenance(user_id):
        await callback.message.answer("⚙️ البوت قيد الصيانة حالياً.")
        return
    
    user = db.get_user(user_id)
    if not user:
        return
    
    price = db.settings['service_prices'].get(service_type, 1000)
    
    if user.balance < price:
        await callback.message.answer(
            f"💰 رصيدك غير كافي\nالسعر: {format_number(price)} دينار\nرصيدك: {format_number(user.balance)} دينار"
        )
        return
    
    if service_type == "exemption":
        await state.set_state(UserStates.waiting_for_course1)
        await callback.message.answer("📝 أدخل درجة الكورس الأول (0-100):")
    
    elif service_type == "summarize":
        await state.set_state(UserStates.waiting_for_pdf)
        await callback.message.answer(f"📄 أرسل ملف PDF لتلخيصه (السعر: {format_number(price)} دينار)")
    
    elif service_type == "qa":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 نص", callback_data="qa_text"),
                InlineKeyboardButton(text="🖼️ صورة", callback_data="qa_image")
            ],
            [InlineKeyboardButton(text="↩️ إلغاء", callback_data="back_to_menu")]
        ])
        await callback.message.answer(
            f"❓ اختر طريقة إرسال السؤال (السعر: {format_number(price)} دينار):",
            reply_markup=keyboard
        )
    
    elif service_type == "materials":
        materials = db.get_all_materials()
        if materials:
            stages = set(m.stage for m in materials)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            
            for stage in stages:
                count = len([m for m in materials if m.stage == stage])
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text=f"📚 {stage} ({count})", callback_data=f"materials_stage_{stage}")
                ])
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="↩️ العودة", callback_data="back_to_menu")
            ])
            
            await callback.message.answer(
                f"📚 اختر المرحلة الدراسية (السعر: {format_number(price)} دينار):",
                reply_markup=keyboard
            )
        else:
            await callback.message.answer("⚠️ لا توجد ملازم متاحة حالياً.")

# ========== معالجة درجات الإعفاء ==========

@dp.message(UserStates.waiting_for_course1)
async def process_course1(message: Message, state: FSMContext):
    """معالجة درجة الكورس الأول"""
    try:
        grade = float(message.text)
        if 0 <= grade <= 100:
            await state.update_data(course1=grade)
            await state.set_state(UserStates.waiting_for_course2)
            await message.answer("📝 أدخل درجة الكورس الثاني (0-100):")
        else:
            await message.answer("⚠️ الرجاء إدخال درجة بين 0 و 100")
    except:
        await message.answer("⚠️ الرجاء إدخال رقم صحيح")

@dp.message(UserStates.waiting_for_course2)
async def process_course2(message: Message, state: FSMContext):
    """معالجة درجة الكورس الثاني"""
    try:
        grade = float(message.text)
        if 0 <= grade <= 100:
            await state.update_data(course2=grade)
            await state.set_state(UserStates.waiting_for_course3)
            await message.answer("📝 أدخل درجة الكورس الثالث (0-100):")
        else:
            await message.answer("⚠️ الرجاء إدخال درجة بين 0 و 100")
    except:
        await message.answer("⚠️ الرجاء إدخال رقم صحيح")

@dp.message(UserStates.waiting_for_course3)
async def process_course3(message: Message, state: FSMContext):
    """معالجة درجة الكورس الثالث وحساب المعدل"""
    try:
        grade = float(message.text)
        if 0 <= grade <= 100:
            data = await state.get_data()
            avg = (data['course1'] + data['course2'] + grade) / 3
            
            user_id = message.from_user.id
            user = db.get_user(user_id)
            price = db.settings['service_prices']['exemption']
            
            if user.balance >= price:
                user.balance -= price
                user.total_spent += price
                db.update_user(user)
                
                # تحديث الإحصائيات
                db.stats['total_services'] = db.stats.get('total_services', 0) + 1
                db.stats['total_revenue'] = db.stats.get('total_revenue', 0) + price
                db.save_stats()
                
                if avg >= 90:
                    result_msg = format_arabic(f"""
🎉 مبروك! تم حساب معدلك بنجاح:

📊 الدرجات المدخلة:
الكورس الأول: {data['course1']}
الكورس الثاني: {data['course2']}
الكورس الثالث: {grade}

⚖️ المعدل النهائي: {avg:.2f}

🏆 أنت معفي من المادة! 
تهانينا على هذا الإنجاز!

💰 تم خصم: {format_number(price)} دينار
💳 رصيدك المتبقي: {format_number(user.balance)} دينار
                    """)
                else:
                    result_msg = format_arabic(f"""
📊 تم حساب معدلك بنجاح:

الدرجات المدخلة:
الكورس الأول: {data['course1']}
الكورس الثاني: {data['course2']}
الكورس الثالث: {grade}

⚖️ المعدل النهائي: {avg:.2f}

⚠️ للأسف، أنت لست معفياً من المادة.
المعدل المطلوب للإعفاء: 90

💰 تم خصم: {format_number(price)} دينار
💳 رصيدك المتبقي: {format_number(user.balance)} دينار
                    """)
                
                await message.answer(result_msg, reply_markup=create_main_menu(user_id))
                await state.clear()
            else:
                await message.answer(f"💰 رصيدك غير كافي. تحتاج {format_number(price)} دينار")
                await state.clear()
        else:
            await message.answer("⚠️ الرجاء إدخال درجة بين 0 و 100")
    except:
        await message.answer("⚠️ الرجاء إدخال رقم صحيح")

# ========== بدء التشغيل ==========

async def on_startup():
    """دالة بدء التشغيل"""
    logger.info("✅ بدأ تشغيل بوت 'يلا نتعلم'...")
    
    # إرسال إشعار للمدير
    try:
        await bot.send_message(
            ADMIN_ID,
            format_arabic(f"""
🤖 بوت 'يلا نتعلم' يعمل الآن!

👥 المستخدمين: {db.stats.get('total_users', 0)}
💰 إجمالي الإيرادات: {format_number(db.stats.get('total_revenue', 0))} دينار
🕒 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """)
        )
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال إشعار البدء: {e}")

async def on_shutdown():
    """دالة إيقاف التشغيل"""
    logger.info("⏹️ إيقاف البوت...")
    await bot.session.close()

if __name__ == "__main__":
    # تشغيل البوت
    async def main():
        await on_startup()
        await dp.start_polling(bot)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت يدوياً")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
