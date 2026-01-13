from db.mongo import config_col

def get_thumb():
    d = config_col.find_one({"_id": "thumb"})
    return d["file_id"] if d else None

def set_thumb(fid):
    config_col.update_one(
        {"_id": "thumb"},
        {"$set": {"file_id": fid}},
        upsert=True
    )
