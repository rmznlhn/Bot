import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Railway ortam değişkeninden tokeni al
TOKEN = os.environ.get("BOT_TOKEN")

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! 👋\nBen senin Telegram botunum.\nTüm komutları görmek için /help yaz."
    )

# /help komutu
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📜 Kullanılabilir Komutlar:\n"
        "/start - Botu başlatır\n"
        "/help - Bu komut listesini gösterir\n"
        "/merhaba - Sana selam verir\n"
    )
    await update.message.reply_text(help_text)

# /merhaba komutu
async def merhaba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! 😊 Nasılsın?")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("merhaba", merhaba))

    print("Bot çalışıyor...")
    app.run_polling()
