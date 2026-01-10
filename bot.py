import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

# ========== TELEGRAM COMMANDS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 Forward me a DOCUMENT file\n"
        "Then send /clone\n\n"
        "I will give you a usable FILE_ID."
    )

async def clone_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        doc = update.message.document

        # Re-send document to generate NEW file_id
        sent = await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=doc.file_id
        )

        new_file_id = sent.document.file_id

        await update.message.reply_text(
            "♻️ File cloned successfully!\n\n"
            f"🆔 NEW FILE_ID:\n{new_file_id}"
        )
    else:
        await update.message.reply_text(
            "❌ Forward a DOCUMENT file first, then send /clone"
        )

# ========== HTTP SERVER (Render Web Service fix) ==========

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
    app.add_handler(CommandHandler("clone", clone_document))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
