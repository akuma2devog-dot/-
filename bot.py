import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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

# ========== ADMIN ==========
ADMIN_IDS = [6028405107]  # 🔴 replace with YOUR Telegram user ID

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ========== DB ==========
client = MongoClient(MONGO_URI)
db = client.animebot
episodes = db.episodes
config = db.config  # for thumbnail

# ========== GLOBAL STATES ==========
BULK_STATE = {}   # per admin
SET_THUMB_WAIT = set()

# ========== HELPERS ==========
def get_thumbnail_file_id():
    doc = config.find_one({"_id": "thumbnail"})
    return doc["file_id"] if doc else None

def set_thumbnail_file_id(file_id):
    config.update_one(
        {"_id": "thumbnail"},
        {"$set": {"file_id": file_id}},
        upsert=True
    )

# ========== TELEGRAM HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Use channel buttons to get anime.\n"
        "Admins can use /admin."
    )

# ---------- ADMIN PANEL ----------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    kb = [
        [InlineKeyboardButton("📦 Start Bulk Upload", callback_data="admin_bulk")],
        [InlineKeyboardButton("🛑 Stop Bulk Upload", callback_data="admin_done")],
        [InlineKeyboardButton("🖼️ Change Thumbnail", callback_data="admin_setthumb")],
        [InlineKeyboardButton("ℹ️ Mongo Status", callback_data="admin_mongo")]
    ]
    await update.message.reply_text(
        "👑 Admin Panel",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_admin(q.from_user.id):
        return

    if q.data == "admin_bulk":
        await q.message.reply_text(
            "Start bulk upload:\n"
            "`/bulk <ANIME> <SEASON> <QUALITY>`\n\n"
            "Example:\n`/bulk COTE 1 480p`",
            parse_mode="Markdown"
        )

    elif q.data == "admin_done":
        await done_bulk(update, context)

    elif q.data == "admin_setthumb":
        SET_THUMB_WAIT.add(q.from_user.id)
        await q.message.reply_text("Send the new thumbnail image.")

    elif q.data == "admin_mongo":
        try:
            db.command("ping")
            count = episodes.count_documents({})
            await q.message.reply_text(
                f"✅ MongoDB connected\n📦 Episodes stored: {count}"
            )
        except Exception as e:
            await q.message.reply_text(f"❌ Mongo error:\n{e}")

# ---------- SET THUMB ----------
async def receive_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in SET_THUMB_WAIT:
        return
    if not is_admin(uid):
        return
    if not update.message.photo:
        return

    file_id = update.message.photo[-1].file_id
    set_thumbnail_file_id(file_id)
    SET_THUMB_WAIT.remove(uid)

    await update.message.reply_text("✅ Thumbnail updated")

# ---------- BULK ----------
async def bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            "Usage:\n/bulk <ANIME> <SEASON> <QUALITY>"
        )
        return

    anime, season, quality = context.args
    BULK_STATE[update.effective_user.id] = {
        "anime": anime.upper(),
        "season": int(season),
        "quality": quality,
        "episode": 1
    }

    await update.message.reply_text(
        f"📦 Bulk upload started\n\n"
        f"Anime: {anime.upper()}\n"
        f"Season: {season}\n"
        f"Quality: {quality}\n\n"
        f"➡️ Send Episode 1 (DOCUMENT)"
    )

async def done_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return

    if uid not in BULK_STATE:
        await update.message.reply_text("❌ Bulk mode not active.")
        return

    state = BULK_STATE.pop(uid)
    await update.message.reply_text(
        f"🎉 Bulk upload completed\n\n"
        f"{state['anime']} – Season {state['season']} – {state['quality']}"
    )

# ---------- DOCUMENT HANDLER (AUTO CLONE + SAVE) ----------
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in BULK_STATE:
        return
    if not is_admin(uid):
        return

    state = BULK_STATE[uid]
    ep = state["episode"]

    thumb = get_thumbnail_file_id()

    sent = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=update.message.document.file_id,
        filename=f"{state['anime']} S{state['season']:02}E{ep:02} {state['quality']}.mkv",
        thumbnail=thumb
    )

    episodes.insert_one({
        "anime": state["anime"],
        "season": state["season"],
        "episode": ep,
        "quality": state["quality"],
        "file_id": sent.document.file_id
    })

    state["episode"] += 1

    await update.message.reply_text(
        f"✅ Episode {ep} added\n➡️ Send next file"
    )

# ========== HTTP (RENDER KEEPALIVE) ==========
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
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_buttons))
    app.add_handler(CommandHandler("bulk", bulk_start))
    app.add_handler(CommandHandler("done", done_bulk))

    app.add_handler(MessageHandler(filters.PHOTO, receive_thumbnail))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
