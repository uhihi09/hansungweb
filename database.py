import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('hansung.db')
    c = conn.cursor()
    
    # 멤버 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 프로필 수정 기록 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS profile_edits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            editor_discord_id TEXT NOT NULL,
            edit_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_member(discord_id, nickname, description=""):
    conn = sqlite3.connect('hansung.db')
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO members (discord_id, nickname, description)
            VALUES (?, ?, ?)
        ''', (discord_id, nickname, description))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_member_profile(discord_id, editor_discord_id, new_description):
    conn = sqlite3.connect('hansung.db')
    c = conn.cursor()
    try:
        # 멤버 정보 업데이트
        c.execute('''
            UPDATE members 
            SET description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE discord_id = ?
        ''', (new_description, discord_id))
        
        # 수정 기록 저장
        c.execute('''
            INSERT INTO profile_edits (member_id, editor_discord_id, edit_content)
            SELECT id, ?, ?
            FROM members
            WHERE discord_id = ?
        ''', (editor_discord_id, new_description, discord_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False
    finally:
        conn.close()

def get_all_members():
    conn = sqlite3.connect('hansung.db')
    c = conn.cursor()
    c.execute('SELECT * FROM members ORDER BY nickname')
    members = c.fetchall()
    conn.close()
    return members

def get_member(discord_id):
    conn = sqlite3.connect('hansung.db')
    c = conn.cursor()
    c.execute('SELECT * FROM members WHERE discord_id = ?', (discord_id,))
    member = c.fetchone()
    conn.close()
    return member

if __name__ == "__main__":
    init_db() 