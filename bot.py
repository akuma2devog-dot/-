import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN, PORT

from utils import (
    start,
    admin_panel,
    admin_buttons,
    bulk_start,
    bulk_done,
    preview,
    delete_season,
    reupload,
    mongostatus,
    get_episode,
    receive_thumb,
    settemplate,
)

# ---------- HTTP SERVER (UptimeRobot) ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.add_handler(CommandHandler("bulk", bulk_start))
    app.add_handler(CommandHandler("done", bulk_done))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("delete", delete_season))
    app.add_handler(CommandHandler("reupload", reupload))
    app.add_handler(CommandHandler("mongostatus", mongostatus))
    app.add_handler(CommandHandler("get", get_episode))
    app.add_handler(CommandHandler("settemplate", settemplate))

    # Media
    app.add_handler(MessageHandler(filters.PHOTO, receive_thumb))

    print("🚀 Bot started successfully (rename disabled)")
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    main()
