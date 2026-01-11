import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
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
ADMIN_IDS = [6028405107]

def is_admin(uid):
    return uid in ADMIN_IDS

# ========== DB ==========
client = MongoClient(MONGO_URI)
db = client.animebot
episodes = db.episodes
config = db.config

# ========== STATES ==========
BULK_STATE = {}
REUPLOAD_STATE = {}
SET_THUMB_WAIT = set()

# ========== HELPERS ==========
def get_thumb():
    d = config.find_one({"_id": "thumb"})
    return d["file_id"] if d else None

def set_thumb(fid):
    config.update_one({"_id": "thumb"}, {"$set": {"file_id": fid}}, upsert=True)

def build_filename(season, episode):
    return f"S{season}E{episode} @anifindX.mkv"

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Use channel buttons to get anime.\n"
        "Admins can use /admin"
    )

# ========== ADMIN PANEL ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    kb = [
        [InlineKeyboardButton("📦 Start Bulk Upload", callback_data="admin_bulk")],
        [InlineKeyboardButton("🛑 Stop Bulk Upload", callback_data="admin_done")],
        [InlineKeyboardButton("👁 Preview Episodes", callback_data="admin_preview")],
        [InlineKeyboardButton("♻ Reupload Episode", callback_data="admin_reupload")],
        [InlineKeyboardButton("🗑 Delete Season", callback_data="admin_delete")],
        [InlineKeyboardButton("🖼 Change Thumbnail", callback_data="admin_thumb")],
        [InlineKeyboardButton("📊 Mongo Status", callback_data="admin_mongo")]
    ]

    await update.message.reply_text(
        "👑 **Admin Panel**",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_admin(q.from_user.id):
        return

    if q.data == "admin_bulk":
        await q.message.reply_text("Use:\n/bulk <ANIME> <SEASON> <QUALITY>")

    elif q.data == "admin_done":
        await bulk_done(update, context)

    elif q.data == "admin_preview":
        await q.message.reply_text("Use:\n/preview <ANIME> <SEASON> <QUALITY>")

    elif q.data == "admin_reupload":
        await q.message.reply_text(
            "Use:\n/reupload <ANIME> <SEASON> <QUALITY> <EP>"
        )

    elif q.data == "admin_delete":
        await q.message.reply_text("Use:\n/delete <ANIME> <SEASON>")

    elif q.data == "admin_thumb":
        SET_THUMB_WAIT.add(q.from_user.id)
        await q.message.reply_text("🖼 Send new thumbnail image")

    elif q.data == "admin_mongo":
        try:
            db.command("ping")
            total = episodes.count_documents({})
            await q.message.reply_text(
                f"✅ MongoDB connected\n📦 Total episodes stored: {total}"
            )
        except Exception as e:
            await q.message.reply_text(f"❌ Mongo error:\n{e}")

# ========== THUMB ==========
async def receive_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in SET_THUMB_WAIT:
        return
    if not is_admin(uid):
        return
    if not update.message.photo:
        return

    fid = update.message.photo[-1].file_id
    set_thumb(fid)
    SET_THUMB_WAIT.remove(uid)
    await update.message.reply_text("✅ Thumbnail updated")

# ========== BULK ==========
async def bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /bulk <ANIME> <SEASON> <QUALITY>")
        return

    anime, season, quality = context.args
    BULK_STATE[update.effective_user.id] = {
        "anime": anime.upper(),
        "season": int(season),
        "quality": quality,
        "ep": 1
    }

    await update.message.reply_text(
        f"📦 Bulk started\n{anime.upper()} S{season} {quality}\nSend Episode 1"
    )

async def bulk_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in BULK_STATE:
        BULK_STATE.pop(uid)
        await update.message.reply_text("🎉 Bulk upload finished")

# ========== DOCUMENT HANDLER ==========
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # REUPLOAD
    if uid in REUPLOAD_STATE:
        r = REUPLOAD_STATE.pop(uid)
        sent = await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=update.message.document.file_id,
            filename=build_filename(r["season"], r["ep"]),
            thumbnail=get_thumb()
        )
        episodes.update_one(
            {"anime": r["anime"], "season": r["season"], "episode": r["ep"], "quality": r["quality"]},
            {"$set": {"file_id": sent.document.file_id}}
        )
        await update.message.reply_text("✅ Episode replaced")
        return

    # BULK
    if uid not in BULK_STATE:
        return
    if not is_admin(uid):
        return

    s = BULK_STATE[uid]
    ep = s["ep"]

    sent = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=update.message.document.file_id,
        filename=build_filename(s["season"], ep),
        thumbnail=get_thumb()
    )

    episodes.insert_one({
        "anime": s["anime"],
        "season": s["season"],
        "episode": ep,
        "quality": s["quality"],
        "file_id": sent.document.file_id
    })

    s["ep"] += 1
    await update.message.reply_text(f"✅ Episode {ep} added")

# ========== PREVIEW ==========
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /preview <ANIME> <SEASON> <QUALITY>")
        return

    anime, season, quality = context.args
    eps = episodes.find(
        {"anime": anime.upper(), "season": int(season), "quality": quality}
    ).sort("episode", 1)

    txt = f"📦 {anime.upper()} S{season} {quality}\n\n"
    found = False
    for e in eps:
        txt += f"E{e['episode']} ✅\n"
        found = True

    if not found:
        txt += "❌ No episodes found"

    await update.message.reply_text(txt)

# ========== DELETE ==========
async def delete_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /delete <ANIME> <SEASON>")
        return

    anime, season = context.args
    res = episodes.delete_many({"anime": anime.upper(), "season": int(season)})
    await update.message.reply_text(f"🗑 Deleted {res.deleted_count} episodes")

# ========== REUPLOAD ==========
async def reupload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 4:
        await update.message.reply_text(
            "Usage: /reupload <ANIME> <SEASON> <QUALITY> <EP>"
        )
        return

    anime, season, quality, ep = context.args
    REUPLOAD_STATE[update.effective_user.id] = {
        "anime": anime.upper(),
        "season": int(season),
        "quality": quality,
        "ep": int(ep)
    }
    await update.message.reply_text("♻️ Send new file now")

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
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.add_handler(CommandHandler("bulk", bulk_start))
    app.add_handler(CommandHandler("done", bulk_done))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("delete", delete_season))
    app.add_handler(CommandHandler("reupload", reupload))

    app.add_handler(MessageHandler(filters.PHOTO, receive_thumb))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
