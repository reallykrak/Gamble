import json, random, time, asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

TOKEN = "7150888063:AAGZizuDzTxE4RFlBsFJLWTLkwDo061FKyU"  # BotFather'dan alınan token
DATA_FILE = "data.json"
router = Router()

# === JSON VERİ YÖNETİMİ ===
DEFAULT_DATA = {
    "users": {},
    "admins": [],
    "exchange_rates": {
        "dolar": 20.0,
        "euro": 22.0,
        "sterlin": 25.0,
        "elmas": 1000.0
    }
}

def load_data():
    if not Path(DATA_FILE).exists():
        save_data(DEFAULT_DATA)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user(user_id):
    data = load_data()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "bakiye": 1000,
            "banka": 0,
            "doviz": {"dolar": 0, "euro": 0, "sterlin": 0, "elmas": 0},
            "bonus_time": 0
        }
        save_data(data)
    return data["users"][uid]

def set_user(user_id, user_data):
    data = load_data()
    data["users"][str(user_id)] = user_data
    save_data(data)

def get_rates():
    return load_data().get("exchange_rates", DEFAULT_DATA["exchange_rates"])

# === KOMUTLAR ===

@router.message(Command("start"))
async def start_cmd(message: Message):
    user = message.from_user
    get_user(user.id)
    await message.answer(f"👋 Merhaba <b>{user.first_name}</b>!\n🎰 Kumar Botuna Hoş Geldin!\n\n💵 Başlangıç bakiyen: <b>1000₺</b>", parse_mode="HTML")

@router.message(Command("bakiye"))
async def bakiye_cmd(message: Message):
    u = get_user(message.from_user.id)
    d = u["doviz"]
    msg = (
        f"💰 <b>Bakiye:</b> {u['bakiye']}₺\n"
        f"🏦 <b>Banka:</b> {u['banka']}₺\n\n"
        f"💱 <b>Döviz Cüzdanı</b>\n"
        f"💵 Dolar: {d['dolar']}\n"
        f"💶 Euro: {d['euro']}\n"
        f"💷 Sterlin: {d['sterlin']}\n"
        f"💎 Elmas: {d['elmas']}"
    )
    await message.answer(msg, parse_mode="HTML")

@router.message(Command("bonus"))
async def bonus_cmd(message: Message):
    u = get_user(message.from_user.id)
    now = time.time()
    if now - u.get("bonus_time", 0) >= 86400:
        miktar = random.randint(1000, 5000)
        u["bonus_time"] = now
        u["bakiye"] += miktar
        set_user(message.from_user.id, u)
        await message.answer(f"🎁 Günlük Bonus Aldın: <b>{miktar}₺</b>!", parse_mode="HTML")
    else:
        kalan = int(86400 - (now - u["bonus_time"]))
        saat = kalan // 3600
        dakika = (kalan % 3600) // 60
        await message.answer(f"⏳ Bonus için bekleme süresi: <b>{saat} saat {dakika} dakika</b>", parse_mode="HTML")

@router.message(Command("bankaparaekle"))
async def banka_ekle(message: Message):
    try:
        miktar = int(message.text.split()[1])
        u = get_user(message.from_user.id)
        if u["bakiye"] >= miktar:
            u["bakiye"] -= miktar
            u["banka"] += miktar
            set_user(message.from_user.id, u)
            await message.answer(f"🏦 {miktar}₺ bankaya yatırıldı!")
        else:
            await message.answer("❌ Yetersiz bakiye.")
    except:
        await message.answer("🔢 Doğru kullanım: /bankaparaekle <miktar>")

@router.message(Command("bankaparaçek"))
async def banka_cek(message: Message):
    try:
        miktar = int(message.text.split()[1])
        u = get_user(message.from_user.id)
        if u["banka"] >= miktar:
            u["banka"] -= miktar
            u["bakiye"] += miktar
            set_user(message.from_user.id, u)
            await message.answer(f"💳 {miktar}₺ bankadan çekildi!")
        else:
            await message.answer("❌ Bankada bu kadar paran yok.")
    except:
        await message.answer("🔢 Doğru kullanım: /bankaparaçek <miktar>")

@router.message(Command("banka"))
async def banka_info(message: Message):
    u = get_user(message.from_user.id)
    rates = get_rates()
    msg = (
        f"🏦 <b>BANKA BİLGİLERİ</b>\n"
        f"💳 Banka Bakiyesi: {u['banka']}₺\n\n"
        f"💱 <b>Güncel Döviz Kurları</b>\n"
        f"💵 Dolar: {rates['dolar']}₺\n"
        f"💶 Euro: {rates['euro']}₺\n"
        f"💷 Sterlin: {rates['sterlin']}₺\n"
        f"💎 Elmas: {rates['elmas']}₺"
    )
    await message.answer(msg, parse_mode="HTML")

@router.message(Command("dövizal"))
async def doviz_al(message: Message):
    try:
        _, tur, miktar = message.text.split()
        miktar = int(miktar)
        u = get_user(message.from_user.id)
        rates = get_rates()
        if tur not in rates:
            await message.answer("❌ Geçersiz döviz türü.")
            return
        toplam = miktar * rates[tur]
        if u["banka"] >= toplam:
            u["banka"] -= toplam
            u["doviz"][tur] += miktar
            set_user(message.from_user.id, u)
            await message.answer(f"✅ {miktar} {tur.upper()} alındı! (💸 {toplam}₺ harcandı)")
        else:
            await message.answer("❌ Bankada yeterli paran yok.")
    except:
        await message.answer("🔢 Kullanım: /dövizal <tür> <miktar>")

@router.message(Command("dövizsat"))
async def doviz_sat(message: Message):
    try:
        _, tur, miktar = message.text.split()
        miktar = int(miktar)
        u = get_user(message.from_user.id)
        rates = get_rates()
        if tur not in rates:
            await message.answer("❌ Geçersiz döviz türü.")
            return
        if u["doviz"][tur] >= miktar:
            gelir = miktar * rates[tur]
            u["doviz"][tur] -= miktar
            u["banka"] += gelir
            set_user(message.from_user.id, u)
            await message.answer(f"💱 {miktar} {tur.upper()} satıldı, 💵 {gelir}₺ kazandın!")
        else:
            await message.answer("❌ Elinde bu kadar döviz yok.")
    except:
        await message.answer("🔢 Kullanım: /dövizsat <tür> <miktar>")
        @router.message(Command("slot"))
async def slot_cmd(message: Message):
    try:
        miktar = int(message.text.split()[1])
        u = get_user(message.from_user.id)
        if u["bakiye"] < miktar:
            await message.answer("💸 Yetersiz bakiye!")
            return
        u["bakiye"] -= miktar
        semboller = ["🍒", "🍋", "🍇", "🍉", "7️⃣", "💎"]
        slotlar = [random.choice(semboller) for _ in range(3)]
        kazanc = 0
        if slotlar.count(slotlar[0]) == 3:
            kazanc = miktar * (10 if slotlar[0] == "7️⃣" else 7 if slotlar[0] == "💎" else 5)
        elif slotlar[0] == slotlar[1] or slotlar[1] == slotlar[2] or slotlar[0] == slotlar[2]:
            kazanc = miktar * 2
        u["bakiye"] += kazanc
        set_user(message.from_user.id, u)
        sonuc = " | ".join(slotlar)
        mesaj = f"{sonuc}\n\n"
        if kazanc > 0:
            mesaj += f"🎉 Kazandın: {kazanc}₺"
        else:
            mesaj += "💀 Kaybettin!"
        await message.answer(mesaj)
    except:
        await message.answer("🔢 Kullanım: /slot <miktar>")

@router.message(Command("risk"))
async def risk_cmd(message: Message):
    try:
        miktar = int(message.text.split()[1])
        u = get_user(message.from_user.id)
        if u["bakiye"] < miktar:
            await message.answer("💸 Yetersiz bakiye!")
            return
        sonuc = random.randint(1, 100)
        if sonuc <= 45:
            u["bakiye"] += miktar
            await message.answer(f"🔥 Şanslısın! {miktar}₺ kazandın!")
        else:
            u["bakiye"] -= miktar
            await message.answer(f"💀 Kaybettin! {miktar}₺ gitti...")
        set_user(message.from_user.id, u)
    except:
        await message.answer("🔢 Kullanım: /risk <miktar>")

@router.message(Command("bahis"))
async def bahis_cmd(message: Message):
    try:
        miktar = int(message.text.split()[1])
        u = get_user(message.from_user.id)
        if u["bakiye"] < miktar:
            await message.answer("💸 Yetersiz bakiye!")
            return
        takimlar = ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Real Madrid", "Barcelona", "Atletico Madrid",
                    "Manchester City", "Arsenal", "Liverpool", "PSG", "Bayern Münih", "Juventus", "Napoli",
                    "Inter", "Ajax"]
        secilen = random.sample(takimlar, 3)
        kazanan = random.choice(secilen)
        u["bakiye"] -= miktar
        set_user(message.from_user.id, u)
        buttons = [
            [InlineKeyboardButton(f"⚽ {t}", callback_data=f"bahis|{t}|{miktar}|{kazanan}")]
            for t in secilen
        ]
        await message.answer("⚽ Takımını seç!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        await message.answer("🔢 Kullanım: /bahis <miktar>")

@router.callback_query(F.data.startswith("bahis"))
async def bahis_callback(query: CallbackQuery):
    _, secilen, miktar, kazanan = query.data.split("|")
    miktar = int(miktar)
    u = get_user(query.from_user.id)
    if secilen == kazanan:
        kazanc = miktar * 4
        u["bakiye"] += kazanc
        sonuc = f"🏆 {kazanan} kazandı!\n🎉 Doğru tahmin! +{kazanc}₺"
    else:
        sonuc = f"❌ {kazanan} kazandı, sen {secilen} dedin.\n💸 {miktar}₺ kaybettin!"
    set_user(query.from_user.id, u)
    await query.message.edit_text(sonuc)

@router.message(Command("paragönder"))
async def gonder_cmd(message: Message):
    try:
        _, hedef, miktar = message.text.split()
        miktar = int(miktar)
        uid = int(hedef)
        u = get_user(message.from_user.id)
        if u["bakiye"] >= miktar:
            u["bakiye"] -= miktar
            alici = get_user(uid)
            alici["bakiye"] += miktar
            set_user(message.from_user.id, u)
            set_user(uid, alici)
            await message.answer(f"✅ {uid} ID'ye {miktar}₺ gönderildi!")
        else:
            await message.answer("❌ Yetersiz bakiye!")
    except:
        await message.answer("🔢 Kullanım: /paragönder <id> <miktar>")

@router.message(Command("parabasma"))
async def basma_cmd(message: Message):
    try:
        _, hedef, miktar = message.text.split()
        miktar = int(miktar)
        uid = int(hedef)
        u = get_user(uid)
        u["bakiye"] += miktar
        set_user(uid, u)
        await message.answer(f"🤑 {uid} ID'ye {miktar}₺ basıldı!")
    except:
        await message.answer("🔢 Kullanım: /parabasma <id> <miktar>")

@router.message(Command("id"))
async def id_cmd(message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.answer(f"🆔 Kullanıcı ID: <code>{user.id}</code>", parse_mode="HTML")

@router.message(Command("top"))
async def top_cmd(message: Message):
    data = load_data().get("users", {})
    sirali = sorted(data.items(), key=lambda x: x[1]["bakiye"], reverse=True)[:10]
    msg = "🏆 <b>EN ZENGİN 10</b>\n\n"
    for i, (uid, user) in enumerate(sirali, 1):
        msg += f"{i}. ID: <code>{uid}</code> — {user['bakiye']}₺\n"
    await message.answer(msg, parse_mode="HTML")

@router.message(Command("komutlar"))
async def komutlar_cmd(message: Message):
    komutlar = (
        "🎮 /start – Botu başlat\n"
        "💰 /bakiye – Bakiye ve döviz\n"
        "🎁 /bonus – Günlük bonus\n"
        "🏦 /bankaparaekle – Bankaya yatır\n"
        "💳 /bankaparaçek – Bankadan çek\n"
        "💱 /banka – Döviz kurları\n"
        "📈 /dövizal – Döviz al\n"
        "📉 /dövizsat – Döviz sat\n"
        "🎰 /slot – Slot çevir\n"
        "🔥 /risk – Risk al kazan\n"
        "⚽ /bahis – Takım seç bahis\n"
        "🤝 /paragönder – Para gönder\n"
        "🤑 /parabasma – Admin para basar\n"
        "🆔 /id – Kullanıcı ID göster\n"
        "🏆 /top – En zenginler\n"
        "📜 /komutlar – Tüm komutlar\n"
        "🛡 /admin – Admin ekle\n"
        "🔍 /rep – Kullanıcı bilgisi"
    )
    await message.answer(komutlar)

@router.message(Command("admin"))
async def admin_ekle(message: Message):
    uid = str(message.text.split()[1])
    data = load_data()
    if uid not in data["admins"]:
        data["admins"].append(uid)
        save_data(data)
        await message.answer(f"🛡 {uid} ID admin yapıldı.")
    else:
        await message.answer("ℹ️ Zaten admin.")

@router.message(Command("rep"))
async def rep_cmd(message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    ad = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    await message.answer(f"👤 {ad}\n🆔 <code>{user.id}</code>", parse_mode="HTML")

# === BOT BAŞLATICI ===

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
