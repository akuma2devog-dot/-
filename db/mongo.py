from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.animebot

episodes = db.episodes
config_col = db.config
templates = db.templates
