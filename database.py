import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('MONGODB_DB', 'hansung')

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
members = db['members']
profile_edits = db['profile_edits']

def init_db():
    # MongoDB는 스키마가 없으므로 초기화 불필요
    pass

def add_member(discord_id, nickname, description=""):
    if members.find_one({"discord_id": discord_id}):
        return False
    members.insert_one({
        "discord_id": discord_id,
        "nickname": nickname,
        "description": description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    return True

def update_member_profile(discord_id, editor_discord_id, new_description):
    result = members.update_one(
        {"discord_id": discord_id},
        {"$set": {"description": new_description, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count:
        member = members.find_one({"discord_id": discord_id})
        profile_edits.insert_one({
            "member_id": member["_id"],
            "editor_discord_id": editor_discord_id,
            "edit_content": new_description,
            "created_at": datetime.utcnow()
        })
        return True
    return False

def get_all_members():
    return list(members.find().sort("nickname", 1))

def get_member(discord_id):
    return members.find_one({"discord_id": discord_id})

if __name__ == "__main__":
    init_db() 