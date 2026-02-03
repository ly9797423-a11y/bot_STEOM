#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لوحة تحكم بوت "يلا نتعلم"
للمدير فقط: 6130994941
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from telegram.constants import ParseMode

# ============= إعدادات البوت =============
TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
ADMIN_ID = 6130994941

# ============= تسجيل =============
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
        self.users = DataManager.load_data("users_data.json", {})
    
    def get_user(self, user_id: int) -> Dict:
        """الحصول على بيانات المستخدم"""
        return self.users.get(str(user_id), {})
    
    def update_balance(self, user_id: int, amount: int, description: str = "") -> bool:
        """تحديد رصيد المستخدم"""
        try:
            user_id_str = str(user_id)
            if user_id_str not in self.users:
                return False
            
            user = self.users[user_id_str]
            user["balance"] = user.get("balance", 0) + amount
            
            # تسجيل المعاملة
            transaction = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "description": description,
                "balance_after": user["balance"]
            }
            user.setdefault("transactions", []).append(transaction)
            
            DataManager.save_data("users_data.json", self.users)
            logger.info(f"Admin charged user {user_id}: +{amount}")
            return True
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False

# ============= لوحة التحكم =============
class AdminPanel:
    def __init__(self):
        self.user_manager = UserManager()
        self.load_settings()
        logger.info("AdminPanel initialized")
    
    def load_settings(self):
        """تحميل الإعدادات"""
        self.settings = DataManager.load_data("admin_settings.json", {
            "maintenance": False,
            "prices": {
                "exemption": 1000,
                "summarize": 1000,
                "qa": 1000,
                "materials": 1000
            },
            "welcome_bonus": 1000,
            "referral_bonus": 500,
            "channel_link": "https://t.me/joinchat/AAAA",
            "support_link": "https://t.me/Allawi04"
        })
    
    def save_settings(self):
        """حفظ الإعدادات"""
        DataManager.save_data("admin_settings.json", self.settings)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر لوحة التحكم"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ <b>غير مصرح لك بالدخول!</b>", parse_mode=ParseMode.HTML)
            return
        
        await self.show_admin_panel(update.message)
    
    async def show_admin_panel(self, message):
        """عرض لوحة التحكم الرئيسية"""
        total_users = len(self.user_manager.users)
        total_balance = sum(user.get("balance", 0) for user in self.user_manager.users.values())
        
        panel_text = f"""
👑 <b>لوحة التحكم الإدارية</b>

📊 <b>إحصائيات البوت:</b>
- عدد المستخدمين: {total_users}
- إجمالي الرصيد: {total_balance:,} دينار
- حالة البوت: {"🟢 نشط" if not self.settings['maintenance'] else "🔴 صيانة"}

⚙️ <b>اختر الإجراء:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("💰 شحن الرصيد", callback_data="admin_charge")],
            [InlineKeyboardButton("⚙️ تغيير الأسعار", callback_data="admin_prices")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("🛠️ إعدادات البوت", callback_data="admin_settings")],
            [InlineKeyboardButton("📚 إدارة المواد", callback_data="admin_materials")],
            [InlineKeyboardButton("🔙 خروج", callback_data="admin_exit")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(panel_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ردود لوحة التحكم"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ <b>غير مصرح لك!</b>", parse_mode=ParseMode.HTML)
            return
        
        if query.data == "admin_users":
            await self.show_users_management(query)
        elif query.data == "admin_charge":
            await self.show_charge_menu(query)
        elif query.data == "admin_prices":
            await self.show_prices_menu(query)
        elif query.data == "admin_stats":
            await self.show_stats_menu(query)
        elif query.data == "admin_settings":
            await self.show_settings_menu(query)
        elif query.data == "admin_materials":
            await self.show_materials_menu(query)
        elif query.data == "admin_exit":
            await query.edit_message_text("✅ <b>تم الخروج من لوحة التحكم</b>", parse_mode=ParseMode.HTML)
            return
        elif query.data.startswith("user_"):
            await self.handle_user_action(query, query.data)
        elif query.data.startswith("charge_"):
            await self.handle_charge_action(query, query.data, context)
        elif query.data.startswith("price_"):
            await self.handle_price_action(query, query.data, context)
        elif query.data.startswith("setting_"):
            await self.handle_setting_action(query, query.data, context)
        elif query.data.startswith("material_"):
            await self.handle_material_action(query, query.data, context)
        elif query.data == "back_to_admin":
            await self.show_admin_panel(query)
    
    async def show_users_management(self, query):
        """عرض إدارة المستخدمين"""
        users_count = len(self.user_manager.users)
        
        keyboard = [
            [InlineKeyboardButton("🔍 عرض مستخدم", callback_data="user_view")],
            [InlineKeyboardButton("📋 قائمة المستخدمين", callback_data="user_list_0")],
            [InlineKeyboardButton("⛔ حظر مستخدم", callback_data="user_ban")],
            [InlineKeyboardButton("✅ إلغاء حظر", callback_data="user_unban")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]
        ]
        
        await query.edit_message_text(
            f"👥 <b>إدارة المستخدمين</b>\n\n"
            f"📊 عدد المستخدمين: {users_count}\n\n"
            f"اختر الإجراء:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_charge_menu(self, query):
        """عرض قائمة الشحن"""
        keyboard = [
            [InlineKeyboardButton("💰 شحن مستخدم", callback_data="charge_user")],
            [InlineKeyboardButton("💸 خصم من مستخدم", callback_data="charge_deduct")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]
        ]
        
        await query.edit_message_text(
            "💰 <b>إدارة الشحن والرصيد</b>\n\n"
            "اختر نوع المعاملة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_prices_menu(self, query):
        """عرض قائمة الأسعار"""
        prices_text = "<b>💰 الأسعار الحالية:</b>\n\n"
        
        service_names = {
            "exemption": "حساب درجة الإعفاء",
            "summarize": "تلخيص الملازم",
            "qa": "سؤال وجواب",
            "materials": "ملازمي ومرشحاتي"
        }
        
        for service, price in self.settings["prices"].items():
            prices_text += f"{service_names.get(service, service)}: {price:,} دينار\n"
        
        keyboard = []
        for service in self.settings["prices"]:
            service_name = service_names.get(service, service)
            keyboard.append([InlineKeyboardButton(
                f"✏️ تعديل {service_name}", callback_data=f"price_{service}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")])
        
        await query.edit_message_text(
            prices_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_stats_menu(self, query):
        """عرض الإحصائيات"""
        users = self.user_manager.users
        
        total_users = len(users)
        active_users = sum(1 for user in users.values() if user.get("balance", 0) > 0)
        total_balance = sum(user.get("balance", 0) for user in users.values())
        
        # حساب الخدمات المستخدمة
        services_count = {
            "exemption": 0,
            "summarize": 0,
            "qa": 0,
            "materials": 0
        }
        
        for user in users.values():
            for service in user.get("used_services", []):
                service_type = service.get("service", "")
                if service_type in services_count:
                    services_count[service_type] += 1
        
        stats_text = f"""
📊 <b>إحصائيات مفصلة</b>

👥 <b>المستخدمين:</b>
- الإجمالي: {total_users:,}
- النشطين: {active_users:,}
- النسبة: {(active_users/total_users*100) if total_users > 0 else 0:.1f}%

💰 <b>الماليات:</b>
- إجمالي الرصيد: {total_balance:,} دينار
- متوسط الرصيد: {(total_balance/total_users) if total_users > 0 else 0:,.0f} دينار

📈 <b>الخدمات المستخدمة:</b>
- حساب الإعفاء: {services_count['exemption']:,}
- تلخيص الملازم: {services_count['summarize']:,}
- سؤال وجواب: {services_count['qa']:,}
- المواد: {services_count['materials']:,}
- الإجمالي: {sum(services_count.values()):,}

🕐 <b>آخر تحديث:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]
        ]
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_settings_menu(self, query):
        """عرض إعدادات البوت"""
        maintenance_status = "🔴 مفعل" if self.settings['maintenance'] else "🟢 معطل"
        
        settings_text = f"""
⚙️ <b>إعدادات البوت</b>

🔧 <b>وضع الصيانة:</b> {maintenance_status}
🎁 <b>الهدية الترحيبية:</b> {self.settings['welcome_bonus']:,} دينار
👥 <b>مكافأة الدعوة:</b> {self.settings['referral_bonus']:,} دينار

🔗 <b>الروابط:</b>
- القناة: {self.settings['channel_link'][:30]}...
- الدعم: {self.settings['support_link']}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔧 وضع الصيانة", callback_data="setting_maintenance")],
            [InlineKeyboardButton("🎁 الهدية الترحيبية", callback_data="setting_welcome_bonus")],
            [InlineKeyboardButton("👥 مكافأة الدعوة", callback_data="setting_referral_bonus")],
            [InlineKeyboardButton("📢 رابط القناة", callback_data="setting_channel")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]
        ]
        
        await query.edit_message_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_materials_menu(self, query):
        """عرض إدارة المواد"""
        materials = DataManager.load_data("materials_data.json", [])
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مادة", callback_data="material_add")],
            [InlineKeyboardButton("📋 عرض المواد", callback_data="material_list")],
            [InlineKeyboardButton("🗑️ حذف مادة", callback_data="material_delete")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")]
        ]
        
        await query.edit_message_text(
            f"📚 <b>إدارة المواد التعليمية</b>\n\n"
            f"📊 عدد المواد: {len(materials)}\n\n"
            f"اختر الإجراء:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_user_action(self, query, action):
        """معالجة إجراءات المستخدمين"""
        if action == "user_view":
            await query.edit_message_text(
                "🔍 <b>عرض مستخدم</b>\n\n"
                "أرسل ID المستخدم:\n"
                "<code>123456789</code>",
                parse_mode=ParseMode.HTML
            )
            # سيتم معالجة هذا في handle_message
        elif action.startswith("user_list_"):
            try:
                page = int(action.split("_")[2])
                await self.show_users_list(query, page)
            except:
                await self.show_users_list(query, 0)
    
    async def handle_charge_action(self, query, action, context):
        """معالجة إجراءات الشحن"""
        if action == "charge_user":
            await query.edit_message_text(
                "💰 <b>شحن مستخدم</b>\n\n"
                "أرسل ID المستخدم:\n"
                "<code>123456789</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['action'] = 'charge_user'
        elif action == "charge_deduct":
            await query.edit_message_text(
                "💸 <b>خصم من مستخدم</b>\n\n"
                "أرسل ID المستخدم:\n"
                "<code>123456789</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['action'] = 'charge_deduct'
    
    async def handle_price_action(self, query, action, context):
        """معالجة تغيير الأسعار"""
        service = action.replace("price_", "")
        
        service_names = {
            "exemption": "حساب درجة الإعفاء",
            "summarize": "تلخيص الملازم",
            "qa": "سؤال وجواب",
            "materials": "ملازمي ومرشحاتي"
        }
        
        service_name = service_names.get(service, service)
        current_price = self.settings["prices"].get(service, 1000)
        
        await query.edit_message_text(
            f"💰 <b>تغيير سعر {service_name}</b>\n\n"
            f"السعر الحالي: {current_price:,} دينار\n\n"
            f"أرسل السعر الجديد:\n"
            f"<code>1500</code>",
            parse_mode=ParseMode.HTML
        )
        context.user_data['action'] = f'price_{service}'
    
    async def handle_setting_action(self, query, action, context):
        """معالجة تغيير الإعدادات"""
        setting = action.replace("setting_", "")
        
        if setting == "maintenance":
            self.settings['maintenance'] = not self.settings['maintenance']
            self.save_settings()
            status = "تم تفعيل" if self.settings['maintenance'] else "تم إلغاء"
            await query.answer(f"✅ {status} وضع الصيانة")
            await self.show_settings_menu(query)
        
        elif setting == "welcome_bonus":
            await query.edit_message_text(
                f"🎁 <b>تغيير الهدية الترحيبية</b>\n\n"
                f"القيمة الحالية: {self.settings['welcome_bonus']:,} دينار\n\n"
                f"أرسل القيمة الجديدة:\n"
                f"<code>2000</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['action'] = 'welcome_bonus'
        
        elif setting == "referral_bonus":
            await query.edit_message_text(
                f"👥 <b>تغيير مكافأة الدعوة</b>\n\n"
                f"القيمة الحالية: {self.settings['referral_bonus']:,} دينار\n\n"
                f"أرسل القيمة الجديدة:\n"
                f"<code>1000</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['action'] = 'referral_bonus'
        
        elif setting == "channel":
            await query.edit_message_text(
                f"📢 <b>تغيير رابط القناة</b>\n\n"
                f"الرابط الحالي: {self.settings['channel_link']}\n\n"
                f"أرسل الرابط الجديد:\n"
                f"<code>https://t.me/joinchat/BBBB</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['action'] = 'channel_link'
    
    async def handle_material_action(self, query, action, context):
        """معالجة إجراءات المواد"""
        if action == "material_add":
            await query.edit_message_text(
                "➕ <b>إضافة مادة جديدة</b>\n\n"
                "أرسل تفاصيل المادة بالشكل التالي:\n\n"
                "<code>اسم المادة | الوصف | المرحلة | رابط التحميل</code>\n\n"
                "مثال:\n"
                "<code>رياضيات السادس | ملزمة شاملة | السادس الإعدادي | https://example.com/file.pdf</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['action'] = 'material_add'
    
    async def show_users_list(self, query, page=0):
        """عرض قائمة المستخدمين"""
        users = list(self.user_manager.users.items())
        users_per_page = 10
        start_idx = page * users_per_page
        end_idx = start_idx + users_per_page
        
        message = f"📋 <b>المستخدمين (الصفحة {page + 1})</b>\n\n"
        
        for user_id, user_data in users[start_idx:end_idx]:
            balance = user_data.get("balance", 0)
            join_date = user_data.get("joined_date", "غير معروف")
            message += f"🆔 {user_id} | 💰 {balance:,} | 📅 {join_date.split()[0]}\n"
        
        # أزرار التنقل
        keyboard = []
        if page > 0:
            keyboard.append(InlineKeyboardButton("◀️ السابق", callback_data=f"user_list_{page-1}"))
        if end_idx < len(users):
            keyboard.append(InlineKeyboardButton("▶️ التالي", callback_data=f"user_list_{page+1}"))
        
        if keyboard:
            keyboard = [keyboard]
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة رسائل المدير"""
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            return
        
        text = update.message.text.strip()
        action = context.user_data.get('action', '')
        
        if not action:
            await update.message.reply_text("⚙️ <b>استخدم لوحة التحكم للبدء</b>\n\nاكتب /admin", parse_mode=ParseMode.HTML)
            return
        
        try:
            if action == 'charge_user':
                # شحن مستخدم
                if text.isdigit():
                    target_id = int(text)
                    context.user_data['charge_target'] = target_id
                    context.user_data['action'] = 'charge_amount'
                    
                    await update.message.reply_text(
                        f"✅ <b>تم تحديد المستخدم:</b> {target_id}\n\n"
                        f"💰 <b>أرسل المبلغ للشحن:</b>\n"
                        f"<code>5000</code>",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await update.message.reply_text("❌ <b>أدخل ID صحيح</b>", parse_mode=ParseMode.HTML)
            
            elif action == 'charge_deduct':
                # خصم من مستخدم
                if text.isdigit():
                    target_id = int(text)
                    context.user_data['charge_target'] = target_id
                    context.user_data['action'] = 'deduct_amount'
                    
                    await update.message.reply_text(
                        f"✅ <b>تم تحديد المستخدم:</b> {target_id}\n\n"
                        f"💸 <b>أرسل المبلغ للخصم:</b>\n"
                        f"<code>1000</code>",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await update.message.reply_text("❌ <b>أدخل ID صحيح</b>", parse_mode=ParseMode.HTML)
            
            elif action == 'charge_amount':
                # كمية الشحن
                if text.isdigit():
                    amount = int(text)
                    target_id = context.user_data.get('charge_target')
                    
                    if target_id and self.user_manager.update_balance(target_id, amount, "شحن من المدير"):
                        user_data = self.user_manager.get_user(target_id)
                        new_balance = user_data.get("balance", 0)
                        
                        await update.message.reply_text(
                            f"✅ <b>تم الشحن بنجاح!</b>\n\n"
                            f"👤 <b>المستخدم:</b> {target_id}\n"
                            f"💰 <b>المبلغ:</b> {amount:,} دينار\n"
                            f"💳 <b>الرصيد الجديد:</b> {new_balance:,} دينار",
                            parse_mode=ParseMode.HTML
                        )
                        
                        # إرسال إشعار للمستخدم
                        try:
                            await context.bot.send_message(
                                chat_id=target_id,
                                text=f"🎉 <b>تم شحن رصيدك!</b>\n\n"
                                     f"💰 <b>المبلغ:</b> {amount:,} دينار\n"
                                     f"💳 <b>رصيدك الحالي:</b> {new_balance:,} دينار",
                                parse_mode=ParseMode.HTML
                            )
                        except:
                            pass
                    else:
                        await update.message.reply_text("❌ <b>فشل في الشحن. تحقق من ID المستخدم</b>", parse_mode=ParseMode.HTML)
                    
                    # تنظيف
                    context.user_data.pop('action', None)
                    context.user_data.pop('charge_target', None)
                    await self.show_admin_panel(update.message)
                else:
                    await update.message.reply_text("❌ <b>أدخل مبلغاً صحيحاً</b>", parse_mode=ParseMode.HTML)
            
            elif action == 'deduct_amount':
                # كمية الخصم
                if text.isdigit():
                    amount = -int(text)  # سالب للخصم
                    target_id = context.user_data.get('charge_target')
                    
                    if target_id and self.user_manager.update_balance(target_id, amount, "خصم من المدير"):
                        user_data = self.user_manager.get_user(target_id)
                        new_balance = user_data.get("balance", 0)
                        
                        await update.message.reply_text(
                            f"✅ <b>تم الخصم بنجاح!</b>\n\n"
                            f"👤 <b>المستخدم:</b> {target_id}\n"
                            f"💸 <b>المبلغ:</b> {-amount:,} دينار\n"
                            f"💳 <b>الرصيد الجديد:</b> {new_balance:,} دينار",
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await update.message.reply_text("❌ <b>فشل في الخصم. تحقق من ID المستخدم والرصيد</b>", parse_mode=ParseMode.HTML)
                    
                    # تنظيف
                    context.user_data.pop('action', None)
                    context.user_data.pop('charge_target', None)
                    await self.show_admin_panel(update.message)
                else:
                    await update.message.reply_text("❌ <b>أدخل مبلغاً صحيحاً</b>", parse_mode=ParseMode.HTML)
            
            elif action.startswith('price_'):
                # تغيير السعر
                service = action.replace('price_', '')
                
                if text.isdigit():
                    new_price = int(text)
                    self.settings['prices'][service] = new_price
                    self.save_settings()
                    
                    service_names = {
                        "exemption": "حساب درجة الإعفاء",
                        "summarize": "تلخيص الملازم",
                        "qa": "سؤال وجواب",
                        "materials": "ملازمي ومرشحاتي"
                    }
                    
                    await update.message.reply_text(
                        f"✅ <b>تم تغيير السعر بنجاح!</b>\n\n"
                        f"📝 <b>الخدمة:</b> {service_names.get(service, service)}\n"
                        f"💰 <b>السعر الجديد:</b> {new_price:,} دينار",
                        parse_mode=ParseMode.HTML
                    )
                    
                    context.user_data.pop('action', None)
                    await self.show_admin_panel(update.message)
                else:
                    await update.message.reply_text("❌ <b>أدخل سعراً صحيحاً</b>", parse_mode=ParseMode.HTML)
            
            elif action == 'welcome_bonus':
                # تغيير الهدية الترحيبية
                if text.isdigit():
                    new_bonus = int(text)
                    self.settings['welcome_bonus'] = new_bonus
                    self.save_settings()
                    
                    await update.message.reply_text(
                        f"✅ <b>تم تغيير الهدية الترحيبية!</b>\n\n"
                        f"🎁 <b>القيمة الجديدة:</b> {new_bonus:,} دينار",
                        parse_mode=ParseMode.HTML
                    )
                    
                    context.user_data.pop('action', None)
                    await self.show_admin_panel(update.message)
                else:
                    await update.message.reply_text("❌ <b>أدخل قيمة صحيحة</b>", parse_mode=ParseMode.HTML)
            
            elif action == 'referral_bonus':
                # تغيير مكافأة الدعوة
                if text.isdigit():
                    new_bonus = int(text)
                    self.settings['referral_bonus'] = new_bonus
                    self.save_settings()
                    
                    await update.message.reply_text(
                        f"✅ <b>تم تغيير مكافأة الدعوة!</b>\n\n"
                        f"👥 <b>القيمة الجديدة:</b> {new_bonus:,} دينار",
                        parse_mode=ParseMode.HTML
                    )
                    
                    context.user_data.pop('action', None)
                    await self.show_admin_panel(update.message)
                else:
                    await update.message.reply_text("❌ <b>أدخل قيمة صحيحة</b>", parse_mode=ParseMode.HTML)
            
            elif action == 'channel_link':
                # تغيير رابط القناة
                self.settings['channel_link'] = text
                self.save_settings()
                
                await update.message.reply_text(
                    f"✅ <b>تم تغيير رابط القناة!</b>\n\n"
                    f"📢 <b>الرابط الجديد:</b>\n{text}",
                    parse_mode=ParseMode.HTML
                )
                
                context.user_data.pop('action', None)
                await self.show_admin_panel(update.message)
            
            elif action == 'material_add':
                # إضافة مادة جديدة
                parts = text.split('|')
                if len(parts) >= 4:
                    name = parts[0].strip()
                    description = parts[1].strip()
                    stage = parts[2].strip()
                    url = parts[3].strip()
                    
                    materials = DataManager.load_data("materials_data.json", [])
                    
                    new_material = {
                        "id": len(materials) + 1,
                        "name": name,
                        "description": description,
                        "stage": stage,
                        "file_url": url,
                        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    materials.append(new_material)
                    DataManager.save_data("materials_data.json", materials)
                    
                    await update.message.reply_text(
                        f"✅ <b>تم إضافة المادة بنجاح!</b>\n\n"
                        f"📚 <b>الاسم:</b> {name}\n"
                        f"📝 <b>الوصف:</b> {description}\n"
                        f"🎓 <b>المرحلة:</b> {stage}\n"
                        f"🔗 <b>الرابط:</b> {url[:50]}...",
                        parse_mode=ParseMode.HTML
                    )
                    
                    context.user_data.pop('action', None)
                    await self.show_admin_panel(update.message)
                else:
                    await update.message.reply_text("❌ <b>تنسيق غير صحيح. استخدم | لفصل الحقول</b>", parse_mode=ParseMode.HTML)
        
        except Exception as e:
            logger.error(f"Error in admin message handler: {e}")
            await update.message.reply_text(f"❌ <b>حدث خطأ:</b> {str(e)}", parse_mode=ParseMode.HTML)
    
    def run(self):
        """تشغيل لوحة التحكم"""
        print("👑 لوحة التحكم تعمل الآن...")
        print(f"🆘 للمدير فقط: {ADMIN_ID}")
        print("📝 اكتب /admin في البوت للدخول")
        
        app = Application.builder().token(TOKEN).build()
        
        # إضافة handlers
        app.add_handler(CommandHandler("admin", self.admin_command))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# ============= تشغيل لوحة التحكم =============
if __name__ == "__main__":
    panel = AdminPanel()
    panel.run()
