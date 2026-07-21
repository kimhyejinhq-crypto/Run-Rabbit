from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room
import eventlet
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

ROOM = "RABBIT"
players = {}  # sid -> {'name': str, 'position': int}

# ---------- ROUTES ----------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Quan trọng: bắt tất cả file tĩnh (script.js, style.css, ...)
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# ---------- SOCKET EVENTS ----------
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f'🔗 {sid} connected')
    players[sid] = {'name': None, 'position': 0}
    join_room(ROOM)
    emit('room_joined', {'room': ROOM, 'players': get_players_info()}, room=sid)
    emit('update_players', get_players_info(), room=ROOM)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in players:
        del players[sid]
    emit('update_players', get_players_info(), room=ROOM)
    print(f'❌ {sid} disconnected')

@socketio.on('set_name')
def handle_set_name(data):
    sid = request.sid
    name = data.get('name', 'Rabbit')
    if sid in players:
        players[sid]['name'] = name
        emit('update_players', get_players_info(), room=ROOM)

@socketio.on('roll_dice')
def handle_roll_dice():
    sid = request.sid
    if sid not in players or players[sid]['name'] is None:
        return
    dice = random.randint(1, 6)
    players[sid]['position'] = min(players[sid]['position'] + dice, 30)
    emit('dice_rolled', {
        'player': sid,
        'name': players[sid]['name'],
        'dice': dice,
        'position': players[sid]['position'],
        'winner': players[sid]['position'] == 30
    }, room=ROOM)
    if players[sid]['position'] == 30:
        emit('game_over', {'winner': players[sid]['name']}, room=ROOM)

def get_players_info():
    return [{'id': sid, 'name': p['name'], 'position': p['position']}
            for sid, p in players.items() if p['name'] is not None]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
