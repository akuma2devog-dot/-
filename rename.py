from telegram import InputFile
from config import episodes
from utils import build_filename, get_thumb

async def handle_document(update, context, BULK_STATE, LAST_BULK, REUPLOAD_STATE):
    uid = update.effective_user.id
    doc = update.message.document

    await update.message.reply_text("⏳ Processing file…")

    # ---------- REUPLOAD ----------
    if uid in REUPLOAD_STATE:
        r = REUPLOAD_STATE.pop(uid)
        filename = build_filename(
            r["anime"], r["season"], r["ep"], r["quality"]
        )

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

    # ---------- BULK ----------
    if uid not in BULK_STATE:
        return

    s = BULK_STATE[uid]
    ep = s["ep"]

    exists = episodes.find_one({
        "anime": s["anime"],
        "season": s["season"],
        "episode": ep,
        "quality": s["quality"]
    })

    if exists:
        await update.message.reply_text("⚠️ Episode already exists")
        return

    filename = build_filename(
        s["anime"], s["season"], ep, s["quality"]
    )

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
