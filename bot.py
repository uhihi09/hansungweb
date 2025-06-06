import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database as db
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# .env 파일 로드
load_dotenv()

# 봇 설정
intents = discord.Intents.default()
intents.members = True  # 멤버 정보 접근 권한
intents.message_content = True  # 메시지 내용 접근 권한
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} 봇이 시작되었습니다!')
    logger.info(f'현재 접속된 서버: {[guild.name for guild in bot.guilds]}')

@bot.event
async def on_message(message):
    logger.info(f'메시지 수신: {message.content} from {message.author}')
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    """새로운 멤버가 서버에 들어올 때 자동으로 추가"""
    if not member.bot:  # 봇 제외
        try:
            # 새 멤버 추가
            db.add_member(
                str(member.id),
                member.display_name,
                f"닉네임: {member.display_name}\n역할: {', '.join([role.name for role in member.roles if role.name != '@everyone'])}"
            )
            print(f"새로운 멤버 추가됨: {member.display_name}")
        except Exception as e:
            print(f"멤버 추가 중 오류 발생: {e}")

@bot.command(name='sync_members')
async def sync_members(ctx):
    """서버의 모든 멤버를 데이터베이스에 동기화합니다."""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("이 명령어는 관리자만 사용할 수 있습니다.")
        return

    guild = ctx.guild
    added_count = 0
    updated_count = 0

    # 시작 메시지
    status_msg = await ctx.send("멤버 동기화를 시작합니다...")

    async with ctx.typing():
        for member in guild.members:
            if not member.bot:  # 봇 제외
                try:
                    # 기존 멤버 확인
                    existing_member = db.get_member(str(member.id))
                    
                    if existing_member:
                        # 멤버 정보 업데이트
                        db.update_member_profile(
                            str(member.id),
                            str(bot.user.id),
                            f"닉네임: {member.display_name}\n역할: {', '.join([role.name for role in member.roles if role.name != '@everyone'])}"
                        )
                        updated_count += 1
                    else:
                        # 새 멤버 추가
                        db.add_member(
                            str(member.id),
                            member.display_name,
                            f"닉네임: {member.display_name}\n역할: {', '.join([role.name for role in member.roles if role.name != '@everyone'])}"
                        )
                        added_count += 1
                except Exception as e:
                    print(f"Error processing member {member.display_name}: {e}")

    # 완료 메시지
    await status_msg.edit(content=f"멤버 동기화 완료!\n추가된 멤버: {added_count}\n업데이트된 멤버: {updated_count}\n\n웹사이트에서 확인하실 수 있습니다: {os.getenv('WEBSITE_URL', 'http://localhost:5000')}")

@bot.command(name='update_profile')
async def update_profile(ctx, member: discord.Member, *, description: str):
    """특정 멤버의 프로필을 업데이트합니다."""
    try:
        success = db.update_member_profile(
            str(member.id),
            str(ctx.author.id),
            description
        )
        if success:
            await ctx.send(f"{member.display_name}의 프로필이 업데이트되었습니다!")
        else:
            await ctx.send("프로필 업데이트에 실패했습니다.")
    except Exception as e:
        await ctx.send(f"오류가 발생했습니다: {str(e)}")

# 봇 실행
bot.run(os.getenv('DISCORD_TOKEN')) 