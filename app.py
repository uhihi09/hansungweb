from flask import Flask, render_template, request, jsonify, redirect, url_for
import database as db
import os
from waitress import serve

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    members = db.get_all_members()
    return render_template('index.html', members=members)

@app.route('/member/<discord_id>')
def member_profile(discord_id):
    member = db.get_member(discord_id)
    if member:
        return render_template('member.html', member=member)
    return redirect(url_for('index'))

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
    db.init_db()
    port = int(os.environ.get('PORT', 5000))
    serve(app, host='0.0.0.0', port=port) 