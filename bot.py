import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from pymongo import MongoClient

BOT_TOKEN = os.getenv("7543377011:AAFPhEM3rhC-T0yPpvJ9xXejatjCv39zT9o")
MONGO_URI = os.getenv("mongodb+srv://akukamibot:%3A%40kum%40d3v0g@cluster0.bgfgveu.mongodb.net/?appName=Cluster0")

client = MongoClient(MONGO_URI)
db = client.animebot

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot is alive!\nMongoDB connected.\nMore features coming soon."
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
