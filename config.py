import os
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

ADMIN_IDS = [6028405107]

client = MongoClient(MONGO_URI)
db = client.animebot

episodes = db.episodes
config = db.config
templates = db.templates
