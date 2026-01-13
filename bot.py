import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import BOT_TOKEN, PORT
from utils import *

# ---------- HTTP SERVER ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()

# ---------- MAIN ----------
def main():
    # Start HTTP server in background
    threading.Thread(target=run_server, daemon=True).start()

    # Telegram bot MUST run in main thread
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("bulk", bulk_start))
    app.add_handler(CommandHandler("done", bulk_done))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("delete", delete_season))
    app.add_handler(CommandHandler("reupload", reupload))
    app.add_handler(CommandHandler("mongostatus", mongostatus))
    app.add_handler(CommandHandler("get", get_episode))
    app.add_handler(CommandHandler("settemplate", settemplate))

    # Buttons
    app.add_handler(CallbackQueryHandler(admin_buttons))

    # Media
    app.add_handler(MessageHandler(filters.PHOTO, receive_thumb))

    print("🤖 Bot started correctly")
    app.run_polling(
        allowed_updates=["message", "callback_query"]
    )

if __name__ == "__main__":
    main()
