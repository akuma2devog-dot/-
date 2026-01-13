import threading
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import BOT_TOKEN
from server import run_server

from handlers.start import start
from handlers.admin import admin_panel, admin_buttons
from handlers.bulk import bulk_start, bulk_done
from handlers.document import handle_doc
from handlers.misc import (
    preview,
    delete_season,
    reupload,
    mongostatus,
    get_episode,
    settemplate,
    receive_thumb
)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # BASIC
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    # BULK / ADMIN
    app.add_handler(CommandHandler("bulk", bulk_start))
    app.add_handler(CommandHandler("done", bulk_done))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("delete", delete_season))
    app.add_handler(CommandHandler("reupload", reupload))
    app.add_handler(CommandHandler("mongostatus", mongostatus))
    app.add_handler(CommandHandler("get", get_episode))
    app.add_handler(CommandHandler("settemplate", settemplate))

    # FILES
    app.add_handler(MessageHandler(filters.PHOTO, receive_thumb))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))

    app.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    main()
