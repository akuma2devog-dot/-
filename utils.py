from telegram import Update
from telegram.ext import ContextTypes

# ---------- BASIC COMMANDS (TEMP SAFE) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Admin panel")

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

# ---------- BULK (STUBS) ----------
async def bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def bulk_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

# ---------- MANAGEMENT ----------
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def delete_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def reupload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def mongostatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def get_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def receive_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def settemplate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
