import os
import re
import json
import asyncio
import requests
from bs4 import BeautifulSoup

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# ───────── Ayarlar ─────────
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Opsiyonel: fiyat düşüşü bildirimi için

# ───────── JSON Yardımcıları ─────────
def urunler_yukle():
    try:
        with open("urunler.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def urunler_kaydet(urunler):
    with open("urunler.json", "w", encoding="utf-8") as f:
        json.dump(urunler, f, ensure_ascii=False)

# ───────── Metin → sayı yardımcı ─────────
def metinden_sayi_al(metin: str):
    if not metin:
        return None
    # 12.999,90 → 12999.90 gibi normalize edelim
    temiz = metin.strip()
    temiz = temiz.replace("\xa0", " ")  # non-breaking space
    # Parayı/para birimini, harfleri temizle
    temiz = re.sub(r"[^\d,\.]", "", temiz)
    # Türk formatını yakalamak için: önce nokta binlik ayırıcılarını sil, sonra virgülü noktaya çevir
    if "," in temiz and temiz.count(",") == 1 and (temiz.rfind(",") > temiz.rfind(".")):
        temiz = temiz.replace(".", "")
        temiz = temiz.replace(",", ".")
    try:
        return float(temiz)
    except:
        return None

# ───────── Hızlı (requests) dene ─────────
def hepsiburada_statikten_fiyat(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Birkaç yaygın seçici dene
        adaylar = [
            ("span", {"class": "price-value"}),
            ("span", {"class": "value"}),
            ("meta", {"itemprop": "price"}),
            ("meta", {"property": "product:price:amount"}),
        ]
        for tag, attrs in adaylar:
            el = soup.find(tag, attrs=attrs)
            if el:
                # meta ise content, değilse text
                icerik = el.get("content") if tag == "meta" else el.get_text()
                sayi = metinden_sayi_al(icerik)
                if sayi:
                    return sayi
        return None
    except:
        return None

# ───────── Selenium (headless Chromium) ─────────
# Railway’de Aptfile ile chromium + chromium-driver kuruyoruz.
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def selenium_ile_fiyat(url: str):
    try:
        chrome_opts = Options()
        # Yeni headless
        chrome_opts.add_argument("--headless=new")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--window-size=1920,1080")
        chrome_opts.binary_location = "/usr/bin/chromium"  # Aptfile ile gelecek

        service = Service("/usr/bin/chromedriver")  # Aptfile ile gelecek
        driver = webdriver.Chrome(service=service, options=chrome_opts)
        driver.get(url)

        # En yaygın seçiciler – biri bulunana kadar sırayla dene
        seciciler = [
            (By.CSS_SELECTOR, "span.price-value"),
            (By.CSS_SELECTOR, "span.value"),
            (By.CSS_SELECTOR, "meta[itemprop='price']"),
            (By.CSS_SELECTOR, "meta[property='product:price:amount']"),
        ]

        fiyat_metin = None
        for by, sel in seciciler:
            try:
                elem = WebDriverWait(driver, 15).until(EC.presence_of_element_located((by, sel)))
                if elem.tag_name.lower() == "meta":
                    fiyat_metin = elem.get_attribute("content")
                else:
                    fiyat_metin = elem.text
                if fiyat_metin:
                    break
            except:
                continue

        driver.quit()

        return metinden_sayi_al(fiyat_metin) if fiyat_metin else None
    except:
        try:
            driver.quit()
        except:
            pass
        return None

# ───────── Fiyat çekme (önce hızlı, sonra garanti) ─────────
def urun_fiyati_al(url: str):
    # 1) Statik HTML denemesi (hızlı)
    f = hepsiburada_statikten_fiyat(url)
    if f:
        return f
    # 2) Selenium fallback (garanti)
    return selenium_ile_fiyat(url)

# ───────── Telegram Komutları ─────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tus = [[InlineKeyboardButton("Bilgi Al", callback_data="bilgi")]]
    await update.message.reply_text("Merhaba! Bot çalışıyor ✅", reply_markup=InlineKeyboardMarkup(tus))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "bilgi":
        await q.edit_message_text("Inline buton çalışıyor!")

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yazi = update.message.text or ""
    urunler = urunler_yukle()

    # /ekle ÜrünAdi URL
    if yazi.lower().startswith("/ekle"):
        try:
            parcalar = yazi.split(maxsplit=2)
            if len(parcalar) < 3:
                await update.message.reply_text("Hatalı kullanım. Örnek: /ekle ÜrünAdı URL")
                return
            urun_adi = parcalar[1]
            urun_url = parcalar[2]
            urunler[urun_adi] = {"url": urun_url, "fiyat": None}
            urunler_kaydet(urunler)
            await update.message.reply_text(f"{urun_adi} başarıyla eklendi!")
        except:
            await update.message.reply_text("Hata oluştu, tekrar deneyin.")
        return

    # Basit sohbet / fiyat
    alt = yazi.lower()
    if "merhaba" in alt:
        await update.message.reply_text("Merhaba! Nasılsın?")
    elif "fiyat" in alt:
        cevap = []
        for ad, veriler in urunler.items():
            f = urun_fiyati_al(veriler["url"])
            if f:
                cevap.append(f"{ad}: {f} TL")
        await update.message.reply_text("\n".join(cevap) if cevap else "Fiyat alınamadı.")

# ───────── Otomatik kontrol ─────────
async def otomatik_kontrol(app):
    await asyncio.sleep(5)
    while True:
        urunler = urunler_yukle()
        degisti = False
        for ad, veriler in urunler.items():
            yeni = urun_fiyati_al(veriler["url"])
            if yeni:
                eski = veriler.get("fiyat")
                if eski and yeni < eski and CHAT_ID:
                    try:
                        await app.bot.send_message(CHAT_ID, f"{ad} fiyatı düştü! Yeni fiyat: {yeni} TL (Eski: {eski} TL)")
                    except:
                        pass
                veriler["fiyat"] = yeni
                degisti = True
        if degisti:
            urunler_kaydet(urunler)
        await asyncio.sleep(60)  # 1 dk

# ───────── Çalıştır ─────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
    app.add_handler(CallbackQueryHandler(button))

    # Arkaplanda otomatik takip
    app.job_queue.run_once(lambda ctx: asyncio.create_task(otomatik_kontrol(app)), when=0)

    print("Bot çalışıyor...")
    app.run_polling()
