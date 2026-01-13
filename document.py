from telegram import Update
from telegram.ext import ContextTypes
from config import is_admin
from state.runtime import BULK_STATE, LAST_BULK, REUPLOAD_STATE
from helpers.template import build_filename
from helpers.thumb import get_thumb
from db.mongo import episodes

async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    doc = update.message.document

    await update.message.reply_text("⏳ Processing file...")

    # REUPLOAD
    if uid in REUPLOAD_STATE:
        r = REUPLOAD_STATE.pop(uid)
        filename = build_filename(r["anime"], r["season"], r["ep"], r["quality"])

        sent = await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=doc.file_id,
            filename=filename,
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

    if episodes.find_one({
        "anime": s["anime"],
        "season": s["season"],
        "episode": ep,
        "quality": s["quality"]
    }):
        await update.message.reply_text(f"⚠ Episode {ep} already exists")
        return

    filename = build_filename(s["anime"], s["season"], ep, s["quality"])

    sent = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=doc.file_id,
        filename=filename,
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
