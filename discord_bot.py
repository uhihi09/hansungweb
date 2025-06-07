import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# 환경 변수 로드
load_dotenv()

# 환경 변수 설정
os.environ['DATABASE_PATH'] = '/opt/render/project/src/hansung.db'
os.environ['ENVIRONMENT'] = 'production'

# 봇 설정
intents = discord.Intents.default()
intents.members = True  # 멤버 관련 이벤트를 받기 위해 필요
intents.message_content = True

class HansungBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            reconnect=True
        )
        self.db = Database()
        self.initial_members_synced = False

    async def setup_hook(self):
        # 봇이 시작될 때 실행되는 코드
        logger.info("봇 설정 초기화 중...")

    async def on_ready(self):
        logger.info(f'{self.user} 봇이 시작되었습니다!')
        # 서버 ID를 환경 변수에서 가져옴
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if guild_id:
            try:
                guild = self.get_guild(int(guild_id))
                if guild:
                    logger.info(f'서버 "{guild.name}"에 연결되었습니다.')
                    # 모든 멤버 정보 업데이트
                    member_count = 0
                    for member in guild.members:
                        try:
                            avatar_hash = member.avatar.key if member.avatar else None
                            self.db.add_member(str(member.id), member.display_name, avatar_hash)
                            logger.info(f"멤버 추가: {member.display_name} (ID: {member.id}, 아바타: {avatar_hash})")
                            member_count += 1
                        except Exception as e:
                            logger.error(f"멤버 {member.display_name} 추가 중 오류 발생: {e}")
                    logger.info(f"총 {member_count}명의 멤버 정보를 업데이트했습니다.")
                    self.initial_members_synced = True
                else:
                    logger.error(f'서버 ID {guild_id}를 찾을 수 없습니다.')
                    logger.info('서버 ID가 올바른지 확인해주세요.')
            except ValueError:
                logger.error(f'잘못된 서버 ID 형식입니다: {guild_id}')
                logger.info('서버 ID는 숫자만 포함해야 합니다.')
        else:
            logger.error('DISCORD_GUILD_ID가 설정되지 않았습니다.')
            logger.info('다음 단계를 따라 서버 ID를 설정해주세요:')
            logger.info('1. Discord 설정에서 개발자 모드를 활성화합니다.')
            logger.info('2. 서버 이름을 우클릭하고 "ID 복사"를 선택합니다.')
            logger.info('3. .env 파일에 다음 줄을 추가합니다:')
            logger.info('   DISCORD_GUILD_ID=복사한_서버_ID')
            logger.info('4. 봇을 다시 시작합니다.')

    async def on_member_join(self, member):
        try:
            avatar_hash = member.avatar.key if member.avatar else None
            self.db.add_member(str(member.id), member.display_name, avatar_hash)
            logger.info(f"새 멤버 추가: {member.display_name} (ID: {member.id}, 아바타: {avatar_hash})")
        except Exception as e:
            logger.error(f"새 멤버 {member.display_name} 추가 중 오류 발생: {e}")

    async def on_member_update(self, before, after):
        if before.display_name != after.display_name or before.avatar != after.avatar:
            try:
                avatar_hash = after.avatar.key if after.avatar else None
                self.db.update_member_name(str(after.id), after.display_name, avatar_hash)
                logger.info(f"멤버 정보 업데이트: {before.display_name} -> {after.display_name} (ID: {after.id}, 아바타: {avatar_hash})")
            except Exception as e:
                logger.error(f"멤버 {after.display_name} 업데이트 중 오류 발생: {e}")

    async def on_error(self, event_method, *args, **kwargs):
        logger.error(f"이벤트 {event_method} 처리 중 오류 발생")
        logger.error(f"인자: {args}")
        logger.error(f"키워드 인자: {kwargs}")

bot = HansungBot()

# 봇 실행
try:
    bot.run(os.getenv('DISCORD_TOKEN'))
except Exception as e:
    logger.error(f"봇 실행 중 오류 발생: {e}") 