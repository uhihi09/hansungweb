import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class Database:
    def __init__(self):
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.bot.event(self.on_ready)
        self.conn = sqlite3.connect('hansung.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
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
        
        self.conn.commit()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord!')
        await self.update_members()
    
    async def update_members(self):
        guild = self.bot.get_guild(int(os.getenv('GUILD_ID')))
        if guild:
            cursor = self.conn.cursor()
            for member in guild.members:
                cursor.execute('''
                INSERT OR REPLACE INTO members (discord_id, nickname, role, status, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(member.id),
                    member.display_name,
                    '멤버',
                    str(member.status),
                    datetime.now()
                ))
            self.conn.commit()
    
    def get_all_members(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM members')
        return [dict(zip(['discord_id', 'nickname', 'role', 'status', 'last_seen'], row)) 
                for row in cursor.fetchall()]
    
    def get_member_by_id(self, discord_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM members WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(['discord_id', 'nickname', 'role', 'status', 'last_seen'], row))
        return None
    
    def get_all_profiles(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM profiles')
        return [dict(zip(['discord_id', 'introduction', 'interests', 'github', 'blog'], row)) 
                for row in cursor.fetchall()]
    
    def get_profile(self, discord_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(['discord_id', 'introduction', 'interests', 'github', 'blog'], row))
        return None
    
    def create_or_update_profile(self, discord_id, profile_data):
        cursor = self.conn.cursor()
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
        self.conn.commit()

if __name__ == "__main__":
    db = Database() 