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
        return "Profit Bot Alive! Income > Payout - bKash/Nagad/Binance"
    def run_flask():
        port = int(os.getenv('PORT', 8080))
        app.run(host='0.0.0.0', port=port)
    Thread(target=run_flask, daemon=True).start()
    print("Flask keep-alive started")
except:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN set koro!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "users.json"
WITHDRAW_FILE = "withdraws.json"
TASKS_FILE = "tasks.json"
INCOME_FILE = "income.json"
STATS_FILE = "stats.json"

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@TasklyEarn_Official")
CHANNEL_ID = CHANNEL_USERNAME
MIN_WITHDRAW = float(os.getenv("MIN_WITHDRAW", "1.00"))  # PROFIT: $1.00 minimum

user_states = {}

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_data(): return load_json(DATA_FILE, {})
def save_data(): save_json(DATA_FILE, users)
def load_withdraws(): return load_json(WITHDRAW_FILE, [])
def save_withdraws(): save_json(WITHDRAW_FILE, withdraws)
def load_tasks(): return load_json(TASKS_FILE, None)
def save_tasks(): save_json(TASKS_FILE, tasks)
def load_income(): return load_json(INCOME_FILE, [])
def save_income(): save_json(INCOME_FILE, incomes)
def load_stats(): return load_json(STATS_FILE, {"total_income": 0.0, "total_payout": 0.0, "total_tasks_done": 0})

users = load_data()
withdraws = load_withdraws()
incomes = load_income()
stats = load_stats()

# Default profit tasks - Reward < Sponsor Income = PROFIT
DEFAULT_TASKS = [
    {
        "id": 1,
        "title": "Join Main Channel ($0.01)",
        "desc": "Amader Main Channel e join koro.\nReward: $0.01\n\nLink: https://t.me/TasklyEarn_Official\n\nJoin korar por Check koro.",
        "reward": 0.01,
        "sponsor_income": 0.05,  # Sponsor gives 0.05, you give 0.01 = Profit 0.04
        "link": "https://t.me/TasklyEarn_Official",
        "sponsor": "Own Channel Growth"
    },
    {
        "id": 2,
        "title": "Daily Bonus ($0.005)",
        "desc": "Protidin bonus nao!\nReward: $0.005\n\n24 ghonta por por claim korte parba!",
        "reward": 0.005,
        "sponsor_income": 0.00,  # No sponsor, but needed for retention
        "link": None,
        "daily": True,
        "sponsor": "Retention"
    },
    {
        "id": 3,
        "title": "Sponsor Channel 1 ($0.02)",
        "desc": "Sponsor er Channel e join koro.\nReward: $0.02\n\nLink: https://t.me/EarningTipsBD_Official\n\nJoin korar por Check koro.",
        "reward": 0.02,
        "sponsor_income": 0.10,  # Sponsor pays $0.10, you pay $0.02 = Profit $0.08
        "link": "https://t.me/EarningTipsBD_Official",
        "sponsor": "Paid Sponsor - 100 BDT per 1000 joins"
    },
    {
        "id": 4,
        "title": "App Install ($0.05)",
        "desc": "Sponsor App install koro.\nReward: $0.05 (High!)\n\nLink: https://play.google.com/store/apps/details?id=com.taskly.app\n\nInstall kore screenshot admin ke pathao, tarpor Claim koro.",
        "reward": 0.05,
        "sponsor_income": 0.30,  # CPA network pays $0.30 per install, you pay $0.05 = Profit $0.25
        "link": "https://play.google.com/store/apps/details?id=com.taskly.app",
        "sponsor": "CPA - App Install $0.30"
    },
    {
        "id": 5,
        "title": "Ad Click - Link Shortener ($0.002)",
        "desc": "Link e click kore 10 sec wait koro.\nReward: $0.002\n\nLink: https://shrinkme.io/example\n\nClick kore ad dekho, tarpor Check.",
        "reward": 0.002,
        "sponsor_income": 0.01,  # Ad network pays $0.01 per click
        "link": "https://shrinkme.io/example",
        "sponsor": "Ad Network - $0.01 per click"
    }
]

tasks_data = load_tasks()
if tasks_data is None:
    tasks = DEFAULT_TASKS
    save_tasks()
else:
    tasks = tasks_data

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

def is_admin(user_id):
    if ADMIN_ID == 0:
        return True
    return user_id == ADMIN_ID

# ================= ADMIN COMMANDS - PROFIT =================

@bot.message_handler(commands=['addtask'])
def addtask_cmd(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    try:
        # Format: /addtask Title | Description | Reward | SponsorIncome | Link | SponsorName
        text = message.text[len("/addtask"):].strip()
        if "|" not in text:
            bot.send_message(message.chat.id,
                "❌ Format:\n/addtask Title | Description | Reward | SponsorIncome | Link | SponsorName\n\n"
                "Example:\n/addtask Join BD Earning | Join @BDEarning | 0.02 | 0.10 | https://t.me/BDEarning | Sponsor pays 1000 BDT"
            )
            return
        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 5:
            bot.send_message(message.chat.id, "❌ Minimum 5 part lagbe: Title | Desc | Reward | SponsorIncome | Link")
            return
        title = parts[0]
        desc = parts[1]
        reward = float(parts[2])
        sponsor_income = float(parts[3])
        link = parts[4]
        sponsor_name = parts[5] if len(parts) > 5 else "Paid Sponsor"
        
        new_id = max([t["id"] for t in tasks], default=0) + 1
        new_task = {
            "id": new_id,
            "title": f"{title} (${reward})",
            "desc": f"{desc}\nReward: ${reward}\n\nLink: {link}\n\nJoin korar por Check koro.",
            "reward": reward,
            "sponsor_income": sponsor_income,
            "link": link,
            "sponsor": sponsor_name
        }
        tasks.append(new_task)
        save_tasks()
        profit = sponsor_income - reward
        bot.send_message(message.chat.id,
            f"✅ Task Added!\n\nID: {new_id}\nTitle: {title}\nReward: ${reward} (user pabe)\nSponsor Income: ${sponsor_income} (tumi paba)\nProfit: ${profit:.4f} per user\nLink: {link}\n\nSponsor: {sponsor_name}"
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['deltask'])
def deltask_cmd(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Usage: /deltask TASK_ID")
            return
        tid = int(parts[1])
        global tasks
        before = len(tasks)
        tasks = [t for t in tasks if t["id"] != tid]
        if len(tasks) == before:
            bot.send_message(message.chat.id, "❌ Task ID not found!")
            return
        save_tasks()
        bot.send_message(message.chat.id, f"✅ Task {tid} deleted!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['addincome'])
def addincome_cmd(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.send_message(message.chat.id, "Usage: /addincome AMOUNT Description\nExample: /addincome 10 Sponsor @BDEarning paid for 1000 joins")
            return
        amount = float(parts[1])
        desc = parts[2]
        record = {
            "amount": amount,
            "desc": desc,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        incomes.append(record)
        stats["total_income"] += amount
        save_income()
        save_json(STATS_FILE, stats)
        bot.send_message(message.chat.id, f"✅ Income Added: ${amount:.2f}\nDesc: {desc}\nTotal Income: ${stats['total_income']:.2f}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['adminstats', 'profit', 'stats'])
def admin_stats(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    total_income = stats.get("total_income", 0.0)
    total_payout = stats.get("total_payout", 0.0)
    profit = total_income - total_payout
    pending_withdraw = sum([w["amount_usd"] for w in withdraws if w.get("status") == "pending"])
    pending_count = len([w for w in withdraws if w.get("status") == "pending"])
    
    txt = f"📊 ADMIN PROFIT DASHBOARD\n\n"
    txt += f"💰 Total Sponsor Income: ${total_income:.4f}\n"
    txt += f"💸 Total User Payout: ${total_payout:.4f}\n"
    txt += f"📈 PROFIT: ${profit:.4f} {'✅' if profit >=0 else '❌ LOSS'}\n\n"
    txt += f"⏳ Pending Withdraws: {pending_count} (${pending_withdraw:.4f})\n"
    txt += f"👥 Total Users: {len(users)}\n"
    txt += f"📋 Total Tasks Done: {stats.get('total_tasks_done', 0)}\n"
    txt += f"💵 Min Withdraw: ${MIN_WITHDRAW:.2f}\n\n"
    txt += f"📋 Recent Incomes:\n"
    for inc in incomes[-5:][::-1]:
        txt += f"  +${inc['amount']} - {inc['desc'][:30]} ({inc['time']})\n"
    txt += f"\n💡 Tip: /addincome diye sponsor er taka add koro, /addtask diye profit task add koro!"
    bot.send_message(message.chat.id, txt)

@bot.message_handler(commands=['markpaid'])
def markpaid_cmd(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Usage: /markpaid USER_ID or /markpaid all")
            return
        target = parts[1].lower()
        count = 0
        if target == "all":
            for w in withdraws:
                if w["status"] == "pending":
                    w["status"] = "paid"
                    count += 1
            save_withdraws()
            bot.send_message(message.chat.id, f"✅ {count} withdraws marked as PAID!")
        else:
            uid = str(target)
            for w in withdraws:
                if str(w["user_id"]) == uid and w["status"] == "pending":
                    w["status"] = "paid"
                    count += 1
            save_withdraws()
            bot.send_message(message.chat.id, f"✅ {count} withdraws for user {uid} marked as PAID!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['addbalance', 'add_balance'])
def add_balance_cmd(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Usage: /addbalance USER_ID AMOUNT\nExample: /addbalance me 0.20 or /addbalance 123456789 0.50")
            return
        target_id = parts[1].strip()
        amount = float(parts[2])
        if target_id.lower() == "me":
            uid = str(message.from_user.id)
        else:
            uid = str(target_id)
        if uid not in users:
            bot.send_message(message.chat.id, f"❌ User {uid} not found! User must /start first.")
            return
        users[uid]["balance"] += amount
        save_data()
        bot.send_message(message.chat.id, f"✅ Added ${amount:.4f} to {uid}\nNew Balance: ${users[uid]['balance']:.4f}")
        if uid != str(message.from_user.id):
            try:
                bot.send_message(uid, f"🎉 Admin added ${amount:.4f} to your balance!\nNew Balance: ${users[uid]['balance']:.4f}")
            except:
                pass
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['removebalance'])
def remove_balance_cmd(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    try:
        parts = message.text.split()
        target_id = parts[1].strip()
        amount = float(parts[2])
        uid = str(target_id)
        if uid not in users:
            bot.send_message(message.chat.id, "❌ User not found!")
            return
        users[uid]["balance"] = max(0, users[uid]["balance"] - amount)
        save_data()
        bot.send_message(message.chat.id, f"✅ Removed ${amount:.4f} from {uid}\nNew Balance: ${users[uid]['balance']:.4f}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['admin_withdraws'])
def admin_withdraws(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Admin only!")
        return
    if not withdraws:
        bot.send_message(message.chat.id, "No withdraw requests yet.")
        return
    txt = f"📋 Total Withdraws: {len(withdraws)} | Pending: {len([w for w in withdraws if w['status']=='pending'])}\n\n"
    for w in withdraws[-10:][::-1]:
        bdt = f" ({w['amount_bdt']} BDT)" if w.get('amount_bdt') else ""
        txt += f"👤 {w['name']} | {w['method']} | ${w['amount_usd']}{bdt} | {w['account']} | {w['status']} | {w['time']}\n\n"
    bot.send_message(message.chat.id, txt)

# ================= USER HANDLERS =================

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
                stats["total_payout"] += 0.02
                save_json(STATS_FILE, stats)
                save_data()
                try:
                    bot.send_message(ref_id, f"🎉 New referral! +$0.02 bonus. Total referrals: {users[ref_id]['referrals']}")
                except:
                    pass
    if not user["verified"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(message.chat.id,
            "Welcome to PROFIT Earn Bot!\n\n"
            "☑ Earn by doing sponsor tasks\n"
            "💰 Min Withdraw: $1.00\n"
            "💸 bKash/Nagad/Binance\n\n"
            "Click Verify to start!",
            reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
            f"Welcome back, {message.from_user.first_name}!\n\n"
            f"💰 Balance: ${user['balance']:.4f}\n"
            f"Min Withdraw: ${MIN_WITHDRAW:.2f}\n"
            f"Please select a task.",
            reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = str(call.from_user.id)
    user = get_user(call.from_user.id)

    if call.data == "verify":
        user["verified"] = True
        save_data()
        bot.edit_message_text("✅ Verification successful!", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Main menu:", reply_markup=main_menu())

    elif call.data.startswith("withdraw_"):
        method = call.data.split("_")[1]
        if user["balance"] < MIN_WITHDRAW:
            bot.answer_callback_query(call.id, f"❌ Minimum ${MIN_WITHDRAW:.2f} needed! Your: ${user['balance']:.4f}")
            return
        user_states[call.from_user.id] = {"step": "awaiting_account", "method": method}
        method_name = {"bkash":"bKash", "nagad":"Nagad", "binance":"Binance USDT"}.get(method, method)
        bot.send_message(call.message.chat.id,
            f"💳 {method_name} Selected!\n\n"
            f"📱 Tomar {method_name} number / ID dao:\n"
            f"Example: 01XXXXXXXXX (bKash/Nagad) or Binance Email/ID\n\n"
            f"⚠️ Vul number dile taka harabe!"
        )
        bot.answer_callback_query(call.id)

    elif call.data == "cancel":
        if call.from_user.id in user_states:
            del user_states[call.from_user.id]
        bot.edit_message_text("❌ Cancelled", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Main menu:", reply_markup=main_menu())

    elif call.data.startswith("task_"):
        try:
            tid = int(call.data.split("_")[1])
            action = call.data.split("_")[2] if len(call.data.split("_")) > 2 else "view"
            task = next((t for t in tasks if t["id"] == tid), None)
            if not task:
                bot.answer_callback_query(call.id, "❌ Task not found!")
                return
            if uid in [str(x) for x in user.get("completed", [])] or tid in user.get("completed", []):
                bot.answer_callback_query(call.id, "✅ Already completed!")
                return
            if action == "view":
                markup = types.InlineKeyboardMarkup()
                if task.get("link"):
                    markup.add(types.InlineKeyboardButton("🔗 Open Link", url=task["link"]))
                markup.add(types.InlineKeyboardButton("✅ Check & Claim", callback_data=f"task_{tid}_claim"))
                markup.add(types.InlineKeyboardButton("❌ Back", callback_data="back_tasks"))
                bot.edit_message_text(
                    f"📋 {task['title']}\n\n{task['desc']}\n\nReward: ${task['reward']}",
                    call.message.chat.id, call.message.message_id, reply_markup=markup
                )
            elif action == "claim":
                # Daily check
                if task.get("daily"):
                    last = user.get("last_daily")
                    if last:
                        last_date = datetime.strptime(last, "%Y-%m-%d %H:%M:%S") if len(last) > 10 else datetime.strptime(last, "%Y-%m-%d")
                        if (datetime.now() - last_date).total_seconds() < 24*3600:
                            bot.answer_callback_query(call.id, "❌ Daily bonus 24h por! Already claimed today.")
                            return
                    user["last_daily"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # For channel join tasks, check join (optional)
                user["balance"] += task["reward"]
                if "completed" not in user:
                    user["completed"] = []
                user["completed"].append(tid)
                stats["total_payout"] += task["reward"]
                stats["total_income"] += task.get("sponsor_income", 0)
                stats["total_tasks_done"] = stats.get("total_tasks_done", 0) + 1
                save_data()
                save_json(STATS_FILE, stats)
                bot.edit_message_text(
                    f"✅ Task Completed!\n\n{task['title']}\n+${task['reward']:.4f} added!\n\nNew Balance: ${user['balance']:.4f}",
                    call.message.chat.id, call.message.message_id
                )
                bot.send_message(call.message.chat.id, "Main menu:", reply_markup=main_menu())
                bot.answer_callback_query(call.id, f"+${task['reward']:.4f} added!")
        except Exception as e:
            print(f"Task callback error: {e}")
            bot.answer_callback_query(call.id, f"Error: {e}")

    elif call.data == "back_tasks":
        show_tasks_list(call.message)

def show_tasks_list(message_or_call):
    chat_id = message_or_call.chat.id if hasattr(message_or_call, 'chat') else message_or_call.message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    for t in tasks:
        markup.add(types.InlineKeyboardButton(f"{t['title']}", callback_data=f"task_{t['id']}_view"))
    # Edit or send
    try:
        bot.edit_message_text(f"📋 Available Tasks ({len(tasks)}) - Min Withdraw ${MIN_WITHDRAW:.2f}\n\nSelect a task to earn:", chat_id, message_or_call.message_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, f"📋 Available Tasks ({len(tasks)}) - Min Withdraw ${MIN_WITHDRAW:.2f}\n\nSelect a task to earn:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📋 Tasks")
def show_tasks(message):
    user = get_user(message.from_user.id)
    if not user["verified"]:
        bot.send_message(message.chat.id, "Please verify first with /start")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for t in tasks:
        done = "✅" if t["id"] in user.get("completed", []) else "💰"
        markup.add(types.InlineKeyboardButton(f"{done} {t['title']}", callback_data=f"task_{t['id']}_view"))
    bot.send_message(message.chat.id, f"📋 Tasks ({len(tasks)}) | Min Withdraw ${MIN_WITHDRAW:.2f} | Balance ${user['balance']:.4f}\n\nSelect:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 Balance: ${user['balance']:.4f}\nMin Withdraw: ${MIN_WITHDRAW:.2f}\nNeed: ${max(0, MIN_WITHDRAW - user['balance']):.4f} more", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎁 Daily Bonus")
def daily_bonus(message):
    user = get_user(message.from_user.id)
    daily_task = next((t for t in tasks if t.get("daily")), None)
    if not daily_task:
        bot.send_message(message.chat.id, "No daily bonus today!", reply_markup=main_menu())
        return
    if daily_task["id"] in user.get("completed", []):
        # Check if 24h passed for re-claim
        last = user.get("last_daily")
        if last:
            try:
                last_date = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - last_date).total_seconds() < 24*3600:
                    bot.send_message(message.chat.id, f"❌ Already claimed! 24h wait. Last: {last}", reply_markup=main_menu())
                    return
            except:
                pass
        # Allow re-do daily
        user["completed"] = [x for x in user["completed"] if x != daily_task["id"]]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎁 Claim Daily Bonus", callback_data=f"task_{daily_task['id']}_claim"))
    bot.send_message(message.chat.id, f"🎁 Daily Bonus: ${daily_task['reward']}\n\nClick to claim:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"👤 Profile\nID: {message.from_user.id}\nName: {message.from_user.first_name}\nBalance: ${user['balance']:.4f}\nTasks: {len(user['completed'])}\nReferrals: {user['referrals']}\nJoined: {user['joined']}", reply_markup=main_menu())

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
    bot.send_message(message.chat.id, f"👥 Referrals: {user['referrals']}\nBonus: $0.02 per referral\n\nYour link:\n{link}\n\nShare and earn! When friend joins, you get $0.02", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "💸 Withdraw")
def withdraw(message):
    user = get_user(message.from_user.id)
    if user["balance"] < MIN_WITHDRAW:
        bot.send_message(message.chat.id, f"❌ Minimum Withdraw ${MIN_WITHDRAW:.2f}\nYour Balance: ${user['balance']:.4f}\nNeed ${MIN_WITHDRAW - user['balance']:.4f} more\n\nComplete more tasks!", reply_markup=main_menu())
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
        f"Minimum: ${MIN_WITHDRAW:.2f}\n"
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
            bot.send_message(message.chat.id, "❌ Valid number/ID din!")
            return
        state["account"] = account
        state["step"] = "awaiting_amount"
        bot.send_message(message.chat.id, 
            f"✅ Account: {account}\n\n"
            f"💰 Koto withdraw korben? Amount likhun:\n"
            f"Example: 1.00\n"
            f"Balance: ${get_user(uid)['balance']:.4f}\n"
            f"Min: ${MIN_WITHDRAW:.2f}\n\n"
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
                bot.send_message(message.chat.id, "❌ Valid amount din!")
                return
        if amount < MIN_WITHDRAW:
            bot.send_message(message.chat.id, f"❌ Minimum ${MIN_WITHDRAW:.2f}!")
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
            f"💰 New Balance: ${user['balance']:.4f}",
            reply_markup=main_menu()
        )
        if ADMIN_ID != 0:
            try:
                bot.send_message(ADMIN_ID,
                    f"🔔 NEW WITHDRAW!\n\n"
                    f"👤 {record['name']} (@{record['username']})\n"
                    f"🆔 {uid}\n"
                    f"💳 {method_name}\n"
                    f"🔢 {state['account']}\n"
                    f"💵 ${amount:.4f}{bdt_txt}\n"
                    f"⏰ {record['time']}"
                )
            except:
                pass

@bot.message_handler(func=lambda m: m.text in ["🌐 Language", "Language"])
def lang(message):
    bot.send_message(message.chat.id, "🌐 Language: English", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def default(message):
    if message.from_user.id in user_states:
        return
    bot.send_message(message.chat.id, "Use menu buttons below:", reply_markup=main_menu())

print(f"Profit Bot Started! Min Withdraw ${MIN_WITHDRAW} | Profit = Income - Payout")
try:
    bot.delete_webhook(drop_pending_updates=True)
except: pass

while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
    except Exception as e:
        print(f"Polling error: {e} - Restarting in 5 sec...")
        time.sleep(5)
