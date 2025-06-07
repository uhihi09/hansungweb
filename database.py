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

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client[os.getenv('MONGODB_DB', 'hansung')]
        self.members = self.db.members
        self.profiles = self.db.profiles  # 프로필 컬렉션 추가

    def get_all_members(self):
        return list(self.members.find().sort("nickname", 1))

    def get_member_by_id(self, member_id):
        return self.members.find_one({"id": member_id})

    def add_or_update_member(self, member_data):
        existing_member = self.members.find_one({"discord_id": member_data["discord_id"]})
        
        if existing_member:
            self.members.update_one(
                {"discord_id": member_data["discord_id"]},
                {"$set": member_data}
            )
            return "updated"
        else:
            self.members.insert_one(member_data)
            return "added"

    def delete_member(self, member_id):
        result = self.members.delete_one({"id": member_id})
        return result.deleted_count > 0

    def update_member_role(self, member_id, new_role):
        result = self.members.update_one(
            {"id": member_id},
            {"$set": {"role": new_role}}
        )
        return result.modified_count > 0

    def update_member_status(self, member_id, new_status):
        result = self.members.update_one(
            {"id": member_id},
            {"$set": {"status": new_status}}
        )
        return result.modified_count > 0

    # 프로필 관련 함수들
    def get_profile(self, discord_id):
        return self.profiles.find_one({"discord_id": discord_id})

    def create_or_update_profile(self, discord_id, profile_data):
        profile_data["discord_id"] = discord_id
        profile_data["updated_at"] = datetime.utcnow()
        
        result = self.profiles.update_one(
            {"discord_id": discord_id},
            {"$set": profile_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def get_all_profiles(self):
        return list(self.profiles.find().sort("updated_at", -1))

if __name__ == "__main__":
    init_db() 