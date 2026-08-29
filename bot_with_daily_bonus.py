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
        return "Taskly Earn Official Bot is Alive! bKash/Nagad/Binance"
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
WITHDRAW_FILE = "withdraws.json"

# Admin ID - Tomar Telegram ID ekhane bosao ba Render e ENV variable ADMIN_ID set koro
# Telegram e @userinfobot e giye /start dile tomar ID pabe
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # 0 mane admin notify off, file e save hobe

# Channel to check - Bot must be admin in this channel - TASKLY OFFICIAL
CHANNEL_USERNAME = "@TasklyEarn_Official"
CHANNEL_ID = "@TasklyEarn_Official"

# User state for withdraw flow: {user_id: {step, method, account}}
user_states = {}

def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Join check error: {e}")
        return False

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

def load_withdraws():
    if os.path.exists(WITHDRAW_FILE):
        try:
            with open(WITHDRAW_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_withdraws():
    with open(WITHDRAW_FILE, "w", encoding="utf-8") as f:
        json.dump(withdraws, f, indent=2)

users = load_data()
withdraws = load_withdraws()

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

    elif call.data.startswith("withdraw_"):
        method = call.data.split("_")[1]
        if user["balance"] < 0.10:
            bot.answer_callback_query(call.id, "❌ Minimum $0.10 needed!")
            return
        user_states[call.from_user.id] = {"step": "awaiting_account", "method": method}
        method_name = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance (USDT/BEP20)"}[method]
        bot.edit_message_text(
            f"💸 {method_name} Withdraw Selected!\n\n"
            f"💰 Your Balance: ${user['balance']:.4f}\n"
            f"Minimum: $0.10\n\n"
            f"👉 Ekhon apnar {method_name} number / ID din:\n"
            f"bKash hole: 01XXXXXXXXX\n"
            f"Nagad hole: 01XXXXXXXXX\n"
            f"Binance hole: Binance ID / Email / Wallet Address\n\n"
            f"❌ Cancel korte /cancel likhun",
            call.message.chat.id, call.message.message_id
        )
        bot.answer_callback_query(call.id, f"{method_name} selected")

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
        if task_id in user["completed"]:
            markup.add(types.InlineKeyboardButton("✅ Completed", callback_data="already_done"))
        else:
            markup.add(types.InlineKeyboardButton("✅ Claim / Completed", callback_data=f"done_{task_id}"))
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        bot.send_message(call.message.chat.id, f"📋 {task['title']}\n\n{task['desc']}\nReward: ${task['reward']:.4f}", reply_markup=markup)

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
        if call.from_user.id in user_states:
            del user_states[call.from_user.id]
        bot.send_message(call.message.chat.id, "❌ Action cancelled.", reply_markup=main_menu())
    elif call.data == "already_done":
        bot.answer_callback_query(call.id, "Already completed!")

@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ Withdraw cancelled.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Nothing to cancel.", reply_markup=main_menu())

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
        bot.send_message(message.chat.id, f"❌ Minimum Withdraw $0.10\nYour Balance: ${user['balance']:.4f}\n\nComplete tasks + daily bonus + referrals to reach $0.10", reply_markup=main_menu())
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📱 bKash (BDT)", callback_data="withdraw_bkash"),
        types.InlineKeyboardButton("📱 Nagad (BDT)", callback_data="withdraw_nagad"),
        types.InlineKeyboardButton("🟡 Binance USDT", callback_data="withdraw_binance"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    )
    bot.send_message(message.chat.id, 
        f"💸 Withdraw - Select Method\n\n"
        f"💰 Balance: ${user['balance']:.4f}\n"
        f"Minimum: $0.10\n"
        f"Rate: $1 = ~124 BDT (bKash/Nagad)\n\n"
        f"👇 Method select korun:",
        reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def withdraw_flow(message):
    uid = message.from_user.id
    state = user_states.get(uid)
    if not state:
        return
    if state["step"] == "awaiting_account":
        account = message.text.strip()
        if len(account) < 6:
            bot.send_message(message.chat.id, "❌ Valid number/ID din! Abar try korun:")
            return
        state["account"] = account
        state["step"] = "awaiting_amount"
        bot.send_message(message.chat.id, 
            f"✅ Account: {account}\n\n"
            f"💰 Koto withdraw korben? Amount likhun:\n"
            f"Example: 0.15\n"
            f"Balance: ${get_user(uid)['balance']:.4f}\n"
            f"Min: $0.10\n\n"
            f"Full balance withdraw korte 'all' likhun."
        )
    elif state["step"] == "awaiting_amount":
        user = get_user(uid)
        txt = message.text.strip().lower()
        if txt == "all":
            amount = user["balance"]
        else:
            try:
                amount = float(txt.replace("$", ""))
            except:
                bot.send_message(message.chat.id, "❌ Valid amount din! Example: 0.10 ba all")
                return
        if amount < 0.10:
            bot.send_message(message.chat.id, f"❌ Minimum $0.10! Apni diyechen ${amount:.4f}")
            return
        if amount > user["balance"] + 0.0001:
            bot.send_message(message.chat.id, f"❌ Balance kom! Balance: ${user['balance']:.4f}")
            return
        user["balance"] -= amount
        save_data()
        method_map = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance USDT"}
        method_name = method_map.get(state["method"], state["method"])
        record = {
            "user_id": uid,
            "username": message.from_user.username,
            "name": message.from_user.first_name,
            "method": method_name,
            "account": state["account"],
            "amount_usd": round(amount, 4),
            "amount_bdt": round(amount * 124, 2) if state["method"] in ["bkash", "nagad"] else None,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        }
        withdraws.append(record)
        save_withdraws()
        del user_states[uid]
        bdt_txt = f" (~{record['amount_bdt']} BDT)" if record['amount_bdt'] else ""
        bot.send_message(message.chat.id,
            f"✅ Withdraw Request Received!\n\n"
            f"💳 Method: {method_name}\n"
            f"🔢 Account: {state['account']}\n"
            f"💵 Amount: ${amount:.4f}{bdt_txt}\n"
            f"⏰ Time: {record['time']}\n"
            f"📋 Status: Pending (24h er moddhe payment)\n\n"
            f"💰 New Balance: ${user['balance']:.4f}\n\n"
            f"Admin apnake payment korbe, tarpor channel e proof deya hobe!",
            reply_markup=main_menu()
        )
        if ADMIN_ID != 0:
            try:
                bot.send_message(ADMIN_ID,
                    f"🔔 NEW WITHDRAW REQUEST!\n\n"
                    f"👤 User: {record['name']} (@{record['username']})\n"
                    f"🆔 ID: {uid}\n"
                    f"💳 Method: {method_name}\n"
                    f"🔢 Account: {state['account']}\n"
                    f"💵 Amount: ${amount:.4f}{bdt_txt}\n"
                    f"⏰ {record['time']}\n\n"
                    f"Payment diye /admin_withdraws e giye paid mark koro."
                )
            except Exception as e:
                print(f"Admin notify failed: {e}")

@bot.message_handler(commands=['admin_withdraws'])
def admin_withdraws(message):
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    if not withdraws:
        bot.send_message(message.chat.id, "No withdraw requests yet.")
        return
    txt = f"📋 Total Withdraws: {len(withdraws)}\n\n"
    for w in withdraws[-10:][::-1]:
        bdt = f" ({w['amount_bdt']} BDT)" if w.get('amount_bdt') else ""
        txt += f"👤 {w['name']} | {w['method']} | ${w['amount_usd']}{bdt} | {w['account']} | {w['status']} | {w['time']}\n\n"
    bot.send_message(message.chat.id, txt)

@bot.message_handler(func=lambda m: m.text in ["🌐 Language", "Language"])
def lang(message):
    bot.send_message(message.chat.id, "🌐 Language: English (Default)", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def default(message):
    if message.from_user.id in user_states:
        return
    bot.send_message(message.chat.id, "Use menu buttons below:", reply_markup=main_menu())

print("Bot Started with Tasks 1,2,6 + bKash/Nagad/Binance Withdraw! Polling...")
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("Webhook cleared!")
except: pass

while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
    except Exception as e:
        print(f"Polling error: {e} - Restarting in 5 sec...")
        time.sleep(5)
