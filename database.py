import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import threading

load_dotenv()

class Database:
    def __init__(self):
        # 데이터베이스 파일 경로를 환경 변수에서 가져옴
        db_path = os.getenv('DATABASE_PATH', 'database.db')
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        
        # Discord 봇 설정
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
    
    def get_connection(self):
        db_path = os.getenv('DATABASE_PATH', 'database.db')
        return sqlite3.connect(db_path)
    
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 기존 테이블 삭제
        cursor.execute('DROP TABLE IF EXISTS profiles')
        cursor.execute('DROP TABLE IF EXISTS members')
        
        # 멤버 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            discord_id TEXT PRIMARY KEY,
            nickname TEXT,
            role TEXT,
            status TEXT,
            last_seen TIMESTAMP,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
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
        
        conn.commit()
    
    def add_or_update_member(self, member_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 역할 정보 가져오기
        roles = [role.name for role in member_data.get('roles', []) if role.name != "@everyone"]
        role_name = roles[0] if roles else "멤버"
        
        cursor.execute('''
        INSERT OR REPLACE INTO members (discord_id, nickname, role, status, last_seen, joined_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(member_data['id']),
            member_data['display_name'],
            role_name,
            str(member_data.get('status', 'offline')),
            datetime.now(),
            datetime.now()
        ))
        conn.commit()
        return True
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord!')
        await self.update_members()
    
    async def update_members(self):
        guild_id = os.getenv('GUILD_ID')
        if not guild_id:
            print("Warning: GUILD_ID is not set in environment variables")
            return
            
        guild = self.bot.get_guild(int(guild_id))
        if guild:
            conn = self.get_connection()
            cursor = conn.cursor()
            for member in guild.members:
                # 역할 정보 가져오기
                roles = [role.name for role in member.roles if role.name != "@everyone"]
                role_name = roles[0] if roles else "멤버"
                
                cursor.execute('''
                INSERT OR REPLACE INTO members (discord_id, nickname, role, status, last_seen, joined_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    str(member.id),
                    member.display_name,
                    role_name,
                    str(member.status),
                    datetime.now(),
                    datetime.now()
                ))
            conn.commit()
    
    def get_all_members(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM members')
        return [dict(zip(['discord_id', 'nickname', 'role', 'status', 'last_seen', 'joined_at'], row)) 
                for row in cursor.fetchall()]
    
    def get_member_by_id(self, discord_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM members WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(['discord_id', 'nickname', 'role', 'status', 'last_seen', 'joined_at'], row))
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
    
    def get_profile(self, discord_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(['discord_id', 'introduction', 'profile_image', 'incidents', 'updated_at'], row))
        return None
    
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