#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                    بوت الحارس الذكي لحماية القنوات - النسخة العملاقة المتكاملة
#                                        Smart Guardian Channel Protection Bot
#                                             Version: 20.0.0 | Build: 2025
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

import asyncio
import logging
import json
import os
import re
import pickle
import secrets
import time
import traceback
import sys
import shutil
import random
import string
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from functools import wraps
from collections import defaultdict, deque

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters,
    ChatMemberHandler
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, TelegramError

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           إعدادات النظام المركزية
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

class GuardianConfig:
    """
    إعدادات النظام المركزية لبوت تفاعلكم الذكي
    
    هذا الكلاس يحتوي على جميع الثوابت والإعدادات الأساسية التي يعتمد عليها البوت
    في جميع عملياته. تم تجميعها هنا لتسهيل عملية التعديل والصيانة.
    """
    
    # ═══════════════════════════ معلومات البوت الأساسية ═══════════════════════════
    BOT_TOKEN: str = "8682323172:AAFYWlT7EQQmCBjQVk4BzBSdnVCXK1lR07A"
    BOT_USERNAME: str = "protGebot"
    
    # ═══════════════════════════ معلومات المدير الرئيسي ═══════════════════════════
    MASTER_ADMIN_ID: int = 6130994941
    MASTER_ADMIN_USERNAME: str = "Allawi04"
    
    # ═══════════════════════════ حدود القنوات والاشتراكات ═══════════════════════════
    FREE_CHANNELS_LIMIT: int = 2
    VIP_CHANNELS_LIMIT: int = 10
    FREE_TRIAL_DAYS: int = 14
    VIP_DURATION_DAYS: int = 30
    
    # ═══════════════════════════ الإعدادات المالية ═══════════════════════════
    DEFAULT_VIP_PRICE: int = 5000
    VIP_DISCOUNT_PERCENT: int = 15
    VIP_BONUS_PERCENT: int = 10
    FUNDING_PRICE_PER_MEMBER: int = 20
    SUBSCRIBE_REWARD_AMOUNT: int = 25
    INVITER_REWARD_AMOUNT: int = 150
    INVITED_REWARD_AMOUNT: int = 50
    
    # ═══════════════════════════ إعدادات التحويل ═══════════════════════════
    MAX_TRANSFER_AMOUNT: int = 50000
    TRANSFER_COOLDOWN_HOURS: int = 24
    
    # ═══════════════════════════ إعدادات الملفات والمجلدات ═══════════════════════════
    DATABASE_FILE: str = "guardian_database.pkl"
    SETTINGS_FILE: str = "guardian_settings.json"
    BACKUP_FOLDER: str = "guardian_backups"
    TEMP_FOLDER: str = "guardian_temp"
    LOG_FOLDER: str = "guardian_logs"
    QR_FOLDER: str = "guardian_qrcodes"
    
    # ═══════════════════════════ إعدادات الواجهة ═══════════════════════════
    CHANNELS_PER_PAGE: int = 5
    AUTO_BAN_DAYS: int = 1000
    
    # ═══════════════════════════ إعدادات الكابتشا والأمان ═══════════════════════════
    CAPTCHA_MAX_ATTEMPTS: int = 4
    CAPTCHA_BAN_MINUTES: int = 15
    CAPTCHA_CODE_LENGTH: int = 6
    
    # ═══════════════════════════ إعدادات VIP المتقدمة ═══════════════════════════
    VIP_AUTO_RENEW_DAYS_BEFORE: int = 1

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           حالات المحادثة
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

# الحالات الأساسية
STATE_WAIT_CHANNEL_LINK = 1
STATE_WAIT_CHARGE_USER = 2
STATE_WAIT_CHARGE_AMOUNT = 3
STATE_WAIT_FORCE_CHANNEL = 4
STATE_WAIT_FORCE_COUNT = 5
STATE_WAIT_BROADCAST = 6
STATE_WAIT_VIP_PRICE = 7
STATE_WAIT_TRIAL_DAYS = 8
STATE_WAIT_BACKUP_FILE = 9
STATE_WAIT_FUNDING_CHANNEL = 10
STATE_WAIT_FUNDING_COUNT = 11
STATE_WAIT_REPORT_REASON = 12
STATE_WAIT_INVITER_REWARD = 13
STATE_WAIT_INVITED_REWARD = 14
STATE_WAIT_SUBSCRIBE_REWARD = 15
STATE_WAIT_FUNDING_PRICE = 16
STATE_WAIT_GIFT_USES = 17
STATE_WAIT_GIFT_AMOUNT = 18
STATE_WAIT_BAN_USER = 19
STATE_WAIT_UNBAN_USER = 20
STATE_WAIT_BAN_REASON = 21
STATE_WAIT_DELETE_USER = 22
STATE_WAIT_SEARCH_USER = 23
STATE_WAIT_SEND_MESSAGE_USER = 24
STATE_WAIT_SEND_MESSAGE_TEXT = 25
STATE_WAIT_PROMOTE_ADMIN = 26
STATE_WAIT_DEMOTE_ADMIN = 27

# حالات الخدمات والأقسام
STATE_WAIT_SERVICE_CATEGORY_NAME = 28
STATE_WAIT_SERVICE_CATEGORY_DESC = 29
STATE_WAIT_SERVICE_NAME = 30
STATE_WAIT_SERVICE_DESC = 31
STATE_WAIT_SERVICE_PRICE = 33
STATE_WAIT_SERVICE_DURATION = 34
STATE_WAIT_SERVICE_MIN = 35
STATE_WAIT_SERVICE_MAX = 36
STATE_WAIT_SERVICE_QUANTITY = 37
STATE_WAIT_SERVICE_LINK = 38
STATE_WAIT_BUTTON_NEW_NAME = 39

# حالات الخصم والشحن الجماعي
STATE_WAIT_DEDUCT_ALL_AMOUNT = 40
STATE_WAIT_DEDUCT_ALL_MESSAGE = 41
STATE_WAIT_CHARGE_ALL_AMOUNT = 42
STATE_WAIT_CHARGE_ALL_MESSAGE = 43
STATE_WAIT_DEDUCT_USER = 44
STATE_WAIT_DEDUCT_AMOUNT = 45

# حالات جديدة للإصدار 20.0.0
STATE_WAIT_WELCOME_MESSAGE = 46
STATE_WAIT_CANCEL_VIP_USER = 47
STATE_WAIT_RENAME_CATEGORY = 48
STATE_WAIT_RENAME_SERVICE = 49
STATE_WAIT_TRANSFER_TARGET = 50
STATE_WAIT_TRANSFER_AMOUNT = 51
STATE_WAIT_CAPTCHA_CODE = 52

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           نظام التسجيل
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def setup_logging():
    """
    إعداد نظام التسجيل للبوت
    
    تقوم هذه الدالة بإنشاء مجلد السجلات إذا لم يكن موجوداً،
    وتقوم بإعداد نظام التسجيل مع تنسيق مخصص للرسائل.
    يتم تسجيل جميع الأحداث في ملف منفصل مع عرضها في وحدة التحكم.
    """
    os.makedirs(GuardianConfig.LOG_FOLDER, exist_ok=True)
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler(
                f"{GuardianConfig.LOG_FOLDER}/guardian.log",
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # تقليل مستوى تسجيل المكتبات الخارجية لتجنب الإزعاج
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    return logging.getLogger('GuardianBot')

# إنشاء كائن التسجيل العالمي
logger = setup_logging()

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           نظام قاعدة البيانات المتكامل
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

class MegaDatabase:
    """
    نظام قاعدة البيانات الرئيسي للبوت
    
    هذا الكلاس هو القلب النابض للبوت، حيث يدير جميع البيانات بما فيها:
    - الأعضاء ومعلوماتهم
    - قنوات الحماية
    - اشتراكات VIP
    - حملات التمويل
    - الأقسام والخدمات
    - رموز الهدايا
    - سجل النشاطات والتحويلات
    - بيانات الكابتشا
    
    الإصدار 20.0.0 مع دعم كامل للمميزات الجديدة
    """
    
    def __init__(self):
        """
        تهيئة قاعدة البيانات وتحميل البيانات المحفوظة من الملفات
        
        يتم تحميل البيانات من ملفين:
        1. guardian_database.pkl - البيانات الرئيسية
        2. guardian_settings.json - الإعدادات والتكوينات
        """
        # البيانات الأساسية - الأعضاء والقنوات
        self._members: Dict[int, dict] = {}
        self._protected_channels: Dict[str, dict] = {}
        self._vip_members: Dict[int, datetime] = {}
        self._settings: Dict[str, Any] = {}
        
        # بيانات الحملات والتمويل
        self._active_campaigns: Dict[str, dict] = {}
        self._pending_campaigns: Dict[str, dict] = {}
        self._campaign_index: Dict[str, dict] = {}
        self._campaign_stats: Dict[str, dict] = {}
        
        # بيانات الهدايا والرموز
        self._gift_codes: Dict[str, dict] = {}
        self._used_gifts: Dict[int, List[str]] = {}
        
        # سجل النشاطات والحركات
        self._activity_history: List[dict] = []
        
        # إعدادات القنوات الإجبارية والمشرفين
        self._mandatory_channels_config: Dict[str, dict] = {}
        self._admin_list: Set[int] = {GuardianConfig.MASTER_ADMIN_ID}
        
        # بيانات الخدمات والأقسام
        self._service_categories: Dict[str, dict] = {}
        self._services: Dict[str, dict] = {}
        self._service_orders: Dict[str, dict] = {}
        
        # تخصيص أسماء الأزرار
        self._custom_button_names: Dict[str, str] = {}
        self._weekly_referral_winners: Dict[str, List[int]] = {}
        
        # بيانات جديدة للإصدار 20.0.0
        self._transfer_history: List[dict] = []
        self._captcha_data: Dict[int, dict] = {}
        self._transfer_blocked: Set[int] = set()
        self._welcome_messages: List[dict] = []
        
        # تحميل البيانات من الملفات
        self._load_settings()
        self._load_database()
        
        # التأكد من وجود الحسابات الأساسية
        self._ensure_master_exists()
        self._rebuild_indexes()
        self._init_default_button_names()
        self._upgrade_members_data()
        
    # ═══════════════════════════ دوال التهيئة ═══════════════════════════
    
    def _init_default_button_names(self):
        """
        تهيئة أسماء الأزرار الافتراضية في واجهة المستخدم
        
        يتم تخزين هذه الأسماء في ملف الإعدادات ويمكن للمدير تغييرها
        من خلال لوحة التحكم في أي وقت. الأسماء الافتراضية هنا هي
        مجرد قيم ابتدائية يتم استخدامها عند تشغيل البوت لأول مرة.
        """
        defaults = {
            'menu_services': '⚡ الخدمات',
            'menu_protection_system': '🛡 نظام الحماية',
            'menu_exchange': '🔄 تبادل اشتراك والربح',
            'menu_funding': '💰 تمويل اعضاء',
            'menu_referral': '🔗 دعوة صديق',
            'menu_vip': '⭐ اشتراك VIP',
            'menu_support': '💬 تواصل مع الدعم',
            'menu_admin': '🎛 لوحة التحكم',
            'menu_account_info': 'ℹ️ معلومات حسابك',
            'menu_transfer': '💸 تحويل رصيد'
        }
        for key, value in defaults.items():
            if key not in self._custom_button_names:
                self._custom_button_names[key] = value
    
    def _upgrade_members_data(self):
        """
        ترقية بيانات الأعضاء القدامى لإضافة الحقول الجديدة
        
        عند التحديث من إصدار قديم إلى الإصدار 20.0.0،
        قد تكون بعض الحقول غير موجودة في بيانات الأعضاء القدامى.
        هذه الدالة تقوم بإضافة الحقول الناقصة بقيم افتراضية
        لضمان توافق البيانات مع المميزات الجديدة.
        """
        for mid in self._members:
            m = self._members[mid]
            defaults = {
                'captcha_verified': mid == GuardianConfig.MASTER_ADMIN_ID,
                'captcha_attempts': 0,
                'captcha_banned_until': None,
                'last_transfer_time': None,
                'transfer_blocked': False,
                'vip_auto_renew': True,
                'referral_reward_given': False,
            }
            for key, default_value in defaults.items():
                if key not in m:
                    m[key] = default_value
        self._save_database()
        
    def _ensure_master_exists(self):
        """
        التأكد من وجود حساب المدير الرئيسي في قاعدة البيانات
        
        المدير الرئيسي هو حساب خاص له صلاحيات كاملة في البوت.
        إذا لم يكن موجوداً في قاعدة البيانات، يتم إنشاؤه تلقائياً
        مع جميع الصلاحيات والمميزات.
        """
        master_id = GuardianConfig.MASTER_ADMIN_ID
        
        if master_id not in self._members:
            self._members[master_id] = {
                'member_id': master_id,
                'username': GuardianConfig.MASTER_ADMIN_USERNAME,
                'display_name': 'المدير',
                'balance': 0,
                'first_seen': datetime.now(),
                'joined_date': datetime.now(),
                'protected_channels': [],
                'last_active': datetime.now(),
                'referred_by': None,
                'referred_members': [],
                'referral_earnings': 0,
                'is_blocked': False,
                'block_reason': '',
                'referral_claimed': False,
                'completed_campaigns': [],
                'campaign_earnings': 0,
                'pending_verifications': {},
                'captcha_verified': True,
                'captcha_attempts': 0,
                'captcha_banned_until': None,
                'last_transfer_time': None,
                'transfer_blocked': False,
                'vip_auto_renew': True
            }
            self._save_database()
            logger.info("✅ تم إنشاء حساب المدير الرئيسي في قاعدة البيانات")
            
    def _rebuild_indexes(self):
        """
        إعادة بناء الفهارس المساعدة للبحث السريع
        
        الفهارس تساعد في تسريع عمليات البحث عن الحملات النشطة
        وتحديث الإحصائيات بشكل فعال.
        """
        self._campaign_index.clear()
        
        for campaign_id, campaign in self._active_campaigns.items():
            if campaign.get('status') == 'active':
                channel_id = campaign.get('channel_id', '')
                channel_username = campaign.get('channel_username', '')
                key = channel_id if channel_id else channel_username
                
                if key:
                    self._campaign_index[key] = {
                        'campaign_id': campaign_id,
                        'channel_id': channel_id,
                        'channel_username': channel_username,
                        'channel_link': campaign.get('channel_link', ''),
                        'channel_title': campaign.get('channel_title', ''),
                        'owner_id': campaign.get('owner_id'),
                        'members_required': campaign.get('members_required', 0),
                        'members_joined': campaign.get('members_joined', 0),
                        'members_remaining': campaign.get('members_remaining', 0),
                        'completed_by': campaign.get('completed_by', []),
                        'reward': campaign.get('reward_per_subscriber', 
                            self._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT))
                    }
        
    # ═══════════════════════════ دوال التحميل والحفظ ═══════════════════════════
    
    def _load_settings(self):
        """
        تحميل إعدادات النظام من ملف JSON
        
        الإعدادات تشمل:
        - أسعار الاشتراك والمكافآت
        - قائمة المشرفين
        - القنوات الإجبارية
        - بيانات الخدمات والأقسام
        - رسائل الترحيب
        """
        default_settings = {
            "vip_price": GuardianConfig.DEFAULT_VIP_PRICE,
            "free_trial_days": GuardianConfig.FREE_TRIAL_DAYS,
            "maintenance_mode": False,
            "mandatory_channels": [],
            "funding_price_per_member": GuardianConfig.FUNDING_PRICE_PER_MEMBER,
            "subscribe_reward": GuardianConfig.SUBSCRIBE_REWARD_AMOUNT,
            "inviter_reward": GuardianConfig.INVITER_REWARD_AMOUNT,
            "invited_reward": GuardianConfig.INVITED_REWARD_AMOUNT,
            "admin_list": [GuardianConfig.MASTER_ADMIN_ID],
            "mandatory_channels_config": {},
            "service_categories": {},
            "services": {},
            "service_orders": {},
            "custom_button_names": {},
            "weekly_referral_winners": {},
            "welcome_messages": [],
            "vip_discount_percent": GuardianConfig.VIP_DISCOUNT_PERCENT
        }
        
        try:
            if os.path.exists(GuardianConfig.SETTINGS_FILE):
                with open(GuardianConfig.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
                    logger.info(f"✅ تم تحميل الإعدادات من الملف")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الإعدادات: {e}")
            
        self._settings = default_settings
        self._mandatory_channels_config = self._settings.get('mandatory_channels_config', {})
        self._admin_list = set(self._settings.get('admin_list', [GuardianConfig.MASTER_ADMIN_ID]))
        
        # تحميل بيانات الخدمات من الإعدادات
        self._service_categories = self._settings.get('service_categories', {})
        self._services = self._settings.get('services', {})
        self._service_orders = self._settings.get('service_orders', {})
        self._custom_button_names = self._settings.get('custom_button_names', {})
        self._weekly_referral_winners = self._settings.get('weekly_referral_winners', {})
        self._welcome_messages = self._settings.get('welcome_messages', [])
        
    def _save_settings(self):
        """
        حفظ إعدادات النظام إلى ملف JSON
        
        يتم حفظ جميع الإعدادات الحالية إلى الملف لاستعادتها
        عند إعادة تشغيل البوت. هذه العملية تضمن عدم فقدان
        أي تغييرات في الإعدادات.
        """
        try:
            self._settings['mandatory_channels_config'] = self._mandatory_channels_config
            self._settings['admin_list'] = list(self._admin_list)
            self._settings['service_categories'] = self._service_categories
            self._settings['services'] = self._services
            self._settings['service_orders'] = self._service_orders
            self._settings['custom_button_names'] = self._custom_button_names
            self._settings['weekly_referral_winners'] = self._weekly_referral_winners
            self._settings['welcome_messages'] = self._welcome_messages
            with open(GuardianConfig.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الإعدادات: {e}")
            
    def _load_database(self):
        """
        تحميل قاعدة البيانات الرئيسية من ملف pickle
        
        قاعدة البيانات تحتوي على جميع معلومات الأعضاء والقنوات
        والحملات والهدايا. في حالة عدم وجود الملف، يتم إنشاء
        قاعدة بيانات فارغة جديدة.
        """
        try:
            if os.path.exists(GuardianConfig.DATABASE_FILE):
                with open(GuardianConfig.DATABASE_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self._members = data.get('members', {})
                    self._protected_channels = data.get('protected_channels', {})
                    self._vip_members = data.get('vip_members', {})
                    self._activity_history = data.get('activity_history', [])
                    self._active_campaigns = data.get('active_campaigns', {})
                    self._pending_campaigns = data.get('pending_campaigns', {})
                    self._campaign_stats = data.get('campaign_stats', {})
                    self._gift_codes = data.get('gift_codes', {})
                    self._used_gifts = data.get('used_gifts', {})
                    self._transfer_history = data.get('transfer_history', [])
                    self._captcha_data = data.get('captcha_data', {})
                    self._transfer_blocked = data.get('transfer_blocked', set())
                    logger.info(f"✅ تم تحميل البيانات: {len(self._members)} عضو")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل قاعدة البيانات: {e}")
            
    def _save_database(self):
        """
        حفظ قاعدة البيانات الرئيسية إلى ملف pickle مع نسخ احتياطية
        
        يتم إنشاء نسخة احتياطية قبل كل عملية حفظ لضمان
        استعادة البيانات في حالة حدوث أي خطأ. يتم الاحتفاظ
        بآخر 30 نسخة احتياطية فقط لتوفير المساحة.
        """
        try:
            data = {
                'members': self._members,
                'protected_channels': self._protected_channels,
                'vip_members': self._vip_members,
                'activity_history': self._activity_history,
                'active_campaigns': self._active_campaigns,
                'pending_campaigns': self._pending_campaigns,
                'campaign_stats': self._campaign_stats,
                'gift_codes': self._gift_codes,
                'used_gifts': self._used_gifts,
                'transfer_history': self._transfer_history,
                'captcha_data': self._captcha_data,
                'transfer_blocked': self._transfer_blocked
            }
            
            # إنشاء نسخة احتياطية قبل الحفظ
            if os.path.exists(GuardianConfig.DATABASE_FILE):
                os.makedirs(GuardianConfig.BACKUP_FOLDER, exist_ok=True)
                backup_path = f"{GuardianConfig.BACKUP_FOLDER}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                shutil.copy2(GuardianConfig.DATABASE_FILE, backup_path)
                
                # الاحتفاظ بآخر 30 نسخة فقط
                backups = sorted([
                    f for f in os.listdir(GuardianConfig.BACKUP_FOLDER) 
                    if f.startswith('backup_')
                ])
                if len(backups) > 30:
                    for old in backups[:-30]:
                        os.remove(os.path.join(GuardianConfig.BACKUP_FOLDER, old))
                
            with open(GuardianConfig.DATABASE_FILE, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ قاعدة البيانات: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال الأعضاء والمشرفين
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_member(self, member_id: int) -> dict:
        """
        الحصول على بيانات العضو أو إنشاء عضو جديد إذا لم يكن موجوداً
        
        هذه الدالة هي المدخل الرئيسي للتعامل مع بيانات الأعضاء.
        إذا كان العضو جديداً، يتم إنشاء سجل كامل له مع جميع
        الحقول المطلوبة بقيم افتراضية مناسبة.
        """
        member_id = int(member_id)
        if member_id not in self._members:
            self._members[member_id] = {
                'member_id': member_id,
                'username': '',
                'display_name': '',
                'balance': 0,
                'first_seen': datetime.now(),
                'joined_date': datetime.now(),
                'protected_channels': [],
                'last_active': datetime.now(),
                'referred_by': None,
                'referred_members': [],
                'referral_earnings': 0,
                'is_blocked': False,
                'block_reason': '',
                'referral_claimed': False,
                'completed_campaigns': [],
                'campaign_earnings': 0,
                'pending_verifications': {},
                'captcha_verified': False,
                'captcha_attempts': 0,
                'captcha_banned_until': None,
                'last_transfer_time': None,
                'transfer_blocked': False,
                'vip_auto_renew': True
            }
            self._save_database()
        return self._members[member_id]
    
    def update_member_info(self, member_id: int, user_obj):
        """
        تحديث معلومات العضو من كائن المستخدم في تيليجرام
        
        يتم استدعاء هذه الدالة في كل مرة يتفاعل فيها المستخدم
        مع البوت لضمان تحديث اسم المستخدم واليوزر تلقائياً.
        """
        member = self.get_member(member_id)
        member['username'] = user_obj.username or ''
        member['display_name'] = user_obj.first_name or ''
        member['last_active'] = datetime.now()
        self._save_database()
        
    def is_admin(self, member_id: int) -> bool:
        """التحقق من صلاحيات المشرف - المدير الرئيسي والمشرفين المضافين"""
        return member_id in self._admin_list
    
    def promote_admin(self, target_id: int) -> bool:
        """رفع عضو إلى رتبة مشرف مع تسجيل العملية في السجل"""
        self._admin_list.add(target_id)
        self._save_settings()
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"👑 رفع العضو {target_id} كمشرف في البوت")
        return True
    
    def demote_admin(self, target_id: int) -> bool:
        """إزالة عضو من قائمة المشرفين - لا يمكن إزالة المدير الرئيسي"""
        if target_id == GuardianConfig.MASTER_ADMIN_ID:
            return False
        self._admin_list.discard(target_id)
        self._save_settings()
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"⬇️ إزالة العضو {target_id} من المشرفين")
        return True
        
    def is_member_blocked(self, member_id: int) -> bool:
        """التحقق من حالة حظر العضو"""
        member = self.get_member(member_id)
        return member.get('is_blocked', False)
        
    def block_member(self, member_id: int, reason: str = "") -> bool:
        """حظر عضو من استخدام البوت مع تسجيل سبب الحظر"""
        member = self.get_member(member_id)
        member['is_blocked'] = True
        member['block_reason'] = reason
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🚫 تم حظر العضو {member_id}. السبب: {reason}")
        self._save_database()
        return True
        
    def unblock_member(self, member_id: int) -> bool:
        """فك الحظر عن عضو وإعادته للحالة الطبيعية"""
        member = self.get_member(member_id)
        member['is_blocked'] = False
        member['block_reason'] = ''
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"✅ تم فك الحظر عن العضو {member_id}")
        self._save_database()
        return True
        
    def delete_member(self, member_id: int) -> bool:
        """
        حذف عضو وجميع بياناته المرتبطة من النظام بالكامل
        
        هذه العملية لا يمكن التراجع عنها وتقوم بحذف:
        - بيانات العضو الشخصية
        - قنوات الحماية المرتبطة به
        - اشتراك VIP إذا كان مشتركاً
        - جميع حملات التمويل الخاصة به
        """
        if member_id == GuardianConfig.MASTER_ADMIN_ID:
            return False
            
        if member_id in self._members:
            del self._members[member_id]
            
        channels_to_delete = []
        for ch_id, ch_data in self._protected_channels.items():
            if ch_data.get('owner_id') == member_id:
                channels_to_delete.append(ch_id)
        for ch_id in channels_to_delete:
            del self._protected_channels[ch_id]
            
        if member_id in self._vip_members:
            del self._vip_members[member_id]
            
        for cid, camp in list(self._active_campaigns.items()):
            if camp.get('owner_id') == member_id:
                self.cancel_campaign(cid, "تم حذف العضو من النظام")
                
        self._admin_list.discard(member_id)
        self._save_settings()
        
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🗑 تم حذف العضو {member_id} وجميع بياناته من النظام")
        self._save_database()
        return True
        
    def get_blocked_members(self) -> List[dict]:
        """الحصول على قائمة الأعضاء المحظورين حالياً"""
        return [m for m in self._members.values() if m.get('is_blocked', False)]
        
    def search_member(self, member_id: int) -> Optional[dict]:
        """البحث عن عضو بواسطة المعرف الخاص به"""
        if member_id in self._members:
            return self._members[member_id]
        return None
        
    def get_top_balance_members(self, count: int = 10) -> List[dict]:
        """الحصول على أعلى الأعضاء رصيداً في النظام"""
        members = list(self._members.values())
        members.sort(key=lambda x: x.get('balance', 0), reverse=True)
        return members[:count]
    
    def get_top_referrers(self, count: int = 5) -> List[dict]:
        """الحصول على أفضل المشاركين في نظام الإحالة"""
        members = list(self._members.values())
        members.sort(key=lambda x: len(x.get('referred_members', [])), reverse=True)
        return members[:count]
        
    def get_member_activity(self, member_id: int) -> List[dict]:
        """الحصول على سجل نشاطات عضو معين مرتبة من الأحدث للأقدم"""
        return [log for log in self._activity_history if log.get('member_id') == member_id]
    
    def get_member_referrals_detail(self, member_id: int) -> List[dict]:
        """الحصول على تفاصيل المدعوين بواسطة عضو معين مع معلوماتهم الكاملة"""
        member = self.get_member(member_id)
        referred_ids = member.get('referred_members', [])
        result = []
        for rid in referred_ids:
            if rid in self._members:
                rm = self._members[rid]
                joined = rm.get('joined_date', '')
                if isinstance(joined, datetime):
                    joined = joined.strftime('%Y-%m-%d %H:%M')
                result.append({
                    'member_id': rid,
                    'username': rm.get('username', ''),
                    'display_name': rm.get('display_name', ''),
                    'balance': rm.get('balance', 0),
                    'joined_date': joined
                })
        return result
    
    def get_active_members(self) -> List[int]:
        """الحصول على قائمة بمعرفات جميع الأعضاء المسجلين في النظام"""
        return list(self._members.keys())
    
    def _log_activity(self, member_id: int, action: str):
        """
        تسجيل نشاط في سجل الحركات مع تحديد التاريخ والوقت
        
        يتم الاحتفاظ بآخر 5000 سجل فقط لتوفير المساحة
        وضمان أداء سريع للنظام.
        """
        self._activity_history.append({
            'member_id': member_id,
            'action': action,
            'timestamp': datetime.now()
        })
        if len(self._activity_history) > 5000:
            self._activity_history = self._activity_history[-5000:]
        self._save_database()
        
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال الإحالة المتقدمة
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process_referral(self, new_member_id: int, inviter_id: int) -> Tuple[bool, str]:
        """
        معالجة عملية الإحالة - تسجيل العلاقة فقط بدون منح المكافأة فوراً
        
        المكافأة تؤجل حتى يكمل العضو الجديد عملية التحقق والاشتراك
        في جميع القنوات الإجبارية لضمان جدية المستخدمين ومنع التلاعب.
        """
        if inviter_id == new_member_id:
            return False, "❌ لا يمكنك دعوة نفسك - هذا مخالف لقواعد النظام"
            
        if inviter_id not in self._members:
            return False, "❌ رابط الدعوة غير صالح أو منتهي الصلاحية"
            
        new_member = self.get_member(new_member_id)
        inviter = self.get_member(inviter_id)
        
        if new_member.get('referral_claimed', False):
            return False, "❌ لقد حصلت على مكافأة الإحالة مسبقاً ولا يمكنك الحصول عليها مرة أخرى"
        
        if 'referred_members' not in inviter:
            inviter['referred_members'] = []
        if new_member_id not in inviter['referred_members']:
            inviter['referred_members'].append(new_member_id)
            
        new_member['referred_by'] = inviter_id
        new_member['referral_claimed'] = True
        
        self._save_database()
        return True, "✅ تم تسجيل الإحالة بنجاح! ستحصل على المكافأة بعد إكمال التحقق والاشتراك في جميع القنوات الإجبارية."
    
    def give_referral_reward(self, new_member_id: int):
        """
        منح مكافأة الإحالة بعد التحقق والاشتراك في القنوات الإجبارية
        
        يحصل الداعي على مكافأة الإحالة ويحصل العضو الجديد
        على مكافأة التسجيل في نفس الوقت.
        """
        new_member = self.get_member(new_member_id)
        inviter_id = new_member.get('referred_by')

        # ⚠️ تحقق: إذا كان العضو قد حصل على المكافأة مسبقاً، لا تعطيه مرة أخرى
        if new_member.get('referral_reward_given', False):
            return
        
        if inviter_id and inviter_id in self._members:
            inviter = self.get_member(inviter_id)
            inviter_reward = self._settings.get('inviter_reward', GuardianConfig.INVITER_REWARD_AMOUNT)
            invited_reward = self._settings.get('invited_reward', GuardianConfig.INVITED_REWARD_AMOUNT)
            
            inviter['balance'] = inviter.get('balance', 0) + inviter_reward
            inviter['referral_earnings'] = inviter.get('referral_earnings', 0) + inviter_reward
            new_member['balance'] = new_member.get('balance', 0) + invited_reward
            
            # ✅ تعليم أن المكافأة تم منحها
            new_member['referral_reward_given'] = True
            
            self._log_activity(inviter_id, f"💰 حصل على {inviter_reward:,} IQD مكافأة إحالة بعد تحقق المدعو")
            self._log_activity(new_member_id, f"🎁 حصل على {invited_reward:,} IQD مكافأة تسجيل بعد التحقق")
            self._save_database()
        
    def get_referral_link(self, member_id: int) -> str:
        """إنشاء رابط الإحالة الخاص بالعضو لمشاركته مع الأصدقاء"""
        return f"https://t.me/{GuardianConfig.BOT_USERNAME}?start={member_id}"
        
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال نظام الكابتشا والتحقق
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generate_captcha(self, member_id: int) -> str:
        """
        توليد رمز تحقق عشوائي مكون من 6 أرقام
        
        يستخدم هذا الرمز للتأكد من أن المستخدم إنسان حقيقي
        وليس روبوت أو حساب وهمي.
        """
        code = ''.join(random.choices(string.digits, k=GuardianConfig.CAPTCHA_CODE_LENGTH))
        self._captcha_data[member_id] = {
            'code': code,
            'generated_at': datetime.now()
        }
        self._save_database()
        return code
    
    def verify_captcha(self, member_id: int, user_input: str) -> Tuple[bool, str]:
        """
        التحقق من صحة رمز الكابتشا المدخل من المستخدم
        
        النظام يسمح بـ 4 محاولات فقط، وبعدها يتم تقييد المستخدم
        لمدة 15 دقيقة قبل أن يتمكن من المحاولة مرة أخرى.
        """
        member = self.get_member(member_id)
        
        banned_until = member.get('captcha_banned_until')
        if banned_until:
            if isinstance(banned_until, str):
                banned_until = datetime.fromisoformat(banned_until)
            if datetime.now() < banned_until:
                remaining = int((banned_until - datetime.now()).total_seconds() / 60)
                return False, f"❌ تم تقييدك لمدة {remaining} دقيقة أخرى بسبب كثرة المحاولات الخاطئة. يرجى الانتظار والمحاولة لاحقاً."
            else:
                member['captcha_banned_until'] = None
                member['captcha_attempts'] = 0
        
        captcha_data = self._captcha_data.get(member_id, {})
        correct_code = captcha_data.get('code', '')
        
        if user_input == correct_code:
            member['captcha_verified'] = True
            member['captcha_attempts'] = 0
            self._captcha_data.pop(member_id, None)
            self._save_database()
            return True, "✅ تم التحقق من هويتك بنجاح! أهلاً بك في بوت تفاعلكم الذكي."
        
        member['captcha_attempts'] = member.get('captcha_attempts', 0) + 1
        
        if member['captcha_attempts'] >= GuardianConfig.CAPTCHA_MAX_ATTEMPTS:
            member['captcha_banned_until'] = datetime.now() + timedelta(minutes=GuardianConfig.CAPTCHA_BAN_MINUTES)
            member['captcha_attempts'] = 0
            self._save_database()
            return False, f"❌ لقد تجاوزت الحد الأقصى من المحاولات المسموحة! تم تقييد حسابك لمدة {GuardianConfig.CAPTCHA_BAN_MINUTES} دقيقة كاملة."
        
        remaining = GuardianConfig.CAPTCHA_MAX_ATTEMPTS - member['captcha_attempts']
        self._save_database()
        return False, f"❌ الرقم الذي أدخلته غير صحيح! تبقى لك {remaining} محاولات فقط قبل أن يتم تقييد حسابك."
    
    def is_captcha_verified(self, member_id: int) -> bool:
        """التحقق من حالة اجتياز الكابتشا للعضو"""
        member = self.get_member(member_id)
        if member_id == GuardianConfig.MASTER_ADMIN_ID:
            return True
        return member.get('captcha_verified', False)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال نظام التحويل
    # ═══════════════════════════════════════════════════════════════════════════
    
    def can_transfer(self, member_id: int) -> Tuple[bool, str]:
        """
        التحقق من إمكانية قيام العضو بعملية تحويل رصيد
        
        شروط التحويل:
        - ألا يكون محظوراً
        - ألا يكون محظوراً من التحويل
        - ألا يكون قد قام بتحويل خلال 24 ساعة الماضية
        """
        member = self.get_member(member_id)
        
        if member.get('transfer_blocked', False):
            return False, "❌ تم تقييد حسابك من عمليات التحويل. يرجى التواصل مع الدعم الفني للمساعدة."
        
        if member.get('is_blocked', False):
            return False, "❌ حسابك محظور حالياً ولا يمكنك إجراء أي عمليات تحويل."
        
        last_transfer = member.get('last_transfer_time')
        if last_transfer:
            if isinstance(last_transfer, str):
                last_transfer = datetime.fromisoformat(last_transfer)
            cooldown = datetime.now() - last_transfer
            if cooldown < timedelta(hours=GuardianConfig.TRANSFER_COOLDOWN_HOURS):
                remaining_hours = GuardianConfig.TRANSFER_COOLDOWN_HOURS - int(cooldown.total_seconds() / 3600)
                remaining_minutes = int((cooldown.total_seconds() % 3600) / 60)
                return False, f"❌ يمكنك إجراء تحويل واحد فقط كل {GuardianConfig.TRANSFER_COOLDOWN_HOURS} ساعة.\n⏰ الوقت المتبقي: {remaining_hours} ساعة و {remaining_minutes} دقيقة"
        
        return True, "✅ يمكنك إجراء عملية التحويل الآن"
    
    def transfer_balance(self, from_id: int, to_id: int, amount: int) -> Tuple[bool, str]:
        """
        تنفيذ عملية تحويل رصيد بين مستخدمين مع جميع التحققات الأمنية
        
        يتم تسجيل العملية في سجل التحويلات وإرسال إشعارات
        للطرفين وللمدير الرئيسي.
        """
        if from_id == to_id:
            return False, "❌ لا يمكنك تحويل الرصيد إلى نفسك! هذه محاولة تحايل مرفوضة."
        
        if amount > GuardianConfig.MAX_TRANSFER_AMOUNT:
            return False, f"❌ الحد الأقصى المسموح به للتحويل هو {GuardianConfig.MAX_TRANSFER_AMOUNT:,} IQD فقط."
        
        if amount <= 0:
            return False, "❌ المبلغ غير صالح. يجب أن يكون المبلغ أكبر من صفر."
        
        can_transfer, msg = self.can_transfer(from_id)
        if not can_transfer:
            return False, msg
        
        if to_id not in self._members:
            return False, "❌ المستخدم الذي تريد التحويل إليه غير موجود في قاعدة البيانات."
        
        sender = self.get_member(from_id)
        receiver = self.get_member(to_id)
        
        if sender.get('balance', 0) < amount:
            return False, f"❌ رصيدك غير كافي لإتمام هذه العملية. رصيدك الحالي: {sender.get('balance', 0):,} IQD"
        
        sender['balance'] = sender.get('balance', 0) - amount
        receiver['balance'] = receiver.get('balance', 0) + amount
        sender['last_transfer_time'] = datetime.now()
        
        transfer_record = {
            'from_id': from_id,
            'to_id': to_id,
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            'from_username': sender.get('username', ''),
            'to_username': receiver.get('username', '')
        }
        self._transfer_history.append(transfer_record)
        
        self._log_activity(from_id, f"💸 قام بتحويل مبلغ {amount:,} IQD إلى العضو {to_id}")
        self._log_activity(to_id, f"💰 استلم مبلغ {amount:,} IQD من العضو {from_id}")
        
        self._save_database()
        return True, f"✅ تمت عملية التحويل بنجاح!\n💰 المبلغ المحول: {amount:,} IQD\n💳 رصيدك الحالي: {sender['balance']:,} IQD"
    
    def toggle_transfer_block(self, member_id: int) -> bool:
        """تبديل حالة تقييد التحويل للعضو بين المنع والسماح"""
        member = self.get_member(member_id)
        member['transfer_blocked'] = not member.get('transfer_blocked', False)
        state = "تقييد" if member['transfer_blocked'] else "فك تقييد"
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🔒 تم {state} عمليات التحويل للعضو {member_id}")
        self._save_database()
        return member['transfer_blocked']
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال رسائل الترحيب
    # ═══════════════════════════════════════════════════════════════════════════
    
    def add_welcome_message(self, message_type: str, content: str, media_id: str = None) -> int:
        """
        إضافة رسالة ترحيب جديدة تظهر للمستخدمين بعد التحقق
        
        يمكن إضافة رسائل نصية أو صور أو فيديوهات ترحيبية
        """
        msg_id = len(self._welcome_messages) + 1
        self._welcome_messages.append({
            'id': msg_id,
            'type': message_type,
            'content': content,
            'media_id': media_id,
            'created_at': datetime.now().isoformat()
        })
        self._save_settings()
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"📨 أضاف رسالة ترحيب جديدة رقم {msg_id}")
        return msg_id
    
    def delete_welcome_message(self, msg_id: int) -> bool:
        """حذف رسالة ترحيب من القائمة"""
        for i, msg in enumerate(self._welcome_messages):
            if msg.get('id') == msg_id:
                self._welcome_messages.pop(i)
                self._save_settings()
                self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🗑 حذف رسالة ترحيب رقم {msg_id}")
                return True
        return False
    
    def get_welcome_messages(self) -> List[dict]:
        """الحصول على جميع رسائل الترحيب المسجلة"""
        return self._welcome_messages
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال نظام VIP المتقدم
    # ═══════════════════════════════════════════════════════════════════════════
    
    def is_vip_member(self, member_id: int) -> bool:
        """
        التحقق من عضوية VIP للعضو مع مراعاة تاريخ الانتهاء
        
        المدير الرئيسي يعتبر VIP دائماً بدون الحاجة لاشتراك
        """
        member_id = int(member_id)
        if member_id == GuardianConfig.MASTER_ADMIN_ID:
            return True
            
        if member_id in self._vip_members:
            expiry = self._vip_members[member_id]
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry)
            return datetime.now() < expiry
        return False
    
    def is_exempt_from_mandatory(self, member_id: int) -> bool:
        """
        التحقق من إعفاء العضو من الاشتراك الإجباري
        
        مشتركي VIP والمدير الرئيسي معفيون من الاشتراك
        في القنوات الإجبارية
        """
        return self.is_vip_member(member_id) or member_id == GuardianConfig.MASTER_ADMIN_ID
    
    def get_vip_discount(self, member_id: int) -> int:
        """الحصول على نسبة خصم VIP على الخدمات (15% للمشتركين)"""
        if self.is_vip_member(member_id):
            return self._settings.get('vip_discount_percent', GuardianConfig.VIP_DISCOUNT_PERCENT)
        return 0
    
    def get_service_price_with_vip_discount(self, member_id: int, service_id: str) -> int:
        """حساب سعر الخدمة بعد تطبيق خصم VIP إذا كان العضو مشتركاً"""
        service = self._services.get(service_id, {})
        original_price = service.get('price_per_1000', 0)
        discount = self.get_vip_discount(member_id)
        if discount > 0:
            discounted = int(original_price * (1 - discount / 100))
            return discounted
        return original_price
    
    def subscribe_vip(self, member_id: int) -> Tuple[bool, str]:
        """الاشتراك في خدمة VIP مع شرح جميع المميزات"""
        price = self._settings.get('vip_price', GuardianConfig.DEFAULT_VIP_PRICE)
        
        if self.deduct_balance(member_id, price):
            expiry = datetime.now() + timedelta(days=GuardianConfig.VIP_DURATION_DAYS)
            self._vip_members[member_id] = expiry
            self._log_activity(member_id, f"⭐ اشترك في VIP لمدة {GuardianConfig.VIP_DURATION_DAYS} يوم")
            self._save_database()
            return True, (
                f"✅ تم الاشتراك في VIP بنجاح!\n\n"
                f"📅 تاريخ الانتهاء: {expiry.strftime('%Y-%m-%d')}\n"
                f"🎁 خصم {GuardianConfig.VIP_DISCOUNT_PERCENT}% على جميع الخدمات\n"
                f"🚀 تمويل مباشر بدون انتظار موافقة\n"
                f"🛡 إعفاء من الاشتراك في القنوات الإجبارية\n"
                f"💰 هدية {GuardianConfig.VIP_BONUS_PERCENT}% على كل عملية شحن\n"
                f"🔄 تجديد تلقائي للاشتراك\n"
                f"📊 إضافة حتى {GuardianConfig.VIP_CHANNELS_LIMIT} قنوات حماية"
            )
        else:
            return False, (
                f"❌ رصيدك غير كافي للاشتراك في VIP.\n"
                f"💰 المطلوب: {price:,} IQD\n"
                f"💳 رصيدك الحالي: {self.get_member(member_id).get('balance', 0):,} IQD\n\n"
                f"يمكنك شحن رصيدك من خلال التواصل مع الدعم الفني."
            )
    
    def cancel_vip(self, member_id: int) -> bool:
        """
        إلغاء اشتراك VIP للعضو مع حذف جميع مميزاته
        
        بعد الإلغاء يفقد العضو جميع مميزات VIP فوراً
        """
        if member_id in self._vip_members:
            del self._vip_members[member_id]
            self._save_database()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"❌ تم إلغاء اشتراك VIP للعضو {member_id}")
            return True
        return False
    
    def auto_renew_vip(self, member_id: int) -> bool:
        """
        محاولة التجديد التلقائي لاشتراك VIP قبل يوم من انتهائه
        
        يتم الخصم من رصيد العضو تلقائياً إذا كان لديه رصيد كاف
        """
        price = self._settings.get('vip_price', GuardianConfig.DEFAULT_VIP_PRICE)
        member = self.get_member(member_id)
        
        if not member.get('vip_auto_renew', True):
            return False
        
        if member.get('balance', 0) >= price:
            if self.deduct_balance(member_id, price):
                expiry = datetime.now() + timedelta(days=GuardianConfig.VIP_DURATION_DAYS)
                self._vip_members[member_id] = expiry
                self._log_activity(member_id, "🔄 تم تجديد اشتراك VIP تلقائياً بنجاح")
                self._save_database()
                return True
        return False
    
    def add_balance_with_bonus(self, member_id: int, amount: int) -> int:
        """
        شحن رصيد مع هدية إضافية 10% لمشتركي VIP
        
        المشترك العادي يحصل على المبلغ المضاف فقط
        """
        bonus = 0
        if self.is_vip_member(member_id):
            bonus = int(amount * GuardianConfig.VIP_BONUS_PERCENT / 100)
        total = amount + bonus
        member = self.get_member(member_id)
        member['balance'] = member.get('balance', 0) + total
        if bonus > 0:
            self._log_activity(member_id, f"💰 تم شحن {amount:,} IQD + هدية VIP {bonus:,} IQD ({GuardianConfig.VIP_BONUS_PERCENT}%)")
        else:
            self._log_activity(member_id, f"💰 تم شحن {amount:,} IQD")
        self._save_database()
        return total
    
    def add_balance(self, member_id: int, amount: int) -> int:
        """إضافة رصيد للعضو بدون هدية إضافية"""
        member = self.get_member(member_id)
        member['balance'] = member.get('balance', 0) + amount
        self._log_activity(member_id, f"💰 تم شحن {amount:,} IQD إلى الرصيد")
        self._save_database()
        return member['balance']
        
    def deduct_balance(self, member_id: int, amount: int) -> bool:
        """خصم من رصيد العضو مع التحقق من كفاية الرصيد"""
        member = self.get_member(member_id)
        if member.get('balance', 0) >= amount:
            member['balance'] -= amount
            self._save_database()
            return True
        return False
    
    def force_deduct_balance(self, member_id: int, amount: int) -> int:
        """خصم إجباري من الرصيد حتى لو أصبح الرصيد سالباً"""
        member = self.get_member(member_id)
        member['balance'] = member.get('balance', 0) - amount
        self._save_database()
        return member['balance']
        
    def is_free_trial_valid(self, member_id: int) -> bool:
        """التحقق من صلاحية الفترة التجريبية المجانية للعضو"""
        member_id = int(member_id)
        if member_id == GuardianConfig.MASTER_ADMIN_ID:
            return True
            
        member = self.get_member(member_id)
        first_seen = member['first_seen']
        if isinstance(first_seen, str):
            first_seen = datetime.fromisoformat(first_seen)
        free_days = self._settings.get('free_trial_days', GuardianConfig.FREE_TRIAL_DAYS)
        return datetime.now() < first_seen + timedelta(days=free_days)
        
    def can_use_bot(self, member_id: int) -> Tuple[bool, str]:
        """
        التحقق الشامل من إمكانية استخدام البوت
        
        يراعي جميع الحالات: مدير، VIP، تجريبي، محظور، صيانة
        """
        member_id = int(member_id)
        
        if member_id == GuardianConfig.MASTER_ADMIN_ID:
            return True, "مدير النظام - صلاحيات كاملة"
            
        if self.is_member_blocked(member_id):
            return False, "تم حظر حسابك من استخدام البوت"
            
        if self._settings.get('maintenance_mode', False):
            return False, "البوت حالياً في وضع الصيانة"
            
        if self.is_vip_member(member_id):
            expiry = self._vip_members[member_id]
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry)
            days_left = (expiry - datetime.now()).days
            return True, f"⭐ مشترك VIP - متبقي {days_left} يوم"
            
        if self.is_free_trial_valid(member_id):
            member = self.get_member(member_id)
            first_seen = member['first_seen']
            if isinstance(first_seen, str):
                first_seen = datetime.fromisoformat(first_seen)
            free_days = self._settings.get('free_trial_days', GuardianConfig.FREE_TRIAL_DAYS)
            days_passed = (datetime.now() - first_seen).days
            days_left = free_days - days_passed
            return True, f"🎁 فترة تجريبية - متبقي {days_left} يوم"
            
        return False, "انتهت الفترة التجريبية المجانية"
        
    def get_max_channels(self, member_id: int) -> int:
        """الحصول على الحد الأقصى للقنوات المسموح بها حسب نوع الاشتراك"""
        if self.is_vip_member(member_id) or member_id == GuardianConfig.MASTER_ADMIN_ID:
            return GuardianConfig.VIP_CHANNELS_LIMIT
        return GuardianConfig.FREE_CHANNELS_LIMIT
        
    def get_vip_expiry_date(self, member_id: int) -> Optional[datetime]:
        """الحصول على تاريخ انتهاء اشتراك VIP للعضو"""
        if member_id in self._vip_members:
            expiry = self._vip_members[member_id]
            if isinstance(expiry, str):
                return datetime.fromisoformat(expiry)
            return expiry
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال الخدمات والأقسام
    # ═══════════════════════════════════════════════════════════════════════════
    
    def create_service_category(self, name: str, description: str) -> str:
        """إنشاء قسم خدمات جديد مع إشعار المدير"""
        cat_id = f"CAT_{int(time.time())}"
        self._service_categories[cat_id] = {
            'id': cat_id,
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'services': {}
        }
        self._save_settings()
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"📁 أنشأ قسم خدمات جديد: {name}")
        return cat_id
    
    def rename_category(self, category_id: str, new_name: str) -> bool:
        """تغيير اسم القسم مع تسجيل الاسم القديم والجديد في السجل"""
        if category_id in self._service_categories:
            old_name = self._service_categories[category_id].get('name', '')
            self._service_categories[category_id]['name'] = new_name
            self._save_settings()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"✏️ تغيير اسم القسم من '{old_name}' إلى '{new_name}'")
            return True
        return False
    
    def rename_service(self, service_id: str, new_name: str) -> bool:
        """تغيير اسم الخدمة في جميع الأماكن المرتبطة بها"""
        if service_id in self._services:
            old_name = self._services[service_id].get('name', '')
            self._services[service_id]['name'] = new_name
            cat_id = self._services[service_id].get('category_id', '')
            if cat_id and cat_id in self._service_categories:
                if service_id in self._service_categories[cat_id].get('services', {}):
                    self._service_categories[cat_id]['services'][service_id]['name'] = new_name
            self._save_settings()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"✏️ تغيير اسم الخدمة من '{old_name}' إلى '{new_name}'")
            return True
        return False
    
    def add_service_to_category(self, category_id: str, name: str, description: str, 
                                price_per_1000: int, duration: str,
                                min_amount: int, max_amount: int) -> str:
        """إضافة خدمة جديدة إلى قسم معين مع جميع التفاصيل"""
        srv_id = f"SRV_{int(time.time())}"
        service_data = {
            'id': srv_id,
            'name': name,
            'description': description,
            'category_id': category_id,
            'needs_link': True,
            'price_per_1000': price_per_1000,
            'duration': duration,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'created_at': datetime.now().isoformat()
        }
        self._services[srv_id] = service_data
        
        if category_id in self._service_categories:
            if 'services' not in self._service_categories[category_id]:
                self._service_categories[category_id]['services'] = {}
            self._service_categories[category_id]['services'][srv_id] = service_data
        
        self._save_settings()
        self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"➕ أضاف خدمة جديدة: {name} إلى القسم {category_id}")
        return srv_id
    
    def delete_category(self, category_id: str) -> bool:
        """حذف قسم مع جميع الخدمات المرتبطة به بشكل نهائي"""
        if category_id in self._service_categories:
            services_to_delete = list(self._service_categories[category_id].get('services', {}).keys())
            for srv_id in services_to_delete:
                if srv_id in self._services:
                    del self._services[srv_id]
            del self._service_categories[category_id]
            self._save_settings()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🗑 حذف قسم خدمات بالكامل: {category_id}")
            return True
        return False
    
    def delete_service(self, service_id: str) -> bool:
        """حذف خدمة محددة من القسم ومن قائمة الخدمات"""
        if service_id in self._services:
            cat_id = self._services[service_id].get('category_id')
            if cat_id and cat_id in self._service_categories:
                if service_id in self._service_categories[cat_id].get('services', {}):
                    del self._service_categories[cat_id]['services'][service_id]
            del self._services[service_id]
            self._save_settings()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🗑 حذف خدمة: {service_id}")
            return True
        return False
    
    def get_all_categories(self) -> List[dict]:
        """الحصول على جميع أقسام الخدمات المتاحة"""
        return list(self._service_categories.values())
    
    def get_category_services(self, category_id: str) -> List[dict]:
        """الحصول على جميع الخدمات في قسم معين"""
        if category_id in self._service_categories:
            services = []
            for srv_id in self._service_categories[category_id].get('services', {}):
                if srv_id in self._services:
                    services.append(self._services[srv_id])
            return services
        return []
    
    def create_service_order(self, user_id: int, service_id: str, quantity: int, link: str = "") -> str:
        """إنشاء طلب خدمة جديد مع حساب التكلفة تلقائياً"""
        order_id = f"ORD_{int(time.time())}"
        service = self._services.get(service_id, {})
        price = self.get_service_price_with_vip_discount(user_id, service_id)
        total_cost = int((quantity / 1000) * price)
        
        self._service_orders[order_id] = {
            'order_id': order_id,
            'user_id': user_id,
            'service_id': service_id,
            'service_name': service.get('name', ''),
            'category_id': service.get('category_id', ''),
            'quantity': quantity,
            'link': link,
            'total_cost': total_cost,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        self._save_settings()
        self._log_activity(user_id, f"📝 أنشأ طلب خدمة: {service.get('name', '')} - كمية: {quantity}")
        return order_id
    
    def get_pending_orders(self) -> List[dict]:
        """الحصول على جميع الطلبات المعلقة التي تنتظر المراجعة"""
        return [o for o in self._service_orders.values() if o.get('status') == 'pending']
    
    def get_order(self, order_id: str) -> Optional[dict]:
        """الحصول على تفاصيل طلب محدد"""
        return self._service_orders.get(order_id)
    
    def approve_order(self, order_id: str) -> bool:
        """الموافقة على طلب خدمة وتغيير حالته إلى مقبول"""
        if order_id in self._service_orders:
            self._service_orders[order_id]['status'] = 'approved'
            self._save_settings()
            return True
        return False
    
    def reject_order(self, order_id: str) -> bool:
        """رفض طلب خدمة وإعادة المبلغ المدفوع إلى رصيد المستخدم"""
        if order_id in self._service_orders:
            order = self._service_orders[order_id]
            self._service_orders[order_id]['status'] = 'rejected'
            self.add_balance(order['user_id'], order['total_cost'])
            self._save_settings()
            return True
        return False
    
    def get_button_name(self, key: str) -> str:
        """الحصول على اسم الزر المخصص أو الاسم الافتراضي"""
        return self._custom_button_names.get(key, key)
    
    def set_button_name(self, key: str, name: str):
        """تعيين اسم مخصص لزر في واجهة المستخدم"""
        self._custom_button_names[key] = name
        self._save_settings()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال حملات التمويل
    # ═══════════════════════════════════════════════════════════════════════════
    
    def has_active_campaign_for_channel(self, owner_id: int, channel_username: str) -> bool:
        """التحقق من وجود حملة تمويل نشطة لنفس القناة"""
        for campaign in self._active_campaigns.values():
            if (campaign.get('owner_id') == owner_id and 
                campaign.get('channel_username', '').lower() == channel_username.lower() and
                campaign.get('status') in ['pending', 'active']):
                return True
        return False
    
    def create_pending_campaign(self, owner_id: int, channel_id: str, channel_title: str,
                                channel_link: str, channel_username: str, members_count: int) -> Tuple[bool, Any]:
        """
        إنشاء حملة تمويل جديدة
        
        مشتركي VIP: يتم تفعيل الحملة مباشرة بدون انتظار موافقة
        المستخدمين العاديين: تدخل الحملة في قائمة الانتظار للمراجعة
        """
        if self.has_active_campaign_for_channel(owner_id, channel_username):
            return False, "❌ لديك حملة تمويل نشطة بالفعل لهذه القناة. يرجى الانتظار حتى اكتمالها."
        
        is_vip = self.is_vip_member(owner_id)
        price_per_member = self._settings.get('funding_price_per_member', GuardianConfig.FUNDING_PRICE_PER_MEMBER)
        total_cost = members_count * price_per_member
        
        campaign_id = f"CAMP_{int(time.time())}"
        
        if not channel_username and channel_link:
            if 't.me/' in channel_link:
                channel_username = channel_link.split('t.me/')[-1].split('/')[0]
            elif channel_link.startswith('@'):
                channel_username = channel_link.replace('@', '')
        
        if channel_link and not channel_link.startswith('http'):
            if channel_username:
                channel_link = f"https://t.me/{channel_username}"
        
        campaign = {
            'campaign_id': campaign_id,
            'owner_id': owner_id,
            'channel_id': channel_id,
            'channel_title': channel_title,
            'channel_link': channel_link,
            'channel_username': channel_username,
            'members_required': members_count,
            'members_joined': 0,
            'members_remaining': members_count,
            'price_per_member': price_per_member,
            'total_cost': total_cost,
            'status': 'active' if is_vip else 'pending',
            'is_approved': is_vip,
            'approved_by': owner_id if is_vip else None,
            'approved_at': datetime.now() if is_vip else None,
            'created_at': datetime.now(),
            'completed_at': None,
            'completed_by': [],
            'is_reported': False,
            'report_reason': '',
            'reported_by': None,
            'reward_per_subscriber': self._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT)
        }
        
        if is_vip:
            self._active_campaigns[campaign_id] = campaign
            key = campaign.get('channel_id') or campaign.get('channel_username', '')
            if key:
                self._campaign_index[key] = {
                    'campaign_id': campaign_id,
                    'channel_id': campaign.get('channel_id', ''),
                    'channel_username': campaign.get('channel_username', ''),
                    'channel_link': campaign.get('channel_link', ''),
                    'channel_title': channel_title,
                    'owner_id': owner_id,
                    'members_required': members_count,
                    'members_joined': 0,
                    'members_remaining': members_count,
                    'completed_by': [],
                    'reward': campaign.get('reward_per_subscriber', self._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT))
                }
        else:
            self._pending_campaigns[campaign_id] = campaign
        
        self._log_activity(owner_id, f"📢 أنشأ حملة تمويل: {channel_title} - {members_count} عضو" + (" (VIP - تفعيل مباشر)" if is_vip else ""))
        self._save_database()
        
        return True, campaign
    
    def approve_campaign(self, campaign_id: str, admin_id: int) -> Tuple[bool, str, Optional[dict]]:
        """الموافقة على حملة تمويل معلقة وتفعيلها"""
        if campaign_id not in self._pending_campaigns:
            return False, "الحملة غير موجودة", None
            
        campaign = self._pending_campaigns[campaign_id]
        campaign['status'] = 'active'
        campaign['is_approved'] = True
        campaign['approved_by'] = admin_id
        campaign['approved_at'] = datetime.now()
        
        self._active_campaigns[campaign_id] = campaign
        
        key = campaign.get('channel_id') or campaign.get('channel_username', '')
        if key:
            self._campaign_index[key] = {
                'campaign_id': campaign_id,
                'channel_id': campaign.get('channel_id', ''),
                'channel_username': campaign.get('channel_username', ''),
                'channel_link': campaign.get('channel_link', ''),
                'channel_title': campaign.get('channel_title', ''),
                'owner_id': campaign.get('owner_id'),
                'members_required': campaign.get('members_required', 0),
                'members_joined': 0,
                'members_remaining': campaign.get('members_required', 0),
                'completed_by': [],
                'reward': campaign.get('reward_per_subscriber', self._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT))
            }
        
        del self._pending_campaigns[campaign_id]
        self._save_database()
        return True, "✅ تمت الموافقة على الحملة وتفعيلها بنجاح", campaign
    
    def reject_campaign(self, campaign_id: str, admin_id: int, reason: str = "") -> Tuple[bool, str, Optional[dict]]:
        """رفض حملة تمويل وإعادة المبلغ المدفوع لصاحبها"""
        if campaign_id not in self._pending_campaigns:
            return False, "الحملة غير موجودة", None
            
        campaign = self._pending_campaigns[campaign_id]
        owner_id = campaign['owner_id']
        total_cost = campaign['total_cost']
        
        self.add_balance(owner_id, total_cost)
        
        campaign['status'] = 'rejected'
        campaign['rejected_by'] = admin_id
        campaign['rejected_at'] = datetime.now()
        campaign['reject_reason'] = reason
        
        self._active_campaigns[campaign_id] = campaign
        del self._pending_campaigns[campaign_id]
        self._save_database()
        
        return True, "✅ تم رفض الحملة وإعادة المبلغ إلى رصيد صاحبها", campaign
    
    def get_pending_campaigns(self) -> List[dict]:
        """الحصول على جميع الحملات المعلقة التي تنتظر المراجعة"""
        return list(self._pending_campaigns.values())
    
    def get_active_campaigns(self) -> List[dict]:
        """الحصول على جميع الحملات النشطة حالياً"""
        return [c for c in self._active_campaigns.values() if c.get('status') == 'active']
    
    def get_uncompleted_campaigns_for_member(self, member_id: int) -> List[dict]:
        """الحصول على الحملات النشطة التي لم يكملها العضو بعد"""
        active = self.get_active_campaigns()
        uncompleted = []
        member = self.get_member(member_id)
        completed = member.get('completed_campaigns', [])
        
        for camp in active:
            if camp.get('owner_id') == member_id:
                continue
            campaign_id = camp.get('campaign_id', '')
            if campaign_id and campaign_id not in completed and member_id not in camp.get('completed_by', []):
                uncompleted.append(camp)
                
        return uncompleted
    
    def verify_member_subscriptions(self, member_id: int, campaign_ids: List[str], bot=None) -> Tuple[int, List[str]]:
        """التحقق من اشتراكات العضو وإعطاء المكافآت المستحقة"""
        successful = []
        total_reward = 0
        member = self.get_member(member_id)
        
        for campaign_id in campaign_ids:
            campaign = self._active_campaigns.get(campaign_id)
            
            if not campaign or campaign.get('status') != 'active':
                continue
                
            if campaign_id in member.get('completed_campaigns', []) or member_id in campaign.get('completed_by', []):
                continue
                
            reward = campaign.get('reward_per_subscriber', self._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT))
            
            member['balance'] = member.get('balance', 0) + reward
            member['campaign_earnings'] = member.get('campaign_earnings', 0) + reward
            member.setdefault('completed_campaigns', []).append(campaign_id)
            campaign.setdefault('completed_by', []).append(member_id)
            
            campaign['members_joined'] = campaign.get('members_joined', 0) + 1
            if campaign.get('members_remaining', 0) > 0:
                campaign['members_remaining'] = campaign.get('members_remaining', 0) - 1
            
            key = campaign.get('channel_id') or campaign.get('channel_username', '')
            if key and key in self._campaign_index:
                self._campaign_index[key]['members_joined'] = campaign['members_joined']
                self._campaign_index[key]['members_remaining'] = campaign['members_remaining']
            
            if campaign['members_remaining'] == 0:
                campaign['status'] = 'completed'
                campaign['completed_at'] = datetime.now()
                self._remove_mandatory_by_link(campaign.get('channel_link', ''))
                
            total_reward += reward
            successful.append(campaign_id)
            self._log_activity(member_id, f"💰 حصل على {reward} IQD من حملة {campaign.get('channel_title', '')}")
            
        if successful:
            self._save_database()
            
        return len(successful), successful
    
    def _remove_mandatory_by_link(self, link: str):
        """إزالة قناة من قائمة الاشتراك الإجباري بعد اكتمال التمويل"""
        if link and link in self._settings.get('mandatory_channels', []):
            self._settings['mandatory_channels'].remove(link)
            self._mandatory_channels_config.pop(link, None)
            self._save_settings()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🔓 تم إزالة القناة من الاشتراك الإجباري تلقائياً: {link}")
    
    def remove_mandatory_channel(self, channel: str) -> bool:
        """حذف قناة إجبارية مع البحث بجميع الصيغ الممكنة للرابط"""
        channels = self._settings.get('mandatory_channels', [])
        removed = False
        
        if channel in channels:
            channels.remove(channel)
            self._mandatory_channels_config.pop(channel, None)
            removed = True
        else:
            to_remove = [ch for ch in channels if channel in ch or ch in channel]
            for ch in to_remove:
                channels.remove(ch)
                self._mandatory_channels_config.pop(ch, None)
                removed = True
        
        if removed:
            self._settings['mandatory_channels'] = channels
            self._save_settings()
            self._log_activity(GuardianConfig.MASTER_ADMIN_ID, f"🗑 حذف قناة من الاشتراك الإجباري: {channel}")
        
        return removed
    
    def cancel_campaign(self, campaign_id: str, reason: str = "") -> bool:
        """إلغاء حملة تمويل نشطة"""
        if campaign_id in self._active_campaigns:
            campaign = self._active_campaigns[campaign_id]
            campaign['status'] = 'cancelled'
            campaign['cancelled_at'] = datetime.now()
            campaign['cancel_reason'] = reason
            
            key = campaign.get('channel_id') or campaign.get('channel_username', '')
            if key in self._campaign_index:
                del self._campaign_index[key]
                
            self._log_activity(campaign['owner_id'], f"🚫 ألغيت حملة تمويل: {campaign.get('channel_title', '')}")
            self._save_database()
            return True
        return False
    
    def cancel_all_campaigns_for_channel(self, channel_username_or_id: str, reason: str = "") -> List[int]:
        """إلغاء جميع حملات التمويل المرتبطة بقناة محددة"""
        owners = []
        for cid, camp in list(self._active_campaigns.items()):
            if (camp.get('channel_username') == channel_username_or_id or 
                camp.get('channel_id') == channel_username_or_id):
                if camp.get('status') in ['active', 'pending']:
                    camp['status'] = 'cancelled'
                    camp['cancelled_at'] = datetime.now()
                    camp['cancel_reason'] = reason
                    owners.append(camp['owner_id'])
        
        for cid, camp in list(self._pending_campaigns.items()):
            if camp.get('channel_username') == channel_username_or_id or camp.get('channel_id') == channel_username_or_id:
                camp['status'] = 'cancelled'
                camp['cancelled_at'] = datetime.now()
                camp['cancel_reason'] = reason
                owners.append(camp['owner_id'])
        
        self.remove_mandatory_channel(channel_username_or_id)
        
        if owners:
            self._save_database()
            self._save_settings()
        return list(set(owners))
    
    def report_campaign(self, campaign_id: str, reporter_id: int, reason: str) -> bool:
        """الإبلاغ عن حملة تمويل مشبوهة"""
        if campaign_id in self._active_campaigns:
            campaign = self._active_campaigns[campaign_id]
            campaign['is_reported'] = True
            campaign['report_reason'] = reason
            campaign['reported_by'] = reporter_id
            campaign['reported_at'] = datetime.now()
            self._log_activity(reporter_id, f"🚨 أبلغ عن حملة: {campaign.get('channel_title', '')}")
            self._save_database()
            return True
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال الهدايا
    # ═══════════════════════════════════════════════════════════════════════════
    
    def create_gift_code(self, admin_id: int, max_uses: int, amount: int) -> str:
        """إنشاء رمز هدية جديد يمكن للمستخدمين استخدامه"""
        code = secrets.token_urlsafe(16)
        
        self._gift_codes[code] = {
            'code': code,
            'created_by': admin_id,
            'created_at': datetime.now(),
            'max_uses': max_uses,
            'used_count': 0,
            'amount': amount,
            'total_amount': max_uses * amount,
            'used_by': [],
            'is_active': True
        }
        self._log_activity(admin_id, f"🎁 أنشأ رمز هدية: {max_uses} استخدام، {amount} IQD لكل استخدام")
        self._save_database()
        return code
    
    def redeem_gift_code(self, code: str, member_id: int) -> Tuple[bool, str]:
        """استخدام رمز هدية وإضافة الرصيد للمستخدم"""
        code = code.strip()
        
        if code not in self._gift_codes:
            return False, "❌ رمز الهدية غير صالح أو غير موجود في النظام"
            
        gift = self._gift_codes[code]
        
        if not gift.get('is_active', False):
            return False, "❌ انتهت صلاحية رمز الهدية هذا"
            
        if gift['used_count'] >= gift['max_uses']:
            gift['is_active'] = False
            self._save_database()
            return False, "❌ اكتمل العدد المسموح به من المستخدمين لهذا الرمز"
            
        if member_id not in self._used_gifts:
            self._used_gifts[member_id] = []
            
        if code in self._used_gifts[member_id]:
            return False, "❌ لقد قمت باستخدام رمز الهدية هذا مسبقاً"
            
        member = self.get_member(member_id)
        amount = gift['amount']
        
        member['balance'] = member.get('balance', 0) + amount
        
        gift['used_count'] = gift.get('used_count', 0) + 1
        gift.setdefault('used_by', []).append(member_id)
        self._used_gifts[member_id].append(code)
        
        if gift['used_count'] >= gift['max_uses']:
            gift['is_active'] = False
            
        self._log_activity(member_id, f"🎁 حصل على {amount} IQD من رمز هدية")
        self._save_database()
        
        return True, f"✅ تم إضافة {amount} IQD إلى رصيدك بنجاح"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال قنوات الحماية
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_member_channels(self, member_id: int) -> List[str]:
        """الحصول على قائمة القنوات المحمية الخاصة بالعضو"""
        member = self.get_member(member_id)
        return member.get('protected_channels', [])
    
    def add_protected_channel(self, member_id: int, channel_id: str, channel_title: str = "") -> bool:
        """إضافة قناة جديدة إلى نظام الحماية"""
        member = self.get_member(member_id)
        channels = member.get('protected_channels', [])
        
        if str(channel_id) not in channels:
            channels.append(str(channel_id))
            member['protected_channels'] = channels
            
        self._protected_channels[str(channel_id)] = {
            'owner_id': member_id,
            'title': channel_title,
            'added_date': datetime.now(),
            'protection_settings': {
                'block_new_members': False,
                'block_leaving_members': False,
                'block_no_username': False
            },
            'stats': {
                'total_blocked': 0,
                'total_joined': 0,
                'total_left': 0
            }
        }
        
        self._log_activity(member_id, f"➕ أضاف قناة حماية: {channel_title}")
        self._save_database()
        return True
    
    def remove_protected_channel(self, member_id: int, channel_id: str) -> bool:
        """حذف قناة من نظام الحماية"""
        member = self.get_member(member_id)
        channels = member.get('protected_channels', [])
        
        if str(channel_id) in channels:
            channels.remove(str(channel_id))
            member['protected_channels'] = channels
            
        if str(channel_id) in self._protected_channels:
            channel_title = self._protected_channels[str(channel_id)].get('title', '')
            del self._protected_channels[str(channel_id)]
            self._log_activity(member_id, f"🗑 حذف قناة حماية: {channel_title}")
            
        self._save_database()
        return True
    
    def get_channel_settings(self, channel_id: str) -> dict:
        """الحصول على إعدادات الحماية لقناة محددة"""
        if str(channel_id) in self._protected_channels:
            return self._protected_channels[str(channel_id)].get('protection_settings', {})
        return {}
    
    def toggle_channel_protection(self, channel_id: str, setting: str) -> bool:
        """تبديل حالة إعداد حماية معين لقناة"""
        if str(channel_id) in self._protected_channels:
            settings = self._protected_channels[str(channel_id)].get('protection_settings', {})
            current = settings.get(setting, False)
            settings[setting] = not current
            
            action = "تفعيل" if not current else "تعطيل"
            owner_id = self._protected_channels[str(channel_id)]['owner_id']
            channel_title = self._protected_channels[str(channel_id)].get('title', '')
            
            setting_names = {
                'block_new_members': 'حظر المنضمين الجدد',
                'block_leaving_members': 'حظر المغادرين',
                'block_no_username': 'حظر المستخدمين بدون يوزر'
            }
            setting_name = setting_names.get(setting, setting)
            
            self._log_activity(owner_id, f"⚙️ {action} {setting_name} في قناة {channel_title}")
            self._save_database()
            return not current
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال القنوات الإجبارية
    # ═══════════════════════════════════════════════════════════════════════════
    
    def add_mandatory_channel(self, channel: str, max_members: int = 0) -> bool:
        """إضافة قناة إلى قائمة الاشتراك الإجباري"""
        channels = self._settings.get('mandatory_channels', [])
        if channel not in channels:
            channels.append(channel)
            self._settings['mandatory_channels'] = channels
            
            if max_members > 0:
                self._mandatory_channels_config[channel] = {
                    'max_members': max_members,
                    'current_members': 0,
                    'added_date': datetime.now().isoformat()
                }
            
            self._save_settings()
            return True
        return False
    
    def increment_mandatory_channel_members(self, channel: str) -> bool:
        """زيادة عداد الأعضاء للقناة الإجبارية عند تحقق مستخدم جديد"""
        if channel in self._mandatory_channels_config:
            config = self._mandatory_channels_config[channel]
            config['current_members'] = config.get('current_members', 0) + 1
            
            if config['current_members'] >= config.get('max_members', 0) > 0:
                self.remove_mandatory_channel(channel)
                return True
                
            self._save_settings()
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # دوال الإحصائيات والتصدير والاستيراد
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_system_stats(self) -> dict:
        """الحصول على إحصائيات شاملة عن النظام"""
        now = datetime.now()
        
        active_vip = 0
        for mid, exp in self._vip_members.items():
            exp_date = exp if isinstance(exp, datetime) else datetime.fromisoformat(exp)
            if exp_date > now:
                active_vip += 1
                
        return {
            'total_members': len(self._members),
            'total_protected_channels': len(self._protected_channels),
            'total_campaigns': len(self._active_campaigns),
            'active_vip': active_vip,
            'blocked_members': len(self.get_blocked_members()),
            'admin_count': len(self._admin_list),
            'total_balance': sum(m.get('balance', 0) for m in self._members.values()),
            'pending_campaigns': len(self._pending_campaigns),
            'active_campaigns_count': len([c for c in self._active_campaigns.values() if c.get('status') == 'active']),
            'completed_campaigns': len([c for c in self._active_campaigns.values() if c.get('status') == 'completed']),
            'active_gifts': len([g for g in self._gift_codes.values() if g.get('is_active', False)]),
            'total_categories': len(self._service_categories),
            'total_services': len(self._services),
            'pending_orders': len(self.get_pending_orders()),
            'welcome_messages': len(self._welcome_messages),
            'total_transfers': len(self._transfer_history)
        }
    
    def get_recent_members(self, count: int = 20) -> List[dict]:
        """الحصول على أحدث الأعضاء المسجلين في النظام"""
        members = list(self._members.values())
        members.sort(key=lambda x: x.get('joined_date', datetime.now()) if isinstance(x.get('joined_date'), datetime) else datetime.now(), reverse=True)
        return members[:count]
    
    def get_all_vip_members(self) -> List[Tuple[int, datetime]]:
        """الحصول على جميع أعضاء VIP مع تواريخ انتهاء اشتراكاتهم"""
        result = []
        for mid, exp in self._vip_members.items():
            exp_date = exp if isinstance(exp, datetime) else datetime.fromisoformat(exp)
            result.append((mid, exp_date))
        return result
    
    def check_expired_vip(self) -> List[int]:
        """فحص انتهاء اشتراكات VIP وإزالة المنتهية"""
        expired = []
        now = datetime.now()
        
        for mid, exp in list(self._vip_members.items()):
            exp_date = exp if isinstance(exp, datetime) else datetime.fromisoformat(exp)
            if exp_date < now:
                del self._vip_members[mid]
                expired.append(mid)
                self._log_activity(mid, "⏰ انتهاء اشتراك VIP بشكل تلقائي")
                
        if expired:
            self._save_database()
        return expired
    
    def get_near_expiry_vip(self) -> List[Tuple[int, int]]:
        """الحصول على المشتركين الذين أوشكت اشتراكاتهم على الانتهاء"""
        near = []
        now = datetime.now()
        
        for mid, exp in self._vip_members.items():
            exp_date = exp if isinstance(exp, datetime) else datetime.fromisoformat(exp)
            days_left = (exp_date - now).days
            
            if days_left in [1, 3, 5]:
                near.append((mid, days_left))
        return near
    
    def export_all_data(self) -> dict:
        """تصدير جميع بيانات النظام إلى قاموس واحد"""
        members_export = {}
        for mid, mdata in self._members.items():
            mcopy = mdata.copy()
            for key in ['first_seen', 'joined_date', 'last_active', 'last_transfer_time', 'captcha_banned_until']:
                if key in mcopy and mcopy[key] and isinstance(mcopy[key], datetime):
                    mcopy[key] = mcopy[key].isoformat()
            members_export[str(mid)] = mcopy
            
        return {
            'export_date': datetime.now().isoformat(),
            'bot_info': {
                'username': GuardianConfig.BOT_USERNAME,
                'admin_id': GuardianConfig.MASTER_ADMIN_ID,
                'admin_username': GuardianConfig.MASTER_ADMIN_USERNAME
            },
            'members': members_export,
            'protected_channels': self._protected_channels,
            'vip_members': {str(k): v.isoformat() if isinstance(v, datetime) else v for k, v in self._vip_members.items()},
            'active_campaigns': self._active_campaigns,
            'pending_campaigns': self._pending_campaigns,
            'campaign_index': self._campaign_index,
            'campaign_stats': self._campaign_stats,
            'gift_codes': self._gift_codes,
            'used_gifts': {str(k): v for k, v in self._used_gifts.items()},
            'activity_history': self._activity_history,
            'transfer_history': self._transfer_history,
            'settings': self._settings.copy(),
            'version': '20.0.0'
        }
    
    def import_all_data(self, data: dict) -> bool:
        """استيراد جميع البيانات من ملف نسخ احتياطي"""
        try:
            self._members.clear()
            self._protected_channels.clear()
            self._vip_members.clear()
            self._active_campaigns.clear()
            self._pending_campaigns.clear()
            self._campaign_index.clear()
            self._campaign_stats.clear()
            self._gift_codes.clear()
            self._used_gifts.clear()
            self._activity_history.clear()
            self._service_categories.clear()
            self._services.clear()
            self._service_orders.clear()
            self._transfer_history.clear()
            
            members_data = data.get('members', {})
            for mid_str, mdata in members_data.items():
                mid = int(mid_str)
                mcopy = mdata.copy()
                for key in ['first_seen', 'joined_date', 'last_active', 'last_transfer_time', 'captcha_banned_until']:
                    if key in mcopy and mcopy[key] and isinstance(mcopy[key], str):
                        try:
                            mcopy[key] = datetime.fromisoformat(mcopy[key])
                        except:
                            mcopy[key] = None if key != 'first_seen' else datetime.now()
                for new_key in ['captcha_verified', 'captcha_attempts', 'transfer_blocked', 'vip_auto_renew']:
                    if new_key not in mcopy:
                        mcopy[new_key] = False if new_key != 'captcha_verified' else (mid == GuardianConfig.MASTER_ADMIN_ID)
                self._members[mid] = mcopy
                
            self._protected_channels = data.get('protected_channels', {})
            
            vip_data = data.get('vip_members', {})
            for mid_str, exp_str in vip_data.items():
                try:
                    self._vip_members[int(mid_str)] = datetime.fromisoformat(exp_str)
                except:
                    pass
                    
            self._active_campaigns = data.get('active_campaigns', {})
            self._pending_campaigns = data.get('pending_campaigns', {})
            self._campaign_index = data.get('campaign_index', {})
            self._campaign_stats = data.get('campaign_stats', {})
            self._gift_codes = data.get('gift_codes', {})
            
            used_data = data.get('used_gifts', {})
            for mid_str, codes in used_data.items():
                self._used_gifts[int(mid_str)] = codes
                
            self._activity_history = data.get('activity_history', [])
            self._transfer_history = data.get('transfer_history', [])
            
            imported_settings = data.get('settings', {})
            if imported_settings:
                self._settings.update(imported_settings)
                
            self._admin_list = set(self._settings.get('admin_list', [GuardianConfig.MASTER_ADMIN_ID]))
            self._mandatory_channels_config = self._settings.get('mandatory_channels_config', {})
            
            self._service_categories = self._settings.get('service_categories', {})
            self._services = self._settings.get('services', {})
            self._service_orders = self._settings.get('service_orders', {})
            self._custom_button_names = self._settings.get('custom_button_names', {})
            self._weekly_referral_winners = self._settings.get('weekly_referral_winners', {})
            self._welcome_messages = self._settings.get('welcome_messages', [])
                
            self._save_database()
            self._save_settings()
            self._ensure_master_exists()
            self._init_default_button_names()
            self._rebuild_indexes()
            
            logger.info(f"✅ تم استيراد البيانات بنجاح: {len(self._members)} عضو")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في استيراد البيانات: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           إنشاء كائن قاعدة البيانات العالمي
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

db = MegaDatabase()

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           الدوال المساعدة
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

async def notify_master(context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    إرسال إشعار مباشر إلى المدير الرئيسي للبوت
    
    تستخدم هذه الدالة لإرسال تنبيهات هامة للمدير مثل:
    - طلبات التمويل الجديدة
    - عمليات التحويل
    - الاشتراكات الجديدة
    - البلاغات والمخالفات
    """
    try:
        await context.bot.send_message(
            chat_id=GuardianConfig.MASTER_ADMIN_ID,
            text=f"🔔 إشعار من بوت تفاعلكم الذكي:\n\n{text}"
        )
    except Exception as e:
        logger.error(f"❌ فشل إرسال إشعار للمدير: {e}")

def get_btn(key: str) -> str:
    """
    الحصول على اسم الزر المخصص أو الاسم الافتراضي
    
    يمكن للمدير تغيير أسماء الأزرار من لوحة التحكم
    لتناسب احتياجات البوت الخاصة به
    """
    return db.get_button_name(key)

async def check_mandatory_channels(member_id: int, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, List[dict]]:
    """
    التحقق من اشتراك العضو في جميع القنوات الإجبارية
    
    تتم هذه العملية دون زيادة العداد - الزيادة تحدث فقط
    عند ضغط المستخدم على زر "تحقق من الاشتراك"
    """
    channels = db._settings.get('mandatory_channels', [])
    not_joined = []
    
    for channel in channels:
        try:
            if 't.me/' in channel:
                username = channel.split('t.me/')[-1].split('/')[0]
                chat_id = f"@{username}"
            elif channel.startswith('@'):
                chat_id = channel
            else:
                chat_id = f"@{channel}"
                
            member = await context.bot.get_chat_member(chat_id, member_id)
            if member.status in ['left', 'kicked']:
                not_joined.append({
                    'id': chat_id,
                    'link': channel if channel.startswith('http') else f"https://t.me/{chat_id.replace('@', '')}",
                    'name': chat_id
                })
        except:
            pass
            
    return len(not_joined) == 0, not_joined

def generate_qr_code(data: str, member_id: int) -> str:
    """
    توليد صورة QR Code تحتوي على بيانات معينة
    
    تستخدم لإنشاء باركود الإحالة الذي يمكن للمستخدم
    مشاركته مع أصدقائه لدعوتهم إلى البوت
    """
    os.makedirs(GuardianConfig.QR_FOLDER, exist_ok=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#1a73e8", back_color="white")
    
    filename = f"{GuardianConfig.QR_FOLDER}/qr_{member_id}.png"
    img.save(filename)
    
    return filename

async def verify_channel_subscription(bot, member_id: int, channel_username: str, channel_id: str = None) -> bool:
    """
    التحقق من اشتراك عضو معين في قناة محددة
    
    تستخدم في نظام تبادل الاشتراكات للتحقق من
    أن العضو مشترك فعلاً في القناة قبل منحه المكافأة
    """
    if channel_username:
        try:
            username = channel_username.replace('https://t.me/', '').replace('@', '').strip()
            username = username.split('/')[0].split('?')[0]
            chat_id = f"@{username}"
            
            member = await bot.get_chat_member(chat_id=chat_id, user_id=member_id)
            
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    
    if channel_id:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=member_id)
            
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    
    return False

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           لوحات المفاتيح
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def build_main_menu(member_id: int) -> InlineKeyboardMarkup:
    """
    بناء القائمة الرئيسية للمستخدم
    
    تحتوي على جميع الأزرار الأساسية:
    - نظام الحماية
    - الخدمات
    - تبادل اشتراك والربح
    - تمويل أعضاء
    - دعوة صديق
    - اشتراك VIP
    - تحويل رصيد
    - معلومات حسابك
    - تواصل مع الدعم
    - لوحة التحكم (للمشرفين فقط)
    """
    keyboard = [
        [
            InlineKeyboardButton(get_btn('menu_protection_system'), callback_data="menu_protection_system"),
            InlineKeyboardButton(get_btn('menu_services'), callback_data="menu_services")
        ],
        [
            InlineKeyboardButton(get_btn('menu_exchange'), callback_data="menu_exchange"),
            InlineKeyboardButton(get_btn('menu_funding'), callback_data="menu_funding")
        ],
        [
            InlineKeyboardButton(get_btn('menu_referral'), callback_data="menu_referral"),
            InlineKeyboardButton(get_btn('menu_vip'), callback_data="menu_vip")
        ],
        [
            InlineKeyboardButton(get_btn('menu_transfer'), callback_data="menu_transfer"),
            InlineKeyboardButton(get_btn('menu_account_info'), callback_data="menu_account_info")
        ],
        [
            InlineKeyboardButton(get_btn('menu_support'), callback_data="menu_support")
        ]
    ]
    
    if db.is_admin(member_id):
        keyboard.append([
            InlineKeyboardButton(get_btn('menu_admin'), callback_data="menu_admin")
        ])
    
    return InlineKeyboardMarkup(keyboard)

def build_protection_menu() -> InlineKeyboardMarkup:
    """
    بناء قائمة نظام الحماية
    
    تحتوي على:
    - قنواتي
    - إضافة قناة
    - حذف قناة
    - حظر المنضمين
    - حظر المغادرين
    - حظر بدون يوزر
    - إعدادات الحماية
    - شرح القسم
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 قنواتي", callback_data="menu_my_channels")],
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="menu_add_channel")],
        [InlineKeyboardButton("🗑 حذف قناة", callback_data="menu_delete_channel")],
        [InlineKeyboardButton("🛡 حظر المنضمين", callback_data="menu_quick_block_join")],
        [InlineKeyboardButton("🚫 حظر المغادرين", callback_data="menu_quick_block_leave")],
        [InlineKeyboardButton("👤 حظر بدون يوزر", callback_data="menu_quick_block_nouser")],
        [InlineKeyboardButton("⚙️ إعدادات الحماية", callback_data="menu_protection")],
        [InlineKeyboardButton("📖 شرح القسم", callback_data="menu_protection_help")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]
    ])

def build_services_menu() -> InlineKeyboardMarkup:
    """بناء قائمة الخدمات مع عرض الأقسام المتاحة"""
    categories = db.get_all_categories()
    keyboard = []
    
    if not categories:
        keyboard.append([InlineKeyboardButton("❌ لا توجد أقسام متاحة حالياً", callback_data="no_action")])
    else:
        for cat in categories:
            keyboard.append([
                InlineKeyboardButton(f"📁 {cat['name']}", callback_data=f"service_cat_{cat['id']}")
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")])
    return InlineKeyboardMarkup(keyboard)

def build_funding_menu() -> InlineKeyboardMarkup:
    """بناء قائمة التمويل"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ تمويل اعضاء الان", callback_data="fund_create")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]
    ])

def build_admin_panel(member_id: int) -> InlineKeyboardMarkup:
    """
    بناء لوحة تحكم المدير الكاملة
    
    تحتوي على جميع أزرار الإدارة:
    - احصائيات
    - آخر 20 عضو
    - أعضاء VIP
    - أعلى 10 أرصدة
    - شحن رصيد
    - خصم رصيد
    - انشاء هدية
    - شحن الكل
    - خصم من الكل
    - إدارة الحظر
    - قنوات إجبارية
    - بحث عن عضو
    - رسالة لعضو
    - حملات معلقة
    - جميع الحملات
    - إدارة الخدمات
    - طلبات معلقة
    - تصدير
    - استيراد
    - سعر VIP
    - التجربة
    - المكافآت
    - أسماء الأزرار
    - رسائل الترحيب
    - إلغاء VIP
    - رفع مشرف (للمدير الرئيسي)
    - حذف مشرف (للمدير الرئيسي)
    - حذف عضو
    - صيانة
    - اذاعة
    """
    is_master = member_id == GuardianConfig.MASTER_ADMIN_ID
    
    keyboard = [
        [
            InlineKeyboardButton("📊 احصائيات", callback_data="admin_stats"),
            InlineKeyboardButton("👥 آخر 20 عضو", callback_data="admin_recent")
        ],
        [
            InlineKeyboardButton("⭐ أعضاء VIP", callback_data="admin_vip_list"),
            InlineKeyboardButton("🏆 أعلى 10 أرصدة", callback_data="admin_top_balance")
        ],
        [
            InlineKeyboardButton("💰 شحن رصيد", callback_data="admin_charge"),
            InlineKeyboardButton("💸 خصم رصيد", callback_data="admin_deduct")
        ],
        [
            InlineKeyboardButton("🎁 انشاء هدية", callback_data="admin_gift"),
            InlineKeyboardButton("📤 شحن الكل", callback_data="admin_charge_all")
        ],
        [
            InlineKeyboardButton("📥 خصم من الكل", callback_data="admin_deduct_all")
        ],
        [
            InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_blocks"),
            InlineKeyboardButton("📢 قنوات إجبارية", callback_data="admin_mandatory")
        ],
        [
            InlineKeyboardButton("🔍 بحث عن عضو", callback_data="admin_search"),
            InlineKeyboardButton("📨 رسالة لعضو", callback_data="admin_send_message")
        ],
        [
            InlineKeyboardButton("⏳ حملات معلقة", callback_data="admin_pending"),
            InlineKeyboardButton("📋 جميع الحملات", callback_data="admin_campaigns")
        ],
        [
            InlineKeyboardButton("📁 إدارة الخدمات", callback_data="admin_services"),
            InlineKeyboardButton("📝 طلبات معلقة", callback_data="admin_pending_orders")
        ],
        [
            InlineKeyboardButton("📥 تصدير", callback_data="admin_export"),
            InlineKeyboardButton("📤 استيراد", callback_data="admin_import")
        ],
        [
            InlineKeyboardButton("💵 سعر VIP", callback_data="admin_vip_price"),
            InlineKeyboardButton("⏰ التجربة", callback_data="admin_trial_days")
        ],
        [
            InlineKeyboardButton("🎁 المكافآت", callback_data="admin_rewards"),
            InlineKeyboardButton("✏️ أسماء الأزرار", callback_data="admin_button_names")
        ],
        [
            InlineKeyboardButton("📨 رسائل الترحيب", callback_data="admin_welcome_msgs")
        ],
        [
            InlineKeyboardButton("❌ إلغاء VIP", callback_data="admin_cancel_vip")
        ],
    ]
    
    if is_master:
        keyboard.append([
            InlineKeyboardButton("👑 رفع مشرف", callback_data="admin_promote"),
            InlineKeyboardButton("⬇️ حذف مشرف", callback_data="admin_demote")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🗑 حذف عضو", callback_data="admin_delete_member"),
        InlineKeyboardButton("🔧 صيانة", callback_data="admin_maintenance")
    ])
    keyboard.append([
        InlineKeyboardButton("📣 اذاعة", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def build_service_management_menu() -> InlineKeyboardMarkup:
    """بناء قائمة إدارة الخدمات والأقسام"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 إضافة قسم", callback_data="admin_add_category")],
        [InlineKeyboardButton("➕ إضافة خدمة", callback_data="admin_add_service")],
        [InlineKeyboardButton("✏️ تغيير اسم قسم", callback_data="admin_rename_category_menu")],
        [InlineKeyboardButton("✏️ تغيير اسم خدمة", callback_data="admin_rename_service_menu")],
        [InlineKeyboardButton("🗑 حذف قسم", callback_data="admin_delete_category_menu")],
        [InlineKeyboardButton("❌ حذف خدمة", callback_data="admin_delete_service_menu")],
        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
    ])

def build_welcome_messages_menu() -> InlineKeyboardMarkup:
    """بناء قائمة إدارة رسائل الترحيب"""
    msgs = db.get_welcome_messages()
    keyboard = []
    for msg in msgs:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑 رسالة #{msg.get('id')} - {msg.get('type', 'نص')}",
                callback_data=f"del_wmsg_{msg.get('id')}"
            )
        ])
    keyboard.append([InlineKeyboardButton("➕ إضافة رسالة نصية", callback_data="add_wmsg_text")])
    keyboard.append([InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)

def build_button_names_menu() -> InlineKeyboardMarkup:
    """بناء قائمة تغيير أسماء الأزرار"""
    buttons = [
        ('menu_services', '⚡ الخدمات'),
        ('menu_protection_system', '🛡 نظام الحماية'),
        ('menu_exchange', '🔄 تبادل اشتراك والربح'),
        ('menu_funding', '💰 تمويل اعضاء'),
        ('menu_referral', '🔗 دعوة صديق'),
        ('menu_vip', '⭐ اشتراك VIP'),
        ('menu_support', '💬 تواصل مع الدعم'),
        ('menu_admin', '🎛 لوحة التحكم'),
        ('menu_account_info', 'ℹ️ معلومات حسابك'),
        ('menu_transfer', '💸 تحويل رصيد'),
    ]
    
    keyboard = []
    for key, default in buttons:
        current = db.get_button_name(key)
        keyboard.append([InlineKeyboardButton(f"✏️ {current}", callback_data=f"edit_btn_{key}")])
    
    keyboard.append([InlineKeyboardButton("🔄 استعادة الأسماء الافتراضية", callback_data="reset_buttons")])
    keyboard.append([InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)

def build_blocks_menu() -> InlineKeyboardMarkup:
    """بناء قائمة إدارة الحظر"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 حظر عضو", callback_data="block_add")],
        [InlineKeyboardButton("✅ فك حظر عضو", callback_data="block_remove")],
        [InlineKeyboardButton("📋 عرض المحظورين", callback_data="block_list")],
        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
    ])

def build_rewards_menu() -> InlineKeyboardMarkup:
    """بناء قائمة المكافآت والإعدادات المالية"""
    inviter = db._settings.get('inviter_reward', GuardianConfig.INVITER_REWARD_AMOUNT)
    invited = db._settings.get('invited_reward', GuardianConfig.INVITED_REWARD_AMOUNT)
    subscribe = db._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT)
    funding = db._settings.get('funding_price_per_member', GuardianConfig.FUNDING_PRICE_PER_MEMBER)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👤 مكافأة الداعي: {inviter} IQD", callback_data="reward_inviter")],
        [InlineKeyboardButton(f"🆕 مكافأة المدعو: {invited} IQD", callback_data="reward_invited")],
        [InlineKeyboardButton(f"✅ مكافأة الاشتراك: {subscribe} IQD", callback_data="reward_subscribe")],
        [InlineKeyboardButton(f"👥 سعر تمويل العضو: {funding} IQD", callback_data="reward_funding")],
        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
    ])

def build_mandatory_menu() -> InlineKeyboardMarkup:
    """بناء قائمة القنوات الإجبارية"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="mandatory_add")],
        [InlineKeyboardButton("📋 عرض القنوات", callback_data="mandatory_list")],
        [InlineKeyboardButton("🗑 حذف قناة", callback_data="mandatory_delete_menu")],
        [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
    ])

def build_channels_list(member_id: int, prefix: str) -> Optional[InlineKeyboardMarkup]:
    """بناء قائمة القنوات المحمية للعضو"""
    channels = db.get_member_channels(member_id)
    if not channels:
        return None
        
    keyboard = []
    for ch_id in channels:
        ch_data = db._protected_channels.get(str(ch_id), {})
        title = ch_data.get('title', 'قناة')
        if len(title) > 30:
            title = title[:27] + "..."
        keyboard.append([
            InlineKeyboardButton(f"📢 {title}", callback_data=f"{prefix}_{ch_id}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")])
    return InlineKeyboardMarkup(keyboard)

def build_channel_settings(channel_id: str) -> InlineKeyboardMarkup:
    """بناء قائمة إعدادات الحماية لقناة محددة"""
    settings = db.get_channel_settings(channel_id)
    
    block_join = settings.get('block_new_members', False)
    block_leave = settings.get('block_leaving_members', False)
    block_nouser = settings.get('block_no_username', False)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🛡 حظر المنضمين: {'✅ مفعل' if block_join else '❌ معطل'}",
            callback_data=f"toggle_block_new_{channel_id}"
        )],
        [InlineKeyboardButton(
            f"🚫 حظر المغادرين: {'✅ مفعل' if block_leave else '❌ معطل'}",
            callback_data=f"toggle_block_leave_{channel_id}"
        )],
        [InlineKeyboardButton(
            f"👤 حظر بدون يوزر: {'✅ مفعل' if block_nouser else '❌ معطل'}",
            callback_data=f"toggle_block_nouser_{channel_id}"
        )],
        [InlineKeyboardButton("📊 إحصائيات", callback_data=f"stats_{channel_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection")]
    ])

def build_exchange_page(campaigns: List[dict], page: int = 0) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """بناء صفحة تبادل الاشتراك والربح مع التصفح"""
    if not campaigns:
        return "📊 لا توجد قنوات متاحة حالياً للتبادل.\n\nيمكنك العودة في وقت لاحق عندما تتوفر حملات جديدة.", None
    
    per_page = GuardianConfig.CHANNELS_PER_PAGE
    total_pages = (len(campaigns) + per_page - 1) // per_page
    
    if page >= total_pages:
        page = 0
    elif page < 0:
        page = total_pages - 1
    
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(campaigns))
    page_campaigns = campaigns[start_idx:end_idx]
    
    total_possible_points = len(campaigns) * db._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT)
    
    text = f"""
📢 اشترك بالقنوات الموجودة للحصول على النقاط والمكافآت

💰 كل قناة تمنحك {db._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT)} نقطة
🎯 إجمالي النقاط الممكنة: {total_possible_points} نقطة
📄 الصفحة {page + 1} من {total_pages}

⚠️ ملاحظة هامة: يجب الاشتراك في القناة أولاً ثم الضغط على زر "تحقق من الاشتراكات" للحصول على النقاط. لن تحصل على نقاط إذا لم تكن مشتركاً فعلياً في القناة.
"""
    
    keyboard = []
    
    for campaign in page_campaigns:
        channel_title = campaign.get('channel_title', 'قناة')
        channel_link = campaign.get('channel_link', '')
        campaign_id = campaign.get('campaign_id', '')
        
        row = []
        if channel_link:
            row.append(InlineKeyboardButton(f"📢 {channel_title[:20]}", url=channel_link))
        else:
            row.append(InlineKeyboardButton(f"📢 {channel_title[:20]}", callback_data="no_link"))
        
        row.append(InlineKeyboardButton("📝 ابلاغ", callback_data=f"report_ex_{campaign_id}_{page}"))
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("✅ تحقق من الاشتراكات", callback_data=f"verify_page_{page}")
    ])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"exchange_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("التالي ➡️", callback_data=f"exchange_page_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")])
    
    return text, InlineKeyboardMarkup(keyboard)

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           ديكور الحماية
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def guardian_shield(func):
    """
    ديكور للحماية والتحقق من صلاحيات المستخدم
    
    يمنع المستخدمين المحظورين من استخدام أي وظيفة في البوت
    ويوفر حماية ضد الأخطاء غير المتوقعة
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        
        if db.is_member_blocked(user.id):
            if update.callback_query:
                await update.callback_query.answer("❌ تم حظر حسابك من استخدام البوت", show_alert=True)
            elif update.message:
                await update.message.reply_text("❌ تم حظر حسابك من استخدام البوت")
            return
        
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"❌ خطأ في {func.__name__}: {e}")
            if update.callback_query:
                await update.callback_query.answer("❌ حدث خطأ غير متوقع", show_alert=True)
            raise
    return wrapper

async def check_mandatory_before_action(update: Update, context: ContextTypes.DEFAULT_TYPE, member_id: int) -> bool:
    """
    التحقق من الاشتراك في القنوات الإجبارية قبل تنفيذ أي إجراء
    
    مشتركي VIP والمدير الرئيسي معفيون من هذا التحقق
    """
    if db.is_exempt_from_mandatory(member_id):
        return True
    
    is_joined, not_joined = await check_mandatory_channels(member_id, context)
    
    if not is_joined:
        keyboard = []
        for ch in not_joined:
            btn_text = f"📢 {ch['name'].replace('@', '')[:20]}"
            keyboard.append([InlineKeyboardButton(btn_text, url=ch['link'])])
        keyboard.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="verify_mandatory")])
        
        channels_text = "\n".join([f"• {ch['name']}" for ch in not_joined])
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                f"⚠️ يجب الاشتراك في جميع القنوات التالية لاستخدام البوت:\n\n"
                f"{channels_text}\n\n"
                f"بعد الاشتراك في جميع القنوات، اضغط على زر 'تحقق من الاشتراك' للمتابعة.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"⚠️ يجب الاشتراك في جميع القنوات التالية لاستخدام البوت:\n\n"
                f"{channels_text}\n\n"
                f"بعد الاشتراك في جميع القنوات، اضغط على زر 'تحقق من الاشتراك' للمتابعة.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return False
    return True

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           دوال عرض الواجهات
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

async def show_main_menu(update: Update, member_id: int):
    """
    عرض القائمة الرئيسية للمستخدم مع معلومات حسابه
    
    تعرض:
    - حالة الحساب (VIP، تجريبي، منتهي)
    - الرصيد الحالي
    - عدد القنوات المضافة
    - مميزات VIP إذا كان مشتركاً
    """
    can_use, status = db.can_use_bot(member_id)
    member = db.get_member(member_id)
    channels_count = len(member.get('protected_channels', []))
    max_channels = db.get_max_channels(member_id)
    price = db._settings.get('vip_price', GuardianConfig.DEFAULT_VIP_PRICE)
    free_days = db._settings.get('free_trial_days', GuardianConfig.FREE_TRIAL_DAYS)
    is_vip = db.is_vip_member(member_id)
    
    text = f"""
🤖 مرحباً بك في بوت تفاعلكم

🛡 حالة حسابك: {status}
💰 رصيدك الحالي: {member.get('balance', 0):,} IQD
📊 القنوات المضافة: {channels_count} من {max_channels}

🎁 فترة تجريبية مجانية: {free_days} يوم
⭐ سعر الاشتراك VIP: {price:,} IQD / شهر
"""
    
    if is_vip:
        text += f"""
✨ مميزات VIP الخاصة بك:
• 🎁 خصم {GuardianConfig.VIP_DISCOUNT_PERCENT}% على جميع الخدمات
• 🚀 تمويل مباشر بدون انتظار موافقة
• 🛡 إعفاء من الاشتراك في القنوات الإجبارية
• 💰 هدية {GuardianConfig.VIP_BONUS_PERCENT}% عند كل عملية شحن
• 🔄 تجديد تلقائي للاشتراك
"""
    
    text += "\nاستخدم الأزرار أدناه للتحكم في البوت:"
    
    keyboard = build_main_menu(member_id)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text=text, reply_markup=keyboard)

async def show_account_info(update: Update, member_id: int):
    """
    عرض معلومات الحساب الكاملة للمستخدم
    
    تعرض:
    - الايدي والاسم واليوزر
    - الرصيد وتاريخ التسجيل
    - حالة الحساب والاشتراك
    - إحصائيات القنوات والمدعوين
    - حالة التحويل
    - مكافآت الإحالة
    """
    query = update.callback_query
    member = db.get_member(member_id)
    
    mid = member.get('member_id', 'غير معروف')
    username = member.get('username', 'بدون يوزر')
    display_name = member.get('display_name', '')
    balance = member.get('balance', 0)
    joined = member.get('joined_date', '')
    if isinstance(joined, datetime):
        joined = joined.strftime('%Y-%m-%d %H:%M')
    
    is_vip = "⭐ VIP" if db.is_vip_member(member_id) else "👤 عادي"
    if db.is_vip_member(member_id):
        expiry = db.get_vip_expiry_date(member_id)
        if expiry:
            days_left = (expiry - datetime.now()).days
            is_vip = f"⭐ VIP | متبقي {days_left} يوم"
    
    can_use, status = db.can_use_bot(member_id)
    channels_count = len(member.get('protected_channels', []))
    referrals_count = len(member.get('referred_members', []))
    referral_earnings = member.get('referral_earnings', 0)
    campaigns_completed = len(member.get('completed_campaigns', []))
    campaign_earnings = member.get('campaign_earnings', 0)
    
    transfer_blocked = "❌ مقيد" if member.get('transfer_blocked', False) else "✅ مسموح"
    
    inviter_reward = db._settings.get('inviter_reward', GuardianConfig.INVITER_REWARD_AMOUNT)
    invited_reward = db._settings.get('invited_reward', GuardianConfig.INVITED_REWARD_AMOUNT)
    
    text = f"""
ℹ️ معلومات حسابك الكاملة

🆔 الايدي: `{mid}`
👤 الاسم: {display_name}
📱 اليوزر: @{username}
💰 الرصيد: {balance:,} IQD
📅 تاريخ التسجيل: {joined}
🛡 حالة الحساب: {status}
⭐ الاشتراك: {is_vip}
💸 حالة التحويل: {transfer_blocked}

📊 إحصائيات نشاطك:
• القنوات المحمية: {channels_count}
• عدد المدعوين: {referrals_count}
• أرباح الإحالات: {referral_earnings:,} IQD
• الحملات المكتملة: {campaigns_completed}
• أرباح الحملات: {campaign_earnings:,} IQD

💰 مكافآت نظام الإحالة:
• مكافأة الداعي: {inviter_reward:,} IQD عن كل صديق
• مكافأة المدعو: {invited_reward:,} IQD عند التسجيل

📞 للدعم الفني والمساعدة: @{GuardianConfig.MASTER_ADMIN_USERNAME}
"""
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]]),
        parse_mode=ParseMode.MARKDOWN
    )

async def show_vip_menu(update: Update, member_id: int):
    """
    عرض قائمة VIP مع جميع المميزات والتفاصيل
    
    إذا كان المستخدم مشترك VIP: يعرض المتبقي والمميزات
    إذا لم يكن مشتركاً: يعرض السعر والمميزات للتشجيع على الاشتراك
    """
    query = update.callback_query
    member = db.get_member(member_id)
    price = db._settings.get('vip_price', GuardianConfig.DEFAULT_VIP_PRICE)
    
    if db.is_vip_member(member_id):
        expiry = db.get_vip_expiry_date(member_id)
        if expiry:
            days = (expiry - datetime.now()).days
            text = f"""
✅ أنت مشترك VIP حالياً!

📅 المتبقي على اشتراكك: {days} يوم
💰 رصيدك الحالي: {member.get('balance', 0):,} IQD

✨ مميزات VIP الخاصة بك:
• 🎁 خصم {GuardianConfig.VIP_DISCOUNT_PERCENT}% على جميع الخدمات
• 🚀 تمويل مباشر بدون انتظار موافقة
• 🛡 إعفاء من الاشتراك في القنوات الإجبارية
• 💰 هدية {GuardianConfig.VIP_BONUS_PERCENT}% على كل عملية شحن
• 🔄 تجديد تلقائي للاشتراك
• 📊 إضافة حتى {GuardianConfig.VIP_CHANNELS_LIMIT} قنوات حماية
• ⭐ أولوية في الدعم الفني

يمكنك الاستمتاع بجميع هذه المميزات حتى تاريخ انتهاء الاشتراك.
"""
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]])
            )
            return
    
    keyboard = [
        [InlineKeyboardButton("✅ تأكيد الاشتراك", callback_data="confirm_vip")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="menu_main")]
    ]
    
    text = f"""
⭐ الاشتراك في VIP

💰 سعر الاشتراك: {price:,} IQD
📅 مدة الاشتراك: {GuardianConfig.VIP_DURATION_DAYS} يوم كامل
💳 رصيدك الحالي: {member.get('balance', 0):,} IQD

✨ ستحصل على جميع هذه المميزات فور الاشتراك:
• 🎁 خصم {GuardianConfig.VIP_DISCOUNT_PERCENT}% على جميع الخدمات
• 🚀 تمويل مباشر بدون انتظار موافقة
• 🛡 إعفاء من الاشتراك في القنوات الإجبارية
• 💰 هدية {GuardianConfig.VIP_BONUS_PERCENT}% على كل عملية شحن
• 🔄 تجديد تلقائي للاشتراك
• 📊 إضافة حتى {GuardianConfig.VIP_CHANNELS_LIMIT} قنوات حماية
• ⭐ أولوية في الدعم الفني

📞 للشحن والاستفسار: @{GuardianConfig.MASTER_ADMIN_USERNAME}
"""
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_referral_menu(update: Update, member_id: int):
    """
    عرض قائمة الإحالة مع أفضل 5 مشاركين
    
    تعرض:
    - إحصائيات الإحالة الخاصة بالمستخدم
    - المكافآت المتاحة
    - أفضل 5 مشاركين في نظام الإحالة
    - رابط الإحالة الخاص
    """
    query = update.callback_query
    member = db.get_member(member_id)
    invited = len(member.get('referred_members', []))
    earned = member.get('referral_earnings', 0)
    link = db.get_referral_link(member_id)
    
    inviter_reward = db._settings.get('inviter_reward', GuardianConfig.INVITER_REWARD_AMOUNT)
    invited_reward = db._settings.get('invited_reward', GuardianConfig.INVITED_REWARD_AMOUNT)
    
    top_referrers = db.get_top_referrers(5)
    top_text = ""
    if top_referrers:
        top_text = "\n🏆 أفضل 5 مشاركين:\n"
        for i, ref in enumerate(top_referrers, 1):
            ref_id = ref.get('member_id', 'غير معروف')
            ref_count = len(ref.get('referred_members', []))
            if ref_count > 0:
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1] if i <= 5 else f"{i}️⃣"
                top_text += f"{medal} ايدي: `{ref_id}` ({ref_count} دعوة)\n"
    
    text = f"""
🔗 نظام دعوة الأصدقاء

🎁 شارك رابط الدعوة الخاص بك واربح المكافآت!

📊 إحصائياتك:
• عدد الأشخاص الذين دعوتهم: {invited}
• إجمالي أرباحك من الإحالات: {earned:,} IQD

💰 المكافآت:
• أنت تحصل على: {inviter_reward:,} IQD عن كل صديق يسجل
• صديقك يحصل على: {invited_reward:,} IQD عند التسجيل
{top_text}

⚠️ ملاحظة هامة: المكافأة تضاف بعد تحقق المدعو من الكابتشا واشتراكه في جميع القنوات الإجبارية.

🔗 رابط الدعوة الخاص بك:
`{link}`

انسخ الرابط وأرسله لأصدقائك للربح!
"""
    keyboard = [
        [InlineKeyboardButton("📤 مشاركة رابط الدعوة", switch_inline_query=link)],
        [InlineKeyboardButton("📱 استخراج باركود", callback_data=f"qr_{member_id}")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def handle_transfer_start(update: Update, context: ContextTypes.DEFAULT_TYPE, member_id: int):
    """
    بدء عملية تحويل الرصيد
    
    يتحقق من:
    - إمكانية التحويل (ليس محظور، لم يحول خلال 24 ساعة)
    - يعرض الرصيد الحالي والحد الأقصى
    """
    query = update.callback_query
    
    can_transfer, msg = db.can_transfer(member_id)
    if not can_transfer:
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]])
        )
        return
    
    member = db.get_member(member_id)
    await query.edit_message_text(
        f"💸 تحويل رصيد إلى مستخدم آخر\n\n"
        f"💰 رصيدك الحالي: {member.get('balance', 0):,} IQD\n"
        f"📊 الحد الأقصى للتحويل: {GuardianConfig.MAX_TRANSFER_AMOUNT:,} IQD\n"
        f"⏰ يمكنك إجراء تحويل واحد فقط كل {GuardianConfig.TRANSFER_COOLDOWN_HOURS} ساعة\n\n"
        f"⚠️ تنبيه هام:\n"
        f"• لا يمكنك التحويل إلى نفسك\n"
        f"• تأكد من ايدي المستخدم قبل التحويل\n"
        f"• عملية التحويل لا يمكن التراجع عنها\n\n"
        f"أرسل ايدي المستخدم المراد التحويل له:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_main")]])
    )
    context.user_data['TRANSFER_ACTION'] = 'wait_target'
    return STATE_WAIT_TRANSFER_TARGET

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           معالج الأزرار التفاعلية
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

@guardian_shield
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج الأزرار التفاعلية الرئيسي
    
    يتعامل مع جميع ضغطات الأزرار في البوت ويقوم بتوجيهها
    إلى الدوال المناسبة حسب نوع الزر المضغوط
    """
    query = update.callback_query
    member_id = update.effective_user.id
    data = query.data
    
    if db.is_member_blocked(member_id) and member_id != GuardianConfig.MASTER_ADMIN_ID:
        await query.edit_message_text("❌ تم حظر حسابك.")
        return
    
    if data not in ["menu_main", "verify_mandatory", "menu_account_info"] and member_id != GuardianConfig.MASTER_ADMIN_ID:
        if not await check_mandatory_before_action(update, context, member_id):
            return
    
    # ═══════════ القائمة الرئيسية والمعلومات ═══════════
    if data == "menu_main":
        await show_main_menu(update, member_id)
    
    elif data == "menu_account_info":
        await show_account_info(update, member_id)
    
    elif data == "verify_mandatory":
        is_joined, _ = await check_mandatory_channels(member_id, context)
        if is_joined:
            channels = db._settings.get('mandatory_channels', [])
            for ch in channels:
                db.increment_mandatory_channel_members(ch)
            db.give_referral_reward(member_id)
            await query.edit_message_text("✅ تم التحقق من اشتراكك في جميع القنوات! أهلاً بك في البوت.")
            await show_main_menu(update, member_id)
        else:
            await query.answer("❌ لم تشترك في جميع القنوات المطلوبة بعد!", show_alert=True)
    
    # ═══════════ نظام الحماية ═══════════
    elif data == "menu_protection_system":
        await query.edit_message_text(
            "🛡 نظام الحماية المتكامل\n\n"
            "يمكنك من خلال هذا القسم حماية قنواتك من المخالفين والمزعجين.\n"
            "اختر ما تريد القيام به من الخيارات أدناه:",
            reply_markup=build_protection_menu()
        )
    
    elif data == "menu_protection_help":
        await query.edit_message_text(
            "📖 شرح مفصل لقسم نظام الحماية\n\n"
            "🛡 هذا القسم يمكنك من حماية قناتك على تيليجرام من:\n\n"
            "1️⃣ حظر المنضمين الجدد:\n"
            "• عند تفعيل هذا الخيار، أي شخص جديد ينضم إلى قناتك يتم حظره تلقائياً ومنعه من الدخول.\n"
            "• مفيد لمنع المتطفلين والمزعجين من دخول قناتك.\n\n"
            "2️⃣ حظر المغادرين:\n"
            "• عند تفعيل هذا الخيار، أي شخص يغادر قناتك يتم حظره تلقائياً ومنعه من العودة مرة أخرى.\n"
            "• مفيد لمنع الأشخاص من الخروج والدخول المتكرر لإزعاج الأعضاء.\n\n"
            "3️⃣ حظر بدون يوزر:\n"
            "• عند تفعيل هذا الخيار، أي شخص ليس لديه يوزر (معرف) في تيليجرام يتم حظره تلقائياً.\n"
            "• مفيد لمنع الحسابات الوهمية وغير الموثوقة من دخول قناتك.\n\n"
            "📋 قنواتي: عرض جميع القنوات التي أضفتها للحماية.\n"
            "➕ إضافة قناة: إضافة قناة جديدة إلى نظام الحماية.\n"
            "🗑 حذف قناة: إزالة قناة من نظام الحماية.\n"
            "⚙️ إعدادات الحماية: تخصيص إعدادات الحماية لكل قناة على حدة.\n\n"
            "⚠️ شروط استخدام الحماية:\n"
            "• يجب رفع البوت كمشرف (أدمن) في القناة المراد حمايتها.\n"
            "• يجب منح البوت صلاحيات: حذف الرسائل، حظر المستخدمين، إضافة مشرفين جدد.\n"
            "• البوت لا يستطيع حظر المشرفين أو مالك القناة.\n"
            "• في حالة عدم عمل الحماية، تأكد من صلاحيات البوت في القناة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]])
        )
    
    elif data == "menu_add_channel":
        channels = db.get_member_channels(member_id)
        max_channels = db.get_max_channels(member_id)
        
        if len(channels) >= max_channels:
            await query.edit_message_text(
                f"❌ لقد وصلت للحد الأقصى من القنوات المسموح بها ({max_channels} قنوات).\n\n"
                f"لإضافة المزيد من القنوات، يمكنك:\n"
                f"• حذف قناة موجودة من قائمة قنواتك.\n"
                f"• الاشتراك في VIP للحصول على حد أقصى {GuardianConfig.VIP_CHANNELS_LIMIT} قنوات.\n\n"
                f"⭐ سعر الاشتراك VIP: {db._settings.get('vip_price', GuardianConfig.DEFAULT_VIP_PRICE):,} IQD",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]])
            )
            return
        
        await query.edit_message_text(
            "📢 إضافة قناة حماية جديدة\n\n"
            "أرسل رابط القناة التي تريد إضافتها إلى نظام الحماية:\n\n"
            "مثال على الروابط المدعومة:\n"
            "• https://t.me/username\n"
            "• @username\n\n"
            "⚠️ شروط إضافة القناة:\n"
            "• يجب رفع البوت كمشرف (أدمن) في القناة.\n"
            "• يجب منح البوت صلاحيات: حذف الرسائل، حظر المستخدمين، إضافة مشرفين جدد.\n"
            "• البوت يجب أن يكون لديه صلاحية الوصول إلى الرسائل.\n\n"
            "إذا لم تكن متأكداً من الصلاحيات، قم بإعادة رفع البوت كمشرف مع جميع الصلاحيات.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_protection_system")]])
        )
        context.user_data['PROT_ACTION'] = 'add_channel'
        return STATE_WAIT_CHANNEL_LINK
    
    elif data == "menu_delete_channel":
        keyboard = build_channels_list(member_id, "del")
        if keyboard:
            await query.edit_message_text(
                "🗑 حذف قناة من الحماية\n\n"
                "اختر القناة التي تريد حذفها من نظام الحماية.\n"
                "لن يتم حذف القناة نفسها من تيليجرام، فقط ستتوقف الحماية عنها.",
                reply_markup=keyboard
            )
        else:
            await query.edit_message_text(
                "❌ ليس لديك أي قنوات حماية مضافة حالياً.\n\n"
                "يمكنك إضافة قنوات جديدة من خلال زر 'إضافة قناة'.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]])
            )
    
    elif data.startswith("del_"):
        channel_id = data.replace("del_", "")
        db.remove_protected_channel(member_id, channel_id)
        await query.edit_message_text(
            "✅ تم حذف القناة من قائمة الحماية بنجاح!\n\n"
            "لن يتم تطبيق أي إعدادات حماية على هذه القناة بعد الآن.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 نظام الحماية", callback_data="menu_protection_system")]])
        )
    
    elif data == "menu_my_channels":
        channels = db.get_member_channels(member_id)
        if not channels:
            await query.edit_message_text(
                "❌ ليس لديك أي قنوات حماية مضافة حالياً.\n\n"
                "يمكنك إضافة قنوات جديدة من خلال زر 'إضافة قناة' في قائمة الحماية.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]])
            )
            return
            
        text = "📋 قنوات الحماية الخاصة بك:\n\n"
        for ch_id in channels:
            ch_data = db._protected_channels.get(str(ch_id), {})
            text += f"• {ch_data.get('title', 'قناة بدون اسم')}\n"
        text += f"\nإجمالي القنوات: {len(channels)}"
            
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]])
        )
    
    elif data == "menu_protection":
        keyboard = build_channels_list(member_id, "settings")
        if keyboard:
            await query.edit_message_text(
                "⚙️ إعدادات الحماية المتقدمة\n\n"
                "اختر القناة التي تريد تعديل إعدادات الحماية الخاصة بها.",
                reply_markup=keyboard
            )
        else:
            await query.edit_message_text(
                "❌ ليس لديك أي قنوات حماية مضافة.\n\n"
                "قم بإضافة قناة أولاً لتتمكن من تعديل إعدادات الحماية.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]])
            )
    
    elif data.startswith("settings_"):
        channel_id = data.replace("settings_", "")
        keyboard = build_channel_settings(channel_id)
        ch_data = db._protected_channels.get(str(channel_id), {})
        title = ch_data.get('title', 'القناة')
        
        await query.edit_message_text(
            f"⚙️ إعدادات الحماية لقناة: {title}\n\n"
            f"اختر الإعداد الذي تريد تفعيله أو تعطيله.\n"
            f"التغييرات تطبق فوراً على القناة.",
            reply_markup=keyboard
        )
    
    elif data.startswith("toggle_"):
        parts = data.split("_")
        if len(parts) >= 4:
            setting = f"{parts[1]}_{parts[2]}"
            channel_id = parts[3]
            
            db.toggle_channel_protection(channel_id, setting)
            keyboard = build_channel_settings(channel_id)
            ch_data = db._protected_channels.get(str(channel_id), {})
            title = ch_data.get('title', 'القناة')
            
            await query.answer("✅ تم تحديث الإعدادات بنجاح", show_alert=True)
            await query.edit_message_text(
                f"⚙️ إعدادات الحماية لقناة: {title}\n\n"
                f"اختر الإعداد الذي تريد تفعيله أو تعطيله.\n"
                f"التغييرات تطبق فوراً على القناة.",
                reply_markup=keyboard
            )
    
    elif data.startswith("stats_"):
        channel_id = data.replace("stats_", "")
        ch_data = db._protected_channels.get(str(channel_id), {})
        title = ch_data.get('title', 'القناة')
        stats = ch_data.get('stats', {})
        
        text = f"📊 إحصائيات قناة: {title}\n\n"
        text += f"👥 عدد الأعضاء الذين انضموا: {stats.get('total_joined', 0)}\n"
        text += f"🚪 عدد الأعضاء الذين غادروا: {stats.get('total_left', 0)}\n"
        text += f"🔨 عدد الأعضاء المحظورين: {stats.get('total_blocked', 0)}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=f"settings_{channel_id}")]])
        )
    
    elif data == "menu_quick_block_join":
        await handle_quick_protection(update, context, member_id, "block_new_members", "حظر المنضمين الجدد")
    elif data == "menu_quick_block_leave":
        await handle_quick_protection(update, context, member_id, "block_leaving_members", "حظر المغادرين")
    elif data == "menu_quick_block_nouser":
        await handle_quick_protection(update, context, member_id, "block_no_username", "حظر بدون يوزر")
    
    # ═══════════ الخدمات ═══════════
    elif data == "menu_services":
        await query.edit_message_text(
            "⚡ قسم الخدمات\n\n"
            "يمكنك تصفح الأقسام والخدمات المتاحة وشراء ما يناسبك.\n"
            "اختر القسم الذي تريد تصفح خدماته:",
            reply_markup=build_services_menu()
        )
    
    elif data.startswith("service_cat_"):
        cat_id = data.replace("service_cat_", "")
        services = db.get_category_services(cat_id)
        cat_data = db._service_categories.get(cat_id, {})
        cat_name = cat_data.get('name', 'القسم')
        cat_desc = cat_data.get('description', '')
        
        if not services:
            await query.edit_message_text(
                f"📁 {cat_name}\n{cat_desc}\n\n"
                f"❌ لا توجد خدمات متاحة في هذا القسم حالياً.\n"
                f"سيتم إضافة خدمات جديدة قريباً.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الأقسام", callback_data="menu_services")]])
            )
            return
        
        keyboard = []
        for srv in services:
            keyboard.append([
                InlineKeyboardButton(f"📌 {srv['name']}", callback_data=f"service_view_{srv['id']}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 الأقسام", callback_data="menu_services")])
        
        await query.edit_message_text(
            f"📁 {cat_name}\n{cat_desc}\n\n"
            f"اختر الخدمة التي تريد الاطلاع على تفاصيلها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("service_view_"):
        srv_id = data.replace("service_view_", "")
        srv = db._services.get(srv_id)
        
        if not srv:
            await query.answer("❌ الخدمة غير موجودة", show_alert=True)
            return
        
        discount = db.get_vip_discount(member_id)
        original_price = srv.get('price_per_1000', 0)
        final_price = db.get_service_price_with_vip_discount(member_id, srv_id)
        
        discount_text = ""
        if discount > 0:
            discount_text = f"\n🎁 السعر بعد خصم VIP ({discount}%): {final_price:,} IQD لكل 1000"
        
        text = f"""
📌 {srv['name']}

📝 وصف الخدمة: {srv['description']}
💰 السعر لكل 1000: {original_price:,} IQD{discount_text}
⏰ المدة المتوقعة للتسليم: {srv['duration']}
📊 الحد الأدنى للطلب: {srv['min_amount']}
📊 الحد الأقصى للطلب: {srv['max_amount']}
🔗 الرابط: إجباري (يجب إرفاق رابط مع الطلب)

هل تريد تقديم طلب شراء لهذه الخدمة؟
"""
        keyboard = [
            [InlineKeyboardButton("✅ تقديم طلب", callback_data=f"order_service_{srv_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"service_cat_{srv['category_id']}")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("order_service_"):
        srv_id = data.replace("order_service_", "")
        srv = db._services.get(srv_id)
        
        if not srv:
            await query.answer("❌ الخدمة غير موجودة", show_alert=True)
            return
        
        context.user_data['ORDER_SRV_ID'] = srv_id
        context.user_data['ORDER_SRV_PRICE'] = db.get_service_price_with_vip_discount(member_id, srv_id)
        context.user_data['ORDER_SRV_NAME'] = srv['name']
        context.user_data['ORDER_MIN'] = srv['min_amount']
        context.user_data['ORDER_MAX'] = srv['max_amount']
        context.user_data['ORDER_ACTION'] = 'wait_quantity'
        
        await query.edit_message_text(
            f"📌 {srv['name']}\n\n"
            f"أرسل العدد المطلوب من هذه الخدمة:\n\n"
            f"📊 الحد الأدنى: {srv['min_amount']}\n"
            f"📊 الحد الأقصى: {srv['max_amount']}\n"
            f"💰 السعر لكل 1000: {context.user_data['ORDER_SRV_PRICE']:,} IQD\n\n"
            f"سيتم حساب التكلفة الإجمالية تلقائياً بناءً على العدد الذي ترسله.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_services")]])
        )
        return STATE_WAIT_SERVICE_QUANTITY
    
    # ═══════════ التبادل والتمويل ═══════════
    elif data == "menu_exchange":
        campaigns = db.get_uncompleted_campaigns_for_member(member_id)
        text, keyboard = build_exchange_page(campaigns, 0)
        
        if keyboard is None:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]]))
        else:
            await query.edit_message_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    
    elif data.startswith("exchange_page_"):
        page = int(data.replace("exchange_page_", ""))
        campaigns = db.get_uncompleted_campaigns_for_member(member_id)
        text, keyboard = build_exchange_page(campaigns, page)
        
        if keyboard is None:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]]))
        else:
            await query.edit_message_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    
    elif data.startswith("verify_page_"):
        page = int(data.replace("verify_page_", ""))
        
        all_campaigns = db.get_uncompleted_campaigns_for_member(member_id)
        per_page = GuardianConfig.CHANNELS_PER_PAGE
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(all_campaigns))
        page_campaigns = all_campaigns[start_idx:end_idx]
        
        if not page_campaigns:
            await query.answer("❌ لا توجد قنوات في هذه الصفحة", show_alert=True)
            return
        
        await query.answer("⏳ جاري التحقق من اشتراكاتك في القنوات...", show_alert=False)
        
        subscribed_ids = []
        for campaign in page_campaigns:
            is_sub = await verify_channel_subscription(
                context.bot, member_id,
                campaign.get('channel_username', '') or campaign.get('channel_link', ''),
                campaign.get('channel_id', '')
            )
            if is_sub:
                subscribed_ids.append(campaign['campaign_id'])
        
        if subscribed_ids:
            count, successful = db.verify_member_subscriptions(member_id, subscribed_ids)
            
            if count > 0:
                reward_per = db._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT)
                total_reward = count * reward_per
                
                await query.answer(f"✅ تمت إضافة {total_reward} نقطة لرصيدك! ({count} قناة)", show_alert=True)
                
                for cid in successful:
                    camp = db.get_campaign(cid)
                    if camp:
                        try:
                            owner_id = camp['owner_id']
                            await context.bot.send_message(
                                chat_id=owner_id,
                                text=f"✅ عضو جديد اشترك في قناتك!\n\n"
                                     f"📺 {camp.get('channel_title', '')}\n"
                                     f"👤 @{update.effective_user.username or update.effective_user.first_name}\n"
                                     f"🎯 متبقي: {camp.get('members_remaining', 0)} عضو"
                            )
                        except:
                            pass
            else:
                await query.answer("❌ لم تتم إضافة نقاط (ربما حصلت عليها مسبقاً)", show_alert=True)
        else:
            await query.answer("❌ لم يتم التحقق من أي اشتراك! تأكد من اشتراكك في القنوات.", show_alert=True)
        
        campaigns = db.get_uncompleted_campaigns_for_member(member_id)
        text, keyboard = build_exchange_page(campaigns, page)
        if keyboard is None:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]]))
        else:
            await query.edit_message_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    
    elif data.startswith("report_ex_"):
        parts = data.split("_")
        campaign_id = parts[2]
        page = int(parts[3]) if len(parts) > 3 else 0
        
        await query.edit_message_text(
            "📝 الإبلاغ عن قناة تمويل\n\n"
            "أرسل سبب الإبلاغ عن هذه القناة.\n"
            "يرجى توضيح المشكلة بالتفصيل ليتم مراجعتها من قبل الإدارة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data=f"exchange_page_{page}")]])
        )
        context.user_data['REPORT_ID'] = campaign_id
        context.user_data['REPORT_PAGE'] = page
        context.user_data['REPORT_ACTION'] = 'report_campaign'
        return STATE_WAIT_REPORT_REASON
    
    elif data == "menu_funding":
        await query.edit_message_text(
            "💰 قسم التمويل\n\n"
            "يمكنك تمويل قناتك بعدد من الأعضاء للمساعدة في زيادة التفاعل.\n"
            "اختر 'تمويل أعضاء الان' للبدء في إنشاء حملة تمويل جديدة.",
            reply_markup=build_funding_menu()
        )
        
    elif data == "fund_create":
        price = db._settings.get('funding_price_per_member', GuardianConfig.FUNDING_PRICE_PER_MEMBER)
        is_vip = db.is_vip_member(member_id)
        vip_text = "\n\n✨ أنت مشترك VIP: سيتم تفعيل حملتك مباشرة بدون انتظار موافقة الإدارة!" if is_vip else "\n\n⏳ سيتم مراجعة طلبك من قبل الإدارة قبل التفعيل."
        
        await query.edit_message_text(
            f"⚡ تمويل اعضاء الان\n\n"
            f"💰 سعر العضو الواحد: {price} IQD\n\n"
            f"📢 أرسل رابط قناتك التي تريد تمويلها:\n"
            f"مثال: @username أو https://t.me/username\n\n"
            f"⚠️ ملاحظات مهمة قبل الطلب:\n"
            f"• يجب رفع البوت كمشرف في القناة مع جميع الصلاحيات.\n"
            f"• عند الموافقة، سيتم إضافة القناة إلى قسم تبادل الاشتراك والربح.\n"
            f"• لا يمكنك إنشاء حملة لنفس القناة إذا كانت هناك حملة نشطة مسبقاً.\n"
            f"• سعر العضو قابل للتغيير حسب إعدادات البوت."
            f"{vip_text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_funding")]])
        )
        context.user_data['FUND_ACTION'] = 'funding_channel'
        return STATE_WAIT_FUNDING_CHANNEL
    
    # ═══════════ الإحالة ═══════════
    elif data == "menu_referral":
        await show_referral_menu(update, member_id)
    
    # ═══════════ VIP ═══════════
    elif data == "menu_vip":
        await show_vip_menu(update, member_id)
    
    elif data == "confirm_vip":
        success, message = db.subscribe_vip(member_id)
        if success:
            await query.edit_message_text(
                f"{message}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]])
            )
            await notify_master(context, f"⭐ العضو {member_id} اشترك في VIP!")
        else:
            await query.edit_message_text(
                f"{message}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_vip")]])
            )
    
    # ═══════════ الدعم ═══════════
    elif data == "menu_support":
        await query.edit_message_text(
            f"💬 تواصل مع مسؤول البوت\n\n"
            f"👤 للدعم الفني والاستفسارات:\n"
            f"• تيليجرام: @{GuardianConfig.MASTER_ADMIN_USERNAME}\n\n"
            f"📞 للشحن والمساعدة:\n"
            f"• راسل الدعم مباشرة على الرابط أعلاه\n\n"
            f"🕐 مواعيد الرد:\n"
            f"• يتم الرد خلال 24 ساعة كحد أقصى",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📱 راسل @{GuardianConfig.MASTER_ADMIN_USERNAME}", url=f"https://t.me/{GuardianConfig.MASTER_ADMIN_USERNAME}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="menu_main")]
            ])
        )
    
    # ═══════════ تحويل رصيد ═══════════
    elif data == "menu_transfer":
        await handle_transfer_start(update, context, member_id)
    
    # ═══════════ لوحة التحكم ═══════════
    elif data == "menu_admin":
        if not db.is_admin(member_id):
            await query.answer("❌ غير مصرح لك بالوصول إلى لوحة التحكم", show_alert=True)
            return
        await query.edit_message_text(
            "🎛 لوحة تحكم المدير\n\n"
            "مرحباً بك في لوحة التحكم الرئيسية. من هنا يمكنك إدارة جميع جوانب البوت.\n"
            "اختر العملية التي تريد القيام بها من الأزرار أدناه:",
            reply_markup=build_admin_panel(member_id)
        )
    
    elif data == "admin_services":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📁 إدارة قسم الخدمات\n\n"
            "من هنا يمكنك إدارة الأقسام والخدمات المتاحة في البوت.\n"
            "يمكنك إضافة أقسام جديدة، إضافة خدمات، تغيير الأسماء، أو حذف الأقسام والخدمات.",
            reply_markup=build_service_management_menu()
        )
    
    elif data == "admin_add_category":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📁 إضافة قسم جديد\n\n"
            "أرسل اسم القسم الذي تريد إضافته.\n"
            "مثال: 'خدمات تيليجرام'، 'خدمات يوتيوب'، 'تصميم'...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_category_name'
        return STATE_WAIT_SERVICE_CATEGORY_NAME
    
    elif data == "admin_add_service":
        if not db.is_admin(member_id): return
        categories = db.get_all_categories()
        if not categories:
            await query.edit_message_text(
                "❌ لا توجد أقسام متاحة.\n\n"
                "يجب إضافة قسم أولاً قبل إضافة الخدمات.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]])
            )
            return
        keyboard = [[InlineKeyboardButton(f"📁 {cat['name']}", callback_data=f"add_srv_to_{cat['id']}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
        await query.edit_message_text(
            "اختر القسم الذي تريد إضافة الخدمة الجديدة إليه:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("add_srv_to_"):
        cat_id = data.replace("add_srv_to_", "")
        context.user_data['SRV_CAT_ID'] = cat_id
        await query.edit_message_text(
            "➕ إضافة خدمة جديدة\n\n"
            "الخطوة 1 من 6:\n"
            "أرسل اسم الخدمة التي تريد إضافتها.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_service_name'
        return STATE_WAIT_SERVICE_NAME
    
    elif data == "admin_rename_category_menu":
        if not db.is_admin(member_id): return
        categories = db.get_all_categories()
        if not categories:
            await query.edit_message_text("❌ لا توجد أقسام.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]]))
            return
        keyboard = [[InlineKeyboardButton(f"✏️ {cat['name']}", callback_data=f"rncat_{cat['id']}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
        await query.edit_message_text("اختر القسم الذي تريد تغيير اسمه:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("rncat_"):
        cat_id = data.replace("rncat_", "")
        context.user_data['RENAME_CAT_ID'] = cat_id
        await query.edit_message_text(
            "✏️ تغيير اسم القسم\n\n"
            "أرسل الاسم الجديد للقسم:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'rename_category'
        return STATE_WAIT_RENAME_CATEGORY
    
    elif data == "admin_rename_service_menu":
        if not db.is_admin(member_id): return
        if not db._services:
            await query.edit_message_text("❌ لا توجد خدمات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]]))
            return
        keyboard = [[InlineKeyboardButton(f"✏️ {srv['name']}", callback_data=f"rnsrv_{srv_id}")] for srv_id, srv in db._services.items()]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
        await query.edit_message_text("اختر الخدمة التي تريد تغيير اسمها:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("rnsrv_"):
        srv_id = data.replace("rnsrv_", "")
        context.user_data['RENAME_SRV_ID'] = srv_id
        await query.edit_message_text(
            "✏️ تغيير اسم الخدمة\n\n"
            "أرسل الاسم الجديد للخدمة:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'rename_service'
        return STATE_WAIT_RENAME_SERVICE
    
    elif data == "admin_delete_category_menu":
        if not db.is_admin(member_id): return
        categories = db.get_all_categories()
        if not categories:
            await query.edit_message_text("❌ لا توجد أقسام.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]]))
            return
        keyboard = [[InlineKeyboardButton(f"🗑 {cat['name']}", callback_data=f"delcat_{cat['id']}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
        await query.edit_message_text(
            "🗑 حذف قسم\n\n"
            "⚠️ تحذير: حذف القسم سيؤدي إلى حذف جميع الخدمات المرتبطة به نهائياً.\n"
            "اختر القسم الذي تريد حذفه:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("delcat_"):
        cat_id = data.replace("delcat_", "")
        db.delete_category(cat_id)
        await query.answer("✅ تم حذف القسم بنجاح مع جميع خدماته")
        await query.edit_message_text("✅ تم حذف القسم وجميع الخدمات المرتبطة به بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]]))
    
    elif data == "admin_delete_service_menu":
        if not db.is_admin(member_id): return
        if not db._services:
            await query.edit_message_text("❌ لا توجد خدمات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]]))
            return
        keyboard = [[InlineKeyboardButton(f"❌ {srv['name']}", callback_data=f"delsrv_{srv_id}")] for srv_id, srv in db._services.items()]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")])
        await query.edit_message_text("اختر الخدمة التي تريد حذفها:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("delsrv_"):
        srv_id = data.replace("delsrv_", "")
        db.delete_service(srv_id)
        await query.answer("✅ تم حذف الخدمة بنجاح")
        await query.edit_message_text("✅ تم حذف الخدمة بنجاح.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_services")]]))
    
    # ═══════════ الطلبات المعلقة ═══════════
    elif data == "admin_pending_orders":
        if not db.is_admin(member_id): return
        pending_orders = db.get_pending_orders()
        if not pending_orders:
            await query.edit_message_text("📝 لا توجد طلبات معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
            return
        
        for order in pending_orders[:1]:
            user = db.get_member(order['user_id'])
            service = db._services.get(order['service_id'], {})
            category = db._service_categories.get(order.get('category_id', ''), {})
            
            text = f"""
📝 طلب خدمة جديد بانتظار المراجعة

🆔 رقم الطلب: `{order['order_id']}`
👤 المستخدم: {user.get('display_name', '')} (@{user.get('username', 'بدون')})
🆔 ايدي المستخدم: `{order['user_id']}`
📁 القسم: {category.get('name', 'غير معروف')}
📌 الخدمة: {order.get('service_name', '')}
📊 الكمية المطلوبة: {order['quantity']}
💰 التكلفة الإجمالية: {order['total_cost']:,} IQD
🔗 الرابط المرفق: {order.get('link', 'غير مطلوب')}
📅 تاريخ الطلب: {order.get('created_at', '')}
"""
            keyboard = [
                [
                    InlineKeyboardButton("✅ موافقة", callback_data=f"approve_order_{order['order_id']}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"reject_order_{order['order_id']}")
                ],
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("approve_order_"):
        order_id = data.replace("approve_order_", "")
        order = db.get_order(order_id)
        if db.approve_order(order_id):
            await query.answer("✅ تمت الموافقة على الطلب", show_alert=True)
            if order:
                try:
                    await context.bot.send_message(
                        chat_id=order['user_id'],
                        text=f"✅ تمت الموافقة على طلبك!\n\n📌 الخدمة: {order.get('service_name', '')}\n🆔 رقم الطلب: `{order_id}`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except: pass
        await query.edit_message_text("✅ تمت الموافقة على الطلب وإشعار المستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الطلبات", callback_data="admin_pending_orders")]]))
    
    elif data.startswith("reject_order_"):
        order_id = data.replace("reject_order_", "")
        order = db.get_order(order_id)
        if db.reject_order(order_id):
            await query.answer("❌ تم رفض الطلب", show_alert=True)
            if order:
                try:
                    await context.bot.send_message(
                        chat_id=order['user_id'],
                        text=f"❌ تم رفض طلبك.\n\n📌 الخدمة: {order.get('service_name', '')}\n💰 تم إعادة {order['total_cost']:,} IQD إلى رصيدك\n🆔 رقم الطلب: `{order_id}`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except: pass
        await query.edit_message_text("❌ تم رفض الطلب وإعادة المبلغ للمستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الطلبات", callback_data="admin_pending_orders")]]))
    
    # ═══════════ رسائل الترحيب ═══════════
    elif data == "admin_welcome_msgs":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📨 إدارة رسائل الترحيب\n\n"
            "هذه الرسائل تظهر للمستخدمين الجدد بعد التحقق من الكابتشا والاشتراك في القنوات الإجبارية.\n"
            "يمكنك إضافة رسائل ترحيبية نصية.",
            reply_markup=build_welcome_messages_menu()
        )
    
    elif data == "add_wmsg_text":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📨 إضافة رسالة ترحيب نصية\n\n"
            "أرسل نص الرسالة التي تريد أن تظهر للمستخدمين الجدد.\n"
            "يمكنك استخدام الإيموجي والتنسيق.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_welcome_msgs")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_welcome_msg'
        return STATE_WAIT_WELCOME_MESSAGE
    
    elif data.startswith("del_wmsg_"):
        msg_id = int(data.replace("del_wmsg_", ""))
        db.delete_welcome_message(msg_id)
        await query.answer("✅ تم حذف الرسالة")
        await query.edit_message_text("📨 إدارة رسائل الترحيب", reply_markup=build_welcome_messages_menu())
    
    # ═══════════ إلغاء VIP ═══════════
    elif data == "admin_cancel_vip":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "❌ إلغاء اشتراك VIP\n\n"
            "أرسل ايدي المستخدم الذي تريد إلغاء اشتراك VIP الخاص به.\n"
            "⚠️ تحذير: سيتم حذف جميع مميزات VIP من المستخدم فوراً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'cancel_vip'
        return STATE_WAIT_CANCEL_VIP_USER
    
    # ═══════════ أسماء الأزرار ═══════════
    elif data == "admin_button_names":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "✏️ تغيير أسماء أزرار واجهة المستخدم\n\n"
            "يمكنك تخصيص أسماء الأزرار التي تظهر للمستخدمين.\n"
            "اختر الزر الذي تريد تغيير اسمه:",
            reply_markup=build_button_names_menu()
        )
    
    elif data.startswith("edit_btn_"):
        btn_key = data.replace("edit_btn_", "")
        context.user_data['EDIT_BTN_KEY'] = btn_key
        current_name = db.get_button_name(btn_key)
        await query.edit_message_text(
            f"✏️ الاسم الحالي: {current_name}\n\n"
            f"أرسل الاسم الجديد للزر:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_button_names")]])
        )
        context.user_data['ADMIN_ACTION'] = 'edit_button_name'
        return STATE_WAIT_BUTTON_NEW_NAME
    
    elif data == "reset_buttons":
        if not db.is_admin(member_id): return
        for key in list(db._custom_button_names.keys()):
            db._custom_button_names.pop(key, None)
        db._init_default_button_names()
        db._save_settings()
        await query.edit_message_text("✅ تم استعادة جميع الأسماء الافتراضية للأزرار.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
    
    # ═══════════ باقي لوحة التحكم ═══════════
    elif data == "admin_stats":
        if not db.is_admin(member_id): return
        stats = db.get_system_stats()
        text = f"""
📊 إحصائيات النظام الكاملة

👥 إحصائيات الأعضاء:
• إجمالي الأعضاء المسجلين: {stats['total_members']}
• مشتركي VIP النشطين: {stats['active_vip']}
• الأعضاء المحظورين: {stats['blocked_members']}
• المشرفين: {stats['admin_count']}

📢 إحصائيات القنوات:
• قنوات الحماية: {stats['total_protected_channels']}

💰 إحصائيات مالية:
• إجمالي الأرصدة: {stats['total_balance']:,} IQD

📊 إحصائيات التمويل:
• إجمالي الحملات: {stats['total_campaigns']}
• حملات معلقة: {stats['pending_campaigns']}
• حملات نشطة: {stats['active_campaigns_count']}
• حملات مكتملة: {stats['completed_campaigns']}

📁 الخدمات:
• الأقسام: {stats['total_categories']}
• الخدمات: {stats['total_services']}
• الطلبات المعلقة: {stats['pending_orders']}

📨 رسائل الترحيب: {stats['welcome_messages']}
💸 إجمالي التحويلات: {stats['total_transfers']}
🎁 روابط الهدايا النشطة: {stats['active_gifts']}

⚙️ الإعدادات الحالية:
• سعر الاشتراك VIP: {db._settings.get('vip_price', 0):,} IQD
• فترة التجربة المجانية: {db._settings.get('free_trial_days', 0)} يوم
"""
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تحديث", callback_data="admin_stats")], [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
    
    elif data == "admin_recent":
        if not db.is_admin(member_id): return
        members = db.get_recent_members(20)
        text = "👥 آخر 20 عضو سجلوا في البوت:\n\n"
        for m in members:
            mid = m.get('member_id', 'غير معروف')
            username = m.get('username', 'بدون')
            balance = m.get('balance', 0)
            blocked = "🚫" if m.get('is_blocked') else "✅"
            vip = "⭐" if db.is_vip_member(mid) else "👤"
            text += f"{blocked}{vip} {mid} | @{username} | {balance:,} IQD\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
    
    elif data == "admin_vip_list":
        if not db.is_admin(member_id): return
        vip_members = db.get_all_vip_members()
        text = "⭐ المشتركون في VIP:\n\n"
        for mid, exp in vip_members:
            days = (exp - datetime.now()).days
            if days >= 0:
                text += f"🆔 {mid} | 📅 متبقي {days} يوم\n"
            else:
                text += f"🆔 {mid} | ⏰ منتهي\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
    
    elif data == "admin_top_balance":
        if not db.is_admin(member_id): return
        top_members = db.get_top_balance_members(10)
        text = "🏆 أعلى 10 أعضاء رصيداً:\n\n"
        for i, m in enumerate(top_members, 1):
            mid = m.get('member_id', '?')
            username = m.get('username', 'بدون')
            display_name = m.get('display_name', '')
            balance = m.get('balance', 0)
            text += f"{i}. 🆔 {mid} | @{username} | {display_name}\n   💰 {balance:,} IQD\n\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
    
    elif data == "admin_charge":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "💰 شحن رصيد لعضو\n\n"
            "أرسل ايدي العضو الذي تريد شحن الرصيد له.\n"
            "سيتم إضافة هدية 10% تلقائياً إذا كان العضو مشترك VIP.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'charge_user_id'
        return STATE_WAIT_CHARGE_USER
    
    elif data == "admin_deduct":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "💸 خصم رصيد من عضو\n\n"
            "أرسل ايدي العضو الذي تريد خصم الرصيد منه.\n"
            "سيتم الخصم حتى لو أصبح الرصيد سالباً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'deduct_user_id'
        return STATE_WAIT_DEDUCT_USER
    
    elif data == "admin_charge_all":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📤 شحن رصيد لجميع المستخدمين\n\n"
            "أرسل المبلغ الذي تريد شحنه لجميع الأعضاء.\n"
            "سيتم شحن الرصيد مع هدية VIP للمشتركين تلقائياً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'charge_all_amount'
        return STATE_WAIT_CHARGE_ALL_AMOUNT
    
    elif data == "admin_deduct_all":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📥 خصم رصيد من جميع المستخدمين\n\n"
            "أرسل المبلغ الذي تريد خصمه من جميع الأعضاء.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'deduct_all_amount'
        return STATE_WAIT_DEDUCT_ALL_AMOUNT
    
    elif data == "admin_gift":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "🎁 انشاء رابط هدية\n\n"
            "أرسل عدد الأعضاء المسموح لهم باستخدام رابط الهدية.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'gift_uses'
        return STATE_WAIT_GIFT_USES
    
    elif data == "admin_blocks":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "🚫 إدارة حظر الأعضاء\n\n"
            "يمكنك حظر أو فك حظر الأعضاء وعرض قائمة المحظورين.",
            reply_markup=build_blocks_menu()
        )
    
    elif data == "block_add":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "🚫 حظر عضو\n\n"
            "أرسل ايدي العضو الذي تريد حظره من استخدام البوت.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_blocks")]])
        )
        context.user_data['ADMIN_ACTION'] = 'block_user'
        return STATE_WAIT_BAN_USER
    
    elif data == "block_remove":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "✅ فك حظر عضو\n\n"
            "أرسل ايدي العضو الذي تريد فك الحظر عنه.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_blocks")]])
        )
        context.user_data['ADMIN_ACTION'] = 'unblock_user'
        return STATE_WAIT_UNBAN_USER
    
    elif data == "block_list":
        if not db.is_admin(member_id): return
        blocked = db.get_blocked_members()
        if not blocked:
            text = "✅ لا يوجد أعضاء محظورين حالياً."
        else:
            text = f"🚫 قائمة الأعضاء المحظورين ({len(blocked)}):\n\n"
            for m in blocked[:20]:
                text += f"🆔 {m['member_id']} | @{m.get('username', 'بدون')}\n"
                text += f"   👤 {m.get('display_name', '')}\n"
                text += f"   📝 سبب الحظر: {m.get('block_reason', 'غير محدد')}\n\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_blocks")]]))
    
    elif data == "admin_mandatory":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📢 إدارة قنوات الاشتراك الإجباري\n\n"
            "المستخدمون الجدد مطالبون بالاشتراك في هذه القنوات قبل استخدام البوت.\n"
            "مشتركي VIP معفيون من الاشتراك الإجباري.",
            reply_markup=build_mandatory_menu()
        )
    
    elif data == "mandatory_add":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📢 إضافة قناة اشتراك اجباري\n\n"
            "أرسل رابط القناة أو معرفها:\n"
            "مثال: @username أو https://t.me/username",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_mandatory")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_mandatory_channel'
        return STATE_WAIT_FORCE_CHANNEL
    
    elif data == "mandatory_list":
        if not db.is_admin(member_id): return
        channels = db._settings.get('mandatory_channels', [])
        if not channels:
            text = "❌ لا توجد قنوات اشتراك اجباري مضافة."
        else:
            text = "📋 قنوات الاشتراك الإجباري:\n\n"
            for i, ch in enumerate(channels, 1):
                config = db._mandatory_channels_config.get(ch, {})
                max_members = config.get('max_members', 0)
                current = config.get('current_members', 0)
                extra = f" | 👥 {current}/{max_members}" if max_members > 0 else ""
                text += f"{i}. {ch}{extra}\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_mandatory")]]))
    
    elif data == "mandatory_delete_menu":
        if not db.is_admin(member_id): return
        channels = db._settings.get('mandatory_channels', [])
        if not channels:
            await query.edit_message_text("❌ لا توجد قنوات للحذف.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_mandatory")]]))
            return
        keyboard = [[InlineKeyboardButton(f"🗑 {ch[:40]}", callback_data=f"delmand_{ch}")] for ch in channels]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_mandatory")])
        await query.edit_message_text("اختر القناة التي تريد حذفها من الاشتراك الإجباري:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("delmand_"):
        channel = data.replace("delmand_", "")
        db.remove_mandatory_channel(channel)
        await query.answer("✅ تم حذف القناة بنجاح")
        await query.edit_message_text("✅ تم حذف القناة من قائمة الاشتراك الإجباري.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_mandatory")]]))
    
    elif data == "admin_pending":
        if not db.is_admin(member_id): return
        pending = db.get_pending_campaigns()
        if not pending:
            await query.edit_message_text("📋 لا توجد حملات تمويل معلقة حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]))
            return
        
        for camp in pending[:1]:
            text = f"⏳ حملة تمويل معلقة\n\n📢 اسم القناة: {camp['channel_title']}\n🔗 رابط القناة: {camp['channel_link']}\n👤 صاحب الحملة: {camp['owner_id']}\n👥 عدد الأعضاء المطلوب: {camp['members_required']}\n💰 التكلفة الإجمالية: {camp['total_cost']:,} IQD"
            keyboard = [
                [InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{camp['campaign_id']}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_{camp['campaign_id']}")],
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
            ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    
    elif data.startswith("approve_"):
        if not db.is_admin(member_id): return
        campaign_id = data.replace("approve_", "")
        success, msg, campaign = db.approve_campaign(campaign_id, member_id)
        if success:
            try:
                await context.bot.send_message(
                    chat_id=campaign['owner_id'],
                    text=f"✅ تمت الموافقة على حملة التمويل الخاصة بك!\n\n📢 القناة: {campaign['channel_title']}\n👥 عدد الأعضاء: {campaign['members_required']}\n\n🎯 تم إضافة قناتك إلى قسم تبادل الاشتراك والربح."
                )
            except: pass
        await query.answer(msg)
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_pending")]]))
    
    elif data.startswith("reject_"):
        if not db.is_admin(member_id): return
        campaign_id = data.replace("reject_", "")
        await query.edit_message_text(
            "❌ رفض حملة تمويل\n\n"
            "أرسل سبب رفض الحملة ليتم إعلام صاحبها.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_pending")]])
        )
        context.user_data['REJECT_CAMP_ID'] = campaign_id
        context.user_data['ADMIN_ACTION'] = 'reject_campaign'
        return STATE_WAIT_REPORT_REASON
    
    elif data == "admin_campaigns":
        if not db.is_admin(member_id): return
        campaigns = list(db._active_campaigns.values())
        active = [c for c in campaigns if c.get('status') == 'active']
        text = f"📋 الحملات النشطة ({len(active)}):\n\n"
        keyboard = []
        for camp in active[-5:]:
            text += f"📢 {camp['channel_title']} | {camp['members_joined']}/{camp['members_required']}\n"
            keyboard.append([InlineKeyboardButton(f"❌ إلغاء", callback_data=f"cancel_{camp['campaign_id']}"), InlineKeyboardButton(f"🚫 حظر", callback_data=f"block_owner_{camp['owner_id']}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    
    elif data.startswith("cancel_"):
        if not db.is_admin(member_id): return
        campaign_id = data.replace("cancel_", "")
        db.cancel_campaign(campaign_id, "إلغاء من قبل الإدارة")
        await query.edit_message_text("✅ تم إلغاء الحملة", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_campaigns")]]))
    
    elif data.startswith("block_owner_"):
        if not db.is_admin(member_id): return
        owner_id = int(data.replace("block_owner_", ""))
        db.block_member(owner_id, "حظر إداري بسبب مخالفة في حملة تمويل")
        for cid, camp in db._active_campaigns.items():
            if camp['owner_id'] == owner_id and camp.get('status') == 'active':
                db.cancel_campaign(cid, "حظر صاحب الحملة")
        await query.edit_message_text(f"✅ تم حظر العضو {owner_id} وإلغاء جميع حملاته", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_campaigns")]]))
    
    elif data == "admin_search":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "🔍 بحث عن عضو\n\n"
            "أرسل ايدي العضو للبحث عن جميع معلوماته.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'search_member'
        return STATE_WAIT_SEARCH_USER
    
    elif data == "admin_send_message":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📨 إرسال رسالة لعضو\n\n"
            "أرسل ايدي العضو الذي تريد مراسلته.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'send_message_user'
        return STATE_WAIT_SEND_MESSAGE_USER
    
    elif data == "admin_delete_member":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "🗑 حذف عضو\n\n"
            "⚠️ تحذير: لا يمكن التراجع عن هذا الإجراء!\n"
            "سيتم حذف العضو وجميع بياناته بشكل نهائي.\n\n"
            "أرسل ايدي العضو:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'delete_member'
        return STATE_WAIT_DELETE_USER
    
    elif data == "admin_export":
        if not db.is_admin(member_id): return
        export_data = db.export_all_data()
        os.makedirs(GuardianConfig.BACKUP_FOLDER, exist_ok=True)
        filename = f"{GuardianConfig.BACKUP_FOLDER}/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        with open(filename, 'rb') as f:
            await context.bot.send_document(
                chat_id=member_id,
                document=f,
                caption=f"📥 نسخة احتياطية من بيانات البوت\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📦 الإصدار 20.0.0"
            )
        await query.edit_message_text("✅ تم تصدير جميع البيانات بنجاح", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")]]))
    
    elif data == "admin_import":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📤 استيراد بيانات\n\n"
            "أرسل ملف JSON الذي تم تصديره مسبقاً من البوت.\n\n"
            "⚠️ تحذير هام: سيتم استبدال جميع البيانات الحالية بالبيانات الموجودة في الملف!\n"
            "تأكد من أن الملف هو نسخة احتياطية صالحة من البوت.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'import'
        return STATE_WAIT_BACKUP_FILE
    
    elif data == "admin_vip_price":
        if not db.is_admin(member_id): return
        current = db._settings.get('vip_price', GuardianConfig.DEFAULT_VIP_PRICE)
        await query.edit_message_text(
            f"💵 السعر الحالي لاشتراك VIP: {current:,} IQD\n\n"
            f"أرسل السعر الجديد للاشتراك:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'vip_price'
        return STATE_WAIT_VIP_PRICE
    
    elif data == "admin_trial_days":
        if not db.is_admin(member_id): return
        current = db._settings.get('free_trial_days', GuardianConfig.FREE_TRIAL_DAYS)
        await query.edit_message_text(
            f"⏰ الفترة التجريبية الحالية: {current} يوم\n\n"
            f"أرسل عدد الأيام الجديد للفترة التجريبية:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'trial_days'
        return STATE_WAIT_TRIAL_DAYS
    
    elif data == "admin_rewards":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "🎁 إعدادات المكافآت والأسعار\n\n"
            "يمكنك تغيير قيم المكافآت وأسعار الخدمات من هنا:",
            reply_markup=build_rewards_menu()
        )
    
    elif data == "reward_inviter":
        if not db.is_admin(member_id): return
        current = db._settings.get('inviter_reward', GuardianConfig.INVITER_REWARD_AMOUNT)
        await query.edit_message_text(
            f"👤 مكافأة الداعي الحالية: {current} IQD\n\n"
            f"أرسل القيمة الجديدة للمكافأة:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_rewards")]])
        )
        context.user_data['ADMIN_ACTION'] = 'inviter_reward'
        return STATE_WAIT_INVITER_REWARD
    
    elif data == "reward_invited":
        if not db.is_admin(member_id): return
        current = db._settings.get('invited_reward', GuardianConfig.INVITED_REWARD_AMOUNT)
        await query.edit_message_text(
            f"🆕 مكافأة المدعو الحالية: {current} IQD\n\n"
            f"أرسل القيمة الجديدة للمكافأة:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_rewards")]])
        )
        context.user_data['ADMIN_ACTION'] = 'invited_reward'
        return STATE_WAIT_INVITED_REWARD
    
    elif data == "reward_subscribe":
        if not db.is_admin(member_id): return
        current = db._settings.get('subscribe_reward', GuardianConfig.SUBSCRIBE_REWARD_AMOUNT)
        await query.edit_message_text(
            f"✅ مكافأة الاشتراك الحالية: {current} IQD\n\n"
            f"أرسل القيمة الجديدة للمكافأة:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_rewards")]])
        )
        context.user_data['ADMIN_ACTION'] = 'subscribe_reward'
        return STATE_WAIT_SUBSCRIBE_REWARD
    
    elif data == "reward_funding":
        if not db.is_admin(member_id): return
        current = db._settings.get('funding_price_per_member', GuardianConfig.FUNDING_PRICE_PER_MEMBER)
        await query.edit_message_text(
            f"👥 سعر تمويل العضو الحالي: {current} IQD\n\n"
            f"أرسل السعر الجديد:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_rewards")]])
        )
        context.user_data['ADMIN_ACTION'] = 'funding_price'
        return STATE_WAIT_FUNDING_PRICE
    
    elif data == "admin_promote":
        if member_id != GuardianConfig.MASTER_ADMIN_ID:
            await query.answer("❌ هذه الميزة متاحة فقط للمدير الرئيسي", show_alert=True)
            return
        await query.edit_message_text(
            "👑 رفع مشرف جديد\n\n"
            "أرسل ايدي العضو الذي تريد ترقيته إلى رتبة مشرف.\n"
            "المشرف يمكنه الوصول إلى لوحة التحكم وإدارة البوت.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'promote_admin'
        return STATE_WAIT_PROMOTE_ADMIN
    
    elif data == "admin_demote":
        if member_id != GuardianConfig.MASTER_ADMIN_ID:
            await query.answer("❌ هذه الميزة متاحة فقط للمدير الرئيسي", show_alert=True)
            return
        await query.edit_message_text(
            "⬇️ حذف مشرف\n\n"
            "أرسل ايدي المشرف الذي تريد إزالته من منصبه.\n"
            "لن يتم حذف العضو، فقط سيتم إلغاء صلاحياته الإدارية.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'demote_admin'
        return STATE_WAIT_DEMOTE_ADMIN
    
    elif data == "admin_maintenance":
        if not db.is_admin(member_id): return
        current = db._settings.get('maintenance_mode', False)
        db._settings['maintenance_mode'] = not current
        db._save_settings()
        state = "تفعيل" if not current else "تعطيل"
        await query.edit_message_text(
            f"✅ تم {state} وضع الصيانة بنجاح.\n\n"
            f"{'المستخدمون العاديون لن يتمكنوا من استخدام البوت حالياً.' if not current else 'عاد البوت للعمل بشكل طبيعي.'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")]])
        )
    
    elif data == "admin_broadcast":
        if not db.is_admin(member_id): return
        await query.edit_message_text(
            "📣 اذاعة للجميع\n\n"
            "أرسل الرسالة التي تريد إرسالها إلى جميع أعضاء البوت.\n"
            "ستصل الرسالة إلى جميع المستخدمين المسجلين.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
        )
        context.user_data['ADMIN_ACTION'] = 'broadcast'
        return STATE_WAIT_BROADCAST

async def handle_quick_protection(update: Update, context: ContextTypes.DEFAULT_TYPE, member_id: int, setting: str, setting_name: str):
    """
    معالج الحماية السريعة للقنوات
    
    يسمح بتفعيل أو تعطيل إعدادات الحماية بسرعة
    دون الحاجة للدخول إلى قائمة الإعدادات التفصيلية
    """
    query = update.callback_query
    
    channels = db.get_member_channels(member_id)
    if not channels:
        await query.edit_message_text(
            "❌ ليس لديك أي قنوات حماية مضافة.\n\n"
            "قم بإضافة قناة أولاً من خلال زر 'إضافة قناة'.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة قناة", callback_data="menu_add_channel")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")]
            ])
        )
        return
        
    if len(channels) == 1:
        channel_id = channels[0]
        db.toggle_channel_protection(channel_id, setting)
        ch_data = db._protected_channels.get(str(channel_id), {})
        title = ch_data.get('title', 'القناة')
        
        await query.edit_message_text(
            f"✅ تم {setting_name} في قناة {title} بنجاح.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 نظام الحماية", callback_data="menu_protection_system")]])
        )
    else:
        keyboard = []
        for ch_id in channels:
            ch_data = db._protected_channels.get(str(ch_id), {})
            title = ch_data.get('title', 'قناة')
            if len(title) > 30:
                title = title[:27] + "..."
            keyboard.append([InlineKeyboardButton(f"📢 {title}", callback_data=f"quick_{setting}_{ch_id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_protection_system")])
        
        await query.edit_message_text(
            f"اختر القناة التي تريد {setting_name} فيها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           معالج أمر البدء
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

@guardian_shield
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /start - نقطة الدخول الرئيسية للبوت
    
    يتعامل مع:
    - المستخدمين الجدد (الكابتشا)
    - روابط الإحالة
    - رموز الهدايا
    - القنوات الإجبارية
    - رسائل الترحيب
    """
    user = update.effective_user
    member_id = user.id
    message_text = update.message.text or ""
    
    logger.info(f"🚀 العضو {member_id} (@{user.username}) بدأ استخدام البوت")
    
    db.update_member_info(member_id, user)
    
    if db.is_member_blocked(member_id):
        await update.message.reply_text(
            "❌ تم حظر حسابك من استخدام البوت.\n\n"
            "إذا كنت تعتقد أن هذا الحظر تم عن طريق الخطأ، يرجى التواصل مع الدعم الفني:\n"
            f"@{GuardianConfig.MASTER_ADMIN_USERNAME}"
        )
        return ConversationHandler.END
    
    # التحقق من الكابتشا للمستخدمين الجدد
    if not db.is_captcha_verified(member_id):
        member = db.get_member(member_id)
        banned_until = member.get('captcha_banned_until')
        if banned_until:
            if isinstance(banned_until, str):
                banned_until = datetime.fromisoformat(banned_until)
            if datetime.now() < banned_until:
                remaining = int((banned_until - datetime.now()).total_seconds() / 60)
                await update.message.reply_text(
                    f"❌ تم تقييد حسابك لمدة {remaining} دقيقة أخرى بسبب المحاولات الخاطئة.\n"
                    f"يرجى الانتظار حتى انتهاء مدة التقييد ثم المحاولة مرة أخرى."
                )
                return ConversationHandler.END
            else:
                member['captcha_banned_until'] = None
                member['captcha_attempts'] = 0
                db._save_database()
        
        existing_captcha = db._captcha_data.get(member_id)
        if existing_captcha:
            code = existing_captcha.get('code', '')
        else:
            code = db.generate_captcha(member_id)
        
        await update.message.reply_text(
            f"🔐 مرحباً بك في بوت تفاعلكم الذكي لحماية القنوات!\n\n"
            f"للتحقق من أنك إنسان حقيقي ولست روبوت، يرجى إرسال الرقم الظاهر أدناه:\n\n"
            f"🔢 الرقم: `{code}`\n\n"
            f"⚠️ تنبيهات هامة:\n"
            f"• لديك {GuardianConfig.CAPTCHA_MAX_ATTEMPTS} محاولات فقط لإدخال الرقم الصحيح.\n"
            f"• بعد {GuardianConfig.CAPTCHA_MAX_ATTEMPTS} محاولات خاطئة، سيتم تقييد حسابك لمدة {GuardianConfig.CAPTCHA_BAN_MINUTES} دقيقة.\n"
            f"• الرقم يتكون من 6 خانات رقمية فقط.\n\n"
            f"أرسل الرقم الآن للمتابعة:",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['CAPTCHA_ACTION'] = 'wait_code'
        return STATE_WAIT_CAPTCHA_CODE
    
    # معالجة معاملات الرابط (إحالة أو هدية)
    args = context.args
    param = args[0] if args else None
    
    if not param and message_text:
        match = re.search(r'/start[=\s]+(\S+)', message_text)
        if match:
            param = match.group(1)
    
    if param:
        param = param.strip()
        try:
            int(param)
            is_gift = False
        except ValueError:
            is_gift = True
        
        if is_gift:
            success, msg = db.redeem_gift_code(param, member_id)
            if success:
                await update.message.reply_text(
                    f"🎁 {msg}\n\n💰 رصيدك الحالي: {db.get_member(member_id).get('balance', 0):,} IQD"
                )
            else:
                await update.message.reply_text(f"{msg}")
        else:
            inviter_id = int(param)
            if inviter_id != member_id:
                success, msg = db.process_referral(member_id, inviter_id)
                await update.message.reply_text(
                    f"{msg}\n\n"
                    f"⚠️ ملاحظة: ستحصل على مكافأة التسجيل بعد إكمال التحقق من الكابتشا "
                    f"والاشتراك في جميع القنوات الإجبارية."
                )
    
    # التحقق من وضع الصيانة
    if db._settings.get('maintenance_mode', False) and member_id != GuardianConfig.MASTER_ADMIN_ID:
        await update.message.reply_text(
            "🔧 البوت حالياً في وضع الصيانة.\n\n"
            "نقوم حالياً بتحديث النظام وإضافة مميزات جديدة.\n"
            "يرجى المحاولة في وقت لاحق. شكراً لتفهمك!"
        )
        return ConversationHandler.END
    
    # VIP معفي من الاشتراك الإجباري
    if db.is_exempt_from_mandatory(member_id):
        await show_main_menu(update, member_id)
        for wmsg in db.get_welcome_messages():
            try:
                if wmsg.get('type') == 'text':
                    await context.bot.send_message(
                        chat_id=member_id,
                        text=wmsg.get('content', '')
                    )
            except:
                pass
        return ConversationHandler.END
    
    # التحقق من القنوات الإجبارية
    is_joined, not_joined = await check_mandatory_channels(member_id, context)
    
    if not is_joined:
        keyboard = []
        for ch in not_joined:
            btn_text = f"📢 {ch['name'].replace('@', '')[:20]}"
            keyboard.append([InlineKeyboardButton(btn_text, url=ch['link'])])
        keyboard.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="verify_mandatory")])
        
        channels_text = "\n".join([f"• {ch['name']}" for ch in not_joined])
        
        await update.message.reply_text(
            f"⚠️ يجب الاشتراك في جميع القنوات التالية لاستخدام البوت:\n\n"
            f"{channels_text}\n\n"
            f"بعد الاشتراك في جميع القنوات، اضغط على زر 'تحقق من الاشتراك' للمتابعة.\n"
            f"⭐ مشتركي VIP معفيون من الاشتراك الإجباري.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    # إعطاء مكافأة الإحالة بعد التحقق والاشتراك
    db.give_referral_reward(member_id)
    
    # إرسال رسائل الترحيب
    for wmsg in db.get_welcome_messages():
        try:
            if wmsg.get('type') == 'text':
                await context.bot.send_message(
                    chat_id=member_id,
                    text=wmsg.get('content', '')
                )
        except:
            pass
    
    await show_main_menu(update, member_id)
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           معالج الرسائل النصية الموحد
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

@guardian_shield
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج موحد لجميع الرسائل النصية في البوت
    
    يقوم بتوجيه الرسالة إلى المعالج المناسب حسب الحالة الحالية
    للمستخدم. يدعم جميع عمليات الإدخال في البوت.
    """
    member_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""
    
    # استخراج نوع الإجراء الحالي من بيانات المستخدم المؤقتة
    prot_action = context.user_data.get('PROT_ACTION')
    fund_action = context.user_data.get('FUND_ACTION')
    report_action = context.user_data.get('REPORT_ACTION')
    order_action = context.user_data.get('ORDER_ACTION')
    admin_action = context.user_data.get('ADMIN_ACTION')
    captcha_action = context.user_data.get('CAPTCHA_ACTION')
    transfer_action = context.user_data.get('TRANSFER_ACTION')
    
    logger.info(f"📝 رسالة من {member_id} | admin={admin_action} | captcha={captcha_action} | transfer={transfer_action}")
    
    # ═══════════════ معالجة الكابتشا ═══════════════
    if captcha_action == 'wait_code':
        success, msg = db.verify_captcha(member_id, text)
        if success:
            await update.message.reply_text(
                "✅ تم التحقق من هويتك بنجاح! أهلاً بك في بوت تفاعلكم الذكي.\n\n"
                "جاري متابعة عملية التسجيل..."
            )
            context.user_data.pop('CAPTCHA_ACTION', None)
            
            if db.is_exempt_from_mandatory(member_id):
                await show_main_menu(update, member_id)
                for wmsg in db.get_welcome_messages():
                    try:
                        if wmsg.get('type') == 'text':
                            await context.bot.send_message(chat_id=member_id, text=wmsg.get('content', ''))
                    except: pass
                return ConversationHandler.END
            
            is_joined, not_joined = await check_mandatory_channels(member_id, context)
            if not is_joined:
                kb = [[InlineKeyboardButton(f"📢 {ch['name'].replace('@','')[:20]}", url=ch['link'])] for ch in not_joined]
                kb.append([InlineKeyboardButton("✅ تحقق", callback_data="verify_mandatory")])
                await update.message.reply_text("⚠️ يرجى الاشتراك في القنوات التالية:", reply_markup=InlineKeyboardMarkup(kb))
                return ConversationHandler.END
            
            db.give_referral_reward(member_id)
            for wmsg in db.get_welcome_messages():
                try:
                    if wmsg.get('type') == 'text':
                        await context.bot.send_message(chat_id=member_id, text=wmsg.get('content', ''))
                except: pass
            await show_main_menu(update, member_id)
            return ConversationHandler.END
        else:
            await update.message.reply_text(msg)
            if "تقييدك" in msg:
                context.user_data.clear()
                return ConversationHandler.END
            return STATE_WAIT_CAPTCHA_CODE
    
    # ═══════════════ معالجة التحويل ═══════════════
    if transfer_action == 'wait_target':
        try:
            target_id = int(text)
            if target_id == member_id:
                await update.message.reply_text("❌ لا يمكنك تحويل الرصيد إلى نفسك! هذه محاولة تحايل مرفوضة.")
                return STATE_WAIT_TRANSFER_TARGET
            if target_id not in db._members:
                await update.message.reply_text("❌ هذا المستخدم غير موجود في قاعدة البيانات. تأكد من الايدي.")
                return STATE_WAIT_TRANSFER_TARGET
            context.user_data['TRANSFER_TARGET'] = target_id
            target_member = db.get_member(target_id)
            await update.message.reply_text(
                f"👤 المستخدم المستقبل: {target_member.get('display_name', '')} (@{target_member.get('username', 'بدون')})\n\n"
                f"💰 أرسل المبلغ المراد تحويله:\n"
                f"الحد الأقصى للتحويل: {GuardianConfig.MAX_TRANSFER_AMOUNT:,} IQD\n\n"
                f"⚠️ تأكد من المبلغ قبل الإرسال. عملية التحويل لا يمكن التراجع عنها.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_main")]])
            )
            context.user_data['TRANSFER_ACTION'] = 'wait_amount'
            return STATE_WAIT_TRANSFER_AMOUNT
        except ValueError:
            await update.message.reply_text("❌ ايدي غير صالح. أرسل رقماً صحيحاً:")
            return STATE_WAIT_TRANSFER_TARGET
    
    elif transfer_action == 'wait_amount':
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ المبلغ يجب أن يكون أكبر من صفر.")
                return STATE_WAIT_TRANSFER_AMOUNT
            
            target_id = context.user_data.get('TRANSFER_TARGET')
            success, msg = db.transfer_balance(member_id, target_id, amount)
            
            await update.message.reply_text(
                msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]])
            )
            
            if success:
                try:
                    sender = update.effective_user
                    receiver = db.get_member(target_id)
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=f"💰 تم استلام مبلغ {amount:,} IQD من @{sender.username or sender.first_name}\n\n"
                             f"💳 رصيدك الحالي: {receiver.get('balance', 0):,} IQD"
                    )
                except: pass
                
                sender = update.effective_user
                receiver = db.get_member(target_id)
                await notify_master(
                    context,
                    f"💸 عملية تحويل جديدة!\n\n"
                    f"👤 المرسل: {sender.first_name} (@{sender.username})\n"
                    f"🆔 ايدي المرسل: `{member_id}`\n"
                    f"👤 المستقبل: {receiver.get('display_name', '')} (@{receiver.get('username', '')})\n"
                    f"🆔 ايدي المستقبل: `{target_id}`\n"
                    f"💰 المبلغ: {amount:,} IQD"
                )
            
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً:")
            return STATE_WAIT_TRANSFER_AMOUNT
    
    # ═══════════════ طلبات الخدمات ═══════════════
    if order_action == 'wait_quantity':
        try:
            quantity = int(text)
            min_qty = context.user_data.get('ORDER_MIN', 1)
            max_qty = context.user_data.get('ORDER_MAX', 999999)
            
            if quantity < min_qty or quantity > max_qty:
                await update.message.reply_text(f"❌ الكمية يجب أن تكون بين {min_qty} و {max_qty}")
                return STATE_WAIT_SERVICE_QUANTITY
            
            srv_id = context.user_data.get('ORDER_SRV_ID', '')
            price_per_1000 = context.user_data.get('ORDER_SRV_PRICE', 0)
            total_cost = int((quantity / 1000) * price_per_1000)
            
            member_balance = db.get_member(member_id).get('balance', 0)
            
            if member_balance < total_cost:
                await update.message.reply_text(
                    f"❌ رصيدك غير كافي لإتمام هذا الطلب.\n"
                    f"💰 رصيدك الحالي: {member_balance:,} IQD\n"
                    f"💵 تكلفة الطلب: {total_cost:,} IQD\n\n"
                    f"يمكنك شحن رصيدك من خلال التواصل مع الدعم.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_services")]])
                )
                context.user_data.clear()
                return ConversationHandler.END
            
            context.user_data['ORDER_QTY'] = quantity
            context.user_data['ORDER_COST'] = total_cost
            
            await update.message.reply_text(
                f"📌 الكمية المطلوبة: {quantity}\n"
                f"💰 التكلفة الإجمالية: {total_cost:,} IQD\n\n"
                f"🔗 أرسل الرابط المطلوب للخدمة:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_services")]])
            )
            context.user_data['ORDER_ACTION'] = 'wait_link'
            return STATE_WAIT_SERVICE_LINK
        except ValueError:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً:")
            return STATE_WAIT_SERVICE_QUANTITY
    
    elif order_action == 'wait_link':
        context.user_data['ORDER_LINK'] = text
        await confirm_service_order(update, context, member_id)
        return ConversationHandler.END
    
    # ═══════════════ إضافة قناة حماية ═══════════════
    if prot_action == 'add_channel':
        channel_input = text.strip()
        channel_id = None
        
        if 't.me/' in channel_input:
            parts = channel_input.split('t.me/')
            if len(parts) > 1:
                username = parts[1].split('/')[0].split('?')[0]
                channel_id = f"@{username}"
        elif channel_input.startswith('@'):
            channel_id = channel_input
        else:
            channel_id = f"@{channel_input}"
            
        try:
            chat = await context.bot.get_chat(channel_id)
            bot_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            
            if bot_member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ البوت ليس مشرفاً (أدمن) في هذه القناة.\n\n"
                    "يجب رفع البوت كمشرف في القناة مع الصلاحيات التالية:\n"
                    "• حذف الرسائل\n"
                    "• حظر المستخدمين\n"
                    "• إضافة مشرفين جدد\n\n"
                    "بعد رفع البوت بالمطلوب، حاول مرة أخرى.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 نظام الحماية", callback_data="menu_protection_system")]])
                )
                context.user_data.clear()
                return ConversationHandler.END
                
            member_channels = db.get_member_channels(member_id)
            if str(chat.id) in member_channels:
                await update.message.reply_text(
                    "❌ هذه القناة مضافة بالفعل إلى قائمة الحماية الخاصة بك.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 نظام الحماية", callback_data="menu_protection_system")]])
                )
                context.user_data.clear()
                return ConversationHandler.END
                
            db.add_protected_channel(member_id, str(chat.id), chat.title)
            
            await update.message.reply_text(
                f"✅ تم إضافة القناة إلى نظام الحماية بنجاح!\n\n"
                f"📢 اسم القناة: {chat.title}\n"
                f"🆔 معرف القناة: {chat.id}\n\n"
                f"يمكنك الآن تفعيل ميزات الحماية من خلال قائمة 'نظام الحماية'.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛡 نظام الحماية", callback_data="menu_protection_system")],
                    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]
                ])
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text("❌ القناة غير موجودة أو الرابط غير صحيح. حاول مرة أخرى:")
            return STATE_WAIT_CHANNEL_LINK
    
    # ═══════════════ طلب تمويل ═══════════════
    elif fund_action == 'funding_channel':
        channel_input = text.strip()
        channel_id = None
        channel_link = channel_input
        channel_username = ""
        
        if 't.me/' in channel_input:
            parts = channel_input.split('t.me/')
            if len(parts) > 1:
                username = parts[1].split('/')[0].split('?')[0]
                channel_id = f"@{username}"
                channel_username = username
        elif channel_input.startswith('@'):
            channel_id = channel_input
            channel_username = channel_input.replace('@', '')
        else:
            channel_id = f"@{channel_input}"
            channel_username = channel_input
            
        if not channel_link.startswith('http'):
            channel_link = f"https://t.me/{channel_username}"
            
        if db.has_active_campaign_for_channel(member_id, channel_username):
            await update.message.reply_text(
                "❌ لديك حملة تمويل نشطة بالفعل لهذه القناة.\n\n"
                "يرجى الانتظار حتى اكتمال الحملة الحالية قبل إنشاء حملة جديدة.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_funding")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
            
        try:
            chat = await context.bot.get_chat(channel_id)
            bot_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            
            if bot_member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ البوت ليس مشرفاً في القناة. يرجى رفع البوت كمشرف أولاً.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_funding")]])
                )
                context.user_data.clear()
                return ConversationHandler.END
                
            context.user_data['FUND_CH_ID'] = str(chat.id)
            context.user_data['FUND_CH_TITLE'] = chat.title
            context.user_data['FUND_CH_LINK'] = channel_link
            context.user_data['FUND_CH_USERNAME'] = channel_username
            
            price = db._settings.get('funding_price_per_member', GuardianConfig.FUNDING_PRICE_PER_MEMBER)
            
            await update.message.reply_text(
                f"📢 القناة: {chat.title}\n"
                f"💰 سعر العضو الواحد: {price} IQD\n\n"
                f"أرسل عدد الأعضاء المطلوب تمويل القناة بهم:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_funding")]])
            )
            
            context.user_data['FUND_ACTION'] = 'funding_members'
            return STATE_WAIT_FUNDING_COUNT
            
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ. حاول مرة أخرى:")
            return STATE_WAIT_FUNDING_CHANNEL
    
    elif fund_action == 'funding_members':
        try:
            members_count = int(text)
            if members_count <= 0:
                await update.message.reply_text("❌ العدد يجب أن يكون أكبر من صفر.")
                return STATE_WAIT_FUNDING_COUNT
                
            price = db._settings.get('funding_price_per_member', GuardianConfig.FUNDING_PRICE_PER_MEMBER)
            total_cost = members_count * price
            
            member = db.get_member(member_id)
            
            if member.get('balance', 0) < total_cost:
                await update.message.reply_text(
                    f"❌ رصيدك غير كافي.\n💰 رصيدك: {member.get('balance', 0):,} IQD\n💵 التكلفة: {total_cost:,} IQD",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_funding")]])
                )
                context.user_data.clear()
                return ConversationHandler.END
                
            member['balance'] -= total_cost
            
            success, result = db.create_pending_campaign(
                member_id, context.user_data['FUND_CH_ID'], context.user_data['FUND_CH_TITLE'],
                context.user_data['FUND_CH_LINK'], context.user_data['FUND_CH_USERNAME'], members_count
            )
            
            if not success:
                member['balance'] += total_cost
                await update.message.reply_text(
                    f"{result}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_funding")]])
                )
                context.user_data.clear()
                return ConversationHandler.END
            
            campaign = result
            is_vip = db.is_vip_member(member_id)
            
            if is_vip:
                await update.message.reply_text(
                    f"✅ تم إنشاء حملة التمويل وتفعيلها مباشرة!\n\n"
                    f"📢 القناة: {context.user_data['FUND_CH_TITLE']}\n"
                    f"👥 عدد الأعضاء: {members_count}\n"
                    f"💰 التكلفة: {total_cost:,} IQD\n\n"
                    f"✨ مميزة VIP: تم تفعيل الحملة مباشرة بدون انتظار موافقة الإدارة.\n"
                    f"🎯 تم إضافة قناتك إلى قسم تبادل الاشتراك والربح.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]])
                )
                await notify_master(
                    context,
                    f"📢 حملة تمويل VIP مباشرة!\n"
                    f"👤 {member_id}\n📺 {context.user_data['FUND_CH_TITLE']}\n"
                    f"🔗 {context.user_data['FUND_CH_LINK']}\n"
                    f"👥 {members_count}\n💰 {total_cost:,} IQD\n⭐ VIP - مفعلة تلقائياً"
                )
            else:
                await update.message.reply_text(
                    f"✅ تم إنشاء طلب التمويل بنجاح!\n\n"
                    f"📢 القناة: {context.user_data['FUND_CH_TITLE']}\n"
                    f"👥 عدد الأعضاء: {members_count}\n"
                    f"💰 التكلفة: {total_cost:,} IQD\n\n"
                    f"⏳ طلبك قيد المراجعة من قبل الإدارة. سيتم إشعارك عند الموافقة.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]])
                )
                await notify_master(
                    context,
                    f"📢 طلب تمويل جديد!\n👤 {member_id}\n📺 {context.user_data['FUND_CH_TITLE']}\n👥 {members_count}\n💰 {total_cost:,} IQD"
                )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً:")
            return STATE_WAIT_FUNDING_COUNT
    
    # ═══════════════ الإبلاغ ═══════════════
    elif report_action == 'report_campaign':
        campaign_id = context.user_data.get('REPORT_ID')
        page = context.user_data.get('REPORT_PAGE', 0)
        
        db.report_campaign(campaign_id, member_id, text)
        
        await update.message.reply_text(
            "✅ تم إرسال البلاغ إلى الإدارة بنجاح. شكراً لمساهمتك في تحسين البوت.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=f"exchange_page_{page}")]])
        )
        
        await notify_master(context, f"🚨 بلاغ عن حملة!\n👤 {member_id}\n📝 {text}")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    # ═══════════════ لوحة المدير ═══════════════
    if not db.is_admin(member_id):
        return ConversationHandler.END
    
    # --- إضافة قسم ---
    if admin_action == 'add_category_name':
        context.user_data['CAT_NAME'] = text
        await update.message.reply_text(
            f"📁 اسم القسم: {text}\n\nأرسل وصف القسم:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_category_desc'
        return STATE_WAIT_SERVICE_CATEGORY_DESC
    
    elif admin_action == 'add_category_desc':
        cat_name = context.user_data.get('CAT_NAME', '')
        cat_id = db.create_service_category(cat_name, text)
        await update.message.reply_text(
            f"✅ تم إضافة القسم: {cat_name}\n📝 الوصف: {text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الخدمات", callback_data="admin_services")]])
        )
        await notify_master(context, f"📁 تم إضافة قسم خدمات جديد: {cat_name}")
        context.user_data.clear()
        return ConversationHandler.END
    
    # --- إضافة خدمة (6 خطوات) ---
    elif admin_action == 'add_service_name':
        context.user_data['SRV_NAME'] = text
        await update.message.reply_text(
            f"📌 اسم الخدمة: {text}\n\n"
            f"الخطوة 2 من 6:\n"
            f"أرسل وصف الخدمة بالتفصيل:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_service_desc'
        return STATE_WAIT_SERVICE_DESC
    
    elif admin_action == 'add_service_desc':
        context.user_data['SRV_DESC'] = text
        await update.message.reply_text(
            f"📝 الوصف: {text}\n\n"
            f"الخطوة 3 من 6:\n"
            f"أرسل السعر لكل 1000:\n"
            f"(أرسل رقماً فقط، مثال: 5000)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_service_price'
        return STATE_WAIT_SERVICE_PRICE
    
    elif admin_action == 'add_service_price':
        try:
            price = int(text)
            if price <= 0:
                await update.message.reply_text("❌ السعر يجب أن يكون أكبر من 0، أرسل رقماً صحيحاً:")
                return STATE_WAIT_SERVICE_PRICE
            context.user_data['SRV_PRICE'] = price
            await update.message.reply_text(
                f"💰 السعر لكل 1000: {price:,} IQD\n\n"
                f"الخطوة 4 من 6:\n"
                f"كم هي المدة المتوقعة لتسليم الخدمة؟\n"
                f"(مثال: 24 ساعة، 3 أيام، أسبوع)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
            )
            context.user_data['ADMIN_ACTION'] = 'add_service_duration'
            return STATE_WAIT_SERVICE_DURATION
        except ValueError:
            await update.message.reply_text("❌ رقم غير صالح، أرسل رقماً صحيحاً:")
            return STATE_WAIT_SERVICE_PRICE
    
    elif admin_action == 'add_service_duration':
        context.user_data['SRV_DURATION'] = text
        await update.message.reply_text(
            f"⏰ المدة المتوقعة: {text}\n\n"
            f"الخطوة 5 من 6:\n"
            f"ما هو الحد الأدنى للطلب؟\n"
            f"(أرسل رقماً)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_service_min'
        return STATE_WAIT_SERVICE_MIN
    
    elif admin_action == 'add_service_min':
        try:
            min_val = int(text)
            if min_val <= 0:
                await update.message.reply_text("❌ الحد الأدنى يجب أن يكون أكبر من 0:")
                return STATE_WAIT_SERVICE_MIN
            context.user_data['SRV_MIN'] = min_val
            await update.message.reply_text(
                f"📊 الحد الأدنى: {min_val}\n\n"
                f"الخطوة 6 من 6:\n"
                f"ما هو الحد الأقصى للطلب؟\n"
                f"(أرسل رقماً)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_services")]])
            )
            context.user_data['ADMIN_ACTION'] = 'add_service_max'
            return STATE_WAIT_SERVICE_MAX
        except ValueError:
            await update.message.reply_text("❌ رقم غير صالح، أرسل رقماً:")
            return STATE_WAIT_SERVICE_MIN
    
    elif admin_action == 'add_service_max':
        try:
            max_val = int(text)
            if max_val <= 0:
                await update.message.reply_text("❌ الحد الأقصى يجب أن يكون أكبر من 0:")
                return STATE_WAIT_SERVICE_MAX
            if max_val < context.user_data.get('SRV_MIN', 0):
                await update.message.reply_text("❌ الحد الأقصى يجب أن يكون أكبر من أو يساوي الحد الأدنى:")
                return STATE_WAIT_SERVICE_MAX
            
            srv_id = db.add_service_to_category(
                context.user_data.get('SRV_CAT_ID', ''),
                context.user_data.get('SRV_NAME', ''),
                context.user_data.get('SRV_DESC', ''),
                context.user_data.get('SRV_PRICE', 0),
                context.user_data.get('SRV_DURATION', ''),
                context.user_data.get('SRV_MIN', 0),
                max_val
            )
            
            cat_name = db._service_categories.get(context.user_data.get('SRV_CAT_ID', ''), {}).get('name', '')
            
            await update.message.reply_text(
                f"✅ تم إضافة الخدمة بنجاح إلى قسم {cat_name}!\n\n"
                f"📌 اسم الخدمة: {context.user_data.get('SRV_NAME', '')}\n"
                f"📝 الوصف: {context.user_data.get('SRV_DESC', '')}\n"
                f"💰 السعر لكل 1000: {context.user_data.get('SRV_PRICE', 0):,} IQD\n"
                f"⏰ المدة المتوقعة: {context.user_data.get('SRV_DURATION', '')}\n"
                f"📊 الحد الأدنى: {context.user_data.get('SRV_MIN', 0)}\n"
                f"📊 الحد الأقصى: {max_val}\n"
                f"🔗 الرابط: إجباري\n\n"
                f"🎯 الخدمة متاحة الآن للمستخدمين في قسم {cat_name}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الخدمات", callback_data="admin_services")]])
            )
            
            await notify_master(
                context,
                f"➕ خدمة جديدة: {context.user_data.get('SRV_NAME', '')}\n"
                f"💰 {context.user_data.get('SRV_PRICE', 0):,} IQD/1000"
            )
            
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ رقم غير صالح، أرسل رقماً:")
            return STATE_WAIT_SERVICE_MAX
    
    # --- تغيير اسم القسم ---
    elif admin_action == 'rename_category':
        cat_id = context.user_data.get('RENAME_CAT_ID', '')
        db.rename_category(cat_id, text)
        await update.message.reply_text(
            f"✅ تم تغيير اسم القسم إلى: {text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الخدمات", callback_data="admin_services")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # --- تغيير اسم الخدمة ---
    elif admin_action == 'rename_service':
        srv_id = context.user_data.get('RENAME_SRV_ID', '')
        db.rename_service(srv_id, text)
        await update.message.reply_text(
            f"✅ تم تغيير اسم الخدمة إلى: {text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الخدمات", callback_data="admin_services")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # --- رسائل الترحيب ---
    elif admin_action == 'add_welcome_msg':
        msg_id = db.add_welcome_message('text', text)
        await update.message.reply_text(
            f"✅ تم إضافة رسالة الترحيب رقم {msg_id}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الرسائل", callback_data="admin_welcome_msgs")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # --- إلغاء VIP ---
    elif admin_action == 'cancel_vip':
        try:
            target_id = int(text)
            if db.cancel_vip(target_id):
                await update.message.reply_text(
                    f"✅ تم إلغاء اشتراك VIP للعضو {target_id}.\nتم حذف جميع مميزات VIP منه فوراً.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
                )
            else:
                await update.message.reply_text("❌ هذا العضو ليس مشتركاً في VIP.")
        except ValueError:
            await update.message.reply_text("❌ ايدي غير صالح")
            return STATE_WAIT_CANCEL_VIP_USER
        context.user_data.clear()
        return ConversationHandler.END
    
    # --- استيراد البيانات ---
    elif admin_action == 'import':
        if update.message.document:
            try:
                if not update.message.document.file_name.endswith('.json'):
                    await update.message.reply_text(
                        "❌ يجب أن يكون الملف بصيغة JSON!\n\n"
                        "الرجاء إرسال ملف بيانات بصيغة .json فقط.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                
                file = await update.message.document.get_file()
                os.makedirs(GuardianConfig.TEMP_FOLDER, exist_ok=True)
                file_path = f"{GuardianConfig.TEMP_FOLDER}/import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                await file.download_to_drive(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                if db.import_all_data(imported_data):
                    stats = db.get_system_stats()
                    await update.message.reply_text(
                        f"✅ تم استيراد البيانات بنجاح!\n\n"
                        f"📊 إحصائيات البيانات المستوردة:\n"
                        f"👥 عدد الأعضاء: {stats['total_members']}\n"
                        f"📢 قنوات الحماية: {stats['total_protected_channels']}\n"
                        f"📊 إجمالي الحملات: {stats['total_campaigns']}\n"
                        f"⭐ مشتركي VIP النشطين: {stats['active_vip']}\n"
                        f"🚫 الأعضاء المحظورين: {stats['blocked_members']}\n"
                        f"📁 أقسام الخدمات: {stats['total_categories']}\n"
                        f"📌 الخدمات: {stats['total_services']}\n"
                        f"📝 الطلبات المعلقة: {stats['pending_orders']}\n"
                        f"💰 إجمالي الأرصدة: {stats['total_balance']:,} IQD\n\n"
                        f"🔔 تم استبدال جميع بيانات البوت بالبيانات المستوردة بنجاح!",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
                    )
                else:
                    await update.message.reply_text(
                        "❌ فشل استيراد البيانات!\n\nتأكد من أن الملف سليم وغير تالف.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
                    )
                
                try:
                    os.remove(file_path)
                except:
                    pass
                    
            except json.JSONDecodeError:
                await update.message.reply_text(
                    "❌ الملف غير صالح!\n\nالملف ليس بصيغة JSON صحيحة أو أنه تالف.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
                )
            except Exception as e:
                logger.error(f"❌ خطأ في الاستيراد: {e}")
                await update.message.reply_text(
                    f"❌ حدث خطأ أثناء استيراد البيانات!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
                )
        else:
            await update.message.reply_text(
                "❌ يرجى إرسال ملف JSON!\n\nالرجاء إرسال ملف البيانات بصيغة .json فقط.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
            )
            return STATE_WAIT_BACKUP_FILE
        
        context.user_data.clear()
        return ConversationHandler.END
    
    # --- بحث عن عضو ---
    elif admin_action == 'search_member':
        try:
            target_id = int(text)
            member = db.search_member(target_id)
            
            if not member:
                await update.message.reply_text("❌ العضو غير موجود في قاعدة البيانات.")
                context.user_data.clear()
                return ConversationHandler.END
            
            mid = member.get('member_id', 'غير معروف')
            username = member.get('username', 'بدون يوزر')
            display_name = member.get('display_name', '')
            balance = member.get('balance', 0)
            joined = member.get('joined_date', '')
            if isinstance(joined, datetime):
                joined = joined.strftime('%Y-%m-%d %H:%M')
            is_blocked = "🚫 محظور" if member.get('is_blocked', False) else "✅ نشط"
            is_vip = "⭐ VIP" if db.is_vip_member(mid) else "👤 عادي"
            transfer_blocked = "❌ مقيد" if member.get('transfer_blocked', False) else "✅ مسموح"
            
            text = f"""
🔍 معلومات العضو

🆔 الايدي: `{mid}`
👤 الاسم: {display_name}
📱 اليوزر: @{username}
💰 الرصيد: {balance:,} IQD
📅 تاريخ التسجيل: {joined}
🚫 الحالة: {is_blocked}
⭐ الاشتراك: {is_vip}
💸 حالة التحويل: {transfer_blocked}
"""
            
            keyboard = [
                [InlineKeyboardButton("📋 عرض حركات المستخدم", callback_data=f"show_activity_{mid}")],
                [InlineKeyboardButton("👥 عرض المدعوين", callback_data=f"show_referrals_{mid}")],
                [
                    InlineKeyboardButton(
                        "🚫 تقييد تحويل" if not member.get('transfer_blocked') else "✅ فك تقييد تحويل",
                        callback_data=f"toggle_transfer_{mid}"
                    )
                ],
                [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]
            ]
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ ايدي غير صالح:")
            return STATE_WAIT_SEARCH_USER
    
    # --- باقي إجراءات المدير ---
    elif admin_action == 'edit_button_name':
        db.set_button_name(context.user_data.get('EDIT_BTN_KEY', ''), text)
        await update.message.reply_text(
            f"✅ تم تغيير اسم الزر إلى: {text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 أسماء الأزرار", callback_data="admin_button_names")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'charge_user_id':
        try:
            target_id = int(text)
            db.get_member(target_id)
            context.user_data['CHARGE_TARGET'] = target_id
            await update.message.reply_text("💰 أرسل المبلغ (IQD):")
            context.user_data['ADMIN_ACTION'] = 'charge_amount'
            return STATE_WAIT_CHARGE_AMOUNT
        except ValueError:
            await update.message.reply_text("❌ ايدي غير صالح:")
            return STATE_WAIT_CHARGE_USER
    
    elif admin_action == 'charge_amount':
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ المبلغ > 0")
                return STATE_WAIT_CHARGE_AMOUNT
            target_id = context.user_data['CHARGE_TARGET']
            total = db.add_balance_with_bonus(target_id, amount)
            bonus_text = ""
            if db.is_vip_member(target_id):
                bonus_text = f" (تشمل هدية VIP {GuardianConfig.VIP_BONUS_PERCENT}%)"
            await update.message.reply_text(
                f"✅ تم شحن {total:,} IQD للعضو {target_id}{bonus_text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ مبلغ غير صالح:")
            return STATE_WAIT_CHARGE_AMOUNT
    
    elif admin_action == 'deduct_user_id':
        try:
            target_id = int(text)
            db.get_member(target_id)
            context.user_data['DEDUCT_TARGET'] = target_id
            await update.message.reply_text(f"💸 أرسل المبلغ للخصم من {target_id}:")
            context.user_data['ADMIN_ACTION'] = 'deduct_amount'
            return STATE_WAIT_DEDUCT_AMOUNT
        except ValueError:
            await update.message.reply_text("❌ ايدي غير صالح:")
            return STATE_WAIT_DEDUCT_USER
    
    elif admin_action == 'deduct_amount':
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ المبلغ > 0")
                return STATE_WAIT_DEDUCT_AMOUNT
            target_id = context.user_data['DEDUCT_TARGET']
            nb = db.force_deduct_balance(target_id, amount)
            await update.message.reply_text(
                f"✅ تم خصم {amount:,} IQD من العضو {target_id}\n💰 الرصيد الجديد: {nb:,} IQD",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ رقم غير صالح")
            return STATE_WAIT_DEDUCT_AMOUNT
    
    elif admin_action == 'charge_all_amount':
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ المبلغ > 0")
                return STATE_WAIT_CHARGE_ALL_AMOUNT
            context.user_data['CHARGE_ALL_AMT'] = amount
            await update.message.reply_text(f"📤 سيتم شحن {amount:,} IQD للجميع\nأرسل رسالة للمستخدمين:")
            context.user_data['ADMIN_ACTION'] = 'charge_all_message'
            return STATE_WAIT_CHARGE_ALL_MESSAGE
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_CHARGE_ALL_AMOUNT
    
    elif admin_action == 'charge_all_message':
        amount = context.user_data.get('CHARGE_ALL_AMT', 0)
        await update.message.reply_text("📤 جاري الشحن...")
        count = 0
        for mid in db.get_active_members():
            try:
                db.add_balance_with_bonus(mid, amount)
                await context.bot.send_message(chat_id=mid, text=f"{text}\n\n💰 تم شحن {amount:,} IQD إلى رصيدك")
                count += 1
            except: pass
        await update.message.reply_text(
            f"✅ تم شحن {amount:,} IQD لـ {count} عضو",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'deduct_all_amount':
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ المبلغ > 0")
                return STATE_WAIT_DEDUCT_ALL_AMOUNT
            context.user_data['DEDUCT_ALL_AMT'] = amount
            await update.message.reply_text(f"📥 سيتم خصم {amount:,} IQD من الجميع\nأرسل رسالة للمستخدمين:")
            context.user_data['ADMIN_ACTION'] = 'deduct_all_message'
            return STATE_WAIT_DEDUCT_ALL_MESSAGE
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_DEDUCT_ALL_AMOUNT
    
    elif admin_action == 'deduct_all_message':
        amount = context.user_data.get('DEDUCT_ALL_AMT', 0)
        await update.message.reply_text("📥 جاري الخصم...")
        count = 0
        for mid in db.get_active_members():
            try:
                nb = db.force_deduct_balance(mid, amount)
                await context.bot.send_message(chat_id=mid, text=f"{text}\n\n💸 تم خصم {amount:,} IQD\n💰 رصيدك: {nb:,} IQD")
                count += 1
            except: pass
        await update.message.reply_text(
            f"✅ تم خصم {amount:,} IQD من {count} عضو",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'block_user':
        try:
            target_id = int(text)
            if db.get_member(target_id).get('is_blocked'):
                await update.message.reply_text("❌ العضو محظور بالفعل")
                context.user_data.clear()
                return ConversationHandler.END
            context.user_data['BLOCK_TARGET'] = target_id
            await update.message.reply_text("📝 أرسل سبب الحظر:")
            context.user_data['ADMIN_ACTION'] = 'block_reason'
            return STATE_WAIT_BAN_REASON
        except ValueError:
            await update.message.reply_text("❌ ايدي")
            return STATE_WAIT_BAN_USER
    
    elif admin_action == 'block_reason':
        db.block_member(context.user_data.get('BLOCK_TARGET'), text)
        await update.message.reply_text(
            "✅ تم حظر العضو",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الحظر", callback_data="admin_blocks")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'unblock_user':
        try:
            target_id = int(text)
            if not db.get_member(target_id).get('is_blocked'):
                await update.message.reply_text("❌ العضو ليس محظوراً")
                context.user_data.clear()
                return ConversationHandler.END
            db.unblock_member(target_id)
            await update.message.reply_text(
                "✅ تم فك الحظر",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إدارة الحظر", callback_data="admin_blocks")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ ايدي")
            return STATE_WAIT_UNBAN_USER
    
    elif admin_action == 'add_mandatory_channel':
        context.user_data['MAND_CHANNEL'] = text
        await update.message.reply_text(
            f"📢 {text}\nأرسل الحد الأقصى للأعضاء (0 = بدون حد):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_mandatory")]])
        )
        context.user_data['ADMIN_ACTION'] = 'add_mandatory_count'
        return STATE_WAIT_FORCE_COUNT
    
    elif admin_action == 'add_mandatory_count':
        try:
            mx = max(0, int(text))
            db.add_mandatory_channel(context.user_data.get('MAND_CHANNEL', ''), mx)
            await update.message.reply_text(
                "✅ تمت الإضافة",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_FORCE_COUNT
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'reject_campaign':
        success, msg, campaign = db.reject_campaign(context.user_data.get('REJECT_CAMP_ID'), member_id, text)
        if success and campaign:
            try:
                await context.bot.send_message(
                    chat_id=campaign['owner_id'],
                    text=f"❌ تم رفض حملة التمويل الخاصة بك.\n📝 السبب: {text}\n💰 تم إعادة {campaign['total_cost']:,} IQD إلى رصيدك"
                )
            except: pass
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_pending")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'vip_price':
        try:
            p = int(text)
            if p <= 0:
                await update.message.reply_text("❌ > 0")
                return STATE_WAIT_VIP_PRICE
            db._settings['vip_price'] = p
            db._save_settings()
            await update.message.reply_text(
                f"✅ تم تغيير سعر VIP إلى {p:,} IQD",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_VIP_PRICE
    
    elif admin_action == 'trial_days':
        try:
            d = int(text)
            if d <= 0:
                await update.message.reply_text("❌ > 0")
                return STATE_WAIT_TRIAL_DAYS
            db._settings['free_trial_days'] = d
            db._save_settings()
            await update.message.reply_text(
                f"✅ تم تغيير الفترة التجريبية إلى {d} يوم",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_TRIAL_DAYS
    
    elif admin_action in ['inviter_reward', 'invited_reward', 'subscribe_reward', 'funding_price']:
        try:
            v = int(text)
            if v < 0:
                await update.message.reply_text("❌ >= 0")
                return {'inviter_reward': STATE_WAIT_INVITER_REWARD, 'invited_reward': STATE_WAIT_INVITED_REWARD,
                        'subscribe_reward': STATE_WAIT_SUBSCRIBE_REWARD, 'funding_price': STATE_WAIT_FUNDING_PRICE}[admin_action]
            k = {'inviter_reward': 'inviter_reward', 'invited_reward': 'invited_reward',
                 'subscribe_reward': 'subscribe_reward', 'funding_price': 'funding_price_per_member'}[admin_action]
            db._settings[k] = v
            db._save_settings()
            await update.message.reply_text(
                f"✅ تم التغيير إلى {v:,}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 المكافآت", callback_data="admin_rewards")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return {'inviter_reward': STATE_WAIT_INVITER_REWARD, 'invited_reward': STATE_WAIT_INVITED_REWARD,
                    'subscribe_reward': STATE_WAIT_SUBSCRIBE_REWARD, 'funding_price': STATE_WAIT_FUNDING_PRICE}[admin_action]
    
    elif admin_action == 'gift_uses':
        try:
            u = int(text)
            if u <= 0:
                await update.message.reply_text("❌ > 0")
                return STATE_WAIT_GIFT_USES
            context.user_data['GIFT_USES'] = u
            await update.message.reply_text(f"👥 {u}\n💰 المبلغ لكل عضو:")
            context.user_data['ADMIN_ACTION'] = 'gift_amount'
            return STATE_WAIT_GIFT_AMOUNT
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_GIFT_USES
    
    elif admin_action == 'gift_amount':
        try:
            a = int(text)
            if a <= 0:
                await update.message.reply_text("❌ > 0")
                return STATE_WAIT_GIFT_AMOUNT
            code = db.create_gift_code(member_id, context.user_data.get('GIFT_USES', 0), a)
            link = f"https://t.me/{GuardianConfig.BOT_USERNAME}?start={code}"
            await update.message.reply_text(
                f"🎁 تم إنشاء رابط الهدية!\n👥 {context.user_data.get('GIFT_USES',0)} استخدام\n💰 {a} IQD\n🔗 `{link}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 مشاركة", switch_inline_query=link)], [InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]]),
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ رقم")
            return STATE_WAIT_GIFT_AMOUNT
    
    elif admin_action == 'broadcast':
        await update.message.reply_text("📣 جاري الإرسال...")
        s, f = 0, 0
        for mid in list(db._members.keys()):
            try:
                await context.bot.send_message(chat_id=int(mid), text=text)
                s += 1
            except:
                f += 1
        await update.message.reply_text(
            f"✅ ناجح: {s}\n❌ فشل: {f}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'send_message_user':
        try:
            tid = int(text)
            if tid not in db._members:
                await update.message.reply_text("❌ غير موجود")
                context.user_data.clear()
                return ConversationHandler.END
            context.user_data['SEND_TARGET'] = tid
            await update.message.reply_text(
                f"📨 أرسل نص الرسالة للعضو {tid}:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="menu_admin")]])
            )
            context.user_data['ADMIN_ACTION'] = 'send_message_text'
            return STATE_WAIT_SEND_MESSAGE_TEXT
        except ValueError:
            await update.message.reply_text("❌ ايدي")
            return STATE_WAIT_SEND_MESSAGE_USER
    
    elif admin_action == 'send_message_text':
        try:
            await context.bot.send_message(
                chat_id=context.user_data.get('SEND_TARGET'),
                text=f"📨 رسالة من الإدارة:\n\n{text}"
            )
            await update.message.reply_text("✅ تم الإرسال")
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")
        context.user_data.clear()
        return ConversationHandler.END
    
    elif admin_action == 'delete_member':
        try:
            tid = int(text)
            if tid == GuardianConfig.MASTER_ADMIN_ID:
                await update.message.reply_text("❌ لا يمكن حذف المدير!")
                context.user_data.clear()
                return ConversationHandler.END
            if tid not in db._members:
                await update.message.reply_text("❌ غير موجود")
                context.user_data.clear()
                return ConversationHandler.END
            db.delete_member(tid)
            await update.message.reply_text(
                f"✅ تم حذف العضو {tid}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ ايدي")
            return STATE_WAIT_DELETE_USER
    
    elif admin_action == 'promote_admin':
        try:
            tid = int(text)
            if tid not in db._members:
                await update.message.reply_text("❌ غير موجود")
                context.user_data.clear()
                return ConversationHandler.END
            db.promote_admin(tid)
            await update.message.reply_text(
                f"✅ تم ترقية {tid} إلى مشرف",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ ايدي")
            return STATE_WAIT_PROMOTE_ADMIN
    
    elif admin_action == 'demote_admin':
        try:
            tid = int(text)
            if tid == GuardianConfig.MASTER_ADMIN_ID:
                await update.message.reply_text("❌ لا يمكن!")
                context.user_data.clear()
                return ConversationHandler.END
            db.demote_admin(tid)
            await update.message.reply_text(
                f"✅ تم إزالة {tid} من المشرفين",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة التحكم", callback_data="menu_admin")]])
            )
            context.user_data.clear()
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ ايدي")
            return STATE_WAIT_DEMOTE_ADMIN

async def confirm_service_order(update: Update, context: ContextTypes.DEFAULT_TYPE, member_id: int):
    """
    تأكيد طلب الخدمة وإنشائه في النظام
    
    تقوم بخصم الرصيد من المستخدم وإنشاء طلب جديد
    وإرسال إشعار للمدير بوجود طلب جديد
    """
    srv_id = context.user_data.get('ORDER_SRV_ID', '')
    quantity = context.user_data.get('ORDER_QTY', 0)
    link = context.user_data.get('ORDER_LINK', '')
    total_cost = context.user_data.get('ORDER_COST', 0)
    srv_name = context.user_data.get('ORDER_SRV_NAME', '')
    
    member = db.get_member(member_id)
    member['balance'] = member.get('balance', 0) - total_cost
    
    order_id = db.create_service_order(member_id, srv_id, quantity, link)
    
    discount = db.get_vip_discount(member_id)
    discount_text = f"\n🎁 خصم VIP: {discount}%" if discount > 0 else ""
    
    text = f"""
✅ تم تقديم طلبك بنجاح!

📌 الخدمة: {srv_name}
📊 الكمية: {quantity}
💰 التكلفة: {total_cost:,} IQD{discount_text}
🔗 الرابط: {link}
🆔 رقم الطلب: `{order_id}`

⏳ طلبك قيد المراجعة من قبل الإدارة.
سيتم إشعارك عند الموافقة أو الرفض.
"""
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_main")]]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    user = update.effective_user
    await notify_master(
        context,
        f"📝 طلب خدمة جديد!\n\n"
        f"👤 المستخدم: {user.first_name} (@{user.username})\n"
        f"🆔 ايدي: `{member_id}`\n"
        f"📌 الخدمة: {srv_name}\n"
        f"📊 الكمية: {quantity}\n"
        f"💰 التكلفة: {total_cost:,} IQD\n"
        f"🔗 الرابط: {link}\n"
        f"🆔 رقم الطلب: `{order_id}`"
    )
    
    context.user_data.clear()

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           معالج تحديثات القناة
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

async def handle_channel_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج تحديثات القناة
    
    يتعامل مع:
    - نظام الحماية (حظر المنضمين، المغادرين، بدون يوزر)
    - كشف حذف البوت من القناة
    - تحديث إحصائيات القنوات المحمية
    """
    chat = update.effective_chat
    if not chat:
        return
        
    chat_id = str(chat.id)
    
    # كشف حذف البوت من القناة
    if update.my_chat_member:
        new_status = update.my_chat_member.new_chat_member.status
        old_status = update.my_chat_member.old_chat_member.status
        
        if old_status in ['administrator', 'creator'] and new_status in ['member', 'left', 'kicked', 'restricted']:
            logger.info(f"🚨 تم حذف البوت من: {chat.title} ({chat_id})")
            
            channel_username = chat.username or ""
            if channel_username:
                owners = db.cancel_all_campaigns_for_channel(
                    channel_username,
                    "تم حذف البوت من القناة - إلغاء بدون تعويض"
                )
                db.remove_mandatory_channel(channel_username)
                for owner_id in owners:
                    try:
                        await context.bot.send_message(
                            chat_id=owner_id,
                            text=f"🚫 تم إلغاء حملة التمويل لقناتك ({chat.title})\n\n"
                                 f"❌ السبب: تم حذف البوت من القناة\n"
                                 f"⚠️ لا يوجد تعويض مالي."
                        )
                    except:
                        pass
            
            await notify_master(
                context,
                f"🚨 تم حذف البوت من قناة!\n\n"
                f"📢 {chat.title}\n🆔 {chat_id}\n👤 @{channel_username}\n\n"
                f"تم إلغاء جميع حملات التمويل المرتبطة."
            )
            
            if chat_id in db._protected_channels:
                del db._protected_channels[chat_id]
                db._save_database()
    
    # نظام الحماية
    if chat_id not in db._protected_channels:
        return
        
    ch_data = db._protected_channels[chat_id]
    settings = ch_data.get('protection_settings', {})
    owner_id = ch_data.get('owner_id')
    
    if not settings or not owner_id:
        return
        
    can_use, _ = db.can_use_bot(owner_id)
    if not can_use:
        return
    
    if update.chat_member and update.chat_member.new_chat_member:
        new_member = update.chat_member.new_chat_member
        user = new_member.user
        user_id = user.id
        
        if user_id == context.bot.id or new_member.status in ['administrator', 'creator']:
            return
            
        ch_data['stats']['total_joined'] = ch_data['stats'].get('total_joined', 0) + 1
        db._save_database()
        
        if settings.get('block_no_username') and not user.username:
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                ch_data['stats']['total_blocked'] = ch_data['stats'].get('total_blocked', 0) + 1
                db._save_database()
            except:
                pass
            return
            
        if settings.get('block_new_members'):
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                ch_data['stats']['total_blocked'] = ch_data['stats'].get('total_blocked', 0) + 1
                db._save_database()
            except:
                pass
            return
    
    if update.chat_member and update.chat_member.old_chat_member and update.chat_member.new_chat_member:
        old_status = update.chat_member.old_chat_member.status
        new_status = update.chat_member.new_chat_member.status
        
        if old_status == 'member' and new_status == 'left':
            user = update.chat_member.old_chat_member.user
            
            ch_data['stats']['total_left'] = ch_data['stats'].get('total_left', 0) + 1
            db._save_database()
            
            if settings.get('block_leaving_members'):
                try:
                    await context.bot.ban_chat_member(chat_id, user.id)
                    ch_data['stats']['total_blocked'] = ch_data['stats'].get('total_blocked', 0) + 1
                    db._save_database()
                except:
                    pass

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           معالج الأزرار الخاصة
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

async def handle_special_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج خاص للأزرار الإضافية التي تحتاج معالجة منفصلة
    
    يتعامل مع:
    - عرض حركات المستخدم
    - عرض المدعوين
    - تقييد/فك تقييد التحويل
    - إنشاء باركود الإحالة
    - الحماية السريعة للقنوات المتعددة
    """
    query = update.callback_query
    data = query.data
    
    if data.startswith("show_activity_"):
        member_id = int(data.replace("show_activity_", ""))
        if not db.is_admin(update.effective_user.id):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        
        activities = db.get_member_activity(member_id)
        if not activities:
            await query.answer("❌ لا توجد حركات مسجلة لهذا المستخدم", show_alert=True)
            return
        
        text = f"📋 سجل حركات المستخدم {member_id}:\n\n"
        for log in activities[-100:]:
            timestamp = log.get('timestamp', '')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
            action = log.get('action', '')
            text += f"📅 {timestamp}\n📝 {action}\n{'─' * 30}\n"
        
        file = BytesIO(text.encode('utf-8'))
        file.name = f"activity_{member_id}.txt"
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=file,
            caption=f"📋 سجل حركات المستخدم {member_id}"
        )
        await query.answer("✅ تم إرسال الملف", show_alert=True)
    
    elif data.startswith("show_referrals_"):
        member_id = int(data.replace("show_referrals_", ""))
        if not db.is_admin(update.effective_user.id):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        
        referrals = db.get_member_referrals_detail(member_id)
        if not referrals:
            await query.answer("❌ لا يوجد مدعوين بواسطة هذا المستخدم", show_alert=True)
            return
        
        text = f"👥 المدعوين بواسطة المستخدم {member_id}:\n\n"
        for r in referrals:
            joined = r.get('joined_date', '')
            text += f"🆔 `{r['member_id']}`\n👤 {r['display_name']}\n📱 @{r['username']}\n💰 {r['balance']:,} IQD\n📅 {joined}\n{'─' * 30}\n"
        
        file = BytesIO(text.encode('utf-8'))
        file.name = f"referrals_{member_id}.txt"
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=file,
            caption=f"👥 المدعوين بواسطة المستخدم {member_id}"
        )
        await query.answer("✅ تم إرسال الملف", show_alert=True)
    
    elif data.startswith("toggle_transfer_"):
        member_id = int(data.replace("toggle_transfer_", ""))
        blocked = db.toggle_transfer_block(member_id)
        await query.answer(f"{'🚫 تم تقييد التحويل' if blocked else '✅ تم فك تقييد التحويل'}")
    
    elif data.startswith("qr_"):
        member_id = int(data.replace("qr_", ""))
        link = db.get_referral_link(member_id)
        try:
            qr_path = generate_qr_code(link, member_id)
            with open(qr_path, 'rb') as f:
                await context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=f,
                    caption=f"📱 باركود الإحالة الخاص بك\n🔗 {link}"
                )
            await query.answer("✅ تم إنشاء الباركود", show_alert=True)
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الباركود: {e}")
            await query.answer("❌ فشل إنشاء الباركود", show_alert=True)
    
    elif data.startswith("quick_"):
        parts = data.split("_")
        if len(parts) >= 3:
            setting = f"{parts[1]}_{parts[2]}"
            channel_id = parts[3] if len(parts) > 3 else ""
            if channel_id:
                member_id = update.effective_user.id
                db.toggle_channel_protection(channel_id, setting)
                ch_data = db._protected_channels.get(str(channel_id), {})
                title = ch_data.get('title', 'القناة')
                setting_names = {
                    'block_new_members': 'حظر المنضمين',
                    'block_leaving_members': 'حظر المغادرين',
                    'block_no_username': 'حظر بدون يوزر'
                }
                setting_name = setting_names.get(setting, setting)
                
                await query.edit_message_text(
                    f"✅ تم {setting_name} في قناة {title}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 نظام الحماية", callback_data="menu_protection_system")]])
                )

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           المهام المجدولة
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

async def scheduled_vip_check(context: ContextTypes.DEFAULT_TYPE):
    """
    المهمة المجدولة لفحص انتهاء VIP والتجديد التلقائي
    
    تعمل كل ساعة وتقوم بـ:
    - فحص اشتراكات VIP المنتهية وإلغائها
    - محاولة التجديد التلقائي للمشتركين قبل يوم من الانتهاء
    - إرسال إشعارات للمستخدمين
    """
    expired = db.check_expired_vip()
    for mid in expired:
        try:
            await context.bot.send_message(
                chat_id=mid,
                text="⚠️ انتهى اشتراك VIP الخاص بك.\n\n"
                     "تم إلغاء جميع مميزات VIP:\n"
                     "• خصم 15% على الخدمات\n"
                     "• تمويل مباشر بدون موافقة\n"
                     "• إعفاء من الاشتراك الإجباري\n"
                     "• هدية 10% على الشحن\n\n"
                     "يمكنك تجديد اشتراكك من قائمة VIP في البوت."
            )
        except:
            pass
    
    for mid in list(db._vip_members.keys()):
        exp = db._vip_members[mid]
        if isinstance(exp, str):
            exp = datetime.fromisoformat(exp)
        days_left = (exp - datetime.now()).days
        
        if days_left <= GuardianConfig.VIP_AUTO_RENEW_DAYS_BEFORE:
            renewed = db.auto_renew_vip(mid)
            if renewed:
                try:
                    await context.bot.send_message(
                        chat_id=mid,
                        text="🔄 تم تجديد اشتراك VIP تلقائياً!\n\n"
                             "تم خصم قيمة الاشتراك من رصيدك وتجديد VIP لمدة 30 يوم."
                    )
                except:
                    pass
            elif days_left <= 0:
                try:
                    await context.bot.send_message(
                        chat_id=mid,
                        text="⚠️ لم يتم تجديد اشتراك VIP لعدم كفاية الرصيد.\n\n"
                             "يمكنك شحن رصيدك ثم تجديد الاشتراك يدوياً من قائمة VIP."
                    )
                except:
                    pass

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    إلغاء المحادثة الحالية وتنظيف البيانات المؤقتة
    
    تستخدم عند ضغط المستخدم على زر إلغاء أو عند انتهاء المحادثة
    """
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.edit_message_text("❌ تم إلغاء العملية بنجاح")
    else:
        await update.message.reply_text("❌ تم إلغاء العملية بنجاح")
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           الدالة الرئيسية
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def main():
    """
    الدالة الرئيسية لتشغيل البوت
    
    تقوم بإنشاء جميع المجلدات الضرورية، تهيئة المعالجات،
    وبدء تشغيل البوت في وضع الاستماع المستمر.
    """
    
    # إنشاء المجلدات الضرورية لعمل البوت
    os.makedirs(GuardianConfig.BACKUP_FOLDER, exist_ok=True)
    os.makedirs(GuardianConfig.TEMP_FOLDER, exist_ok=True)
    os.makedirs(GuardianConfig.LOG_FOLDER, exist_ok=True)
    os.makedirs(GuardianConfig.QR_FOLDER, exist_ok=True)
    
    # إنشاء التطبيق الرئيسي
    app = Application.builder().token(GuardianConfig.BOT_TOKEN).concurrent_updates(True).build()
    
    # إنشاء محادثة موحدة لجميع الإدخالات النصية
    main_conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(handle_callbacks, pattern="^menu_add_channel$"),
            CallbackQueryHandler(handle_callbacks, pattern="^fund_create$"),
            CallbackQueryHandler(handle_callbacks, pattern="^order_service_"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_charge$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_deduct$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_charge_all$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_deduct_all$"),
            CallbackQueryHandler(handle_callbacks, pattern="^block_add$"),
            CallbackQueryHandler(handle_callbacks, pattern="^block_remove$"),
            CallbackQueryHandler(handle_callbacks, pattern="^mandatory_add$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_vip_price$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_trial_days$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_broadcast$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_import$"),
            CallbackQueryHandler(handle_callbacks, pattern="^reward_inviter$"),
            CallbackQueryHandler(handle_callbacks, pattern="^reward_invited$"),
            CallbackQueryHandler(handle_callbacks, pattern="^reward_subscribe$"),
            CallbackQueryHandler(handle_callbacks, pattern="^reward_funding$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_gift$"),
            CallbackQueryHandler(handle_callbacks, pattern="^reject_"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_search$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_send_message$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_delete_member$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_promote$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_demote$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_add_category$"),
            CallbackQueryHandler(handle_callbacks, pattern="^add_srv_to_"),
            CallbackQueryHandler(handle_callbacks, pattern="^edit_btn_"),
            CallbackQueryHandler(handle_callbacks, pattern="^rncat_"),
            CallbackQueryHandler(handle_callbacks, pattern="^rnsrv_"),
            CallbackQueryHandler(handle_callbacks, pattern="^add_wmsg_text$"),
            CallbackQueryHandler(handle_callbacks, pattern="^admin_cancel_vip$"),
            CallbackQueryHandler(handle_callbacks, pattern="^menu_transfer$"),
        ],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            8: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            9: [MessageHandler(filters.Document.ALL | filters.TEXT, handle_all_messages)],
            10: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            11: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            12: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            13: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            14: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            15: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            16: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            17: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            18: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            19: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            20: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            21: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            22: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            23: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            24: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            25: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            26: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            27: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            28: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            29: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            30: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            31: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            33: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            34: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            35: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            36: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            37: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            38: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            39: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            40: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            41: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            42: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            43: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            44: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            45: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            46: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            47: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            48: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            49: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            50: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            51: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
            52: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^menu_main$"),
            CommandHandler("cancel", cancel_conversation)
        ],
        allow_reentry=True,
        per_message=False
    )
    app.add_handler(main_conv)
    
    # إضافة معالج الأزرار التفاعلية الرئيسي
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # إضافة معالج الأزرار الخاصة
    app.add_handler(CallbackQueryHandler(
        handle_special_buttons,
        pattern="^show_activity_|^show_referrals_|^toggle_transfer_|^qr_|^quick_"
    ))
    
    # إضافة معالج تحديثات القناة
    app.add_handler(ChatMemberHandler(
        handle_channel_updates,
        ChatMemberHandler.CHAT_MEMBER | ChatMemberHandler.MY_CHAT_MEMBER
    ))
    
    # إضافة المهمة المجدولة لفحص VIP كل ساعة
    if app.job_queue:
        app.job_queue.run_repeating(scheduled_vip_check, interval=3600, first=10)
    
    # طباعة معلومات البدء
    print("\n" + "=" * 80)
    print("🤖 بوت الحارس الذكي - الإصدار 20.0.0")
    print("=" * 80)
    print(f"📅 تاريخ التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 المدير: @{GuardianConfig.MASTER_ADMIN_USERNAME}")
    print(f"🤖 معرف البوت: @{GuardianConfig.BOT_USERNAME}")
    print("=" * 80)
    print("✅ نظام كابتشا للتحقق من المستخدمين الجدد")
    print("✅ تحويل رصيد بين المستخدمين")
    print("✅ تغيير أسماء الأقسام والخدمات")
    print("✅ رسائل ترحيب مخصصة للمستخدمين الجدد")
    print("✅ نظام VIP متقدم:")
    print("   - خصم 15% على الخدمات")
    print("   - تمويل مباشر بدون موافقة")
    print("   - إعفاء من الاشتراك الإجباري")
    print("   - هدية 10% على الشحن")
    print("   - تجديد تلقائي")
    print("✅ بحث متقدم مع المدعوين وتقييد التحويل")
    print("✅ إلغاء VIP من لوحة التحكم")
    print("✅ حماية من الحسابات الوهمية")
    print("✅ متوافق مع استيراد وتصدير البيانات")
    print("✅ جميع الأزرار تعمل بشكل كامل")
    print("=" * 80)
    print("🚀 جاري تشغيل البوت...")
    print("=" * 80 + "\n")
    
    # بدء تشغيل البوت
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#                                           نقطة البداية
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    نقطة بداية تشغيل البوت
    
    تقوم بتشغيل الدالة الرئيسية مع إمكانية إعادة التشغيل
    التلقائي في حالة حدوث خطأ غير متوقع.
    """
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⚠️ تم إيقاف البوت يدوياً بواسطة المستخدم")
    except Exception as e:
        logger.critical(f"💥 خطأ حرج في تشغيل البوت: {e}\n{traceback.format_exc()}")
