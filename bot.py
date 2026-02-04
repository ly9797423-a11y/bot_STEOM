#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت "يلا نتعلم" - البوت التعليمي للطلاب العراقيين
الإصدار الكامل مع نظام VIP المتكامل
المطور: Allawi04@
"""

import logging
import json
import os
import re
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import PyPDF2
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
from telegram.constants import ParseMode
import google.generativeai as genai
import requests
import aiofiles
import httpx

# ============= إعدادات البوت =============
TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
SUPPORT_USERNAME = "Allawi04"
GEMINI_API_KEY = "AIzaSyARsl_YMXA74bPQpJduu0jJVuaku7MaHuY"

# ============= حالات المحادثة =============
(
    ADMIN_MENU, CHARGE_USER, CHARGE_AMOUNT, PRICE_CHANGE, CHANGE_PRICE_SERVICE,
    MATERIAL_FILE, MATERIAL_DESC, MATERIAL_STAGE, QUESTION_DETAILS, 
    QUESTION_ANSWER, BAN_USER, CHANGE_CHANNEL, DELETE_MATERIAL, 
    ADD_MATERIAL, VIEW_USER, TOGGLE_SERVICE, EXEMPTION_COURSE1,
    EXEMPTION_COURSE2, EXEMPTION_COURSE3, VIP_MANAGEMENT,
    VIP_ADD_LECTURE, VIP_LECTURE_TITLE, VIP_LECTURE_DESC,
    VIP_LECTURE_FILE, VIP_LECTURE_PRICE, VIP_SUBSCRIPTION_MANAGE,
    VIP_CHANGE_SUBSCRIPTION_PRICE, VIP_APPROVE_LECTURE, 
    VIP_BAN_TEACHER, VIP_VIEW_LECTURES, VIP_BUY_LECTURE,
    VIP_VIEW_LECTURE_DETAIL, SUMMARIZE_PDF, QA_QUESTION,
    HELP_STUDENT_QUESTION, HELP_STUDENT_ANSWER,
    MATERIALS_SELECT_STAGE, MATERIALS_VIEW
) = range(36)

# ============= إعداد التسعير =============
SERVICE_PRICES = {
    "exemption": 1000,
    "summarize": 1000,
    "qa": 1000,
    "materials": 1000,
    "help_student": 250,
    "vip_subscription": 5000
}

# ============= إعداد الخدمات النشطة =============
ACTIVE_SERVICES = {
    "exemption": True,
    "summarize": True,
    "qa": True,
    "materials": True,
    "help_student": True,
    "vip_lectures": True
}

WELCOME_BONUS = 1000
REFERRAL_BONUS = 500
ANSWER_REWARD = 100

# ============= إعداد الملفات =============
DATA_FILE = "users_data.json"
MATERIALS_FILE = "materials_data.json"
ADMIN_FILE = "admin_settings.json"
QUESTIONS_FILE = "questions_data.json"
BANNED_FILE = "banned_users.json"
CHANNEL_FILE = "channel_info.json"
SERVICES_FILE = "services_status.json"
VIP_FILE = "vip_data.json"
VIP_LECTURES_FILE = "vip_lectures.json"
VIP_PURCHASES_FILE = "vip_purchases.json"

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
        user_id_str = str(user_id)
        
        if user_id_str in self.banned_users:
            return self.banned_users[user_id_str]
        
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                "balance": WELCOME_BONUS,
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "first_name": "",
                "username": "",
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
                "pending_purchase": None,
                "total_spent": 0,
                "vip_subscription": None,
                "vip_expiry": None,
                "is_teacher": False,
                "vip_lectures": [],
                "teacher_status": "pending",
                "vip_purchases": [],
                "vip_earnings": 0,
                "vip_sales": 0
            }
            self.save_users()
            logger.info(f"New user created: {user_id}")
        return self.users[user_id_str]
    
    def is_vip(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user.get("vip_expiry"):
            return False
        
        try:
            expiry_date = datetime.strptime(user["vip_expiry"], "%Y-%m-%d %H:%M:%S")
            return datetime.now() < expiry_date
        except:
            return False
    
    def add_vip_subscription(self, user_id: int, months: int = 1):
        user = self.get_user(user_id)
        
        now = datetime.now()
        if user.get("vip_expiry"):
            try:
                current_expiry = datetime.strptime(user["vip_expiry"], "%Y-%m-%d %H:%M:%S")
                if current_expiry > now:
                    new_expiry = current_expiry + timedelta(days=30 * months)
                else:
                    new_expiry = now + timedelta(days=30 * months)
            except:
                new_expiry = now + timedelta(days=30 * months)
        else:
            new_expiry = now + timedelta(days=30 * months)
        
        user["vip_subscription"] = True
        user["vip_expiry"] = new_expiry.strftime("%Y-%m-%d %H:%M:%S")
        user["is_teacher"] = True
        user["teacher_status"] = "approved"
        
        transaction = {
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "vip_subscription",
            "months": months,
            "expiry_date": user["vip_expiry"]
        }
        user.setdefault("vip_transactions", []).append(transaction)
        
        self.save_users()
        logger.info(f"VIP subscription added for user {user_id} until {user['vip_expiry']}")
        return True
    
    def remove_vip_subscription(self, user_id: int):
        user = self.get_user(user_id)
        user["vip_subscription"] = False
        user["vip_expiry"] = None
        user["teacher_status"] = "pending"
        self.save_users()
        logger.info(f"VIP subscription removed for user {user_id}")
        return True
    
    def update_user_info(self, user_id: int, first_name: str, username: str = ""):
        user = self.get_user(user_id)
        user["first_name"] = first_name
        if username:
            user["username"] = username
        self.save_users()
    
    def can_ask_question(self, user_id: int) -> Tuple[bool, str]:
        user = self.get_user(user_id)
        last_question = user.get("last_question_time")
        
        if not last_question:
            return True, ""
        
        try:
            last_time = datetime.strptime(last_question, "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_time
            
            if time_diff.total_seconds() < 86400:
                remaining = 86400 - time_diff.total_seconds()
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return False, f"⏳ يمكنك طرح سؤال جديد بعد {hours} ساعة و{minutes} دقيقة"
            return True, ""
        except:
            return True, ""
    
    def update_question_time(self, user_id: int):
        user = self.get_user(user_id)
        user["last_question_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user["questions_asked"] = user.get("questions_asked", 0) + 1
        self.save_users()
    
    def update_balance(self, user_id: int, amount: int, description: str = "") -> Tuple[int, bool]:
        user = self.get_user(user_id)
        old_balance = user.get("balance", 0)
        user["balance"] = old_balance + amount
        
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "description": description,
            "balance_before": old_balance,
            "balance_after": user["balance"]
        }
        user.setdefault("transactions", []).append(transaction)
        
        if amount > 0:
            user["total_earned"] = user.get("total_earned", 0) + amount
        else:
            user["total_spent"] = user.get("total_spent", 0) + abs(amount)
        
        self.save_users()
        logger.info(f"Updated balance for user {user_id}: {old_balance} -> {user['balance']} ({amount})")
        
        notify_user = amount > 0
        return user["balance"], notify_user
    
    def set_pending_purchase(self, user_id: int, service: str, price: int):
        user = self.get_user(user_id)
        user["pending_purchase"] = {
            "service": service,
            "price": price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_users()
    
    def complete_purchase(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if user.get("pending_purchase"):
            purchase = user["pending_purchase"]
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
        user = self.get_user(user_id)
        if user.get("pending_purchase"):
            purchase = user["pending_purchase"]
            self.update_balance(user_id, purchase["price"], f"استرجاع رصيد لخدمة: {purchase['service']}")
            user["pending_purchase"] = None
            self.save_users()
            return True
        return False
    
    def get_all_users(self) -> List[Tuple[str, Dict]]:
        return list(self.users.items())
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        return self.users.get(str(user_id))
    
    def get_top_users(self, limit: int = 10) -> List[Tuple[str, Dict]]:
        users_list = list(self.users.items())
        users_list.sort(key=lambda x: x[1].get("balance", 0), reverse=True)
        return users_list[:limit]
    
    def save_users(self):
        DataManager.save_data(DATA_FILE, self.users)
    
    def save_banned(self):
        DataManager.save_data(BANNED_FILE, self.banned_users)

# ============= إدارة المواد التعليمية =============
class MaterialsManager:
    def __init__(self):
        self.materials = DataManager.load_data(MATERIALS_FILE, [])
    
    def get_materials_by_stage(self, stage: str) -> List[Dict]:
        return [m for m in self.materials if m.get("stage") == stage]
    
    def get_all_stages(self) -> List[str]:
        stages = set(m.get("stage", "") for m in self.materials)
        return [s for s in stages if s]
    
    def add_material(self, material_data: Dict):
        material_data["id"] = len(self.materials) + 1
        material_data["added_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.materials.append(material_data)
        self.save_materials()
        logger.info(f"Added material: {material_data.get('name', 'Unknown')}")
    
    def delete_material(self, material_id: int) -> bool:
        original_count = len(self.materials)
        self.materials = [m for m in self.materials if m.get("id") != material_id]
        
        if len(self.materials) < original_count:
            self.save_materials()
            logger.info(f"Deleted material ID: {material_id}")
            return True
        return False
    
    def get_material(self, material_id: int) -> Optional[Dict]:
        for material in self.materials:
            if material.get("id") == material_id:
                return material
        return None
    
    def save_materials(self):
        DataManager.save_data(MATERIALS_FILE, self.materials)

# ============= إدارة الأسئلة =============
class QuestionsManager:
    def __init__(self):
        self.questions = DataManager.load_data(QUESTIONS_FILE, [])
    
    def add_question(self, user_id: int, question_text: str) -> str:
        question_id = str(uuid.uuid4())[:8].upper()
        question_data = {
            "id": question_id,
            "user_id": user_id,
            "question": question_text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "answers": [],
            "answered": False,
            "views": 0
        }
        self.questions.append(question_data)
        self.save_questions()
        logger.info(f"Added question {question_id} by user {user_id}")
        return question_id
    
    def add_answer(self, question_id: str, answerer_id: int, answer_text: str) -> Tuple[bool, Optional[int]]:
        for question in self.questions:
            if question["id"] == question_id and not question["answered"]:
                answer_data = {
                    "answerer_id": answerer_id,
                    "answer": answer_text,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                question["answers"].append(answer_data)
                question["answered"] = True
                self.save_questions()
                logger.info(f"Added answer to question {question_id} by user {answerer_id}")
                return True, question["user_id"]
        return False, None
    
    def get_active_questions(self, exclude_user_id: int = None) -> List[Dict]:
        active_questions = [q for q in self.questions if not q["answered"]]
        
        if exclude_user_id:
            active_questions = [q for q in active_questions if q["user_id"] != exclude_user_id]
        
        for question in active_questions[:10]:
            question["views"] = question.get("views", 0) + 1
        
        return active_questions[:10]
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        for question in self.questions:
            if question["id"] == question_id:
                return question
        return None
    
    def remove_old_questions(self, days: int = 7):
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(self.questions)
        
        self.questions = [
            q for q in self.questions 
            if datetime.strptime(q["date"], "%Y-%m-%d %H:%M:%S") > cutoff_date
        ]
        
        if len(self.questions) < original_count:
            self.save_questions()
            logger.info(f"Removed {original_count - len(self.questions)} old questions")
    
    def save_questions(self):
        DataManager.save_data(QUESTIONS_FILE, self.questions)

# ============= إدارة نظام VIP =============
class VIPManager:
    def __init__(self):
        self.vip_data = DataManager.load_data(VIP_FILE, {
            "subscription_price": 5000,
            "teachers": [],
            "pending_lectures": [],
            "approved_lectures": [],
            "banned_teachers": []
        })
        
        self.lectures = DataManager.load_data(VIP_LECTURES_FILE, [])
        self.purchases = DataManager.load_data(VIP_PURCHASES_FILE, [])
    
    def add_lecture(self, teacher_id: int, title: str, description: str, file_info: Dict, price: int = 0) -> str:
        lecture_id = str(uuid.uuid4())[:8].upper()
        lecture_data = {
            "id": lecture_id,
            "teacher_id": teacher_id,
            "title": title,
            "description": description,
            "file_info": file_info,
            "price": price,
            "status": "pending",
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "approved_date": None,
            "views": 0,
            "downloads": 0,
            "sales": 0,
            "earnings": 0
        }
        
        self.lectures.append(lecture_data)
        self.vip_data["pending_lectures"].append(lecture_id)
        self.save_all_data()
        
        logger.info(f"Added lecture {lecture_id} by teacher {teacher_id}")
        return lecture_id
    
    def approve_lecture(self, lecture_id: str) -> bool:
        for lecture in self.lectures:
            if lecture["id"] == lecture_id and lecture["status"] == "pending":
                lecture["status"] = "approved"
                lecture["approved_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if lecture_id in self.vip_data["pending_lectures"]:
                    self.vip_data["pending_lectures"].remove(lecture_id)
                self.vip_data["approved_lectures"].append(lecture_id)
                
                self.save_all_data()
                logger.info(f"Approved lecture {lecture_id}")
                return True
        return False
    
    def reject_lecture(self, lecture_id: str) -> bool:
        for lecture in self.lectures:
            if lecture["id"] == lecture_id and lecture["status"] == "pending":
                lecture["status"] = "rejected"
                
                if lecture_id in self.vip_data["pending_lectures"]:
                    self.vip_data["pending_lectures"].remove(lecture_id)
                
                self.save_all_data()
                logger.info(f"Rejected lecture {lecture_id}")
                return True
        return False
    
    def get_pending_lectures(self) -> List[Dict]:
        return [lecture for lecture in self.lectures if lecture["status"] == "pending"]
    
    def get_approved_lectures(self) -> List[Dict]:
        return [lecture for lecture in self.lectures if lecture["status"] == "approved"]
    
    def get_teacher_lectures(self, teacher_id: int) -> List[Dict]:
        return [lecture for lecture in self.lectures 
                if lecture["teacher_id"] == teacher_id and lecture["status"] == "approved"]
    
    def get_lecture_by_id(self, lecture_id: str) -> Optional[Dict]:
        for lecture in self.lectures:
            if lecture["id"] == lecture_id:
                return lecture
        return None
    
    def delete_lecture(self, lecture_id: str) -> bool:
        original_count = len(self.lectures)
        self.lectures = [lecture for lecture in self.lectures if lecture["id"] != lecture_id]
        
        for key in ["pending_lectures", "approved_lectures"]:
            if lecture_id in self.vip_data[key]:
                self.vip_data[key].remove(lecture_id)
        
        if len(self.lectures) < original_count:
            self.save_all_data()
            logger.info(f"Deleted lecture {lecture_id}")
            return True
        return False
    
    def ban_teacher(self, teacher_id: int) -> bool:
        if teacher_id not in self.vip_data["banned_teachers"]:
            self.vip_data["banned_teachers"].append(teacher_id)
            self.save_all_data()
            logger.info(f"Banned teacher {teacher_id}")
            return True
        return False
    
    def unban_teacher(self, teacher_id: int) -> bool:
        if teacher_id in self.vip_data["banned_teachers"]:
            self.vip_data["banned_teachers"].remove(teacher_id)
            self.save_all_data()
            logger.info(f"Unbanned teacher {teacher_id}")
            return True
        return False
    
    def purchase_lecture(self, student_id: int, lecture_id: str, price: int) -> Tuple[bool, Optional[int]]:
        """شراء محاضرة من قبل طالب"""
        lecture = self.get_lecture_by_id(lecture_id)
        if not lecture or lecture["status"] != "approved":
            return False, None
        
        teacher_id = lecture["teacher_id"]
        
        # تسجيل عملية الشراء
        purchase_id = str(uuid.uuid4())[:8].upper()
        purchase_data = {
            "id": purchase_id,
            "lecture_id": lecture_id,
            "student_id": student_id,
            "teacher_id": teacher_id,
            "price": price,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "teacher_share": price * 0.5,  # 50% للمعلم
            "admin_share": price * 0.5     # 50% للإدارة
        }
        
        self.purchases.append(purchase_data)
        
        # تحديث إحصائيات المحاضرة
        lecture["sales"] = lecture.get("sales", 0) + 1
        lecture["earnings"] = lecture.get("earnings", 0) + price
        lecture["downloads"] = lecture.get("downloads", 0) + 1
        
        self.save_all_data()
        logger.info(f"Purchase {purchase_id}: Student {student_id} bought lecture {lecture_id} for {price}")
        
        return True, teacher_id
    
    def get_student_purchases(self, student_id: int) -> List[Dict]:
        """الحصول على مشتريات طالب"""
        return [purchase for purchase in self.purchases if purchase["student_id"] == student_id]
    
    def update_subscription_price(self, price: int):
        self.vip_data["subscription_price"] = price
        self.save_all_data()
    
    def get_subscription_price(self) -> int:
        return self.vip_data.get("subscription_price", 5000)
    
    def save_all_data(self):
        DataManager.save_data(VIP_FILE, self.vip_data)
        DataManager.save_data(VIP_LECTURES_FILE, self.lectures)
        DataManager.save_data(VIP_PURCHASES_FILE, self.purchases)

# ============= إدارة القناة والخدمات =============
class SettingsManager:
    def __init__(self):
        self.channel_info = DataManager.load_data(CHANNEL_FILE, {
            "channel_link": "https://t.me/FCJCV",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        self.services_status = DataManager.load_data(SERVICES_FILE, ACTIVE_SERVICES.copy())
        
        self.admin_settings = DataManager.load_data(ADMIN_FILE, {
            "maintenance": False,
            "prices": SERVICE_PRICES.copy(),
            "welcome_bonus": WELCOME_BONUS,
            "referral_bonus": REFERRAL_BONUS,
            "answer_reward": ANSWER_REWARD,
            "notify_new_users": True,
            "last_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def get_channel_link(self) -> str:
        return self.channel_info.get("channel_link", "https://t.me/FCJCV")
    
    def update_channel_link(self, new_link: str):
        self.channel_info["channel_link"] = new_link
        self.channel_info["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_channel_info()
    
    def is_service_active(self, service: str) -> bool:
        return self.services_status.get(service, True)
    
    def toggle_service(self, service: str) -> bool:
        if service in self.services_status:
            self.services_status[service] = not self.services_status[service]
            self.save_services_status()
            return self.services_status[service]
        return False
    
    def get_active_services(self) -> List[str]:
        return [service for service, active in self.services_status.items() if active]
    
    def get_all_services(self) -> Dict[str, bool]:
        return self.services_status.copy()
    
    def get_price(self, service: str) -> int:
        return self.admin_settings.get("prices", {}).get(service, 1000)
    
    def update_price(self, service: str, price: int):
        if "prices" not in self.admin_settings:
            self.admin_settings["prices"] = {}
        self.admin_settings["prices"][service] = price
        self.save_admin_settings()
    
    def get_welcome_bonus(self) -> int:
        return self.admin_settings.get("welcome_bonus", WELCOME_BONUS)
    
    def update_welcome_bonus(self, amount: int):
        self.admin_settings["welcome_bonus"] = amount
        self.save_admin_settings()
    
    def save_channel_info(self):
        DataManager.save_data(CHANNEL_FILE, self.channel_info)
    
    def save_services_status(self):
        DataManager.save_data(SERVICES_FILE, self.services_status)
    
    def save_admin_settings(self):
        DataManager.save_data(ADMIN_FILE, self.admin_settings)

# ============= الذكاء الاصطناعي =============
class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': api_key
        }
        
    def call_gemini_api(self, prompt: str) -> str:
        try:
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '❌ لم أتمكن من إجابة على سؤالك')
            else:
                logger.error(f"Gemini API Error: {response.status_code} - {response.text}")
                return f"❌ خطأ في خدمة الذكاء الاصطناعي (رمز الخطأ: {response.status_code})"
                
        except requests.exceptions.Timeout:
            return "❌ تجاوز المهلة، يرجى المحاولة مرة أخرى"
        except Exception as e:
            logger.error(f"Gemini API Exception: {e}")
            return f"❌ حدث خطأ في الخدمة: {str(e)[:100]}"
    
    def summarize_pdf(self, pdf_path: str) -> str:
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if len(text) < 100:
                return "❌ النص قصير جداً للتلخيص"
            
            prompt = f"""
            أنت مساعد تعليمي للطلاب العراقيين. قم بتلخيص النص التعليمي التالي:
            
            {text[:3000]}
            
            المتطلبات:
            1. استخدم اللغة العربية الفصحى
            2. ركز على النقاط الرئيسية
            3. حذف المعلومات غير الأساسية
            4. نظم النقاط بشكل منطقي
            5. اجعل التلخيص مفيداً للدراسة
            
            قدم التلخيص في فقرات واضحة.
            """
            
            return self.call_gemini_api(prompt)
            
        except Exception as e:
            logger.error(f"❌ خطأ في تلخيص PDF: {e}")
            return f"❌ حدث خطأ في التلخيص: {str(e)[:100]}"
    
    def answer_question(self, question: str) -> str:
        try:
            prompt = f"""
            أنت مساعد تعليمي متخصص للمناهج العراقية.
            أجب على السؤال التالي بدقة ووضوح:
            
            السؤال: {question}
            
            المتطلبات:
            1. قدم إجابة شاملة ودقيقة
            2. استخدم أمثلة توضيحية إذا لزم الأمر
            3. كن واضحاً ومنظماً
            4. استخدم اللغة العربية الفصحى
            5. ركز على المعلومات المهمة للدراسة
            
            إذا كان السؤال غير واضح، اطلب توضيحاً.
            """
            
            return self.call_gemini_api(prompt)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الإجابة على السؤال: {e}")
            return f"❌ حدث خطأ في الإجابة: {str(e)[:100]}"
    
    def create_summary_pdf(self, original_text: str, summary: str, output_path: str) -> bool:
        try:
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, height - 50, "تلخيص الملزمة التعليمية")
            c.line(50, height - 65, width - 50, height - 65)
            
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 90, f"تاريخ التلخيص: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 120, "التلخيص:")
            c.setFont("Helvetica", 12)
            
            y_position = height - 150
            lines = summary.split('\n')
            
            for line in lines:
                if y_position < 100:
                    c.showPage()
                    y_position = height - 50
                    c.setFont("Helvetica", 12)
                
                try:
                    reshaped_text = arabic_reshaper.reshape(line)
                    bidi_text = get_display(reshaped_text)
                    display_text = bidi_text[:80]
                except:
                    display_text = line[:80]
                
                c.drawString(50, y_position, display_text)
                y_position -= 20
            
            c.save()
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء PDF: {e}")
            return False

# ============= الفئة الرئيسية للبوت =============
class YallaNataalamBot:
    def __init__(self):
        self.user_manager = UserManager()
        self.materials_manager = MaterialsManager()
        self.questions_manager = QuestionsManager()
        self.settings_manager = SettingsManager()
        self.vip_manager = VIPManager()
        self.ai_service = AIService(GEMINI_API_KEY)
        
        logger.info("✅ تم تهيئة البوت بنجاح")
        logger.info(f"📢 القناة: {self.settings_manager.get_channel_link()}")
        logger.info(f"💎 الهدية: {self.settings_manager.get_welcome_bonus()} دينار")
        logger.info(f"👑 VIP الاشتراك: {self.vip_manager.get_subscription_price()} دينار شهرياً")
    
    async def send_notification(self, user_id: int, message: str, context: ContextTypes.DEFAULT_TYPE):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الإشعار لـ {user_id}: {e}")
            return False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.user_manager.update_user_info(user.id, user.first_name, user.username)
        user_data = self.user_manager.get_user(user.id)
        
        welcome_message = f"""
🎓 <b>مرحباً {user.first_name}!</b>

أهلاً بك في بوت "يلا نتعلم" التعليمي 📚

🆔 <b>رقم حسابك:</b> <code>{user.id}</code>
💰 <b>رصيدك الحالي:</b> {user_data['balance']:,} دينار

🎁 <b>هدية ترحيبية:</b> {self.settings_manager.get_welcome_bonus():,} دينار

📝 <b>لشحن الرصيد:</b>
1. انسخ رقم حسابك أعلاه 👆
2. راسل الدعم الفني: @{SUPPORT_USERNAME}
3. أرسل رقم حسابك والمبلغ المطلوب

اختر الخدمة التي تريدها:
"""
        
        keyboard = []
        active_services = self.settings_manager.get_active_services()
        
        service_buttons = {
            "exemption": ("🧮 حساب درجة الإعفاء", "service_exemption"),
            "summarize": ("📚 تلخيص الملازم", "service_summarize"),
            "qa": ("❓ سؤال وجواب بالذكاء", "service_qa"),
            "materials": ("📖 ملازمي ومرشحاتي", "service_materials"),
            "help_student": ("🤝 ساعدوني طلاب", "service_help_student")
        }
        
        row = []
        for service, (text, callback) in service_buttons.items():
            if service in active_services:
                price = self.settings_manager.get_price(service)
                button_text = f"{text} ({price:,} د)"
                row.append(InlineKeyboardButton(button_text, callback_data=callback))
                
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("👑 محاضرات VIP", callback_data="vip_lectures_store")])
        
        keyboard.append([
            InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
            InlineKeyboardButton("📊 إحصائياتي", callback_data="stats"),
            InlineKeyboardButton("❓ أسئلة الطلاب", callback_data="student_questions")
        ])
        
        keyboard.append([
            InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite"),
            InlineKeyboardButton("📢 قناة البوت", url=self.settings_manager.get_channel_link())
        ])
        
        keyboard.append([
            InlineKeyboardButton("👑 اشتراك VIP", callback_data="vip_subscription_info"),
            InlineKeyboardButton("🆘 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME}")
        ])
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    # ============= قسم تلخيص الملازم =============
    async def handle_service_summarize(self, query, context: ContextTypes.DEFAULT_TYPE):
        user_id = query.from_user.id
        
        if not self.settings_manager.is_service_active("summarize"):
            await query.edit_message_text(
                "⏸️ <b>هذه الخدمة غير متاحة حالياً</b>\n\n"
                "تم تعطيل هذه الخدمة مؤقتاً.\n"
                f"📞 للاستفسار: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        user_data = self.user_manager.get_user(user_id)
        price = self.settings_manager.get_price("summarize")
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي!</b>\n\n"
                f"💰 سعر الخدمة: {price:,} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>\n\n"
                f"📞 تواصل مع الدعم الفني: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        self.user_manager.set_pending_purchase(user_id, "summarize", price)
        
        await query.edit_message_text(
            "📤 <b>أرسل ملف PDF المراد تلخيصه</b>\n\n"
            f"💰 سعر الخدمة: {price:,} دينار\n"
            f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
            "⏳ قد تستغرق العملية بضع دقائق\n"
            "⚠️ <b>سيتم خصم المبلغ بعد إتمام الخدمة</b>",
            parse_mode=ParseMode.HTML
        )
        
        return SUMMARIZE_PDF
    
    async def handle_summarize_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not update.message.document:
            await update.message.reply_text("❌ <b>يرجى إرسال ملف PDF فقط</b>", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
            return SUMMARIZE_PDF
        
        document = update.message.document
        
        if not document.mime_type == 'application/pdf':
            await update.message.reply_text("❌ <b>يرجى إرسال ملف PDF فقط</b>", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
            return SUMMARIZE_PDF
        
        processing_msg = await update.message.reply_text("⏳ <b>جاري معالجة الملف...</b>", parse_mode=ParseMode.HTML)
        
        try:
            file = await document.get_file()
            pdf_path = f"temp_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            await file.download_to_drive(pdf_path)
            
            await processing_msg.edit_text("📖 <b>جاري قراءة الملف...</b>", parse_mode=ParseMode.HTML)
            
            text = ""
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                await processing_msg.edit_text(f"❌ <b>خطأ في قراءة الملف:</b> {str(e)[:100]}", parse_mode=ParseMode.HTML)
                os.remove(pdf_path)
                self.user_manager.cancel_purchase(user_id)
                return ConversationHandler.END
            
            if len(text) < 100:
                await processing_msg.edit_text("❌ <b>الملف فارغ أو لا يحتوي على نص كافٍ</b>", parse_mode=ParseMode.HTML)
                os.remove(pdf_path)
                self.user_manager.cancel_purchase(user_id)
                return ConversationHandler.END
            
            await processing_msg.edit_text("🤖 <b>جاري التلخيص بالذكاء الاصطناعي...</b>", parse_mode=ParseMode.HTML)
            
            summary = self.ai_service.summarize_pdf(pdf_path)
            
            if summary.startswith("❌"):
                await processing_msg.edit_text(f"{summary}\n\n⚠️ <b>تم استرجاع المبلغ</b>", parse_mode=ParseMode.HTML)
                os.remove(pdf_path)
                self.user_manager.cancel_purchase(user_id)
                return ConversationHandler.END
            
            await processing_msg.edit_text("📄 <b>جاري إنشاء ملف PDF جديد...</b>", parse_mode=ParseMode.HTML)
            
            output_path = f"summary_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            success = self.ai_service.create_summary_pdf(text[:1000], summary, output_path)
            
            if success:
                if self.user_manager.complete_purchase(user_id):
                    price = self.settings_manager.get_price("summarize")
                    new_balance = self.user_manager.update_balance(user_id, -price, f"تلخيص ملف PDF")
                    
                    await update.message.reply_document(
                        document=open(output_path, 'rb'),
                        filename=f"تلخيص_{document.file_name or 'ملف.pdf'}",
                        caption=f"✅ <b>تم تلخيص الملزمة بنجاح</b>\n\n"
                               f"📊 <b>ملخص التلخيص:</b>\n{summary[:300]}...\n\n"
                               f"💰 تم خصم: {price:,} دينار\n"
                               f"💳 رصيدك المتبقي: {new_balance:,} دينار",
                        parse_mode=ParseMode.HTML
                    )
                    
                    os.remove(pdf_path)
                    os.remove(output_path)
                    
                    keyboard = [[InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="back_home")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("🔙", reply_markup=reply_markup)
                else:
                    await processing_msg.edit_text("❌ <b>حدث خطأ في المعاملة</b>", parse_mode=ParseMode.HTML)
                    os.remove(pdf_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
            else:
                await processing_msg.edit_text("❌ <b>فشل في إنشاء ملف PDF</b>\n\n⚠️ <b>تم استرجاع المبلغ</b>", parse_mode=ParseMode.HTML)
                os.remove(pdf_path)
                self.user_manager.cancel_purchase(user_id)
        
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة PDF: {e}")
            await processing_msg.edit_text("❌ <b>حدث خطأ في معالجة الملف</b>\n\n⚠️ <b>تم استرجاع المبلغ</b>", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
        
        return ConversationHandler.END
    
    # ============= قسم سؤال وجواب بالذكاء =============
    async def handle_service_qa(self, query, context: ContextTypes.DEFAULT_TYPE):
        user_id = query.from_user.id
        
        if not self.settings_manager.is_service_active("qa"):
            await query.edit_message_text(
                "⏸️ <b>هذه الخدمة غير متاحة حالياً</b>\n\n"
                "تم تعطيل هذه الخدمة مؤقتاً.\n"
                f"📞 للاستفسار: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        user_data = self.user_manager.get_user(user_id)
        price = self.settings_manager.get_price("qa")
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي!</b>\n\n"
                f"💰 سعر الخدمة: {price:,} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>\n\n"
                f"📞 تواصل مع الدعم الفني: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        self.user_manager.set_pending_purchase(user_id, "qa", price)
        
        await query.edit_message_text(
            "❓ <b>أرسل سؤالك الآن</b>\n\n"
            f"💰 سعر الخدمة: {price:,} دينار\n"
            f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
            "⏳ جاهز للإجابة على أسئلتك\n"
            "⚠️ <b>سيتم خصم المبلغ بعد إتمام الخدمة</b>",
            parse_mode=ParseMode.HTML
        )
        
        return QA_QUESTION
    
    async def handle_qa_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        question = update.message.text.strip()
        
        if len(question) < 5:
            await update.message.reply_text("❌ <b>السؤال قصير جداً</b>\n\nيرجى كتابة سؤال مفصل", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
            return QA_QUESTION
        
        processing_msg = await update.message.reply_text("🤖 <b>جاري البحث عن الإجابة...</b>", parse_mode=ParseMode.HTML)
        
        try:
            answer = self.ai_service.answer_question(question)
            
            if answer.startswith("❌"):
                await processing_msg.edit_text(f"{answer}\n\n⚠️ <b>تم استرجاع المبلغ</b>", parse_mode=ParseMode.HTML)
                self.user_manager.cancel_purchase(user_id)
                return ConversationHandler.END
            
            if self.user_manager.complete_purchase(user_id):
                price = self.settings_manager.get_price("qa")
                new_balance = self.user_manager.update_balance(user_id, -price, f"سؤال وجواب بالذكاء")
                
                await processing_msg.edit_text(
                    f"❓ <b>سؤالك:</b>\n{question}\n\n"
                    f"💡 <b>الإجابة:</b>\n{answer[:2000]}\n\n"
                    f"💰 تم خصم: {price:,} دينار\n"
                    f"💳 رصيدك المتبقي: {new_balance:,} دينار",
                    parse_mode=ParseMode.HTML
                )
                
                keyboard = [[InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="back_home")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("🔙", reply_markup=reply_markup)
            else:
                await processing_msg.edit_text("❌ <b>حدث خطأ في المعاملة</b>", parse_mode=ParseMode.HTML)
                self.user_manager.cancel_purchase(user_id)
        
        except Exception as e:
            logger.error(f"❌ خطأ في الإجابة على السؤال: {e}")
            await processing_msg.edit_text("❌ <b>حدث خطأ في الإجابة</b>\n\n⚠️ <b>تم استرجاع المبلغ</b>", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
        
        return ConversationHandler.END
    
    # ============= قسم ساعدوني طلاب =============
    async def handle_service_help_student(self, query, context: ContextTypes.DEFAULT_TYPE):
        user_id = query.from_user.id
        
        if not self.settings_manager.is_service_active("help_student"):
            await query.edit_message_text(
                "⏸️ <b>هذه الخدمة غير متاحة حالياً</b>\n\n"
                "تم تعطيل هذه الخدمة مؤقتاً.\n"
                f"📞 للاستفسار: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        can_ask, message = self.user_manager.can_ask_question(user_id)
        if not can_ask:
            await query.edit_message_text(
                f"⏳ <b>لا يمكنك طرح سؤال جديد الآن</b>\n\n{message}\n\n"
                f"💡 يمكنك الإجابة على أسئلة الآخرين وكسب {self.settings_manager.admin_settings.get('answer_reward', 100)} نقطة",
                parse_mode=ParseMode.HTML
            )
            return
        
        user_data = self.user_manager.get_user(user_id)
        price = self.settings_manager.get_price("help_student")
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي!</b>\n\n"
                f"💰 سعر الخدمة: {price:,} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        self.user_manager.set_pending_purchase(user_id, "help_student", price)
        
        await query.edit_message_text(
            "🤝 <b>ساعدوني طلاب</b>\n\n"
            f"💰 سعر الخدمة: {price:,} دينار\n"
            f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
            "📝 <b>أرسل سؤالك الآن:</b>\n"
            "• يمكنك إرسال نص فقط\n"
            "• السؤال يجب أن يكون متعلقاً بالدراسة\n"
            "• سوف يتم خصم المبلغ بعد إرسال السؤال\n\n"
            "⚠️ <b>ملاحظة:</b> يمكنك طرح سؤال واحد كل 24 ساعة\n"
            f"🎯 <b>المكافأة للمجيب:</b> {self.settings_manager.admin_settings.get('answer_reward', 100)} نقطة",
            parse_mode=ParseMode.HTML
        )
        
        return HELP_STUDENT_QUESTION
    
    async def handle_help_student_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        question_text = update.message.text.strip()
        
        if len(question_text) < 10:
            await update.message.reply_text("❌ <b>السؤال قصير جداً</b>\n\nيرجى كتابة سؤال مفصل", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
            return HELP_STUDENT_QUESTION
        
        if self.user_manager.complete_purchase(user_id):
            price = self.settings_manager.get_price("help_student")
            new_balance = self.user_manager.update_balance(user_id, -price, f"طرح سؤال في ساعدوني طلاب")
            
            self.user_manager.update_question_time(user_id)
            
            question_id = self.questions_manager.add_question(user_id, question_text)
            
            await update.message.reply_text(
                f"✅ <b>تم إضافة سؤالك بنجاح!</b>\n\n"
                f"🆔 <b>رقم السؤال:</b> {question_id}\n"
                f"💰 <b>تم خصم:</b> {price:,} دينار\n"
                f"💳 <b>رصيدك المتبقي:</b> {new_balance:,} دينار\n\n"
                f"⏳ <b>الحالة:</b> في انتظار الإجابة\n"
                f"🎯 <b>المكافأة للمجيب:</b> {self.settings_manager.admin_settings.get('answer_reward', 100)} نقطة\n\n"
                f"💡 سوف تتلقى إشعاراً عندما يتم الرد على سؤالك",
                parse_mode=ParseMode.HTML
            )
            
            await self.show_student_questions_internal(update, context, user_id)
        else:
            await update.message.reply_text("❌ <b>حدث خطأ في المعاملة</b>", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
        
        return ConversationHandler.END
    
    async def show_student_questions_internal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, exclude_user_id: int = None):
        active_questions = self.questions_manager.get_active_questions(exclude_user_id)
        
        if not active_questions:
            keyboard = [[InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="back_home")]]
            
            await update.message.reply_text(
                "📭 <b>لا توجد أسئلة متاحة للإجابة حالياً</b>\n\n"
                "يمكنك العودة لاحقاً للبحث عن أسئلة للإجابة عليها",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return
        
        message = f"🤝 <b>الأسئلة المتاحة للإجابة:</b>\n\n"
        message += f"🎯 <b>مكافأة الإجابة:</b> {self.settings_manager.admin_settings.get('answer_reward', 100)} نقطة\n\n"
        
        keyboard = []
        for question in active_questions:
            question_text = question['question'][:50] + "..." if len(question['question']) > 50 else question['question']
            views = question.get('views', 0)
            
            btn_text = f"❓ {question_text} ({views} 👁️)"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"view_question_{question['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔄 تحديث القائمة", callback_data="student_questions")])
        keyboard.append([InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="back_home")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    # ============= قسم ملازمي ومرشحاتي =============
    async def handle_service_materials(self, query):
        user_id = query.from_user.id
        
        if not self.settings_manager.is_service_active("materials"):
            await query.edit_message_text(
                "⏸️ <b>خدمة المواد غير متاحة حالياً</b>\n\n"
                "تم تعطيل هذه الخدمة مؤقتاً.\n"
                f"📞 للاستفسار: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        user_data = self.user_manager.get_user(user_id)
        price = self.settings_manager.get_price("materials")
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي!</b>\n\n"
                f"💰 سعر الخدمة: {price:,} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        stages = self.materials_manager.get_all_stages()
        
        if not stages:
            keyboard = [[InlineKeyboardButton("🏠 الرجوع للرئيسية", callback_data="back_home")]]
            await query.edit_message_text(
                "📭 <b>لا توجد مواد متاحة حالياً</b>\n\n"
                "📞 تواصل مع الدعم الفني لإضافة مواد جديدة",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return
        
        self.user_manager.set_pending_purchase(user_id, "materials", price)
        
        keyboard = []
        for stage in stages:
            materials_count = len(self.materials_manager.get_materials_by_stage(stage))
            btn_text = f"📘 {stage} ({materials_count})"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"materials_stage_{stage}")])
        
        keyboard.append([InlineKeyboardButton("🏠 الرجوع للرئيسية", callback_data="back_home")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📖 <b>اختر المرحلة الدراسية:</b>\n\n"
            f"💰 سعر الخدمة: {price:,} دينار\n"
            f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
            "⚠️ <b>سيتم خصم المبلغ عند اختيار المرحلة</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_materials_stage_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, stage: str):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if self.user_manager.complete_purchase(user_id):
            price = self.settings_manager.get_price("materials")
            new_balance = self.user_manager.update_balance(user_id, -price, f"الوصول لمواد مرحلة {stage}")
            
            materials = self.materials_manager.get_materials_by_stage(stage)
            
            if not materials:
                keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="service_materials")]]
                await query.edit_message_text(
                    f"📭 <b>لا توجد مواد لمرحلة {stage}</b>\n\n"
                    f"💰 تم خصم: {price:,} دينار\n"
                    f"💳 رصيدك المتبقي: {new_balance:,} دينار",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
                return
            
            message = f"<b>📚 مواد مرحلة {stage}:</b>\n\n"
            message += f"💰 تم خصم: {price:,} دينار\n"
            message += f"💳 رصيدك المتبقي: {new_balance:,} دينار\n\n"
            
            keyboard = []
            for material in materials:
                btn_text = f"📄 {material.get('name', 'بدون اسم')}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"download_material_{material['id']}")])
                
                message += f"<b>📖 {material.get('name', 'بدون اسم')}</b>\n"
                description = material.get('description', '')
                if len(description) > 60:
                    description = description[:60] + "..."
                message += f"📝 {description}\n\n"
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="service_materials")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text("❌ <b>حدث خطأ في المعاملة</b>", parse_mode=ParseMode.HTML)
            self.user_manager.cancel_purchase(user_id)
    
    # ============= نظام VIP الكامل =============
    async def show_vip_lectures_store(self, query):
        """عرض متجر محاضرات VIP"""
        approved_lectures = self.vip_manager.get_approved_lectures()
        
        if not approved_lectures:
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="vip_lectures_store")],
                [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")]
            ]
            
            await query.edit_message_text(
                "📭 <b>لا توجد محاضرات VIP متاحة حالياً</b>\n\n"
                "يمكنك العودة لاحقاً للتحقق من المحاضرات الجديدة",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return
        
        message = f"👑 <b>متجر محاضرات VIP ({len(approved_lectures)})</b>\n\n"
        message += "📚 <b>اختر محاضرة للشراء:</b>\n\n"
        
        keyboard = []
        for lecture in approved_lectures[:15]:  # عرض أول 15 محاضرة
            title = lecture.get('title', 'بدون عنوان')[:40]
            price = lecture.get('price', 0)
            teacher_id = lecture.get('teacher_id')
            teacher_data = self.user_manager.get_user(teacher_id)
            teacher_name = teacher_data.get('first_name', 'مجهول')[:15]
            
            btn_text = f"🎓 {title}"
            if price > 0:
                btn_text += f" - {price:,} د"
            else:
                btn_text += " - مجاني"
            
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"vip_view_lecture_{lecture['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔄 تحديث", callback_data="vip_lectures_store")])
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")])
        
        if query.from_user.id == ADMIN_ID or self.user_manager.is_vip(query.from_user.id):
            keyboard.append([InlineKeyboardButton("📤 رفع محاضرة", callback_data="vip_add_lecture")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_vip_view_lecture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
        """عرض تفاصيل محاضرة للشراء"""
        query = update.callback_query
        await query.answer()
        
        lecture = self.vip_manager.get_lecture_by_id(lecture_id)
        if not lecture or lecture["status"] != "approved":
            await query.edit_message_text("❌ <b>المحاضرة غير موجودة أو غير معتمدة</b>", parse_mode=ParseMode.HTML)
            return
        
        teacher_id = lecture["teacher_id"]
        teacher_data = self.user_manager.get_user(teacher_id)
        teacher_name = teacher_data.get('first_name', 'مجهول')
        
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        # التحقق إذا كان المستخدم اشترى المحاضرة مسبقاً
        student_purchases = self.vip_manager.get_student_purchases(user_id)
        already_purchased = any(purchase["lecture_id"] == lecture_id for purchase in student_purchases)
        
        message = f"""
👑 <b>تفاصيل المحاضرة</b>

📝 <b>العنوان:</b> {lecture.get('title', 'بدون عنوان')}
👤 <b>المعلم:</b> {teacher_name}
💰 <b>السعر:</b> {lecture.get('price', 0):,} دينار
📅 <b>تاريخ النشر:</b> {lecture.get('approved_date', 'غير معروف')}
👁️ <b>المشاهدات:</b> {lecture.get('views', 0)}
🛒 <b>المبيعات:</b> {lecture.get('sales', 0)}
💎 <b>الأرباح:</b> {lecture.get('earnings', 0):,} دينار

📄 <b>الوصف:</b>
{lecture.get('description', 'بدون وصف')}

💳 <b>رصيدك:</b> {user_data['balance']:,} دينار
"""
        
        keyboard = []
        
        if already_purchased:
            message += "\n✅ <b>لقد اشتريت هذه المحاضرة مسبقاً</b>"
            keyboard.append([InlineKeyboardButton("📥 تحميل المحاضرة", callback_data=f"vip_download_{lecture_id}")])
        else:
            if lecture.get('price', 0) == 0:
                keyboard.append([InlineKeyboardButton("🎁 تحميل مجاني", callback_data=f"vip_buy_{lecture_id}")])
            else:
                if user_data['balance'] >= lecture.get('price', 0):
                    keyboard.append([InlineKeyboardButton(f"🛒 شراء المحاضرة ({lecture.get('price', 0):,} د)", callback_data=f"vip_buy_{lecture_id}")])
                else:
                    message += f"\n❌ <b>رصيدك غير كافي للشراء</b>\n💵 تحتاج: {lecture.get('price', 0):,} دينار"
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع للمتجر", callback_data="vip_lectures_store")])
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_vip_buy_lecture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
        """شراء محاضرة VIP"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        lecture = self.vip_manager.get_lecture_by_id(lecture_id)
        
        if not lecture or lecture["status"] != "approved":
            await query.answer("❌ المحاضرة غير موجودة", show_alert=True)
            return
        
        price = lecture.get('price', 0)
        
        # التحقق إذا كان المحاضرة مجانية
        if price == 0:
            # معالجة التحميل المجاني
            await self.handle_vip_download_lecture(query, context, lecture_id)
            return
        
        user_data = self.user_manager.get_user(user_id)
        
        if user_data['balance'] < price:
            await query.answer(f"❌ رصيدك غير كافي! تحتاج {price:,} دينار", show_alert=True)
            return
        
        # التحقق إذا كان المستخدم اشترى المحاضرة مسبقاً
        student_purchases = self.vip_manager.get_student_purchases(user_id)
        if any(purchase["lecture_id"] == lecture_id for purchase in student_purchases):
            await query.answer("✅ لقد اشتريت هذه المحاضرة مسبقاً", show_alert=True)
            await self.handle_vip_download_lecture(query, context, lecture_id)
            return
        
        # خصم المبلغ من الطالب
        new_balance, _ = self.user_manager.update_balance(user_id, -price, f"شراء محاضرة VIP: {lecture.get('title', '')}")
        
        # تسجيل عملية الشراء
        success, teacher_id = self.vip_manager.purchase_lecture(user_id, lecture_id, price)
        
        if success:
            # إعطاء 50% للمعلم
            teacher_share = int(price * 0.5)
            teacher_new_balance, _ = self.user_manager.update_balance(teacher_id, teacher_share, f"ربح من بيع محاضرة: {lecture.get('title', '')}")
            
            # تحديث إحصائيات المعلم
            teacher_data = self.user_manager.get_user(teacher_id)
            teacher_data["vip_earnings"] = teacher_data.get("vip_earnings", 0) + teacher_share
            teacher_data["vip_sales"] = teacher_data.get("vip_sales", 0) + 1
            self.user_manager.save_users()
            
            # إشعار للمعلم
            teacher_message = f"""
💰 <b>تم بيع محاضرة لك!</b>

📝 <b>المحاضرة:</b> {lecture.get('title', 'بدون عنوان')}
👤 <b>الطالب:</b> {user_data.get('first_name', 'مجهول')}
💵 <b>السعر:</b> {price:,} دينار
🎁 <b>حصتك:</b> {teacher_share:,} دينار (50%)
💳 <b>رصيدك الجديد:</b> {teacher_new_balance:,} دينار

🎉 <b>مبروك على البيع!</b>
"""
            await self.send_notification(teacher_id, teacher_message, context)
            
            # إشعار للطالب
            student_message = f"""
✅ <b>تم شراء المحاضرة بنجاح!</b>

📝 <b>المحاضرة:</b> {lecture.get('title', 'بدون عنوان')}
👤 <b>المعلم:</b> {self.user_manager.get_user(teacher_id).get('first_name', 'مجهول')}
💵 <b>المبلغ:</b> {price:,} دينار
💳 <b>رصيدك الجديد:</b> {new_balance:,} دينار

📥 <b>يمكنك الآن تحميل المحاضرة</b>
"""
            await query.edit_message_text(student_message, parse_mode=ParseMode.HTML)
            
            # إضافة زر التحميل
            keyboard = [
                [InlineKeyboardButton("📥 تحميل المحاضرة", callback_data=f"vip_download_{lecture_id}")],
                [InlineKeyboardButton("🔙 رجوع للمتجر", callback_data="vip_lectures_store")],
                [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("📥", reply_markup=reply_markup)
        else:
            # استرجاع المبلغ في حالة الفشل
            self.user_manager.update_balance(user_id, price, f"استرجاع رصيد لشراء محاضرة فاشل")
            await query.answer("❌ فشل في عملية الشراء", show_alert=True)
    
    async def handle_vip_download_lecture(self, query, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
        """تحميل محاضرة VIP"""
        user_id = query.from_user.id
        lecture = self.vip_manager.get_lecture_by_id(lecture_id)
        
        if not lecture:
            await query.answer("❌ المحاضرة غير موجودة", show_alert=True)
            return
        
        # التحقق من صلاحية التحميل
        if lecture.get('price', 0) > 0:
            student_purchases = self.vip_manager.get_student_purchases(user_id)
            if not any(purchase["lecture_id"] == lecture_id for purchase in student_purchases):
                await query.answer("❌ يجب شراء المحاضرة أولاً", show_alert=True)
                return
        
        file_info = lecture.get('file_info', {})
        file_id = file_info.get('file_id')
        file_type = file_info.get('file_type', 'document')
        
        if not file_id:
            await query.answer("❌ لا يوجد ملف لهذه المحاضرة", show_alert=True)
            return
        
        try:
            # زيادة عدد التحميلات
            lecture["downloads"] = lecture.get("downloads", 0) + 1
            self.vip_manager.save_all_data()
            
            # إرسال الملف
            if file_type == 'video':
                await context.bot.send_video(
                    chat_id=user_id,
                    video=file_id,
                    caption=f"📹 <b>{lecture.get('title', 'بدون عنوان')}</b>\n\n"
                           f"👤 <b>المعلم:</b> {self.user_manager.get_user(lecture['teacher_id']).get('first_name', 'مجهول')}\n"
                           f"📝 {lecture.get('description', '')[:200]}",
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file_id,
                    caption=f"📄 <b>{lecture.get('title', 'بدون عنوان')}</b>\n\n"
                           f"👤 <b>المعلم:</b> {self.user_manager.get_user(lecture['teacher_id']).get('first_name', 'مجهول')}\n"
                           f"📝 {lecture.get('description', '')[:200]}",
                    parse_mode=ParseMode.HTML
                )
            
            await query.answer("✅ تم إرسال المحاضرة", show_alert=True)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الملف: {e}")
            await query.answer("❌ فشل في إرسال الملف", show_alert=True)
    
    # ============= لوحة التحكم الكاملة =============
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        vip_users = sum(1 for user in self.user_manager.users.values() 
                       if user.get("vip_subscription") and self.user_manager.is_vip(int(list(self.user_manager.users.keys())[0])))
        
        panel_text = f"""
👑 <b>لوحة التحكم الإدارية</b>

📊 <b>إحصائيات البوت:</b>
• 👥 عدد المستخدمين: {total_users:,}
• 💰 إجمالي الرصيد: {total_balance:,} دينار
• 👑 مشتركين VIP: {vip_users}
• 📢 رابط القناة: {self.settings_manager.get_channel_link()}
• ❓ الأسئلة النشطة: {len(self.questions_manager.get_active_questions())}
• 📚 عدد المواد: {len(self.materials_manager.materials)}
• 📤 محاضرات VIP: {len(self.vip_manager.get_approved_lectures())}

⚙️ <b>اختر الإجراء:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("💰 شحن/خصم الرصيد", callback_data="admin_charge")],
            [InlineKeyboardButton("⚙️ إدارة الخدمات", callback_data="admin_services")],
            [InlineKeyboardButton("💰 تغيير الأسعار", callback_data="admin_change_prices")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📚 إدارة المواد", callback_data="admin_materials")],
            [InlineKeyboardButton("❓ إدارة الأسئلة", callback_data="admin_questions")],
            [InlineKeyboardButton("👑 إدارة VIP", callback_data="admin_vip_management")],
            [InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="admin_settings")],
            [InlineKeyboardButton("🔙 رجوع للبوت", callback_data="back_home")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message, 'edit_message_text'):
            await message.edit_message_text(panel_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(panel_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def handle_admin_change_prices(self, query):
        services = {
            "exemption": "🧮 حساب درجة الإعفاء",
            "summarize": "📚 تلخيص الملازم", 
            "qa": "❓ سؤال وجواب بالذكاء",
            "materials": "📖 ملازمي ومرشحاتي",
            "help_student": "🤝 ساعدوني طلاب",
            "vip_subscription": "👑 اشتراك VIP شهري"
        }
        
        message = "💰 <b>تغيير أسعار الخدمات</b>\n\n"
        message += "📊 <b>الأسعار الحالية:</b>\n\n"
        
        keyboard = []
        for service_key, service_name in services.items():
            current_price = self.settings_manager.get_price(service_key)
            message += f"{service_name}: {current_price:,} دينار\n"
            keyboard.append([InlineKeyboardButton(f"تغيير {service_name}", callback_data=f"change_price_{service_key}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_change_price_service(self, query, context: ContextTypes.DEFAULT_TYPE, service: str):
        service_names = {
            "exemption": "حساب درجة الإعفاء",
            "summarize": "تلخيص الملازم",
            "qa": "سؤال وجواب بالذكاء",
            "materials": "ملازمي ومرشحاتي",
            "help_student": "ساعدوني طلاب",
            "vip_subscription": "اشتراك VIP شهري"
        }
        
        current_price = self.settings_manager.get_price(service)
        
        await query.edit_message_text(
            f"💰 <b>تغيير سعر الخدمة</b>\n\n"
            f"📝 <b>الخدمة:</b> {service_names.get(service, service)}\n"
            f"💵 <b>السعر الحالي:</b> {current_price:,} دينار\n\n"
            f"🔢 <b>أدخل السعر الجديد:</b>\n"
            f"<code>1000</code>\n\n"
            f"❌ للإلغاء: /cancel",
            parse_mode=ParseMode.HTML
        )
        
        context.user_data['changing_price_service'] = service
        return CHANGE_PRICE_SERVICE
    
    async def handle_change_price_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text(
                "❌ <b>مبلغ غير صحيح!</b>\n\n"
                "يجب أن يكون المبلغ رقماً فقط\n"
                "أعد إدخال السعر:",
                parse_mode=ParseMode.HTML
            )
            return CHANGE_PRICE_SERVICE
        
        new_price = int(text)
        service = context.user_data.get('changing_price_service')
        
        if new_price <= 0:
            await update.message.reply_text(
                "❌ <b>السعر يجب أن يكون أكبر من صفر</b>\n\n"
                "أعد إدخال السعر:",
                parse_mode=ParseMode.HTML
            )
            return CHANGE_PRICE_SERVICE
        
        if service == "vip_subscription":
            self.vip_manager.update_subscription_price(new_price)
        else:
            self.settings_manager.update_price(service, new_price)
        
        service_names = {
            "exemption": "حساب درجة الإعفاء",
            "summarize": "تلخيص الملازم",
            "qa": "سؤال وجواب بالذكاء",
            "materials": "ملازمي ومرشحاتي",
            "help_student": "ساعدوني طلاب",
            "vip_subscription": "اشتراك VIP شهري"
        }
        
        await update.message.reply_text(
            f"✅ <b>تم تغيير السعر بنجاح!</b>\n\n"
            f"📝 <b>الخدمة:</b> {service_names.get(service, service)}\n"
            f"💰 <b>السعر الجديد:</b> {new_price:,} دينار",
            parse_mode=ParseMode.HTML
        )
        
        if 'changing_price_service' in context.user_data:
            del context.user_data['changing_price_service']
        
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    async def handle_admin_services(self, query):
        all_services = self.settings_manager.get_all_services()
        
        message = "⚙️ <b>إدارة الخدمات</b>\n\n"
        message += "🔧 <b>حالة الخدمات:</b>\n\n"
        
        service_names = {
            "exemption": "🧮 حساب درجة الإعفاء",
            "summarize": "📚 تلخيص الملازم",
            "qa": "❓ سؤال وجواب بالذكاء",
            "materials": "📖 ملازمي ومرشحاتي",
            "help_student": "🤝 ساعدوني طلاب",
            "vip_lectures": "👑 محاضرات VIP"
        }
        
        keyboard = []
        for service, active in all_services.items():
            status = "🟢 مفعل" if active else "🔴 معطل"
            price = self.settings_manager.get_price(service) if service in service_names else 0
            service_name = service_names.get(service, service)
            
            message += f"{service_name}: {status} ({price:,} د)\n"
            
            btn_text = f"{'❌ تعطيل' if active else '✅ تفعيل'} {service_name.split()[-1]}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"toggle_service_{service}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_toggle_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service: str):
        query = update.callback_query
        await query.answer()
        
        new_status = self.settings_manager.toggle_service(service)
        status_text = "تم تفعيل" if new_status else "تم تعطيل"
        
        service_names = {
            "exemption": "حساب درجة الإعفاء",
            "summarize": "تلخيص الملازم",
            "qa": "سؤال وجواب بالذكاء",
            "materials": "ملازمي ومرشحاتي",
            "help_student": "ساعدوني طلاب",
            "vip_lectures": "محاضرات VIP"
        }
        
        service_name = service_names.get(service, service)
        
        await query.answer(f"✅ {status_text} {service_name}")
        await self.handle_admin_services(query)
    
    async def handle_admin_materials(self, query):
        materials_count = len(self.materials_manager.materials)
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مادة جديدة", callback_data="admin_material_add")],
            [InlineKeyboardButton("📋 عرض جميع المواد", callback_data="admin_material_list")],
            [InlineKeyboardButton("🗑️ حذف مادة", callback_data="admin_material_delete_menu")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            f"📚 <b>إدارة المواد التعليمية</b>\n\n"
            f"📊 عدد المواد: {materials_count}\n\n"
            f"اختر الإجراء:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_admin_material_add(self, query, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text(
            "➕ <b>إضافة مادة جديدة</b>\n\n"
            "📤 <b>الخطوة 1 من 3:</b> أرسل ملف PDF للمادة\n\n"
            "⚠️ يجب أن يكون الملف بصيغة PDF فقط",
            parse_mode=ParseMode.HTML
        )
        return MATERIAL_FILE
    
    async def handle_material_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        if not update.message.document:
            await update.message.reply_text(
                "❌ <b>لم ترسل ملفاً!</b>\n\n"
                "يرجى إرسال ملف PDF للمادة:",
                parse_mode=ParseMode.HTML
            )
            return MATERIAL_FILE
        
        document = update.message.document
        
        if not document.mime_type == 'application/pdf':
            await update.message.reply_text(
                "❌ <b>الملف ليس بصيغة PDF!</b>\n\n"
                "يرجى إرسال ملف PDF فقط:",
                parse_mode=ParseMode.HTML
            )
            return MATERIAL_FILE
        
        file_id = document.file_id
        file_name = document.file_name or f"material_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        try:
            file = await document.get_file()
            temp_path = f"temp_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            await file.download_to_drive(temp_path)
            
            context.user_data['material_file'] = {
                'file_id': file_id,
                'file_name': file_name,
                'temp_path': temp_path
            }
            
            await update.message.reply_text(
                "✅ <b>تم حفظ الملف بنجاح</b>\n\n"
                "📝 <b>الخطوة 2 من 3:</b> أرسل وصف المادة\n\n"
                "💡 مثال: 'ملزمة رياضيات للصف السادس تحتوي على جميع الدروس والتمارين'",
                parse_mode=ParseMode.HTML
            )
            
            return MATERIAL_DESC
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الملف: {e}")
            await update.message.reply_text(
                "❌ <b>حدث خطأ في تحميل الملف</b>\n\n"
                "أعد إرسال الملف:",
                parse_mode=ParseMode.HTML
            )
            return MATERIAL_FILE
    
    async def handle_material_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        description = update.message.text.strip()
        
        if len(description) < 10:
            await update.message.reply_text(
                "❌ <b>الوصف قصير جداً!</b>\n\n"
                "يرجى كتابة وصف مفصل (10 أحرف على الأقل):",
                parse_mode=ParseMode.HTML
            )
            return MATERIAL_DESC
        
        context.user_data['material_desc'] = description
        
        await update.message.reply_text(
            "✅ <b>تم حفظ الوصف بنجاح</b>\n\n"
            "🎓 <b>الخطوة 3 من 3:</b> أرسل المرحلة الدراسية\n\n"
            "💡 مثال: 'السادس الاعدادي' أو 'الثالث متوسط'",
            parse_mode=ParseMode.HTML
        )
        
        return MATERIAL_STAGE
    
    async def handle_material_stage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        stage = update.message.text.strip()
        
        if len(stage) < 2:
            await update.message.reply_text(
                "❌ <b>المرحلة قصيرة جداً!</b>\n\n"
                "يرجى إدخال اسم المرحلة بشكل صحيح:",
                parse_mode=ParseMode.HTML
            )
            return MATERIAL_STAGE
        
        try:
            file_info = context.user_data.get('material_file', {})
            description = context.user_data.get('material_desc', '')
            
            if not file_info or not description:
                await update.message.reply_text(
                    "❌ <b>بيانات غير مكتملة!</b>\n\n"
                    "يرجى إعادة العملية من البداية",
                    parse_mode=ParseMode.HTML
                )
                return ConversationHandler.END
            
            material_name = f"ملزمة {stage} - {datetime.now().strftime('%Y/%m/%d')}"
            
            material_data = {
                "name": material_name,
                "description": description,
                "stage": stage,
                "file_id": file_info.get('file_id'),
                "file_name": file_info.get('file_name'),
                "file_path": file_info.get('temp_path'),
                "added_by": user_id
            }
            
            self.materials_manager.add_material(material_data)
            
            temp_path = file_info.get('temp_path')
            if temp_path and os.path.exists(temp_path):
                pass
            
            for key in ['material_file', 'material_desc']:
                if key in context.user_data:
                    del context.user_data[key]
            
            await update.message.reply_text(
                f"✅ <b>تم إضافة المادة بنجاح!</b>\n\n"
                f"📚 <b>الاسم:</b> {material_name}\n"
                f"📝 <b>الوصف:</b> {description[:100]}...\n"
                f"🎓 <b>المرحلة:</b> {stage}\n"
                f"📅 <b>التاريخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                parse_mode=ParseMode.HTML
            )
            
            await self.admin_panel(update, context)
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المادة: {e}")
            await update.message.reply_text(
                f"❌ <b>حدث خطأ في إضافة المادة:</b>\n{str(e)[:100]}",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
    
    async def handle_admin_material_delete_menu(self, query):
        materials = self.materials_manager.materials
        
        if not materials:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_materials")]]
            await query.edit_message_text(
                "📭 <b>لا توجد مواد للحذف</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return
        
        message = "🗑️ <b>اختر المادة للحذف:</b>\n\n"
        
        keyboard = []
        for material in materials[:10]:
            btn_text = f"❌ {material.get('name', 'بدون اسم')} - {material.get('stage', 'غير محدد')}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"delete_material_{material['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_materials")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_delete_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE, material_id: int):
        query = update.callback_query
        await query.answer()
        
        material = self.materials_manager.get_material(material_id)
        
        if not material:
            await query.edit_message_text("❌ <b>المادة غير موجودة</b>", parse_mode=ParseMode.HTML)
            return
        
        if self.materials_manager.delete_material(material_id):
            file_path = material.get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ <b>تم حذف المادة بنجاح!</b>\n\n"
                f"📚 <b>اسم المادة:</b> {material.get('name', 'بدون اسم')}\n"
                f"🎓 <b>المرحلة:</b> {material.get('stage', 'غير محدد')}",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text("❌ <b>فشل في حذف المادة</b>", parse_mode=ParseMode.HTML)
        
        await self.handle_admin_materials(query)
    
    async def handle_admin_vip_management(self, query):
        pending_lectures = len(self.vip_manager.get_pending_lectures())
        approved_lectures = len(self.vip_manager.get_approved_lectures())
        subscription_price = self.vip_manager.get_subscription_price()
        
        vip_users = 0
        for user_id_str, user_data in self.user_manager.users.items():
            if user_data.get("vip_subscription") and self.user_manager.is_vip(int(user_id_str)):
                vip_users += 1
        
        message = f"""
👑 <b>إدارة نظام VIP</b>

📊 <b>الإحصائيات:</b>
• 👥 مشتركين VIP: {vip_users}
• 📤 محاضرات قيد المراجعة: {pending_lectures}
• ✅ محاضرات معتمدة: {approved_lectures}
• 💰 سعر الاشتراك: {subscription_price:,} دينار

⚙️ <b>اختر الإجراء:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("📝 مراجعة المحاضرات", callback_data="vip_review_lectures")],
            [InlineKeyboardButton("👥 إدارة المعلمين", callback_data="vip_manage_teachers")],
            [InlineKeyboardButton("💰 تغيير سعر الاشتراك", callback_data="vip_change_subscription_price")],
            [InlineKeyboardButton("📊 إحصائيات VIP", callback_data="vip_statistics")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_vip_review_lectures(self, query):
        pending_lectures = self.vip_manager.get_pending_lectures()
        
        if not pending_lectures:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip_management")]]
            await query.edit_message_text(
                "📭 <b>لا توجد محاضرات قيد المراجعة</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return
        
        message = f"📝 <b>المحاضرات قيد المراجعة ({len(pending_lectures)})</b>\n\n"
        
        keyboard = []
        for lecture in pending_lectures[:10]:
            teacher_id = lecture["teacher_id"]
            teacher_data = self.user_manager.get_user(teacher_id)
            teacher_name = teacher_data.get("first_name", "مجهول")
            
            title = lecture.get("title", "بدون عنوان")[:30]
            date = lecture.get("added_date", "").split()[0]
            price = lecture.get("price", 0)
            
            btn_text = f"📤 {title} - {teacher_name}"
            if price > 0:
                btn_text += f" ({price:,} د)"
            
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"vip_review_detail_{lecture['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_vip_management")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_vip_review_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
        query = update.callback_query
        await query.answer()
        
        lecture = None
        for l in self.vip_manager.get_pending_lectures():
            if l["id"] == lecture_id:
                lecture = l
                break
        
        if not lecture:
            await query.edit_message_text("❌ <b>المحاضرة غير موجودة</b>", parse_mode=ParseMode.HTML)
            return
        
        teacher_id = lecture["teacher_id"]
        teacher_data = self.user_manager.get_user(teacher_id)
        
        message = f"""
📤 <b>مراجعة المحاضرة #{lecture_id}</b>

👤 <b>المعلم:</b>
• 🆔 ID: {teacher_id}
• 📛 الاسم: {teacher_data.get('first_name', 'مجهول')}
• 📅 اشتراك حتى: {teacher_data.get('vip_expiry', 'غير مشترك')}

📝 <b>تفاصيل المحاضرة:</b>
• 📌 العنوان: {lecture.get('title', 'بدون عنوان')}
• 📄 الوصف: {lecture.get('description', 'بدون وصف')}
• 💰 السعر: {lecture.get('price', 0):,} دينار
• 📅 تاريخ الإضافة: {lecture.get('added_date', 'غير معروف')}
• 📊 نوع الملف: {lecture.get('file_info', {}).get('file_type', 'غير معروف')}

⚡ <b>اختر الإجراء:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ الموافقة على المحاضرة", callback_data=f"vip_approve_lecture_{lecture_id}")],
            [InlineKeyboardButton("❌ رفض المحاضرة", callback_data=f"vip_reject_lecture_{lecture_id}")],
            [InlineKeyboardButton("👤 حظر المعلم", callback_data=f"vip_ban_teacher_{teacher_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="vip_review_lectures")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_vip_approve_lecture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
        query = update.callback_query
        await query.answer()
        
        if self.vip_manager.approve_lecture(lecture_id):
            lecture = None
            for l in self.vip_manager.lectures:
                if l["id"] == lecture_id:
                    lecture = l
                    break
            
            if lecture:
                teacher_id = lecture["teacher_id"]
                notify_message = f"""
✅ <b>تمت الموافقة على محاضراتك!</b>

🆔 <b>رقم المحاضرة:</b> {lecture_id}
📝 <b>العنوان:</b> {lecture.get('title', 'بدون عنوان')}

🎉 <b>مبروك! المحاضرة متاحة الآن للطلاب.</b>
"""
                await self.send_notification(teacher_id, notify_message, context)
            
            await query.answer("✅ تمت الموافقة على المحاضرة", show_alert=True)
            await self.handle_vip_review_lectures(query)
        else:
            await query.answer("❌ فشل في الموافقة على المحاضرة", show_alert=True)
    
    async def handle_vip_reject_lecture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
        query = update.callback_query
        await query.answer()
        
        if self.vip_manager.reject_lecture(lecture_id):
            lecture = None
            for l in self.vip_manager.lectures:
                if l["id"] == lecture_id:
                    lecture = l
                    break
            
            if lecture:
                teacher_id = lecture["teacher_id"]
                notify_message = f"""
❌ <b>تم رفض محاضراتك</b>

🆔 <b>رقم المحاضرة:</b> {lecture_id}
📝 <b>العنوان:</b> {lecture.get('title', 'بدون عنوان')}

📞 <b>للاستفسار عن أسباب الرفض:</b> @{SUPPORT_USERNAME}
"""
                await self.send_notification(teacher_id, notify_message, context)
            
            await query.answer("❌ تم رفض المحاضرة", show_alert=True)
            await self.handle_vip_review_lectures(query)
        else:
            await query.answer("❌ فشل في رفض المحاضرة", show_alert=True)
    
    async def handle_vip_ban_teacher(self, update: Update, context: ContextTypes.DEFAULT_TYPE, teacher_id: int):
        query = update.callback_query
        await query.answer()
        
        if self.vip_manager.ban_teacher(teacher_id):
            self.user_manager.remove_vip_subscription(teacher_id)
            
            notify_message = f"""
🚫 <b>تم حظر حسابك من نظام VIP!</b>

❌ <b>تم إلغاء اشتراكك وحظر حسابك</b>

📞 <b>للاستفسار:</b> @{SUPPORT_USERNAME}
"""
            await self.send_notification(teacher_id, notify_message, context)
            
            await query.answer("✅ تم حظر المعلم وإلغاء اشتراكه", show_alert=True)
        else:
            await query.answer("❌ فشل في حظر المعلم", show_alert=True)
        
        await self.handle_vip_review_lectures(query)
    
    async def handle_vip_change_subscription_price(self, query, context: ContextTypes.DEFAULT_TYPE):
        current_price = self.vip_manager.get_subscription_price()
        
        await query.edit_message_text(
            f"💰 <b>تغيير سعر اشتراك VIP</b>\n\n"
            f"💵 <b>السعر الحالي:</b> {current_price:,} دينار شهرياً\n\n"
            f"🔢 <b>أدخل السعر الجديد:</b>\n"
            f"<code>5000</code>\n\n"
            f"❌ للإلغاء: /cancel",
            parse_mode=ParseMode.HTML
        )
        
        return VIP_CHANGE_SUBSCRIPTION_PRICE
    
    async def handle_vip_subscription_price_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text(
                "❌ <b>مبلغ غير صحيح!</b>\n\n"
                "يجب أن يكون المبلغ رقماً فقط\n"
                "أعد إدخال السعر:",
                parse_mode=ParseMode.HTML
            )
            return VIP_CHANGE_SUBSCRIPTION_PRICE
        
        new_price = int(text)
        
        if new_price <= 0:
            await update.message.reply_text(
                "❌ <b>السعر يجب أن يكون أكبر من صفر</b>\n\n"
                "أعد إدخال السعر:",
                parse_mode=ParseMode.HTML
            )
            return VIP_CHANGE_SUBSCRIPTION_PRICE
        
        self.vip_manager.update_subscription_price(new_price)
        
        await update.message.reply_text(
            f"✅ <b>تم تغيير سعر الاشتراك بنجاح!</b>\n\n"
            f"💰 <b>السعر الجديد:</b> {new_price:,} دينار شهرياً",
            parse_mode=ParseMode.HTML
        )
        
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    # ============= نظام الإعفاء المعدل =============
    async def handle_service_exemption(self, query):
        user_id = query.from_user.id
        
        if not self.settings_manager.is_service_active("exemption"):
            await query.edit_message_text(
                "⏸️ <b>هذه الخدمة غير متاحة حالياً</b>\n\n"
                "تم تعطيل هذه الخدمة مؤقتاً.\n"
                f"📞 للاستفسار: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        user_data = self.user_manager.get_user(user_id)
        price = self.settings_manager.get_price("exemption")
        
        if user_data['balance'] < price:
            await query.edit_message_text(
                f"❌ <b>رصيدك غير كافي!</b>\n\n"
                f"💰 سعر الخدمة: {price:,} دينار\n"
                f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
                f"🆔 <b>رقم حسابك للشحن:</b> <code>{user_id}</code>\n\n"
                f"📞 تواصل مع الدعم الفني: @{SUPPORT_USERNAME}",
                parse_mode=ParseMode.HTML
            )
            return
        
        self.user_manager.set_pending_purchase(user_id, "exemption", price)
        
        keyboard = [
            [InlineKeyboardButton("🏠 الرجوع للرئيسية", callback_data="back_home")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🧮 <b>حاسبة درجة الإعفاء</b>\n\n"
            f"💰 سعر الخدمة: {price:,} دينار\n"
            f"💳 رصيدك الحالي: {user_data['balance']:,} دينار\n\n"
            "📝 <b>الخطوة 1 من 3:</b>\n"
            "أدخل درجة الكورس الأول:\n\n"
            "🎯 <b>المعدل المطلوب للإعفاء:</b> 90 فما فوق\n"
            "⚠️ <b>سيتم خصم المبلغ بعد الحساب</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return EXEMPTION_COURSE1
    
    async def handle_exemption_course1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        try:
            score = float(update.message.text.strip())
            
            if score < 0 or score > 100:
                await update.message.reply_text("❌ <b>الدرجة يجب أن تكون بين 0 و 100</b>\n\nأعد إدخال درجة الكورس الأول:", parse_mode=ParseMode.HTML)
                return EXEMPTION_COURSE1
            
            context.user_data['exemption_scores'] = [score]
            
            await update.message.reply_text(
                "✅ <b>تم حفظ درجة الكورس الأول</b>\n\n"
                "📝 <b>الخطوة 2 من 3:</b>\n"
                "أدخل درجة الكورس الثاني (نصف السنة):",
                parse_mode=ParseMode.HTML
            )
            
            return EXEMPTION_COURSE2
            
        except ValueError:
            await update.message.reply_text("❌ <b>أدخل رقماً صحيحاً فقط</b>\n\nأعد إدخال درجة الكورس الأول:", parse_mode=ParseMode.HTML)
            return EXEMPTION_COURSE1
    
    async def handle_exemption_course2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            score = float(update.message.text.strip())
            
            if score < 0 or score > 100:
                await update.message.reply_text("❌ <b>الدرجة يجب أن تكون بين 0 و 100</b>\n\nأعد إدخال درجة الكورس الثاني:", parse_mode=ParseMode.HTML)
                return EXEMPTION_COURSE2
            
            context.user_data['exemption_scores'].append(score)
            
            await update.message.reply_text(
                "✅ <b>تم حفظ درجة الكورس الثاني</b>\n\n"
                "📝 <b>الخطوة 3 من 3:</b>\n"
                "أدخل درجة الكورس الثالث:",
                parse_mode=ParseMode.HTML
            )
            
            return EXEMPTION_COURSE3
            
        except ValueError:
            await update.message.reply_text("❌ <b>أدخل رقماً صحيحاً فقط</b>\n\nأعد إدخال درجة الكورس الثاني:", parse_mode=ParseMode.HTML)
            return EXEMPTION_COURSE2
    
    async def handle_exemption_course3(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        try:
            score = float(update.message.text.strip())
            
            if score < 0 or score > 100:
                await update.message.reply_text("❌ <b>الدرجة يجب أن تكون بين 0 و 100</b>\n\nأعد إدخال درجة الكورس الثالث:", parse_mode=ParseMode.HTML)
                return EXEMPTION_COURSE3
            
            scores = context.user_data['exemption_scores'] + [score]
            
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
            
            if self.user_manager.complete_purchase(user_id):
                price = self.settings_manager.get_price("exemption")
                new_balance, should_notify = self.user_manager.update_balance(user_id, -price, f"حساب درجة الإعفاء")
                
                message += f"\n💰 تم خصم: {price:,} دينار"
                message += f"\n💳 رصيدك المتبقي: {new_balance:,} دينار"
                
                user_data = self.user_manager.get_user(user_id)
                user_data.setdefault("exemption_scores", []).append({
                    "scores": scores,
                    "average": average,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "exempted": average >= 90
                })
                self.user_manager.save_users()
                
                await update.message.reply_text(message, parse_mode=ParseMode.HTML)
                
                if 'exemption_scores' in context.user_data:
                    del context.user_data['exemption_scores']
                
                keyboard = [[InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="back_home")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("🔙", reply_markup=reply_markup)
            else:
                await update.message.reply_text("❌ <b>حدث خطأ في المعاملة</b>", parse_mode=ParseMode.HTML)
                self.user_manager.cancel_purchase(user_id)
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ <b>أدخل رقماً صحيحاً فقط</b>\n\nأعد إدخال درجة الكورس الثالث:", parse_mode=ParseMode.HTML)
            return EXEMPTION_COURSE3
    
    # ============= معالجة الردود الرئيسية =============
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        
        try:
            await query.answer()
            
            # ============= الخدمات الرئيسية =============
            if query.data == "service_summarize":
                await self.handle_service_summarize(query, context)
                return SUMMARIZE_PDF
            
            elif query.data == "service_qa":
                await self.handle_service_qa(query, context)
                return QA_QUESTION
            
            elif query.data == "service_help_student":
                await self.handle_service_help_student(query, context)
                return HELP_STUDENT_QUESTION
            
            elif query.data == "service_materials":
                await self.handle_service_materials(query)
            
            elif query.data == "service_exemption":
                await self.handle_service_exemption(query)
                return EXEMPTION_COURSE1
            
            elif query.data.startswith("materials_stage_"):
                stage = query.data.replace("materials_stage_", "")
                await self.handle_materials_stage_selection(update, context, stage)
            
            # ============= نظام VIP =============
            elif query.data == "vip_lectures_store":
                await self.show_vip_lectures_store(query)
            
            elif query.data.startswith("vip_view_lecture_"):
                lecture_id = query.data.replace("vip_view_lecture_", "")
                await self.handle_vip_view_lecture(update, context, lecture_id)
            
            elif query.data.startswith("vip_buy_"):
                lecture_id = query.data.replace("vip_buy_", "")
                await self.handle_vip_buy_lecture(update, context, lecture_id)
            
            elif query.data.startswith("vip_download_"):
                lecture_id = query.data.replace("vip_download_", "")
                await self.handle_vip_download_lecture(query, context, lecture_id)
            
            elif query.data == "vip_subscription_info":
                await self.show_vip_subscription_info(query)
            
            elif query.data == "vip_subscribe":
                await self.handle_vip_subscribe(query, context)
            
            elif query.data == "vip_add_lecture":
                await self.handle_vip_add_lecture(query, context)
                return VIP_LECTURE_TITLE
            
            # ============= أسئلة الطلاب =============
            elif query.data == "student_questions":
                await self.show_student_questions_internal(update, context, query.from_user.id)
            
            # ============= لوحة التحكم =============
            elif query.data == "admin_panel":
                await self.admin_panel(update, context)
            
            elif query.data == "admin_change_prices":
                await self.handle_admin_change_prices(query)
            
            elif query.data.startswith("change_price_"):
                service = query.data.replace("change_price_", "")
                await self.handle_change_price_service(query, context, service)
                return CHANGE_PRICE_SERVICE
            
            elif query.data == "admin_vip_management":
                await self.handle_admin_vip_management(query)
            
            elif query.data == "vip_review_lectures":
                await self.handle_vip_review_lectures(query)
            
            elif query.data.startswith("vip_review_detail_"):
                lecture_id = query.data.replace("vip_review_detail_", "")
                await self.handle_vip_review_detail(update, context, lecture_id)
            
            elif query.data.startswith("vip_approve_lecture_"):
                lecture_id = query.data.replace("vip_approve_lecture_", "")
                await self.handle_vip_approve_lecture(update, context, lecture_id)
            
            elif query.data.startswith("vip_reject_lecture_"):
                lecture_id = query.data.replace("vip_reject_lecture_", "")
                await self.handle_vip_reject_lecture(update, context, lecture_id)
            
            elif query.data.startswith("vip_ban_teacher_"):
                teacher_id = int(query.data.replace("vip_ban_teacher_", ""))
                await self.handle_vip_ban_teacher(update, context, teacher_id)
            
            elif query.data == "vip_change_subscription_price":
                await self.handle_vip_change_subscription_price(query, context)
                return VIP_CHANGE_SUBSCRIPTION_PRICE
            
            # ============= باقي الأوامر =============
            elif query.data == "admin_users":
                await self.handle_admin_users(query)
            
            elif query.data.startswith("admin_user_list_"):
                page = int(query.data.replace("admin_user_list_", ""))
                await self.show_users_list(query, page)
            
            elif query.data == "admin_charge":
                await self.handle_admin_charge(query)
            
            elif query.data == "admin_charge_user":
                await self.handle_admin_charge_user(query, context)
                return CHARGE_USER
            
            elif query.data == "admin_deduct_user":
                await self.handle_admin_deduct_user(query, context)
                return CHARGE_USER
            
            elif query.data == "admin_services":
                await self.handle_admin_services(query)
            
            elif query.data.startswith("toggle_service_"):
                service = query.data.replace("toggle_service_", "")
                await self.handle_toggle_service(update, context, service)
            
            elif query.data == "admin_materials":
                await self.handle_admin_materials(query)
            
            elif query.data == "admin_material_add":
                await self.handle_admin_material_add(query, context)
                return MATERIAL_FILE
            
            elif query.data == "admin_material_delete_menu":
                await self.handle_admin_material_delete_menu(query)
            
            elif query.data.startswith("delete_material_"):
                material_id = int(query.data.replace("delete_material_", ""))
                await self.handle_delete_material(update, context, material_id)
            
            elif query.data == "admin_questions":
                await self.handle_admin_questions(query)
            
            elif query.data == "admin_settings":
                await self.handle_admin_settings(query)
            
            elif query.data == "admin_change_channel":
                await self.handle_admin_change_channel(query, context)
                return CHANGE_CHANNEL
            
            elif query.data.startswith("stage_"):
                stage = query.data.replace("stage_", "")
                await self.show_stage_materials(query, stage)
            
            elif query.data.startswith("download_material_"):
                material_id = int(query.data.replace("download_material_", ""))
                await self.handle_download_material(update, context, material_id)
            
            elif query.data.startswith("view_question_"):
                question_id = query.data.replace("view_question_", "")
                await self.handle_view_question(update, context, question_id)
            
            elif query.data.startswith("answer_question_"):
                question_id = query.data.replace("answer_question_", "")
                return await self.handle_answer_question(update, context, question_id)
            
            elif query.data == "refresh_questions":
                await self.show_student_questions_internal(update, context, query.from_user.id)
            
            elif query.data == "balance":
                await self.handle_balance_check(update, context)
            
            elif query.data == "back_home":
                await self.handle_back_home(update, context)
            
            else:
                await query.answer("⏳ جاري التحميل...")
        
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرد: {e}")
            await query.answer("❌ حدث خطأ. حاول مرة أخرى")
    
    # ============= دوال مساعدة إضافية =============
    async def show_student_questions(self, query):
        await self.show_student_questions_internal(None, None, query.from_user.id)
    
    async def show_vip_subscription_info(self, query):
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        vip_price = self.vip_manager.get_subscription_price()
        is_vip = self.user_manager.is_vip(user_id)
        
        if is_vip:
            expiry_date = user_data.get("vip_expiry")
            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
                days_left = (expiry - datetime.now()).days
                vip_status = f"✅ <b>مشترك VIP حتى:</b> {expiry_date}\n⏳ <b>متبقي:</b> {days_left} يوم"
            except:
                vip_status = "✅ <b>مشترك VIP</b>"
        else:
            vip_status = "❌ <b>غير مشترك</b>"
        
        message = f"""
👑 <b>نظام المحاضرات VIP</b>

📊 <b>حالتك:</b> {vip_status}

💰 <b>سعر الاشتراك الشهري:</b> {vip_price:,} دينار

🎯 <b>مزايا الاشتراك:</b>
• ✅ رفع محاضرات فيديو
• ✅ قسم خاص لمحاضراتك
• ✅ دخل إضافي من بيع المحاضرات
• ✅ لوحة تحكم خاصة
• ✅ دعم فني مميز

📝 <b>شروط الاشتراك:</b>
1. أن تكون معلماً أو محاضراً
2. دفع الاشتراك الشهري
3. الموافقة على المحاضرات من الإدارة
4. الالتزام بمعايير الجودة

💳 <b>رصيدك الحالي:</b> {user_data['balance']:,} دينار
"""
        
        keyboard = []
        
        if is_vip:
            keyboard.append([InlineKeyboardButton("📤 رفع محاضرة جديدة", callback_data="vip_add_lecture")])
            keyboard.append([InlineKeyboardButton("📚 محاضراتي", callback_data="vip_my_lectures")])
            keyboard.append([InlineKeyboardButton("📊 إحصائياتي", callback_data="vip_my_stats")])
        else:
            if user_data['balance'] >= vip_price:
                keyboard.append([InlineKeyboardButton("💳 اشتراك الآن", callback_data="vip_subscribe")])
            else:
                keyboard.append([InlineKeyboardButton("💰 شحن الرصيد", url=f"https://t.me/{SUPPORT_USERNAME}")])
        
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")])
        
        if query.from_user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 إدارة VIP", callback_data="admin_vip_management")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_vip_subscribe(self, query, context: ContextTypes.DEFAULT_TYPE):
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        vip_price = self.vip_manager.get_subscription_price()
        
        if user_data['balance'] < vip_price:
            await query.answer(f"❌ رصيدك غير كافي! تحتاج {vip_price:,} دينار", show_alert=True)
            return
        
        new_balance, should_notify = self.user_manager.update_balance(user_id, -vip_price, "اشتراك VIP شهري")
        
        self.user_manager.add_vip_subscription(user_id, 1)
        
        notify_message = f"""
✅ <b>تم تفعيل اشتراك VIP بنجاح!</b>

💰 <b>المبلغ:</b> {vip_price:,} دينار
💳 <b>رصيدك الجديد:</b> {new_balance:,} دينار
📅 <b>تاريخ الانتهاء:</b> {self.user_manager.get_user(user_id)['vip_expiry']}

🎉 <b>مبروك! يمكنك الآن رفع محاضراتك.</b>
"""
        await self.send_notification(user_id, notify_message, context)
        
        admin_message = f"""
👑 <b>اشتراك VIP جديد</b>

👤 <b>المستخدم:</b> {user_id}
📛 <b>الاسم:</b> {user_data['first_name']}
📅 <b>تاريخ الانتهاء:</b> {self.user_manager.get_user(user_id)['vip_expiry']}
"""
        await self.send_notification(ADMIN_ID, admin_message, context)
        
        await query.answer("✅ تم تفعيل اشتراك VIP بنجاح!", show_alert=True)
        await self.show_vip_subscription_info(query)
    
    async def handle_vip_add_lecture(self, query, context: ContextTypes.DEFAULT_TYPE):
        user_id = query.from_user.id
        
        if not self.user_manager.is_vip(user_id):
            await query.answer("❌ يجب الاشتراك في VIP أولاً", show_alert=True)
            return
        
        await query.edit_message_text(
            "📤 <b>إضافة محاضرة VIP جديدة</b>\n\n"
            "📝 <b>الخطوة 1 من 4:</b>\n"
            "أدخل عنوان المحاضرة:\n\n"
            "💡 مثال: 'شرح الدرس الأول في الرياضيات'",
            parse_mode=ParseMode.HTML
        )
        
        return VIP_LECTURE_TITLE
    
    async def handle_vip_lecture_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        title = update.message.text.strip()
        
        if len(title) < 5:
            await update.message.reply_text("❌ <b>العنوان قصير جداً</b>\n\nأدخل عنواناً واضحاً (5 أحرف على الأقل):", parse_mode=ParseMode.HTML)
            return VIP_LECTURE_TITLE
        
        context.user_data['vip_lecture_title'] = title
        
        await update.message.reply_text(
            "✅ <b>تم حفظ العنوان</b>\n\n"
            "📝 <b>الخطوة 2 من 4:</b>\n"
            "أدخل وصف المحاضرة:\n\n"
            "💡 مثال: 'شرح مفصل للدرس الأول مع أمثلة تطبيقية'",
            parse_mode=ParseMode.HTML
        )
        
        return VIP_LECTURE_DESC
    
    async def handle_vip_lecture_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        description = update.message.text.strip()
        
        if len(description) < 10:
            await update.message.reply_text("❌ <b>الوصف قصير جداً</b>\n\nأدخل وصفاً مفصلاً (10 أحرف على الأقل):", parse_mode=ParseMode.HTML)
            return VIP_LECTURE_DESC
        
        context.user_data['vip_lecture_desc'] = description
        
        await update.message.reply_text(
            "✅ <b>تم حفظ الوصف</b>\n\n"
            "📝 <b>الخطوة 3 من 4:</b>\n"
            "حدد سعر المحاضرة (اختياري):\n\n"
            "💡 أدخل 0 إذا كانت مجانية\n"
            "💸 أو أدخل السعر المطلوب",
            parse_mode=ParseMode.HTML
        )
        
        return VIP_LECTURE_PRICE
    
    async def handle_vip_lecture_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            price = int(update.message.text.strip())
            
            if price < 0:
                await update.message.reply_text("❌ <b>السعر لا يمكن أن يكون سالباً</b>\n\nأدخل سعراً صحيحاً:", parse_mode=ParseMode.HTML)
                return VIP_LECTURE_PRICE
            
            context.user_data['vip_lecture_price'] = price
            
            await update.message.reply_text(
                "✅ <b>تم حفظ السعر</b>\n\n"
                "📝 <b>الخطوة 4 من 4:</b>\n"
                "أرسل ملف المحاضرة (فيديو):\n\n"
                "📹 يمكنك إرسال ملف فيديو\n"
                "📎 أو ملف PDF\n"
                "⚠️ الحد الأقصى: 50 ميجابايت",
                parse_mode=ParseMode.HTML
            )
            
            return VIP_LECTURE_FILE
            
        except ValueError:
            await update.message.reply_text("❌ <b>أدخل رقماً صحيحاً فقط</b>\n\nأدخل سعر المحاضرة:", parse_mode=ParseMode.HTML)
            return VIP_LECTURE_PRICE
    
    async def handle_vip_lecture_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not update.message.document and not update.message.video:
            await update.message.reply_text("❌ <b>لم ترسل ملفاً!</b>\n\nأرسل ملف المحاضرة (فيديو أو PDF):", parse_mode=ParseMode.HTML)
            return VIP_LECTURE_FILE
        
        file_info = {}
        
        if update.message.document:
            document = update.message.document
            file_info = {
                "file_id": document.file_id,
                "file_name": document.file_name or f"lecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "file_type": "document",
                "mime_type": document.mime_type,
                "file_size": document.file_size
            }
        elif update.message.video:
            video = update.message.video
            file_info = {
                "file_id": video.file_id,
                "file_name": f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                "file_type": "video",
                "mime_type": "video/mp4",
                "file_size": video.file_size,
                "duration": video.duration,
                "width": video.width,
                "height": video.height
            }
        
        lecture_id = self.vip_manager.add_lecture(
            user_id,
            context.user_data['vip_lecture_title'],
            context.user_data['vip_lecture_desc'],
            file_info,
            context.user_data['vip_lecture_price']
        )
        
        for key in ['vip_lecture_title', 'vip_lecture_desc', 'vip_lecture_price']:
            if key in context.user_data:
                del context.user_data[key]
        
        admin_message = f"""
📤 <b>محاضرة VIP جديدة تنتظر الموافقة</b>

👤 <b>المعلم:</b> {user_id}
📛 <b>الاسم:</b> {self.user_manager.get_user(user_id)['first_name']}
📝 <b>العنوان:</b> {context.user_data.get('vip_lecture_title', 'بدون عنوان')}
💰 <b>السعر:</b> {context.user_data.get('vip_lecture_price', 0):,} دينار
🆔 <b>رقم المحاضرة:</b> {lecture_id}

⚡ <b>استخدم لوحة التحكم للموافقة أو الرفض</b>
"""
        await self.send_notification(ADMIN_ID, admin_message, context)
        
        await update.message.reply_text(
            f"✅ <b>تم إرسال المحاضرة للمراجعة!</b>\n\n"
            f"🆔 <b>رقم المحاضرة:</b> {lecture_id}\n"
            f"⏳ <b>الحالة:</b> في انتظار الموافقة\n\n"
            f"📞 <b>سيتم إعلامك عند الموافقة عليها.</b>",
            parse_mode=ParseMode.HTML
        )
        
        keyboard = [[InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔙", reply_markup=reply_markup)
        
        return ConversationHandler.END
    
    async def show_vip_my_lectures(self, query):
        user_id = query.from_user.id
        lectures = self.vip_manager.get_teacher_lectures(user_id)
        
        if not lectures:
            keyboard = [
                [InlineKeyboardButton("📤 إضافة محاضرة", callback_data="vip_add_lecture")],
                [InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")]
            ]
            await query.edit_message_text(
                "📭 <b>لا توجد محاضرات لعرضها</b>\n\n"
                "يمكنك إضافة محاضرة جديدة من الزر أدناه",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return
        
        message = f"📚 <b>محاضراتي ({len(lectures)})</b>\n\n"
        
        keyboard = []
        for lecture in lectures[:10]:
            status_emoji = "✅" if lecture.get("status") == "approved" else "⏳"
            title = lecture.get("title", "بدون عنوان")[:30]
            price = lecture.get("price", 0)
            views = lecture.get("views", 0)
            
            btn_text = f"{status_emoji} {title}"
            if price > 0:
                btn_text += f" ({price:,} د)"
            
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"view_vip_lecture_{lecture['id']}")])
        
        keyboard.append([InlineKeyboardButton("📤 إضافة محاضرة", callback_data="vip_add_lecture")])
        keyboard.append([InlineKeyboardButton("📊 الإحصائيات", callback_data="vip_my_stats")])
        keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="back_home")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    # ============= دوال إضافية من الكود الأصلي =============
    # (يجب إضافة باقي الدوال هنا)
    
    async def handle_admin_users(self, query):
        users_count = len(self.user_manager.users)
        
        keyboard = [
            [InlineKeyboardButton("🔍 عرض مستخدم", callback_data="admin_user_view")],
            [InlineKeyboardButton("📋 قائمة المستخدمين", callback_data="admin_user_list_1")],
            [InlineKeyboardButton("🏆 أفضل 10 مستخدمين", callback_data="admin_top_users")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            f"👥 <b>إدارة المستخدمين</b>\n\n"
            f"📊 عدد المستخدمين: {users_count:,}\n\n"
            f"اختر الإجراء:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_users_list(self, query, page: int = 1):
        users = self.user_manager.get_all_users()
        users_per_page = 10
        total_pages = max(1, (len(users) + users_per_page - 1) // users_per_page)
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * users_per_page
        end_idx = min(start_idx + users_per_page, len(users))
        
        message = f"📋 <b>قائمة المستخدمين</b>\n\n"
        message += f"📄 الصفحة {page}/{total_pages}\n"
        message += f"👥 إجمالي المستخدمين: {len(users):,}\n\n"
        
        for idx, (user_id_str, user_data) in enumerate(users[start_idx:end_idx], start_idx + 1):
            user_id = int(user_id_str)
            balance = user_data.get("balance", 0)
            join_date = user_data.get("joined_date", "غير معروف").split()[0]
            first_name = user_data.get("first_name", "بدون اسم")[:15]
            
            message += f"{idx}. <code>{user_id}</code> - {first_name}\n"
            message += f"   💰 {balance:,} دينار | 📅 {join_date}\n"
            message += "   ─" * 15 + "\n"
        
        keyboard = []
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"admin_user_list_{page-1}"))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("▶️ التالي", callback_data=f"admin_user_list_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_admin_charge(self, query):
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
        await query.edit_message_text(
            "💰 <b>شحن مستخدم</b>\n\n"
            "🔢 <b>أرسل ID المستخدم:</b>\n"
            "<code>123456789</code>\n\n"
            "💡 يمكنك الحصول على ID من قائمة المستخدمين",
            parse_mode=ParseMode.HTML
        )
        context.user_data['admin_action'] = 'charge_user'
        return CHARGE_USER
    
    async def handle_admin_deduct_user(self, query, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text(
            "💸 <b>خصم من مستخدم</b>\n\n"
            "🔢 <b>أرسل ID المستخدم:</b>\n"
            "<code>123456789</code>\n\n"
            "⚠️ تأكد من وجود رصيد كافي لدى المستخدم",
            parse_mode=ParseMode.HTML
        )
        context.user_data['admin_action'] = 'deduct_user'
        return CHARGE_USER
    
    async def handle_charge_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text(
                "❌ <b>ID غير صحيح!</b>\n\n"
                "يجب أن يكون ID مكون من أرقام فقط\n"
                "أعد إدخال ID المستخدم:",
                parse_mode=ParseMode.HTML
            )
            return CHARGE_USER
        
        target_id = int(text)
        
        target_user = self.user_manager.get_user_by_id(target_id)
        if not target_user:
            await update.message.reply_text(
                f"❌ <b>المستخدم غير موجود!</b>\n\n"
                f"ID: {target_id}\n\n"
                "تأكد من:\n"
                "• أن المستخدم استخدم البوت\n"
                "• صحة ID المستخدم\n"
                "• يمكنك التحقق من قائمة المستخدمين\n\n"
                "أعد إدخال ID المستخدم:",
                parse_mode=ParseMode.HTML
            )
            return CHARGE_USER
        
        context.user_data['charge_target'] = target_id
        context.user_data['charge_target_name'] = target_user.get('first_name', 'مستخدم')
        context.user_data['charge_target_balance'] = target_user.get('balance', 0)
        
        action = context.user_data.get('admin_action', '')
        
        if action == 'charge_user':
            await update.message.reply_text(
                f"✅ <b>تم تحديد المستخدم</b>\n\n"
                f"👤 <b>المستخدم:</b> {target_id}\n"
                f"📛 <b>الاسم:</b> {context.user_data['charge_target_name']}\n"
                f"💰 <b>الرصيد الحالي:</b> {context.user_data['charge_target_balance']:,} دينار\n\n"
                f"💵 <b>أرسل المبلغ للشحن:</b>\n"
                f"<code>5000</code>",
                parse_mode=ParseMode.HTML
            )
        elif action == 'deduct_user':
            await update.message.reply_text(
                f"✅ <b>تم تحديد المستخدم</b>\n\n"
                f"👤 <b>المستخدم:</b> {target_id}\n"
                f"📛 <b>الاسم:</b> {context.user_data['charge_target_name']}\n"
                f"💰 <b>الرصيد الحالي:</b> {context.user_data['charge_target_balance']:,} دينار\n\n"
                f"💸 <b>أرسل المبلغ للخصم:</b>\n"
                f"<code>1000</code>",
                parse_mode=ParseMode.HTML
            )
        
        return CHARGE_AMOUNT
    
    async def handle_charge_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text(
                "❌ <b>مبلغ غير صحيح!</b>\n\n"
                "يجب أن يكون المبلغ رقماً فقط\n"
                "أعد إدخال المبلغ:",
                parse_mode=ParseMode.HTML
            )
            return CHARGE_AMOUNT
        
        amount = int(text)
        target_id = context.user_data.get('charge_target')
        action = context.user_data.get('admin_action', '')
        
        if action == 'charge_user':
            if amount <= 0:
                await update.message.reply_text(
                    "❌ <b>المبلغ يجب أن يكون أكبر من صفر</b>\n\n"
                    "أعد إدخال المبلغ:",
                    parse_mode=ParseMode.HTML
                )
                return CHARGE_AMOUNT
            
            new_balance, should_notify = self.user_manager.update_balance(target_id, amount, "شحن من المدير")
            user_data = self.user_manager.get_user(target_id)
            
            if should_notify:
                notify_message = f"""
💰 <b>تم شحن رصيدك!</b>

💵 <b>المبلغ:</b> {amount:,} دينار
💳 <b>رصيدك الجديد:</b> {new_balance:,} دينار
📅 <b>التاريخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎉 <b>تمت العملية بنجاح!</b>
"""
                await self.send_notification(target_id, notify_message, context)
            
            await update.message.reply_text(
                f"✅ <b>تم الشحن بنجاح!</b>\n\n"
                f"👤 <b>المستخدم:</b> {target_id}\n"
                f"💰 <b>المبلغ:</b> {amount:,} دينار\n"
                f"💳 <b>الرصيد الجديد:</b> {user_data.get('balance', 0):,} دينار",
                parse_mode=ParseMode.HTML
            )
        
        elif action == 'deduct_user':
            if amount <= 0:
                await update.message.reply_text(
                    "❌ <b>المبلغ يجب أن يكون أكبر من صفر</b>\n\n"
                    "أعد إدخال المبلغ:",
                    parse_mode=ParseMode.HTML
                )
                return CHARGE_AMOUNT
            
            current_balance = context.user_data.get('charge_target_balance', 0)
            
            if current_balance < amount:
                await update.message.reply_text(
                    f"❌ <b>رصيد المستخدم غير كافي!</b>\n\n"
                    f"💰 رصيد المستخدم: {current_balance:,} دينار\n"
                    f"💸 المبلغ المطلوب: {amount:,} دينار\n\n"
                    f"أعد إدخال مبلغ أقل:",
                    parse_mode=ParseMode.HTML
                )
                return CHARGE_AMOUNT
            
            new_balance, should_notify = self.user_manager.update_balance(target_id, -amount, "خصم من المدير")
            user_data = self.user_manager.get_user(target_id)
            
            if should_notify:
                notify_message = f"""
💸 <b>تم خصم من رصيدك!</b>

💵 <b>المبلغ:</b> {amount:,} دينار
💳 <b>رصيدك الجديد:</b> {new_balance:,} دينار
📅 <b>التاريخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
📝 <b>السبب:</b> خصم من المدير

📞 <b>للاستفسار:</b> @{SUPPORT_USERNAME}
"""
                await self.send_notification(target_id, notify_message, context)
            
            await update.message.reply_text(
                f"✅ <b>تم الخصم بنجاح!</b>\n\n"
                f"👤 <b>المستخدم:</b> {target_id}\n"
                f"💸 <b>المبلغ:</b> {amount:,} دينار\n"
                f"💳 <b>الرصيد الجديد:</b> {user_data.get('balance', 0):,} دينار",
                parse_mode=ParseMode.HTML
            )
        
        for key in ['admin_action', 'charge_target', 'charge_target_name', 'charge_target_balance']:
            if key in context.user_data:
                del context.user_data[key]
        
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    async def handle_admin_questions(self, query):
        active_questions = self.questions_manager.get_active_questions()
        total_questions = len(self.questions_manager.questions)
        
        keyboard = [
            [InlineKeyboardButton("❓ عرض الأسئلة النشطة", callback_data="admin_active_questions")],
            [InlineKeyboardButton("🗑️ إزالة الأسئلة القديمة", callback_data="admin_remove_old_questions")],
            [InlineKeyboardButton("📊 إحصائيات الأسئلة", callback_data="admin_questions_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            f"❓ <b>إدارة الأسئلة</b>\n\n"
            f"📊 <b>الإحصائيات:</b>\n"
            f"• ❓ الأسئلة النشطة: {len(active_questions)}\n"
            f"• 📂 إجمالي الأسئلة: {total_questions}\n"
            f"• 🎯 مكافأة الإجابة: {self.settings_manager.admin_settings.get('answer_reward', 100)} نقطة\n\n"
            f"اختر الإجراء:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_admin_settings(self, query):
        keyboard = [
            [InlineKeyboardButton("📢 تغيير رابط القناة", callback_data="admin_change_channel")],
            [InlineKeyboardButton("💰 تغيير أسعار الخدمات", callback_data="admin_change_prices")],
            [InlineKeyboardButton("🎁 تغيير الهدية الترحيبية", callback_data="admin_change_welcome_bonus")],
            [InlineKeyboardButton("👥 تغيير مكافأة الدعوة", callback_data="admin_change_referral_bonus")],
            [InlineKeyboardButton("💬 تغيير مكافأة الإجابة", callback_data="admin_change_answer_reward")],
            [InlineKeyboardButton("💾 إنشاء نسخة احتياطية", callback_data="admin_backup_data")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            "⚙️ <b>إعدادات البوت</b>\n\n"
            "اختر الإجراء المطلوب:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_admin_change_channel(self, query, context: ContextTypes.DEFAULT_TYPE):
        current_link = self.settings_manager.get_channel_link()
        
        await query.edit_message_text(
            "📢 <b>تغيير رابط قناة البوت</b>\n\n"
            f"🔗 <b>الرابط الحالي:</b> {current_link}\n\n"
            "🔗 <b>أرسل الرابط الجديد:</b>\n"
            "• يجب أن يبدأ بـ https://t.me/\n"
            "• مثال: https://t.me/FCJCV\n\n"
            "❌ للإلغاء: /cancel",
            parse_mode=ParseMode.HTML
        )
        return CHANGE_CHANNEL
    
    async def handle_change_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        new_link = update.message.text.strip()
        
        if not new_link.startswith("https://t.me/"):
            await update.message.reply_text(
                "❌ <b>رابط غير صحيح!</b>\n\n"
                "يجب أن يبدأ الرابط بـ: https://t.me/\n"
                "أعد إرسال الرابط الصحيح:",
                parse_mode=ParseMode.HTML
            )
            return CHANGE_CHANNEL
        
        self.settings_manager.update_channel_link(new_link)
        
        await update.message.reply_text(
            f"✅ <b>تم تغيير رابط القناة بنجاح!</b>\n\n"
            f"📢 <b>الرابط الجديد:</b> {new_link}\n\n"
            f"سيظهر الرابط الجديد في واجهة المستخدم مباشرة.",
            parse_mode=ParseMode.HTML
        )
        
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    async def handle_balance_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_data = self.user_manager.get_user(user_id)
        
        balance_text = f"""
💰 <b>رصيدك الحالي:</b> {user_data['balance']:,} دينار

🆔 <b>رقم حسابك:</b> <code>{user_id}</code>

📊 <b>آخر المعاملات:</b>
"""
        
        transactions = user_data.get('transactions', [])[-5:]
        if transactions:
            for trans in transactions:
                sign = "+" if trans['amount'] > 0 else ""
                date = trans['date'].split()[0]
                description = trans['description'][:30]
                balance_text += f"\n📅 {date}: {sign}{trans['amount']:,} - {description}"
        else:
            balance_text += "\n📭 لا توجد معاملات سابقة"
        
        balance_text += f"\n\n💵 <b>إجمالي الإنفاق:</b> {user_data.get('total_spent', 0):,} دينار"
        balance_text += f"\n💎 <b>إجمالي الأرباح:</b> {user_data.get('total_earned', 0):,} دينار"
        
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
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        user_data = self.user_manager.get_user(user.id)
        
        welcome_message = f"""
🎓 <b>مرحباً بعودتك {user.first_name}!</b>

🆔 <b>رقم حسابك:</b> <code>{user.id}</code>
💰 <b>رصيدك الحالي:</b> {user_data['balance']:,} دينار

اختر الخدمة:
"""
        
        keyboard = []
        active_services = self.settings_manager.get_active_services()
        
        service_buttons = {
            "exemption": ("🧮 حساب درجة الإعفاء", "service_exemption"),
            "summarize": ("📚 تلخيص الملازم", "service_summarize"),
            "qa": ("❓ سؤال وجواب بالذكاء", "service_qa"),
            "materials": ("📖 ملازمي ومرشحاتي", "service_materials"),
            "help_student": ("🤝 ساعدوني طلاب", "service_help_student")
        }
        
        row = []
        for service, (text, callback) in service_buttons.items():
            if service in active_services:
                price = self.settings_manager.get_price(service)
                button_text = f"{text} ({price:,} د)"
                row.append(InlineKeyboardButton(button_text, callback_data=callback))
                
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("👑 محاضرات VIP", callback_data="vip_lectures_store")])
        
        keyboard.append([
            InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
            InlineKeyboardButton("📊 إحصائياتي", callback_data="stats"),
            InlineKeyboardButton("❓ أسئلة الطلاب", callback_data="student_questions")
        ])
        
        keyboard.append([
            InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite"),
            InlineKeyboardButton("📢 قناة البوت", url=self.settings_manager.get_channel_link())
        ])
        
        keyboard.append([
            InlineKeyboardButton("👑 اشتراك VIP", callback_data="vip_subscription_info"),
            InlineKeyboardButton("🆘 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME}")
        ])
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        self.user_manager.update_user_info(user.id, user.first_name, user.username)
        
        if update.message.document and context.user_data.get('awaiting_pdf'):
            await self.handle_summarize_pdf(update, context)
        
        elif update.message.text:
            text = update.message.text
            
            if context.user_data.get('awaiting_question'):
                await self.handle_qa_question(update, context)
            
            elif context.user_data.get('awaiting_help_question'):
                await self.handle_help_student_question(update, context)
            
            elif text.replace('.', '', 1).isdigit() or (text.count(' ') >= 2 and all(part.replace('.', '', 1).isdigit() for part in text.split()[:3])):
                await self.handle_exemption_calculation(update, context)
            
            elif context.user_data.get('admin_action'):
                action = context.user_data.get('admin_action')
                
                if action in ['charge_user', 'deduct_user']:
                    await self.handle_charge_user_id(update, context)
                
                elif action == 'change_channel':
                    await self.handle_change_channel(update, context)
            
            else:
                await update.message.reply_text(
                    "🤖 <b>استخدم الأزرار للتفاعل مع البوت</b>\n\n"
                    "📝 اكتب /start لعرض القائمة الرئيسية",
                    parse_mode=ParseMode.HTML
                )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"❌ تحديث {update} تسبب في خطأ {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ <b>حدث خطأ غير متوقع</b>\n\n"
                    f"🆘 تواصل مع الدعم الفني: @{SUPPORT_USERNAME}",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return ConversationHandler.END
        
        await update.message.reply_text("❌ <b>تم إلغاء العملية</b>", parse_mode=ParseMode.HTML)
        await self.admin_panel(update, context)
        return ConversationHandler.END
    
    def run(self):
        print("=" * 60)
        print("🤖 بوت 'يلا نتعلم' التعليمي - الإصدار الكامل")
        print("=" * 60)
        print(f"👑 المدير: {ADMIN_ID}")
        print(f"🆘 الدعم: @{SUPPORT_USERNAME}")
        print(f"📢 القناة: {self.settings_manager.get_channel_link()}")
        print(f"💎 الهدية الترحيبية: {self.settings_manager.get_welcome_bonus():,} دينار")
        print(f"👑 سعر VIP: {self.vip_manager.get_subscription_price():,} دينار شهرياً")
        print(f"🤖 الذكاء الاصطناعي: Gemini 2.0 Flash")
        print("=" * 60)
        print("✅ البوت يعمل الآن...")
        
        app = Application.builder().token(TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start),
                CommandHandler("admin", self.admin_panel),
                CallbackQueryHandler(self.handle_callback)
            ],
            states={
                # نظام الإعفاء
                EXEMPTION_COURSE1: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_exemption_course1),
                    CallbackQueryHandler(self.handle_callback)
                ],
                EXEMPTION_COURSE2: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_exemption_course2),
                    CallbackQueryHandler(self.handle_callback)
                ],
                EXEMPTION_COURSE3: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_exemption_course3),
                    CallbackQueryHandler(self.handle_callback)
                ],
                
                # تلخيص الملازم
                SUMMARIZE_PDF: [
                    MessageHandler(filters.Document.PDF | filters.TEXT & ~filters.COMMAND, self.handle_summarize_pdf),
                    CallbackQueryHandler(self.handle_callback)
                ],
                
                # سؤال وجواب بالذكاء
                QA_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_qa_question),
                    CallbackQueryHandler(self.handle_callback)
                ],
                
                # ساعدوني طلاب
                HELP_STUDENT_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_help_student_question),
                    CallbackQueryHandler(self.handle_callback)
                ],
                
                # لوحة التحكم
                CHARGE_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_charge_user_id),
                    CallbackQueryHandler(self.handle_callback)
                ],
                CHARGE_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_charge_amount),
                    CallbackQueryHandler(self.handle_callback)
                ],
                CHANGE_PRICE_SERVICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_change_price_amount),
                    CallbackQueryHandler(self.handle_callback)
                ],
                CHANGE_CHANNEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_change_channel),
                    CallbackQueryHandler(self.handle_callback)
                ],
                
                # المواد التعليمية
                MATERIAL_FILE: [
                    MessageHandler(filters.Document.PDF | filters.TEXT & ~filters.COMMAND, self.handle_material_file),
                    CallbackQueryHandler(self.handle_callback)
                ],
                MATERIAL_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_material_desc),
                    CallbackQueryHandler(self.handle_callback)
                ],
                MATERIAL_STAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_material_stage),
                    CallbackQueryHandler(self.handle_callback)
                ],
                
                # نظام VIP
                VIP_LECTURE_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_vip_lecture_title),
                    CallbackQueryHandler(self.handle_callback)
                ],
                VIP_LECTURE_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_vip_lecture_desc),
                    CallbackQueryHandler(self.handle_callback)
                ],
                VIP_LECTURE_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_vip_lecture_price),
                    CallbackQueryHandler(self.handle_callback)
                ],
                VIP_LECTURE_FILE: [
                    MessageHandler(filters.Document.ALL | filters.VIDEO | filters.TEXT & ~filters.COMMAND, self.handle_vip_lecture_file),
                    CallbackQueryHandler(self.handle_callback)
                ],
                VIP_CHANGE_SUBSCRIPTION_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_vip_subscription_price_change),
                    CallbackQueryHandler(self.handle_callback)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CommandHandler("start", self.start),
                CallbackQueryHandler(self.handle_callback, pattern="^back_home$|^admin_panel$")
            ]
        )
        
        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(MessageHandler(filters.Document.PDF, self.handle_summarize_pdf))
        app.add_error_handler(self.error_handler)
        
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# ============= تشغيل البوت =============
if __name__ == "__main__":
    bot = YallaNataalamBot()
    bot.run()
