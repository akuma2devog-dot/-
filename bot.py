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

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

# Store last document per user
LAST_DOC = {}

# ========== TELEGRAM HANDLERS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 Forward me a DOCUMENT file\n"
        "Then send /clone\n\n"
        "I will give you a usable FILE_ID."
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
            "❌ No document found.\n"
            "Forward a DOCUMENT file first."
        )
        return

    original_file_id = LAST_DOC[user_id]

    sent = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=original_file_id
    )

    new_file_id = sent.document.file_id

    await update.message.reply_text(
        "♻️ File cloned successfully!\n\n"
        f"🆔 NEW FILE_ID:\n{new_file_id}"
    )

# ========== HTTP SERVER (Render Web Service) ==========

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

# ========== MAIN ==========

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, capture_document))
    app.add_handler(CommandHandler("clone", clone_document))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
