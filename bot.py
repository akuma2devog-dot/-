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

# ========== ENV ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN or not MONGO_URI:
    raise RuntimeError("Missing environment variables")

# ========== DB ==========
client = MongoClient(MONGO_URI)
db = client.animebot
episodes = db.episodes

# Store last cloned file per user
LAST_DOC = {}

# ========== TELEGRAM ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 Forward a DOCUMENT file\n"
        "Then send /clone\n\n"
        "Store it using:\n"
        "/add <episode> <quality>\n\n"
        "Example:\n/add 1 480p"
    )

async def capture_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        user_id = update.effective_user.id
        LAST_DOC[user_id] = update.message.document.file_id
        await update.message.reply_text("✅ Document received. Now send /clone")

async def clone_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in LAST_DOC:
        await update.message.reply_text("❌ Forward a document first.")
        return

    sent = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=LAST_DOC[user_id]
    )

    LAST_DOC[user_id] = sent.document.file_id

    await update.message.reply_text(
        "♻️ File cloned successfully!\n\n"
        "Now store it:\n/add <episode> <quality>"
    )

async def add_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /add <episode> <quality>")
        return

    user_id = update.effective_user.id
    if user_id not in LAST_DOC:
        await update.message.reply_text("❌ Clone a file first.")
        return

    ep = int(context.args[0])
    quality = context.args[1]

    episodes.update_one(
        {"episode": ep, "quality": quality},
        {"$set": {"file_id": LAST_DOC[user_id]}},
        upsert=True
    )

    await update.message.reply_text(
        f"✅ Stored Episode {ep} ({quality})"
    )

async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /get <episode> <quality>")
        return

    ep = int(context.args[0])
    quality = context.args[1]

    data = episodes.find_one({"episode": ep, "quality": quality})

    if not data:
        await update.message.reply_text("❌ Episode not found.")
        return

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=data["file_id"]
    )
async def mongo_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db.command("ping")
        count = episodes.count_documents({})
        await update.message.reply_text(
            f"✅ MongoDB connected\n📦 Episodes stored: {count}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ MongoDB error:\n{str(e)}"
        )
# ========== HTTP ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, capture_document))
    app.add_handler(CommandHandler("clone", clone_document))
    app.add_handler(CommandHandler("add", add_episode))
    app.add_handler(CommandHandler("get", get_episode))
    app.add_handler(CommandHandler("mongotest", mongo_test))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
