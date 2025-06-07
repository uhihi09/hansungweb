from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from database import Database
import os
from dotenv import load_dotenv
import threading
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

# 이미지 업로드 설정
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 업로드 폴더가 없으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 전역 변수로 Database 인스턴스 생성
db = Database()

# 봇 실행 상태를 저장할 파일
BOT_STATUS_FILE = 'bot_status.txt'

def is_bot_running():
    try:
        with open(BOT_STATUS_FILE, 'r') as f:
            return f.read().strip() == 'running'
    except FileNotFoundError:
        return False

def set_bot_status(status):
    with open(BOT_STATUS_FILE, 'w') as f:
        f.write(status)

# Discord 봇을 백그라운드에서 실행
def run_bot():
    if not is_bot_running():
        set_bot_status('running')
        try:
            db.bot.run(os.getenv('DISCORD_TOKEN'))
        finally:
            set_bot_status('stopped')

# 봇 실행을 위한 스레드 시작
if not is_bot_running():
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True  # 메인 프로그램이 종료되면 봇도 종료
    bot_thread.start()

# 템플릿에서 사용할 함수 등록
@app.context_processor
def utility_processor():
    return dict(get_discord_profile=db.get_discord_profile)

@app.route('/')
def index():
    members = db.get_all_members()
    print(f"가져온 멤버 수: {len(members)}")  # 디버깅용 로그
    for member in members:
        print(f"멤버: {member}")  # 디버깅용 로그
    return render_template('index.html', members=members)

@app.route('/profile/<discord_id>')
def view_profile(discord_id):
    member = db.get_member_by_id(discord_id)
    profile = db.get_profile(discord_id)
    return render_template('profile.html', member=member, profile=profile)

@app.route('/profile/<discord_id>/edit', methods=['GET', 'POST'])
def edit_profile(discord_id):
    if request.method == 'POST':
        introduction = request.form.get('introduction')
        profile_image = request.form.get('profile_image')
        incidents = request.form.get('incidents')
        
        db.add_profile(discord_id, introduction, profile_image, incidents)
        flash('프로필이 업데이트되었습니다.')
        return redirect(url_for('view_profile', discord_id=discord_id))
    
    member = db.get_member_by_id(discord_id)
    profile = db.get_profile(discord_id)
    return render_template('edit_profile.html', member=member, profile=profile)

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    discord_id = data.get('discord_id')
    editor_discord_id = data.get('editor_discord_id')
    new_description = data.get('description')
    
    if not all([discord_id, editor_discord_id, new_description]):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    success = db.update_member_profile(discord_id, editor_discord_id, new_description)
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(debug=True) 