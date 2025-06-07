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
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# MongoDB 연결
db = Database()

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 시작되었습니다!')
    # 서버의 모든 멤버 정보를 MongoDB에 저장
    guild = bot.get_guild(int(os.getenv('GUILD_ID')))
    if guild:
        for member in guild.members:
            member_data = {
                'id': member.id,
                'display_name': member.display_name,
                'roles': member.roles,
                'status': member.status
            }
            db.add_or_update_member(member_data)
            print(f"멤버 추가/업데이트: {member.display_name}")

@bot.event
async def on_member_join(member):
    if not member.bot:
        member_data = {
            'id': member.id,
            'display_name': member.display_name,
            'roles': member.roles,
            'status': member.status
        }
        db.add_or_update_member(member_data)
        print(f"새 멤버 추가: {member.display_name}")

@bot.event
async def on_member_update(before, after):
    if not after.bot:
        member_data = {
            'id': after.id,
            'display_name': after.display_name,
            'roles': after.roles,
            'status': after.status
        }
        db.add_or_update_member(member_data)
        print(f"멤버 정보 업데이트: {after.display_name}")

@bot.event
async def on_member_remove(member):
    # 멤버가 나가면 데이터베이스에서 삭제
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM members WHERE discord_id = ?', (str(member.id),))
    cursor.execute('DELETE FROM profiles WHERE discord_id = ?', (str(member.id),))
    conn.commit()

# 봇 실행
bot.run(os.getenv('DISCORD_TOKEN')) 