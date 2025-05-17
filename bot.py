import telebot
import json
import os
import threading
import time
from exchange import update_exchange_rates

TOKEN = "7763395301:AAGPcdU8SAwZBVqXWGqw7_oCuro1XjASqkA"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(user_id):
    data = load_data()
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "balance": 100000,
            "bank": 0,
            "bonus_used": False,
            "currencies": {"dolar": 0, "euro": 0, "altin": 0, "sterlin": 0}
        }
        save_data(data)
    return data["users"][str(user_id)]

def is_admin(user_id):
    data = load_data()
    return str(user_id) in data["admins"]

# Döviz fiyatlarını her 120 saniyede güncelle
def schedule_exchange_updates():
    while True:
        update_exchange_rates()
        time.sleep(120)

@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.from_user.id)
    bot.reply_to(message, "Botu kullandığın için teşekkürler! /bakiye ile paranı kontrol edebilirsin.")

@bot.message_handler(commands=["bakiye"])
def bakiye(message):
    user = get_user(message.from_user.id)
    bot.reply_to(message, f"Güncel paran: {user['balance']} TL")

@bot.message_handler(commands=["bonus"])
def bonus(message):
    data = load_data()
    user = get_user(message.from_user.id)
    if user["bonus_used"]:
        bot.reply_to(message, "Bonus zaten alındı!")
        return
    user["balance"] += 50000
    user["bonus_used"] = True
    save_data(data)
    bot.reply_to(message, "50.000 TL bonus aldın!")

@bot.message_handler(commands=["parabasma"])
def parabasma(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komut sadece adminler içindir.")
        return
    try:
        miktar = int(message.text.split()[1])
    except:
        return bot.reply_to(message, "Kullanım: /parabasma 1000000")
    data = load_data()
    user = get_user(message.from_user.id)
    user["balance"] += miktar
    save_data(data)
    bot.reply_to(message, f"{miktar} TL başarıyla basıldı.")

@bot.message_handler(commands=["para"])
def para(message):
    parts = message.text.split()
    if len(parts) != 3 or not message.reply_to_message:
        return bot.reply_to(message, "Kullanım: /para 10000 (bir mesaja cevap olarak)")
    try:
        miktar = int(parts[1])
    except:
        return bot.reply_to(message, "Geçersiz miktar.")
    from_user = get_user(message.from_user.id)
    to_user_id = message.reply_to_message.from_user.id
    to_user = get_user(to_user_id)
    if from_user["balance"] < miktar:
        return bot.reply_to(message, "Yetersiz bakiye.")
    from_user["balance"] -= miktar
    to_user["balance"] += miktar
    data = load_data()
    save_data(data)
    bot.reply_to(message, f"{miktar} TL gönderildi.")

@bot.message_handler(commands=["id"])
def get_id(message):
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        bot.reply_to(message, f"Kullanıcı ID: {uid}")
    else:
        bot.reply_to(message, "Bir kullanıcıya cevap vererek kullan.")

@bot.message_handler(commands=["bankaparaekle"])
def bankaparaekle(message):
    try:
        miktar = int(message.text.split()[1])
    except:
        return bot.reply_to(message, "Kullanım: /bankaparaekle 1000")
    user = get_user(message.from_user.id)
    if user["balance"] < miktar:
        return bot.reply_to(message, "Yetersiz paran var.")
    user["balance"] -= miktar
    user["bank"] += miktar
    data = load_data()
    save_data(data)
    bot.reply_to(message, f"{miktar} TL bankaya eklendi.")

@bot.message_handler(commands=["bankaparaçek"])
def bankaparaçek(message):
    try:
        miktar = int(message.text.split()[1])
    except:
        return bot.reply_to(message, "Kullanım: /bankaparaçek 1000")
    user = get_user(message.from_user.id)
    if user["bank"] < miktar:
        return bot.reply_to(message, "Bankada bu kadar para yok.")
    user["bank"] -= miktar
    user["balance"] += miktar
    data = load_data()
    save_data(data)
    bot.reply_to(message, f"{miktar} TL bankadan çekildi.")

@bot.message_handler(commands=["banka"])
def banka(message):
    user = get_user(message.from_user.id)
    data = load_data()
    rates = data["exchange_rates"]
    reply = f"Bankadaki Para: {user['bank']} TL\n\nDöviz Fiyatları:\n"
    for c in rates:
        reply += f"{c.capitalize()}: {rates[c]} TL\n"
    bot.reply_to(message, reply)

# Başlat
threading.Thread(target=schedule_exchange_updates, daemon=True).start()
bot.polling()
