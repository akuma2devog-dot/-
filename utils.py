from config import config, templates

def is_admin(uid, admins):
    return uid in admins

def get_thumb():
    d = config.find_one({"_id": "thumb"})
    return d["file_id"] if d else None

def set_thumb(fid):
    config.update_one(
        {"_id": "thumb"},
        {"$set": {"file_id": fid}},
        upsert=True
    )

def get_template(anime):
    d = templates.find_one({"anime": anime})
    return d["template"] if d else None

def build_filename(anime, season, episode, quality):
    tpl = get_template(anime)
    if not tpl:
        return f"S{season}E{episode} @anifindX.mkv"

    return tpl.format(
        ANIME=anime,
        SEASON=f"{season:02}",
        EP=f"{episode:02}",
        QUALITY=quality
    )
