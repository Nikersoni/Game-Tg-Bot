import telebot
from telebot.types import *
import sqlite3
import time
import random
import os

TOKEN = os.getenv("TOKEN") or "8640949306:AAG5n2Af4LHtj8qe5pT1eLZb4oY1pe_NT3c"
ADMINS = [8200958216]

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
CREATE TABLE IF NOT EXISTS emojis (
    name TEXT PRIMARY KEY,
    value TEXT,
    is_custom INTEGER
)
""")

conn.commit()

# ===== ЭМОДЗИ =====
default_emojis = {
    "profile":"👤","money":"💰","tree":"🌳","fap":"🍆",
    "inv":"🎒","dig":"⛏","bonus":"🎁","top":"🏆",
    "water":"💧","fert":"🌿","back":"⬅️"
}

for k,v in default_emojis.items():
    cursor.execute("INSERT OR IGNORE INTO emojis VALUES (?, ?, 0)", (k, v))
conn.commit()

# ===== КЭШ =====
emoji_cache = {}

def load_emojis():
    global emoji_cache
    cursor.execute("SELECT name, value, is_custom FROM emojis")
    emoji_cache = {r[0]: (r[1], r[2]) for r in cursor.fetchall()}

load_emojis()

def get_emoji(name):
    return emoji_cache.get(name, ("❓", 0))

# ===== UTILS =====
def get_user(uid, name):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cursor.fetchone()
    if not u:
        cursor.execute("INSERT INTO users VALUES (?, ?, 500, 5, 5, 0, 0, 0, 0, 0)", (uid, name))
        conn.commit()
        return get_user(uid, name)
    return u

def add(field, val, uid):
    cursor.execute(f"UPDATE users SET {field}={field}+? WHERE user_id=?", (val, uid))
    conn.commit()

def update(field, val, uid):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (val, uid))
    conn.commit()

def cooldown(last, cd):
    now = int(time.time())
    return (True,0) if now-last>=cd else (False, cd-(now-last))

def fmt(sec):
    return f"{sec//3600}ч {(sec%3600)//60}м"

def tree_fmt(cm):
    return f"{cm//100} м {cm%100} см" if cm>=100 else f"{cm} см"

def rand(a,b): return random.randint(a,b)
def rand_res(): return random.choice(["bank","bone"])

# ===== PREMIUM TEXT =====
def build_text(text):
    entities=[]
    result=""
    i=0

    while i<len(text):
        if text[i]=="{":
            end=text.find("}",i)
            if end!=-1:
                key=text[i+1:end]
                val,is_custom=get_emoji(key)

                if is_custom:
                    offset=len(result)
                    result+="▫️"
                    entities.append(MessageEntity(
                        type="custom_emoji",
                        offset=offset,
                        length=1,
                        custom_emoji_id=val
                    ))
                else:
                    result+=val

                i=end+1
                continue

        result+=text[i]
        i+=1

    return result,entities

def send(chat_id,text,kb=None,edit=None):
    text,entities=build_text(text)
    try:
        if edit:
            bot.edit_message_text(text,chat_id,edit,reply_markup=kb,entities=entities)
        else:
            bot.send_message(chat_id,text,reply_markup=kb,entities=entities)
    except:
        pass

# ===== КНОПКИ INLINE =====
def menu():
    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Профиль",callback_data="profile"),
           InlineKeyboardButton("Инвентарь",callback_data="inv"))
    kb.add(InlineKeyboardButton("Бонус",callback_data="bonus"),
           InlineKeyboardButton("Топ",callback_data="top"))
    return kb

def profile_kb():
    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Инвентарь",callback_data="inv"))
    kb.add(InlineKeyboardButton("Дерево",callback_data="tree"))
    kb.add(InlineKeyboardButton("Копать",callback_data="dig"))
    kb.add(InlineKeyboardButton("Фап",callback_data="fap"))
    kb.add(InlineKeyboardButton("Назад",callback_data="menu"))
    return kb

def tree_kb():
    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Полить",callback_data="water"),
           InlineKeyboardButton("Удобрить",callback_data="fert"))
    kb.add(InlineKeyboardButton("Назад",callback_data="profile"))
    return kb

def fap_kb():
    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Использовать",callback_data="fap_use"))
    kb.add(InlineKeyboardButton("Назад",callback_data="profile"))
    return kb

# ===== КЛАВИАТУРА НИЖНЯЯ =====
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👤 Профиль","🎒 Инвентарь")
    kb.row("⛏ Копать","🌳 Дерево")
    kb.row("🎁 Бонус","🏆 Топ")
    return kb

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    get_user(m.from_user.id, m.from_user.first_name)
    send(m.chat.id,"👋 Привет")
    bot.send_message(m.chat.id,"📱 Панель управления",reply_markup=main_kb())

# ===== АДМИН =====
waiting={}

@bot.message_handler(commands=['admin'])
def admin(m):
    if m.from_user.id not in ADMINS: return
    kb=InlineKeyboardMarkup()
    for k in default_emojis:
        kb.add(InlineKeyboardButton(k,callback_data=f"edit_{k}"))
    bot.send_message(m.chat.id,"🎨 Эмодзи",reply_markup=kb)

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    u=get_user(call.from_user.id,call.from_user.first_name)
    uid=u[0]

    if call.data=="profile":
        send(call.message.chat.id,f"""
{{profile}} Профиль

{{money}} {u[2]}
{{tree}} {tree_fmt(u[5])}
{{fap}} {u[6]}
""",profile_kb(),call.message.message_id)

    elif call.data=="tree":
        send(call.message.chat.id,f"""
{{tree}} Дерево

Рост: {tree_fmt(u[5])}
""",tree_kb(),call.message.message_id)

    elif call.data=="dig":
        ok,left=cooldown(u[7],1800)
        if not ok:
            return send(call.message.chat.id,f"⏳ {fmt(left)}",profile_kb(),call.message.message_id)

        coins=rand(12,99)
        add("balance",coins,uid)
        update("last_dig",int(time.time()),uid)

        send(call.message.chat.id,f"{coins} монет",profile_kb(),call.message.message_id)

    elif call.data=="fap":
        send(call.message.chat.id,f"""
{{fap}} Фап

Всего: {u[6]}
Банки: {u[3]}
""",fap_kb(),call.message.message_id)

    elif call.data=="fap_use":
        if u[3]<=0:
            return send(call.message.chat.id,"❌ Нет банок",fap_kb(),call.message.message_id)

        add("bank",-1,uid)
        add("fap",1,uid)

        send(call.message.chat.id,f"✅ +1\nВсего: {u[6]+1}",fap_kb(),call.message.message_id)

    elif call.data.startswith("edit_"):
        if call.from_user.id not in ADMINS: return
        key=call.data.split("_")[1]
        waiting[call.from_user.id]=key
        bot.send_message(call.message.chat.id,f"Отправь эмодзи для {key}")

# ===== ТЕКСТ КНОПКИ =====
@bot.message_handler(func=lambda m: True)
def text_handler(m):
    if m.from_user.id in waiting:
        key=waiting[m.from_user.id]

        if m.entities:
            for e in m.entities:
                if e.type=="custom_emoji":
                    cursor.execute("UPDATE emojis SET value=?,is_custom=1 WHERE name=?",(e.custom_emoji_id,key))
                    conn.commit()
                    load_emojis()
                    del waiting[m.from_user.id]
                    return bot.send_message(m.chat.id,"✅ Premium обновлен")

        cursor.execute("UPDATE emojis SET value=?,is_custom=0 WHERE name=?",(m.text,key))
        conn.commit()
        load_emojis()
        del waiting[m.from_user.id]
        return bot.send_message(m.chat.id,"✅ Обновлено")

    text=m.text.lower()
    u=get_user(m.from_user.id,m.from_user.first_name)

    if "профиль" in text:
        return send(m.chat.id,"{profile} Профиль",profile_kb())

    elif "дерево" in text:
        return send(m.chat.id,f"{tree_fmt(u[5])}",tree_kb())

    elif "копать" in text:
        ok,left=cooldown(u[7],1800)
        if not ok:
            return bot.send_message(m.chat.id,fmt(left))

        coins=rand(12,99)
        add("balance",coins,u[0])
        update("last_dig",int(time.time()),u[0])

        return bot.send_message(m.chat.id,f"⛏ +{coins}")

    elif "бонус" in text:
        ok,left=cooldown(u[9],86400)
        if not ok:
            return bot.send_message(m.chat.id,fmt(left))

        add("balance",500,u[0])
        update("last_bonus",int(time.time()),u[0])

        return bot.send_message(m.chat.id,"🎁 +500")

    elif "топ" in text:
        return bot.send_message(m.chat.id,"🏆 В разработке")

print("Запущен")
bot.infinity_polling()
