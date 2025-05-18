import json
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# === TOKEN ve SABİT ADMIN ===
TOKEN = "7150888063:AAGZizuDzTxE4RFlBsFJLWTLkwDo061FKyU"
SABIT_ADMIN_ID = 8121637254
DATA_FILE = "data.json"

# === VERİ İŞLEME ===
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
            "doviz": {"dolar": 0, "euro": 0, "sterlin": 0, "elmas": 0},
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
    return str(user_id) == str(SABIT_ADMIN_ID) or str(user_id) in data.get("admins", [])

# === KOMUTLAR ===
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    get_user(user.id)
    update.message.reply_text(f"👋 Merhaba {user.first_name}! Kumar botuna hoş geldin!\n💸 Başlangıç bakiyen: 1000₺")

def bakiye(update: Update, context: CallbackContext):
    u = get_user(update.effective_user.id)
    doviz = "\n".join([
        f"💵 Dolar: {u['doviz']['dolar']}",
        f"💶 Euro: {u['doviz']['euro']}",
        f"💷 Sterlin: {u['doviz']['sterlin']}",
        f"💎 Elmas: {u['doviz']['elmas']}"
    ])
    update.message.reply_text(
        f"💰 Bakiye: {u['bakiye']}₺\n🏦 Banka: {u['banka']}₺\n💱 Döviz:\n{doviz}"
    )

def bonus(update: Update, context: CallbackContext):
    u = get_user(update.effective_user.id)
    now = time.time()
    if now - u["bonus_time"] >= 86400:
        miktar = 50000
        u["bonus_time"] = now
        u["bakiye"] += miktar
        set_user(update.effective_user.id, u)
        update.message.reply_text(f"🎁 Günlük bonus: {miktar}₺! Harca gitsin!")
    else:
        kalan = int(86400 - (now - u["bonus_time"]))
        update.message.reply_text(f"⏳ Bonus için bekleme süresi: {kalan//3600} saat {kalan%3600//60} dk")

def bankaparaekle(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["bakiye"] >= miktar:
            u["bakiye"] -= miktar
            u["banka"] += miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"🏦 {miktar}₺ bankaya yatırıldı!")
        else:
            update.message.reply_text("❌ Yetersiz bakiye.")
    except:
        update.message.reply_text("🔢 Kullanım: /bankaparaekle miktar")

def bankaparaçek(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["banka"] >= miktar:
            u["banka"] -= miktar
            u["bakiye"] += miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"💳 {miktar}₺ bankadan çekildi!")
        else:
            update.message.reply_text("❌ Bankada bu kadar para yok.")
    except:
        update.message.reply_text("🔢 Kullanım: /bankaparaçek miktar")

def banka(update: Update, context: CallbackContext):
    u = get_user(update.effective_user.id)
    data = load_data()
    rates = data.get("exchange_rates", {})
    metin = (
        f"🏛️ <b>BANKA & DÖVİZ BİLGİLERİ</b>\n"
        f"💳 Banka Bakiyesi: {u['banka']}₺\n\n"
        f"💱 <b>Döviz Kurları:</b>\n"
        f"💵 Dolar: {rates.get('dolar', '?')}₺\n"
        f"💶 Euro: {rates.get('euro', '?')}₺\n"
        f"💷 Sterlin: {rates.get('sterlin', '?')}₺\n"
        f"💎 Elmas: {rates.get('elmas', '?')}₺"
    )
    update.message.reply_text(metin, parse_mode="HTML")
    def banka(update: Update, context: CallbackContext):
    u = get_user(update.effective_user.id)
    data = load_data()
    rates = data.get("exchange_rates", {})
    metin = (
        f"🏛️ <b>BANKA & DÖVİZ BİLGİLERİ</b>\n"
        f"💳 Banka Bakiyesi: {u['banka']}₺\n\n"
        f"💱 <b>Döviz Kurları:</b>\n"
        f"💵 Dolar: {rates.get('dolar', '?')}₺\n"
        f"💶 Euro: {rates.get('euro', '?')}₺\n"
        f"💷 Sterlin: {rates.get('sterlin', '?')}₺\n"
        f"💎 Elmas: {rates.get('elmas', '?')}₺"
    )
    update.message.reply_text(metin, parse_mode="HTML")

# BU KISIM ARTIK FONKSİYON DIŞINDA
def dovizal(update: Update, context: CallbackContext):
    try:
        tur = context.args[0].lower()
        miktar = int(context.args[1])
        data = load_data()
        u = get_user(update.effective_user.id)
        kur = data["exchange_rates"].get(tur)
        if not kur:
            return update.message.reply_text("❌ Geçersiz döviz türü!")
        toplam = miktar * kur
        if u["banka"] >= toplam:
            u["banka"] -= toplam
            u["doviz"][tur] = u["doviz"].get(tur, 0) + miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"✅ {miktar} {tur.upper()} alındı! (💵 {toplam}₺ harcandı)")
        else:
            update.message.reply_text("❌ Bankada yeterli para yok!")
    except:
        update.message.reply_text("🔢 Kullanım: /dövizal tür miktar")

def dovizsat(update: Update, context: CallbackContext):
    try:
        tur = context.args[0].lower()
        miktar = int(context.args[1])
        data = load_data()
        u = get_user(update.effective_user.id)
        mevcut = u["doviz"].get(tur, 0)
        kur = data["exchange_rates"].get(tur)
        if mevcut >= miktar:
            gelir = miktar * kur
            u["doviz"][tur] -= miktar
            u["banka"] += gelir
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"💱 {miktar} {tur.upper()} satıldı! Gelir: {gelir}₺")
        else:
            update.message.reply_text("❌ Elinizde bu kadar döviz yok!")
    except:
        update.message.reply_text("🔢 Kullanım: /dövizsat tür miktar")

def slot(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            return update.message.reply_text("💀 Yetersiz bakiye!")
        u["bakiye"] -= miktar
        emojis = ["🍒", "🍉", "🍇", "🍋", "🍓", "7️⃣"]
        r = [random.choice(emojis) for _ in range(3)]
        if r[0] == r[1] == r[2]:
            kazanc = miktar * 5
            u["bakiye"] += kazanc
            text = f"{r[0]} | {r[1]} | {r[2]}\n🎉 3 aynı geldi! {kazanc}₺ kazandın!"
        else:
            text = f"{r[0]} | {r[1]} | {r[2]}\n💀 Kaybettin! Tekrar dene."
        set_user(update.effective_user.id, u)
        update.message.reply_text(text)
    except:
        update.message.reply_text("🔢 Kullanım: /slot miktar")

def risk(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            return update.message.reply_text("💀 Yetersiz bakiye!")
        sans = random.randint(1, 100)
        if sans <= 50:
            u["bakiye"] += miktar
            text = f"🔥 Kazandın! +{miktar}₺"
        else:
            u["bakiye"] -= miktar
            text = "💀 Kaybettin! Tekrar dene!"
        set_user(update.effective_user.id, u)
        update.message.reply_text(text)
    except:
        update.message.reply_text("🔢 Kullanım: /risk miktar")

def bahis(update: Update, context: CallbackContext):
    try:
        miktar = int(context.args[0])
        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            return update.message.reply_text("💀 Yetersiz bakiye!")
        takimlar = ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Real Madrid", "Barcelona",
                    "Manchester City", "Liverpool", "Arsenal", "PSG", "Bayern", "Juventus", "Inter", "Dortmund", "Milan"]
        secilenler = random.sample(takimlar, 3)
        kazanan = random.choice(secilenler)
        buttons = [
            [InlineKeyboardButton(f"⚽ {team}", callback_data=f"bahis|{team}|{miktar}|{kazanan}")]
            for team in secilenler
        ]
        markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(f"⚽ Takımını seç! Bahis miktarı: {miktar}₺", reply_markup=markup)
    except:
        update.message.reply_text("🔢 Kullanım: /bahis miktar")

def bahis_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    _, secilen, miktar, kazanan = query.data.split("|")
    miktar = int(miktar)
    u = get_user(query.from_user.id)
    if secilen == kazanan:
        kazanc = miktar * 4
        u["bakiye"] += kazanc
        sonuc = f"🏆 {kazanan} kazandı! Doğru tahmin! +{kazanc}₺"
    else:
        sonuc = f"💀 Kaybettin! Kazanan: {kazanan}"
    set_user(query.from_user.id, u)
    query.edit_message_text(sonuc)

def paragönder(update: Update, context: CallbackContext):
    try:
        hedef = int(context.args[0])
        miktar = int(context.args[1])
        gonderen = get_user(update.effective_user.id)
        if gonderen["bakiye"] >= miktar:
            alici = get_user(hedef)
            gonderen["bakiye"] -= miktar
            alici["bakiye"] += miktar
            set_user(update.effective_user.id, gonderen)
            set_user(hedef, alici)
            update.message.reply_text(f"✅ {miktar}₺ başarıyla gönderildi!")
        else:
            update.message.reply_text("❌ Yetersiz bakiye!")
    except:
        update.message.reply_text("🔢 Kullanım: /paragönder kullanıcı_id miktar")

def parabasma(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return update.message.reply_text("🚫 Bu komut sadece adminlere özel!")
    try:
        hedef = int(context.args[0])
        miktar = int(context.args[1])
        u = get_user(hedef)
        u["bakiye"] += miktar
        set_user(hedef, u)
        update.message.reply_text(f"🤑 {hedef} kişisine {miktar}₺ basıldı!")
    except:
        update.message.reply_text("🔢 Kullanım: /parabasma kullanıcı_id miktar")

def admin(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return update.message.reply_text("🚫 Bu komut sadece adminlere özel!")
    try:
        yeni = str(context.args[0])
        data = load_data()
        if yeni not in data["admins"]:
            data["admins"].append(yeni)
            save_data(data)
            update.message.reply_text(f"👑 {yeni} artık admin!")
        else:
            update.message.reply_text("⚠️ Bu kullanıcı zaten admin!")
    except:
        update.message.reply_text("🔢 Kullanım: /admin kullanıcı_id")

def id(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        hedef = update.message.reply_to_message.from_user
        update.message.reply_text(f"🆔 {hedef.full_name} - {hedef.id}")
    else:
        update.message.reply_text(f"🆔 Senin ID: {update.effective_user.id}")

def top(update: Update, context: CallbackContext):
    data = load_data()
    sirali = sorted(data["users"].items(), key=lambda x: x[1]["bakiye"] + x[1]["banka"], reverse=True)[:10]
    metin = "🏆 <b>En Zenginler</b>\n\n"
    for i, (uid, user) in enumerate(sirali, 1):
        toplam = user["bakiye"] + user["banka"]
        metin += f"{i}. 👤 <code>{uid}</code> • {toplam}₺\n"
    update.message.reply_text(metin, parse_mode="HTML")
    def komutlar(update: Update, context: CallbackContext):
    text = (
        "📜 <b>Komutlar Listesi</b>\n"
        "🟢 /start - Botu başlat\n"
        "💸 /bakiye - Bakiyeni göster\n"
        "🎁 /bonus - Günlük bonus al\n"
        "🏦 /bankaparaekle x - Bankaya para yatır\n"
        "💳 /bankaparaçek x - Bankadan para çek\n"
        "🏛️ /banka - Banka ve döviz bilgilerini gösterir\n"
        "💱 /dövizal tür miktar - Döviz satın al\n"
        "💵 /dövizsat tür miktar - Döviz sat\n"
        "🎰 /slot x - Slot oynar (3 aynı emoji: X5 kazanır!)\n"
        "☠️ /risk x - %50 X2 kazanma riski\n"
        "⚽ /bahis x - 3 takım arasında seçim yap\n"
        "🧾 /paragönder id miktar - Başkasına para gönder\n"
        "🤑 /parabasma id miktar - Admin para basar\n"
        "👑 /admin id - Admin yetkisi ver\n"
        "🆔 /id - Kendi veya başkasının ID'si\n"
        "🏆 /top - En zengin 10 kişiyi göster"
    )
    update.message.reply_text(text, parse_mode="HTML")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Komutlar
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("bakiye", bakiye))
    dp.add_handler(CommandHandler("bonus", bonus))
    dp.add_handler(CommandHandler("bankaparaekle", bankaparaekle))
    dp.add_handler(CommandHandler("bankaparaçek", bankaparaçek))
    dp.add_handler(CommandHandler("banka", banka))
    dp.add_handler(CommandHandler("komutlar", komutlar))
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

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
