import os
from pymongo import MongoClient

# ---------- ENV ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is missing")

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI is missing")

# ---------- ADMINS ----------
ADMIN_IDS = [6028405107]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ---------- DATABASE ----------
client = MongoClient(MONGO_URI)
db = client.animebot

episodes = db.episodes
config = db.config
templates = db.templates
