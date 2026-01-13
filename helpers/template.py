from db.mongo import templates

def get_template(anime):
    doc = templates.find_one({"anime": anime})
    return doc["template"] if doc else None

def set_template(anime, template):
    templates.update_one(
        {"anime": anime},
        {"$set": {"template": template}},
        upsert=True
    )

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
