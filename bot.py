import json
import random
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters

# === TOKEN ve SABİT ADMIN ===
TOKEN = "7150888063:AAGZizuDzTxE4RFlBsFJLWTLkwDo061FKyU"  # <-- Buraya bot tokenını yaz
SABIT_ADMIN_ID = 8121637254         # <-- Buraya kendi Telegram ID'ni yaz

DATA_FILE = "data.json"

# === VERİ FONKSİYONLARI ===
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
            "bakiye": 1000,
            "banka": 0,
            "doviz": {},
            "bonus_time": 0
        }
        save_data(data)
    return data["users"][str(user_id)]

def set_user(user_id, user_data):
    data = load_data()
    data["users"][str(user_id)] = user_data
    save_data(data)

def is_admin(user_id):
    data = load_data()
    return str(user_id) == str(SABIT_ADMIN_ID) or str(user_id) in data["admins"]
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    get_user(user.id)
    update.message.reply_text(f"👋 Merhaba {user.first_name}! Kumar botuna hoş geldin!\n💸 Başlangıç bakiyen: 1000₺")

def bakiye(update: Update, context: CallbackContext):
    user = update.effective_user
    u = get_user(user.id)
    bakiye = u["bakiye"]
    banka = u["banka"]
    doviz = u.get("doviz", {})
    doviz_text = "\n".join([f"💱 {k.upper()}: {v}" for k, v in doviz.items()]) if doviz else "💱 Dövizin yok."
    update.message.reply_text(f"💰 Bakiye: {bakiye}₺\n🏦 Banka: {banka}₺\n{doviz_text}")

def bonus(update: Update, context: CallbackContext):
    user = update.effective_user
    u = get_user(user.id)
    now = time.time()
    if now - u["bonus_time"] >= 86400:
        bonus = random.randint(500, 1000)
        u["bakiye"] += bonus
        u["bonus_time"] = now
        set_user(user.id, u)
        update.message.reply_text(f"🎁 Günlük bonus: {bonus}₺! Keyfini çıkar!")
    else:
        kalan = int(86400 - (now - u["bonus_time"]))
        update.message.reply_text(f"⏳ Bonus için bekle: {kalan // 3600} saat {kalan % 3600 // 60} dk")

def bankaparaekle(update: Update, context: CallbackContext):
    user = update.effective_user
    try:
        miktar = int(context.args[0])
        u = get_user(user.id)
        if u["bakiye"] >= miktar:
            u["bakiye"] -= miktar
            u["banka"] += miktar
            set_user(user.id, u)
            update.message.reply_text(f"🏦 {miktar}₺ bankaya yatırıldı!")
        else:
            update.message.reply_text("❌ Yetersiz bakiye!")
    except:
        update.message.reply_text("🔢 Kullanım: /bankaparaekle miktar")

def bankaparaçek(update: Update, context: CallbackContext):
    user = update.effective_user
    try:
        miktar = int(context.args[0])
        u = get_user(user.id)
        if u["banka"] >= miktar:
            u["banka"] -= miktar
            u["bakiye"] += miktar
            set_user(user.id, u)
            update.message.reply_text(f"💳 {miktar}₺ bankadan çekildi!")
        else:
            update.message.reply_text("❌ Bankada bu kadar yok!")
    except:
        update.message.reply_text("🔢 Kullanım: /bankaparaçek miktar")

def dovizal(update: Update, context: CallbackContext):
    try:
        tur = context.args[0]
        miktar = int(context.args[1])
        data = load_data()
        fiyat = data["exchange_rates"][tur]
        u = get_user(update.effective_user.id)
        toplam = fiyat * miktar
        if u["bakiye"] >= toplam:
            u["bakiye"] -= toplam
            u["doviz"][tur] = u["doviz"].get(tur, 0) + miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"💱 {miktar} {tur.upper()} alındı! Toplam: {toplam}₺")
        else:
            update.message.reply_text("❌ Bakiye yetersiz!")
    except:
        update.message.reply_text("🔢 Kullanım: /dövizal tür miktar")

def dovizsat(update: Update, context: CallbackContext):
    try:
        tur = context.args[0]
        miktar = int(context.args[1])
        data = load_data()
        fiyat = data["exchange_rates"][tur]
        u = get_user(update.effective_user.id)
        if u["doviz"].get(tur, 0) >= miktar:
            u["doviz"][tur] -= miktar
            u["bakiye"] += fiyat * miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"💸 {miktar} {tur.upper()} satıldı! Kazanç: {fiyat * miktar}₺")
        else:
            update.message.reply_text("❌ Elinde bu kadar yok!")
    except:
        update.message.reply_text("🔢 Kullanım: /dövizsat tür miktar")

def slot(update: Update, context: CallbackContext):
    user = update.effective_user
    try:
        miktar = int(context.args[0])
        u = get_user(user.id)
        if u["bakiye"] < miktar:
            return update.message.reply_text("💀 Yetersiz bakiye!")
        u["bakiye"] -= miktar
        emojis = ["🍒", "🍍", "🍇", "🍉", "💀", "7️⃣"]
        sonuc = [random.choice(emojis) for _ in range(3)]
        if sonuc.count(sonuc[0]) == 3:
            kazanc = miktar * 5
            u["bakiye"] += kazanc
            text = f"{' '.join(sonuc)}\n🎉 TEBRİKLER! {kazanc}₺ kazandın!"
        else:
            text = f"{' '.join(sonuc)}\n💀 Kaybettin! Tekrar dene!"
        set_user(user.id, u)
        update.message.reply_text(text)
    except:
        update.message.reply_text("🔢 Kullanım: /slot miktar")

def risk(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            return update.message.reply_text("💀 Yetersiz bakiye!")
        u["bakiye"] -= miktar
        if random.random() < 0.5:
            u["bakiye"] += miktar * 2
            text = f"🔥 KAZANDIN! {miktar*2}₺ oldu!"
        else:
            text = "💀 Kaybettin! Şansını zorladın!"
        set_user(update.effective_user.id, u)
        update.message.reply_text(text)
    except:
        update.message.reply_text("🔢 Kullanım: /risk miktar")

def bahis(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            return update.message.reply_text("❌ Bakiye yetersiz!")
        takimlar = ["Real Madrid", "Fenerbahçe", "Beşiktaş", "Galatasaray", "Juventus", "Barcelona", "Manchester City",
                    "Bayern Munchen", "Manchester United", "Dortmund", "Milan", "Arsenal", "İnter", "Liverpool", "Atletico Madrid"]
        secilenler = random.sample(takimlar, 3)
        kazanan = random.choice(secilenler)

        buttons = [
            [InlineKeyboardButton(f"⚽ {takim}", callback_data=f"bahis|{takim}|{miktar}|{kazanan}")]
            for takim in secilenler
        ]
        markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(f"⚽ Takımını seç:\nBahis: {miktar}₺", reply_markup=markup)
    except:
        update.message.reply_text("🔢 Kullanım: /bahis miktar")

def bahis_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    _, secilen, miktar, kazanan = query.data.split("|")
    miktar = int(miktar)
    u = get_user(user_id)
    u["bakiye"] -= miktar
    if secilen == kazanan:
        kazanc = miktar * 4
        u["bakiye"] += kazanc
        text = f"🏆 Doğru tahmin: {kazanan}! Kazandın +{kazanc}₺"
    else:
        text = f"❌ Kazanan: {kazanan}. Kaybettin!"
    set_user(user_id, u)
    query.edit_message_text(text)

def paragönder(update: Update, context: CallbackContext):
    try:
        hedef_id = int(context.args[0])
        miktar = int(context.args[1])
        gonderen = get_user(update.effective_user.id)
        if gonderen["bakiye"] >= miktar:
            gonderen["bakiye"] -= miktar
            alici = get_user(hedef_id)
            alici["bakiye"] += miktar
            set_user(update.effective_user.id, gonderen)
            set_user(hedef_id, alici)
            update.message.reply_text(f"✅ {miktar}₺ gönderildi!")
        else:
            update.message.reply_text("❌ Bakiye yetersiz!")
    except:
        update.message.reply_text("🔢 Kullanım: /paragönder id miktar")

def parabasma(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return update.message.reply_text("🚫 Bu komut sadece adminlere özel!")
    try:
        hedef_id = int(context.args[0])
        miktar = int(context.args[1])
        u = get_user(hedef_id)
        u["bakiye"] += miktar
        set_user(hedef_id, u)
        update.message.reply_text(f"💸 {miktar}₺ başarıyla basıldı ve {hedef_id} ID'li kullanıcıya eklendi!")
    except:
        update.message.reply_text("🔢 Kullanım: /parabasma id miktar")

def admin(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return update.message.reply_text("🚫 Bu komut sadece adminlere özel!")
    try:
        yeni_admin = str(context.args[0])
        data = load_data()
        if yeni_admin not in data["admins"]:
            data["admins"].append(yeni_admin)
            save_data(data)
            update.message.reply_text(f"👑 {yeni_admin} artık admin!")
        else:
            update.message.reply_text("⚠️ Zaten admin!")
    except:
        update.message.reply_text("🔢 Kullanım: /admin kullanıcı_id")

def id(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        hedef = update.message.reply_to_message.from_user
        update.message.reply_text(f"🆔 {hedef.first_name}: {hedef.id}")
    elif context.args:
        update.message.reply_text("❗ Etiket yerine yanıtla özelliğini kullan!")
    else:
        update.message.reply_text(f"🆔 Senin ID: {update.effective_user.id}")

def top(update: Update, context: CallbackContext):
    data = load_data()
    sirali = sorted(data["users"].items(), key=lambda x: x[1]["bakiye"] + x[1]["banka"], reverse=True)[:10]
    text = "🏆 En Zenginler Listesi:\n\n"
    for i, (uid, veriler) in enumerate(sirali, 1):
        toplam = veriler["bakiye"] + veriler["banka"]
        text += f"{i}. 👤 ID:{uid} - {toplam}₺\n"
    update.message.reply_text(text)

def komutlar(update: Update, context: CallbackContext):
    text = (
        "📜 *Komutlar Listesi*\n"
        "🟢 /start - Botu başlat\n"
        "💸 /bakiye - Bakiyeni göster\n"
        "🎁 /bonus - Günlük bonus al\n"
        "🏦 /bankaparaekle x - Bankaya Para Yatır\n"
        "🏦 /banka - Dövizleir Takip et\n"
        "💳 /bankaparaçek x - Bankadan Para Çek\n"
        "💱 /dövizal tür miktar - Döviz al\n"
        "💵 /dövizsat tür miktar - Döviz sat\n"
        "🎰 /slot x - Slot oynar (%30 X5)\n"
        "☠️ /risk x - %50 kazanma riski\n"
        "⚽ /bahis x - Takıma bahis yap\n"
        "🧾 /paragönder id x - Para gönder\n"
        "🧾 /parabasma id x - Admin para basar\n"
        "👑 /admin id - Admin ekler\n"
        "🆔 /id - Kullanıcı ID'sini göster\n"
        "🏆 /top - En zenginleri göster"
    )
    update.message.reply_text(text, parse_mode="Markdown")

def main():
    from telegram.ext import ApplicationBuilder

app = ApplicationBuilder().token("BOT_TOKEN").build()
app.add_handler(...)
app.run_polling()

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("bakiye", bakiye))
    dp.add_handler(CommandHandler("bonus", bonus))
    dp.add_handler(CommandHandler("bankaparaekle", bankaparaekle))
    dp.add_handler(CommandHandler("bankaparaçek", bankaparaçek))
    dp.add_handler(CommandHandler("dövizal", dovizal))
    dp.add_handler(CommandHandler("dövizsat", dovizsat))
    dp.add_handler(CommandHandler("slot", slot))
    dp.add_handler(CommandHandler("risk", risk))
    dp.add_handler(CommandHandler("bahis", bahis))
    dp.add_handler(CallbackQueryHandler(bahis_callback, pattern="^bahis\\|"))
    dp.add_handler(CommandHandler("paragönder", paragönder))
    dp.add_handler(CommandHandler("parabasma", parabasma))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("id", id))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(CommandHandler("komutlar", komutlar))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
