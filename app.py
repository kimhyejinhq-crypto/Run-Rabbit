from flask import Flask, send_from_directory, request, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Phòng cố định
ROOM = "RABBIT"

# Lưu trữ players: sid -> {'name': ..., 'position': 0}
players = {}

@app.route('/')
def index():
    # Trả về file index.html từ thư mục hiện tại
    return send_from_directory('.', 'index.html')

@app.route('/')
def static_files(path):
    return send_from_directory('.', path)

@socketio.on('connect')
def handle_connect():
    print(f'Connected: {request.sid}')
    players[request.sid] = {'name': None, 'position': 0}
    # Tự động tham gia phòng RABBIT
    join_room(ROOM)
    # Gửi danh sách người chơi hiện tại cho client mới
    emit('room_joined', {'room': ROOM, 'players': get_players_info()}, room=request.sid)
    # Thông báo cho cả phòng có người mới
    emit('update_players', get_players_info(), room=ROOM)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in players:
        del players[sid]
    emit('update_players', get_players_info(), room=ROOM)
    print(f'Disconnected: {sid}')

@socketio.on('set_name')
def handle_set_name(data):
    sid = request.sid
    name = data.get('name', 'Rabbit')
    players[sid]['name'] = name
    emit('update_players', get_players_info(), room=ROOM)

@socketio.on('roll_dice')
def handle_roll_dice():
    sid = request.sid
    if sid not in players or players[sid]['name'] is None:
        return
    # Tung xúc xắc
    dice = random.randint(1, 6)
    players[sid]['position'] = min(players[sid]['position'] + dice, 30)
    # Gửi kết quả cho cả phòng
    emit('dice_rolled', {
        'player': sid,
        'name': players[sid]['name'],
        'dice': dice,
        'position': players[sid]['position'],
        'winner': players[sid]['position'] == 30
    }, room=ROOM)
    # Nếu có người thắng, thông báo
    if players[sid]['position'] == 30:
        emit('game_over', {'winner': players[sid]['name']}, room=ROOM)

def get_players_info():
    return [{'id': sid, 'name': p['name'], 'position': p['position']}
            for sid, p in players.items() if p['name'] is not None]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)[reference:0]
