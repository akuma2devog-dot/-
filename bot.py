import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from pymongo import MongoClient

# ===== Environment variables =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

if not BOT_TOKEN or not MONGO_URI:
    raise RuntimeError("Missing environment variables")

# ===== MongoDB connection (ready for later use) =====
client = MongoClient(MONGO_URI)
db = client.animebot
anime_col = db.anime

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to AKUKAMI Anime Bot\n\n"
        "Use channel buttons to get episodes."
    )

# STEP 1: Get DOCUMENT file_id
async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name

        await update.message.reply_text(
            f"📁 Document received\n\n"
            f"📄 File name:\n{file_name}\n\n"
            f"🆔 FILE_ID:\n{file_id}"
        )
    else:
        await update.message.reply_text(
            "❌ Please upload the episode as a DOCUMENT file."
        )

# ===== Main =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fileid", get_file_id))

    app.run_polling()

if __name__ == "__main__":
    main()
