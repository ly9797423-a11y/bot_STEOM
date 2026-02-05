#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت يلا نتعلم - بوت تعليمي متكامل للطلاب العراقيين
مطور بواسطة: Allawi04@
إصدار: 3.0 - كامل المميزات
"""

import logging
import sqlite3
import json
import os
import datetime
import asyncio
import pdfplumber
import arabic_reshaper
import random
import hashlib
import time
import io
import uuid
import threading
import csv
from typing import Dict, List, Tuple, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
import re
import math
from decimal import Decimal
import base64
import mimetypes

from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InputFile, InputMediaPhoto, InputMediaDocument,
    MenuButtonCommands, MenuButtonDefault,
    ChatPermissions, ChatMember
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler, PicklePersistence, JobQueue,
    ExtBot, CallbackContext
)
from telegram.constants import ParseMode, ChatAction, ChatType
from telegram.error import TelegramError, BadRequest, NetworkError
import pytz
from dateutil import parser, relativedelta
from cachetools import TTLCache, LRUCache
import aiohttp
import async_timeout
from io import BytesIO
import qrcode
from babel.dates import format_date, format_datetime, format_time
import html

# ============== إعدادات البوت الأساسية ==============
TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_USERNAME = "@FC4Xbot"
ADMIN_ID = 6130994941
ADMIN_USERNAME = "Allawi04@"
BOT_CHANNEL = "https://t.me/FCJCV"
CHANNEL_USERNAME = "@FCJCV"
SUPPORT_USERNAME = "Allawi04@"
GEMINI_API_KEY = "AIzaSyARsl_YMXA74bPQpJduu0jJVuaku7MaHuY"
BOT_VERSION = "3.0.0"
CREATOR = "Allawi04@"

# ============== الثوابت والإعدادات ==============
class ServiceType(Enum):
    EXEMPTION_CALC = "exemption_calc"
    PDF_SUMMARY = "pdf_summary"
    AI_QA = "ai_qa"
    HELP_STUDENT = "help_student"
    VIP_LECTURES = "vip_lectures"
    STUDY_MATERIALS = "study_materials"
    QUIZ_GENERATOR = "quiz_generator"
    EXAM_PREP = "exam_prep"
    GRADE_CONVERTER = "grade_converter"

class UserRole(Enum):
    USER = "user"
    VIP = "vip"
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PURCHASE = "purchase"
    REFUND = "refund"
    BONUS = "bonus"
    REFERRAL = "referral"
    PRIZE = "prize"

# ============== هياكل البيانات ==============
@dataclass
class UserProfile:
    user_id: int
    username: str
    first_name: str
    last_name: str
    balance: int
    points: int
    level: int
    experience: int
    role: str
    join_date: datetime.datetime
    last_active: datetime.datetime
    settings: Dict[str, Any]
    achievements: List[str]
    badges: List[str]

@dataclass
class Lecture:
    lecture_id: int
    teacher_id: int
    title: str
    description: str
    video_file_id: str
    thumbnail_file_id: Optional[str]
    price: int
    category: str
    subject: str
    grade_level: str
    duration: int  # بالثواني
    views: int
    purchases: int
    rating: float
    rating_count: int
    is_approved: bool
    is_featured: bool
    upload_date: datetime.datetime
    tags: List[str]
    requirements: List[str]
    learning_outcomes: List[str]

@dataclass
class Question:
    question_id: int
    user_id: int
    question_text: str
    subject: str
    grade: str
    price: int
    attachment_file_id: Optional[str]
    is_answered: bool
    answer_user_id: Optional[int]
    answer_text: Optional[str]
    answer_date: Optional[datetime.datetime]
    is_approved: bool
    question_date: datetime.datetime
    views: int
    upvotes: int
    downvotes: int

# ============== إعدادات التسجيل ==============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== إعدادات الذاكرة المؤقتة ==============
cache = TTLCache(maxsize=1000, ttl=300)
user_cache = TTLCache(maxsize=500, ttl=60)

# ============== تهيئة الذكاء الاصطناعي ==============
genai.configure(api_key=GEMINI_API_KEY)
ai_models = {
    'default': genai.GenerativeModel('gemini-pro'),
    'vision': genai.GenerativeModel('gemini-pro-vision'),
    'advanced': genai.GenerativeModel('gemini-1.5-pro')
}

# ============== إعدادات قاعدة البيانات المتقدمة ==============
class AdvancedDatabase:
    """فئة متقدمة لإدارة قاعدة البيانات مع نسخ احتياطي وتشفير"""
    
    def __init__(self, db_name="database.db", backup_interval=3600):
        self.db_name = db_name
        self.backup_interval = backup_interval
        self.conn = self._create_connection()
        self._init_database()
        self._start_backup_scheduler()
    
    def _create_connection(self):
        """إنشاء اتصال بقاعدة البيانات مع إعدادات متقدمة"""
        conn = sqlite3.connect(
            self.db_name,
            check_same_thread=False,
            timeout=30,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def _init_database(self):
        """تهيئة جميع الجداول بشكل متقدم"""
        cursor = self.conn.cursor()
        
        # جدول المستخدمين الموسع
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                phone_number TEXT,
                email TEXT,
                balance INTEGER DEFAULT 0 CHECK(balance >= 0),
                points INTEGER DEFAULT 0,
                experience INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                role TEXT DEFAULT 'user' CHECK(role IN ('user', 'vip', 'teacher', 'admin', 'super_admin')),
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_referred INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0 CHECK(is_banned IN (0, 1)),
                ban_reason TEXT,
                ban_until TIMESTAMP,
                is_premium INTEGER DEFAULT 0,
                premium_until TIMESTAMP,
                settings TEXT DEFAULT '{}',
                achievements TEXT DEFAULT '[]',
                badges TEXT DEFAULT '[]',
                daily_streak INTEGER DEFAULT 0,
                last_daily_reward TIMESTAMP,
                total_spent INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                session_count INTEGER DEFAULT 0,
                avg_session_time INTEGER DEFAULT 0,
                favorite_subjects TEXT DEFAULT '[]',
                notification_count INTEGER DEFAULT 0,
                security_code TEXT,
                two_factor_enabled INTEGER DEFAULT 0,
                last_password_change TIMESTAMP,
                account_status TEXT DEFAULT 'active' CHECK(account_status IN ('active', 'suspended', 'deleted', 'inactive')),
                profile_image TEXT,
                bio TEXT,
                education_level TEXT,
                specialization TEXT,
                institute TEXT,
                year_of_study INTEGER,
                gender TEXT,
                birth_date DATE,
                country TEXT DEFAULT 'Iraq',
                city TEXT,
                language TEXT DEFAULT 'ar',
                timezone TEXT DEFAULT 'Asia/Baghdad',
                theme TEXT DEFAULT 'light',
                font_size INTEGER DEFAULT 14,
                auto_renew_vip INTEGER DEFAULT 0,
                email_verified INTEGER DEFAULT 0,
                phone_verified INTEGER DEFAULT 0,
                kyc_status TEXT DEFAULT 'pending' CHECK(kyc_status IN ('pending', 'verified', 'rejected')),
                kyc_document TEXT,
                kyc_verified_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الفروع (للمستخدمين المتعددين)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_branches (
                branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                branch_name TEXT NOT NULL,
                branch_balance INTEGER DEFAULT 0,
                branch_manager INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (branch_manager) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول خدمات VIP المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL CHECK(plan_type IN ('monthly', 'quarterly', 'semiannual', 'annual', 'lifetime')),
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                auto_renew INTEGER DEFAULT 0 CHECK(auto_renew IN (0, 1)),
                renewal_count INTEGER DEFAULT 0,
                total_paid INTEGER DEFAULT 0,
                last_renewal_date TIMESTAMP,
                next_renewal_date TIMESTAMP,
                payment_method TEXT,
                transaction_id TEXT,
                features TEXT DEFAULT '{}',
                limitations TEXT DEFAULT '{}',
                discount_applied REAL DEFAULT 0,
                tax_amount INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول محاضرات VIP المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_lectures (
                lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT,
                description TEXT,
                long_description TEXT,
                video_file_id TEXT NOT NULL,
                thumbnail_file_id TEXT,
                preview_file_id TEXT,
                price INTEGER NOT NULL CHECK(price >= 0),
                discount_price INTEGER,
                category TEXT NOT NULL,
                subcategory TEXT,
                subject TEXT NOT NULL,
                grade_level TEXT,
                duration INTEGER, -- بالثواني
                file_size INTEGER,
                video_quality TEXT CHECK(video_quality IN ('360p', '480p', '720p', '1080p', '2k', '4k')),
                video_format TEXT,
                views INTEGER DEFAULT 0,
                unique_views INTEGER DEFAULT 0,
                purchases INTEGER DEFAULT 0,
                rating REAL DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
                rating_count INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 0 CHECK(is_approved IN (0, 1)),
                is_featured INTEGER DEFAULT 0,
                is_draft INTEGER DEFAULT 0,
                approval_date TIMESTAMP,
                featured_date TIMESTAMP,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT DEFAULT '[]',
                requirements TEXT DEFAULT '[]',
                learning_outcomes TEXT DEFAULT '[]',
                resources TEXT DEFAULT '[]',
                related_lectures TEXT DEFAULT '[]',
                seo_title TEXT,
                seo_description TEXT,
                seo_keywords TEXT,
                access_type TEXT DEFAULT 'public' CHECK(access_type IN ('public', 'private', 'unlisted')),
                password TEXT,
                max_downloads INTEGER,
                download_count INTEGER DEFAULT 0,
                completion_certificate INTEGER DEFAULT 0,
                certificate_template TEXT,
                min_score_for_certificate INTEGER DEFAULT 70,
                includes_quiz INTEGER DEFAULT 0,
                quiz_id INTEGER,
                includes_assignment INTEGER DEFAULT 0,
                assignment_id INTEGER,
                discussion_enabled INTEGER DEFAULT 1,
                comments_count INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                delete_reason TEXT,
                restore_code TEXT,
                FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES lecture_quizzes(quiz_id) ON DELETE SET NULL,
                FOREIGN KEY (assignment_id) REFERENCES lecture_assignments(assignment_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول تقييمات المحاضرات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecture_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                title TEXT,
                review TEXT,
                is_helpful INTEGER,
                helpful_count INTEGER DEFAULT 0,
                not_helpful_count INTEGER DEFAULT 0,
                is_verified_purchase INTEGER DEFAULT 0,
                is_edited INTEGER DEFAULT 0,
                edit_history TEXT DEFAULT '[]',
                status TEXT DEFAULT 'approved' CHECK(status IN ('pending', 'approved', 'rejected', 'flagged')),
                flagged_reason TEXT,
                moderated_by INTEGER,
                moderation_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lecture_id, user_id),
                FOREIGN KEY (lecture_id) REFERENCES vip_lectures(lecture_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (moderated_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول مشتريات المحاضرات المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecture_purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lecture_id INTEGER NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amount_paid INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                discount_applied REAL DEFAULT 0,
                tax_amount INTEGER DEFAULT 0,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'completed' CHECK(payment_status IN ('pending', 'completed', 'failed', 'refunded')),
                transaction_id TEXT UNIQUE,
                invoice_number TEXT UNIQUE,
                is_gift INTEGER DEFAULT 0,
                gift_to_user_id INTEGER,
                gift_message TEXT,
                viewed INTEGER DEFAULT 0,
                last_viewed TIMESTAMP,
                completion_percentage REAL DEFAULT 0,
                completed INTEGER DEFAULT 0,
                completion_date TIMESTAMP,
                certificate_issued INTEGER DEFAULT 0,
                certificate_id TEXT,
                certificate_issue_date TIMESTAMP,
                rating_given INTEGER DEFAULT 0,
                review_given INTEGER DEFAULT 0,
                refund_requested INTEGER DEFAULT 0,
                refund_reason TEXT,
                refund_status TEXT,
                refund_amount INTEGER,
                refund_date TIMESTAMP,
                notes TEXT,
                device_info TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (lecture_id) REFERENCES vip_lectures(lecture_id) ON DELETE CASCADE,
                FOREIGN KEY (gift_to_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول أرباح المدرسين المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_earnings (
                earning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                lecture_id INTEGER,
                purchase_id INTEGER,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                commission_rate REAL DEFAULT 60.0,
                tax_amount INTEGER DEFAULT 0,
                net_amount INTEGER NOT NULL,
                earning_type TEXT DEFAULT 'lecture_sale' CHECK(earning_type IN ('lecture_sale', 'subscription', 'referral', 'bonus', 'refund')),
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'available', 'withdrawn', 'cancelled')),
                period_start DATE,
                period_end DATE,
                is_paid INTEGER DEFAULT 0,
                payment_date TIMESTAMP,
                payment_method TEXT,
                payment_reference TEXT,
                withdrawal_request_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (lecture_id) REFERENCES vip_lectures(lecture_id) ON DELETE SET NULL,
                FOREIGN KEY (purchase_id) REFERENCES lecture_purchases(purchase_id) ON DELETE SET NULL,
                FOREIGN KEY (withdrawal_request_id) REFERENCES withdrawal_requests(request_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول طلبات سحب الأرباح
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'processing', 'completed', 'rejected', 'cancelled')),
                processed_date TIMESTAMP,
                processed_by INTEGER,
                payment_method TEXT NOT NULL,
                payment_details TEXT,
                admin_notes TEXT,
                user_notes TEXT,
                receipt_file_id TEXT,
                transaction_fee INTEGER DEFAULT 0,
                net_amount INTEGER,
                bank_name TEXT,
                account_name TEXT,
                account_number TEXT,
                iban TEXT,
                swift_code TEXT,
                mobile_wallet TEXT,
                wallet_number TEXT,
                is_urgent INTEGER DEFAULT 0,
                priority_level TEXT DEFAULT 'normal' CHECK(priority_level IN ('low', 'normal', 'high', 'urgent')),
                reminder_sent INTEGER DEFAULT 0,
                last_reminder_date TIMESTAMP,
                auto_approve INTEGER DEFAULT 0,
                approved_date TIMESTAMP,
                rejection_reason TEXT,
                cancelled_reason TEXT,
                completed_date TIMESTAMP,
                verification_code TEXT,
                is_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (processed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الأسئلة والأجوبة المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'text' CHECK(question_type IN ('text', 'image', 'document', 'voice', 'video')),
                subject TEXT NOT NULL,
                grade TEXT,
                topic TEXT,
                difficulty TEXT DEFAULT 'medium' CHECK(difficulty IN ('easy', 'medium', 'hard', 'expert')),
                price INTEGER NOT NULL CHECK(price >= 0),
                attachment_file_id TEXT,
                attachment_type TEXT,
                is_answered INTEGER DEFAULT 0 CHECK(is_answered IN (0, 1)),
                answer_user_id INTEGER,
                answer_text TEXT,
                answer_type TEXT,
                answer_attachment_file_id TEXT,
                answer_date TIMESTAMP,
                is_approved INTEGER DEFAULT 0,
                approved_by INTEGER,
                approval_date TIMESTAMP,
                rejection_reason TEXT,
                views INTEGER DEFAULT 0,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                report_count INTEGER DEFAULT 0,
                is_closed INTEGER DEFAULT 0,
                closed_reason TEXT,
                closed_by INTEGER,
                closed_date TIMESTAMP,
                bounty_amount INTEGER DEFAULT 0,
                bounty_expiry TIMESTAMP,
                tags TEXT DEFAULT '[]',
                language TEXT DEFAULT 'ar',
                is_anonymous INTEGER DEFAULT 0,
                anonymous_id TEXT,
                editing_history TEXT DEFAULT '[]',
                last_edited TIMESTAMP,
                is_featured INTEGER DEFAULT 0,
                featured_date TIMESTAMP,
                is_urgent INTEGER DEFAULT 0,
                urgency_level TEXT,
                estimated_time TEXT,
                actual_time_taken INTEGER,
                satisfaction_rating INTEGER CHECK(satisfaction_rating >= 1 AND satisfaction_rating <= 5),
                feedback TEXT,
                is_deleted INTEGER DEFAULT 0,
                deleted_by INTEGER,
                deleted_at TIMESTAMP,
                restore_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (answer_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (closed_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (deleted_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول التصويت على الأسئلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_votes (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote_type TEXT CHECK(vote_type IN ('upvote', 'downvote')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(question_id, user_id),
                FOREIGN KEY (question_id) REFERENCES student_questions(question_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول المواد الدراسية المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_materials (
                material_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                detailed_description TEXT,
                grade TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                file_id TEXT NOT NULL,
                file_type TEXT CHECK(file_type IN ('pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'image', 'video', 'audio', 'zip')),
                file_size INTEGER,
                page_count INTEGER,
                language TEXT DEFAULT 'ar',
                author TEXT,
                publisher TEXT,
                publication_year INTEGER,
                edition TEXT,
                isbn TEXT,
                license_type TEXT,
                download_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                is_featured INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                price INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 1,
                approved_by INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT DEFAULT '[]',
                related_materials TEXT DEFAULT '[]',
                prerequisites TEXT DEFAULT '[]',
                learning_objectives TEXT DEFAULT '[]',
                target_audience TEXT,
                duration_minutes INTEGER,
                difficulty_level TEXT CHECK(difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
                is_interactive INTEGER DEFAULT 0,
                interactive_elements TEXT DEFAULT '[]',
                accessibility_features TEXT DEFAULT '[]',
                seo_title TEXT,
                seo_description TEXT,
                seo_keywords TEXT,
                thumbnail_file_id TEXT,
                preview_file_id TEXT,
                sample_pages TEXT DEFAULT '[]',
                version TEXT DEFAULT '1.0',
                changelog TEXT,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                delete_reason TEXT,
                restore_code TEXT,
                FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول المعاملات المالية المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                type TEXT NOT NULL CHECK(type IN ('deposit', 'withdrawal', 'purchase', 'refund', 'bonus', 'referral', 'prize', 'commission', 'fee', 'transfer')),
                description TEXT NOT NULL,
                status TEXT DEFAULT 'completed' CHECK(status IN ('pending', 'completed', 'failed', 'cancelled', 'reversed')),
                reference_id TEXT,
                invoice_number TEXT UNIQUE,
                payment_method TEXT,
                payment_gateway TEXT,
                gateway_transaction_id TEXT,
                gateway_response TEXT,
                tax_amount INTEGER DEFAULT 0,
                fee_amount INTEGER DEFAULT 0,
                net_amount INTEGER,
                balance_before INTEGER,
                balance_after INTEGER,
                related_user_id INTEGER,
                related_item_id INTEGER,
                item_type TEXT,
                notes TEXT,
                metadata TEXT DEFAULT '{}',
                device_info TEXT,
                ip_address TEXT,
                user_agent TEXT,
                receipt_file_id TEXT,
                verified_by INTEGER,
                verification_date TIMESTAMP,
                is_reconciled INTEGER DEFAULT 0,
                reconciled_date TIMESTAMP,
                reconciliation_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (related_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول التقييمات المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_type TEXT NOT NULL CHECK(item_type IN ('lecture', 'material', 'question', 'answer', 'teacher', 'service')),
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                title TEXT,
                comment TEXT,
                is_anonymous INTEGER DEFAULT 0,
                is_verified_purchase INTEGER DEFAULT 0,
                is_edited INTEGER DEFAULT 0,
                edit_history TEXT DEFAULT '[]',
                helpful_count INTEGER DEFAULT 0,
                not_helpful_count INTEGER DEFAULT 0,
                report_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'approved' CHECK(status IN ('pending', 'approved', 'rejected', 'hidden')),
                moderated_by INTEGER,
                moderation_date TIMESTAMP,
                moderation_notes TEXT,
                tags TEXT DEFAULT '[]',
                sentiment_score REAL,
                aspect_ratings TEXT DEFAULT '{}',
                recommendation INTEGER CHECK(recommendation IN (0, 1)),
                would_purchase_again INTEGER CHECK(would_purchase_again IN (0, 1)),
                value_for_money INTEGER CHECK(value_for_money >= 1 AND value_for_money <= 5),
                difficulty_level INTEGER CHECK(difficulty_level >= 1 AND difficulty_level <= 5),
                clarity_rating INTEGER CHECK(clarity_rating >= 1 AND clarity_rating <= 5),
                engagement_rating INTEGER CHECK(engagement_rating >= 1 AND engagement_rating <= 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (moderated_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الإنجازات المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                achievement_level TEXT DEFAULT 'bronze' CHECK(achievement_level IN ('bronze', 'silver', 'gold', 'platinum', 'diamond')),
                points_awarded INTEGER DEFAULT 0,
                xp_awarded INTEGER DEFAULT 0,
                badge_awarded TEXT,
                title_awarded TEXT,
                unlocked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress_current INTEGER DEFAULT 0,
                progress_target INTEGER DEFAULT 1,
                is_secret INTEGER DEFAULT 0,
                is_hidden INTEGER DEFAULT 0,
                display_order INTEGER,
                category TEXT,
                subcategory TEXT,
                difficulty TEXT DEFAULT 'easy' CHECK(difficulty IN ('easy', 'medium', 'hard', 'legendary')),
                rarity TEXT DEFAULT 'common' CHECK(rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic')),
                description TEXT,
                lore_text TEXT,
                icon_file_id TEXT,
                notification_sent INTEGER DEFAULT 0,
                shared_socially INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                reset_on_fail INTEGER DEFAULT 0,
                time_limit_days INTEGER,
                completed_date TIMESTAMP,
                expires_date TIMESTAMP,
                prerequisites TEXT DEFAULT '[]',
                rewards TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                version TEXT DEFAULT '1.0',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الإشعارات المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL CHECK(notification_type IN ('system', 'transaction', 'social', 'reminder', 'promotional', 'security', 'achievement', 'update')),
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT DEFAULT '{}',
                priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
                is_read INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
                is_archived INTEGER DEFAULT 0 CHECK(is_archived IN (0, 1)),
                read_date TIMESTAMP,
                action_url TEXT,
                action_text TEXT,
                action_data TEXT,
                icon_type TEXT CHECK(icon_type IN ('info', 'success', 'warning', 'error', 'gift', 'star', 'heart', 'bell', 'message', 'money')),
                icon_file_id TEXT,
                sender_id INTEGER,
                related_item_id INTEGER,
                related_item_type TEXT,
                scheduled_for TIMESTAMP,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 0,
                delivery_method TEXT DEFAULT 'in_app' CHECK(delivery_method IN ('in_app', 'email', 'sms', 'push')),
                delivery_status TEXT DEFAULT 'pending' CHECK(delivery_status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')),
                delivery_attempts INTEGER DEFAULT 0,
                last_delivery_attempt TIMESTAMP,
                delivery_error TEXT,
                expires_at TIMESTAMP,
                click_count INTEGER DEFAULT 0,
                last_clicked TIMESTAMP,
                conversion INTEGER DEFAULT 0,
                conversion_data TEXT,
                campaign_id TEXT,
                segment_id TEXT,
                a_b_test_group TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الإحصائيات اليومية المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date DATE NOT NULL UNIQUE,
                period_type TEXT DEFAULT 'daily' CHECK(period_type IN ('daily', 'weekly', 'monthly', 'yearly')),
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                returning_users INTEGER DEFAULT 0,
                churned_users INTEGER DEFAULT 0,
                vip_users INTEGER DEFAULT 0,
                teachers_count INTEGER DEFAULT 0,
                admins_count INTEGER DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                avg_session_duration INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                total_commands INTEGER DEFAULT 0,
                total_interactions INTEGER DEFAULT 0,
                total_income INTEGER DEFAULT 0,
                total_expenses INTEGER DEFAULT 0,
                net_profit INTEGER DEFAULT 0,
                total_deposits INTEGER DEFAULT 0,
                total_withdrawals INTEGER DEFAULT 0,
                total_purchases INTEGER DEFAULT 0,
                total_refunds INTEGER DEFAULT 0,
                avg_transaction_value INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0,
                vip_sales INTEGER DEFAULT 0,
                lecture_sales INTEGER DEFAULT 0,
                material_downloads INTEGER DEFAULT 0,
                questions_asked INTEGER DEFAULT 0,
                questions_answered INTEGER DEFAULT 0,
                ai_requests INTEGER DEFAULT 0,
                pdf_summaries INTEGER DEFAULT 0,
                exemption_calculations INTEGER DEFAULT 0,
                server_uptime REAL DEFAULT 100.0,
                error_count INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                cache_hit_rate REAL DEFAULT 0,
                memory_usage_mb REAL DEFAULT 0,
                cpu_usage_percent REAL DEFAULT 0,
                disk_usage_percent REAL DEFAULT 0,
                network_traffic_mb REAL DEFAULT 0,
                backup_size_mb REAL DEFAULT 0,
                security_scans INTEGER DEFAULT 0,
                security_issues INTEGER DEFAULT 0,
                user_satisfaction_score REAL DEFAULT 0,
                user_retention_rate REAL DEFAULT 0,
                referral_signups INTEGER DEFAULT 0,
                social_shares INTEGER DEFAULT 0,
                feedback_received INTEGER DEFAULT 0,
                support_tickets INTEGER DEFAULT 0,
                ticket_resolution_time INTEGER DEFAULT 0,
                revenue_per_user INTEGER DEFAULT 0,
                lifetime_value INTEGER DEFAULT 0,
                acquisition_cost INTEGER DEFAULT 0,
                roi_percent REAL DEFAULT 0,
                top_performing_lectures TEXT DEFAULT '[]',
                top_performing_teachers TEXT DEFAULT '[]',
                most_active_users TEXT DEFAULT '[]',
                most_popular_subjects TEXT DEFAULT '[]',
                peak_usage_hours TEXT DEFAULT '[]',
                geographic_distribution TEXT DEFAULT '{}',
                device_distribution TEXT DEFAULT '{}',
                browser_distribution TEXT DEFAULT '{}',
                os_distribution TEXT DEFAULT '{}',
                traffic_sources TEXT DEFAULT '{}',
                campaign_performance TEXT DEFAULT '{}',
                kpi_status TEXT DEFAULT '{}',
                anomalies_detected TEXT DEFAULT '[]',
                recommendations TEXT DEFAULT '[]',
                forecast_data TEXT DEFAULT '{}',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                review_status TEXT DEFAULT 'pending' CHECK(review_status IN ('pending', 'reviewed', 'approved', 'rejected')),
                review_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول إعدادات البوت المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                setting_type TEXT CHECK(setting_type IN ('string', 'integer', 'float', 'boolean', 'json', 'array', 'object')),
                default_value TEXT,
                min_value TEXT,
                max_value TEXT,
                options TEXT DEFAULT '[]',
                description TEXT,
                help_text TEXT,
                is_public INTEGER DEFAULT 0 CHECK(is_public IN (0, 1)),
                is_editable INTEGER DEFAULT 1 CHECK(is_editable IN (0, 1)),
                is_required INTEGER DEFAULT 0 CHECK(is_required IN (0, 1)),
                validation_regex TEXT,
                validation_message TEXT,
                display_order INTEGER DEFAULT 0,
                group_name TEXT,
                subgroup TEXT,
                depends_on TEXT,
                visible_condition TEXT,
                last_modified_by INTEGER,
                last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version TEXT DEFAULT '1.0',
                audit_log TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (last_modified_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول السجلات والتدقيق
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT NOT NULL,
                action_details TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                entity_name TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                device_info TEXT,
                location_info TEXT,
                severity TEXT DEFAULT 'info' CHECK(severity IN ('debug', 'info', 'warning', 'error', 'critical', 'security')),
                status TEXT DEFAULT 'success' CHECK(status IN ('success', 'failure', 'partial')),
                error_message TEXT,
                stack_trace TEXT,
                session_id TEXT,
                request_id TEXT,
                response_time_ms INTEGER,
                resource_usage TEXT DEFAULT '{}',
                affected_users TEXT DEFAULT '[]',
                data_changes TEXT DEFAULT '{}',
                compliance_flags TEXT DEFAULT '[]',
                retention_days INTEGER DEFAULT 365,
                is_archived INTEGER DEFAULT 0 CHECK(is_archived IN (0, 1)),
                archived_date TIMESTAMP,
                archive_reason TEXT,
                reviewed_by INTEGER,
                review_status TEXT DEFAULT 'pending' CHECK(review_status IN ('pending', 'reviewed', 'action_required', 'resolved')),
                review_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الإذاعات والتسويق
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                message_type TEXT DEFAULT 'text' CHECK(message_type IN ('text', 'photo', 'video', 'document', 'audio', 'voice', 'animation', 'sticker', 'poll', 'quiz')),
                media_file_id TEXT,
                thumbnail_file_id TEXT,
                caption TEXT,
                parse_mode TEXT DEFAULT 'Markdown',
                buttons TEXT DEFAULT '[]',
                target_audience TEXT DEFAULT 'all' CHECK(target_audience IN ('all', 'users', 'vip', 'teachers', 'admins', 'inactive', 'new', 'specific')),
                target_user_ids TEXT DEFAULT '[]',
                target_filters TEXT DEFAULT '{}',
                scheduled_for TIMESTAMP,
                sent_at TIMESTAMP,
                status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'scheduled', 'sending', 'sent', 'failed', 'cancelled')),
                sent_count INTEGER DEFAULT 0,
                delivered_count INTEGER DEFAULT 0,
                read_count INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                failure_reasons TEXT DEFAULT '[]',
                cost INTEGER DEFAULT 0,
                budget INTEGER,
                campaign_name TEXT,
                campaign_id TEXT,
                a_b_test_id TEXT,
                variant_name TEXT,
                success_metrics TEXT DEFAULT '{}',
                notes TEXT,
                created_by INTEGER NOT NULL,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                approval_status TEXT DEFAULT 'pending' CHECK(approval_status IN ('pending', 'approved', 'rejected')),
                rejection_reason TEXT,
                is_recurring INTEGER DEFAULT 0 CHECK(is_recurring IN (0, 1)),
                recurrence_pattern TEXT,
                next_recurrence TIMESTAMP,
                recurrence_count INTEGER DEFAULT 0,
                max_recurrences INTEGER,
                stop_condition TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الكوبونات والعروض
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                coupon_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                discount_type TEXT NOT NULL CHECK(discount_type IN ('percentage', 'fixed', 'free_shipping', 'bogo')),
                discount_value INTEGER NOT NULL,
                min_purchase_amount INTEGER DEFAULT 0,
                max_discount_amount INTEGER,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                usage_limit INTEGER,
                per_user_limit INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                is_public INTEGER DEFAULT 1 CHECK(is_public IN (0, 1)),
                applicable_to TEXT DEFAULT 'all' CHECK(applicable_to IN ('all', 'products', 'categories', 'users', 'vip', 'teachers', 'specific')),
                applicable_items TEXT DEFAULT '[]',
                excluded_items TEXT DEFAULT '[]',
                applicable_users TEXT DEFAULT '[]',
                excluded_users TEXT DEFAULT '[]',
                conditions TEXT DEFAULT '{}',
                stackable INTEGER DEFAULT 0 CHECK(stackable IN (0, 1)),
                priority_level INTEGER DEFAULT 0,
                redemption_instructions TEXT,
                terms_and_conditions TEXT,
                banner_image TEXT,
                notification_text TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الاختبارات والامتحانات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT NOT NULL,
                grade TEXT,
                topic TEXT,
                difficulty TEXT DEFAULT 'medium' CHECK(difficulty IN ('easy', 'medium', 'hard', 'expert')),
                question_count INTEGER NOT NULL,
                time_limit_minutes INTEGER,
                passing_score INTEGER DEFAULT 70,
                max_attempts INTEGER DEFAULT 1,
                is_shuffle_questions INTEGER DEFAULT 0,
                is_shuffle_answers INTEGER DEFAULT 0,
                show_correct_answers INTEGER DEFAULT 0,
                show_explanations INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 1,
                is_premium INTEGER DEFAULT 0,
                price INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL,
                approved_by INTEGER,
                is_approved INTEGER DEFAULT 0,
                approval_date TIMESTAMP,
                view_count INTEGER DEFAULT 0,
                attempt_count INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0,
                tags TEXT DEFAULT '[]',
                cover_image TEXT,
                instructions TEXT,
                metadata TEXT DEFAULT '{}',
                is_deleted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول أسئلة الاختبارات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'multiple_choice' CHECK(question_type IN ('multiple_choice', 'true_false', 'short_answer', 'essay', 'matching', 'ordering', 'fill_blank')),
                options TEXT DEFAULT '[]',
                correct_answer TEXT,
                explanation TEXT,
                points INTEGER DEFAULT 1,
                difficulty TEXT DEFAULT 'medium',
                category TEXT,
                subcategory TEXT,
                image_file_id TEXT,
                audio_file_id TEXT,
                video_file_id TEXT,
                hint TEXT,
                time_limit_seconds INTEGER,
                is_required INTEGER DEFAULT 1,
                display_order INTEGER,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول محاولات الاختبار
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                score REAL DEFAULT 0,
                max_score INTEGER,
                percentage REAL DEFAULT 0,
                is_passed INTEGER DEFAULT 0,
                time_taken_seconds INTEGER,
                answers TEXT DEFAULT '{}',
                feedback TEXT,
                reviewed_by INTEGER,
                review_notes TEXT,
                is_cheating_suspected INTEGER DEFAULT 0,
                cheating_reasons TEXT DEFAULT '[]',
                ip_address TEXT,
                user_agent TEXT,
                device_info TEXT,
                session_id TEXT,
                is_completed INTEGER DEFAULT 0,
                completion_status TEXT DEFAULT 'in_progress' CHECK(completion_status IN ('in_progress', 'completed', 'abandoned', 'timed_out', 'submitted')),
                certificate_issued INTEGER DEFAULT 0,
                certificate_id TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
                FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL)
        ''')
        
        # جدول جلسات الدردشة والدعم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                support_user_id INTEGER,
                subject TEXT,
                category TEXT,
                priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
                status TEXT DEFAULT 'open' CHECK(status IN ('open', 'assigned', 'in_progress', 'waiting', 'resolved', 'closed', 'cancelled')),
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                feedback TEXT,
                first_response_time INTEGER,
                resolution_time INTEGER,
                satisfaction_score INTEGER,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                closed_by INTEGER,
                closure_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (support_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (closed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول رسائل الدردشة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message_type TEXT DEFAULT 'text' CHECK(message_type IN ('text', 'image', 'document', 'audio', 'video', 'sticker', 'location', 'contact')),
                message_text TEXT,
                file_id TEXT,
                file_type TEXT,
                file_size INTEGER,
                thumbnail_id TEXT,
                is_read INTEGER DEFAULT 0,
                read_at TIMESTAMP,
                is_edited INTEGER DEFAULT 0,
                edit_history TEXT DEFAULT '[]',
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                deleted_by INTEGER,
                delete_reason TEXT,
                reactions TEXT DEFAULT '{}',
                forwarded_from INTEGER,
                reply_to_message_id INTEGER,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (deleted_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (forwarded_from) REFERENCES chat_messages(message_id) ON DELETE SET NULL,
                FOREIGN KEY (reply_to_message_id) REFERENCES chat_messages(message_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول المهام المجدولة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                task_name TEXT NOT NULL,
                description TEXT,
                schedule_pattern TEXT NOT NULL,
                next_run TIMESTAMP NOT NULL,
                last_run TIMESTAMP,
                last_run_status TEXT CHECK(last_run_status IN ('success', 'failure', 'running')),
                last_run_result TEXT,
                last_run_duration INTEGER,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                max_retries INTEGER DEFAULT 3,
                retry_count INTEGER DEFAULT 0,
                timeout_seconds INTEGER DEFAULT 300,
                priority INTEGER DEFAULT 0,
                parameters TEXT DEFAULT '{}',
                dependencies TEXT DEFAULT '[]',
                on_failure_action TEXT,
                notification_on_failure INTEGER DEFAULT 1,
                notification_on_success INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول تحديثات النظام
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_updates (
                update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                update_type TEXT NOT NULL CHECK(update_type IN ('feature', 'bugfix', 'security', 'performance', 'maintenance')),
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                changelog TEXT,
                release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_mandatory INTEGER DEFAULT 0 CHECK(is_mandatory IN (0, 1)),
                min_version_required TEXT,
                max_version_applicable TEXT,
                affected_modules TEXT DEFAULT '[]',
                rollback_instructions TEXT,
                known_issues TEXT DEFAULT '[]',
                fixed_issues TEXT DEFAULT '[]',
                security_notes TEXT,
                performance_impact TEXT,
                database_changes TEXT,
                api_changes TEXT,
                ui_changes TEXT,
                documentation_url TEXT,
                support_article_url TEXT,
                is_published INTEGER DEFAULT 1 CHECK(is_published IN (0, 1)),
                published_by INTEGER,
                published_at TIMESTAMP,
                download_url TEXT,
                checksum TEXT,
                file_size INTEGER,
                installation_instructions TEXT,
                verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'failed')),
                verified_by INTEGER,
                verified_at TIMESTAMP,
                rollout_percentage INTEGER DEFAULT 100,
                rollout_strategy TEXT,
                feedback_stats TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (published_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول التقارير والإحصائيات المخصصة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_name TEXT NOT NULL,
                report_type TEXT NOT NULL CHECK(report_type IN ('financial', 'user', 'content', 'system', 'marketing', 'custom')),
                description TEXT,
                parameters TEXT DEFAULT '{}',
                filters TEXT DEFAULT '{}',
                columns TEXT DEFAULT '[]',
                grouping TEXT DEFAULT '[]',
                sorting TEXT DEFAULT '[]',
                chart_type TEXT CHECK(chart_type IN ('bar', 'line', 'pie', 'doughnut', 'radar', 'polar', 'bubble', 'scatter', 'area')),
                chart_config TEXT DEFAULT '{}',
                schedule_pattern TEXT,
                last_generated TIMESTAMP,
                generation_status TEXT,
                file_url TEXT,
                file_format TEXT DEFAULT 'pdf' CHECK(file_format IN ('pdf', 'excel', 'csv', 'json', 'html')),
                file_size INTEGER,
                is_public INTEGER DEFAULT 0 CHECK(is_public IN (0, 1)),
                access_level TEXT DEFAULT 'admin' CHECK(access_level IN ('public', 'user', 'vip', 'teacher', 'admin', 'super_admin')),
                authorized_users TEXT DEFAULT '[]',
                is_auto_generated INTEGER DEFAULT 0 CHECK(is_auto_generated IN (0, 1)),
                generation_frequency TEXT,
                next_generation TIMESTAMP,
                retention_days INTEGER DEFAULT 30,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول إدارة المحتوى
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_management (
                content_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL CHECK(content_type IN ('page', 'article', 'blog', 'faq', 'tutorial', 'guide', 'announcement', 'policy', 'term')),
                title TEXT NOT NULL,
                slug TEXT UNIQUE,
                content TEXT NOT NULL,
                excerpt TEXT,
                featured_image TEXT,
                author_id INTEGER NOT NULL,
                status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'review', 'published', 'archived', 'deleted')),
                visibility TEXT DEFAULT 'public' CHECK(visibility IN ('public', 'private', 'password', 'scheduled')),
                password TEXT,
                publish_date TIMESTAMP,
                expiry_date TIMESTAMP,
                template TEXT,
                meta_title TEXT,
                meta_description TEXT,
                meta_keywords TEXT,
                tags TEXT DEFAULT '[]',
                categories TEXT DEFAULT '[]',
                reading_time INTEGER,
                word_count INTEGER,
                language TEXT DEFAULT 'ar',
                version INTEGER DEFAULT 1,
                parent_id INTEGER,
                menu_order INTEGER DEFAULT 0,
                comment_status INTEGER DEFAULT 0 CHECK(comment_status IN (0, 1)),
                comment_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                seo_score INTEGER DEFAULT 0,
                accessibility_features TEXT DEFAULT '[]',
                related_content TEXT DEFAULT '[]',
                custom_fields TEXT DEFAULT '{}',
                revisions TEXT DEFAULT '[]',
                last_edited_by INTEGER,
                last_edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                published_by INTEGER,
                published_at TIMESTAMP,
                archived_by INTEGER,
                archived_at TIMESTAMP,
                deleted_by INTEGER,
                deleted_at TIMESTAMP,
                restore_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES content_management(content_id) ON DELETE SET NULL,
                FOREIGN KEY (last_edited_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (published_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (archived_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (deleted_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الأحداث والتتبع
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_name TEXT NOT NULL,
                event_data TEXT DEFAULT '{}',
                page_url TEXT,
                referrer_url TEXT,
                device_type TEXT,
                browser TEXT,
                os TEXT,
                screen_resolution TEXT,
                ip_address TEXT,
                country TEXT,
                city TEXT,
                region TEXT,
                timezone TEXT,
                language TEXT,
                session_id TEXT NOT NULL,
                session_start TIMESTAMP,
                session_end TIMESTAMP,
                session_duration INTEGER,
                is_bounce INTEGER DEFAULT 0 CHECK(is_bounce IN (0, 1)),
                conversion_value INTEGER DEFAULT 0,
                campaign_source TEXT,
                campaign_medium TEXT,
                campaign_name TEXT,
                campaign_term TEXT,
                campaign_content TEXT,
                utm_parameters TEXT DEFAULT '{}',
                funnel_stage TEXT,
                funnel_name TEXT,
                revenue INTEGER DEFAULT 0,
                engagement_score INTEGER DEFAULT 0,
                scroll_depth INTEGER DEFAULT 0,
                time_on_page INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                form_submissions INTEGER DEFAULT 0,
                errors_encountered TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                processed INTEGER DEFAULT 0 CHECK(processed IN (0, 1)),
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول التعلم الآلي والتوصيات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL CHECK(item_type IN ('lecture', 'material', 'question', 'quiz', 'teacher', 'content')),
                item_id INTEGER NOT NULL,
                recommendation_type TEXT NOT NULL CHECK(recommendation_type IN ('collaborative', 'content_based', 'popular', 'trending', 'personalized', 'similar')),
                score REAL NOT NULL,
                reason TEXT,
                context TEXT DEFAULT '{}',
                position INTEGER,
                is_shown INTEGER DEFAULT 0 CHECK(is_shown IN (0, 1)),
                shown_at TIMESTAMP,
                is_clicked INTEGER DEFAULT 0 CHECK(is_clicked IN (0, 1)),
                clicked_at TIMESTAMP,
                click_position INTEGER,
                engagement_time INTEGER,
                conversion INTEGER DEFAULT 0 CHECK(conversion IN (0, 1)),
                conversion_value INTEGER DEFAULT 0,
                feedback INTEGER CHECK(feedback >= 1 AND feedback <= 5),
                feedback_reason TEXT,
                model_version TEXT,
                features_used TEXT DEFAULT '[]',
                prediction_confidence REAL,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الأمن والمراقبة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                security_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL CHECK(event_type IN ('login', 'logout', 'failed_login', 'password_change', '2fa_enabled', '2fa_disabled', 'suspicious_activity', 'blocked_ip', 'malicious_request', 'data_export', 'data_import', 'permission_change', 'role_change', 'api_call', 'file_upload', 'file_download')),
                event_details TEXT NOT NULL,
                severity TEXT DEFAULT 'medium' CHECK(severity IN ('low', 'medium', 'high', 'critical')),
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                device_fingerprint TEXT,
                location TEXT,
                is_vpn INTEGER DEFAULT 0 CHECK(is_vpn IN (0, 1)),
                is_tor INTEGER DEFAULT 0 CHECK(is_tor IN (0, 1)),
                is_proxy INTEGER DEFAULT 0 CHECK(is_proxy IN (0, 1)),
                threat_score INTEGER DEFAULT 0,
                threat_type TEXT,
                mitigation_action TEXT,
                mitigation_result TEXT,
                block_duration INTEGER,
                reviewed_by INTEGER,
                review_status TEXT DEFAULT 'pending' CHECK(review_status IN ('pending', 'reviewed', 'false_positive', 'confirmed', 'mitigated')),
                review_notes TEXT,
                related_logs TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول النسخ الاحتياطي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type TEXT NOT NULL CHECK(backup_type IN ('full', 'incremental', 'differential', 'manual')),
                backup_name TEXT NOT NULL,
                description TEXT,
                file_path TEXT,
                file_size INTEGER,
                checksum TEXT,
                database_version TEXT,
                app_version TEXT,
                includes_data INTEGER DEFAULT 1 CHECK(includes_data IN (0, 1)),
                includes_files INTEGER DEFAULT 0 CHECK(includes_files IN (0, 1)),
                includes_config INTEGER DEFAULT 1 CHECK(includes_config IN (0, 1)),
                compression_type TEXT DEFAULT 'gzip',
                encryption_type TEXT,
                encryption_key_hash TEXT,
                status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed', 'failed', 'verified', 'corrupted')),
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                verified_at TIMESTAMP,
                verification_result TEXT,
                storage_location TEXT,
                retention_days INTEGER DEFAULT 30,
                is_auto_backup INTEGER DEFAULT 1 CHECK(is_auto_backup IN (0, 1)),
                triggered_by INTEGER,
                restore_count INTEGER DEFAULT 0,
                last_restored_at TIMESTAMP,
                last_restored_by INTEGER,
                notes TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (triggered_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (last_restored_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول التكاملات والواجهات البرمجية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integrations (
                integration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('payment', 'sms', 'email', 'storage', 'analytics', 'social', 'crm', 'erp', 'ai', 'notification', 'other')),
                provider TEXT NOT NULL,
                api_key TEXT,
                api_secret TEXT,
                webhook_url TEXT,
                webhook_secret TEXT,
                config TEXT DEFAULT '{}',
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                last_sync TIMESTAMP,
                sync_status TEXT,
                error_count INTEGER DEFAULT 0,
                last_error TEXT,
                rate_limit_remaining INTEGER,
                rate_limit_reset TIMESTAMP,
                webhook_events TEXT DEFAULT '[]',
                webhook_last_received TIMESTAMP,
                webhook_last_status TEXT,
                credentials_encrypted INTEGER DEFAULT 1 CHECK(credentials_encrypted IN (0, 1)),
                encryption_key TEXT,
                test_mode INTEGER DEFAULT 0 CHECK(test_mode IN (0, 1)),
                test_config TEXT DEFAULT '{}',
                sandbox_credentials TEXT,
                webhook_test_results TEXT DEFAULT '{}',
                documentation_url TEXT,
                support_contact TEXT,
                version TEXT,
                endpoints TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الرموز والكوتشينات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                token_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_type TEXT NOT NULL CHECK(token_type IN ('access', 'refresh', 'password_reset', 'email_verification', 'api', 'one_time', 'session')),
                token_value TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                is_used INTEGER DEFAULT 0 CHECK(is_used IN (0, 1)),
                used_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الألعاب والتحديات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('quiz', 'puzzle', 'memory', 'speed', 'strategy', 'luck', 'knowledge')),
                description TEXT,
                rules TEXT,
                min_players INTEGER DEFAULT 1,
                max_players INTEGER DEFAULT 1,
                duration_minutes INTEGER,
                difficulty TEXT DEFAULT 'medium',
                is_multiplayer INTEGER DEFAULT 0 CHECK(is_multiplayer IN (0, 1)),
                is_competitive INTEGER DEFAULT 0 CHECK(is_competitive IN (0, 1)),
                entry_fee INTEGER DEFAULT 0,
                prize_pool INTEGER DEFAULT 0,
                prize_distribution TEXT DEFAULT '{}',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'upcoming' CHECK(status IN ('upcoming', 'registration', 'live', 'paused', 'ended', 'cancelled')),
                current_players INTEGER DEFAULT 0,
                max_players_limit INTEGER,
                winner_user_id INTEGER,
                winner_prize INTEGER,
                leaderboard TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (winner_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول المشاركة في الألعاب
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_participants (
                participation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                join_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                leave_time TIMESTAMP,
                score INTEGER DEFAULT 0,
                rank INTEGER,
                prize_won INTEGER DEFAULT 0,
                status TEXT DEFAULT 'playing' CHECK(status IN ('waiting', 'playing', 'finished', 'disqualified', 'abandoned')),
                play_data TEXT DEFAULT '{}',
                play_time_seconds INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0,
                speed REAL DEFAULT 0,
                is_winner INTEGER DEFAULT 0 CHECK(is_winner IN (0, 1)),
                feedback TEXT,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, user_id),
                FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول البطاقات والمجموعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_type TEXT NOT NULL CHECK(card_type IN ('achievement', 'badge', 'collectible', 'powerup', 'character', 'item')),
                name TEXT NOT NULL,
                description TEXT,
                rarity TEXT DEFAULT 'common' CHECK(rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic')),
                image_file_id TEXT,
                animation_file_id TEXT,
                value_points INTEGER DEFAULT 0,
                is_tradable INTEGER DEFAULT 1 CHECK(is_tradable IN (0, 1)),
                is_sellable INTEGER DEFAULT 0 CHECK(is_sellable IN (0, 1)),
                sell_price INTEGER,
                mint_count INTEGER DEFAULT 0,
                max_mint_count INTEGER,
                collection_id INTEGER,
                attributes TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection_id) REFERENCES card_collections(collection_id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول مجموعات البطاقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_collections (
                collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                theme TEXT,
                total_cards INTEGER DEFAULT 0,
                unique_cards INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 1 CHECK(is_public IN (0, 1)),
                is_complete INTEGER DEFAULT 0 CHECK(is_complete IN (0, 1)),
                completion_reward TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول ممتلكات البطاقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_cards (
                user_card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                acquisition_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acquisition_method TEXT CHECK(acquisition_method IN ('purchase', 'reward', 'trade', 'gift', 'found', 'crafted', 'upgraded')),
                acquisition_cost INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0 CHECK(is_favorite IN (0, 1)),
                is_locked INTEGER DEFAULT 0 CHECK(is_locked IN (0, 1)),
                lock_reason TEXT,
                condition TEXT DEFAULT 'mint' CHECK(condition IN ('mint', 'near_mint', 'excellent', 'good', 'fair', 'poor')),
        trades_count INTEGER DEFAULT 0,
                last_traded TIMESTAMP,
                display_order INTEGER,
        metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, card_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول تجارة البطاقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_user_id INTEGER NOT NULL,
                buyer_user_id INTEGER,
                card_id INTEGER NOT NULL,
                trade_type TEXT DEFAULT 'sell' CHECK(trade_type IN ('sell', 'buy', 'auction', 'trade', 'gift')),
                asking_price INTEGER,
                selling_price INTEGER,
                status TEXT DEFAULT 'listed' CHECK(status IN ('listed', 'reserved', 'sold', 'cancelled', 'expired', 'completed')),
                list_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sale_date TIMESTAMP,
                auction_end_time TIMESTAMP,
                current_bid INTEGER,
                highest_bidder_user_id INTEGER,
                bid_count INTEGER DEFAULT 0,
                is_instant_buy INTEGER DEFAULT 0 CHECK(is_instant_buy IN (0, 1)),
                instant_buy_price INTEGER,
                shipping_cost INTEGER DEFAULT 0,
                transaction_fee INTEGER DEFAULT 0,
                net_amount INTEGER,
                payment_method TEXT,
                payment_status TEXT,
                delivery_method TEXT,
                delivery_status TEXT,
                tracking_number TEXT,
                seller_rating INTEGER CHECK(seller_rating >= 1 AND seller_rating <= 5),
                buyer_rating INTEGER CHECK(buyer_rating >= 1 AND buyer_rating <= 5),
                feedback TEXT,
                dispute_opened INTEGER DEFAULT 0 CHECK(dispute_opened IN (0, 1)),
                dispute_reason TEXT,
                dispute_resolution TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (buyer_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE,
                FOREIGN KEY (highest_bidder_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول السوق والمزادات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL CHECK(item_type IN ('card', 'lecture', 'material', 'service', 'account', 'other')),
                item_id INTEGER NOT NULL,
                seller_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                quantity INTEGER DEFAULT 1,
                quantity_sold INTEGER DEFAULT 0,
                condition TEXT DEFAULT 'new',
                category TEXT,
                tags TEXT DEFAULT '[]',
                images TEXT DEFAULT '[]',
                videos TEXT DEFAULT '[]',
                listing_type TEXT DEFAULT 'fixed_price' CHECK(listing_type IN ('fixed_price', 'auction', 'best_offer', 'classified')),
                auction_end_time TIMESTAMP,
                starting_bid INTEGER,
                reserve_price INTEGER,
                buy_now_price INTEGER,
                is_highlighted INTEGER DEFAULT 0 CHECK(is_highlighted IN (0, 1)),
                is_featured INTEGER DEFAULT 0 CHECK(is_featured IN (0, 1)),
                is_urgent INTEGER DEFAULT 0 CHECK(is_urgent IN (0, 1)),
                is_negotiable INTEGER DEFAULT 0 CHECK(is_negotiable IN (0, 1)),
                shipping_available INTEGER DEFAULT 0 CHECK(shipping_available IN (0, 1)),
                shipping_cost INTEGER DEFAULT 0,
                shipping_locations TEXT DEFAULT '[]',
                return_policy TEXT,
                warranty TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('draft', 'active', 'sold', 'expired', 'cancelled', 'suspended', 'deleted')),
        views INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                inquiries INTEGER DEFAULT 0,
                last_viewed TIMESTAMP,
                expiry_date TIMESTAMP,
                auto_renew INTEGER DEFAULT 0 CHECK(auto_renew IN (0, 1)),
                featured_until TIMESTAMP,
                promoted_until TIMESTAMP,
                seo_title TEXT,
                seo_description TEXT,
                seo_keywords TEXT,
                verification_status TEXT DEFAULT 'unverified' CHECK(verification_status IN ('unverified', 'pending', 'verified', 'rejected')),
                verified_by INTEGER,
                verified_at TIMESTAMP,
                rejection_reason TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول العروض والطلبات في السوق
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_offers (
                offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                buyer_user_id INTEGER NOT NULL,
                offer_price INTEGER NOT NULL,
                message TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'countered', 'expired', 'cancelled')),
                seller_response TEXT,
                seller_counter_price INTEGER,
                expires_at TIMESTAMP,
                is_read INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
                read_at TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES marketplace(listing_id) ON DELETE CASCADE,
                FOREIGN KEY (buyer_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الطلبات والمبيعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                buyer_user_id INTEGER NOT NULL,
                seller_user_id INTEGER NOT NULL,
                order_number TEXT UNIQUE NOT NULL,
                item_title TEXT NOT NULL,
                item_description TEXT,
                quantity INTEGER DEFAULT 1,
                unit_price INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                shipping_cost INTEGER DEFAULT 0,
                tax_amount INTEGER DEFAULT 0,
                discount_amount INTEGER DEFAULT 0,
                final_amount INTEGER NOT NULL,
                payment_method TEXT NOT NULL,
                payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('pending', 'processing', 'completed', 'failed', 'refunded', 'partially_refunded')),
                payment_transaction_id TEXT,
                payment_date TIMESTAMP,
                shipping_method TEXT,
                shipping_status TEXT DEFAULT 'pending' CHECK(shipping_status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')),
                tracking_number TEXT,
                estimated_delivery TIMESTAMP,
                actual_delivery TIMESTAMP,
                buyer_address TEXT,
                buyer_phone TEXT,
                buyer_email TEXT,
                seller_notes TEXT,
                buyer_notes TEXT,
                cancellation_reason TEXT,
                refund_reason TEXT,
                refund_amount INTEGER,
                refund_date TIMESTAMP,
                dispute_opened INTEGER DEFAULT 0 CHECK(dispute_opened IN (0, 1)),
                dispute_reason TEXT,
                dispute_resolution TEXT,
                buyer_rating INTEGER CHECK(buyer_rating >= 1 AND buyer_rating <= 5),
                seller_rating INTEGER CHECK(seller_rating >= 1 AND seller_rating <= 5),
                buyer_feedback TEXT,
                seller_feedback TEXT,
                order_status TEXT DEFAULT 'pending' CHECK(order_status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned', 'refunded')),
                status_history TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES marketplace(listing_id) ON DELETE SET NULL,
                FOREIGN KEY (buyer_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (seller_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول المحفظة الرقمية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS digital_wallets (
                wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                wallet_address TEXT UNIQUE,
                wallet_type TEXT DEFAULT 'internal' CHECK(wallet_type IN ('internal', 'external', 'bank', 'crypto')),
                balance INTEGER DEFAULT 0 CHECK(balance >= 0),
                locked_balance INTEGER DEFAULT 0,
                total_deposited INTEGER DEFAULT 0,
                total_withdrawn INTEGER DEFAULT 0,
                currency TEXT DEFAULT 'IQD',
                is_verified INTEGER DEFAULT 0 CHECK(is_verified IN (0, 1)),
                verification_level TEXT DEFAULT 'basic' CHECK(verification_level IN ('basic', 'intermediate', 'advanced', 'full')),
                last_transaction_date TIMESTAMP,
                transaction_count INTEGER DEFAULT 0,
                security_level TEXT DEFAULT 'medium' CHECK(security_level IN ('low', 'medium', 'high', 'very_high')),
                two_factor_enabled INTEGER DEFAULT 0 CHECK(two_factor_enabled IN (0, 1)),
                backup_codes TEXT DEFAULT '[]',
                recovery_phrase TEXT,
                private_key_encrypted TEXT,
                public_key TEXT,
                qr_code_file_id TEXT,
                limits TEXT DEFAULT '{}',
                fees TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول معاملات المحفظة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('deposit', 'withdrawal', 'transfer', 'payment', 'refund', 'fee', 'reward', 'interest')),
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                fee_amount INTEGER DEFAULT 0,
                net_amount INTEGER NOT NULL,
                balance_before INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                reference_id TEXT,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'reversed')),
                from_address TEXT,
                to_address TEXT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                confirmation_count INTEGER DEFAULT 0,
                required_confirmations INTEGER DEFAULT 1,
                block_height INTEGER,
                transaction_hash TEXT,
                explorer_url TEXT,
                metadata TEXT DEFAULT '{}',
                notified INTEGER DEFAULT 0 CHECK(notified IN (0, 1)),
                notification_sent_at TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                review_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_id) REFERENCES digital_wallets(wallet_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (from_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (to_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول فئات الخدمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_category_id INTEGER,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT,
                color TEXT DEFAULT '#3498db',
                display_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                requires_vip INTEGER DEFAULT 0 CHECK(requires_vip IN (0, 1)),
                min_level INTEGER DEFAULT 1,
                price INTEGER DEFAULT 0,
                commission_rate REAL DEFAULT 0,
                tax_rate REAL DEFAULT 0,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_category_id) REFERENCES service_categories(category_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول الخدمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                detailed_description TEXT,
                icon TEXT,
                cover_image TEXT,
                price INTEGER NOT NULL DEFAULT 0,
                discount_price INTEGER,
                duration_minutes INTEGER,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                is_featured INTEGER DEFAULT 0 CHECK(is_featured IN (0, 1)),
                is_popular INTEGER DEFAULT 0 CHECK(is_popular IN (0, 1)),
                requires_approval INTEGER DEFAULT 0 CHECK(requires_approval IN (0, 1)),
                max_orders_per_day INTEGER,
                preparation_time INTEGER,
                tags TEXT DEFAULT '[]',
                requirements TEXT DEFAULT '[]',
                deliverables TEXT DEFAULT '[]',
                instructions TEXT,
                cancellation_policy TEXT,
                refund_policy TEXT,
                rating REAL DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                order_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 100,
                avg_completion_time INTEGER,
                provider_user_id INTEGER,
                is_auto_assign INTEGER DEFAULT 0 CHECK(is_auto_assign IN (0, 1)),
                assign_to_role TEXT,
                metadata TEXT DEFAULT '{}',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES service_categories(category_id) ON DELETE CASCADE,
                FOREIGN KEY (provider_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول طلبات الخدمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                provider_user_id INTEGER,
                order_number TEXT UNIQUE NOT NULL,
                requirements TEXT,
                attachments TEXT DEFAULT '[]',
                quantity INTEGER DEFAULT 1,
                unit_price INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                discount_amount INTEGER DEFAULT 0,
                final_amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'IQD',
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'in_progress', 'completed', 'delivered', 'cancelled', 'refunded', 'disputed')),
                priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
                deadline TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                delivered_at TIMESTAMP,
                delivery_method TEXT,
                delivery_info TEXT,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                review TEXT,
                cancellation_reason TEXT,
                refund_reason TEXT,
                refund_amount INTEGER,
                refund_date TIMESTAMP,
                dispute_opened INTEGER DEFAULT 0 CHECK(dispute_opened IN (0, 1)),
                dispute_reason TEXT,
                dispute_resolution TEXT,
                communication_log TEXT DEFAULT '[]',
                revision_count INTEGER DEFAULT 0,
                latest_revision TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (provider_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول المرفقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_attachments (
                attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                uploaded_by INTEGER NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_final INTEGER DEFAULT 0 CHECK(is_final IN (0, 1)),
                version INTEGER DEFAULT 1,
                notes TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (order_id) REFERENCES service_orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول المراجعات والمراجعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                provider_user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                title TEXT,
                review TEXT,
                is_anonymous INTEGER DEFAULT 0 CHECK(is_anonymous IN (0, 1)),
                is_verified_purchase INTEGER DEFAULT 1 CHECK(is_verified_purchase IN (0, 1)),
                helpful_count INTEGER DEFAULT 0,
                not_helpful_count INTEGER DEFAULT 0,
                report_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'approved' CHECK(status IN ('pending', 'approved', 'rejected', 'hidden')),
                moderated_by INTEGER,
                moderation_date TIMESTAMP,
                moderation_notes TEXT,
                sentiment_score REAL,
                aspect_ratings TEXT DEFAULT '{}',
                would_recommend INTEGER CHECK(would_recommend IN (0, 1)),
                would_reorder INTEGER CHECK(would_reorder IN (0, 1)),
                value_for_money INTEGER CHECK(value_for_money >= 1 AND value_for_money <= 5),
                communication_rating INTEGER CHECK(communication_rating >= 1 AND communication_rating <= 5),
                quality_rating INTEGER CHECK(quality_rating >= 1 AND quality_rating <= 5),
                timeliness_rating INTEGER CHECK(timeliness_rating >= 1 AND timeliness_rating <= 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES service_orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (provider_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (moderated_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول المهارات والاختصاصات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                skill_category TEXT,
                proficiency_level TEXT DEFAULT 'intermediate' CHECK(proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert', 'master')),
                years_of_experience INTEGER DEFAULT 0,
                certification TEXT,
                certification_date DATE,
                is_verified INTEGER DEFAULT 0 CHECK(is_verified IN (0, 1)),
                verified_by INTEGER,
                verification_date TIMESTAMP,
                portfolio_items TEXT DEFAULT '[]',
                hourly_rate INTEGER,
                is_available INTEGER DEFAULT 1 CHECK(is_available IN (0, 1)),
                availability_schedule TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                description TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, skill_name),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (verified_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول المشاريع
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                project_type TEXT CHECK(project_type IN ('academic', 'professional', 'personal', 'research', 'startup', 'freelance')),
                status TEXT DEFAULT 'planning' CHECK(status IN ('planning', 'in_progress', 'on_hold', 'completed', 'cancelled', 'archived')),
                priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
                start_date DATE,
                end_date DATE,
                deadline DATE,
                budget INTEGER DEFAULT 0,
                actual_cost INTEGER DEFAULT 0,
                currency TEXT DEFAULT 'IQD',
                is_public INTEGER DEFAULT 0 CHECK(is_public IN (0, 1)),
                collaborators TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                attachments TEXT DEFAULT '[]',
                milestones TEXT DEFAULT '[]',
                risks TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                notes TEXT,
                completion_percentage REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول المهام
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                task_type TEXT CHECK(task_type IN ('todo', 'reminder', 'deadline', 'meeting', 'call', 'email', 'research', 'writing', 'coding', 'design', 'review', 'other')),
                status TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'in_progress', 'review', 'completed', 'cancelled', 'deferred')),
                priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
                due_date TIMESTAMP,
                completed_date TIMESTAMP,
                estimated_hours INTEGER,
                actual_hours INTEGER,
                assignee_user_id INTEGER,
                reporter_user_id INTEGER,
                tags TEXT DEFAULT '[]',
                checklist TEXT DEFAULT '[]',
                attachments TEXT DEFAULT '[]',
                comments_count INTEGER DEFAULT 0,
                is_recurring INTEGER DEFAULT 0 CHECK(is_recurring IN (0, 1)),
                recurrence_pattern TEXT,
                next_recurrence TIMESTAMP,
                reminder_sent INTEGER DEFAULT 0 CHECK(reminder_sent IN (0, 1)),
                reminder_time TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (assignee_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (reporter_user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        ''')
        
        # جدول التقويم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT CHECK(event_type IN ('appointment', 'meeting', 'deadline', 'reminder', 'holiday', 'birthday', 'anniversary', 'exam', 'class', 'work', 'personal', 'other')),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                is_all_day INTEGER DEFAULT 0 CHECK(is_all_day IN (0, 1)),
                location TEXT,
                latitude REAL,
                longitude REAL,
                timezone TEXT DEFAULT 'Asia/Baghdad',
                recurrence_pattern TEXT,
                recurrence_end_date TIMESTAMP,
                reminders TEXT DEFAULT '[]',
                attendees TEXT DEFAULT '[]',
                color TEXT DEFAULT '#3498db',
                is_public INTEGER DEFAULT 0 CHECK(is_public IN (0, 1)),
                status TEXT DEFAULT 'confirmed' CHECK(status IN ('tentative', 'confirmed', 'cancelled')),
                cancellation_reason TEXT,
                source TEXT,
                source_id TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول الاجتماعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organizer_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                agenda TEXT,
                meeting_type TEXT CHECK(meeting_type IN ('video', 'audio', 'in_person', 'hybrid')),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                timezone TEXT DEFAULT 'Asia/Baghdad',
                meeting_link TEXT,
                meeting_password TEXT,
                platform TEXT CHECK(platform IN ('zoom', 'google_meet', 'teams', 'skype', 'other', 'telegram')),
                max_participants INTEGER,
                recording_url TEXT,
                transcription_url TEXT,
                status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'started', 'ended', 'cancelled', 'postponed')),
                cancelled_reason TEXT,
                feedback_form_url TEXT,
                notes TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organizer_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # جدول المشاركين في الاجتماعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meeting_participants (
                participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'attendee' CHECK(role IN ('organizer', 'co_organizer', 'presenter', 'attendee', 'guest')),
                invite_status TEXT DEFAULT 'pending' CHECK(invite_status IN ('pending', 'accepted', 'declined', 'tentative', 'no_response')),
                response_date TIMESTAMP,
                attended INTEGER DEFAULT 0 CHECK(attended IN (0, 1)),
                join_time TIMESTAMP,
                leave_time TIMESTAMP,
                duration_seconds INTEGER,
                feedback_submitted INTEGER DEFAULT 0 CHECK(feedback_submitted IN (0, 1)),
                feedback_rating INTEGER CHECK(feedback_rating >= 1 AND feedback_rating <= 5),
                feedback_comments TEXT,
                notes TEXT,
                UNIQUE(meeting_id, user_id),
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        # إنشاء الفهرس لتسريع الاستعلامات
        cursor.executescript('''
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance);
            CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);
            CREATE INDEX IF NOT EXISTS idx_users_join_date ON users(join_date);
            CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
            CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
            
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_teacher_id ON vip_lectures(teacher_id);
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_is_approved ON vip_lectures(is_approved);
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_category ON vip_lectures(category);
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_subject ON vip_lectures(subject);
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_price ON vip_lectures(price);
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_rating ON vip_lectures(rating);
            CREATE INDEX IF NOT EXISTS idx_vip_lectures_upload_date ON vip_lectures(upload_date);
            
            CREATE INDEX IF NOT EXISTS idx_lecture_purchases_user_id ON lecture_purchases(user_id);
            CREATE INDEX IF NOT EXISTS idx_lecture_purchases_lecture_id ON lecture_purchases(lecture_id);
            CREATE INDEX IF NOT EXISTS idx_lecture_purchases_purchase_date ON lecture_purchases(purchase_date);
            CREATE INDEX IF NOT EXISTS idx_lecture_purchases_payment_status ON lecture_purchases(payment_status);
            
            CREATE INDEX IF NOT EXISTS idx_teacher_earnings_teacher_id ON teacher_earnings(teacher_id);
            CREATE INDEX IF NOT EXISTS idx_teacher_earnings_status ON teacher_earnings(status);
            CREATE INDEX IF NOT EXISTS idx_teacher_earnings_is_paid ON teacher_earnings(is_paid);
            
            CREATE INDEX IF NOT EXISTS idx_student_questions_user_id ON student_questions(user_id);
            CREATE INDEX IF NOT EXISTS idx_student_questions_is_answered ON student_questions(is_answered);
            CREATE INDEX IF NOT EXISTS idx_student_questions_is_approved ON student_questions(is_approved);
            CREATE INDEX IF NOT EXISTS idx_student_questions_subject ON student_questions(subject);
            CREATE INDEX IF NOT EXISTS idx_student_questions_question_date ON student_questions(question_date);
            
            CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
            CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
            CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
            
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
            CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);
            
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
            
            CREATE INDEX IF NOT EXISTS idx_broadcasts_status ON broadcasts(status);
            CREATE INDEX IF NOT EXISTS idx_broadcasts_scheduled_for ON broadcasts(scheduled_for);
            CREATE INDEX IF NOT EXISTS idx_broadcasts_created_by ON broadcasts(created_by);
            
            CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code);
            CREATE INDEX IF NOT EXISTS idx_coupons_is_active ON coupons(is_active);
            CREATE INDEX IF NOT EXISTS idx_coupons_valid_until ON coupons(valid_until);
            
            CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_security_logs_severity ON security_logs(severity);
            CREATE INDEX IF NOT EXISTS idx_security_logs_created_at ON security_logs(created_at);
            
            CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON user_events(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON user_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_user_events_session_id ON user_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON user_events(created_at);
        ''')
        
        # إضافة البيانات الأساسية
        self._seed_initial_data(cursor)
        
        self.conn.commit()
        logger.info("تم تهيئة قاعدة البيانات المتقدمة بنجاح")
    
    def _seed_initial_data(self, cursor):
        """إضافة البيانات الأولية"""
        # إضافة المستخدم الإداري
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (ADMIN_ID,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, role, balance, is_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ADMIN_ID, ADMIN_USERNAME, "المدير", "البوت", "super_admin", 0, 1))
        
        # إضافة فئات الخدمات
        services_categories = [
            ("تعليمي", "خدمات تعليمية ودراسية", "🎓", 1),
            ("مالي", "خدمات مالية ومعاملات", "💰", 2),
            ("ترفيهي", "ألعاب وترفيه", "🎮", 3),
            ("اجتماعي", "تفاعل اجتماعي ومجتمعي", "👥", 4),
            ("تقني", "خدمات تقنية ودعم", "🛠️", 5)
        ]
        
        for category in services_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO service_categories 
                (name, description, icon, display_order)
                VALUES (?, ?, ?, ?)
            ''', category)
        
        # إضافة إعدادات البوت الأساسية
        default_settings = [
            ("general", "bot_name", "يلا نتعلم", "string", "اسم البوت"),
            ("general", "bot_username", BOT_USERNAME, "string", "يوزر البوت"),
            ("general", "admin_username", ADMIN_USERNAME, "string", "يوزر المدير"),
            ("general", "bot_channel", BOT_CHANNEL, "string", "قناة البوت"),
            ("general", "welcome_bonus", "1000", "integer", "مكافأة الترحيب"),
            
            ("services", "exemption_calc_price", "1000", "integer", "سعر حساب الإعفاء"),
            ("services", "pdf_summary_price", "1000", "integer", "سعر تلخيص PDF"),
            ("services", "ai_qa_price", "1000", "integer", "سعر سؤال الذكاء الاصطناعي"),
            ("services", "help_student_price", "1000", "integer", "سعر ساعدوني طالب"),
            ("services", "vip_subscription_price", "5000", "integer", "سعر اشتراك VIP"),
            
            ("referral", "referral_bonus", "500", "integer", "مكافأة الدعوة"),
            ("referral", "max_referrals_per_day", "10", "integer", "أقصى دعوات يومياً"),
            
            ("withdrawal", "min_withdrawal_amount", "15000", "integer", "الحد الأدنى للسحب"),
            ("withdrawal", "withdrawal_fee_percent", "5", "integer", "عمولة السحب"),
            
            ("notifications", "enable_transaction_notifications", "1", "boolean", "تفعيل إشعارات المعاملات"),
            ("notifications", "enable_promotional_notifications", "1", "boolean", "تفعيل الإشعارات الترويجية"),
            
            ("security", "max_login_attempts", "5", "integer", "أقصى محاولات تسجيل دخول"),
            ("security", "session_timeout_minutes", "30", "integer", "مدة انتهاء الجلسة"),
            
            ("ui", "default_language", "ar", "string", "اللغة الافتراضية"),
            ("ui", "default_theme", "light", "string", "الثيم الافتراضي"),
        ]
        
        for setting in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO bot_settings 
                (category, setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', setting)
    
    def _start_backup_scheduler(self):
        """بدء مجدول النسخ الاحتياطي"""
        def backup_task():
            while True:
                time.sleep(self.backup_interval)
                self.create_backup()
        
        thread = threading.Thread(target=backup_task, daemon=True)
        thread.start()
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            backup_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_time}.db"
            backup_path = f"backups/{backup_name}"
            
            # إنشاء مجلد النسخ الاحتياطية إذا لم يكن موجوداً
            os.makedirs("backups", exist_ok=True)
            
            # نسخ قاعدة البيانات
            with open(backup_path, 'wb') as f:
                for line in self.conn.iterdump():
                    f.write(f'{line}\n'.encode('utf-8'))
            
            # تسجيل النسخة الاحتياطية
            file_size = os.path.getsize(backup_path)
            checksum = hashlib.md5(open(backup_path, 'rb').read()).hexdigest()
            
            self.execute_query('''
                INSERT INTO backups 
                (backup_type, backup_name, file_path, file_size, checksum, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('incremental', backup_name, backup_path, file_size, checksum, 'completed', datetime.datetime.now()))
            
            logger.info(f"تم إنشاء نسخة احتياطية: {backup_name}")
            
            # حذف النسخ القديمة (احتفظ بـ 7 أيام فقط)
            self._clean_old_backups()
            
        except Exception as e:
            logger.error(f"فشل إنشاء نسخة احتياطية: {str(e)}")
    
    def _clean_old_backups(self):
        """حذف النسخ الاحتياطية القديمة"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
            
            backups = self.fetch_all(
                "SELECT backup_id, file_path FROM backups WHERE completed_at < ?",
                (cutoff_date,)
            )
            
            for backup in backups:
                backup_id, file_path = backup
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                self.execute_query(
                    "DELETE FROM backups WHERE backup_id = ?",
                    (backup_id,)
                )
            
        except Exception as e:
            logger.error(f"فشل تنظيف النسخ الاحتياطية القديمة: {str(e)}")
    
    def execute_query(self, query, params=()):
        """تنفيذ استعلام مع معالجة الأخطاء"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"خطأ في قاعدة البيانات: {str(e)} - الاستعلام: {query}")
            raise
    
    def fetch_one(self, query, params=()):
        """جلب سجل واحد"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query, params=()):
        """جلب جميع السجلات"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        if self.conn:
            self.conn.close()

# ============== نظام الإشعارات المتقدم ==============
class NotificationSystem:
    """نظام الإشعارات المتقدم"""
    
    def __init__(self, db):
        self.db = db
        self.priority_levels = {
            'urgent': {'color': '🔴', 'delay': 0},
            'high': {'color': '🟠', 'delay': 60},
            'normal': {'color': '🔵', 'delay': 300},
            'low': {'color': '⚫', 'delay': 1800}
        }
    
    async def send_notification(self, user_id, title, message, notification_type='system', priority='normal', data=None):
        """إرسال إشعار جديد"""
        try:
            notification_id = self.db.execute_query('''
                INSERT INTO notifications 
                (user_id, notification_type, title, message, data, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, notification_type, title, message, json.dumps(data or {}), priority)).lastrowid
            
            # إرسال الإشعار الفوري إذا كان عاجلاً
            if priority in ['urgent', 'high']:
                await self._send_immediate_notification(user_id, title, message)
            
            return notification_id
            
        except Exception as e:
            logger.error(f"فشل إرسال إشعار: {str(e)}")
            return None
    
    async def _send_immediate_notification(self, user_id, title, message):
        """إرسال إشعار فوري عبر التليجرام"""
        try:
            # سيتم تنفيذ هذا عند دمج نظام البوت
            pass
        except Exception as e:
            logger.error(f"فشل إرسال إشعار فوري: {str(e)}")
    
    def get_user_notifications(self, user_id, unread_only=False, limit=50):
        """الحصول على إشعارات المستخدم"""
        query = "SELECT * FROM notifications WHERE user_id = ?"
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = 0"
        
        query += " ORDER BY sent_at DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def mark_as_read(self, notification_id):
        """تحديد الإشعار كمقروء"""
        self.db.execute_query(
            "UPDATE notifications SET is_read = 1, read_date = ? WHERE notification_id = ?",
            (datetime.datetime.now(), notification_id)
        )
    
    def mark_all_as_read(self, user_id):
        """تحديد كل إشعارات المستخدم كمقروءة"""
        self.db.execute_query(
            "UPDATE notifications SET is_read = 1, read_date = ? WHERE user_id = ? AND is_read = 0",
            (datetime.datetime.now(), user_id)
        )

# ============== نظام الإحصائيات المتقدم ==============
class StatisticsSystem:
    """نظام الإحصائيات المتقدم"""
    
    def __init__(self, db):
        self.db = db
    
    def update_daily_stats(self):
        """تحديث الإحصائيات اليومية"""
        try:
            today = datetime.datetime.now().date()
            
            # التحقق من وجود إحصائيات اليوم
            existing = self.db.fetch_one(
                "SELECT stat_id FROM daily_stats WHERE stat_date = ?",
                (today,)
            )
            
            if existing:
                return  # الإحصائيات موجودة بالفعل
            
            # جمع الإحصائيات
            total_users = self.db.fetch_one("SELECT COUNT(*) FROM users")[0]
            active_users = self.db.fetch_one("SELECT COUNT(*) FROM users WHERE last_active >= ?", 
                                           (datetime.datetime.now() - datetime.timedelta(days=1),))[0]
            new_users = self.db.fetch_one("SELECT COUNT(*) FROM users WHERE join_date >= ?",
                                        (datetime.datetime.now() - datetime.timedelta(days=1),))[0]
            vip_users = self.db.fetch_one("SELECT COUNT(*) FROM vip_subscriptions WHERE is_active = 1")[0]
            
            # الإحصائيات المالية
            total_income = self.db.fetch_one('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE type = 'purchase' AND created_at >= ?
            ''', (datetime.datetime.now() - datetime.timedelta(days=1),))[0] or 0
            
            total_income = abs(total_income)
            
            # إدراج الإحصائيات اليومية
            self.db.execute_query('''
                INSERT INTO daily_stats 
                (stat_date, total_users, active_users, new_users, vip_users, total_income)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, total_users, active_users, new_users, vip_users, total_income))
            
            logger.info(f"تم تحديث الإحصائيات اليومية لتاريخ: {today}")
            
        except Exception as e:
            logger.error(f"فشل تحديث الإحصائيات اليومية: {str(e)}")
    
    def get_overall_stats(self):
        """الحصول على إحصائيات شاملة"""
        stats = {}
        
        # إحصائيات المستخدمين
        stats['total_users'] = self.db.fetch_one("SELECT COUNT(*) FROM users")[0]
        stats['active_users'] = self.db.fetch_one("SELECT COUNT(*) FROM users WHERE is_banned = 0")[0]
        stats['vip_users'] = self.db.fetch_one("SELECT COUNT(*) FROM vip_subscriptions WHERE is_active = 1")[0]
        stats['teachers'] = self.db.fetch_one("SELECT COUNT(*) FROM users WHERE role = 'teacher'")[0]
        stats['admins'] = self.db.fetch_one("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'super_admin')")[0]
        
        # إحصائيات مالية
        stats['total_balance'] = self.db.fetch_one("SELECT SUM(balance) FROM users")[0] or 0
        stats['total_income'] = abs(self.db.fetch_one("SELECT SUM(amount) FROM transactions WHERE type = 'purchase'")[0] or 0)
        stats['total_withdrawals'] = abs(self.db.fetch_one("SELECT SUM(amount) FROM transactions WHERE type = 'withdrawal'")[0] or 0)
        
        # إحصائيات المحتوى
        stats['total_lectures'] = self.db.fetch_one("SELECT COUNT(*) FROM vip_lectures WHERE is_approved = 1")[0]
        stats['total_questions'] = self.db.fetch_one("SELECT COUNT(*) FROM student_questions")[0]
        stats['answered_questions'] = self.db.fetch_one("SELECT COUNT(*) FROM student_questions WHERE is_answered = 1")[0]
        stats['total_materials'] = self.db.fetch_one("SELECT COUNT(*) FROM study_materials")[0]
        
        # إحصائيات النشاط
        stats['today_transactions'] = self.db.fetch_one('''
            SELECT COUNT(*) FROM transactions WHERE DATE(created_at) = DATE('now')
        ''')[0]
        
        stats['weekly_active'] = self.db.fetch_one('''
            SELECT COUNT(DISTINCT user_id) FROM transactions 
            WHERE created_at >= DATE('now', '-7 days')
        ''')[0]
        
        return stats
    
    def get_financial_report(self, start_date=None, end_date=None):
        """تقرير مالي مفصل"""
        if not start_date:
            start_date = datetime.datetime.now() - datetime.timedelta(days=30)
        if not end_date:
            end_date = datetime.datetime.now()
        
        report = {
            'period': {'start': start_date, 'end': end_date},
            'revenue_by_service': {},
            'daily_revenue': [],
            'top_earners': [],
            'conversion_rates': {}
        }
        
        # الإيرادات حسب الخدمة
        revenue_by_service = self.db.fetch_all('''
            SELECT 
                CASE 
                    WHEN item_type = 'lecture' THEN 'محاضرات'
                    WHEN item_type = 'vip' THEN 'اشتراكات VIP'
                    WHEN item_type = 'question' THEN 'أسئلة'
                    ELSE 'أخرى'
                END as service_type,
                SUM(amount) as revenue
            FROM transactions 
            WHERE type = 'purchase' 
                AND created_at BETWEEN ? AND ?
            GROUP BY service_type
        ''', (start_date, end_date))
        
        for service_type, revenue in revenue_by_service:
            report['revenue_by_service'][service_type] = abs(revenue)
        
        # الإيرادات اليومية
        daily_revenue = self.db.fetch_all('''
            SELECT DATE(created_at) as date, SUM(amount) as revenue
            FROM transactions 
            WHERE type = 'purchase' 
                AND created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (start_date, end_date))
        
        for date, revenue in daily_revenue:
            report['daily_revenue'].append({
                'date': date,
                'revenue': abs(revenue)
            })
        
        # أعلى المكسبين (المدرسين)
        top_earners = self.db.fetch_all('''
            SELECT 
                u.user_id,
                u.first_name,
                u.username,
                SUM(te.amount) as earnings
            FROM teacher_earnings te
            JOIN users u ON te.teacher_id = u.user_id
            WHERE te.created_at BETWEEN ? AND ?
                AND te.status = 'available'
            GROUP BY te.teacher_id
            ORDER BY earnings DESC
            LIMIT 10
        ''', (start_date, end_date))
        
        for user_id, first_name, username, earnings in top_earners:
            report['top_earners'].append({
                'user_id': user_id,
                'name': first_name,
                'username': username,
                'earnings': earnings
            })
        
        return report

# ============== نظام الذكاء الاصطناعي المتقدم ==============
class AdvancedAI:
    """نظام ذكاء اصطناعي متقدم"""
    
    def __init__(self):
        self.models = {
            'summary': ai_models['default'],
            'qa': ai_models['default'],
            'advanced': ai_models['advanced'],
            'vision': ai_models['vision']
        }
        
        # نماذج المحادثة
        self.conversations = {}
    
    async def summarize_pdf(self, pdf_bytes, language='ar'):
        """تلخيص ملف PDF متقدم"""
        try:
            # استخراج النص من PDF
            text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        # إعادة تشكيل النص العربي
                        if language == 'ar':
                            page_text = arabic_reshaper.reshape(page_text)
                            page_text = get_display(page_text)
                        text += page_text + "\n\n"
            
            if not text.strip():
                return "❌ لم أتمكن من استخراج النص من الملف. يرجى التأكد أن الملف يحتوي على نص قابل للقراءة."
            
            # تحديد طول النص وضبط الطول المستهدف
            text_length = len(text)
            if text_length > 10000:
                # إذا كان النص طويلاً، نأخذ عينات منه
                sample_size = 8000
                step = text_length // sample_size
                sampled_text = ''.join([text[i] for i in range(0, text_length, step)][:sample_size])
                text = sampled_text + "\n\n[تم اختصار النص بسبب طوله]"
            
            # إنشاء موجه ذكي للتلخيص
            prompt = f"""
            أنت مساعد تعليمي ذكي للطلاب العراقيين. قم بتلخيص النص التعليمي التالي مع مراعاة:
            
            1. التركيز على النقاط الرئيسية والمفاهيم الأساسية
            2. حذف المقدمات الطويلة والتكرار
            3. تنظيم المعلومات في نقاط واضحة
            4. الحفاظ على الدقة العلمية
            5. استخدام لغة عربية سليمة وواضحة
            6. إضافة عناوين فرعية إذا لزم الأمر
            7. تسليط الضوء على المصطلحات المهمة
            
            النص:
            {text[:5000]}
            
            الملخص يجب أن يكون:
            - واضح ومباشر
            - منظم في نقاط
            - شامل للمفاهيم الرئيسية
            - مناسب للطلاب
            
            أبدأ الملخص الآن:
            """
            
            # إضافة سياق إضافي للغة العربية
            if language == 'ar':
                prompt += "\n\nالرجاء الكتابة باللغة العربية الفصحى مع مراعاة القواعد النحوية."
            
            # توليد الملخص
            response = await asyncio.to_thread(
                self.models['summary'].generate_content,
                prompt
            )
            
            summary = response.text
            
            # تحسين تنسيق الملخص
            summary = self._format_summary(summary, language)
            
            return summary
            
        except Exception as e:
            logger.error(f"خطأ في تلخيص PDF: {str(e)}")
            return f"❌ حدث خطأ أثناء معالجة الملف: {str(e)}"
    
    def _format_summary(self, summary, language='ar'):
        """تحسين تنسيق الملخص"""
        # إضافة تنسيق Markdown
        lines = summary.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # تحديد نوع السطر وإضافة التنسيق المناسب
            if line.startswith(('•', '-', '*')) or line[0].isdigit() and '.' in line[:3]:
                formatted_lines.append(f"• {line.lstrip('•-* 1234567890.')}")
            elif ':' in line and len(line.split(':')[0]) < 30:
                formatted_lines.append(f"**{line}**")
            else:
                formatted_lines.append(line)
        
        # إضافة رأس الملخص
        header = "📄 **ملخص الوثيقة**\n\n"
        
        # إضافة تذييل
        footer = "\n\n---\n✅ *تم التلخيص باستخدام الذكاء الاصطناعي*"
        
        result = header + '\n'.join(formatted_lines) + footer
        
        # إعادة تشكيل النص العربي إذا لزم الأمر
        if language == 'ar':
            result = arabic_reshaper.reshape(result)
            result = get_display(result)
        
        return result
    
    async def answer_question(self, question, context=None, subject=None, grade=None):
        """الإجابة على الأسئلة التعليمية"""
        try:
            # بناء موجه ذكي للإجابة
            prompt_parts = []
            
            prompt_parts.append("أنت مساعد تعليمي ذكي متخصص في المنهج العراقي.")
            
            if subject:
                prompt_parts.append(f"المادة: {subject}")
            
            if grade:
                prompt_parts.append(f"الصف: {grade}")
            
            prompt_parts.append("مهمتك: تقديم إجابات علمية دقيقة وواضحة تناسب مستوى الطالب.")
            
            if context:
                prompt_parts.append(f"السياق: {context}")
            
            prompt_parts.append("الشروط:")
            prompt_parts.append("1. استخدم لغة عربية واضحة وسليمة")
            prompt_parts.append("2. قدم المعلومات بشكل منظم")
            prompt_parts.append("3. ركز على النقاط الرئيسية")
            prompt_parts.append("4. تجنب المعلومات غير الدقيقة")
            prompt_parts.append("5. إذا كان السؤال يحتاج إلى رسم توضيحي، صفه بكلمات")
            prompt_parts.append("6. أذكر المصادر إذا كانت المعلومات معروفة")
            
            prompt_parts.append(f"السؤال: {question}")
            prompt_parts.append("الرجاء تقديم الإجابة الآن:")
            
            full_prompt = "\n".join(prompt_parts)
            
            # توليد الإجابة
            response = await asyncio.to_thread(
                self.models['qa'].generate_content,
                full_prompt
            )
            
            answer = response.text
            
            # تحسين تنسيق الإجابة
            answer = self._format_answer(answer, question)
            
            return answer
            
        except Exception as e:
            logger.error(f"خطأ في الإجابة على السؤال: {str(e)}")
            return f"❌ حدث خطأ أثناء معالجة سؤالك: {str(e)}"
    
    def _format_answer(self, answer, question):
        """تحسين تنسيق الإجابة"""
        # إضافة تنسيق Markdown
        header = f"❓ **السؤال:** {question}\n\n"
        header += "💡 **الإجابة:**\n\n"
        
        # تحسين تنسيق النص
        lines = answer.split('\n')
        formatted_lines = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # كشف العناوين
            if line.endswith(':') and len(line) < 50:
                formatted_lines.append(f"\n**{line}**")
                current_section = line
            elif any(marker in line.lower() for marker in ['•', '-', '*', '✓', '→']):
                formatted_lines.append(f"• {line.lstrip('•-*✓→ ')}")
            elif line[0].isdigit() and '.' in line[:3]:
                formatted_lines.append(f"{line}")
            elif current_section and ':' in current_section:
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        # دمج النص
        formatted_text = header + '\n'.join(formatted_lines)
        
        # إضافة تذييل
        formatted_text += "\n\n---\n🤖 *تمت الإجابة باستخدام الذكاء الاصطناعي*"
        
        # إعادة تشكيل النص العربي
        formatted_text = arabic_reshaper.reshape(formatted_text)
        formatted_text = get_display(formatted_text)
        
        return formatted_text
    
    async def generate_quiz(self, subject, topic, difficulty='medium', num_questions=10):
        """إنشاء اختبار تلقائي"""
        try:
            prompt = f"""
            أنت مساعد تعليمي متخصص في إنشاء الاختبارات.
            
            المادة: {subject}
            الموضوع: {topic}
            المستوى: {difficulty}
            عدد الأسئلة: {num_questions}
            
            قم بإنشاء اختبار متكامل يتضمن:
            1. أسئلة اختيار من متعدد (4 خيارات)
            2. أسئلة صواب/خطأ
            3. أسئلة الإجابة القصيرة
            4. تحديد الإجابة الصحيحة لكل سؤال
            5. شرح موجز للإجابة
            
            قدم النتيجة بتنسيق JSON:
            {{
                "quiz_title": "عنوان الاختبار",
                "subject": "{subject}",
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "questions": [
                    {{
                        "question": "نص السؤال",
                        "type": "multiple_choice",
                        "options": ["الخيار 1", "الخيار 2", "الخيار 3", "الخيار 4"],
                        "correct_answer": 0,
                        "explanation": "شرح الإجابة"
                    }}
                ]
            }}
            """
            
            response = await asyncio.to_thread(
                self.models['advanced'].generate_content,
                prompt
            )
            
            # محاولة تحليل JSON
            try:
                quiz_data = json.loads(response.text)
                return quiz_data
            except json.JSONDecodeError:
                # إذا فشل تحليل JSON، نعيد النص كما هو
                return {"raw_content": response.text}
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الاختبار: {str(e)}")
            return None
    
    async def analyze_image_question(self, image_bytes, question=None):
        """تحليل الأسئلة المصورة"""
        try:
            # تحويل الصورة
            image = Image.open(io.BytesIO(image_bytes))
            
            if question:
                prompt = f"""
                هذه صورة تحتوي على سؤال أو مشكلة تعليمية.
                
                السؤال المصاحب: {question}
                
                قم ب:
                1. قراءة ونص الصورة إذا كان فيها نص
                2. تحليل المشكلة أو السؤال
                3. تقديم حله خطوة بخطوة
                4. استخدام لغة عربية واضحة
                5. إذا كانت تحتوي على معادلات، اكتبها بشكل صحيح
                """
            else:
                prompt = """
                هذه صورة تعليمية. قم ب:
                1. قراءة أي نص في الصورة
                2. فهم المحتوى التعليمي
                3. شرح المحتوى بشكل مفصل
                4. إذا كانت تحتوي على رسم بياني أو مخطط، صفه
                5. استخرج المعلومات الرئيسية
                """
            
            response = await asyncio.to_thread(
                self.models['vision'].generate_content,
                [prompt, image]
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"خطأ في تحليل الصورة: {str(e)}")
            return f"❌ حدث خطأ أثناء تحليل الصورة: {str(e)}"

# ============== نظام إدارة الملفات ==============
class FileManager:
    """مدير الملفات المتقدم"""
    
    SUPPORTED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'mp4': 'video/mp4',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'txt': 'text/plain',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed'
    }
    
    def __init__(self, db):
        self.db = db
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def save_file(self, file_bytes, filename, user_id):
        """حفظ ملف في النظام"""
        try:
            # إنشاء اسم فريد للملف
            ext = os.path.splitext(filename)[1].lower()
            unique_filename = f"{user_id}_{int(time.time())}_{hashlib.md5(file_bytes).hexdigest()[:8]}{ext}"
            filepath = os.path.join(self.upload_dir, unique_filename)
            
            # حفظ الملف
            with open(filepath, 'wb') as f:
                f.write(file_bytes)
            
            # تسجيل الملف في قاعدة البيانات
            file_id = self.db.execute_query('''
                INSERT INTO files 
                (user_id, original_filename, stored_filename, filepath, file_size, mime_type, upload_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                filename,
                unique_filename,
                filepath,
                len(file_bytes),
                mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                datetime.datetime.now()
            )).lastrowid
            
            return file_id, unique_filename, filepath
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الملف: {str(e)}")
            raise
    
    def get_file_info(self, file_id):
        """الحصول على معلومات الملف"""
        return self.db.fetch_one(
            "SELECT * FROM files WHERE file_id = ?",
            (file_id,)
        )
    
    def delete_file(self, file_id):
        """حذف ملف"""
        try:
            file_info = self.get_file_info(file_id)
            if file_info:
                filepath = file_info[4]  # عمود filepath
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                self.db.execute_query(
                    "DELETE FROM files WHERE file_id = ?",
                    (file_id,)
                )
                
                return True
            return False
        except Exception as e:
            logger.error(f"خطأ في حذف الملف: {str(e)}")
            return False
    
    def get_user_files(self, user_id, file_type=None):
        """الحصول على ملفات المستخدم"""
        query = "SELECT * FROM files WHERE user_id = ?"
        params = [user_id]
        
        if file_type:
            query += " AND mime_type LIKE ?"
            params.append(f"%{file_type}%")
        
        query += " ORDER BY upload_date DESC"
        
        return self.db.fetch_all(query, params)
    
    def cleanup_old_files(self, days_old=30):
        """تنظيف الملفات القديمة"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
            
            old_files = self.db.fetch_all(
                "SELECT file_id, filepath FROM files WHERE upload_date < ?",
                (cutoff_date,)
            )
            
            deleted_count = 0
            for file_id, filepath in old_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                self.db.execute_query(
                    "DELETE FROM files WHERE file_id = ?",
                    (file_id,)
                )
                
                deleted_count += 1
            
            logger.info(f"تم حذف {deleted_count} ملف قديم")
            return deleted_count
            
        except Exception as e:
            logger.error(f"خطأ في تنظيف الملفات القديمة: {str(e)}")
            return 0

# ============== النظام الرئيسي للبوت ==============
class YallaNataalamBot:
    """الفئة الرئيسية للبوت"""
    
    def __init__(self):
        self.db = AdvancedDatabase()
        self.ai = AdvancedAI()
        self.file_manager = FileManager(self.db)
        self.notification_system = NotificationSystem(self.db)
        self.statistics_system = StatisticsSystem(self.db)
        
        # حالات المستخدمين
        self.user_states = {}
        self.admin_states = {}
        self.conversation_states = {}
        
        # الخدمات وأسعارها
        self.services = {
            'exemption_calc': {
                'name': 'حساب درجة الإعفاء الفردي',
                'price': 1000,
                'active': True,
                'description': 'احسب معدلك وتأهل للإعفاء من المادة'
            },
            'pdf_summary': {
                'name': 'تلخيص الملازم بالذكاء الاصطناعي',
                'price': 1000,
                'active': True,
                'description': 'قم برفع ملف PDF واحصل على ملخص مفصل'
            },
            'ai_qa': {
                'name': 'سؤال وجواب بالذكاء الاصطناعي',
                'price': 1000,
                'active': True,
                'description': 'اسأل أي سؤال دراسي واحصل على إجابة دقيقة'
            },
            'help_student': {
                'name': 'ساعدوني طالب',
                'price': 1000,
                'active': True,
                'description': 'اطرح سؤالك وليجيب عليه الطلاب الآخرون'
            },
            'vip_subscription': {
                'name': 'اشتراك VIP شهري',
                'price': 5000,
                'active': True,
                'description': 'وصول كامل لمحاضرات VIP وخصائص حصرية'
            },
            'vip_lecture_upload': {
                'name': 'رفع محاضرة VIP',
                'price': 0,
                'active': True,
                'description': 'للمدرسين: رفع محاضرات فيديو للبيع'
            },
            'study_materials': {
                'name': 'تصفح المواد الدراسية',
                'price': 0,
                'active': True,
                'description': 'مواد وملازم دراسية مجانية'
            }
        }
        
        # إعدادات البوت
        self.settings = self._load_settings()
        
        # المجدولات
        self.jobs = {}
        
        logger.info("تم تهيئة بوت يلا نتعلم بنجاح")
    
    def _load_settings(self):
        """تحميل إعدادات البوت"""
        settings = {}
        rows = self.db.fetch_all("SELECT setting_key, setting_value FROM bot_settings")
        for key, value in rows:
            settings[key] = value
        return settings
    
    # ============== معالجات الأوامر ==============
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # تسجيل المستخدم
        await self._register_user(user)
        
        # إرسال رسالة الترحيب
        welcome_text = self._generate_welcome_message(user)
        
        keyboard = self._generate_main_keyboard(user.id)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # تحديث إحصائيات النشاط
        self._update_user_activity(user.id)
    
    async def _register_user(self, user):
        """تسجيل مستخدم جديد"""
        try:
            # التحقق من وجود المستخدم
            existing_user = self.db.fetch_one(
                "SELECT user_id FROM users WHERE user_id = ?",
                (user.id,)
            )
            
            if not existing_user:
                # إنشاء رمز دعوة فريد
                referral_code = hashlib.md5(f"{user.id}{time.time()}".encode()).hexdigest()[:8].upper()
                
                # تسجيل المستخدم الجديد
                self.db.execute_query('''
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, referral_code, balance, join_date, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.id,
                    user.username or "",
                    user.first_name or "",
                    user.last_name or "",
                    referral_code,
                    1000,  # هدية الترحيب
                    datetime.datetime.now(),
                    datetime.datetime.now()
                ))
                
                # إرسال إشعار للمدير
                await self._notify_admin_new_user(user)
                
                # منح إنجاز أول دخول
                self._grant_achievement(user.id, "first_login")
                
                logger.info(f"تم تسجيل مستخدم جديد: {user.id} - {user.username}")
            else:
                # تحديث آخر نشاط
                self.db.execute_query(
                    "UPDATE users SET last_active = ? WHERE user_id = ?",
                    (datetime.datetime.now(), user.id)
                )
                
        except Exception as e:
            logger.error(f"خطأ في تسجيل المستخدم: {str(e)}")
    
    def _generate_welcome_message(self, user):
        """إنشاء رسالة ترحيب"""
        user_data = self.db.fetch_one(
            "SELECT balance, referral_code FROM users WHERE user_id = ?",
            (user.id,)
        )
        
        balance = user_data[0] if user_data else 1000
        referral_code = user_data[1] if user_data else ""
        
        welcome = f"""
        🎓 *مرحباً بك في بوت "يلا نتعلم"* {user.first_name}!

        *✨ الخدمات التعليمية المتكاملة:*
        • حساب درجة الإعفاء الفردي
        • تلخيص الملازم بالذكاء الاصطناعي  
        • سؤال وجواب بأي مادة دراسية
        • منصة "ساعدوني طالب"
        • محاضرات VIP حصرية
        • ملازم ومرشحات مجانية

        *💰 معلومات حسابك:*
        • الرصيد الحالي: {balance} دينار
        • كود الدعوة: `{referral_code}`
        • لكل صديق تدعوه: 500 دينار

        *💵 للشحن:* تواصل مع {ADMIN_USERNAME}
        *📢 قناتنا:* {BOT_CHANNEL}

        *🎯 اختر الخدمة المناسبة لك:*
        """
        
        return welcome
    
    def _generate_main_keyboard(self, user_id):
        """إنشاء لوحة المفاتيح الرئيسية"""
        keyboard = []
        
        # عرض الرصيد
        user_data = self.db.fetch_one(
            "SELECT balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        balance = user_data[0] if user_data else 0
        
        keyboard.append([InlineKeyboardButton(
            f"💰 رصيدك: {balance} دينار", 
            callback_data="show_balance"
        )])
        
        # الخدمات المدفوعة
        for service_id, service in self.services.items():
            if service['active'] and service['price'] > 0:
                keyboard.append([InlineKeyboardButton(
                    f"{service['name']} - {service['price']} دينار",
                    callback_data=f"service_{service_id}"
                )])
        
        # الخدمات المجانية
        free_services = ['study_materials']
        for service_id in free_services:
            if self.services[service_id]['active']:
                keyboard.append([InlineKeyboardButton(
                    self.services[service_id]['name'],
                    callback_data=f"service_{service_id}"
                )])
        
        # قسم VIP
        keyboard.append([
            InlineKeyboardButton("🎓 محاضرات VIP", callback_data="vip_section"),
            InlineKeyboardButton("⭐ اشتراك VIP", callback_data="vip_subscribe")
        ])
        
        # روابط مهمة
        keyboard.append([
            InlineKeyboardButton("📢 قناة البوت", url=BOT_CHANNEL),
            InlineKeyboardButton("👨‍💻 الدعم", url=f"https://t.me/{SUPPORT_USERNAME}")
        ])
        
        # لوحة التحكم للمدير
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton(
                "👑 لوحة التحكم", 
                callback_data="admin_panel"
            )])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ============== نظام المعاملات ==============
    
    async def handle_service_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_id):
        """معالجة طلب خدمة"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        service = self.services.get(service_id)
        
        if not service or not service['active']:
            await query.edit_message_text(
                "⛔ هذه الخدمة غير متاحة حالياً",
                reply_markup=self._generate_main_keyboard(user_id)
            )
            return
        
        # التحقق من الرصيد للخدمات المدفوعة
        if service['price'] > 0:
            user_balance = self.db.fetch_one(
                "SELECT balance FROM users WHERE user_id = ?",
                (user_id,)
            )[0]
            
            if user_balance < service['price']:
                await query.edit_message_text(
                    f"❌ رصيدك غير كافي\n"
                    f"رصيدك الحالي: {user_balance} دينار\n"
                    f"سعر الخدمة: {service['price']} دينار\n\n"
                    f"للشحن تواصل مع {ADMIN_USERNAME}",
                    reply_markup=self._generate_main_keyboard(user_id)
                )
                return
        
        # معالجة كل خدمة حسب نوعها
        if service_id == 'exemption_calc':
            await self._handle_exemption_calc(query, user_id)
        elif service_id == 'pdf_summary':
            await self._handle_pdf_summary(query, user_id)
        elif service_id == 'ai_qa':
            await self._handle_ai_qa(query, user_id)
        elif service_id == 'help_student':
            await self._handle_help_student(query, user_id)
        elif service_id == 'vip_subscription':
            await self._handle_vip_subscription(query, user_id)
        elif service_id == 'study_materials':
            await self._handle_study_materials(query, user_id)
    
    async def _handle_exemption_calc(self, query, user_id):
        """معالجة حساب درجة الإعفاء"""
        self.user_states[user_id] = {
            'state': 'waiting_exemption_scores',
            'service': 'exemption_calc'
        }
        
        await query.edit_message_text(
            "📊 *حساب درجة الإعفاء الفردي*\n\n"
            "أدخل درجات الكورسات الثلاثة (مفصولة بمسافة)\n"
            "مثال: `85 90 95`\n\n"
            "ملاحظة: يجب أن يكون المعدل 90 أو أكثر للإعفاء",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_pdf_summary(self, query, user_id):
        """معالجة تلخيص PDF"""
        self.user_states[user_id] = {
            'state': 'waiting_pdf_file',
            'service': 'pdf_summary'
        }
        
        await query.edit_message_text(
            "📄 *تلخيص الملازم بالذكاء الاصطناعي*\n\n"
            "أرسل لي ملف PDF الآن وسأقوم بتلخيصه لك.\n\n"
            "الشروط:\n"
            "• الحد الأقصى: 50 صفحة\n"
            "• يجب أن يحتوي على نص قابل للقراءة\n"
            "• يدعم اللغة العربية والإنجليزية\n\n"
            "⏳ وقت المعالجة: 1-3 دقائق",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_ai_qa(self, query, user_id):
        """معالجة سؤال الذكاء الاصطناعي"""
        self.user_states[user_id] = {
            'state': 'waiting_ai_question',
            'service': 'ai_qa'
        }
        
        await query.edit_message_text(
            "🤖 *سؤال وجواب بالذكاء الاصطناعي*\n\n"
            "اسأل أي سؤال دراسي وسأجيب عليه.\n\n"
            "يمكنك السؤال عن:\n"
            "• أي مادة دراسية\n"
            "• حل مسائل وتمارين\n"
            "• شرح مفاهيم معقدة\n"
            "• استفسارات منهجية\n\n"
            "اكتب سؤالك الآن:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_help_student(self, query, user_id):
        """معالجة قسم ساعدوني طالب"""
        # عرض الأسئلة الحالية
        questions = self.db.fetch_all('''
            SELECT question_id, question_text, subject, price 
            FROM student_questions 
            WHERE is_answered = 0 AND is_approved = 1
            ORDER BY question_date DESC
            LIMIT 10
        ''')
        
        if not questions:
            await query.edit_message_text(
                "📝 *ساعدوني طالب*\n\n"
                "لا توجد أسئلة حالياً.\n\n"
                "يمكنك:\n"
                "1. طرح سؤال جديد (1000 دينار)\n"
                "2. تصفح الأسئلة المجابة\n\n"
                "اختر الخيار المناسب:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._generate_help_student_keyboard()
            )
            return
        
        # عرض قائمة الأسئلة
        questions_text = "📝 *الأسئلة الحالية:*\n\n"
        buttons = []
        
        for q_id, q_text, subject, price in questions:
            short_text = q_text[:50] + "..." if len(q_text) > 50 else q_text
            questions_text += f"• {subject} - {short_text} ({price} دينار)\n"
            buttons.append([
                InlineKeyboardButton(
                    f"{subject}: {short_text}",
                    callback_data=f"view_question_{q_id}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton("➕ طرح سؤال جديد", callback_data="ask_new_question"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
        ])
        
        await query.edit_message_text(
            questions_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    async def _handle_vip_subscription(self, query, user_id):
        """معالجة اشتراك VIP"""
        # التحقق من وجود اشتراك فعال
        vip_sub = self.db.fetch_one('''
            SELECT * FROM vip_subscriptions 
            WHERE user_id = ? AND is_active = 1 AND end_date > ?
        ''', (user_id, datetime.datetime.now()))
        
        if vip_sub:
            # المستخدم مشترك بالفعل
            end_date = datetime.datetime.strptime(vip_sub[3], "%Y-%m-%d %H:%M:%S")
            remaining_days = (end_date - datetime.datetime.now()).days
            
            await query.edit_message_text(
                f"⭐ *اشتراك VIP الحالي*\n\n"
                f"أنت مشترك في VIP حتى:\n"
                f"📅 {end_date.strftime('%Y-%m-%d')}\n"
                f"⏳ متبقي: {remaining_days} يوم\n\n"
                f"مزايا اشتراكك:\n"
                f"• رفع محاضرات فيديو\n"
                f"• 60% أرباح من المبيعات\n"
                f"• وصول كامل للمحاضرات\n"
                f"• دعم فني متميز",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._generate_vip_management_keyboard()
            )
        else:
            # عرض خطط الاشتراك
            await query.edit_message_text(
                "⭐ *اشتراك VIP الشهري*\n\n"
                "بـ 5000 دينار شهرياً تحصل على:\n\n"
                "🎓 *للمدرسين:*\n"
                "• رفع محاضرات فيديو غير محدود\n"
                "• 60% أرباح من كل عملية بيع\n"
                "• لوحة تحكم متقدمة\n"
                "• إحصائيات مفصلة\n\n"
                "📚 *للطلاب:*\n"
                "• وصول كامل لجميع المحاضرات\n"
                "• خصم 20% على المشتريات\n"
                "• دعم فني متميز\n"
                "• محتوى حصري\n\n"
                "💵 *طريقة الدفع:*\n"
                "تواصل مع المدير للدفع والتفعيل",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._generate_vip_subscription_keyboard()
            )
    
    async def _handle_study_materials(self, query, user_id):
        """معالجة قسم المواد الدراسية"""
        # عرض فئات المواد
        categories = self.db.fetch_all('''
            SELECT DISTINCT grade FROM study_materials 
            WHERE is_approved = 1
            ORDER BY grade
        ''')
        
        if not categories:
            await query.edit_message_text(
                "📚 *ملازمي ومرشحاتي*\n\n"
                "لا توجد مواد حالياً.\n\n"
                "سيتم إضافة المواد قريباً...",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
                ]])
            )
            return
        
        buttons = []
        for grade, in categories:
            buttons.append([
                InlineKeyboardButton(f"📂 {grade}", callback_data=f"materials_grade_{grade}")
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
        ])
        
        await query.edit_message_text(
            "📚 *اختر المرحلة الدراسية:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # ============== معالجة الرسائل ==============
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # التحقق من حالة المستخدم
        user_state = self.user_states.get(user_id)
        
        if user_state:
            await self._process_user_state(update, context, user_state, message_text)
            return
        
        # إذا كان المستخدم مديراً وفي وضع الإدارة
        if user_id == ADMIN_ID and user_id in self.admin_states:
            await self._process_admin_state(update, context, message_text)
            return
        
        # الرد العام
        await update.message.reply_text(
            "👋 أهلاً! استخدم الأزرار في القائمة للتفاعل مع البوت.\n"
            "أو اكتب /start لعرض القائمة الرئيسية.",
            reply_markup=self._generate_main_keyboard(user_id)
        )
    
    async def _process_user_state(self, update, context, user_state, message_text):
        """معالجة حالة المستخدم"""
        user_id = update.effective_user.id
        state = user_state.get('state')
        service = user_state.get('service')
        
        if state == 'waiting_exemption_scores':
            await self._process_exemption_scores(update, user_id, message_text)
        
        elif state == 'waiting_ai_question':
            await self._process_ai_question(update, user_id, message_text)
        
        elif state == 'waiting_help_student_question':
            await self._process_help_student_question(update, user_id, message_text)
        
        # حذف حالة المستخدم بعد المعالجة
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def _process_exemption_scores(self, update, user_id, message_text):
        """معالجة درجات الإعفاء"""
        try:
            # تحليل الدرجات
            scores = list(map(float, message_text.split()))
            
            if len(scores) != 3:
                await update.message.reply_text(
                    "❌ يرجى إدخال 3 درجات فقط مفصولة بمسافة\n"
                    "مثال: `85 90 95`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # حساب المعدل
            average = sum(scores) / 3
            
            # التحقق من الرصيد وخصم السعر
            service_price = self.services['exemption_calc']['price']
            if not self._deduct_balance(user_id, service_price, "حساب درجة الإعفاء"):
                await update.message.reply_text(
                    f"❌ رصيدك غير كافي\n"
                    f"السعر: {service_price} دينار",
                    reply_markup=self._generate_main_keyboard(user_id)
                )
                return
            
            # عرض النتيجة
            if average >= 90:
                result_text = f"""
                🎉 *مبروك! أنت معفي من المادة* 🎊

                *الدرجات المدخلة:* {scores[0]}, {scores[1]}, {scores[2]}
                *المعدل العام:* {average:.2f}
                *التقدير:* امتياز

                ✅ تهانينا! لقد حققت المعدل المطلوب للإعفاء.
                """
            else:
                result_text = f"""
                ⚠️ *للأسف أنت غير معفي*

                *الدرجات المدخلة:* {scores[0]}, {scores[1]}, {scores[2]}
                *المعدل العام:* {average:.2f}
                *النسبة المطلوبة:* 90

                📝 *نصيحة:*
                تحتاج لتحسين درجاتك بمقدار {90 - average:.2f} نقطة.
                ركز على المواد التي يمكنك تحسينها.
                """
            
            await update.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._generate_main_keyboard(user_id)
            )
            
            # تسجيل الإنجاز
            self._grant_achievement(user_id, "exemption_calculated")
            
        except ValueError:
            await update.message.reply_text(
                "❌ يرجى إدخال أرقام صحيحة فقط\n"
                "مثال: `85 90 95`",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"خطأ في معالجة درجات الإعفاء: {str(e)}")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء معالجة درجاتك",
                reply_markup=self._generate_main_keyboard(user_id)
            )
    
    async def _process_ai_question(self, update, user_id, message_text):
        """معالجة سؤال الذكاء الاصطناعي"""
        # التحقق من الرصيد وخصم السعر
        service_price = self.services['ai_qa']['price']
        if not self._deduct_balance(user_id, service_price, "سؤال الذكاء الاصطناعي"):
            await update.message.reply_text(
                f"❌ رصيدك غير كافي\n"
                f"السعر: {service_price} دينار",
                reply_markup=self._generate_main_keyboard(user_id)
            )
            return
        
        # إرسال رسالة الانتظار
        wait_msg = await update.message.reply_text(
            "⏳ *جاري معالجة سؤالك...*\n"
            "قد يستغرق الأمر بضع ثوانٍ",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # الحصول على إجابة من الذكاء الاصطناعي
            answer = await self.ai.answer_question(message_text)
            
            # إرسال الإجابة
            await wait_msg.edit_text(
                answer,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # تسجيل الإنجاز
            self._grant_achievement(user_id, "ai_question_asked")
            
        except Exception as e:
            logger.error(f"خطأ في معالجة سؤال الذكاء الاصطناعي: {str(e)}")
            await wait_msg.edit_text(
                "❌ حدث خطأ أثناء معالجة سؤالك\n"
                "يرجى المحاولة مرة أخرى لاحقاً",
                reply_markup=self._generate_main_keyboard(user_id)
            )
    
    # ============== معالجة المستندات ==============
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الملفات المرسلة"""
        user_id = update.effective_user.id
        document = update.message.document
        
        # التحقق من حالة المستخدم
        user_state = self.user_states.get(user_id)
        
        if user_state and user_state.get('state') == 'waiting_pdf_file':
            await self._process_pdf_file(update, user_id, document)
        else:
            await update.message.reply_text(
                "📁 أرسلت لي ملفاً!\n"
                "لكن لا يوجد طلب نشط لمعالجة الملفات.\n\n"
                "استخدم /start للعودة للقائمة الرئيسية.",
                reply_markup=self._generate_main_keyboard(user_id)
            )
    
    async def _process_pdf_file(self, update, user_id, document):
        """معالجة ملف PDF للتلخيص"""
        # التحقق من نوع الملف
        if not document.mime_type == 'application/pdf':
            await update.message.reply_text(
                "❌ يرجى إرسال ملف PDF فقط",
                reply_markup=self._generate_main_keyboard(user_id)
            )
            return
        
        # التحقق من حجم الملف (حد أقصى 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await update.message.reply_text(
                "❌ حجم الملف كبير جداً\n"
                "الحد الأقصى: 20 ميجابايت",
                reply_markup=self._generate_main_keyboard(user_id)
            )
            return
        
        # التحقق من الرصيد وخصم السعر
        service_price = self.services['pdf_summary']['price']
        if not self._deduct_balance(user_id, service_price, "تلخيص ملف PDF"):
            await update.message.reply_text(
                f"❌ رصيدك غير كافي\n"
                f"السعر: {service_price} دينار",
                reply_markup=self._generate_main_keyboard(user_id)
            )
            return
        
        # إرسال رسالة الانتظار
        wait_msg = await update.message.reply_text(
            "⏳ *جاري معالجة الملف...*\n"
            "قد يستغرق الأمر 1-3 دقائق",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # تحميل الملف
            file = await document.get_file()
            file_bytes = io.BytesIO()
            await file.download_to_memory(file_bytes)
            
            # تلخيص الملف
            summary = await self.ai.summarize_pdf(file_bytes.getvalue())
            
            # إرسال الملخص
            if len(summary) > 4000:
                # إذا كان الملخص طويلاً، نقسمه
                parts = [summary[i:i+4000] for i in range(0, len(summary), 4000)]
                for i, part in enumerate(parts):
                    await update.message.reply_text(
                        f"📄 *الجزء {i+1} من {len(parts)}*\n\n{part}",
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                await wait_msg.edit_text(
                    summary,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # تسجيل الإنجاز
            self._grant_achievement(user_id, "pdf_summarized")
            
        except Exception as e:
            logger.error(f"خطأ في معالجة ملف PDF: {str(e)}")
            await wait_msg.edit_text(
                "❌ حدث خطأ أثناء معالجة الملف\n"
                "يرجى التأكد أن الملف يحتوي على نص قابل للقراءة",
                reply_markup=self._generate_main_keyboard(user_id)
            )
    
    # ============== نظام الرصيد والمعاملات ==============
    
    def _deduct_balance(self, user_id, amount, description):
        """خصم مبلغ من رصيد المستخدم"""
        try:
            # التحقق من الرصيد
            user_data = self.db.fetch_one(
                "SELECT balance FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user_data or user_data[0] < amount:
                return False
            
            # الخصم
            self.db.execute_query(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # تسجيل المعاملة
            self.db.execute_query('''
                INSERT INTO transactions 
                (user_id, amount, type, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, -amount, 'purchase', description))
            
            # تحديث إحصائيات الإنفاق
            self.db.execute_query(
                "UPDATE users SET total_spent = total_spent + ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            logger.info(f"تم خصم {amount} دينار من المستخدم {user_id}: {description}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في خصم الرصيد: {str(e)}")
            return False
    
    def _add_balance(self, user_id, amount, description):
        """إضافة مبلغ لرصيد المستخدم"""
        try:
            # الإضافة
            self.db.execute_query(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # تسجيل المعاملة
            self.db.execute_query('''
                INSERT INTO transactions 
                (user_id, amount, type, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, 'deposit', description))
            
            # تحديث إحصائيات الإيداع
            self.db.execute_query(
                "UPDATE users SET total_earned = total_earned + ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # إرسال إشعار للمستخدم
            self._send_notification(
                user_id,
                f"💰 تم إضافة {amount} دينار إلى رصيدك\n"
                f"السبب: {description}"
            )
            
            logger.info(f"تم إضافة {amount} دينار للمستخدم {user_id}: {description}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إضافة الرصيد: {str(e)}")
            return False
    
    def _send_notification(self, user_id, message):
        """إرسال إشعار للمستخدم"""
        try:
            self.db.execute_query('''
                INSERT INTO notifications 
                (user_id, message, notification_type)
                VALUES (?, ?, ?)
            ''', (user_id, message, 'system'))
        except Exception as e:
            logger.error(f"خطأ في إرسال الإشعار: {str(e)}")
    
    # ============== نظام الإنجازات ==============
    
    def _grant_achievement(self, user_id, achievement_type):
        """منح إنجاز للمستخدم"""
        try:
            # التحقق من عدم منح الإنجاز مسبقاً
            existing = self.db.fetch_one(
                "SELECT achievement_id FROM achievements WHERE user_id = ? AND achievement_type = ?",
                (user_id, achievement_type)
            )
            
            if existing:
                return
            
            # تعريف الإنجازات
            achievements_def = {
                "first_login": {
                    "title": "المستخدم الجديد",
                    "points": 100,
                    "level": "bronze"
                },
                "exemption_calculated": {
                    "title": "حساب الإعفاء",
                    "points": 50,
                    "level": "bronze"
                },
                "pdf_summarized": {
                    "title": "ملخص الوثائق",
                    "points": 100,
                    "level": "silver"
                },
                "ai_question_asked": {
                    "title": "باحث ذكي",
                    "points": 50,
                    "level": "bronze"
                },
                "vip_subscriber": {
                    "title": "عضو VIP",
                    "points": 500,
                    "level": "gold"
                }
            }
            
            achievement = achievements_def.get(achievement_type)
            if not achievement:
                return
            
            # إضافة الإنجاز
            self.db.execute_query('''
                INSERT INTO achievements 
                (user_id, achievement_type, achievement_level, points_awarded, title_awarded)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                achievement_type,
                achievement['level'],
                achievement['points'],
                achievement['title']
            ))
            
            # إضافة النقاط
            self.db.execute_query(
                "UPDATE users SET points = points + ? WHERE user_id = ?",
                (achievement['points'], user_id)
            )
            
            # إرسال إشعار
            self._send_notification(
                user_id,
                f"🏆 مبروك! لقد حصلت على إنجاز:\n"
                f"{achievement['title']}\n"
                f"+{achievement['points']} نقطة"
            )
            
            logger.info(f"تم منح إنجاز {achievement_type} للمستخدم {user_id}")
            
        except Exception as e:
            logger.error(f"خطأ في منح الإنجاز: {str(e)}")
    
    # ============== نظام الإدارة ==============
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض لوحة تحكم المدير"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await query.edit_message_text(
                "⛔ غير مصرح لك بالوصول لهذه الصفحة",
                reply_markup=self._generate_main_keyboard(user_id)
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("💰 الشحن والخصم", callback_data="admin_finance")],
            [InlineKeyboardButton("🚫 حظر/رفع حظر", callback_data="admin_ban")],
            [InlineKeyboardButton("⚙️ إعدادات الخدمات", callback_data="admin_services")],
            [InlineKeyboardButton("📚 المواد الدراسية", callback_data="admin_materials")],
            [InlineKeyboardButton("🎓 إدارة VIP", callback_data="admin_vip")],
            [InlineKeyboardButton("📣 الإذاعة", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            "👑 *لوحة تحكم المدير*\n\n"
            "اختر القسم الذي تريد إدارته:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات المدير"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            return
        
        # جمع الإحصائيات
        stats = self.statistics_system.get_overall_stats()
        
        stats_text = f"""
        📊 *إحصائيات البوت الشاملة*

        *👥 المستخدمين:*
        • إجمالي المستخدمين: {stats['total_users']:,}
        • المستخدمين النشطين: {stats['active_users']:,}
        • مشتركين VIP: {stats['vip_users']:,}
        • المدرسين: {stats['teachers']:,}
        • المشرفين: {stats['admins']:,}

        *💰 المالية:*
        • إجمالي الأرصدة: {stats['total_balance']:,} دينار
        • إجمالي الدخل: {stats['total_income']:,} دينار
        • إجمالي السحوبات: {stats['total_withdrawals']:,} دينار
        • المعاملات اليوم: {stats['today_transactions']:,}

        *📚 المحتوى:*
        • المحاضرات: {stats['total_lectures']:,}
        • الأسئلة: {stats['total_questions']:,}
        • المجاب منها: {stats['answered_questions']:,}
        • المواد الدراسية: {stats['total_materials']:,}

        *📈 النشاط:*
        • نشطون أسبوعياً: {stats['weekly_active']:,}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="admin_stats")],
            [InlineKeyboardButton("📈 تقرير مفصل", callback_data="admin_detailed_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_charge_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شحن رصيد مستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            return
        
        self.admin_states[user_id] = {
            'action': 'charge_user',
            'step': 'get_user_id'
        }
        
        await query.edit_message_text(
            "💰 *شحن رصيد مستخدم*\n\n"
            "أرسل ID المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_deduct_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """خصم رصيد مستخدم"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            return
        
        self.admin_states[user_id] = {
            'action': 'deduct_user',
            'step': 'get_user_id'
        }
        
        await query.edit_message_text(
            "➖ *خصم رصيد مستخدم*\n\n"
            "أرسل ID المستخدم:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _process_admin_state(self, update, context, message_text):
        """معالجة حالة المدير"""
        user_id = update.effective_user.id
        admin_state = self.admin_states.get(user_id)
        
        if not admin_state:
            return
        
        action = admin_state['action']
        step = admin_state['step']
        
        if action == 'charge_user':
            if step == 'get_user_id':
                try:
                    target_user_id = int(message_text)
                    admin_state['target_user_id'] = target_user_id
                    admin_state['step'] = 'get_amount'
                    
                    await update.message.reply_text(
                        f"المستخدم: {target_user_id}\n"
                        f"أدخل المبلغ للشحن:",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ يرجى إدخال رقم ID صحيح"
                    )
            
            elif step == 'get_amount':
                try:
                    amount = int(message_text)
                    target_user_id = admin_state['target_user_id']
                    
                    if amount <= 0:
                        await update.message.reply_text(
                            "❌ المبلغ يجب أن يكون أكبر من صفر"
                        )
                        return
                    
                    # شحن الرصيد
                    success = self._add_balance(
                        target_user_id,
                        amount,
                        f"شحن من المدير {user_id}"
                    )
                    
                    if success:
                        await update.message.reply_text(
                            f"✅ تم شحن {amount:,} دينار للمستخدم {target_user_id}",
                            reply_markup=self._generate_admin_keyboard()
                        )
                    else:
                        await update.message.reply_text(
                            "❌ فشل عملية الشحن",
                            reply_markup=self._generate_admin_keyboard()
                        )
                    
                    # حذف حالة المدير
                    del self.admin_states[user_id]
                    
                except ValueError:
                    await update.message.reply_text(
                        "❌ يرجى إدخال مبلغ صحيح"
                    )
        
        elif action == 'deduct_user':
            if step == 'get_user_id':
                try:
                    target_user_id = int(message_text)
                    admin_state['target_user_id'] = target_user_id
                    admin_state['step'] = 'get_amount'
                    
                    await update.message.reply_text(
                        f"المستخدم: {target_user_id}\n"
                        f"أدخل المبلغ للخصم:",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ يرجى إدخال رقم ID صحيح"
                    )
            
            elif step == 'get_amount':
                try:
                    amount = int(message_text)
                    target_user_id = admin_state['target_user_id']
                    
                    if amount <= 0:
                        await update.message.reply_text(
                            "❌ المبلغ يجب أن يكون أكبر من صفر"
                        )
                        return
                    
                    # الخصم
                    success = self._deduct_balance(
                        target_user_id,
                        amount,
                        f"خصم من المدير {user_id}"
                    )
                    
                    if success:
                        await update.message.reply_text(
                            f"✅ تم خصم {amount:,} دينار من المستخدم {target_user_id}",
                            reply_markup=self._generate_admin_keyboard()
                        )
                    else:
                        await update.message.reply_text(
                            "❌ فشل عملية الخصم (رصيد غير كافي)",
                            reply_markup=self._generate_admin_keyboard()
                        )
                    
                    # حذف حالة المدير
                    del self.admin_states[user_id]
                    
                except ValueError:
                    await update.message.reply_text(
                        "❌ يرجى إدخال مبلغ صحيح"
                    )
    
    def _generate_admin_keyboard(self):
        """إنشاء لوحة مفاتيح المدير"""
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("💰 الشحن والخصم", callback_data="admin_finance")],
            [InlineKeyboardButton("⚙️ إعدادات الخدمات", callback_data="admin_services")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ============== أدوات مساعدة ==============
    
    def _update_user_activity(self, user_id):
        """تحديث نشاط المستخدم"""
        try:
            self.db.execute_query(
                "UPDATE users SET last_active = ?, session_count = session_count + 1 WHERE user_id = ?",
                (datetime.datetime.now(), user_id)
            )
        except Exception as e:
            logger.error(f"خطأ في تحديث نشاط المستخدم: {str(e)}")
    
    async def _notify_admin_new_user(self, user):
        """إشعار المدير بمستخدم جديد"""
        try:
            notification = f"""
            👤 *مستخدم جديد*
            
            الاسم: {user.first_name} {user.last_name or ''}
            اليوزر: @{user.username or 'بدون'}
            الايدي: {user.id}
            التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self._send_notification(ADMIN_ID, notification)
            
        except Exception as e:
            logger.error(f"خطأ في إشعار المدير: {str(e)}")
    
    def _generate_help_student_keyboard(self):
        """إنشاء لوحة مفاتيح قسم ساعدوني طالب"""
        keyboard = [
            [InlineKeyboardButton("➕ طرح سؤال جديد", callback_data="ask_new_question")],
            [InlineKeyboardButton("📝 الأسئلة المجابة", callback_data="answered_questions")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _generate_vip_management_keyboard(self):
        """إنشاء لوحة مفاتيح إدارة VIP"""
        keyboard = [
            [InlineKeyboardButton("📹 رفع محاضرة", callback_data="upload_lecture")],
            [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_vip_stats")],
            [InlineKeyboardButton("💰 أرباحي", callback_data="my_earnings")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _generate_vip_subscription_keyboard(self):
        """إنشاء لوحة مفاتيح اشتراك VIP"""
        keyboard = [
            [InlineKeyboardButton("💳 اشترك الآن", callback_data="subscribe_vip_now")],
            [InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="vip_faq")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ============== دوال التشغيل ==============
    
    async def run(self):
        """تشغيل البوت"""
        # إنشاء التطبيق
        app = ApplicationBuilder().token(TOKEN).build()
        
        # إضافة المعالجات
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("admin", self.show_admin_panel))
        
        # معالجات الردود
        app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # معالجة المستندات
        app.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        
        # معالجة الرسائل النصية
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # معالجة الأخطاء
        app.add_error_handler(self._error_handler)
        
        # بدء المهام المجدولة
        self._start_scheduled_tasks(app)
        
        # تشغيل البوت
        logger.info("🚀 بدأ تشغيل بوت يلا نتعلم...")
        await app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة جميع الردود"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        # معالجة الأوامر العامة
        if data == "back_to_main":
            await self.start_command(update, context)
        
        elif data == "admin_panel":
            await self.show_admin_panel(update, context)
        
        elif data == "admin_stats":
            await self.show_admin_stats(update, context)
        
        elif data == "admin_finance":
            await self._show_admin_finance_panel(update, context)
        
        # معالجة الخدمات
        elif data.startswith("service_"):
            service_id = data.split("_", 1)[1]
            await self.handle_service_request(update, context, service_id)
        
        # معالجة أقسام VIP
        elif data == "vip_section":
            await self._show_vip_section(update, context)
        
        elif data == "vip_subscribe":
            await self._handle_vip_subscription(update, context)
        
        # معالجة قسم المواد الدراسية
        elif data.startswith("materials_grade_"):
            grade = data.split("_", 2)[2]
            await self._show_grade_materials(update, context, grade)
    
    async def _show_admin_finance_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض لوحة التحكم المالية"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ شحن رصيد", callback_data="admin_charge")],
            [InlineKeyboardButton("➖ خصم رصيد", callback_data="admin_deduct")],
            [InlineKeyboardButton("📊 تقرير مالي", callback_data="admin_financial_report")],
            [InlineKeyboardButton("💰 سحب أرباح مدرس", callback_data="admin_teacher_withdraw")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            "💰 *لوحة التحكم المالية*\n\n"
            "اختر العملية المالية التي تريد تنفيذها:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _show_vip_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قسم VIP"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # التحقق من اشتراك VIP
        is_vip = self.db.fetch_one('''
            SELECT 1 FROM vip_subscriptions 
            WHERE user_id = ? AND is_active = 1 AND end_date > ?
        ''', (user_id, datetime.datetime.now()))
        
        if is_vip:
            # للمستخدمين المشتركين
            keyboard = [
                [InlineKeyboardButton("📹 رفع محاضرة", callback_data="vip_upload_lecture")],
                [InlineKeyboardButton("📊 محاضراتي", callback_data="vip_my_lectures")],
                [InlineKeyboardButton("💰 أرباحي", callback_data="vip_my_earnings")],
                [InlineKeyboardButton("🎓 تصفح المحاضرات", callback_data="vip_browse_lectures")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
            ]
            
            text = "⭐ *قسم VIP - أنت مشترك*\n\n"
            text += "اختر الخدمة التي تريدها:"
        
        else:
            # للمستخدمين غير المشتركين
            keyboard = [
                [InlineKeyboardButton("💳 اشترك في VIP", callback_data="vip_subscribe")],
                [InlineKeyboardButton("🎓 تصفح المحاضرات", callback_data="vip_browse_lectures")],
                [InlineKeyboardButton("❓ لماذا VIP؟", callback_data="vip_why")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
            ]
            
            text = "⭐ *قسم VIP*\n\n"
            text += "للوصول الكامل للمحاضرات الحصرية والمزايا الخاصة، اشترك في VIP!"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _show_grade_materials(self, update: Update, context: ContextTypes.DEFAULT_TYPE, grade):
        """عرض مواد مرحلة دراسية معينة"""
        query = update.callback_query
        await query.answer()
        
        materials = self.db.fetch_all('''
            SELECT material_id, title, description, download_count 
            FROM study_materials 
            WHERE grade = ? AND is_approved = 1
            ORDER BY upload_date DESC
            LIMIT 20
        ''', (grade,))
        
        if not materials:
            await query.edit_message_text(
                f"📚 *مواد {grade}*\n\n"
                f"لا توجد مواد لهذه المرحلة حالياً.\n"
                f"سيتم إضافتها قريباً...",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع للمراحل", callback_data="service_study_materials")
                ]])
            )
            return
        
        # إنشاء قائمة المواد
        buttons = []
        for material_id, title, description, downloads in materials:
            short_title = title[:30] + "..." if len(title) > 30 else title
            short_desc = description[:40] + "..." if description and len(description) > 40 else description or "لا يوجد وصف"
            
            button_text = f"{short_title}\n{short_desc} ({downloads} ⬇️)"
            buttons.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"view_material_{material_id}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 رجوع للمراحل", callback_data="service_study_materials")
        ])
        
        await query.edit_message_text(
            f"📚 *مواد {grade}*\n\n"
            f"اختر المادة التي تريد تحميلها:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    def _start_scheduled_tasks(self, app):
        """بدء المهام المجدولة"""
        
        async def update_stats(context: ContextTypes.DEFAULT_TYPE):
            """تحديث الإحصائيات اليومية"""
            try:
                self.statistics_system.update_daily_stats()
                
                # تنظيف الملفات القديمة أسبوعياً
                if datetime.datetime.now().weekday() == 0:  # كل إثنين
                    self.file_manager.cleanup_old_files(30)
                
                # نسخ احتياطي يومي (سيتم تنفيذه تلقائياً من قاعدة البيانات)
                
            except Exception as e:
                logger.error(f"خطأ في المهمة المجدولة: {str(e)}")
        
        # جدولة المهمة كل 6 ساعات
        app.job_queue.run_repeating(update_stats, interval=21600, first=10)
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء"""
        logger.error(f"حدث خطأ: {context.error}")
        
        try:
            if update and update.effective_user:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.\n"
                         "إذا استمر الخطأ، تواصل مع الدعم الفني.",
                    reply_markup=self._generate_main_keyboard(update.effective_user.id)
                )
        except:
            pass

# ============== الدالة الرئيسية ==============
async def main():
    """الدالة الرئيسية لتشغيل البرنامج"""
    try:
        # إنشاء مجلدات التخزين
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("backups", exist_ok=True)
        os.makedirs("fonts", exist_ok=True)
        
        # تهيئة الخطوط العربية
        setup_arabic_fonts()
        
        # إنشاء وتشغيل البوت
        bot = YallaNataalamBot()
        await bot.run()
        
    except Exception as e:
        logger.error(f"خطأ فادح في تشغيل البوت: {str(e)}")
        raise

def setup_arabic_fonts():
    """تجهيز الخطوط العربية لملفات PDF"""
    try:
        # هذه دالة افتراضية، في التطبيق الفعلي تحتاج إلى توفير ملفات الخطوط
        pdfmetrics.registerFont(TTFont('Arabic', 'fonts/arial.ttf'))
    except:
        logger.warning("تعذر تحميل الخطوط العربية. سيتم استخدام الخط الافتراضي.")

if __name__ == "__main__":
    # تشغيل البوت
    asyncio.run(main())
