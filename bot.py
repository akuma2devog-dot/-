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
LAST_BULK = {}          # ✅ NEW (for resume)
SET_THUMB_WAIT = set()
REUPLOAD_STATE = {}

# ========== HELPERS ==========
def get_thumb():
    d = config.find_one({"_id": "thumb"})
    return d["file_id"] if d else None

def set_thumb(fid):
    config.update_one(
        {"_id": "thumb"},
        {"$set": {"file_id": fid}},
        upsert=True
    )

def build_filename(season, episode):
    return f"S{season}E{episode} @anifindX.mkv"

def get_next_episode(anime, season, quality):
    last = episodes.find_one(
        {"anime": anime, "season": season, "quality": quality},
        sort=[("episode", -1)]
    )
    return last["episode"] + 1 if last else 1

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nAdmins can use /admin"
    )

# ========== ADMIN ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "👑 ADMIN COMMANDS\n\n"
        "/bulk <ANIME> <SEASON> <QUALITY>\n"
        "/resumebulk\n"
        "/done\n"
        "/preview <ANIME> <SEASON> <QUALITY>\n"
        "/delete <ANIME> <SEASON>\n"
        "/reupload <ANIME> <SEASON> <QUALITY> <EP>\n"
        "/mongostatus\n"
        "\n🖼 Send image to update thumbnail"
    )

# ========== THUMB ==========
async def receive_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not update.message.photo:
        return

    fid = update.message.photo[-1].file_id
    set_thumb(fid)
    await update.message.reply_text("✅ Thumbnail updated")

# ========== BULK ==========
async def bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /bulk <ANIME> <SEASON> <QUALITY>")
        return

    anime, season, quality = context.args
    season = int(season)
    anime = anime.upper()

    ep = get_next_episode(anime, season, quality)

    state = {
        "anime": anime,
        "season": season,
        "quality": quality,
        "ep": ep
    }

    BULK_STATE[update.effective_user.id] = state
    LAST_BULK[update.effective_user.id] = state.copy()

    await update.message.reply_text(
        f"📦 Bulk started\n{anime} S{season} {quality}\n"
        f"➡️ Starting from Episode {ep}"
    )

async def resume_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in LAST_BULK:
        await update.message.reply_text("❌ No previous bulk to resume")
        return

    BULK_STATE[uid] = LAST_BULK[uid].copy()
    s = BULK_STATE[uid]

    await update.message.reply_text(
        f"▶️ Bulk resumed\n{s['anime']} S{s['season']} {s['quality']}\n"
        f"➡️ Next Episode: {s['ep']}"
    )

async def bulk_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in BULK_STATE:
        BULK_STATE.pop(uid)
        await update.message.reply_text("🛑 Bulk upload stopped")

# ========== DOCUMENT ==========
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
            {
                "anime": r["anime"],
                "season": r["season"],
                "episode": r["ep"],
                "quality": r["quality"]
            },
            {"$set": {"file_id": sent.document.file_id}}
        )

        await update.message.reply_text("✅ Episode replaced")
        return

    # BULK
    if uid not in BULK_STATE or not is_admin(uid):
        return

    s = BULK_STATE[uid]
    ep = s["ep"]

    # DUPLICATE CHECK
    exists = episodes.find_one({
        "anime": s["anime"],
        "season": s["season"],
        "episode": ep,
        "quality": s["quality"]
    })

    if exists:
        await update.message.reply_text(
            f"⚠️ Episode {ep} already exists.\nUse /reupload to replace."
        )
        return

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
    LAST_BULK[uid] = s.copy()

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

# ========== MONGO ==========
async def mongo_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    db.command("ping")
    total = episodes.count_documents({})
    await update.message.reply_text(
        f"✅ MongoDB connected\n📦 Total episodes stored: {total}"
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
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("bulk", bulk_start))
    app.add_handler(CommandHandler("resumebulk", resume_bulk))
    app.add_handler(CommandHandler("done", bulk_done))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("delete", delete_season))
    app.add_handler(CommandHandler("reupload", reupload))
    app.add_handler(CommandHandler("mongostatus", mongo_status))

    app.add_handler(MessageHandler(filters.PHOTO, receive_thumb))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    main()
