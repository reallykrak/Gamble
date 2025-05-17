import telebot
from telebot import types
import json
import os
import time
import random
import threading
from exchange import update_exchange_rates
KENDI_ID = 8121637254 

bot = telebot.TeleBot("7920964944:AAEYsvhbs5n2HaXI6QGNhBMMHKjDR-15iLo", parse_mode="HTML")
DATA_FILE = "data.json"
KANALLAR = [
    "https://t.me/+o8QkbLlqKGk1NDlk",
    "https://t.me/+X5UmnY0xK_wzN2Nk"
]

# === Veri İşlemleri ===
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
            "doviz": {
                "dolar": 0,
                "euro": 0,
                "sterlin": 0,
                "elmas": 0
            },
            "bonus_time": 0
        }
        save_data(data)

def check_subscription(user_id):
    return False  # İstersen gerçek API ile kontrol eklenebilir

def get_balance_text(user):
    return f"""
💸 <b>Bakiye:</b> {user["bakiye"]}₺
🏦 <b>Banka:</b> {user["banka"]}₺
💱 <b>Döviz:</b>
  💵 Dolar: {user['doviz']['dolar']}$
  💶 Euro: {user['doviz']['euro']}€
  💷 Sterlin: {user['doviz']['sterlin']}£
  💎 Elmas: {user['doviz']['elmas']}💎
"""

# === Zamanlayıcı ===
def update_loop():
    while True:
        update_exchange_rates()
        time.sleep(120)

threading.Thread(target=update_loop, daemon=True).start()

# === Komutlar ===

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != "private":
        return
    if not check_subscription(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🟢 KATILDIM", callback_data="katildim"))
        text = "⛔ Bu Botu Kullanabilmek İçin Aşağıdaki Kanallara Katılmanız Gerekiyor\n\n"
        for kanal in KANALLAR:
            text += f"➤ {kanal}\n"
        text += "\n✅ Katıldıktan Sonra '🟢 Katıldım' Butonuna Tıklayın"
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    register_user(message.from_user.id)
    bot.send_message(message.chat.id, "✅ Hoş geldin! /bakiye ile başlayabilirsin.")

@bot.callback_query_handler(func=lambda call: call.data == "katildim")
def katildim(call):
    if check_subscription(call.from_user.id):
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Kanallara katılmadınız.", show_alert=True)

@bot.message_handler(commands=['bakiye'])
def bakiye(message):
    register_user(message.from_user.id)
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    bot.send_message(message.chat.id, get_balance_text(user))

@bot.message_handler(commands=['bonus'])
def bonus(message):
    register_user(message.from_user.id)
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    now = time.time()
    if now - user["bonus_time"] >= 86400:
        user["bakiye"] += 50000
        user["bonus_time"] = now
        save_data(data)
        bot.send_message(message.chat.id, "🎁 50.000₺ bonus aldınız!")
    else:
        kalan = int((86400 - (now - user["bonus_time"])) / 3600)
        bot.send_message(message.chat.id, f"⏳ Bonus için {kalan} saat beklemelisin.")

@bot.message_handler(commands=['bankaparaekle'])
def bankaparaekle(message):
    register_user(message.from_user.id)
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] >= miktar:
        user["bakiye"] -= miktar
        user["banka"] += miktar
        save_data(data)
        bot.send_message(message.chat.id, f"🏦 {miktar}₺ bankaya eklendi!")
    else:
        bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")

@bot.message_handler(commands=['bankaparaçek'])
def bankaparaçek(message):
    register_user(message.from_user.id)
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["banka"] >= miktar:
        user["banka"] -= miktar
        user["bakiye"] += miktar
        save_data(data)
        bot.send_message(message.chat.id, f"💸 {miktar}₺ banka'dan çekildi!")
    else:
        bot.send_message(message.chat.id, "❌ Banka bakiyesi yetersiz.")

@bot.message_handler(commands=['dövizal'])
def dovizal(message):
    args = message.text.split()
    if len(args) != 3: return
    register_user(message.from_user.id)
    tur, miktar = args[1].lower(), int(args[2])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    fiyat = data["exchange_rates"].get(tur)
    if not fiyat:
        bot.send_message(message.chat.id, "❌ Geçersiz döviz türü.")
        return
    toplam = fiyat * miktar
    if user["banka"] >= toplam:
        user["banka"] -= toplam
        user["doviz"][tur] += miktar
        save_data(data)
        bot.send_message(message.chat.id, f"✅ {miktar} {tur.upper()} alındı!")
    else:
        bot.send_message(message.chat.id, "❌ Banka bakiyesi yetersiz.")

@bot.message_handler(commands=['dövizsat'])
def dovizsat(message):
    args = message.text.split()
    if len(args) != 3: return
    register_user(message.from_user.id)
    tur, miktar = args[1].lower(), int(args[2])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    fiyat = data["exchange_rates"].get(tur)
    if not fiyat:
        bot.send_message(message.chat.id, "❌ Geçersiz döviz türü.")
        return
    if user["doviz"][tur] >= miktar:
        user["doviz"][tur] -= miktar
        user["banka"] += fiyat * miktar
        save_data(data)
        bot.send_message(message.chat.id, f"💱 {miktar} {tur.upper()} satıldı!")
    else:
        bot.send_message(message.chat.id, "❌ Elinizde yeterli döviz yok.")

@bot.message_handler(commands=['risk'])
def risk(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] < miktar:
        bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")
        return
    if random.randint(1, 100) <= 50:
        user["bakiye"] += miktar
        sonuc = "✅ Kazandın!"
    else:
        user["bakiye"] -= miktar
        sonuc = "☠️ Kaybettin!"
    save_data(data)
    bot.send_message(message.chat.id, f"{sonuc} Yeni bakiye: {user['bakiye']}₺")

@bot.message_handler(commands=['slot'])
def slot(message):
    args = message.text.split()
    if len(args) < 2: return
    miktar = int(args[1])
    emojis = ["🍒", "🍋", "🍉", "7️⃣", "⭐", "🍇"]
    data = load_data()
    user = data["users"][str(message.from_user.id)]
    if user["bakiye"] < miktar:
        bot.send_message(message.chat.id, "❌ Yetersiz bakiye.")
        return
    r = [random.choice(emojis) for _ in range(3)]
    if len(set(r)) == 1:
        kazanc = miktar * 7
        user["bakiye"] += kazanc
        sonuc = "🎉 JACKPOT!"
    else:
        user["bakiye"] -= miktar
        sonuc = "☠️ Kaybettin!"
    save_data(data)
    bot.send_message(message.chat.id, f"{''.join(r)}\n{sonuc} Yeni bakiye: {user['bakiye']}₺")

@bot.message_handler(commands=['top'])
def top(message):
    data = load_data()
    sirala = sorted(data["users"].items(), key=lambda x: x[1]["bakiye"] + x[1]["banka"], reverse=True)
    text = "🏆 En Zenginler:\n"
    for i, (uid, info) in enumerate(sirala[:10], 1):
        text += f"{i}. <code>{uid}</code> - {info['bakiye'] + info['banka']}₺\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['paragönder'])
def paragonder(message):
    args = message.text.split()
    if len(args) < 3: return
    hedef, miktar = args[1], int(args[2])
    data = load_data()
    if hedef not in data["users"]: return
    gonderen = data["users"][str(message.from_user.id)]
    if gonderen["bakiye"] < miktar: return
    gonderen["bakiye"] -= miktar
    data["users"][hedef]["bakiye"] += miktar
    save_data(data)
    bot.send_message(message.chat.id, f"✅ {hedef} kişisine {miktar}₺ gönderildi!")

@bot.message_handler(commands=['id'])
def idkomut(message):
    if message.reply_to_message:
        bot.send_message(message.chat.id, f"🆔 Kullanıcı ID: <code>{message.reply_to_message.from_user.id}</code>")
    else:
        bot.send_message(message.chat.id, "❌ Birine cevap vererek kullan.")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != KENDI_ID: return
    args = message.text.split()
    if len(args) < 2: return
    data = load_data()
    data["admins"].append(args[1])
    save_data(data)
    bot.send_message(message.chat.id, "👑 Admin eklendi!")

@bot.message_handler(commands=['parabasma'])
def parabasma(message):
    data = load_data()
    if str(message.from_user.id) not in data["admins"]: return
    args = message.text.split()
    if len(args) < 3: return
    hedef, miktar = args[1], int(args[2])
    data["users"][hedef]["bakiye"] += miktar
    save_data(data)
    bot.send_message(message.chat.id, f"🤑 {hedef} kişisine {miktar}₺ basıldı!")

@bot.message_handler(commands=['komutlar'])
def komutlar(message):
    bot.send_message(message.chat.id, """
📜 <b>Komutlar Listesi</b>

/start • Botu başlat
/bakiye • Bakiye ve dövizleri göster
/bonus • 24 saatte 1 bonus
/banka • Banka bilgileri
/bankaparaekle x • Bankaya para yatır
/bankaparaçek x • Bankadan para çek
/dövizal tür miktar • Döviz al (dolar, euro, sterlin, elmas)
/dövizsat tür miktar • Döviz sat
/kazı • Kazı kazan
/slot x • Slot oynar
/risk x • %50 X2 kazan
/bahis x • Takıma bahis
/top • En zenginler
/id • Kullanıcı ID'si
/paragönder id x • Para gönder
/parabasma id x • Admin para basar
/admin id • Admin ekler
""")

print("BOT BAŞLADI.")
bot.infinity_polling()
