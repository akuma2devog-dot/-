from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import is_admin
from state.runtime import BULK_STATE, LAST_BULK, SET_THUMB_WAIT
from db.mongo import episodes, db
from handlers.bulk import bulk_done

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    kb = [
        [InlineKeyboardButton("📦 Start Bulk", callback_data="admin_bulk")],
        [InlineKeyboardButton("▶️ Resume Bulk", callback_data="admin_resume")],
        [InlineKeyboardButton("🛑 Stop Bulk", callback_data="admin_done")],
        [InlineKeyboardButton("👁 Preview", callback_data="admin_preview")],
        [InlineKeyboardButton("♻ Reupload", callback_data="admin_reupload")],
        [InlineKeyboardButton("🗑 Delete Season", callback_data="admin_delete")],
        [InlineKeyboardButton("🖼 Change Thumbnail", callback_data="admin_thumb")],
        [InlineKeyboardButton("📊 Mongo Status", callback_data="admin_mongo")]
    ]

    await update.message.reply_text("🛠 Admin Panel", reply_markup=InlineKeyboardMarkup(kb))


async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if not is_admin(uid):
        return

    if q.data == "admin_bulk":
        await q.message.reply_text("Use:\n/bulk <ANIME> <SEASON> <QUALITY>")

    elif q.data == "admin_resume":
        if uid not in LAST_BULK:
            await q.message.reply_text("❌ No bulk to resume")
            return
        BULK_STATE[uid] = LAST_BULK[uid].copy()
        s = BULK_STATE[uid]
        await q.message.reply_text(
            f"▶️ Resumed\n{s['anime']} S{s['season']} {s['quality']}\nNext Episode: {s['ep']}"
        )

    elif q.data == "admin_done":
        await bulk_done(update, context)

    elif q.data == "admin_thumb":
        SET_THUMB_WAIT.add(uid)
        await q.message.reply_text("🖼 Send new thumbnail image")

    elif q.data == "admin_mongo":
        db.command("ping")
        total = episodes.count_documents({})
        await q.message.reply_text(f"✅ MongoDB OK\n📦 Total episodes: {total}")
