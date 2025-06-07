import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import threading

load_dotenv()

class Database:
    _instance = None
    _bot_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_file = 'hansung.db'
        print(f"데이터베이스 파일 경로: {os.path.abspath(self.db_file)}")
        # 데이터베이스 파일이 있으면 삭제
        if os.path.exists(self.db_file):
            print(f"기존 데이터베이스 파일 삭제: {self.db_file}")
            os.remove(self.db_file)
        # 테이블 생성
        self.create_tables()
        
        # Discord 봇 설정 (한 번만 초기화)
        if not Database._bot_initialized:
            intents = discord.Intents.default()
            intents.members = True
            intents.message_content = True
            self.bot = commands.Bot(command_prefix='!', intents=intents)
            
            @self.bot.event
            async def on_ready():
                print(f'{self.bot.user} 봇이 시작되었습니다!')
                # 서버 ID를 환경 변수에서 가져옴
                guild_id = os.getenv('DISCORD_GUILD_ID')
                if guild_id:
                    try:
                        self.guild = self.bot.get_guild(int(guild_id))
                        if self.guild:
                            print(f'서버 "{self.guild.name}"에 연결되었습니다.')
                        else:
                            print(f'서버 ID {guild_id}를 찾을 수 없습니다.')
                    except ValueError:
                        print(f'잘못된 서버 ID 형식입니다: {guild_id}')
                else:
                    print('DISCORD_GUILD_ID가 설정되지 않았습니다. 서버 정보를 가져올 수 없습니다.')
                    self.guild = None
            
            @self.bot.event
            async def on_member_join(member):
                self.add_member(member.id, member.name)
            
            @self.bot.event
            async def on_member_update(before, after):
                if before.name != after.name:
                    self.update_member_name(after.id, after.name)
            
            Database._bot_initialized = True
        else:
            # 이미 초기화된 봇 인스턴스 가져오기
            self.bot = Database._instance.bot
            self.guild = Database._instance.guild

        self._initialized = True

    def get_connection(self):
        print(f"데이터베이스 연결 시도: {self.db_file}")
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # 결과를 딕셔너리로 반환
        return conn
    
    def create_tables(self):
        print("테이블 생성 시작")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 멤버 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            discord_id TEXT PRIMARY KEY,
            nickname TEXT,
            avatar_hash TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("멤버 테이블 생성 완료")
        
        # 프로필 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            discord_id TEXT PRIMARY KEY,
            introduction TEXT,
            profile_image TEXT,
            incidents TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (discord_id) REFERENCES members(discord_id)
        )
        ''')
        print("프로필 테이블 생성 완료")
        
        conn.commit()
        conn.close()
        print("테이블 생성 완료")
    
    def add_member(self, discord_id, nickname, avatar_hash=None):
        print(f"멤버 추가 시도: {discord_id}, {nickname}, {avatar_hash}")
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR REPLACE INTO members (discord_id, nickname, avatar_hash) VALUES (?, ?, ?)',
                          (str(discord_id), nickname, avatar_hash))
            conn.commit()
            print(f"멤버 추가 성공: {discord_id}")
        except Exception as e:
            print(f"멤버 추가 실패: {e}")
            raise
        finally:
            conn.close()
    
    def get_all_members(self):
        print("모든 멤버 조회 시도")
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM members')
            members = [dict(row) for row in cursor.fetchall()]
            print(f"조회된 멤버 수: {len(members)}")
            for member in members:
                print(f"멤버: {member}")
            return members
        except Exception as e:
            print(f"멤버 조회 실패: {e}")
            return []
        finally:
            conn.close()
    
    def get_member_by_id(self, discord_id):
        print(f"멤버 조회 시도: {discord_id}")
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM members WHERE discord_id = ?', (str(discord_id),))
            row = cursor.fetchone()
            if row:
                member = dict(row)
                print(f"멤버 조회 성공: {member}")
                return member
            print(f"멤버를 찾을 수 없음: {discord_id}")
            return None
        except Exception as e:
            print(f"멤버 조회 실패: {e}")
            return None
        finally:
            conn.close()
    
    def update_member_name(self, discord_id, new_name, avatar_hash=None):
        print(f"멤버 정보 업데이트 시도: {discord_id}, {new_name}, {avatar_hash}")
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE members SET nickname = ?, avatar_hash = ? WHERE discord_id = ?',
                          (new_name, avatar_hash, str(discord_id)))
            conn.commit()
            print(f"멤버 정보 업데이트 성공: {discord_id}")
        except Exception as e:
            print(f"멤버 정보 업데이트 실패: {e}")
            raise
        finally:
            conn.close()
    
    def add_profile(self, discord_id, introduction, profile_image, incidents):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO profiles (discord_id, introduction, profile_image, incidents, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (str(discord_id), introduction, profile_image, incidents))
        conn.commit()
        conn.close()
    
    def get_profile(self, discord_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE discord_id = ?', (str(discord_id),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(zip(['discord_id', 'introduction', 'profile_image', 'incidents', 'updated_at'], row))
        return None

    def get_all_profiles(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT p.*, m.nickname, m.joined_at 
        FROM profiles p 
        JOIN members m ON p.discord_id = m.discord_id 
        ORDER BY p.updated_at DESC
        ''')
        return [dict(zip(['discord_id', 'introduction', 'profile_image', 'incidents', 'updated_at', 'nickname', 'joined_at'], row)) 
                for row in cursor.fetchall()]
    
    def create_or_update_profile(self, discord_id, profile_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO profiles (discord_id, introduction, profile_image, incidents, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            discord_id,
            profile_data.get('introduction', ''),
            profile_data.get('profile_image', ''),
            profile_data.get('incidents', '')
        ))
        conn.commit()
        conn.close()

    def get_discord_profile(self, discord_id):
        """Discord 프로필 정보를 가져옵니다."""
        try:
            # 서버 멤버 정보 가져오기 시도
            if hasattr(self, 'guild') and self.guild:
                member = self.guild.get_member(int(discord_id))
                if member:
                    return {
                        'name': member.name,
                        'avatar_url': str(member.avatar.url) if member.avatar else str(member.default_avatar.url),
                        'discriminator': member.discriminator,
                        'created_at': member.created_at.isoformat(),
                        'joined_at': member.joined_at.isoformat() if member.joined_at else None,
                        'nickname': member.nick,
                        'roles': [role.name for role in member.roles if role.name != "@everyone"],
                        'is_bot': member.bot
                    }
            
            # 서버 정보가 없거나 멤버를 찾을 수 없는 경우, 일반 사용자 정보 가져오기
            user = self.bot.get_user(int(discord_id))
            if user:
                return {
                    'name': user.name,
                    'avatar_url': str(user.avatar.url) if user.avatar else str(user.default_avatar.url),
                    'discriminator': user.discriminator,
                    'created_at': user.created_at.isoformat(),
                    'is_bot': user.bot
                }
        except Exception as e:
            print(f"Discord 프로필 가져오기 실패: {e}")
        return None

if __name__ == "__main__":
    db = Database() 