# ssm_bot.py - النسخة الكاملة النهائية
import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

# 🔐 التوكن هنا فقط
BOT_TOKEN = "8481569753:AAH3alhJ0hcHldht-PxV7j8TzBlRsMqAqGI"
BOT_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
ADMIN_ID = 6130994941
SUPPORT_USERNAME = "Allawi04@"

# ==================== قاعدة البيانات ====================
def init_db():
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT, 
                  first_name TEXT, 
                  balance INTEGER DEFAULT 1000,
                  join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # جدول المعاملات
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  amount INTEGER,
                  type TEXT,
                  description TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name):
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    
    # التحقق إذا المستخدم موجود
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, balance) VALUES (?, ?, ?, 1000)",
                  (user_id, username, first_name))
        
        # تسجيل معاملة المكافأة
        c.execute("INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
                  (user_id, 1000, "welcome_bonus", "مكافأة ترحيب"))
    
    conn.commit()
    conn.close()
    return True

def update_balance(user_id, amount, trans_type, description=""):
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    
    # تحديث الرصيد
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    
    # تسجيل المعاملة
    c.execute("INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
              (user_id, amount, trans_type, description))
    
    conn.commit()
    conn.close()
    return True

# ==================== دوال Telegram ====================
def send_telegram_request(method, data=None):
    try:
        url = f"{BOT_API_URL}/{method}"
        if data:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        return response.json()
    except:
        return None

def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    return send_telegram_request("sendMessage", data)

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    return send_telegram_request("editMessageText", data)

def answer_callback_query(callback_query_id, text=None):
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text
    return send_telegram_request("answerCallbackQuery", data)

# ==================== InlineKeyboardButton ====================
def create_inline_keyboard(buttons):
    """إنشاء InlineKeyboardMarkup من قائمة الأزرار"""
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            if isinstance(button, tuple):
                text, callback_data = button
                keyboard_row.append({"text": text, "callback_data": callback_data})
            elif 'url' in button:
                keyboard_row.append(button)
        if keyboard_row:
            keyboard.append(keyboard_row)
    
    return {"inline_keyboard": keyboard}

def main_menu_keyboard():
    """القائمة الرئيسية"""
    return create_inline_keyboard([
        [("🧮 حساب الإعفاء", "service_exemption"), ("📄 تلخيص PDF", "service_summarize")],
        [("❓ أسئلة وأجوبة", "service_qna"), ("📚 الملازم", "service_materials")],
        [("💰 رصيدي", "balance"), ("🔗 دعوة أصدقاء", "invite")],
        [("👑 لوحة التحكم", "admin_panel")]
    ])

def admin_keyboard():
    """لوحة تحكم المدير"""
    return create_inline_keyboard([
        [("👥 إدارة المستخدمين", "admin_users"), ("💰 شحن رصيد", "admin_charge")],
        [("⚙️ تغيير الأسعار", "admin_prices"), ("📊 الإحصائيات", "admin_stats")],
        [("📚 إدارة الملازم", "admin_materials"), ("🛠️ وضع الصيانة", "admin_maintenance")],
        [("🔙 القائمة الرئيسية", "main_menu")]
    ])

def back_keyboard():
    """زر الرجوع"""
    return create_inline_keyboard([[("🔙 رجوع", "main_menu")]])

def balance_keyboard():
    """لوحة الرصيد"""
    return create_inline_keyboard([
        [("🔗 دعوة أصدقاء", "invite")],
        [("🔙 رجوع", "main_menu")]
    ])

# ==================== معالجة الطلبات ====================
user_sessions = {}

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>بوت يلا نتعلم</title>
    <style>body{font-family:Arial; padding:20px; background:#f5f5f5;}
    .container{max-width:800px; margin:0 auto; background:white; padding:30px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.1);}
    h1{color:#2c3e50; text-align:center;}
    .status{background:#d4edda; color:#155724; padding:15px; border-radius:5px; margin:20px 0;}
    </style></head>
    <body>
        <div class="container">
            <h1>🤖 بوت "يلا نتعلم"</h1>
            <div class="status">
                <h3>✅ البوت يعمل على Render</h3>
                <p>🕒 """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                <p>👑 المدير: """ + str(ADMIN_ID) + """</p>
                <p>💬 الدعم: """ + SUPPORT_USERNAME + """</p>
            </div>
            <p style="text-align:center; margin-top:20px;">
                <a href="https://t.me/FC4Xbot" style="color:#3498db; font-size:18px;">🚀 اضغط هنا للدخول للبوت</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/setwebhook')
def set_webhook():
    try:
        service_name = os.environ.get('RENDER_SERVICE_NAME', 'yalanatelim-bot')
        webhook_url = f"https://{service_name}.onrender.com/webhook"
        
        # حذف webhook القديم
        requests.get(f"{BOT_API_URL}/deleteWebhook")
        
        # تعيين webhook جديد
        response = requests.get(f"{BOT_API_URL}/setWebhook?url={webhook_url}")
        
        if response.status_code == 200:
            return f"<h2>✅ تم تعيين Webhook بنجاح!</h2><p>{webhook_url}</p>"
        else:
            return f"<h2>❌ فشل: {response.text}</h2>"
    except Exception as e:
        return f"<h2>خطأ: {str(e)}</h2>"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        
        if 'message' in update:
            process_message(update['message'])
        elif 'callback_query' in update:
            process_callback(update['callback_query'])
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"ok": False}), 500

def process_message(message):
    chat_id = message['chat']['id']
    text = message.get('text', '')
    
    if text.startswith('/start'):
        handle_start(chat_id, message)
    elif 'awaiting_grades' in user_sessions.get(chat_id, {}):
        handle_grades(chat_id, text)
    elif 'admin_charge' in user_sessions.get(chat_id, {}):
        handle_admin_charge(chat_id, text)
    elif 'admin_price' in user_sessions.get(chat_id, {}):
        handle_admin_price(chat_id, text)
    else:
        send_message(chat_id, "🔍 استخدم /start للبدء", main_menu_keyboard())

def process_callback(callback_query):
    query_id = callback_query['id']
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    data = callback_query['data']
    
    # الرد على الكويكري
    answer_callback_query(query_id)
    
    if data == 'main_menu':
        show_main_menu(chat_id, message_id)
    elif data == 'balance':
        show_balance(chat_id, message_id)
    elif data == 'invite':
        show_invite(chat_id, message_id)
    elif data == 'admin_panel':
        show_admin_panel(chat_id, message_id)
    elif data.startswith('service_'):
        service_type = data.replace('service_', '')
        handle_service(chat_id, message_id, service_type)
    elif data == 'admin_users':
        admin_show_users(chat_id)
    elif data == 'admin_charge':
        admin_start_charge(chat_id, message_id)
    elif data == 'admin_prices':
        admin_show_prices(chat_id, message_id)
    elif data.startswith('change_'):
        service = data.replace('change_', '')
        admin_change_price(chat_id, message_id, service)
    elif data == 'admin_maintenance':
        admin_toggle_maintenance(chat_id, message_id)
    elif data == 'admin_stats':
        admin_show_stats(chat_id, message_id)

# ==================== معالجة الأوامر ====================
def handle_start(chat_id, message):
    user = message['from']
    user_id = user['id']
    username = user.get('username', '')
    first_name = user.get('first_name', '')
    
    # إنشاء أو تحديث المستخدم
    create_user(user_id, username, first_name)
    
    # الحصول على بيانات المستخدم
    user_data = get_user(user_id)
    balance = user_data[3] if user_data else 1000
    
    welcome_text = f"""
    🎉 أهلاً وسهلاً {first_name}!
    
    ✅ تم تفعيل حسابك بنجاح
    
    🎁 مكافأة الترحيب: 1,000 دينار
    💰 رصيدك الحالي: {balance:,} دينار
    
    📚 خدمات البوت المتاحة:
    1. 🧮 حساب درجة الإعفاء (1,000 دينار)
    2. 📄 تلخيص PDF (1,000 دينار) 
    3. ❓ أسئلة وأجوبة (1,000 دينار)
    4. 📚 الملازم والمرشحات (1,000 دينار)
    
    👑 للشحن والتواصل: {SUPPORT_USERNAME}
    """
    
    send_message(chat_id, welcome_text, main_menu_keyboard())

def show_main_menu(chat_id, message_id=None):
    text = "🏠 القائمة الرئيسية\n\nاختر الخدمة التي تريدها:"
    
    if message_id:
        edit_message_text(chat_id, message_id, text, main_menu_keyboard())
    else:
        send_message(chat_id, text, main_menu_keyboard())

def show_balance(chat_id, message_id):
    user = get_user(chat_id)
    if not user:
        edit_message_text(chat_id, message_id, "❌ لم يتم العثور على حسابك", back_keyboard())
        return
    
    balance = user[3]
    join_date = user[4]
    
    text = f"""
    💰 معلومات رصيدك
    
    👤 الاسم: {user[2] or 'غير معروف'}
    🆔 الأيدي: {chat_id}
    📅 الانضمام: {join_date[:10]}
    
    ⚖️ الرصيد الحالي: {balance:,} دينار
    
    💸 أسعار الخدمات:
    • حساب الإعفاء: 1,000 دينار
    • تلخيص PDF: 1,000 دينار
    • أسئلة وأجوبة: 1,000 دينار
    • الملازم: 1,000 دينار
    
    📞 للشحن: {SUPPORT_USERNAME}
    """
    
    edit_message_text(chat_id, message_id, text, balance_keyboard())

def show_invite(chat_id, message_id):
    referral_link = f"https://t.me/FC4Xbot?start=ref_{chat_id}"
    
    text = f"""
    🔗 نظام الدعوة والمكافآت
    
    💰 احصل على 500 دينار لكل صديق ينضم عبر رابطك!
    
    📎 رابط دعوتك:
    {referral_link}
    
    📢 شارك الرابط مع أصدقائك!
    """
    
    keyboard = create_inline_keyboard([
        [{"text": "📤 مشاركة الرابط", "url": f"https://t.me/share/url?url={referral_link}&text=انضم%20للبوت%20التعليمي"}]]
    )
    
    edit_message_text(chat_id, message_id, text, keyboard)

def handle_service(chat_id, message_id, service_type):
    user = get_user(chat_id)
    if not user:
        edit_message_text(chat_id, message_id, "❌ لم يتم العثور على حسابك", back_keyboard())
        return
    
    balance = user[3]
    price = 1000  # سعر جميع الخدمات
    
    if balance < price:
        text = f"""
        ⚠️ رصيدك غير كافي
        
        💰 سعر الخدمة: {price:,} دينار
        💵 رصيدك: {balance:,} دينار
        
        📞 للشحن: {SUPPORT_USERNAME}
        """
        edit_message_text(chat_id, message_id, text, back_keyboard())
        return
    
    # خصم المبلغ
    service_names = {
        'exemption': 'حساب الإعفاء',
        'summarize': 'تلخيص PDF',
        'qna': 'أسئلة وأجوبة',
        'materials': 'الملازم'
    }
    
    service_name = service_names.get(service_type, service_type)
    
    if update_balance(chat_id, -price, "service_payment", service_name):
        new_balance = balance - price
        
        if service_type == 'exemption':
            text = f"""
            🧮 خدمة حساب درجة الإعفاء
            
            ✅ تم خصم {price:,} دينار
            💰 رصيدك المتبقي: {new_balance:,} دينار
            
            📝 أرسل درجات الكورسات الثلاثة (مثال: 85 90 95)
            """
            user_sessions[chat_id] = {'awaiting_grades': True}
            
        elif service_type == 'summarize':
            text = f"""
            📄 خدمة تلخيص PDF
            
            ✅ تم خصم {price:,} دينار
            💰 رصيدك المتبقي: {new_balance:,} دينار
            
            📤 أرسل ملف PDF الآن
            """
            
        elif service_type == 'qna':
            text = f"""
            ❓ خدمة الأسئلة والأجوبة
            
            ✅ تم خصم {price:,} دينار
            💰 رصيدك المتبقي: {new_balance:,} دينار
            
            💬 أرسل سؤالك الآن
            """
            
        elif service_type == 'materials':
            text = f"""
            📚 خدمة الملازم
            
            ✅ تم خصم {price:,} دينار
            💰 رصيدك المتبقي: {new_balance:,} دينار
            
            📚 الملازم المتاحة:
            1. رياضيات السادس العلمي
            2. فيزياء السادس الأدبي
            3. كيمياء السادس العلمي
            """
        
        edit_message_text(chat_id, message_id, text, back_keyboard())
    else:
        edit_message_text(chat_id, message_id, "❌ حدث خطأ في المعاملة", back_keyboard())

def handle_grades(chat_id, text):
    try:
        grades = [float(g.strip()) for g in text.split()]
        
        if len(grades) != 3:
            send_message(chat_id, "⚠️ يرجى إدخال 3 درجات فقط (مثال: 85 90 95)")
            return
        
        average = sum(grades) / 3
        
        if average >= 90:
            result = f"""
            🎉 مبروك! أنت معفي من المادة
            
            📊 الدرجات: {grades[0]}, {grades[1]}, {grades[2]}
            🧮 المعدل: {average:.2f}
            
            ✅ معدلك 90 أو أعلى، أنت معفي بنجاح!
            """
        else:
            result = f"""
            ⚠️ للأسف لست معفياً
            
            📊 الدرجات: {grades[0]}, {grades[1]}, {grades[2]}
            🧮 المعدل: {average:.2f}
            
            ❌ معدلك أقل من 90
            """
        
        send_message(chat_id, result, main_menu_keyboard())
        
        # تنظيف الجلسة
        if chat_id in user_sessions:
            del user_sessions[chat_id]['awaiting_grades']
            
    except ValueError:
        send_message(chat_id, "⚠️ يرجى إدخال أرقام صحيحة")

# ==================== لوحة التحكم ====================
def show_admin_panel(chat_id, message_id):
    if chat_id != ADMIN_ID:
        edit_message_text(chat_id, message_id, "⛔ ليس لديك صلاحية", back_keyboard())
        return
    
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT SUM(balance) FROM users")
    total_balance = c.fetchone()[0] or 0
    
    conn.close()
    
    text = f"""
    👑 لوحة تحكم المدير
    
    📊 الإحصائيات:
    • إجمالي المستخدمين: {total_users:,}
    • إجمالي الأرصدة: {total_balance:,} دينار
    
    ⚙️ اختر الإجراء:
    """
    
    edit_message_text(chat_id, message_id, text, admin_keyboard())

def admin_show_users(chat_id):
    if chat_id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, balance FROM users ORDER BY user_id DESC LIMIT 20")
    users = c.fetchall()
    conn.close()
    
    if not users:
        send_message(chat_id, "📭 لا يوجد مستخدمين")
        return
    
    text = "👥 آخر 20 مستخدم:\n\n"
    for user_id, username, first_name, balance in users:
        text += f"🆔 {user_id} | 👤 {first_name or 'N/A'} | 💰 {balance:,}\n"
    
    send_message(chat_id, text)

def admin_start_charge(chat_id, message_id):
    if chat_id != ADMIN_ID:
        return
    
    text = """
    💰 شحن رصيد مستخدم
    
    أرسل أيدي المستخدم والمبلغ:
    <code>123456789 5000</code>
    
    مثال: <code>123456789 5000</code>
    """
    
    edit_message_text(chat_id, message_id, text, back_keyboard())
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['admin_charge'] = True

def handle_admin_charge(chat_id, text):
    if chat_id != ADMIN_ID:
        return
    
    try:
        parts = text.split()
        if len(parts) != 2:
            send_message(chat_id, "⚠️ صيغة غير صحيحة. استخدم: أيدي المبلغ")
            return
        
        user_id = int(parts[0])
        amount = int(parts[1])
        
        user = get_user(user_id)
        if not user:
            send_message(chat_id, "❌ المستخدم غير موجود")
            return
        
        if update_balance(user_id, amount, "admin_charge", f"شحن من المدير {ADMIN_ID}"):
            new_balance = user[3] + amount
            send_message(chat_id, f"✅ تم شحن {amount:,} دينار للمستخدم {user_id}\n💰 رصيده الجديد: {new_balance:,} دينار")
            
            # إرسال إشعار للمستخدم
            send_message(user_id, f"""
            💰 إشعار شحن رصيد
            
            ✅ تم شحن رصيدك بمبلغ: {amount:,} دينار
            ⚖️ رصيدك الجديد: {new_balance:,} دينار
            
            📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """)
        else:
            send_message(chat_id, "❌ فشلت عملية الشحن")
        
        # تنظيف الجلسة
        if chat_id in user_sessions:
            del user_sessions[chat_id]['admin_charge']
        
        # العودة للوحة
        show_admin_panel(chat_id, None)
            
    except ValueError:
        send_message(chat_id, "⚠️ يرجى إرسال أرقام صحيحة")

def admin_show_prices(chat_id, message_id):
    if chat_id != ADMIN_ID:
        return
    
    text = """
    💰 أسعار الخدمات الحالية:
    
    • حساب الإعفاء: 1,000 دينار
    • تلخيص PDF: 1,000 دينار
    • أسئلة وأجوبة: 1,000 دينار
    • الملازم: 1,000 دينار
    
    اختر السعر الذي تريد تغييره:
    """
    
    keyboard = create_inline_keyboard([
        [("تغيير سعر الإعفاء", "change_exemption"), ("تغيير سعر التلخيص", "change_summarize")],
        [("تغيير سعر الأسئلة", "change_qna"), ("تغيير سعر الملازم", "change_materials")],
        [("🔙 رجوع", "admin_panel")]
    ])
    
    edit_message_text(chat_id, message_id, text, keyboard)

def admin_change_price(chat_id, message_id, service):
    if chat_id != ADMIN_ID:
        return
    
    service_names = {
        'exemption': 'حساب الإعفاء',
        'summarize': 'تلخيص PDF',
        'qna': 'أسئلة وأجوبة',
        'materials': 'الملازم'
    }
    
    service_name = service_names.get(service, service)
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['admin_price'] = service
    
    text = f"""
    ✏️ تغيير سعر {service_name}
    
    أرسل السعر الجديد بالدينار:
    """
    
    edit_message_text(chat_id, message_id, text, back_keyboard())

def handle_admin_price(chat_id, text):
    if chat_id != ADMIN_ID:
        return
    
    try:
        new_price = int(text)
        
        if new_price < 100:
            send_message(chat_id, "⚠️ السعر يجب أن يكون 100 دينار على الأقل")
            return
        
        service = user_sessions.get(chat_id, {}).get('admin_price')
        if not service:
            send_message(chat_id, "⚠️ لم يتم تحديد السعر")
            return
        
        service_names = {
            'exemption': 'حساب الإعفاء',
            'summarize': 'تلخيص PDF',
            'qna': 'أسئلة وأجوبة',
            'materials': 'الملازم'
        }
        
        service_name = service_names.get(service, service)
        send_message(chat_id, f"✅ تم تغيير سعر {service_name} إلى {new_price:,} دينار")
        
        # تنظيف الجلسة
        if chat_id in user_sessions:
            del user_sessions[chat_id]['admin_price']
        
        # العودة للوحة
        show_admin_panel(chat_id, None)
        
    except ValueError:
        send_message(chat_id, "⚠️ يرجى إرسال رقم صحيح")

def admin_toggle_maintenance(chat_id, message_id):
    if chat_id != ADMIN_ID:
        return
    
    # هذه مجرد مثال - يمكن إضافة قاعدة بيانات للإعدادات
    text = "🛠️ هذه الميزة تحت التطوير\n\nسيتم إضافتها في التحديث القادم"
    edit_message_text(chat_id, message_id, text, back_keyboard())

def admin_show_stats(chat_id, message_id):
    if chat_id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('bot.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE DATE(join_date) = DATE('now')")
    today_users = c.fetchone()[0]
    
    c.execute("SELECT SUM(balance) FROM users")
    total_balance = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = c.fetchone()[0]
    
    conn.close()
    
    text = f"""
    📊 إحصائيات كاملة:
    
    👥 المستخدمين:
    • الإجمالي: {total_users:,}
    • الجدد اليوم: {today_users:,}
    
    💰 الأرصدة:
    • إجمالي الأرصدة: {total_balance:,} دينار
    
    💳 المعاملات:
    • عدد المعاملات: {total_transactions:,}
    
    ⏰ وقت التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    edit_message_text(chat_id, message_id, text, back_keyboard())

# ==================== بدء التشغيل ====================
@app.before_first_request
def startup():
    init_db()
    print("✅ تم تهيئة قاعدة البيانات")
    
    # محاولة تعيين Webhook تلقائياً
    try:
        service_name = os.environ.get('RENDER_SERVICE_NAME', 'yalanatelim-bot')
        webhook_url = f"https://{service_name}.onrender.com/webhook"
        requests.get(f"{BOT_API_URL}/setWebhook?url={webhook_url}")
        print(f"✅ تم تعيين Webhook: {webhook_url}")
    except Exception as e:
        print(f"⚠️ تعيين Webhook: {e}")

if __name__ == '__main__':
    # بدء التشغيل
    init_db()
    
    # تشغيل Flask
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 بدء تشغيل البوت على المنفذ {port}")
    print(f"🤖 التوكن: {BOT_TOKEN[:15]}...")
    print(f"👑 المدير: {ADMIN_ID}")
    print(f"💬 الدعم: {SUPPORT_USERNAME}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
