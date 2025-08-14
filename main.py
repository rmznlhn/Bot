import os
import requests
import asyncio
import json
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Telegram chat ID

# Ürünleri JSON dosyasından yükle/kaydet
def urunler_yukle():
    try:
        with open("urunler.json", "r") as f:
            return json.load(f)
    except:
        return {}

def urunler_kaydet(urunler):
    with open("urunler.json", "w") as f:
        json.dump(urunler, f)

# Fiyat çekme fonksiyonu
def urun_fiyati_al(url):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        fiyat_tag = soup.find("span", class_="price-value")  # Hepsiburada örnek
        if fiyat_tag:
            fiyat = fiyat_tag.text.replace(".", "").replace(",", ".").strip()
            return float(fiyat)
        return None
    except:
        return None

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Bilgi Al", callback_data='bilgi')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Merhaba! Bot çalışıyor ✅", reply_markup=reply_markup)

# Inline buton callback
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'bilgi':
        await query.edit_message_text("Inline buton çalışıyor!")

# Kullanıcı mesajlarına cevap ve ürün ekleme
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    urunler = urunler_yukle()

    # /ekle komutu
    if text.lower().startswith("/ekle"):
        try:
            _, urun_ad, urun_url = text.split(maxsplit=2)
            urunler[urun_ad] = {"url": urun_url, "fiyat": None}
            urunler_kaydet(urunler)
            await update.message.reply_text(f"{urun_ad} başarıyla eklendi!")
        except:
            await update.message.reply_text("Hatalı kullanım. Örnek: /ekle ÜrünAdı URL")
        return

    # Normal mesaj cevapları
    text_lower = text.lower()
    if "merhaba" in text_lower:
        await update.message.reply_text("Merhaba! Nasılsın?")
    elif "fiyat" in text_lower:
        mesaj_text = ""
        for ad, veriler in urunler.items():
            fiyat = urun_fiyati_al(veriler["url"])
            if fiyat:
                mesaj_text += f"{ad}: {fiyat} TL\n"
        await update.message.reply_text(mesaj_text if mesaj_text else "Fiyat alınamadı.")

# Otomatik fiyat kontrolü
async def otomatik_kontrol(app):
    await asyncio.sleep(5)
    while True:
        urunler = urunler_yukle()
        for ad, veriler in urunler.items():
            yeni_fiyat = urun_fiyati_al(veriler["url"])
            if yeni_fiyat:
                eski_fiyat = veriler["fiyat"]
                if eski_fiyat and yeni_fiyat < eski_fiyat:
                    await app.bot.send_message(CHAT_ID, f"{ad} fiyatı düştü!\nYeni fiyat: {yeni_fiyat} TL")
                veriler["fiyat"] = yeni_fiyat
        urunler_kaydet(urunler)
        await asyncio.sleep(60)  # 1 dakika aralık

# Bot başlat
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Handler eklemeleri
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
    app.add_handler(CallbackQueryHandler(button))

    # Fiyat takibi başlat
    app.job_queue.run_once(lambda ctx: asyncio.create_task(otomatik_kontrol(app)), when=0)

    print("Bot çalışıyor...")
    app.run_polling()
