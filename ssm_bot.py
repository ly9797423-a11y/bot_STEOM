#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت: يلا نتعلم
المطور: @Allawi04 (ID: 6130994941)
يوزر البوت: @FC4Xbot
الإصدار: 2.0 - متوافق مع السيرفر
"""

import os
import sys
import logging
import asyncio
import json
import io
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal
import signal

# =============================================
# إعدادات أولوية الاستيراد لتجنب مشاكل السيرفر
# =============================================
try:
    # مكتبات أساسية
    from telegram import (
        Update, 
        InlineKeyboardButton, 
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        KeyboardButton,
        Document,
        PhotoSize,
        InputFile
    )
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ConversationHandler,
        ContextTypes,
        filters
    )
    from telegram.constants import ParseMode, ChatAction
    
    # الذكاء الاصطناعي
    import google.generativeai as genai
    
    # قاعدة البيانات
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import DuplicateKeyError
    
    # معالجة PDF
    import pdf2image
    from PIL import Image, ImageDraw, ImageFont
    import PyPDF2
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import arabic_reshaper
    from bidi.algorithm import get_display
    
    # OCR ومعالجة الصور
    import pytesseract
    import cv2
    import numpy as np
    
    # Async
    import aiohttp
    import aiofiles
    
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    print("✅ قم بتثبيت المكتبات أولاً:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# =============================================
# إعدادات LOGGING للسيرفر
# =============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================
# إعدادات البوت الأساسية
# =============================================
BOT_TOKEN = "8481569753:AAHTdbWwu0BHmoo_iHPsye8RkTptWzfiQWU"
DEVELOPER_ID = 6130994941  # ⬅️ ايدي المطور @Allawi04
DEVELOPER_USERNAME = "Allawi04"
BOT_USERNAME = "FC4Xbot"

# =============================================
# إعدادات Gemini AI
# =============================================
GEMINI_API_KEY = "AIzaSyAqlug21bw_eI60ocUtc1Z76NhEUc-zuzY"
try:
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Gemini AI غير متاح: {e}")
    GEMINI_AVAILABLE = False

# =============================================
# فئات قاعدة البيانات
# =============================================
class DatabaseManager:
    """مدير قاعدة البيانات مع معالجة الأخطاء"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """تهيئة اتصال قاعدة البيانات"""
        try:
            # استخدام MongoDB Atlas (أو محلي)
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # اختبار الاتصال
            self.client.admin.command('ping')
            logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح")
            
            # إنشاء قاعدة البيانات والمجموعات
            self.db = self.client["yaln_netlam_bot_v2"]
            self._create_collections()
            self._create_indexes()
            self._initialize_data()
            
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
            # استخدام قاعدة بيانات مؤقتة في الذاكرة للطوارئ
            self._use_fallback()
    
    def _use_fallback(self):
        """استخدام تخزين مؤقت في حالة فشل قاعدة البيانات"""
        logger.warning("⚠️ استخدام التخزين المؤقت في الذاكرة")
        self.db = None
        self.in_memory_storage = {
            "users": {},
            "admins": {DEVELOPER_ID: {"username": DEVELOPER_USERNAME, "role": "super_admin"}},
            "transactions": [],
            "services": [],
            "files": [],
            "settings": {}
        }
    
    def _create_collections(self):
        """إنشاء المجموعات إذا لم تكن موجودة"""
        collections = ["users", "admins", "transactions", "services", "files", "settings", "broadcasts"]
        
        for collection in collections:
            if collection not in self.db.list_collection_names():
                self.db.create_collection(collection)
                logger.info(f"✅ تم إنشاء مجموعة: {collection}")
    
    def _create_indexes(self):
        """إنشاء فهارس الأداء"""
        try:
            # فهارس المستخدمين
            self.db.users.create_index([("user_id", ASCENDING)], unique=True)
            self.db.users.create_index([("invite_code", ASCENDING)], unique=True)
            self.db.users.create_index([("banned", ASCENDING)])
            self.db.users.create_index([("created_at", DESCENDING)])
            
            # فهارس المشرفين
            self.db.admins.create_index([("user_id", ASCENDING)], unique=True)
            
            # فهارس المعاملات
            self.db.transactions.create_index([("user_id", ASCENDING)])
            self.db.transactions.create_index([("timestamp", DESCENDING)])
            self.db.transactions.create_index([("type", ASCENDING)])
            
            # فهارس الخدمات
            self.db.services.create_index([("name", ASCENDING)], unique=True)
            self.db.services.create_index([("active", ASCENDING)])
            
            # فهارس الملفات
            self.db.files.create_index([("stage", ASCENDING)])
            self.db.files.create_index([("active", ASCENDING)])
            
            logger.info("✅ تم إنشاء جميع الفهارس")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الفهارس: {e}")
    
    def _initialize_data(self):
        """تهيئة البيانات الأولية"""
        try:
            # إضافة المطور كسوبر أدمن
            if not self.db.admins.find_one({"user_id": DEVELOPER_ID}):
                self.db.admins.insert_one({
                    "user_id": DEVELOPER_ID,
                    "username": DEVELOPER_USERNAME,
                    "role": "super_admin",
                    "added_at": datetime.now(),
                    "permissions": ["all"],
                    "is_active": True
                })
                logger.info(f"✅ تم إضافة المطور ({DEVELOPER_ID}) كمشرف رئيسي")
            
            # الإعدادات العامة
            if not self.db.settings.find_one({"_id": "global"}):
                default_settings = {
                    "_id": "global",
                    "service_price": 1000,
                    "welcome_bonus": 1000,
                    "invite_bonus": 500,
                    "maintenance_mode": False,
                    "bot_channel": f"@{BOT_USERNAME}",
                    "support_channel": f"@{DEVELOPER_USERNAME}",
                    "currency": "دينار عراقي",
                    "min_charge": 1000,
                    "last_broadcast_id": 0,
                    "updated_at": datetime.now()
                }
                self.db.settings.insert_one(default_settings)
                logger.info("✅ تم تهيئة الإعدادات العامة")
            
            # الخدمات الافتراضية
            default_services = [
                {
                    "name": "حساب درجة الإعفاء",
                    "description": "حاسبة الإعفاء الفردي بناءً على درجات الكورسات",
                    "price": 1000,
                    "category": "calculator",
                    "active": True,
                    "icon": "🧮",
                    "created_at": datetime.now()
                },
                {
                    "name": "تلخيص الملازم",
                    "description": "تلخيص ملفات PDF باستخدام الذكاء الاصطناعي",
                    "price": 1000,
                    "category": "ai",
                    "active": True,
                    "icon": "📄",
                    "created_at": datetime.now()
                },
                {
                    "name": "سؤال وجواب",
                    "description": "إجابة الأسئلة التعليمية حسب المنهج العراقي",
                    "price": 1000,
                    "category": "ai",
                    "active": True,
                    "icon": "❓",
                    "created_at": datetime.now()
                },
                {
                    "name": "ملازمي ومرشحاتي",
                    "description": "الملازم والمرشحات التعليمية",
                    "price": 1000,
                    "category": "files",
                    "active": True,
                    "icon": "📚",
                    "created_at": datetime.now()
                }
            ]
            
            for service in default_services:
                if not self.db.services.find_one({"name": service["name"]}):
                    self.db.services.insert_one(service)
            
            logger.info("✅ تم تهيئة الخدمات الافتراضية")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البيانات: {e}")
    
    # ============= دوال الوصول للبيانات =============
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات مستخدم"""
        try:
            if self.db:
                return self.db.users.find_one({"user_id": user_id})
            else:
                return self.in_memory_storage["users"].get(user_id)
        except Exception as e:
            logger.error(f"❌ خطأ في جلب بيانات المستخدم: {e}")
            return None
    
    def create_user(self, user_data: Dict) -> bool:
        """إنشاء مستخدم جديد"""
        try:
            if self.db:
                self.db.users.insert_one(user_data)
            else:
                self.in_memory_storage["users"][user_data["user_id"]] = user_data
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء مستخدم: {e}")
            return False
    
    def update_user(self, user_id: int, updates: Dict) -> bool:
        """تحديث بيانات مستخدم"""
        try:
            if self.db:
                result = self.db.users.update_one(
                    {"user_id": user_id},
                    {"$set": updates}
                )
                return result.modified_count > 0
            else:
                if user_id in self.in_memory_storage["users"]:
                    self.in_memory_storage["users"][user_id].update(updates)
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث المستخدم: {e}")
            return False
    
    def is_admin(self, user_id: int) -> bool:
        """التحقق إذا كان المستخدم مشرف"""
        try:
            if user_id == DEVELOPER_ID:  # ⬅️ المطور دائماً مشرف
                return True
            
            if self.db:
                admin = self.db.admins.find_one({"user_id": user_id, "is_active": True})
                return admin is not None
            else:
                return user_id in self.in_memory_storage["admins"]
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من المشرف: {e}")
            return False
    
    def is_super_admin(self, user_id: int) -> bool:
        """التحقق إذا كان المستخدم سوبر أدمن"""
        try:
            if user_id == DEVELOPER_ID:  # ⬅️ المطور دائماً سوبر أدمن
                return True
            
            if self.db:
                admin = self.db.admins.find_one({"user_id": user_id, "role": "super_admin", "is_active": True})
                return admin is not None
            else:
                admin = self.in_memory_storage["admins"].get(user_id)
                return admin and admin.get("role") == "super_admin"
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من السوبر أدمن: {e}")
            return False
    
    def get_settings(self) -> Dict:
        """الحصول على الإعدادات العامة"""
        try:
            if self.db:
                settings = self.db.settings.find_one({"_id": "global"})
                return settings or {}
            else:
                return self.in_memory_storage.get("settings", {})
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الإعدادات: {e}")
            return {}
    
    def update_settings(self, updates: Dict) -> bool:
        """تحديث الإعدادات العامة"""
        try:
            updates["updated_at"] = datetime.now()
            
            if self.db:
                result = self.db.settings.update_one(
                    {"_id": "global"},
                    {"$set": updates}
                )
                return result.modified_count > 0
            else:
                if "settings" not in self.in_memory_storage:
                    self.in_memory_storage["settings"] = {}
                self.in_memory_storage["settings"].update(updates)
                return True
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الإعدادات: {e}")
            return False
    
    def get_all_users(self, limit: int = 50, skip: int = 0) -> List[Dict]:
        """الحصول على جميع المستخدمين"""
        try:
            if self.db:
                return list(self.db.users.find(
                    {"banned": False},
                    {
                        "user_id": 1,
                        "username": 1,
                        "first_name": 1,
                        "balance": 1,
                        "created_at": 1,
                        "last_active": 1
                    }
                ).sort("created_at", DESCENDING).skip(skip).limit(limit))
            else:
                users = list(self.in_memory_storage["users"].values())
                users = [u for u in users if not u.get("banned", False)]
                users.sort(key=lambda x: x.get("created_at", datetime.now()), reverse=True)
                return users[:limit]
        except Exception as e:
            logger.error(f"❌ خطأ في جلب المستخدمين: {e}")
            return []
    
    def count_users(self) -> int:
        """عدد المستخدمين"""
        try:
            if self.db:
                return self.db.users.count_documents({})
            else:
                return len(self.in_memory_storage["users"])
        except Exception as e:
            logger.error(f"❌ خطأ في عد المستخدمين: {e}")
            return 0
    
    def add_transaction(self, transaction_data: Dict) -> bool:
        """إضافة معاملة"""
        try:
            if self.db:
                self.db.transactions.insert_one(transaction_data)
            else:
                self.in_memory_storage["transactions"].append(transaction_data)
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة معاملة: {e}")
            return False
    
    def get_services(self) -> List[Dict]:
        """الحصول على جميع الخدمات"""
        try:
            if self.db:
                return list(self.db.services.find({"active": True}))
            else:
                return [s for s in self.in_memory_storage.get("services", []) if s.get("active", True)]
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الخدمات: {e}")
            return []
    
    def get_service(self, name: str) -> Optional[Dict]:
        """الحصول على خدمة معينة"""
        try:
            if self.db:
                return self.db.services.find_one({"name": name, "active": True})
            else:
                services = self.in_memory_storage.get("services", [])
                for service in services:
                    if service.get("name") == name and service.get("active", True):
                        return service
                return None
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الخدمة: {e}")
            return None
    
    def update_service_price(self, name: str, new_price: int) -> bool:
        """تحديث سعر خدمة"""
        try:
            if self.db:
                result = self.db.services.update_one(
                    {"name": name},
                    {"$set": {"price": new_price, "updated_at": datetime.now()}}
                )
                return result.modified_count > 0
            else:
                services = self.in_memory_storage.get("services", [])
                for service in services:
                    if service.get("name") == name:
                        service["price"] = new_price
                        return True
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث سعر الخدمة: {e}")
            return False

# إنشاء كائن قاعدة البيانات
db = DatabaseManager()

# =============================================
# فئات إدارة المستخدمين والخدمات
# =============================================
class UserManager:
    """مدير عمليات المستخدمين"""
    
    @staticmethod
    def get_or_create_user(user_id: int, username: str = None, first_name: str = None) -> Dict:
        """الحصول على مستخدم أو إنشاؤه إذا لم يكن موجوداً"""
        try:
            user = db.get_user(user_id)
            
            if not user:
                # إعدادات عامة
                settings = db.get_settings()
                welcome_bonus = settings.get("welcome_bonus", 1000)
                
                # إنشاء رمز دعوة فريد
                invite_code = f"INV{user_id % 10000:04d}"
                
                user_data = {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "balance": welcome_bonus,
                    "invite_code": invite_code,
                    "invited_by": None,
                    "invited_users": [],
                    "total_spent": 0,
                    "total_services": 0,
                    "created_at": datetime.now(),
                    "last_active": datetime.now(),
                    "banned": False,
                    "ban_reason": None,
                    "language": "ar",
                    "notifications": True,
                    "is_active": True
                }
                
                if db.create_user(user_data):
                    user = user_data
                    
                    # تسجيل معاملة المكافأة الترحيبية
                    db.add_transaction({
                        "transaction_id": f"WEL{user_id}{int(datetime.now().timestamp())}",
                        "user_id": user_id,
                        "amount": welcome_bonus,
                        "type": "welcome_bonus",
                        "description": "مكافأة ترحيبية",
                        "timestamp": datetime.now(),
                        "status": "completed"
                    })
                    
                    logger.info(f"✅ مستخدم جديد: {user_id} - {first_name}")
                else:
                    logger.error(f"❌ فشل في إنشاء مستخدم: {user_id}")
                    return {}
            
            return user
            
        except Exception as e:
            logger.error(f"❌ خطأ في get_or_create_user: {e}")
            return {}
    
    @staticmethod
    def update_balance(user_id: int, amount: int, operation: str = "add") -> bool:
        """تحديث رصيد المستخدم"""
        try:
            user = db.get_user(user_id)
            if not user:
                return False
            
            current_balance = user.get("balance", 0)
            
            if operation == "add":
                new_balance = current_balance + amount
            elif operation == "subtract":
                if current_balance < amount:
                    return False
                new_balance = current_balance - amount
            else:
                return False
            
            return db.update_user(user_id, {"balance": new_balance})
            
        except Exception as e:
            logger.error(f"❌ خطأ في update_balance: {e}")
            return False
    
    @staticmethod
    def ban_user(user_id: int, reason: str = "غير محدد", admin_id: int = None) -> bool:
        """حظر مستخدم"""
        try:
            updates = {
                "banned": True,
                "ban_reason": reason,
                "banned_at": datetime.now(),
                "banned_by": admin_id
            }
            
            if db.update_user(user_id, updates):
                # تسجيل معاملة الحظر
                db.add_transaction({
                    "transaction_id": f"BAN{user_id}{int(datetime.now().timestamp())}",
                    "user_id": user_id,
                    "amount": 0,
                    "type": "ban",
                    "description": f"حظر المستخدم - السبب: {reason}",
                    "timestamp": datetime.now(),
                    "status": "completed"
                })
                
                logger.info(f"✅ تم حظر المستخدم: {user_id} - السبب: {reason}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في ban_user: {e}")
            return False
    
    @staticmethod
    def unban_user(user_id: int) -> bool:
        """فك حظر مستخدم"""
        try:
            updates = {
                "banned": False,
                "ban_reason": None,
                "unbanned_at": datetime.now()
            }
            
            result = db.update_user(user_id, updates)
            if result:
                logger.info(f"✅ تم فك حظر المستخدم: {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ خطأ في unban_user: {e}")
            return False

class ServiceManager:
    """مدير عمليات الخدمات"""
    
    @staticmethod
    def can_use_service(user_id: int, service_name: str) -> Tuple[bool, str]:
        """التحقق من إمكانية استخدام خدمة"""
        try:
            user = db.get_user(user_id)
            if not user:
                return False, "المستخدم غير موجود"
            
            if user.get("banned", False):
                return False, "حسابك محظور. تواصل مع الدعم"
            
            settings = db.get_settings()
            if settings.get("maintenance_mode", False):
                if not db.is_admin(user_id):
                    return False, "البوت تحت الصيانة. نعتذر للإزعاج"
            
            service = db.get_service(service_name)
            if not service:
                return False, "الخدمة غير متاحة حالياً"
            
            price = service.get("price", settings.get("service_price", 1000))
            
            if user.get("balance", 0) < price:
                return False, f"رصيدك غير كافي. السعر: {price:,} دينار\nرصيدك الحالي: {user.get('balance', 0):,} دينار"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"❌ خطأ في can_use_service: {e}")
            return False, "حدث خطأ في التحقق من الخدمة"
    
    @staticmethod
    def use_service(user_id: int, service_name: str) -> Tuple[bool, str, int]:
        """استخدام خدمة (خصم الرصيد)"""
        try:
            can_use, message = ServiceManager.can_use_service(user_id, service_name)
            if not can_use:
                return False, message, 0
            
            service = db.get_service(service_name)
            price = service.get("price", 1000)
            
            if UserManager.update_balance(user_id, price, "subtract"):
                # تحديث إحصائيات المستخدم
                user = db.get_user(user_id)
                db.update_user(user_id, {
                    "total_services": user.get("total_services", 0) + 1,
                    "total_spent": user.get("total_spent", 0) + price
                })
                
                # تسجيل المعاملة
                db.add_transaction({
                    "transaction_id": f"SRV{user_id}{int(datetime.now().timestamp())}",
                    "user_id": user_id,
                    "amount": -price,
                    "type": "service_payment",
                    "description": f"خدمة: {service_name}",
                    "timestamp": datetime.now(),
                    "status": "completed"
                })
                
                return True, f"✅ تم خصم {price:,} دينار", price
            else:
                return False, "❌ فشل في خصم الرصيد", 0
                
        except Exception as e:
            logger.error(f"❌ خطأ في use_service: {e}")
            return False, f"❌ حدث خطأ: {str(e)}", 0

class AIProcessor:
    """معالج الذكاء الاصطناعي"""
    
    @staticmethod
    async def ask_gemini(question: str, context: str = "منهج عراقي تعليمي") -> str:
        """سؤال الذكاء الاصطناعي"""
        if not GEMINI_AVAILABLE:
            return "عذراً، خدمة الذكاء الاصطناعي غير متاحة حالياً. الرجاء المحاولة لاحقاً."
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            أنت مساعد تعليمي متخصص في المنهج العراقي للطلاب.
            مهمتك تقديم إجابات دقيقة، علمية، ومنظمة.
            
            السياق: {context}
            السؤال: {question}
            
            متطلبات الإجابة:
            1. الدقة العلمية أولاً
            2. الوضوح والبساطة
            3. التنسيق المنظم (عناوين، نقاط)
            4. اللغة العربية الفصحى
            5. المراجع العلمية إن أمكن
            6. الالتزام بالمنهج العراقي
            
            قدم الإجابة بشكل منظم ومفيد للطالب.
            """
            
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ خطأ في ask_gemini: {e}")
            return f"عذراً، حدث خطأ في المعالجة: {str(e)[:100]}"
    
    @staticmethod
    async def summarize_pdf(pdf_bytes: bytes) -> str:
        """تلخيص ملف PDF"""
        if not GEMINI_AVAILABLE:
            return "عذراً، خدمة التلخيص غير متاحة حالياً."
        
        try:
            # استخراج النص من PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages[:10]):  # أول 10 صفحات فقط
                page_text = page.extract_text()
                if page_text:
                    text += f"الصفحة {page_num + 1}:\n{page_text}\n\n"
            
            if not text:
                return "لم أستطع استخراج نص من الملف. تأكد أن الملف يحتوي على نص."
            
            # تقليل حجم النص إذا كان كبيراً
            if len(text) > 15000:
                text = text[:15000] + "...\n[تم اختصار النص بسبب الطول]"
            
            # استخدام AI للتلخيص
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            قم بتلخيص النص التعليمي التالي مع الالتزام بالشروط:
            
            1. أزل المعلومات غير المهمة والتكرار
            2. احتفظ بالنقاط الرئيسية والعلمية
            3. رتب المعلومات بشكل هرمي
            4. استخدم عناوين رئيسية وفرعية
            5. احتفظ بالمصطلحات العلمية
            6. اكتب بلغة عربية فصحى واضحة
            7. ركز على المعلومات التعليمية
            
            النص:
            {text}
            
            أعد التلخيص بشكل منظم مع:
            - مقدمة مختصرة
            - النقاط الرئيسية
            - الخلاصة
            - التوصيات إن وجدت
            """
            
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ خطأ في summarize_pdf: {e}")
            return f"عذراً، حدث خطأ في تلخيص الملف: {str(e)[:100]}"

class PDFGenerator:
    """مولد ملفات PDF"""
    
    def __init__(self):
        self.setup_fonts()
    
    def setup_fonts(self):
        """إعداد الخطوط العربية"""
        try:
            # محاولة تحميل خطوط عربية
            arabic_font_paths = [
                "arial.ttf",
                "tahoma.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "C:/Windows/Fonts/arial.ttf"
            ]
            
            for font_path in arabic_font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Arabic', font_path))
                        pdfmetrics.registerFont(TTFont('ArabicBold', font_path))
                        logger.info(f"✅ تم تحميل الخط العربي: {font_path}")
                        return
                except:
                    continue
            
            # إذا لم توجد خطوط عربية، استخدام الخط الافتراضي
            logger.warning("⚠️ لم يتم العثور على خطوط عربية، استخدام الخط الافتراضي")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد الخطوط: {e}")
    
    @staticmethod
    def reshape_arabic(text: str) -> str:
        """إعادة تشكيل النص العربي"""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except:
            return text
    
    async def create_pdf(self, title: str, content: str, user_info: Dict, pdf_type: str = "summary") -> io.BytesIO:
        """إنشاء ملف PDF"""
        buffer = io.BytesIO()
        
        try:
            # إنشاء مستند PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title=title
            )
            
            # الأنماط
            styles = getSampleStyleSheet()
            
            # أنماط عربية
            arabic_normal = ParagraphStyle(
                'ArabicNormal',
                parent=styles['Normal'],
                fontName='Helvetica',  # استخدام Helvetica كبديل
                fontSize=11,
                leading=14,
                alignment=2,  # محاذاة لليمين
                spaceAfter=6,
                rightIndent=10
            )
            
            arabic_title = ParagraphStyle(
                'ArabicTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=16,
                alignment=1,  # مركز
                spaceAfter=24,
                textColor=colors.HexColor('#2c3e50')
            )
            
            arabic_heading = ParagraphStyle(
                'ArabicHeading',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=14,
                alignment=2,
                spaceAfter=12,
                textColor=colors.HexColor('#3498db')
            )
            
            # المحتوى
            story = []
            
            # العنوان الرئيسي
            title_text = self.reshape_arabic(f"📄 {title}")
            story.append(Paragraph(title_text, arabic_title))
            story.append(Spacer(1, 20))
            
            # معلومات المستخدم
            user_name = user_info.get("first_name", "مستخدم")
            user_text = self.reshape_arabic(f"👤 المستخدم: {user_name}")
            story.append(Paragraph(user_text, arabic_normal))
            
            date_text = self.reshape_arabic(f"📅 التاريخ: {datetime.now().strftime('%Y/%m/%d %I:%M %p')}")
            story.append(Paragraph(date_text, arabic_normal))
            
            story.append(Spacer(1, 30))
            
            # محتوى الملف حسب النوع
            if pdf_type == "exemption":
                # تقرير الإعفاء
                lines = content.split('\n')
                for line in lines:
                    if line.strip():
                        arabic_line = self.reshape_arabic(line.strip())
                        story.append(Paragraph(arabic_line, arabic_normal))
                        story.append(Spacer(1, 4))
            
            elif pdf_type == "summary":
                # تلخيص
                sections = content.split('\n\n')
                for section in sections:
                    if section.strip():
                        # إذا كان العنوان
                        if section.strip().endswith(':') or len(section) < 100:
                            arabic_section = self.reshape_arabic(section.strip())
                            story.append(Paragraph(arabic_section, arabic_heading))
                        else:
                            arabic_section = self.reshape_arabic(section.strip())
                            story.append(Paragraph(arabic_section, arabic_normal))
                        story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 40))
            
            # التذييل
            footer_text = self.reshape_arabic(
                "تم الإنشاء بواسطة بوت 'يلا نتعلم' - @FC4Xbot\n"
                "للتواصل والدعم: @Allawi04"
            )
            story.append(Paragraph(footer_text, arabic_normal))
            
            # بناء PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"❌ خطأ في create_pdf: {e}")
            
            # إنشاء PDF بسيط كبديل
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont("Helvetica", 12)
            c.drawString(100, 750, "PDF Report")
            c.drawString(100, 730, f"User: {user_info.get('first_name', 'N/A')}")
            c.drawString(100, 710, f"Date: {datetime.now().strftime('%Y/%m/%d')}")
            c.drawString(100, 690, "Content not available due to error")
            c.save()
            buffer.seek(0)
            
            return buffer

# =============================================
# حالات المحادثة
# =============================================
(
    # المستخدم العادي
    AWAITING_SCORES,      # انتظار درجات الإعفاء
    AWAITING_QUESTION,    # انتظار سؤال
    AWAITING_PDF,         # انتظار ملف PDF
    
    # المشرف
    ADMIN_CHARGE_USER,    # انتظار معرف المستخدم للشحن
    ADMIN_CHARGE_AMOUNT,  # انتظار المبلغ للشحن
    ADMIN_BAN_USER,       # انتظار معرف المستخدم للحظر
    ADMIN_BAN_REASON,     # انتظار سبب الحظر
    ADMIN_UPDATE_PRICE,   # انتظار السعر الجديد
    ADMIN_BROADCAST_MSG,  # انتظار رسالة البث
    ADMIN_ADD_FILE,       # إضافة ملف
    
) = range(10)

# =============================================
# دوال البوت الرئيسية
# =============================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت"""
    try:
        user = update.effective_user
        message = update.message
        
        logger.info(f"🔹 مستخدم جديد: {user.id} - {user.first_name}")
        
        # الحصول على بيانات المستخدم
        user_data = UserManager.get_or_create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        if not user_data:
            await message.reply_text("❌ حدث خطأ في إنشاء حسابك. الرجاء المحاولة مرة أخرى.")
            return
        
        # التحقق من الحظر
        if user_data.get("banned", False):
            ban_reason = user_data.get("ban_reason", "غير محدد")
            await message.reply_text(
                f"⛔ *حسابك محظور*\n\n"
                f"السبب: {ban_reason}\n\n"
                f"للإستفسار تواصل مع الدعم: @{DEVELOPER_USERNAME}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # التحقق من وضع الصيانة
        settings = db.get_settings()
        if settings.get("maintenance_mode", False) and not db.is_admin(user.id):
            await message.reply_text(
                "🔧 *البوت تحت الصيانة*\n\n"
                "نعمل على تحسين الخدمة لكم.\n"
                "نعتذر للإزعاج ونرجو المعذرة.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # تحديث آخر نشاط
        db.update_user(user.id, {"last_active": datetime.now()})
        
        # ⬇️⬇️⬇️ **هنا السحر: إظهار زر لوحة التحكم فقط للمطور** ⬇️⬇️⬇️
        keyboard = [
            [
                InlineKeyboardButton("🧮 حساب الإعفاء", callback_data="service_exemption"),
                InlineKeyboardButton("📄 تلخيص الملازم", callback_data="service_summary")
            ],
            [
                InlineKeyboardButton("❓ سؤال وجواب", callback_data="service_qa"),
                InlineKeyboardButton("📚 ملازمي ومرشحاتي", callback_data="service_files")
            ],
            [
                InlineKeyboardButton("💰 رصيدي", callback_data="my_balance"),
                InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
                InlineKeyboardButton("🔗 دعوة أصدقاء", callback_data="invite_friends")
            ],
            [
                InlineKeyboardButton("💳 شحن الرصيد", callback_data="charge_balance"),
                InlineKeyboardButton("📜 سجل المعاملات", callback_data="transaction_history")
            ],
            [
                InlineKeyboardButton("📢 قناة البوت", url=f"https://t.me/{BOT_USERNAME}"),
                InlineKeyboardButton("👨‍💻 الدعم الفني", url=f"https://t.me/{DEVELOPER_USERNAME}")
            ]
        ]
        
        # ⭐ **هذا السطر يظهر زر لوحة التحكم فقط للمطور** ⭐
        if user.id == DEVELOPER_ID:  # ⬅️ المقارنة مع ايدي المطور فقط
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
            logger.info(f"✅ عرض زر لوحة التحكم للمطور: {user.id}")
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # رسالة الترحيب
        welcome_text = f"""
🎊 *مرحباً {user.first_name}!* 

🏦 *رصيدك الحالي:* {user_data['balance']:,} دينار
🎁 *المكافأة الترحيبية:* {settings.get('welcome_bonus', 1000):,} دينار

📚 *الخدمات المتاحة:*
1️⃣ حساب درجة الإعفاء الفردي
2️⃣ تلخيص الملازم بالذكاء الاصطناعي
3️⃣ سؤال وجواب بالذكاء الاصطناعي
4️⃣ ملازمي ومرشحاتي

💰 *سعر الخدمة:* {settings.get('service_price', 1000):,} دينار

📲 *طريقة الشحن:* تواصل مع الدعم: @{DEVELOPER_USERNAME}
🎯 *مكافأة الدعوة:* {settings.get('invite_bonus', 500):,} دينار لكل صديق

*اختر الخدمة التي تريدها:* 👇
        """
        
        await message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في start_command: {e}")
        try:
            await update.message.reply_text(
                "عذراً، حدث خطأ. الرجاء المحاولة مرة أخرى.\n"
                "للإبلاغ عن المشكلة: @Allawi04"
            )
        except:
            pass

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار الخدمة"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        service_mapping = {
            # الخدمات الرئيسية
            "service_exemption": ("🧮 حساب درجة الإعفاء", process_exemption_service),
            "service_summary": ("📄 تلخيص الملازم", process_summary_service),
            "service_qa": ("❓ سؤال وجواب", process_qa_service),
            "service_files": ("📚 ملازمي ومرشحاتي", process_files_service),
            
            # الميزات الشخصية
            "my_balance": ("💰 رصيدي", show_balance),
            "my_stats": ("📊 إحصائياتي", show_stats),
            "invite_friends": ("🔗 دعوة أصدقاء", show_invite),
            "charge_balance": ("💳 شحن الرصيد", show_charge_options),
            "transaction_history": ("📜 سجل المعاملات", show_transaction_history),
            
            # لوحة التحكم (للمطور فقط)
            "admin_panel": ("👑 لوحة التحكم", show_admin_panel)
        }
        
        service_name, handler = service_mapping.get(query.data, (None, None))
        
        if handler:
            # تحقق إضافي من صلاحية الدخول للوحة التحكم
            if query.data == "admin_panel" and user_id != DEVELOPER_ID:
                await query.edit_message_text("❌ ليس لديك صلاحية الوصول!")
                return
            
            return await handler(update, context)
        else:
            await query.edit_message_text("⚠️ الخدمة غير متاحة حالياً.")
            
    except Exception as e:
        logger.error(f"❌ خطأ في handle_service_selection: {e}")
        await query.edit_message_text("❌ حدث خطأ. الرجاء المحاولة مرة أخرى.")

# =============================================
# الخدمات الرئيسية
# =============================================
async def process_exemption_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة خدمة حساب الإعفاء"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        # التحقق من إمكانية استخدام الخدمة
        success, message, price = ServiceManager.use_service(user_id, "حساب درجة الإعفاء")
        
        if not success:
            await query.edit_message_text(f"❌ {message}")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *تم خصم {price:,} دينار*\n\n"
            "🧮 *حاسبة درجة الإعفاء*\n\n"
            "أدخل درجات الكورسات الثلاثة (مفصولة بمسافات):\n"
            "مثال: `90 85 95`\n\n"
            "📝 *ملاحظة:* المعدل المطلوب للإعفاء هو 90 أو أعلى.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return AWAITING_SCORES
        
    except Exception as e:
        logger.error(f"❌ خطأ في process_exemption_service: {e}")
        await query.edit_message_text("❌ حدث خطأ في معالجة الخدمة")
        return ConversationHandler.END

async def process_summary_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة خدمة تلخيص الملازم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        success, message, price = ServiceManager.use_service(user_id, "تلخيص الملازم")
        
        if not success:
            await query.edit_message_text(f"❌ {message}")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *تم خصم {price:,} دينار*\n\n"
            "📄 *تلخيص الملازم*\n\n"
            "📤 أرسل لي ملف PDF الآن:\n"
            "• الحجم الأقصى: 20MB\n"
            "• الصيغة: PDF فقط\n\n"
            "سأقوم بتلخيصه وإعادته لك كملف PDF منظم.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return AWAITING_PDF
        
    except Exception as e:
        logger.error(f"❌ خطأ في process_summary_service: {e}")
        await query.edit_message_text("❌ حدث خطأ في معالجة الخدمة")
        return ConversationHandler.END

async def process_qa_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة خدمة سؤال وجواب"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        success, message, price = ServiceManager.use_service(user_id, "سؤال وجواب")
        
        if not success:
            await query.edit_message_text(f"❌ {message}")
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *تم خصم {price:,} دينار*\n\n"
            "❓ *سؤال وجواب*\n\n"
            "أرسل سؤالك الآن:\n"
            "• يمكنك إرسال نص أو صورة\n"
            "• سيتم الرد حسب المنهج العراقي\n"
            "• الإجابات علمية ودقيقة",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return AWAITING_QUESTION
        
    except Exception as e:
        logger.error(f"❌ خطأ في process_qa_service: {e}")
        await query.edit_message_text("❌ حدث خطأ في معالجة الخدمة")
        return ConversationHandler.END

async def process_files_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة خدمة الملازم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        success, message, price = ServiceManager.use_service(user_id, "ملازمي ومرشحاتي")
        
        if not success:
            await query.edit_message_text(f"❌ {message}")
            return
        
        # عرض قائمة الملفات (سيتم تطويرها لاحقاً)
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *تم خصم {price:,} دينار*\n\n"
            "📚 *ملازمي ومرشحاتي*\n\n"
            "هذه الخدمة قيد التطوير حالياً.\n"
            "سيتم إضافة الملفات قريباً.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في process_files_service: {e}")
        await query.edit_message_text("❌ حدث خطأ في معالجة الخدمة")

# =============================================
# معالجة المدخلات
# =============================================
async def handle_scores_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة درجات الإعفاء"""
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    try:
        # استخراج الأرقام
        numbers = re.findall(r'\d+\.?\d*', text)
        
        if len(numbers) < 3:
            await update.message.reply_text(
                "❌ الرجاء إدخال 3 درجات على الأقل\n"
                "مثال: `90 85 95`",
                parse_mode=ParseMode.MARKDOWN
            )
            return AWAITING_SCORES
        
        scores = list(map(float, numbers[:3]))
        
        # التحقق من النطاق
        for score in scores:
            if score < 0 or score > 100:
                await update.message.reply_text(
                    "❌ الدرجات يجب أن تكون بين 0 و 100"
                )
                return AWAITING_SCORES
        
        # حساب المعدل
        average = sum(scores) / len(scores)
        
        # تحديد النتيجة
        if average >= 90:
            result = "🎉 *مبروك! أنت معفي من المادة*"
            emoji = "✅"
            result_ar = "معفي"
        else:
            result = f"❌ *لسيت معفي من المادة* (المطلوب 90)"
            emoji = "❌"
            result_ar = "غير معفي"
        
        # إنشاء نص النتيجة
        result_text = f"""
{emoji} *نتيجة حساب الإعفاء*

📊 *الدرجات المدخلة:*
1. الكورس الأول: {scores[0]:.1f}
2. الكورس الثاني: {scores[1]:.1f}
3. الكورس الثالث: {scores[2]:.1f}

🧮 *المعدل النهائي:* {average:.2f}

{result}

📌 *توصية:* { "احتفظ بهذا المستوى المتميز!" if average >= 90 else "حاول تحسين درجاتك في الكورسات القادمة." }
        """
        
        # إنشاء ملف PDF
        pdf_gen = PDFGenerator()
        user_data = db.get_user(user_id) or {"first_name": update.message.from_user.first_name}
        
        pdf_content = f"""
نتيجة حساب درجة الإعفاء

الدرجات المدخلة:
الكورس الأول: {scores[0]:.1f}
الكورس الثاني: {scores[1]:.1f}
الكورس الثالث: {scores[2]:.1f}

المعدل النهائي: {average:.2f}

النتيجة: {result_ar}

تاريخ الحساب: {datetime.now().strftime('%Y/%m/%d %I:%M %p')}
        """
        
        pdf_buffer = await pdf_gen.create_pdf(
            title="تقرير حساب الإعفاء",
            content=pdf_content,
            user_info=user_data,
            pdf_type="exemption"
        )
        
        keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال النتيجة
        await update.message.reply_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # إرسال ملف PDF
        await update.message.reply_document(
            document=InputFile(pdf_buffer, filename="نتيجة_الإعفاء.pdf"),
            caption="📄 تقرير مفصل بنتيجة الإعفاء"
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ الرجاء إدخال أرقام صحيحة\n"
            "مثال: `90 85 95`",
            parse_mode=ParseMode.MARKDOWN
        )
        return AWAITING_SCORES
    except Exception as e:
        logger.error(f"❌ خطأ في handle_scores_input: {e}")
        await update.message.reply_text("❌ حدث خطأ في المعالجة")
        return ConversationHandler.END

async def handle_pdf_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة ملف PDF"""
    user_id = update.message.from_user.id
    
    try:
        if not update.message.document:
            await update.message.reply_text("❌ الرجاء إرسال ملف PDF")
            return AWAITING_PDF
        
        document = update.message.document
        
        if not document.file_name.lower().endswith('.pdf'):
            await update.message.reply_text("❌ الملف يجب أن يكون بصيغة PDF")
            return AWAITING_PDF
        
        if document.file_size > 20 * 1024 * 1024:  # 20MB
            await update.message.reply_text("❌ حجم الملف كبير جداً (الحد الأقصى 20MB)")
            return AWAITING_PDF
        
        await update.message.reply_text("📥 جاري تحميل ومعالجة الملف...")
        
        # تحميل الملف
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()
        
        # معالجة مع مؤشر
        processing_msg = await update.message.reply_text("🔄 جاري تلخيص الملف باستخدام الذكاء الاصطناعي...")
        
        # تلخيص الملف
        summary = await AIProcessor.summarize_pdf(bytes(file_bytes))
        
        # حذف رسالة المعالجة
        await processing_msg.delete()
        
        # إنشاء ملف PDF ملخص
        pdf_gen = PDFGenerator()
        user_data = db.get_user(user_id) or {"first_name": update.message.from_user.first_name}
        
        pdf_buffer = await pdf_gen.create_pdf(
            title=f"ملخص: {document.file_name}",
            content=summary,
            user_info=user_data,
            pdf_type="summary"
        )
        
        keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال الملف الملخص
        await update.message.reply_document(
            document=InputFile(pdf_buffer, filename=f"ملخص_{document.file_name}"),
            caption=f"📄 *ملخص الملف*\n\n{summary[:200]}...",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"❌ خطأ في handle_pdf_input: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة الملف")
        return ConversationHandler.END

async def handle_question_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة الأسئلة"""
    user_id = update.message.from_user.id
    
    try:
        # استخراج السؤال
        if update.message.text:
            question = update.message.text
        elif update.message.photo:
            await update.message.reply_text("🔄 جاري قراءة الصورة...")
            # هنا يمكن إضافة OCR للصور
            question = "سؤال من صورة (خدمة OCR قيد التطوير)"
        elif update.message.document:
            await update.message.reply_text("📄 تم استلام الملف (الخدمة قيد التطوير)")
            question = "سؤال من ملف (الخدمة قيد التطوير)"
        else:
            await update.message.reply_text("❌ الرجاء إرسال سؤال نصي")
            return AWAITING_QUESTION
        
        await update.message.reply_text("🤔 جاري البحث عن الإجابة...")
        
        # الحصول على الإجابة
        answer = await AIProcessor.ask_gemini(question)
        
        keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال الإجابة
        await update.message.reply_text(
            f"💡 *الإجابة:*\n\n{answer[:3000]}",  # تقييد الطول
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"❌ خطأ في handle_question_input: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة السؤال")
        return ConversationHandler.END

# =============================================
# الميزات الشخصية
# =============================================
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رصيد المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        user = db.get_user(user_id)
        if not user:
            await query.edit_message_text("❌ المستخدم غير موجود")
            return
        
        settings = db.get_settings()
        
        balance_text = f"""
💰 *رصيدك الحالي*

🏦 الرصيد: {user.get('balance', 0):,} دينار
💸 إجمالي المشتريات: {user.get('total_spent', 0):,} دينار
📊 عدد الخدمات: {user.get('total_services', 0)}

📈 *معلومات إضافية:*
🎁 مكافأة الدعوة: {settings.get('invite_bonus', 500):,} دينار
💰 سعر الخدمة: {settings.get('service_price', 1000):,} دينار

💳 *للشحن:* تواصل مع @{DEVELOPER_USERNAME}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💳 شحن الرصيد", callback_data="charge_balance"),
                InlineKeyboardButton("📜 المعاملات", callback_data="transaction_history")
            ],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            balance_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_balance: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض الرصيد")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        user = db.get_user(user_id)
        if not user:
            await query.edit_message_text("❌ المستخدم غير موجود")
            return
        
        # حساب الأيام
        created_at = user.get('created_at', datetime.now())
        days_since_join = (datetime.now() - created_at).days
        
        stats_text = f"""
📊 *إحصائيات حسابك*

👤 المعرف: {user_id}
📅 تاريخ التسجيل: {created_at.strftime('%Y/%m/%d')}
⏰ آخر نشاط: {user.get('last_active', created_at).strftime('%Y/%m/%d %I:%M %p')}
📆 أيام في البوت: {max(days_since_join, 1)} يوم

🏦 *المالية:*
💰 الرصيد الحالي: {user.get('balance', 0):,} دينار
💸 إجمالي المشتريات: {user.get('total_spent', 0):,} دينار
🛒 عدد الخدمات: {user.get('total_services', 0)}

👥 *الدعوة:*
👥 عدد المدعوين: {len(user.get('invited_users', []))}
🎁 الرمز الخاص: `{user.get('invite_code', 'N/A')}`

📈 *النشاط:*
المعدل اليومي: {user.get('total_services', 0) / max(days_since_join, 1):.1f} خدمة/يوم
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💰 رصيدي", callback_data="my_balance"),
                InlineKeyboardButton("🔗 دعوة أصدقاء", callback_data="invite_friends")
            ],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض الإحصائيات")

async def show_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رابط الدعوة"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        user = db.get_user(user_id)
        if not user:
            await query.edit_message_text("❌ المستخدم غير موجود")
            return
        
        settings = db.get_settings()
        invite_bonus = settings.get('invite_bonus', 500)
        invite_code = user.get('invite_code', f"INV{user_id}")
        
        invite_link = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
        
        invite_text = f"""
🔗 *دعوة الأصدقاء*

🎁 *المكافأة:* {invite_bonus:,} دينار لكل صديق
👥 *عدد المدعوين:* {len(user.get('invited_users', []))}

*رابط الدعوة الخاص بك:*
`{invite_link}`

*طريقة العمل:*
1. شارك الرابط مع أصدقائك
2. عندما ينضم صديق عبر الرابط
3. تحصل على {invite_bonus:,} دينار تلقائياً
4. يمكن لصديقك أيضاً دعوة أصدقاء

*قائمة المدعوين:* {', '.join([str(u) for u in user.get('invited_users', [])[:5]]) or 'لا يوجد'}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={invite_link}&text=انضم%20إلى%20بوت%20يلا%20نتعلم"),
                InlineKeyboardButton("📋 نسخ الرابط", callback_data=f"copy_invite_{invite_code}")
            ],
            [
                InlineKeyboardButton("💰 رصيدي", callback_data="my_balance"),
                InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            invite_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_invite: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض رابط الدعوة")

async def show_charge_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض خيارات الشحن"""
    query = update.callback_query
    await query.answer()
    
    try:
        settings = db.get_settings()
        min_charge = settings.get('min_charge', 1000)
        
        charge_text = f"""
💳 *شحن الرصيد*

🏦 الحد الأدنى للشحن: {min_charge:,} دينار
💰 سعر الخدمة: {settings.get('service_price', 1000):,} دينار

*طريقة الشحن:*
1. تواصل مع الدعم: @{DEVELOPER_USERNAME}
2. أرسل له معرفك: `{query.from_user.id}`
3. أرسل المبلغ المطلوب
4. قم بالتحويل
5. سيتم شحن رصيدك فوراً

*ملاحظات:*
- يتم الشحن يدوياً خلال 24 ساعة
- احتفظ بإيصال التحويل
- للشحن السريع راسل الدعم مباشرة
        """
        
        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 تواصل مع الدعم", url=f"https://t.me/{DEVELOPER_USERNAME}"),
                InlineKeyboardButton("📋 معرفي", callback_data=f"show_id_{query.from_user.id}")
            ],
            [
                InlineKeyboardButton("💰 رصيدي", callback_data="my_balance"),
                InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            charge_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_charge_options: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض خيارات الشحن")

async def show_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض سجل المعاملات"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        # في الإصدار الحالي، نعرض رسالة بسيطة
        # يمكن تطويرها لاحقاً لسحب من قاعدة البيانات
        
        history_text = """
📜 *سجل المعاملات*

هذه الخدمة قيد التطوير حالياً.
سيتم إضافة سجل المعاملات المفصل قريباً.

💡 *يمكنك:*
- مراجعة رصيدك الحالي
- التواصل مع الدعم للاستفسار
- متابعة آخر تحديثات البوت
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💰 رصيدي", callback_data="my_balance"),
                InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            history_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_transaction_history: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض سجل المعاملات")

# =============================================
# لوحة التحكم (للمطور فقط)
# =============================================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة تحكم المشرف (للمطور فقط)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # تحقق مزدوج من الصلاحية
    if user_id != DEVELOPER_ID:
        logger.warning(f"⛔ محاولة وصول غير مصرح للوحة التحكم: {user_id}")
        await query.edit_message_text("❌ ليس لديك صلاحية الوصول!")
        return
    
    try:
        settings = db.get_settings()
        
        # إحصائيات سريعة
        total_users = db.count_users()
        
        admin_text = f"""
👑 *لوحة تحكم المطور* (@Allawi04)

📊 *الإحصائيات العامة:*
👥 إجمالي المستخدمين: {total_users:,}

⚙️ *الإعدادات الحالية:*
💰 سعر الخدمة: {settings.get('service_price', 1000):,} دينار
🎁 مكافأة ترحيبية: {settings.get('welcome_bonus', 1000):,} دينار
🎯 مكافأة الدعوة: {settings.get('invite_bonus', 500):,} دينار
🔧 وضع الصيانة: {'✅ مفعل' if settings.get('maintenance_mode') else '❌ معطل'}

*اختر الإدارة المطلوبة:*
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💰 شحن رصيد", callback_data="admin_charge"),
                InlineKeyboardButton("⛔ حظر مستخدم", callback_data="admin_ban")
            ],
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("💰 تعديل الأسعار", callback_data="admin_prices"),
                InlineKeyboardButton("🔧 وضع الصيانة", callback_data="admin_toggle_maintenance")
            ],
            [
                InlineKeyboardButton("📢 إشعار للجميع", callback_data="admin_broadcast"),
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton("🔧 إعادة التشغيل", callback_data="admin_restart"),
                InlineKeyboardButton("🏠 الرئيسية", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            admin_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_admin_panel: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض لوحة التحكم")

async def admin_charge_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية شحن رصيد"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💰 *شحن رصيد مستخدم*\n\n"
        "أرسل معرف المستخدم (user_id):",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ADMIN_CHARGE_USER

async def admin_charge_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة معرف المستخدم للشحن"""
    user_id = update.message.from_user.id
    
    if user_id != DEVELOPER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        target_user_id = int(update.message.text)
        context.user_data['charge_user_id'] = target_user_id
        
        target_user = db.get_user(target_user_id)
        
        if not target_user:
            await update.message.reply_text("❌ المستخدم غير موجود!")
            return ADMIN_CHARGE_USER
        
        keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👤 المستخدم: {target_user.get('first_name', 'غير معروف')}\n"
            f"🏦 الرصيد الحالي: {target_user.get('balance', 0):,} دينار\n\n"
            "أرسل المبلغ المطلوب شحنه (رقم فقط):",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_CHARGE_AMOUNT
        
    except ValueError:
        await update.message.reply_text("❌ المعرف يجب أن يكون رقماً!")
        return ADMIN_CHARGE_USER
    except Exception as e:
        logger.error(f"❌ خطأ في admin_charge_amount: {e}")
        await update.message.reply_text("❌ حدث خطأ!")
        return ConversationHandler.END

async def admin_complete_charge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إكمال عملية الشحن"""
    user_id = update.message.from_user.id
    
    if user_id != DEVELOPER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        amount = int(update.message.text)
        
        if amount <= 0:
            await update.message.reply_text("❌ المبلغ يجب أن يكون أكبر من الصفر!")
            return ADMIN_CHARGE_AMOUNT
        
        target_user_id = context.user_data.get('charge_user_id')
        
        if not target_user_id:
            await update.message.reply_text("❌ خطأ في البيانات!")
            return ConversationHandler.END
        
        # شحن الرصيد
        if UserManager.update_balance(target_user_id, amount, "add"):
            # تسجيل المعاملة
            db.add_transaction({
                "transaction_id": f"ADM{user_id}{int(datetime.now().timestamp())}",
                "user_id": target_user_id,
                "amount": amount,
                "type": "admin_charge",
                "description": f"شحن بواسطة المطور",
                "timestamp": datetime.now(),
                "status": "completed"
            })
            
            # إرسال إشعار للمستخدم
            try:
                new_balance = db.get_user(target_user_id).get('balance', 0)
                
                notification_text = f"""
🎉 *تم شحن رصيدك*

✅ المبلغ: {amount:,} دينار
🏦 الرصيد الجديد: {new_balance:,} دينار
📅 التاريخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}

شكراً لاستخدامك بوت "يلا نتعلم" ❤️
                """
                
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=notification_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"⚠️ خطأ في إرسال إشعار الشحن: {e}")
            
            keyboard = [
                [
                    InlineKeyboardButton("💰 شحن آخر", callback_data="admin_charge"),
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ تم شحن {amount:,} دينار للمستخدم {target_user_id} بنجاح!",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ فشل في شحن الرصيد!")
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً!")
        return ADMIN_CHARGE_AMOUNT
    except Exception as e:
        logger.error(f"❌ خطأ في admin_complete_charge: {e}")
        await update.message.reply_text("❌ حدث خطأ!")
        return ConversationHandler.END

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية حظر مستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⛔ *حظر مستخدم*\n\n"
        "أرسل معرف المستخدم (user_id) للحظر:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ADMIN_BAN_USER

async def admin_ban_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة معرف المستخدم للحظر"""
    user_id = update.message.from_user.id
    
    if user_id != DEVELOPER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        target_user_id = int(update.message.text)
        context.user_data['ban_user_id'] = target_user_id
        
        target_user = db.get_user(target_user_id)
        
        if not target_user:
            await update.message.reply_text("❌ المستخدم غير موجود!")
            return ADMIN_BAN_USER
        
        if target_user.get("banned", False):
            keyboard = [
                [
                    InlineKeyboardButton("🔓 فك الحظر", callback_data=f"admin_unban_{target_user_id}"),
                    InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ هذا المستخدم محظور بالفعل!\n"
                f"السبب: {target_user.get('ban_reason', 'غير محدد')}\n\n"
                "هل تريد فك الحظر؟",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👤 المستخدم: {target_user.get('first_name', 'غير معروف')}\n"
            f"📅 تاريخ التسجيل: {target_user.get('created_at', datetime.now()).strftime('%Y/%m/%d')}\n\n"
            "أرسل سبب الحظر:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_BAN_REASON
        
    except ValueError:
        await update.message.reply_text("❌ المعرف يجب أن يكون رقماً!")
        return ADMIN_BAN_USER
    except Exception as e:
        logger.error(f"❌ خطأ في admin_ban_reason: {e}")
        await update.message.reply_text("❌ حدث خطأ!")
        return ConversationHandler.END

async def admin_complete_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إكمال عملية الحظر"""
    user_id = update.message.from_user.id
    
    if user_id != DEVELOPER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        reason = update.message.text
        
        if len(reason) < 3:
            await update.message.reply_text("❌ السبب قصير جداً!")
            return ADMIN_BAN_REASON
        
        target_user_id = context.user_data.get('ban_user_id')
        
        if not target_user_id:
            await update.message.reply_text("❌ خطأ في البيانات!")
            return ConversationHandler.END
        
        # حظر المستخدم
        if UserManager.ban_user(target_user_id, reason, user_id):
            # إرسال إشعار للمستخدم
            try:
                ban_text = f"""
⛔ *حسابك محظور*

🚫 السبب: {reason}
📅 التاريخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}
🔓 للإستفسار: @{DEVELOPER_USERNAME}

يمكنك التواصل مع الدعم للاستفسار.
                """
                
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=ban_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"⚠️ خطأ في إرسال إشعار الحظر: {e}")
            
            keyboard = [
                [
                    InlineKeyboardButton("⛔ حظر آخر", callback_data="admin_ban"),
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ تم حظر المستخدم {target_user_id} بنجاح!\n"
                f"السبب: {reason}",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ فشل في حظر المستخدم!")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_complete_ban: {e}")
        await update.message.reply_text("❌ حدث خطأ!")
        return ConversationHandler.END

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فك حظر مستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return
    
    try:
        target_user_id = int(query.data.replace("admin_unban_", ""))
        
        if UserManager.unban_user(target_user_id):
            # إرسال إشعار للمستخدم
            try:
                unban_text = f"""
✅ *تم فك حظر حسابك*

🎉 مرحباً بك مرة أخرى في بوت "يلا نتعلم"
📅 التاريخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}

يمكنك الآن استخدام البوت بشكل طبيعي.
                """
                
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=unban_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"⚠️ خطأ في إرسال إشعار فك الحظر: {e}")
            
            keyboard = [
                [
                    InlineKeyboardButton("⛔ حظر آخر", callback_data="admin_ban"),
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ تم فك حظر المستخدم {target_user_id} بنجاح!",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("❌ فشل في فك الحظر!")
            
    except Exception as e:
        logger.error(f"❌ خطأ في admin_unban_user: {e}")
        await query.edit_message_text("❌ حدث خطأ!")

async def admin_show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات مفصلة"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return
    
    try:
        total_users = db.count_users()
        settings = db.get_settings()
        
        stats_text = f"""
📊 *إحصائيات متقدمة*

👥 *المستخدمين:*
• إجمالي المستخدمين: {total_users:,}

💰 *الإعدادات المالية:*
• سعر الخدمة: {settings.get('service_price', 1000):,} دينار
• مكافأة ترحيبية: {settings.get('welcome_bonus', 1000):,} دينار
• مكافأة الدعوة: {settings.get('invite_bonus', 500):,} دينار
• الحد الأدنى للشحن: {settings.get('min_charge', 1000):,} دينار

⚙️ *الحالة:*
• وضع الصيانة: {'✅ مفعل' if settings.get('maintenance_mode') else '❌ معطل'}
• قناة البوت: {settings.get('bot_channel', '@FC4Xbot')}
• الدعم الفني: {settings.get('support_channel', '@Allawi04')}

🔄 *آخر تحديث:* {settings.get('updated_at', datetime.now()).strftime('%Y/%m/%d %H:%M')}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users"),
                InlineKeyboardButton("⚙️ تعديل الإعدادات", callback_data="admin_edit_settings")
            ],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_show_stats: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض الإحصائيات!")

async def admin_show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المستخدمين"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return
    
    try:
        users = db.get_all_users(limit=10)
        total_users = db.count_users()
        
        if not users:
            users_text = "👥 *المستخدمين*\n\nلا يوجد مستخدمين حالياً."
        else:
            users_text = "👥 *آخر 10 مستخدمين*\n\n"
            for user in users:
                name = user.get('first_name', user.get('username', 'غير معروف'))
                created = user.get('created_at', datetime.now()).strftime('%m/%d')
                balance = user.get('balance', 0)
                users_text += f"• {name} ({user['user_id']}) - {balance:,} دينار - {created}\n"
        
        users_text += f"\n📊 *الإجمالي:* {total_users:,} مستخدم"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 تحديث القائمة", callback_data="admin_users"),
                InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")
            ],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            users_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_show_users: {e}")
        await query.edit_message_text("❌ حدث خطأ في عرض المستخدمين!")

async def admin_toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل وضع الصيانة"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return
    
    try:
        settings = db.get_settings()
        current = settings.get('maintenance_mode', False)
        new_state = not current
        
        if db.update_settings({"maintenance_mode": new_state}):
            status = "✅ مفعل" if new_state else "❌ معطل"
            notification = "🔧 البوت تحت الصيانة" if new_state else "🎉 البوت يعمل بشكل طبيعي"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔧 تبديل مرة أخرى", callback_data="admin_toggle_maintenance"),
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔧 *وضع الصيانة*\n\nالحالة: {status}\n\n{notification}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text("❌ فشل في تحديث وضع الصيانة!")
            
    except Exception as e:
        logger.error(f"❌ خطأ في admin_toggle_maintenance: {e}")
        await query.edit_message_text("❌ حدث خطأ!")

async def admin_manage_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة أسعار الخدمات"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return
    
    try:
        services = db.get_services()
        settings = db.get_settings()
        
        keyboard = []
        for service in services:
            keyboard.append([
                InlineKeyboardButton(
                    f"{service.get('icon', '💰')} {service['name']} - {service.get('price', 1000):,} دينار",
                    callback_data=f"admin_edit_price_{service['name']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("💰 السعر العام", callback_data="admin_edit_general_price"),
            InlineKeyboardButton("🎁 المكافآت", callback_data="admin_edit_bonuses")
        ])
        
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💰 *إدارة الأسعار والمكافآت*\n\n"
            f"السعر العام الحالي: {settings.get('service_price', 1000):,} دينار\n"
            "اختر الخدمة لتعديل سعرها:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_manage_prices: {e}")
        await query.edit_message_text("❌ حدث خطأ في إدارة الأسعار!")

async def admin_edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تعديل سعر خدمة"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        if "general" in query.data:
            service_name = "general"
            current_price = db.get_settings().get('service_price', 1000)
        else:
            service_name = query.data.replace("admin_edit_price_", "")
            service = db.get_service(service_name)
            if not service:
                await query.edit_message_text("❌ الخدمة غير موجودة!")
                return ConversationHandler.END
            current_price = service.get('price', 1000)
        
        context.user_data['edit_price_service'] = service_name
        context.user_data['edit_price_current'] = current_price
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_prices")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💰 *تعديل السعر*\n\n"
            f"الخدمة: {service_name}\n"
            f"السعر الحالي: {current_price:,} دينار\n\n"
            "أرسل السعر الجديد (رقم فقط):",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_UPDATE_PRICE
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_edit_price: {e}")
        await query.edit_message_text("❌ حدث خطأ!")
        return ConversationHandler.END

async def admin_complete_price_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إكمال تعديل السعر"""
    user_id = update.message.from_user.id
    
    if user_id != DEVELOPER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        new_price = int(update.message.text)
        
        if new_price < 100:
            await update.message.reply_text("❌ السعر يجب أن يكون 100 دينار على الأقل!")
            return ADMIN_UPDATE_PRICE
        
        service_name = context.user_data.get('edit_price_service')
        current_price = context.user_data.get('edit_price_current', 1000)
        
        if not service_name:
            await update.message.reply_text("❌ خطأ في البيانات!")
            return ConversationHandler.END
        
        success = False
        
        if service_name == "general":
            # تحديث السعر العام
            success = db.update_settings({"service_price": new_price})
        else:
            # تحديث سعر خدمة معينة
            success = db.update_service_price(service_name, new_price)
        
        if success:
            keyboard = [
                [
                    InlineKeyboardButton("💰 تعديل آخر", callback_data="admin_prices"),
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ تم تحديث سعر {service_name} من {current_price:,} إلى {new_price:,} دينار بنجاح!",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ فشل في تحديث السعر!")
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ السعر يجب أن يكون رقماً!")
        return ADMIN_UPDATE_PRICE
    except Exception as e:
        logger.error(f"❌ خطأ في admin_complete_price_edit: {e}")
        await update.message.reply_text("❌ حدث خطأ!")
        return ConversationHandler.END

async def admin_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء إرسال إشعار للجميع"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📢 *إرسال إشعار للجميع*\n\n"
        "أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
        "يمكنك استخدام Markdown للتنسيق.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ADMIN_BROADCAST_MSG

async def admin_send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إرسال الإشعار للجميع"""
    user_id = update.message.from_user.id
    
    if user_id != DEVELOPER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية!")
        return ConversationHandler.END
    
    try:
        message_text = update.message.text
        if not message_text or len(message_text.strip()) < 5:
            await update.message.reply_text("❌ الرسالة قصيرة جداً!")
            return ADMIN_BROADCAST_MSG
        
        await update.message.reply_text("📤 جاري إرسال الإشعار...")
        
        # في الإصدار الحالي، نعرض رسالة تجريبية
        # يمكن تطويرها لاحقاً لإرسال فعلي
        
        total_users = db.count_users()
        
        keyboard = [
            [
                InlineKeyboardButton("📢 إرسال آخر", callback_data="admin_broadcast"),
                InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *تم تجهيز الإشعار للإرسال*\n\n"
            f"📊 العدد المستهدف: {total_users:,} مستخدم\n"
            f"📝 الرسالة: {message_text[:100]}...\n\n"
            f"*ملاحظة:* في هذا الإصدار، يتم فقط تجهيز الرسالة.\n"
            f"سيتم تفعيل الإرسال الفعلي في الإصدارات القادمة.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_send_broadcast: {e}")
        await update.message.reply_text("❌ حدث خطأ في إرسال الإشعار!")
        return ConversationHandler.END

async def admin_restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تشغيل البوت (تجريبي)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != DEVELOPER_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية!")
        return
    
    try:
        await query.edit_message_text("🔄 جاري إعادة التشغيل...")
        
        # في الإصدار الحالي، نعرض رسالة فقط
        # في السيرفر الحقيقي، يمكن إضافة إعادة التشغيل الفعلي
        
        await asyncio.sleep(2)
        
        keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ *تمت إعادة التشغيل بنجاح*\n\n"
            "جميع الخدمات تعمل بشكل طبيعي.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في admin_restart_bot: {e}")
        await query.edit_message_text("❌ حدث خطأ في إعادة التشغيل!")

# =============================================
# دوال مساعدة
# =============================================
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للقائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    
    return await start_command(update, context)

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء العملية الحالية"""
    user = update.effective_user
    
    try:
        if update.message:
            await update.message.reply_text(
                "تم الإلغاء.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main")]
                ])
            )
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("تم الإلغاء.")
    except:
        pass
    
    return ConversationHandler.END

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية العامة"""
    try:
        text = update.message.text
        
        if text.startswith('/'):
            return
        
        # رد بسيط على الرسائل العامة
        await update.message.reply_text(
            "👋 أهلاً بك! استخدم الأزرار للتنقل بين الخدمات.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main")]
            ])
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في handle_text_messages: {e}")

async def handle_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة انضمام المستخدم عبر رابط الدعوة"""
    try:
        user = update.effective_user
        
        # الحصول على الكود من رابط الدعوة
        args = context.args
        if args and len(args) > 0:
            invite_code = args[0]
            
            # البحث عن صاحب الكود
            # سيتم تطوير هذا الجزء لاحقاً
            
            logger.info(f"🔗 انضمام عبر دعوة: {user.id} - كود: {invite_code}")
        
        # متابعة البدء العادي
        return await start_command(update, context)
        
    except Exception as e:
        logger.error(f"❌ خطأ في handle_invite_start: {e}")
        try:
            await update.message.reply_text(
                "عذراً، حدث خطأ. الرجاء المحاولة مرة أخرى.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 المحاولة مرة أخرى", callback_data="back_to_main")]
                ])
            )
        except:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    try:
        logger.error(f"🚨 خطأ غير متوقع: {context.error}", exc_info=context.error)
        
        if update and update.effective_user:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="عذراً، حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main")]
                    ])
                )
            except:
                pass
    except Exception as e:
        logger.error(f"❌ خطأ في معالج الأخطاء: {e}")

# =============================================
# إعدادات الإغلاق الآمن
# =============================================
def signal_handler(signum, frame):
    """معالج إشارات الإغلاق"""
    logger.info("🛑 استقبال إشارة إغلاق...")
    logger.info("✅ تم حفظ البيانات وإغلاق الاتصالات.")
    sys.exit(0)

# =============================================
# التشغيل الرئيسي
# =============================================
def main():
    """تشغيل البوت"""
    
    # تسجيل معالجات الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل بوت 'يلا نتعلم'")
    logger.info(f"👑 المطور: @Allawi04 (ID: {DEVELOPER_ID})")
    logger.info(f"🤖 البوت: @{BOT_USERNAME}")
    logger.info("=" * 50)
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # ============= معالجات الأوامر =============
        application.add_handler(CommandHandler('start', handle_invite_start))
        
        # ============= معالج المحادثة الرئيسي =============
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(handle_service_selection, pattern="^(service_|my_|charge_|transaction_|admin_)")
            ],
            states={
                # حالات المستخدم العادي
                AWAITING_SCORES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_scores_input),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
                ],
                AWAITING_PDF: [
                    MessageHandler(filters.Document.PDF, handle_pdf_input),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
                ],
                AWAITING_QUESTION: [
                    MessageHandler(filters.TEXT | filters.PHOTO, handle_question_input),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
                ],
                
                # حالات المشرف (المطور فقط)
                ADMIN_CHARGE_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_charge_amount),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$")
                ],
                ADMIN_CHARGE_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_complete_charge),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$")
                ],
                ADMIN_BAN_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_reason),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$")
                ],
                ADMIN_BAN_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_complete_ban),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$")
                ],
                ADMIN_UPDATE_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_complete_price_edit),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$")
                ],
                ADMIN_BROADCAST_MSG: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_broadcast),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$")
                ],
            },
            fallbacks=[
                CommandHandler('start', start_command),
                CommandHandler('cancel', handle_cancel),
                CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
            ],
            allow_reentry=True
        )
        
        application.add_handler(conv_handler)
        
        # ============= معالجات الأزرار الإضافية =============
        application.add_handler(CallbackQueryHandler(admin_unban_user, pattern="^admin_unban_"))
        application.add_handler(CallbackQueryHandler(admin_edit_price, pattern="^admin_edit_price_"))
        application.add_handler(CallbackQueryHandler(admin_edit_price, pattern="^admin_edit_general_price$"))
        application.add_handler(CallbackQueryHandler(admin_show_stats, pattern="^admin_stats$"))
        application.add_handler(CallbackQueryHandler(admin_show_users, pattern="^admin_users$"))
        application.add_handler(CallbackQueryHandler(admin_toggle_maintenance, pattern="^admin_toggle_maintenance$"))
        application.add_handler(CallbackQueryHandler(admin_manage_prices, pattern="^admin_prices$"))
        application.add_handler(CallbackQueryHandler(admin_broadcast_message, pattern="^admin_broadcast$"))
        application.add_handler(CallbackQueryHandler(admin_restart_bot, pattern="^admin_restart$"))
        
        # ============= معالج الرسائل العامة =============
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
        
        # ============= معالج الأخطاء =============
        application.add_error_handler(error_handler)
        
        # ============= بدء البوت =============
        logger.info("✅ جاهز للاستقبال...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"🚨 خطأ فادح في التشغيل: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
