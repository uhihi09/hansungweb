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
    # 서버 ID를 환경 변수에서 가져옴
    guild_id = os.getenv('DISCORD_GUILD_ID')
    if guild_id:
        try:
            guild = bot.get_guild(int(guild_id))
            if guild:
                print(f'서버 "{guild.name}"에 연결되었습니다.')
                # 모든 멤버 정보 업데이트
                for member in guild.members:
                    db.add_member(str(member.id), member.display_name)
            else:
                print(f'서버 ID {guild_id}를 찾을 수 없습니다.')
        except ValueError:
            print(f'잘못된 서버 ID 형식입니다: {guild_id}')
    else:
        print('DISCORD_GUILD_ID가 설정되지 않았습니다. 서버 정보를 가져올 수 없습니다.')

@bot.event
async def on_member_join(member):
    db.add_member(str(member.id), member.display_name)

@bot.event
async def on_member_update(before, after):
    if before.display_name != after.display_name:
        db.update_member_name(str(after.id), after.display_name)

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