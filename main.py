import os
import asyncio
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Railway Environment Variable'dan token al
TOKEN = os.environ.get("BOT_TOKEN")
WEATHER_API = os.environ.get("WEATHER_API", "https://wttr.in")

# Notlar dosyası
NOTLAR_DOSYA = "notlar.json"

# Notları yükle
def notlari_yukle():
    if os.path.exists(NOTLAR_DOSYA):
        with open(NOTLAR_DOSYA, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Notları kaydet
def notlari_kaydet(notlar):
    with open(NOTLAR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(notlar, f, ensure_ascii=False, indent=2)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Komutlar için /help yazabilirsin ✅")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = (
        "📌 Komutlar:\n"
        "/notekle [metin] - Yeni not ekle\n"
        "/notlar - Tüm notları listele\n"
        "/notsil [numara] - Belirtilen numaradaki notu sil\n"
        "/hatirlat [dakika] [mesaj] - Belirtilen dakika sonra hatırlat\n"
        "/hava [şehir] - Anlık hava durumu\n"
    )
    await update.message.reply_text(mesaj)

# /notekle
async def notekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen eklemek istediğin notu yaz.")
        return
    notlar = notlari_yukle()
    not_metni = " ".join(context.args)
    notlar.append(not_metni)
    notlari_kaydet(notlar)
    await update.message.reply_text(f"✅ Not eklendi: {not_metni}")

# /notlar
async def notlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notlar = notlari_yukle()
    if not notlar:
        await update.message.reply_text("📭 Henüz not yok.")
        return
    mesaj = "\n".join([f"{i+1}. {n}" for i, n in enumerate(notlar)])
    await update.message.reply_text(mesaj)

# /notsil
async def notsil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Silmek istediğin not numarasını yazmalısın.")
        return
    index = int(context.args[0]) - 1
    notlar = notlari_yukle()
    if 0 <= index < len(notlar):
        silinen = notlar.pop(index)
        notlari_kaydet(notlar)
        await update.message.reply_text(f"🗑 Silindi: {silinen}")
    else:
        await update.message.reply_text("❌ Geçersiz not numarası.")

# /hatirlat
async def hatirlat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.message.reply_text("Kullanım: /hatirlat [dakika] [mesaj]")
        return
    dakika = int(context.args[0])
    mesaj = " ".join(context.args[1:])
    await update.message.reply_text(f"⏳ {dakika} dakika sonra hatırlatılacak: {mesaj}")
    await asyncio.sleep(dakika * 60)
    await update.message.reply_text(f"🔔 Hatırlatma: {mesaj}")

# /hava
async def hava(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen şehir adı yaz.")
        return
    sehir = " ".join(context.args)
    try:
        url = f"{WEATHER_API}/{sehir}?format=3&lang=tr"
        yanit = requests.get(url).text
        await update.message.reply_text(f"🌤 {yanit}")
    except:
        await update.message.reply_text("❌ Hava durumu alınamadı.")

# Botu başlat
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("notekle", notekle))
app.add_handler(CommandHandler("notlar", notlar))
app.add_handler(CommandHandler("notsil", notsil))
app.add_handler(CommandHandler("hatirlat", hatirlat))
app.add_handler(CommandHandler("hava", hava))

if __name__ == "__main__":
    print("🤖 Bot çalışıyor...")
    app.run_polling()
