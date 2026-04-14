import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import time
import random
import os

TOKEN = os.getenv("TOKEN") or "8640949306:AAG5n2Af4LHtj8qe5pT1eLZb4oY1pe_NT3c"
bot = telebot.TeleBot(TOKEN)

# ===== БД =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER,
    bank INTEGER,
    bone INTEGER,
    tree INTEGER,
    fap INTEGER,
    last_dig INTEGER,
    last_water INTEGER,
    last_bonus INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_stats (
    chat_id INTEGER PRIMARY KEY,
    messages INTEGER
)
""")

conn.commit()

# ===== UTILS =====
def get_user(uid, name):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cursor.fetchone()
    if not u:
        cursor.execute("INSERT INTO users VALUES (?, ?, 500, 5, 5, 0, 0, 0, 0, 0)", (uid, name))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        u = cursor.fetchone()
    return u

def add(field, val, uid):
    cursor.execute(f"UPDATE users SET {field}={field}+? WHERE user_id=?", (val, uid))
    conn.commit()

def update(field, val, uid):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (val, uid))
    conn.commit()

def cooldown(last, cd):
    now = int(time.time())
    if now - last >= cd:
        return True, 0
    return False, cd - (now - last)

def fmt(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    return f"{h}ч {m}м"

def tree_fmt(cm):
    if cm < 100:
        return f"{cm} см"
    return f"{cm//100} м {cm%100} см"

def rand(a, b): return random.randint(a, b)
def rand_res(): return random.choice(["bank", "bone"])

def add_msg(chat_id):
    cursor.execute("INSERT OR IGNORE INTO chat_stats VALUES (?,0)", (chat_id,))
    cursor.execute("UPDATE chat_stats SET messages = messages+1 WHERE chat_id=?", (chat_id,))
    conn.commit()

def get_msgs(chat_id):
    cursor.execute("INSERT OR IGNORE INTO chat_stats VALUES (?,0)", (chat_id,))
    cursor.execute("SELECT messages FROM chat_stats WHERE chat_id=?", (chat_id,))
    return cursor.fetchone()[0]

# ===== КНОПКИ =====
def menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👤 Профиль", callback_data="profile"),
           InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"))
    kb.add(InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
           InlineKeyboardButton("🎁 Бонус", callback_data="bonus"))
    kb.add(InlineKeyboardButton("🏆 Топ", callback_data="top"))
    return kb

def profile_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"))
    kb.add(InlineKeyboardButton("🌳 Дерево", callback_data="tree"))
    kb.add(InlineKeyboardButton("⛏ Копать", callback_data="dig"))
    kb.add(InlineKeyboardButton("🍆 Пофапать", callback_data="fap"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="menu"))
    return kb

def inv_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="profile"))
    return kb

def tree_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💧 Полить", callback_data="water"),
           InlineKeyboardButton("🌿 Удобрить", callback_data="fert"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="profile"))
    return kb

def fap_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🧴 Использовать", callback_data="fap_use"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="profile"))
    return kb

def top_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💰 Монеты", callback_data="tm"),
           InlineKeyboardButton("🌱 Дерево", callback_data="tt"))
    kb.add(InlineKeyboardButton("🍆 Фап", callback_data="tf"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="menu"))
    return kb

def edit(call, text, kb=None):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    get_user(m.from_user.id, m.from_user.first_name)
    bot.send_message(m.chat.id, "👋 Привет!", reply_markup=menu())

# ===== TEXT COMMANDS =====
@bot.message_handler(func=lambda m: True)
def all(m):
    u = get_user(m.from_user.id, m.from_user.first_name)
    add_msg(m.chat.id)

    text = m.text.lower()
    uid = u[0]

    if text == "профиль":
        bot.send_message(m.chat.id, "👤 Открываю профиль", reply_markup=menu())

    elif text == "копать":
        ok, left = cooldown(u[7], 1800)
        if not ok: return bot.send_message(m.chat.id, fmt(left))

        coins = rand(12, 99)
        res = rand_res()
        amt = rand(1, 3)

        add("balance", coins, uid)
        add(res, amt, uid)
        update("last_dig", int(time.time()), uid)

        bot.send_message(m.chat.id, f"+{coins} 💰")

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    u = get_user(call.from_user.id, call.from_user.first_name)
    uid = u[0]

    if call.data == "menu":
        edit(call, "Меню", menu())

    elif call.data == "profile":
        edit(call, f"""
👤 Профиль

🆔 {uid}
📛 {u[1]}
💰 {u[2]}

🌳 {tree_fmt(u[5])}
🍆 {u[6]}
""", profile_kb())

    elif call.data == "inv":
        edit(call, f"""
🎒 Инвентарь

🧴 {u[3]}
🦴 {u[4]}
""", inv_kb())

    elif call.data == "tree":
        edit(call, f"""
🌳 Дерево

📏 Рост: {tree_fmt(u[5])}
""", tree_kb())

    elif call.data == "water":
        ok, left = cooldown(u[8], 14400)
        if not ok: return edit(call, fmt(left), tree_kb())

        grow = rand(1, 10)
        add("tree", grow, uid)
        update("last_water", int(time.time()), uid)

        edit(call, f"🌱 +{grow} см", tree_kb())

    elif call.data == "fert":
        if u[4] <= 0:
            return edit(call, "❌ Нет костей", tree_kb())

        add("bone", -1, uid)
        add("tree", 15, uid)

        edit(call, "🌿 +15 см", tree_kb())

    elif call.data == "dig":
        ok, left = cooldown(u[7], 1800)
        if not ok:
            return edit(call, f"⏳ {fmt(left)}", profile_kb())

        coins = rand(12, 99)
        res = rand_res()
        amt = rand(1, 3)

        add("balance", coins, uid)
        add(res, amt, uid)
        update("last_dig", int(time.time()), uid)

        emoji = "🧴" if res == "bank" else "🦴"

        edit(call, f"""
⛏ Добыча

💰 +{coins}
{emoji} +{amt}
""", profile_kb())

    elif call.data == "fap":
        edit(call, f"""
🍆 Фап

📊 Всего: {u[6]}
🧴 В наличии: {u[3]}
""", fap_kb())

    elif call.data == "fap_use":
        if u[3] <= 0:
            return edit(call, "❌ Нет банок", fap_kb())

        add("bank", -1, uid)
        add("fap", 1, uid)

        edit(call, f"""
✅ Вы успешно пофапали

📊 Всего: {u[6]+1}
🧴 Осталось: {u[3]-1}
""", fap_kb())

    elif call.data == "bonus":
        ok, left = cooldown(u[9], 86400)
        if not ok:
            return edit(call, f"⏳ {fmt(left)}", menu())

        add("balance", 500, uid)
        update("last_bonus", int(time.time()), uid)

        edit(call, "🎁 +500", menu())

    elif call.data == "top":
        edit(call, f"💬 {get_msgs(call.message.chat.id)}", top_kb())

    elif call.data in ["tm","tt","tf"]:
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()

        key = {"tm":2,"tt":5,"tf":6}[call.data]
        data.sort(key=lambda x: x[key], reverse=True)

        text = ""
        pos = 0

        for i,u2 in enumerate(data,1):
            text += f"{i}. {u2[1]} — {u2[key]}\n"
            if u2[0]==uid: pos=i

        text += f"\n📍 Ты: {pos}"
        edit(call, text, top_kb())

print("Запущен")
bot.infinity_polling()
