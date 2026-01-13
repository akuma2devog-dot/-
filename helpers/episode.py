from db.mongo import episodes

def get_next_episode(anime, season, quality):
    last = episodes.find_one(
        {"anime": anime, "season": season, "quality": quality},
        sort=[("episode", -1)]
    )
    return last["episode"] + 1 if last else 1
