from telegram import Update
from telegram.ext import ContextTypes
from config import is_admin
from state.runtime import REUPLOAD_STATE, SET_THUMB_WAIT
from db.mongo import episodes, db
from helpers.template import set_template
from helpers.thumb import set_thumb


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def delete_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime, season = context.args
    res = episodes.delete_many({"anime": anime.upper(), "season": int(season)})
    await update.message.reply_text(f"🗑 Deleted {res.deleted_count} episodes")


async def reupload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime, season, quality, ep = context.args
    REUPLOAD_STATE[update.effective_user.id] = {
        "anime": anime.upper(),
        "season": int(season),
        "quality": quality,
        "ep": int(ep)
    }
    await update.message.reply_text("♻️ Send new file now")


async def mongostatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.command("ping")
    total = episodes.count_documents({})
    await update.message.reply_text(f"✅ MongoDB OK\n📦 Total episodes: {total}")


async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

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

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=data["file_id"]
    )


async def settemplate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/settemplate <ANIME> <TEMPLATE>"
        )
        return

    anime = context.args[0].upper()
    template = " ".join(context.args[1:])
    set_template(anime, template)

    await update.message.reply_text(f"✅ Template set for {anime}")


async def receive_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in SET_THUMB_WAIT and is_admin(uid):
        fid = update.message.photo[-1].file_id
        set_thumb(fid)
        SET_THUMB_WAIT.remove(uid)
        await update.message.reply_text("✅ Thumbnail updated")
