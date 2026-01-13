from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import episodes, config, templates, is_admin

# ---------- STATES ----------
BULK_STATE = {}
LAST_BULK = {}
WAIT_THUMB = set()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nAdmins can use /admin"
    )

# ---------- ADMIN PANEL ----------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    kb = [
        [InlineKeyboardButton("📦 Start Bulk", callback_data="bulk")],
        [InlineKeyboardButton("▶ Resume Bulk", callback_data="resume")],
        [InlineKeyboardButton("🛑 Stop Bulk", callback_data="stop")],
        [InlineKeyboardButton("👁 Preview", callback_data="preview")],
        [InlineKeyboardButton("♻ Reupload", callback_data="reupload")],
        [InlineKeyboardButton("🗑 Delete Season", callback_data="delete")],
        [InlineKeyboardButton("🖼 Change Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("📊 Mongo Status", callback_data="mongo")]
    ]

    await update.message.reply_text(
        "👑 Admin Panel",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ---------- BUTTON HANDLER ----------
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if not is_admin(uid):
        return

    if q.data == "bulk":
        await q.message.reply_text("Use:\n/bulk <ANIME> <SEASON> <QUALITY>")

    elif q.data == "resume":
        if uid not in LAST_BULK:
            await q.message.reply_text("❌ No bulk to resume")
            return
        BULK_STATE[uid] = LAST_BULK[uid].copy()
        s = BULK_STATE[uid]
        await q.message.reply_text(
            f"▶ Resumed\n{s['anime']} S{s['season']} {s['quality']}\nNext EP: {s['ep']}"
        )

    elif q.data == "stop":
        await bulk_done(update, context)

    elif q.data == "preview":
        await q.message.reply_text("Use:\n/preview <ANIME> <SEASON> <QUALITY>")

    elif q.data == "reupload":
        await q.message.reply_text("Use:\n/reupload <ANIME> <SEASON> <QUALITY> <EP>")

    elif q.data == "delete":
        await q.message.reply_text("Use:\n/delete <ANIME> <SEASON>")

    elif q.data == "thumb":
        WAIT_THUMB.add(uid)
        await q.message.reply_text("🖼 Send new thumbnail")

    elif q.data == "mongo":
        await mongostatus(update, context)

# ---------- BULK ----------
async def bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /bulk <ANIME> <SEASON> <QUALITY>")
        return

    anime, season, quality = context.args
    state = {
        "anime": anime.upper(),
        "season": int(season),
        "quality": quality,
        "ep": 1
    }

    BULK_STATE[update.effective_user.id] = state
    LAST_BULK[update.effective_user.id] = state.copy()

    await update.message.reply_text("📦 Bulk started")

async def bulk_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    BULK_STATE.pop(update.effective_user.id, None)
    await update.message.reply_text("🛑 Bulk stopped")

# ---------- PREVIEW ----------
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime, season, quality = context.args
    eps = episodes.find(
        {"anime": anime.upper(), "season": int(season), "quality": quality}
    ).sort("episode", 1)

    text = f"📦 {anime.upper()} S{season} {quality}\n\n"
    found = False

    for e in eps:
        text += f"E{e['episode']} ✅\n"
        found = True

    if not found:
        text += "❌ No episodes found"

    await update.message.reply_text(text)

# ---------- DELETE ----------
async def delete_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime, season = context.args
    res = episodes.delete_many({"anime": anime.upper(), "season": int(season)})
    await update.message.reply_text(f"🗑 Deleted {res.deleted_count} episodes")

# ---------- REUPLOAD ----------
async def reupload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻ Reupload feature ready")

# ---------- MONGO ----------
async def mongostatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = episodes.count_documents({})
    await update.message.reply_text(f"📊 Mongo OK\nTotal episodes: {total}")

# ---------- GET ----------
async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime, season, quality, ep = context.args
    data = episodes.find_one({
        "anime": anime.upper(),
        "season": int(season),
        "quality": quality,
        "episode": int(ep)
    })

    if not data:
        await update.message.reply_text("❌ Episode not found")
        return

    await context.bot.send_document(update.effective_chat.id, data["file_id"])

# ---------- THUMB ----------
async def receive_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in WAIT_THUMB:
        fid = update.message.photo[-1].file_id
        config.update_one(
            {"_id": "thumb"},
            {"$set": {"file_id": fid}},
            upsert=True
        )
        WAIT_THUMB.remove(uid)
        await update.message.reply_text("✅ Thumbnail updated")

# ---------- TEMPLATE ----------
async def settemplate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime = context.args[0].upper()
    template = " ".join(context.args[1:])

    templates.update_one(
        {"anime": anime},
        {"$set": {"template": template}},
        upsert=True
    )

    await update.message.reply_text(f"✅ Template set for {anime}")
