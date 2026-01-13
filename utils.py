from config import config, templates, is_admin as _is_admin

# ---------- ADMIN ----------
def is_admin(uid: int) -> bool:
    return _is_admin(uid)

# ---------- THUMBNAIL ----------
def get_thumb():
    doc = config.find_one({"_id": "thumb"})
    return doc["file_id"] if doc else None

def set_thumb(file_id: str):
    config.update_one(
        {"_id": "thumb"},
        {"$set": {"file_id": file_id}},
        upsert=True
    )

# ---------- TEMPLATE ----------
def get_template(anime: str):
    doc = templates.find_one({"anime": anime})
    return doc["template"] if doc else None

def build_filename(anime: str, season: int, episode: int, quality: str) -> str:
    template = get_template(anime)

    if not template:
        return f"S{season}E{episode} @anifindX.mkv"

    return template.format(
        ANIME=anime,
        SEASON=f"{season:02}",
        EP=f"{episode:02}",
        QUALITY=quality
    )
