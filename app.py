from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from database import Database
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')  # 세션을 위한 시크릿 키
db = Database()

@app.route('/')
def index():
    members = db.get_all_members()
    profiles = db.get_all_profiles()
    return render_template('index.html', members=members, profiles=profiles)

@app.route('/member/<discord_id>')
def view_profile(discord_id):
    profile = db.get_profile(discord_id)
    member = db.get_member_by_id(discord_id)
    return render_template('profile.html', profile=profile, member=member)

@app.route('/member/<discord_id>/edit', methods=['GET', 'POST'])
def edit_profile(discord_id):
    if request.method == 'POST':
        profile_data = {
            "introduction": request.form.get('introduction', ''),
            "interests": request.form.get('interests', ''),
            "github": request.form.get('github', ''),
            "blog": request.form.get('blog', '')
        }
        db.create_or_update_profile(discord_id, profile_data)
        return redirect(url_for('view_profile', discord_id=discord_id))
    
    profile = db.get_profile(discord_id)
    member = db.get_member_by_id(discord_id)
    return render_template('edit_profile.html', profile=profile, member=member)

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