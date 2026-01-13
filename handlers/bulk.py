from telegram import Update
from telegram.ext import ContextTypes
from config import is_admin
from state.runtime import BULK_STATE, LAST_BULK
from helpers.episode import get_next_episode

async def bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    anime, season, quality = context.args
    anime = anime.upper()
    season = int(season)

    ep = get_next_episode(anime, season, quality)

    state = {"anime": anime, "season": season, "quality": quality, "ep": ep}
    BULK_STATE[update.effective_user.id] = state
    LAST_BULK[update.effective_user.id] = state.copy()

    await update.message.reply_text(
        f"📦 Bulk started\n{anime} S{season} {quality}\nStarting from Episode {ep}"
    )

async def bulk_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in BULK_STATE:
        BULK_STATE.pop(uid)
        await update.message.reply_text("🛑 Bulk stopped")
