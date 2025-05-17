import telebot
from telebot import types
import json
import os
import time
import random
import threading
from exchange import update_exchange_rates

BOT_TOKEN = "7150888063:AAGZizuDzTxE4RFlBsFJLWTLkwDo061FKyU"
KENDI_ID = 8121637254  # Admin ID'n

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

# === Veri Fonksiyonları ===
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "users": {},
                "admins": [],
                "exchange_rates": {
                    "dolar": 100,
                    "euro": 100,
                    "sterlin": 100,
                    "elmas": 100
                }
            }, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def register_user(user_id):
    data = load_data()
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "bakiye": 100000,
            "banka": 0,
            "doviz": {"dolar": 0, "euro": 0, "sterlin": 0, "elmas": 0},
            "bonus_time": 0
        }
        save_data(data)

# === Döviz Güncelleme ===
def update_loop():
    while True:
        update_exchange_rates()
        time.sleep(120)

threading.Thread(target=update_loop, daemon=True).start()

# === Komutlar ===

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id)
    bot.send_message(message.chat.id, "✅ Hoş geldin! /komutlar komutunu kullanabilirsin.")

@bot.message_handler(commands=['bakiye'])
def bakiye(message):
    register_user(message.from_user.id)
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    rates = data["exchange_rates"]
    text = f"""💸 <b>Bakiye:</b> {user["bakiye"]}₺
🏦 <b>Banka:</b> {user["banka"]}₺
💱 <b>Döviz:</b>
  💵 Dolar: {user['doviz']['dolar']} (${rates['dolar']}₺)
  💶 Euro: {user['doviz']['euro']} (€{rates['euro']}₺)
  💷 Sterlin: {user['doviz']['sterlin']} (£{rates['sterlin']}₺)
  💎 Elmas: {user['doviz']['elmas']} ({rates['elmas']}₺)
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['bonus'])
def bonus(message):
    register_user(message.from_user.id)
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    now = time.time()
    if now - user["bonus_time"] >= 86400:
        user["bonus_time"] = now
        user["bakiye"] += 50000
        bot.send_message(message.chat.id, "🎁 50.000₺ bonus aldın!")
    else:
        kalan = int((86400 - (now - user["bonus_time"])) / 3600)
        bot.send_message(message.chat.id, f"⏳ Bonus için {kalan} saat bekle.")
    save_data(data)

@bot.message_handler(commands=['bankaparaekle'])
def banka_ekle(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] >= miktar:
        user["bakiye"] -= miktar
        user["banka"] += miktar
        bot.send_message(message.chat.id, f"🏦 {miktar}₺ bankaya yatırıldı.")
    else:
        bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")
    save_data(data)

@bot.message_handler(commands=['bankaparaçek'])
def banka_cek(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["banka"] >= miktar:
        user["banka"] -= miktar
        user["bakiye"] += miktar
        bot.send_message(message.chat.id, f"💵 {miktar}₺ bankadan çekildi.")
    else:
        bot.send_message(message.chat.id, "❌ Banka bakiyesi yetersiz.")
    save_data(data)

@bot.message_handler(commands=['dövizal'])
def dovizal(message):
    args = message.text.split()
    if len(args) != 3: return
    tur, miktar = args[1].lower(), int(args[2])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if tur not in data["exchange_rates"]: return
    fiyat = data["exchange_rates"][tur]
    toplam = fiyat * miktar
    if user["banka"] >= toplam:
        user["banka"] -= toplam
        user["doviz"][tur] += miktar
        bot.send_message(message.chat.id, f"💱 {miktar} {tur.upper()} alındı!")
    else:
        bot.send_message(message.chat.id, "❌ Yetersiz banka bakiyesi.")
    save_data(data)

@bot.message_handler(commands=['dövizsat'])
def dovizsat(message):
    args = message.text.split()
    if len(args) != 3: return
    tur, miktar = args[1].lower(), int(args[2])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["doviz"][tur] < miktar:
        return bot.send_message(message.chat.id, "❌ Elinizde yeterli döviz yok.")
    fiyat = data["exchange_rates"][tur]
    gelir = fiyat * miktar
    user["doviz"][tur] -= miktar
    user["banka"] += gelir
    bot.send_message(message.chat.id, f"💱 {miktar} {tur.upper()} satıldı!")
    save_data(data)

@bot.message_handler(commands=['slot'])
def slot(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    emojis = ["🍒", "🍋", "🍉", "7️⃣", "⭐", "🍇"]
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] < miktar:
        return bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")
    kazanma = random.randint(1, 100)
    slotlar = [random.choice(emojis) for _ in range(3)]
    if kazanma <= 30:
        user["bakiye"] += miktar * 5
        sonuc = "🎉 Kazandın! X5"
    else:
        user["bakiye"] -= miktar
        sonuc = "☠️ Kaybettin!"
    save_data(data)
    bot.send_message(message.chat.id, f"{slotlar[0]}|{slotlar[1]}|{slotlar[2]}\n{sonuc}\nYeni bakiye: {user['bakiye']}₺")

@bot.message_handler(commands=['risk'])
def risk(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] < miktar:
        return bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")
    if random.randint(1, 100) <= 50:
        user["bakiye"] += miktar
        sonuc = "✅ Kazandın!"
    else:
        user["bakiye"] -= miktar
        sonuc = "❌ Kaybettin!"
    save_data(data)
    bot.send_message(message.chat.id, f"{sonuc} Yeni bakiye: {user['bakiye']}₺")

@bot.message_handler(commands=['bahis'])
def bahis(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    takimlar = ["⚽ Galatasaray", "🔵 Fenerbahçe", "🟢 Trabzonspor"]
    secilen = random.choice(takimlar)
    kazanan = random.choice(takimlar)
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] < miktar:
        return bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")
    user["bakiye"] -= miktar
    if secilen == kazanan:
        kazanc = miktar * 2
        user["bakiye"] += kazanc
        sonuc = f"🏆 Kazandın! {kazanc}₺"
    else:
        sonuc = f"☠️ Kaybettin! Kazanan: {kazanan}"
    save_data(data)
    bot.send_message(message.chat.id, f"Bahisin: {secilen}\n{sonuc}\nYeni bakiye: {user['bakiye']}₺")

@bot.message_handler(commands=['parabasma'])
def parabasma(message):
    data = load_data()
    if str(message.from_user.id) not in data["admins"]: return
    args = message.text.split()
    if len(args) < 3: return
    hedef, miktar = args[1], int(args[2])
    if hedef in data["users"]:
        data["users"][hedef]["bakiye"] += miktar
        bot.send_message(message.chat.id, f"🤑 {hedef} kişisine {miktar}₺ basıldı!")
        save_data(data)

@bot.message_handler(commands=['id'])
def idkomut(message):
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        bot.send_message(message.chat.id, f"🆔 Kullanıcı ID: <code>{uid}</code>")
    else:
        bot.send_message(message.chat.id, f"🆔 Senin ID: <code>{message.from_user.id}</code>")

@bot.message_handler(commands=['komutlar'])
def komutlar(message):
    bot.send_message(message.chat.id, """
📜 <b>Komutlar Listesi</b>
🟢 /start - Botu başlat
💸 /bakiye - Bakiyeni göster
🎁 /bonus - Günlük bonus al
🏦 /bankaparaekle x - Bankaya para yatır
💳 /bankaparaçek x - Bankadan para çek
💱 /dövizal tür miktar - Döviz al
💵 /dövizsat tür miktar - Döviz sat
🎰 /slot x - Slot oynar (%30 X5)
☠️ /risk x - %50 kazanma riski
⚽ /bahis x - Takıma bahis yap
🧾 /paragönder id x - Para gönder
🧾 /parabasma id x - Admin para basar
👑 /admin id - Admin ekler
🆔 /id - Kullanıcı ID'sini göster
🏆 /top - En zenginleri göster
""")

print("BOT ÇALIŞIYOR...")
bot.infinity_polling()
