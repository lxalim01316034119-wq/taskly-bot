import os
import json
import time
import telebot
from telebot import types
from datetime import datetime
from threading import Thread

# Flask keep-alive for Replit / Render / UptimeRobot
try:
    from flask import Flask
    app = Flask(__name__)
    @app.route('/')
    def home():
        return "Taskly Bot is Alive! Tasks 1,2,6 Active"
    def run_flask():
        port = int(os.getenv('PORT', 8080))
        app.run(host='0.0.0.0', port=port)
    Thread(target=run_flask, daemon=True).start()
    print("Flask keep-alive started on port 8080")
except:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN set koro!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "users.json"

# Channel to check - Bot must be admin in this channel - TASKLY OFFICIAL
CHANNEL_USERNAME = "@TasklyEarn_Official"  # tomar channel - TASKLY NEW
CHANNEL_ID = "@TasklyEarn_Official"  # same, or use -100... id if private

def is_user_joined(user_id):
    """Check if user joined channel"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Join check error: {e}")
        return False

# Tasks + Daily Bonus - Taskly Official channel - UPDATED with 1,2,6
DEFAULT_TASKS = [
    {
        "id": 1,
        "title": "Channel Subscription ($0.01)",
        "desc": "Amader Telegram Channel e join koro.\nReward: $0.01\n\nLink: https://t.me/TasklyEarn_Official\n\nJoin korar por Check button e click koro.",
        "reward": 0.01,
        "link": "https://t.me/TasklyEarn_Official"
    },
    {
        "id": 2,
        "title": "Daily Bonus ($0.005)",
        "desc": "Protidin bonus nao!\nReward: $0.005\n\n24 ghonta por por claim korte parba!",
        "reward": 0.005,
        "link": None,
        "daily": True
    },
    {
        "id": 6,
        "title": "App Download ($0.05)",
        "desc": "Amader Official App download koro.\nReward: $0.05 (Sobcheye beshi!)\n\nLink: https://play.google.com/store/apps/details?id=com.taskly.app\n\nDownload kore screenshot admin ke pathao, tarpor Claim koro.",
        "reward": 0.05,
        "link": "https://play.google.com/store/apps/details?id=com.taskly.app"
    }
]

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

users = load_data()

def get_user(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "balance": 0.0,
            "completed": [],
            "referrals": 0,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "verified": False,
            "last_daily": None
        }
        save_data()
    if "last_daily" not in users[uid]:
        users[uid]["last_daily"] = None
        save_data()
    return users[uid]

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("💰 Balance"), types.KeyboardButton("📋 Tasks"))
    markup.row(types.KeyboardButton("🎁 Daily Bonus"), types.KeyboardButton("💸 Withdraw"))
    markup.row(types.KeyboardButton("👤 Profile"), types.KeyboardButton("🏆 Top"))
    markup.row(types.KeyboardButton("👥 My Referrals"), types.KeyboardButton("🌐 Language"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    user = get_user(message.from_user.id)
    args = message.text.split()
    if len(args) > 1:
        ref_id = args[1]
        if ref_id != uid and ref_id in users:
            if "referred_by" not in user:
                user["referred_by"] = ref_id
                users[ref_id]["balance"] += 0.02
                users[ref_id]["referrals"] += 1
                save_data()
                try:
                    bot.send_message(ref_id, f"🎉 New referral! +$0.02 bonus. Total referrals: {users[ref_id]['referrals']}")
                except:
                    pass
    if not user["verified"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        markup.add(types.InlineKeyboardButton("📜 Terms of Use", url="https://telegram.org/tos"))
        bot.send_message(message.chat.id,
            "Welcome!\n\n"
            "☑ This Bot helps you earn money by doing simple tasks.\n"
            "By using this Bot, you agree to the Terms of Use.\n\n"
            "To access tasks, please complete verification.\n"
            "Click Verify button below.",
            reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
            f"Welcome back, {message.from_user.first_name}!\n\n"
            "✅ Verification successful. You now have access to tasks.\n"
            "Please select a task.",
            reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = str(call.from_user.id)
    user = get_user(call.from_user.id)
    if call.data == "verify":
        user["verified"] = True
        save_data()
        bot.edit_message_text("✅ Verification successful! You now have access to tasks.\nPlease select a task.", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Main menu:", reply_markup=main_menu())
    elif call.data.startswith("task_"):
        task_id = int(call.data.split("_")[1])
        task = next((t for t in DEFAULT_TASKS if t["id"] == task_id), None)
        if not task:
            return
        if task.get("daily"):
            today = datetime.now().strftime("%Y-%m-%d")
            if user.get("last_daily") == today:
                bot.answer_callback_query(call.id, "❌ Ajker bonus already niyechen!")
                bot.send_message(call.message.chat.id, f"❌ Ajker Daily Bonus already claim korechen!\nKal abar paben.\nBalance: ${user['balance']:.4f}", reply_markup=main_menu())
                return
        markup = types.InlineKeyboardMarkup()
        if task.get("link"):
            markup.add(types.InlineKeyboardButton("🔗 Open Task", url=task["link"]))
        markup.add(types.InlineKeyboardButton("✅ Claim / Completed", callback_data=f"done_{task_id}"))
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        bot.send_message(call.message.chat.id, f"📋 Task: {task['title']}\n\n{task['desc']}\n\nReview time: 1 min", reply_markup=markup)
    elif call.data.startswith("done_"):
        task_id = int(call.data.split("_")[1])
        task = next((t for t in DEFAULT_TASKS if t["id"] == task_id), None)
        if not task:
            return
        if task.get("daily"):
            today = datetime.now().strftime("%Y-%m-%d")
            if user.get("last_daily") == today:
                bot.answer_callback_query(call.id, "❌ Already claimed today!")
                return
            user["last_daily"] = today
            user["balance"] += task["reward"]
            save_data()
            bot.send_message(call.message.chat.id, f"🎁 Daily Bonus claimed! +${task['reward']:.4f}\nNew Balance: ${user['balance']:.4f}\n\nKal abar asben!", reply_markup=main_menu())
            return
        if task_id in user["completed"]:
            bot.answer_callback_query(call.id, "❌ Already completed!")
            return
        # ✅ JOIN CHECK - Task 1 er jonno
        if task_id == 1:
            if not is_user_joined(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Age channel e join koro!")
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔗 Join Channel", url="https://t.me/TasklyEarn_Official"))
                markup.add(types.InlineKeyboardButton("✅ I Joined - Check Again", callback_data=f"done_{task_id}"))
                bot.send_message(call.message.chat.id, 
                    f"❌ Tumi ekhono channel e join koro nai!\n\n👉 Age {CHANNEL_USERNAME} e join koro, tarpor 'I Joined - Check Again' e click koro.",
                    reply_markup=markup)
                return
        user["completed"].append(task_id)
        user["balance"] += task["reward"]
        save_data()
        bot.send_message(call.message.chat.id, f"🎉 Task completed! +${task['reward']:.4f} added.\nNew Balance: ${user['balance']:.4f}", reply_markup=main_menu())
    elif call.data == "cancel":
        bot.send_message(call.message.chat.id, "❌ Action cancelled.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Tasks")
def show_tasks(message):
    user = get_user(message.from_user.id)
    if not user["verified"]:
        bot.send_message(message.chat.id, "Please verify first with /start")
        return
    markup = types.InlineKeyboardMarkup()
    for t in DEFAULT_TASKS:
        if t.get("daily"):
            today = datetime.now().strftime("%Y-%m-%d")
            status = "✅ Claimed" if user.get("last_daily") == today else "🎁"
        else:
            status = "✅" if t["id"] in user["completed"] else "⏳"
        markup.add(types.InlineKeyboardButton(f"{status} {t['title']}", callback_data=f"task_{t['id']}"))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
    bot.send_message(message.chat.id, "Please select a task:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["🎁 Daily Bonus", "Daily Bonus"])
def daily_bonus_handler(message):
    user = get_user(message.from_user.id)
    if not user["verified"]:
        bot.send_message(message.chat.id, "Please verify first with /start")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    if user.get("last_daily") == today:
        bot.send_message(message.chat.id, f"❌ Ajker Daily Bonus already niyechen!\nBalance: ${user['balance']:.4f}\nKal abar asben!", reply_markup=main_menu())
        return
    task = next((t for t in DEFAULT_TASKS if t.get("daily")), None)
    if task:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎁 Claim Daily Bonus", callback_data=f"done_{task['id']}"))
        bot.send_message(message.chat.id, f"🎁 Daily Bonus Ready!\n\n{task['desc']}\nReward: ${task['reward']:.4f}", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    user = get_user(message.from_user.id)
    today = datetime.now().strftime("%Y-%m-%d")
    daily_status = "✅ Claimed" if user.get("last_daily") == today else "🎁 Available"
    bot.send_message(message.chat.id, f"💰 Your Balance: ${user['balance']:.4f}\nCompleted: {len(user['completed'])}\nReferrals: {user['referrals']}\nDaily: {daily_status}", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 Profile\nID: {message.from_user.id}\nName: {message.from_user.first_name}\nBalance: ${user['balance']:.4f}\nTasks: {len(user['completed'])}\nReferrals: {user['referrals']}\nJoined: {user['joined']}\nLast Daily: {user.get('last_daily', 'Never')}", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🏆 Top")
def top(message):
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
    txt = "🏆 Top Earners:\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        txt += f"{i}. User {uid[:6]}... - ${data['balance']:.4f}\n"
    bot.send_message(message.chat.id, txt, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "👥 My Referrals")
def refs(message):
    uid = str(message.from_user.id)
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"👥 Referrals: {user['referrals']}\nBonus: $0.02\n\nYour link:\n{link}", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "💸 Withdraw")
def withdraw(message):
    user = get_user(message.from_user.id)
    if user["balance"] < 0.10:
        bot.send_message(message.chat.id, f"❌ Minimum $0.10\nYour: ${user['balance']:.4f}\nComplete tasks + daily bonus.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, f"💸 Withdraw ${user['balance']:.4f}\nContact admin: @your_admin_username\nID: {message.from_user.id}", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text in ["🌐 Language", "Language"])
def lang(message):
    bot.send_message(message.chat.id, "🌐 Language: English (Default)", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def default(message):
    bot.send_message(message.chat.id, "Use menu buttons below:", reply_markup=main_menu())

print("Bot Started with Tasks 1,2,6 + Daily Bonus! Polling...")
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("Webhook cleared!")
except: pass

# AUTO-RECONNECT LOOP - 24h jonno
while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
    except Exception as e:
        print(f"Polling error: {e} - Restarting in 5 sec...")
        time.sleep(5)
