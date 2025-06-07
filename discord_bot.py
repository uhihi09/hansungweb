import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database

# .env 파일 로드
load_dotenv()

# 봇 설정
intents = discord.Intents.default()
intents.members = True  # 멤버 관련 이벤트를 받기 위해 필요
bot = commands.Bot(command_prefix='!', intents=intents)

# MongoDB 연결
db = Database()

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 시작되었습니다!')
    # 서버의 모든 멤버 정보를 MongoDB에 저장
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:  # 봇이 아닌 실제 사용자만 처리
                member_data = {
                    "discord_id": str(member.id),
                    "nickname": member.display_name,
                    "name": member.name,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                    "role": "일반",  # 기본 역할
                    "status": "재학"  # 기본 상태
                }
                db.add_or_update_member(member_data)
                print(f"멤버 추가/업데이트: {member.display_name}")

@bot.event
async def on_member_join(member):
    if not member.bot:
        member_data = {
            "discord_id": str(member.id),
            "nickname": member.display_name,
            "name": member.name,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "role": "일반",
            "status": "재학"
        }
        db.add_or_update_member(member_data)
        print(f"새 멤버 추가: {member.display_name}")

@bot.event
async def on_member_update(before, after):
    if not after.bot:
        member_data = {
            "discord_id": str(after.id),
            "nickname": after.display_name,
            "name": after.name,
            "joined_at": after.joined_at.isoformat() if after.joined_at else None,
            "role": "일반",
            "status": "재학"
        }
        db.add_or_update_member(member_data)
        print(f"멤버 정보 업데이트: {after.display_name}")

# 봇 실행
bot.run(os.getenv('DISCORD_TOKEN')) 