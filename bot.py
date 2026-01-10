import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("7543377011:AAEekT4reRGc-Nyci5cqoi2v9_F-0wA4FT4")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive (test mode).")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
