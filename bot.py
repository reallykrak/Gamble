import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import time
import random
from exchange import update_exchange_rates

TOKEN = '7920964944:AAEYsvhbs5n2HaXI6QGNhBMMHKjDR-15iLo'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

MEYVELER = ['🍒', '🍋', '🍇', '🍊', '7️⃣', '💎']
TAKIMLAR = ["Real Madrid", "Galatasaray", "Barcelona", "Fenerbahçe", "Liverpool", "Chelsea", "Bayern", "Milan", "Juventus", "PSG", "Arsenal", "Napoli", "Beşiktaş", "Trabzonspor", "Inter"]

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(message):
    data = load_data()
    uid = str(message.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "money": 0,
            "bank": 0,
            "bonus_time": 0,
            "doviz": {"dolar": 0, "euro": 0, "elmas": 0}
        }
        save_data(data)
    return uid, data

@bot.message_handler(commands=['start'])
def start(message):
    uid, data = get_user(message)
    bot.reply_to(message, f"Hoş geldin {message.from_user.first_name}!\nKomutları kullanmaya başlayabilirsin.")

@bot.message_handler(commands=['bakiye'])
def bakiye(message):
    uid, data = get_user(message)
    user = data["users"][uid]
    doviz = user["doviz"]
    bot.reply_to(message,
        f"💰 Ana Bakiye: {user['money']} TL\n"
        f"🏦 Banka: {user['bank']} TL\n"
        f"💵 Dolar: {doviz['dolar']} 💵\n"
        f"💶 Euro: {doviz['euro']} 💶\n"
        f"💎 Elmas: {doviz['elmas']} 💎"
    )

@bot.message_handler(commands=['bonus'])
def bonus(message):
    uid, data = get_user(message)
    now = int(time.time())
    if now - data["users"][uid]["bonus_time"] < 86400:
        bot.reply_to(message, "⏳ Bonusunuzu 24 saatte bir alabilirsiniz.")
    else:
        data["users"][uid]["money"] += 50000
        data["users"][uid]["bonus_time"] = now
        save_data(data)
        bot.reply_to(message, "✅ 50.000 TL bonus verildi!")

@bot.message_handler(commands=['bankaparaekle'])
def banka_ekle(message):
    try:
        uid, data = get_user(message)
        miktar = int(message.text.split()[1])
        if data["users"][uid]["money"] >= miktar:
            data["users"][uid]["money"] -= miktar
            data["users"][uid]["bank"] += miktar
            save_data(data)
            bot.reply_to(message, f"✅ {miktar} TL bankaya yatırıldı.")
        else:
            bot.reply_to(message, "❌ Yetersiz bakiye.")
    except:
        bot.reply_to(message, "Kullanım: /bankaparaekle 1000")

@bot.message_handler(commands=['bankaparaçek'])
def banka_cek(message):
    try:
        uid, data = get_user(message)
        miktar = int(message.text.split()[1])
        if data["users"][uid]["bank"] >= miktar:
            data["users"][uid]["money"] += miktar
            data["users"][uid]["bank"] -= miktar
            save_data(data)
            bot.reply_to(message, f"💸 {miktar} TL bankadan çekildi.")
        else:
            bot.reply_to(message, "❌ Bankada yeterli para yok.")
    except:
        bot.reply_to(message, "Kullanım: /bankaparaçek 1000")

@bot.message_handler(commands=['slot'])
def slot(message):
    uid, data = get_user(message)
    u = data["users"][uid]
    bahis = 10000
    if u["money"] < bahis:
        bot.reply_to(message, "❌ Slot oynamak için yeterli paran yok.")
        return
    u["money"] -= bahis
    secim = [random.choice(MEYVELER) for _ in range(3)]
    msg = '🎰 ' + ' | '.join(secim) + ' 🎰\n'
    if secim[0] == secim[1] == secim[2]:
        kazanc = bahis * 5
        u["money"] += kazanc
        msg += f"🎉 Tebrikler! {kazanc} TL kazandın!"
    else:
        msg += f"☠️ Kaybettin! {bahis} TL gitti."
    save_data(data)
    bot.reply_to(message, msg)

@bot.message_handler(commands=['bahis'])
def bahis(message):
    try:
        uid, data = get_user(message)
        miktar = int(message.text.split()[1])
        if data["users"][uid]["money"] < miktar:
            return bot.reply_to(message, "❌ Yetersiz bakiye.")
        markup = InlineKeyboardMarkup()
        for t in TAKIMLAR[:4]:
            markup.add(InlineKeyboardButton(t, callback_data=f"bahis|{uid}|{miktar}|{t}"))
        bot.reply_to(message, "Hangi takıma bahis oynamak istersin?", reply_markup=markup)
    except:
        bot.reply_to(message, "Kullanım: /bahis 50000")

@bot.callback_query_handler(func=lambda call: call.data.startswith("bahis"))
def bahis_sec(call):
    _, uid, miktar, secim = call.data.split("|")
    data = load_data()
    uid = str(call.from_user.id)
    if uid != call.from_user.id.__str__():
        return bot.answer_callback_query(call.id, "Bu bahis sana ait değil.")
    data["users"][uid]["money"] -= int(miktar)
    kazanan = random.choice(TAKIMLAR[:4])
    if secim == kazanan:
        kazanc = int(miktar) * 7
        data["users"][uid]["money"] += kazanc
        msg = f"🏆 Kazanan: {kazanan}\n🎉 Tebrikler! {kazanc} TL kazandın!"
    else:
        msg = f"☠️ Kaybettin! Kazanan takım: {kazanan}"
    save_data(data)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg)

@bot.message_handler(commands=['top'])
def top(message):
    data = load_data()
    sirali = sorted(data["users"].items(), key=lambda x: x[1]["money"] + x[1]["bank"], reverse=True)[:5]
    msg = "🏆 En Zenginler:\n"
    for i, (uid, u) in enumerate(sirali, 1):
        toplam = u["money"] + u["bank"]
        msg += f"{i}. {uid}: {toplam} TL\n"
    bot.reply_to(message, msg)

# Döviz fiyatı güncelleyici (ayrı çalışan process olabilir)
import threading
def doviz_guncelle():
    while True:
        update_exchange_rates()
        time.sleep(120)
threading.Thread(target=doviz_guncelle, daemon=True).start()

bot.polling()
