import os
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI missing")

ADMIN_IDS = [6028405107]

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

client = MongoClient(MONGO_URI)
db = client.animebot

episodes = db.episodes
config = db.config
templates = db.templates
