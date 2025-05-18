import json
import random
import time
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# Bot Token'ı - BotFather'dan alınmıştır
TOKEN = "7150888063:AAE6C0e3y_wSX-7LaEz57q4F4xQaqzlzIaY"

# Sabit Admin ID'si - Buraya KENDİ Telegram ID'nizi yazın!
SABIT_ADMIN_ID = 8121637254 # Örnek ID, KENDİ ID'nizi yazın!

# Veri Dosyası
DATA_FILE = "data.json"

# Router Tanımı
router = Router()

# Slot Emojileri
SLOT_EMOJIS = ["🍒", "🍋", "🍊", "🍇", "🍉", "🍓", "⭐", "💎"]

# Bahis Takımları
BAHIS_TAKIMLARI = [
    "Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Başakşehir", # Süper Lig örnekleri
    "Real Madrid", "Barcelona", "Atletico Madrid", "Manchester City", "Arsenal",
    "Liverpool", "Chelsea", "PSG", "Bayern Münih", "Juventus",
    "Napoli", "Inter", "Milan", "Ajax", "Borussia Dortmund" # Diğer büyük takımlar
]


# === JSON VERİ YÖNETİMİ ===
DEFAULT_DATA = {
    "users": {},
    "admins": [str(SABIT_ADMIN_ID)], # Başlangıçta sabit admini admin listesine ekle
    "exchange_rates": {
        "dolar": 32.5,  # Örnek başlangıç kurları
        "euro": 35.0,
        "sterlin": 40.0,
        "elmas": 10000.0
    }
}

def load_data():
    """Veriyi JSON dosyasından yükler, yoksa varsayılanı oluşturur."""
    if not Path(DATA_FILE).exists():
        save_data(DEFAULT_DATA)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # JSON bozuksa varsayılanı yükle/oluştur
        print(f"Uyarı: {DATA_FILE} dosyası bozuk, varsayılan veri yükleniyor.")
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    except Exception as e:
        print(f"Veri yüklenirken bir hata oluştu: {e}")
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()


def save_data(data):
    """Veriyi JSON dosyasına kaydeder."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Veri kaydedilirken bir hata oluştu: {e}")


def get_user(user_id):
    """Kullanıcı verisini alır, yoksa yeni kullanıcı oluşturur ve kaydeder."""
    data = load_data()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "bakiye": 1000,
            "banka": 0,
            "doviz": {"dolar": 0, "euro": 0, "sterlin": 0, "elmas": 0},
            "bonus_time": 0,
            "slot_time": 0 # Slot bekleme süresi eklenebilir, şu anlık yok
        }
        save_data(data) # Yeni kullanıcıyı kaydet
    return data["users"][uid]

def set_user(user_id, user_data):
    """Kullanıcı verisini günceller ve kaydeder."""
    data = load_data()
    data["users"][str(user_id)] = user_data
    save_data(data)

def get_rates():
    """Güncel döviz kurlarını alır."""
    return load_data().get("exchange_rates", DEFAULT_DATA["exchange_rates"])

def is_admin(user_id):
    """Kullanıcının admin olup olmadığını kontrol eder."""
    data = load_data()
    return str(user_id) == str(SABIT_ADMIN_ID) or str(user_id) in data.get("admins", [])

# === OTOMATİK GÖREVLER ===

async def update_exchange_rates_task(bot: Bot):
    """Döviz kurlarını periyodik olarak günceller (simülasyon)."""
    while True:
        await asyncio.sleep(120) # 120 saniye (2 dakika) bekle
        try:
            data = load_data()
            rates = data.get("exchange_rates", DEFAULT_DATA["exchange_rates"])

            # Döviz kurlarını rastgele %-5 ile %+5 arasında değiştir (simülasyon)
            for currency in rates:
                change_percentage = random.uniform(-0.05, 0.05) # -%5 ile +%5 arası
                rates[currency] *= (1 + change_percentage)
                # Kurun çok düşmesini engelle (örneğin min 0.1 TL)
                if rates[currency] < 0.1:
                     rates[currency] = random.uniform(0.1, rates[currency] * 2) # Biraz toparla
                # Kuru yuvarla (örneğin 2 ondalık)
                rates[currency] = round(rates[currency], 2)

            data["exchange_rates"] = rates
            save_data(data)
            #print("Döviz kurları güncellendi.") # Debug çıktısı
            # İsteğe bağlı: Admin'e kur güncelleme bilgisini gönderme
            # await bot.send_message(SABIT_ADMIN_ID, "Döviz kurları otomatik olarak güncellendi.")

        except Exception as e:
            print(f"Döviz kurlarını güncellerken hata oluştu: {e}")


# === KOMUTLAR ===

@router.message(Command("start"))
async def start_cmd(message: Message):
    get_user(message.from_user.id)
    await message.answer("✨ Merhaba, Fex Kumar Botuna Hoş Geldin ✨")
    await message.answer("✨ /komutlar Yazarak Tüm Komutlara Bakabilirsin. İyi Eğlenceler 🏆")

@router.message(Command("bakiye"))
async def bakiye_cmd(message: Message):
    u = get_user(message.from_user.id)
    d = u["doviz"]
    msg = (
        f"💰 <b>Bakiye:</b> {u['bakiye']:,}₺\n"
        f"🏦 <b>Banka:</b> {u['banka']:,}₺\n\n"
        f"💱 <b>Döviz Cüzdanı</b>\n"
        f"💵 Dolar: {d['dolar']:,}\n"
        f"💶 Euro: {d['euro']:,}\n"
        f"💷 Sterlin: {d['sterlin']:,}\n"
        f"💎 Elmas: {d['elmas']:,}"
    )
    await message.answer(msg, parse_mode="HTML")

@router.message(Command("bonus"))
async def bonus_cmd(message: Message):
    u = get_user(message.from_user.id)
    now = time.time()
    bonus_cooldown = 86400 # 24 saat

    if now - u.get("bonus_time", 0) >= bonus_cooldown:
        miktar = random.randint(1000, 5000)
        u["bonus_time"] = now
        u["bakiye"] += miktar
        set_user(message.from_user.id, u)
        await message.answer(f"🎁 Günlük Bonus Aldın: <b>{miktar:,}₺</b>!", parse_mode="HTML")
    else:
        kalan = int(bonus_cooldown - (now - u["bonus_time"]))
        saat = kalan // 3600
        dakika = (kalan % 3600) // 60
        saniye = kalan % 60
        await message.answer(f"⏳ Bonus için bekleme süresi: <b>{saat} saat {dakika} dakika {saniye} saniye</b>", parse_mode="HTML")

@router.message(Command("bankaparaekle"))
async def banka_ekle(message: Message):
    try:
        miktar = int(message.text.split()[1])
        if miktar <= 0:
            await message.answer("❌ Yatırmak istediğiniz miktar pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        if u["bakiye"] >= miktar:
            u["bakiye"] -= miktar
            u["banka"] += miktar
            set_user(message.from_user.id, u)
            await message.answer(f"🏦 {miktar:,}₺ bakiyenizden bankaya yatırıldı!")
        else:
            await message.answer("❌ Yetersiz bakiye.")
    except (IndexError, ValueError):
        await message.answer("🔢 Doğru kullanım: /bankaparaekle <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("bankaparaçek"))
async def banka_cek(message: Message):
    try:
        miktar = int(message.text.split()[1])
        if miktar <= 0:
            await message.answer("❌ Çekmek istediğiniz miktar pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        if u["banka"] >= miktar:
            u["banka"] -= miktar
            u["bakiye"] += miktar
            set_user(message.from_user.id, u)
            await message.answer(f"💳 {miktar:,}₺ bankadan bakiyenize çekildi!")
        else:
            await message.answer("❌ Bankada bu kadar paran yok.")
    except (IndexError, ValueError):
        await message.answer("🔢 Doğru kullanım: /bankaparaçek <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("banka"))
async def banka_info(message: Message):
    u = get_user(message.from_user.id)
    rates = get_rates()
    msg = (
        f"🏦 <b>BANKA BİLGİLERİ</b>\n"
        f"💳 Banka Bakiyesi: {u['banka']:,}₺\n\n"
        f"💱 <b>Güncel Döviz Kurları</b>\n"
        f"💵 Dolar: {rates.get('dolar', 0):.2f}₺\n"
        f"💶 Euro: {rates.get('euro', 0):.2f}₺\n"
        f"💷 Sterlin: {rates.get('sterlin', 0):.2f}₺\n"
        f"💎 Elmas: {rates.get('elmas', 0):,.0f}₺" # Elmas tam sayı olabilir
    )
    await message.answer(msg, parse_mode="HTML")

@router.message(Command("dövizal"))
async def doviz_al(message: Message):
    try:
        _, tur, miktar_str = message.text.split()
        miktar = int(miktar_str)

        if miktar <= 0:
            await message.answer("❌ Almak istediğiniz miktar pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        rates = get_rates()
        tur = tur.lower() # Döviz türünü küçük harfe çevir

        if tur not in rates:
            await message.answer("❌ Geçersiz döviz türü. Geçerli türler: Dolar, Euro, Sterlin, Elmas")
            return

        kur = rates[tur]
        toplam_maliyet = miktar * kur

        if u["banka"] >= toplam_maliyet:
            u["banka"] -= toplam_maliyet
            u["doviz"][tur] += miktar
            set_user(message.from_user.id, u)
            await message.answer(f"✅ {miktar:,} adet {tur.upper()} alındı! (💸 {toplam_maliyet:,.2f}₺ bankadan harcandı)")
        else:
            await message.answer("❌ Bankada yeterli paran yok.")
    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /dövizal <tür> <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("dövizsat"))
async def doviz_sat(message: Message):
    try:
        _, tur, miktar_str = message.text.split()
        miktar = int(miktar_str)

        if miktar <= 0:
            await message.answer("❌ Satmak istediğiniz miktar pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        rates = get_rates()
        tur = tur.lower() # Döviz türünü küçük harfe çevir

        if tur not in rates or tur not in u["doviz"]:
             await message.answer("❌ Geçersiz döviz türü veya elinizde o türden döviz yok.")
             return

        if u["doviz"][tur] >= miktar:
            kur = rates[tur]
            gelir = miktar * kur
            u["doviz"][tur] -= miktar
            u["banka"] += gelir
            set_user(message.from_user.id, u)
            await message.answer(f"💱 {miktar:,} adet {tur.upper()} satıldı, 💵 {gelir:,.2f}₺ bankaya eklendi!")
        else:
            await message.answer(f"❌ Elinde bu kadar {tur.upper()} yok.")
    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /dövizsat <tür> <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("risk"))
async def risk_cmd(message: Message):
    try:
        miktar = int(message.text.split()[1])
        if miktar <= 0:
            await message.answer("❌ Bahis miktarı pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        if u["bakiye"] < miktar:
            await message.answer("💸 Yetersiz bakiye!")
            return

        # Bahsi düş (kaybettiğinde düşülmemesi için önce düşülür)
        u["bakiye"] -= miktar

        if random.random() < 0.5: # %50 kazanma şansı
            kazanc = miktar * 2 # Bahsin 2 katı kazanılır (bahis + kar)
            u["bakiye"] += kazanc
            await message.answer(f"🔥 Şanslısın! {miktar:,}₺ risk aldın ve {kazanc:,}₺ kazandın! (Net Kar: {kazanc - miktar:,}₺)")
        else:
            await message.answer(f"💀 Kaybettin! {miktar:,}₺ gitti...")

        set_user(message.from_user.id, u)
    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /risk <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")

@router.message(Command("slot"))
async def slot_cmd(message: Message):
    try:
        miktar = int(message.text.split()[1])
        if miktar <= 0:
            await message.answer("❌ Bahis miktarı pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        if u["bakiye"] < miktar:
            await message.answer("💸 Yetersiz bakiye!")
            return

        # Bahsi düş
        u["bakiye"] -= miktar

        # Slot çevir
        result = [random.choice(SLOT_EMOJIS) for _ in range(3)]
        result_str = f"✨ {result[0]} | {result[1]} | {result[2]} ✨"

        sonuc_mesaj = f"🎰 Slot Çevrildi:\n{result_str}\n"

        # Kazanma kontrolü (Sadece 3 aynı emoji)
        if result[0] == result[1] == result[2]:
            kazanc = miktar * 4
            u["bakiye"] += kazanc
            sonuc_mesaj += f"🎉 TEBRİKLER! 3 tane {result[0]}!\n+{kazanc:,}₺ kazandın! (Net Kar: {kazanc - miktar:,}₺)"
        else:
            sonuc_mesaj += f"💸 Kaybettin! {miktar:,}₺ gitti."

        set_user(message.from_user.id, u)
        await message.answer(sonuc_mesaj)

    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /slot <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("bahis"))
async def bahis_cmd(message: Message):
    try:
        miktar = int(message.text.split()[1])
        if miktar <= 0:
            await message.answer("❌ Bahis miktarı pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        if u["bakiye"] < miktar:
            await message.answer("💸 Yetersiz bakiye!")
            return

        # Bahsi düş (kaybettiğinde düşülmemesi için önce düşülür)
        u["bakiye"] -= miktar
        set_user(message.from_user.id, u) # Bahis düşüldüğünde kaydet

        # 3 farklı takım seç
        if len(BAHIS_TAKIMLARI) < 3:
             await message.answer("Bahis için yeterli takım tanımlı değil.")
             u["bakiye"] += miktar # Bahsi geri ver
             set_user(message.from_user.id, u)
             return

        secilen_takimlar = random.sample(BAHIS_TAKIMLARI, 3)
        kazanan_takim = random.choice(secilen_takimlar) # Seçilenlerden biri kazanır

        buttons = [
            [InlineKeyboardButton(text=f"⚽ {t}", callback_data=f"bahis|{t}|{miktar}|{kazanan_takim}")]
            for t in secilen_takimlar
        ]
        klavye = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(f"⚽ {miktar:,}₺ ile bahis yap!\nHangi takım kazanır?", reply_markup=klavye)

    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /bahis <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.callback_query(F.data.startswith("bahis|"))
async def bahis_callback(query: CallbackQuery):
    try:
        # Callback verisini ayrıştır
        # Yapı: "bahis|SeçilenTakım|Miktar|KazananTakım"
        data_parts = query.data.split("|")
        if len(data_parts) != 4:
             await query.answer("Hata: Geçersiz bahis verisi.", show_alert=True)
             return

        _, secilen_takim, miktar_str, kazanan_takim = data_parts

        try:
             miktar = int(miktar_str)
        except ValueError:
             await query.answer("Hata: Miktar sayı değil.", show_alert=True)
             return

        u = get_user(query.from_user.id)

        # Eğer kullanıcı bakiyesi zaten düşülmüşse (komutta düşülüyor), burada tekrar düşme.
        # Sadece sonucu işle.

        sonuc_mesaj = f"⚽ Bahis Sonucu: {miktar:,}₺\n"

        if secilen_takim == kazanan_takim:
            kazanc = miktar * 4 # Bahsin 4 katı kazanılır (bahis + kar)
            u["bakiye"] += kazanc
            sonuc_mesaj += f"🏆 <b>{kazanan_takim}</b> kazandı!\n🎉 Doğru tahmin! <b>+{kazanc:,}₺</b> kazandın! (Net Kar: {kazanc - miktar:,}₺)"
        else:
            sonuc_mesaj += f"❌ <b>{kazanan_takim}</b> kazandı, sen <b>{secilen_takim}</b> demiştin.\n💸 <b>{miktar:,}₺</b> kaybettin!"

        set_user(query.from_user.id, u) # Sonucu kaydet

        # Butonları kaldır ve sonucu gönder
        await query.message.edit_text(sonuc_mesaj, parse_mode="HTML")
        await query.answer() # Callback sorgusunu tamamla

    except Exception as e:
        await query.answer("Bir hata oluştu.", show_alert=True)
        print(f"Bahis callback hatası: {e}")
        # Eğer hata olursa ve bahis miktarı düşülmüşse, miktarı iade etme durumu
        # karmaşıklaşır. Basitlik adına şimdilik iade etmiyoruz,
        # bu tür hataların loglanıp manuel çözülmesi gerekebilir.
        # Daha sağlam bir sistemde transaction yönetimi gerekebilir.


@router.message(Command("paragönder"))
async def gonder_cmd(message: Message):
    try:
        _, hedef_id_str, miktar_str = message.text.split()
        miktar = int(miktar_str)
        hedef_id = int(hedef_id_str)

        if miktar <= 0:
            await message.answer("❌ Göndermek istediğiniz miktar pozitif olmalı.")
            return

        u = get_user(message.from_user.id)
        if u["bakiye"] >= miktar:
            # Gönderenin bakiyesini düş
            u["bakiye"] -= miktar
            set_user(message.from_user.id, u)

            # Alıcının bakiyesini artır
            alici = get_user(hedef_id) # Alıcı yoksa oluşturulur
            alici["bakiye"] += miktar
            set_user(hedef_id, alici)

            await message.answer(f"✅ <code>{hedef_id}</code> ID'li kullanıcıya <b>{miktar:,}₺</b> gönderildi!", parse_mode="HTML")

            # Alıcıya bildirim göndermeyi deneyebiliriz (isteğe bağlı)
            try:
                 await message.bot.send_message(hedef_id, f"💸 Birisi size <b>{miktar:,}₺</b> gönderdi!", parse_mode="HTML")
            except Exception as e:
                 print(f"Para gönderme bildirimi alıcıya iletilemedi ({hedef_id}): {e}")

        else:
            await message.answer("❌ Yetersiz bakiye!")
    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /paragönder <id> <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("parabasma"))
async def basma_cmd(message: Message):
    # Admin kontrolü
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu komutu kullanma yetkiniz yok.")
        return

    try:
        _, hedef_id_str, miktar_str = message.text.split()
        miktar = int(miktar_str)
        hedef_id = int(hedef_id_str)

        if miktar <= 0:
             await message.answer("❌ Basılacak miktar pozitif olmalı.")
             return

        u = get_user(hedef_id) # Hedef kullanıcıyı al/oluştur
        u["bakiye"] += miktar
        set_user(hedef_id, u)

        await message.answer(f"🤑 <code>{hedef_id}</code> ID'li kullanıcının bakiyesine <b>{miktar:,}₺</b> basıldı!", parse_mode="HTML")

         # Kullanıcıya bildirim göndermeyi deneyebiliriz (isteğe bağlı)
        try:
            await message.bot.send_message(hedef_id, f"🥳 Bakiyenize Admin tarafından <b>{miktar:,}₺</b> eklendi!", parse_mode="HTML")
        except Exception as e:
            print(f"Para basma bildirimi kullanıcıya iletilemedi ({hedef_id}): {e}")

    except (IndexError, ValueError):
        await message.answer("🔢 Kullanım: /parabasma <id> <miktar>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")

@router.message(Command("id"))
async def id_cmd(message: Message):
    # Yanıtlanan mesajın sahibinin ID'sini al, yoksa kendi ID'sini al
    user_to_get_id = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    ad = user_to_get_id.first_name
    if user_to_get_id.last_name:
        ad += f" {user_to_get_id.last_name}"
    await message.answer(f"👤 Kullanıcı: {ad}\n🆔 ID: <code>{user_to_get_id.id}</code>", parse_mode="HTML")

@router.message(Command("top"))
async def top_cmd(message: Message):
    data = load_data().get("users", {})
    sirali = sorted(
        data.items(),
        key=lambda item: item[1].get("bakiye", 0) + item[1].get("banka", 0),
        reverse=True
    )[:10]

    if not sirali:
        await message.answer("🏆 Henüz hiç kullanıcı yok.")
        return

    msg = "🏆 <b>EN ZENGİN 10 Kişi (✨ Toplam • Bakiye • Banka✨ )</b>\n\n"
    for i, (uid, user_data) in enumerate(sirali, 1):
        toplam = user_data.get("bakiye", 0) + user_data.get("banka", 0)
        try:
            user = await message.bot.get_chat(uid)
            if user.username:
                isim = f"@{user.username}"
            else:
                isim = f"{user.first_name} {user.last_name or ''}"
        except:
            isim = f"ID:{uid}"

        sembol = "🏆" if i == 1 else "✨"
        msg += f"{sembol} {i}. Kullanıcı: {isim} — {toplam:,}₺ 💸\n"

    await message.answer(msg, parse_mode="HTML")
    
@@router.message(Command("komutlar"))
async def komutlari_goster(message: Message):
    komutlar = """=== ✨ BOT KOMUTLARI ✨ ===
🟢 /start - Botu başlat  
💰 /bakiye - Bakiye ve döviz  
🎁 /bonus - Günlük bonus  
🏦 /bankaparaekle - Bankaya yatır  
💳 /bankaparaçek - Bankadan çek  
🏦 /banka - Döviz kurları  
📈 /dövizal - Döviz al  
📉 /dövizsat - Döviz sat  
🎰 /slot - Slot çevir  
🔥 /risk - Risk al kazan  
⚽ /bahis - Takım seç bahis  
🤝 /paragönder - Para gönder  
🤑 /parabasma - Admin para basar  
🆔 /id - Kullanıcı ID göster  
🏆 /top - En zenginler  
📜 /komutlar - Tüm komutlar  
🛡 /admin - Admin ekle  
🔍 /rep - Kullanıcı bilgisi
"""
    await message.answer(komutlar)
    
@router.message(Command("admin"))
async def admin_ekle(message: Message):
    # Admin kontrolü
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu komutu kullanma yetkiniz yok.")
        return

    try:
        uid_str = message.text.split()[1]
        data = load_data()
        if uid_str not in data.get("admins", []):
            data["admins"].append(uid_str)
            save_data(data)
            await message.answer(f"🛡 <code>{uid_str}</code> ID'li kullanıcı admin yapıldı.", parse_mode="HTML")
        else:
            await message.answer("ℹ️ Belirtilen kullanıcı zaten admin.")
    except IndexError:
        await message.answer("🔢 Kullanım: /admin <id>")
    except Exception as e:
        await message.answer(f"Bir hata oluştu: {e}")


@router.message(Command("rep"))
async def rep_cmd(message: Message):
    # Yanıtlanan mesajın sahibinin ID'sini al, yoksa kendi ID'sini al
    user_to_get_info = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    ad = user_to_get_info.first_name
    if user_to_get_info.last_name:
        ad += f" {user_to_get_info.last_name}"

    is_adm = "✅" if is_admin(user_to_get_info.id) else "❌"

    await message.answer(
        f"👤 <b>Kullanıcı Bilgisi</b>\n"
        f"Adı: {ad}\n"
        f"ID: <code>{user_to_get_info.id}</code>\n"
        f"Bot Mu?: {'Evet' if user_to_get_info.is_bot else 'Hayır'}\n"
        f"Admin Mi?: {is_adm}",
        parse_mode="HTML"
    )


# === BOT BAŞLATICI ===

async def main():
    # Bot ve Dispatcher oluştur
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Router'ı Dispatcher'a ekle
    dp.include_router(router)

    # Otomatik döviz güncelleme görevini başlat
    asyncio.create_task(update_exchange_rates_task(bot))

    # Botu başlat
    print("Bot başlatılıyor...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Script doğrudan çalıştırıldığında main fonksiyonunu çalıştır
    asyncio.run(main())
    
