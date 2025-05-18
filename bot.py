import json
import random
import time
import os # Dosya işlemleri için eklendi
import logging # Loglama için eklendi

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# === Logging Ayarları ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === TOKEN ve SABİT ADMIN ===
# Lütfen gerçek TOKEN'ınızı buraya girin ve gizli tutun.
# Güvenlik için TOKEN'ı bir ortam değişkeninden veya ayrı bir yapılandırma dosyasından yüklemeniz önerilir.
TOKEN = "7150888063:AAGZizuDzTxE4RFlBsFJLWTLkwDo061FKyU" # GERÇEK TOKEN'INIZI GİRİN
SABIT_ADMIN_ID = 8121637254 # Bu ID'yi kendi Telegram kullanıcı ID'niz ile değiştirin
DATA_FILE = "data.json"

# === Varsayılan Veri Yapısı ===
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

# === VERİ İŞLEME ===
def load_data():
    if not os.path.exists(DATA_FILE):
        logger.info(f"{DATA_FILE} bulunamadı, varsayılan veri ile oluşturuluyor.")
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy() # Kopyasını döndürerek orijinal DEFAULT_DATA'nın değişmesini engelle
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Temel anahtarların varlığını kontrol et, yoksa varsayılan değerlerle güncelle
            changed = False
            if "users" not in data:
                data["users"] = DEFAULT_DATA["users"]
                changed = True
            if "admins" not in data:
                data["admins"] = DEFAULT_DATA["admins"]
                changed = True
            if "exchange_rates" not in data:
                data["exchange_rates"] = DEFAULT_DATA["exchange_rates"]
                changed = True
            elif not all(k in data["exchange_rates"] for k in DEFAULT_DATA["exchange_rates"]):
                # Eksik döviz kurları varsa varsayılanları ekle
                for key, value in DEFAULT_DATA["exchange_rates"].items():
                    data["exchange_rates"].setdefault(key, value)
                changed = True

            if changed:
                save_data(data)
            return data
    except json.JSONDecodeError:
        logger.error(f"{DATA_FILE} bozuk, varsayılan veri ile üzerine yazılıyor.")
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    except Exception as e:
        logger.error(f"Veri yüklenirken beklenmedik bir hata oluştu: {e}")
        # En kötü durumda, varsayılan veriyi döndürerek botun çökmesini engelle
        return DEFAULT_DATA.copy()


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Veri kaydedilirken hata oluştu: {e}")

def get_user(user_id):
    data = load_data()
    # data["users"] anahtarının varlığı load_data tarafından garanti altına alınır
    if str(user_id) not in data["users"]:
        logger.info(f"Yeni kullanıcı eklendi: {user_id}")
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
    # data["admins"] anahtarının varlığı load_data tarafından garanti altına alınır
    return str(user_id) == str(SABIT_ADMIN_ID) or str(user_id) in data.get("admins", [])

# === KOMUTLAR ===
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    get_user(user.id) # Kullanıcı verisini oluştur veya yükle
    update.message.reply_text(f"👋 Merhaba {user.first_name}! Kumar botuna hoş geldin!\n💸 Başlangıç bakiyen: 1000₺")

def bakiye(update: Update, context: CallbackContext):
    u = get_user(update.effective_user.id)
    doviz_listesi = [
        f"💵 Dolar: {u['doviz'].get('dolar', 0)}",
        f"💶 Euro: {u['doviz'].get('euro', 0)}",
        f"💷 Sterlin: {u['doviz'].get('sterlin', 0)}",
        f"💎 Elmas: {u['doviz'].get('elmas', 0)}"
    ]
    doviz_mesaji = "\n".join(doviz_listesi)
    update.message.reply_text(
        f"💰 Bakiye: {u['bakiye']}₺\n🏦 Banka: {u['banka']}₺\n\n💱 Dövizlerin:\n{doviz_mesaji}"
    )

def bonus(update: Update, context: CallbackContext):
    u = get_user(update.effective_user.id)
    now = time.time()
    bonus_bekleme_suresi = 24 * 60 * 60  # 24 saat (saniye cinsinden)

    if now - u.get("bonus_time", 0) >= bonus_bekleme_suresi:
        miktar = random.randint(1000, 5000) # Rastgele bonus miktarı
        u["bonus_time"] = now
        u["bakiye"] += miktar
        set_user(update.effective_user.id, u)
        update.message.reply_text(f"🎁 Günlük bonus kazandın: {miktar}₺! Harca gitsin!")
    else:
        kalan = int(bonus_bekleme_suresi - (now - u.get("bonus_time", 0)))
        saat = kalan // 3600
        dakika = (kalan % 3600) // 60
        update.message.reply_text(f"⏳ Bonus için bekleme süresi: {saat} saat {dakika} dk")

def bankaparaekle(update: Update, context: CallbackContext):
    try:
        if not context.args:
            update.message.reply_text("🔢 Kullanım: /bankaparaekle <miktar>")
            return
        miktar = int(context.args[0])
        if miktar <= 0:
            update.message.reply_text("❌ Geçerli bir miktar girin.")
            return

        u = get_user(update.effective_user.id)
        if u["bakiye"] >= miktar:
            u["bakiye"] -= miktar
            u["banka"] += miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"🏦 {miktar}₺ bankaya başarıyla yatırıldı!")
        else:
            update.message.reply_text("❌ Yetersiz bakiye.")
    except ValueError:
        update.message.reply_text("❌ Lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/bankaparaekle hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu, lütfen tekrar deneyin.")

def bankaparaçek(update: Update, context: CallbackContext):
    try:
        if not context.args:
            update.message.reply_text("🔢 Kullanım: /bankaparaçek <miktar>")
            return
        miktar = int(context.args[0])
        if miktar <= 0:
            update.message.reply_text("❌ Geçerli bir miktar girin.")
            return

        u = get_user(update.effective_user.id)
        if u["banka"] >= miktar:
            u["banka"] -= miktar
            u["bakiye"] += miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"💳 {miktar}₺ bankadan başarıyla çekildi!")
        else:
            update.message.reply_text("❌ Bankada bu kadar para yok.")
    except ValueError:
        update.message.reply_text("❌ Lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/bankaparaçek hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu, lütfen tekrar deneyin.")

def banka(update: Update, context: CallbackContext): # İç içe olan gereksiz tanım kaldırıldı
    u = get_user(update.effective_user.id)
    data = load_data()
    rates = data.get("exchange_rates", DEFAULT_DATA["exchange_rates"]) # Varsayılanı kullan
    metin = (
        f"🏛️ <b>BANKA & DÖVİZ BİLGİLERİ</b>\n"
        f"💳 Banka Bakiyesi: {u['banka']}₺\n\n"
        f"💱 <b>Güncel Döviz Kurları (Alış/Satış):</b>\n"
        f"💵 Dolar: {rates.get('dolar', '?')}₺\n"
        f"💶 Euro: {rates.get('euro', '?')}₺\n"
        f"💷 Sterlin: {rates.get('sterlin', '?')}₺\n"
        f"💎 Elmas: {rates.get('elmas', '?')}₺"
    )
    update.message.reply_text(metin, parse_mode="HTML")

def dovizal(update: Update, context: CallbackContext):
    try:
        if len(context.args) < 2:
            update.message.reply_text("🔢 Kullanım: /dövizal <tür> <miktar>")
            return
        tur = context.args[0].lower()
        miktar = int(context.args[1])

        if miktar <= 0:
            update.message.reply_text("❌ Alınacak miktar pozitif olmalıdır.")
            return

        data = load_data()
        u = get_user(update.effective_user.id)
        kur = data.get("exchange_rates", {}).get(tur)

        if not kur:
            update.message.reply_text(f"❌ Geçersiz döviz türü: {tur}. Kullanılabilir türler: dolar, euro, sterlin, elmas")
            return

        toplam_maliyet = miktar * kur
        if u["banka"] >= toplam_maliyet:
            u["banka"] -= toplam_maliyet
            u["doviz"][tur] = u["doviz"].get(tur, 0) + miktar
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"✅ {miktar} {tur.upper()} alındı! (🏦 Harcanan: {toplam_maliyet:,.2f}₺)")
        else:
            update.message.reply_text(f"❌ Bankada yeterli para yok! (Gereken: {toplam_maliyet:,.2f}₺)")
    except ValueError:
        update.message.reply_text("❌ Miktar için lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/dövizal hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu.")

def dovizsat(update: Update, context: CallbackContext):
    try:
        if len(context.args) < 2:
            update.message.reply_text("🔢 Kullanım: /dövizsat <tür> <miktar>")
            return
        tur = context.args[0].lower()
        miktar = int(context.args[1])

        if miktar <= 0:
            update.message.reply_text("❌ Satılacak miktar pozitif olmalıdır.")
            return

        data = load_data()
        u = get_user(update.effective_user.id)
        mevcut_doviz = u["doviz"].get(tur, 0)
        kur = data.get("exchange_rates", {}).get(tur)

        if not kur:
            update.message.reply_text(f"❌ Geçersiz döviz türü: {tur}.")
            return

        if mevcut_doviz >= miktar:
            gelir = miktar * kur
            u["doviz"][tur] -= miktar
            u["banka"] += gelir
            set_user(update.effective_user.id, u)
            update.message.reply_text(f"💱 {miktar} {tur.upper()} satıldı! (🏦 Bankaya eklenen: {gelir:,.2f}₺)")
        else:
            update.message.reply_text(f"❌ Elinizde yeterli {tur.upper()} yok! (Mevcut: {mevcut_doviz})")
    except ValueError:
        update.message.reply_text("❌ Miktar için lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/dövizsat hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu.")

def slot(update: Update, context: CallbackContext):
    try:
        if not context.args:
            update.message.reply_text("🔢 Kullanım: /slot <miktar>")
            return
        miktar = int(context.args[0])
        if miktar <= 0:
            update.message.reply_text("❌ Bahis miktarı pozitif olmalıdır.")
            return

        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            update.message.reply_text("💀 Yetersiz bakiye!")
            return

        u["bakiye"] -= miktar
        emojis = ["🍒", "🍉", "🍇", "🍋", "🍓", "7️⃣", "💎"]
        r = [random.choice(emojis) for _ in range(3)]
        sonuc_text = f"{r[0]} | {r[1]} | {r[2]}\n"

        if r[0] == r[1] == r[2]:
            if r[0] == "7️⃣":
                kazanc = miktar * 10
            elif r[0] == "💎":
                kazanc = miktar * 7
            else:
                kazanc = miktar * 5
            u["bakiye"] += kazanc
            sonuc_text += f"🎉 JACKPOT! {kazanc}₺ kazandın! (Net: {kazanc-miktar}₺)"
        elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
            kazanc = miktar * 2
            u["bakiye"] += kazanc
            sonuc_text += f"🎊 İkili geldi! {kazanc}₺ kazandın! (Net: {kazanc-miktar}₺)"
        else:
            sonuc_text += "💀 Kaybettin! Tekrar dene."

        set_user(update.effective_user.id, u)
        update.message.reply_text(sonuc_text)
    except ValueError:
        update.message.reply_text("❌ Miktar için lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/slot hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu.")


def risk(update: Update, context: CallbackContext):
    try:
        if not context.args:
            update.message.reply_text("🔢 Kullanım: /risk <miktar>")
            return
        miktar = int(context.args[0])
        if miktar <= 0:
            update.message.reply_text("❌ Risk miktarı pozitif olmalıdır.")
            return

        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            update.message.reply_text("💀 Yetersiz bakiye!")
            return

        sans = random.randint(1, 100)
        if sans <= 45:  # Kazanma şansı %45 (Bot için küçük bir avantaj)
            u["bakiye"] += miktar # Bahis miktarını ikiye katlar (net kazanç: miktar)
            text = f"🔥 Kazandın! Bakiyene +{miktar}₺ eklendi."
        else:
            u["bakiye"] -= miktar
            text = f"💀 Kaybettin! Bakiyenden -{miktar}₺ eksildi."
        set_user(update.effective_user.id, u)
        update.message.reply_text(text)
    except ValueError:
        update.message.reply_text("❌ Miktar için lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/risk hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu.")

def bahis(update: Update, context: CallbackContext):
    try:
        if not context.args:
            update.message.reply_text("🔢 Kullanım: /bahis <miktar>")
            return
        miktar = int(context.args[0])
        if miktar <= 0:
            update.message.reply_text("❌ Bahis miktarı pozitif olmalıdır.")
            return

        u = get_user(update.effective_user.id)
        if u["bakiye"] < miktar:
            update.message.reply_text("💀 Yetersiz bakiye!")
            return

        # Bahis miktarını burada düşür
        u["bakiye"] -= miktar
        set_user(update.effective_user.id, u)

        takimlar = ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Real Madrid", "Barcelona",
                    "Manchester City", "Liverpool", "Arsenal", "PSG", "Bayern", "Juventus"]
        if len(takimlar) < 3:
            update.message.reply_text("❌ Bahis için yeterli takım bulunmuyor.")
            # Düşülen miktarı iade et
            u["bakiye"] += miktar
            set_user(update.effective_user.id, u)
            return

        secilenler = random.sample(takimlar, 3)
        kazanan = random.choice(secilenler)
        buttons = [
            [InlineKeyboardButton(f"⚽ {team}", callback_data=f"bahis|{team}|{miktar}|{kazanan}")]
            for team in secilenler
        ]
        markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(f"⚽ Takımını seç! Bahis miktarı: {miktar}₺ (Bakiyenden düşüldü)", reply_markup=markup)
    except ValueError:
        update.message.reply_text("❌ Miktar için lütfen sayısal bir değer girin.")
    except Exception as e:
        # Eğer bir hata oluşursa ve para düşüldüyse, iade etmeyi düşünebilirsiniz.
        # Ancak bu callback'e gitmeden önce olduğu için genellikle sorun olmaz.
        logger.error(f"/bahis hatası: {e}")
        update.message.reply_text("❌ Bir hata oluştu.")

def bahis_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        _, secilen_takim, bahis_miktari_str, kazanan_takim = query.data.split("|")
        bahis_miktari = int(bahis_miktari_str) # Bu orijinal bahis miktarıdır
        user_id = query.from_user.id
        u = get_user(user_id)

        if secilen_takim == kazanan_takim:
            # Ödül çarpanı (örn: 3 katı net kazanç, yani bahis miktarı + 3*bahis miktarı = 4*bahis miktarı toplam ödül)
            odul_carpani = 3
            kazanilan_para = bahis_miktari * odul_carpani # Bu net kazançtır
            toplam_odul = bahis_miktari + kazanilan_para # Bahis miktarı geri + net kazanç

            u["bakiye"] += toplam_odul # Bahis miktarı zaten düşülmüştü, şimdi toplam ödül ekleniyor.
            set_user(user_id, u)
            sonuc = f"🏆 Tebrikler! {kazanan_takim} kazandı!\nDoğru tahmin! Hesabına {toplam_odul}₺ eklendi. (Net kazanç: {kazanilan_para}₺)"
        else:
            # Kaybedildiğinde bakiye zaten /bahis komutunda düşülmüştü.
            sonuc = f"💀 Maalesef kaybettin! Kazanan takım: {kazanan_takim}.\nBahis miktarın ({bahis_miktari}₺) kesilmişti."

        query.edit_message_text(sonuc)
    except Exception as e:
        logger.error(f"bahis_callback hatası: {e} - Data: {query.data}")
        query.edit_message_text("❌ Bahis sonucu işlenirken bir hata oluştu.")


def paragönder(update: Update, context: CallbackContext):
    try:
        if len(context.args) < 2:
            update.message.reply_text("🔢 Kullanım: /paragönder <kullanıcı_id> <miktar>")
            return
        hedef_id_str = context.args[0]
        miktar = int(context.args[1])

        if not hedef_id_str.isdigit():
            update.message.reply_text("❌ Kullanıcı ID sayısal olmalıdır.")
            return
        hedef_id = int(hedef_id_str)

        if miktar <= 0:
            update.message.reply_text("❌ Gönderilecek miktar pozitif olmalıdır.")
            return

        gonderen_id = update.effective_user.id
        if hedef_id == gonderen_id:
            update.message.reply_text("❌ Kendine para gönderemezsin.")
            return

        gonderen_user = get_user(gonderen_id)
        if gonderen_user["bakiye"] >= miktar:
            # Hedef kullanıcıyı get_user ile alarak var olmasını sağla
            alici_user = get_user(hedef_id)

            gonderen_user["bakiye"] -= miktar
            alici_user["bakiye"] += miktar

            set_user(gonderen_id, gonderen_user)
            set_user(hedef_id, alici_user)
            update.message.reply_text(f"✅ {hedef_id} ID'li kullanıcıya {miktar}₺ başarıyla gönderildi!")
            # İsteğe bağlı: Hedef kullanıcıya bildirim gönder
            context.bot.send_message(chat_id=hedef_id, text=f"🔔 {gonderen_id} ID'li kullanıcıdan {miktar}₺ aldın!")
        else:
            update.message.reply_text("❌ Yetersiz bakiye!")
    except ValueError:
        update.message.reply_text("❌ Miktar veya ID için lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/paragönder hatası: {e}")
        update.message.reply_text("❌ Para gönderme işlemi sırasında bir hata oluştu.")

def parabasma(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Bu komut sadece adminlere özeldir!")
        return
    try:
        if len(context.args) < 2:
            update.message.reply_text("🔢 Kullanım: /parabasma <kullanıcı_id> <miktar>")
            return
        hedef_id_str = context.args[0]
        miktar = int(context.args[1])

        if not hedef_id_str.isdigit():
            update.message.reply_text("❌ Kullanıcı ID sayısal olmalıdır.")
            return
        hedef_id = int(hedef_id_str)

        # Miktar pozitif veya negatif olabilir (para silme için)
        # if miktar <= 0:
        #     update.message.reply_text("❌ Basılacak miktar pozitif olmalıdır.")
        #     return

        u = get_user(hedef_id) # Hedef kullanıcıyı oluşturur veya yükler
        u["bakiye"] += miktar
        set_user(hedef_id, u)
        islem = "basıldı" if miktar >= 0 else "silindi"
        update.message.reply_text(f"🤑 {hedef_id} ID'li kullanıcıya {abs(miktar)}₺ {islem}!")
    except ValueError:
        update.message.reply_text("❌ Miktar veya ID için lütfen sayısal bir değer girin.")
    except Exception as e:
        logger.error(f"/parabasma hatası: {e}")
        update.message.reply_text("❌ Para basma işlemi sırasında bir hata oluştu.")

def admin(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Bu komut sadece sabit admin veya yetkili adminlere özeldir!")
        return
    try:
        if not context.args:
            update.message.reply_text("🔢 Kullanım: /admin <kullanıcı_id>")
            return
        yeni_admin_id = str(context.args[0])
        if not yeni_admin_id.isdigit():
            update.message.reply_text("❌ Admin ID sayısal olmalıdır.")
            return

        data = load_data()
        if yeni_admin_id not in data["admins"]:
            data["admins"].append(yeni_admin_id)
            save_data(data)
            update.message.reply_text(f"👑 {yeni_admin_id} ID'li kullanıcı artık admin!")
        else:
            update.message.reply_text("⚠️ Bu kullanıcı zaten admin yetkisine sahip.")
    except Exception as e:
        logger.error(f"/admin hatası: {e}")
        update.message.reply_text("❌ Admin ekleme işlemi sırasında bir hata oluştu.")

def id(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        hedef = update.message.reply_to_message.from_user
        update.message.reply_text(f"🆔 {hedef.full_name} kullanıcısının ID'si: {hedef.id}")
    else:
        update.message.reply_text(f"🆔 Senin Telegram ID'n: {update.effective_user.id}")

def top(update: Update, context: CallbackContext):
    data = load_data()
    if not data["users"]:
        update.message.reply_text("🏆 Henüz sıralamaya girecek kullanıcı yok.")
        return

    # Kullanıcıları toplam varlıklarına göre sırala (bakiye + banka)
    # (uid, user_data) çiftlerinden oluşan bir liste al
    kullanici_listesi = list(data["users"].items())
    sirali_kullanicilar = sorted(
        kullanici_listesi,
        key=lambda item: item[1].get("bakiye", 0) + item[1].get("banka", 0),
        reverse=True
    )

    metin = "🏆 <b>En Zenginler Listesi (Top 10)</b>\n\n"
    for i, (uid, user_data) in enumerate(sirali_kullanicilar[:10], 1):
        toplam_varlik = user_data.get("bakiye", 0) + user_data.get("banka", 0)
        # Kullanıcı adını veya ID'yi göstermek için bir mantık eklenebilir.
        # Şimdilik sadece ID'yi gösteriyoruz.
        metin += f"{i}. 👤 <code>{uid}</code> • Toplam: {toplam_varlik:,.0f}₺\n"

    update.message.reply_text(metin, parse_mode="HTML")

# Bu fonksiyon global kapsama taşındı
def komutlar(update: Update, context: CallbackContext):
    admin_komutlari = ""
    if is_admin(update.effective_user.id):
        admin_komutlari = (
            "\n🔧 <b>Admin Komutları:</b>\n"
            "🤑 /parabasma <id> <miktar> - Kullanıcıya para basar/siler\n"
            "👑 /admin <id> - Kullanıcıya admin yetkisi verir\n"
            "🛠️ /kurayarla <tür> <değer> - Döviz kurunu ayarlar (dolar, euro, sterlin, elmas)"
        )

    text = (
        "📜 <b>Kullanılabilir Komutlar Listesi</b>\n\n"
        "🟢 /start - Botu başlatır ve başlangıç bakiyesi verir.\n"
        "💸 /bakiye - Mevcut bakiye, banka ve dövizlerinizi gösterir.\n"
        "🎁 /bonus - 24 saatte bir rastgele bonus verir.\n"
        "🏦 /bankaparaekle <miktar> - Bakiyenizden bankaya para yatırır.\n"
        "💳 /bankaparaçek <miktar> - Bankadan bakiyenize para çeker.\n"
        "🏛️ /banka - Banka ve güncel döviz kurlarını gösterir.\n"
        "💱 /dövizal <tür> <miktar> - Bankadaki paranızla döviz satın alır.\n"
        "💵 /dövizsat <tür> <miktar> - Sahip olduğunuz dövizi satıp bankaya aktarır.\n"
        "🎰 /slot <miktar> - Slot makinesinde şansınızı dener.\n"
        "☠️ /risk <miktar> - %45 şansla miktarınızı ikiye katlar veya kaybedersiniz.\n"
        "⚽ /bahis <miktar> - 3 takım arasından doğru olanı tahmin etmeye çalışırsınız.\n"
        "🧾 /paragönder <id> <miktar> - Başka bir kullanıcıya para gönderir.\n"
        "🆔 /id - Kendi Telegram ID'nizi veya yanıtladığınız kişinin ID'sini gösterir.\n"
        "🏆 /top - En zengin 10 kullanıcıyı listeler.\n"
        f"{admin_komutlari}"
    )
    update.message.reply_text(text, parse_mode="HTML")

def kurayarla(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Bu komut sadece adminlere özeldir!")
        return
    try:
        if len(context.args) < 2:
            update.message.reply_text("🔢 Kullanım: /kurayarla <tür> <yeni_kur>\nÖrnek: /kurayarla dolar 25.5")
            return

        tur = context.args[0].lower()
        yeni_kur_str = context.args[1].replace(',', '.') # Virgülü noktaya çevir
        yeni_kur = float(yeni_kur_str)

        if yeni_kur <= 0:
            update.message.reply_text("❌ Kur değeri pozitif olmalıdır.")
            return

        data = load_data()
        if tur not in data.get("exchange_rates", {}):
            update.message.reply_text(f"❌ Geçersiz döviz türü: {tur}. Kullanılabilir: dolar, euro, sterlin, elmas")
            return

        data["exchange_rates"][tur] = yeni_kur
        save_data(data)
        update.message.reply_text(f"✅ {tur.upper()} kuru başarıyla {yeni_kur}₺ olarak ayarlandı.")

    except ValueError:
        update.message.reply_text("❌ Kur değeri için lütfen geçerli bir sayı girin.")
    except Exception as e:
        logger.error(f"/kurayarla hatası: {e}")
        update.message.reply_text("❌ Kur ayarlama işlemi sırasında bir hata oluştu.")


def main():
    # Bot ilk çalıştığında veri dosyasını kontrol et/oluştur
    logger.info("Bot başlatılıyor, veri dosyası kontrol ediliyor...")
    load_data()
    logger.info("Veri dosyası hazır.")

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Komutlar
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("bakiye", bakiye))
    dp.add_handler(CommandHandler("bonus", bonus))
    dp.add_handler(CommandHandler("bankaparaekle", bankaparaekle))
    dp.add_handler(CommandHandler("bankaparaçek", bankaparaçek))
    dp.add_handler(CommandHandler("banka", banka))
    dp.add_handler(CommandHandler("komutlar", komutlar)) # Artık doğru yerde
    dp.add_handler(CommandHandler("dövizal", dovizal))
    dp.add_handler(CommandHandler("dövizsat", dovizsat))
    dp.add_handler(CommandHandler("slot", slot))
    dp.add_handler(CommandHandler("risk", risk))
    dp.add_handler(CommandHandler("bahis", bahis))
    dp.add_handler(CallbackQueryHandler(bahis_callback, pattern="^bahis\\|"))
    dp.add_handler(CommandHandler("paragönder", paragönder))
    # Admin Komutları
    dp.add_handler(CommandHandler("parabasma", parabasma))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("kurayarla", kurayarla)) # Yeni komut eklendi
    # Diğer
    dp.add_handler(CommandHandler("id", id))
    dp.add_handler(CommandHandler("top", top))

    logger.info("Bot polling modunda başlatıldı.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
        
