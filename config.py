import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

ADMIN_IDS = [6028405107]

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

if not BOT_TOKEN or not MONGO_URI:
    raise RuntimeError("Missing environment variables")
