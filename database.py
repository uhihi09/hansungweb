import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import threading

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class Database:
    def __init__(self):
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.bot.event(self.on_ready)
        self._local = threading.local()
        self.create_tables()
    
    def get_connection(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect('hansung.db')
        return self._local.conn
    
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
            last_seen TIMESTAMP
        )
        ''')
        
        # 프로필 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            discord_id TEXT PRIMARY KEY,
            introduction TEXT,
            interests TEXT,
            github TEXT,
            blog TEXT,
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
        INSERT OR REPLACE INTO members (discord_id, nickname, role, status, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            str(member_data['id']),
            member_data['display_name'],
            role_name,
            str(member_data.get('status', 'offline')),
            datetime.now()
        ))
        conn.commit()
        return True
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord!')
        await self.update_members()
    
    async def update_members(self):
        guild = self.bot.get_guild(int(os.getenv('GUILD_ID')))
        if guild:
            conn = self.get_connection()
            cursor = conn.cursor()
            for member in guild.members:
                # 역할 정보 가져오기
                roles = [role.name for role in member.roles if role.name != "@everyone"]
                role_name = roles[0] if roles else "멤버"
                
                cursor.execute('''
                INSERT OR REPLACE INTO members (discord_id, nickname, role, status, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(member.id),
                    member.display_name,
                    role_name,
                    str(member.status),
                    datetime.now()
                ))
            conn.commit()
    
    def get_all_members(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM members')
        return [dict(zip(['discord_id', 'nickname', 'role', 'status', 'last_seen'], row)) 
                for row in cursor.fetchall()]
    
    def get_member_by_id(self, discord_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM members WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(['discord_id', 'nickname', 'role', 'status', 'last_seen'], row))
        return None
    
    def get_all_profiles(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles')
        return [dict(zip(['discord_id', 'introduction', 'interests', 'github', 'blog'], row)) 
                for row in cursor.fetchall()]
    
    def get_profile(self, discord_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(['discord_id', 'introduction', 'interests', 'github', 'blog'], row))
        return None
    
    def create_or_update_profile(self, discord_id, profile_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO profiles (discord_id, introduction, interests, github, blog)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            discord_id,
            profile_data.get('introduction', ''),
            profile_data.get('interests', ''),
            profile_data.get('github', ''),
            profile_data.get('blog', '')
        ))
        conn.commit()

if __name__ == "__main__":
    db = Database() 