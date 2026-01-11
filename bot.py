import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from pymongo import MongoClient

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN or not MONGO_URI:
    raise RuntimeError("Missing environment variables")

# ================= MONGO =================
mongo = MongoClient(MONGO_URI)
db = mongo.animebot
episodes = db.episodes

# ================= MEMORY =================
LAST_DOC = {}        # forwarded document file_id
LAST_CLONED = {}     # cloned (bot-owned) file_id

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 AKUKAMI Anime Bot\n\n"
        "1️⃣ Forward a DOCUMENT file\n"
        "2️⃣ Send /clone\n"
        "3️⃣ Send /add <episode> <quality>\n\n"
        "Example:\n/add 1 720p"
    )

async def capture_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        user_id = update.effective_user.id
        LAST_DOC[user_id] = update.message.document.file_id

        await update.message.reply_text(
            "✅ Document received.\n"
            "Now send /clone"
        )

async def clone_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in LAST_DOC:
        await update.message.reply_text(
            "❌ Forward a DOCUMENT file first."
        )
        return

    sent = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=LAST_DOC[user_id]
    )

    new_file_id = sent.document.file_id
    LAST_CLONED[user_id] = new_file_id

    await update.message.reply_text(
        "♻️ File cloned successfully!\n\n"
        "Now store it using:\n"
        "`/add <episode> <quality>`\n"
        "Example: `/add 1 720p`",
        parse_mode="Markdown"
    )

async def add_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if user_id not in LAST_CLONED:
        await update.message.reply_text(
            "❌ Clone a file first using /clone"
        )
        return

    if len(args) != 2:
        await update.message.reply_text(
            "❌ Usage:\n/add <episode> <quality>\nExample: /add 1 720p"
        )
        return

    try:
        episode_no = int(args[0])
        quality = args[1]
    except ValueError:
        await update.message.reply_text("❌ Episode must be a number")
        return

    episodes.insert_one({
        "anime": "Classroom of the Elite",
        "season": 1,
        "episode": episode_no,
        "quality": quality,
        "file_id": LAST_CLONED[user_id]
    })

    await update.message.reply_text(
        f"✅ Stored successfully!\n\n"
        f"Anime: Classroom of the Elite\n"
        f"Season: 1\n"
        f"Episode: {episode_no}\n"
        f"Quality: {quality}"
    )

# ================= HTTP SERVER =================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, capture_document))
    app.add_handler(CommandHandler("clone", clone_document))
    app.add_handler(CommandHandler("add", add_episode))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
