from telegram.ext import Application, CommandHandler
import asyncio

TOKEN = "8350284060:AAELTkDNIEt_oWP-ZXYDRlo_eBSofz2cziA"

async def start(update, context):
    await update.message.reply_text("Merhaba! Bot çalışıyor 🚀")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

asyncio.run(main())
