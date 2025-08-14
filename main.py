import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token'i Railway Environment Variables'dan al
TOKEN = os.environ.get("BOT_TOKEN")

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Bot çalışıyor ✅")

# Botu çalıştır
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot başladı...")
    app.run_polling()
