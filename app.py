from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Dữ liệu game
players = {}          # sid -> {'name': str, 'room': str, 'position': int}
rooms = {}            # room -> {'players': [sid, ...], 'turn': sid, 'dice': int}
room_codes = set()    # để tạo mã ngẫu nhiên

def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in room_codes:
            room_codes.add(code)
            return code

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template('index.html')

# QUAN TRỌNG: phục vụ file tĩnh (script.js, style.css)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# ---------- SOCKET EVENTS ----------
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    players[sid] = {'name': None, 'room': None, 'position': 0}
    print(f'🔗 {sid} connected')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in players:
        room = players[sid]['room']
        if room and room in rooms:
            rooms[room]['players'].remove(sid)
            if not rooms[room]['players']:
                room_codes.discard(room)
                del rooms[room]
            else:
                # Cập nhật danh sách
                emit('update_players', get_players_info(room), room=room)
                # Nếu người rời là lượt hiện tại, chuyển lượt
                if rooms[room].get('turn') == sid:
                    next_turn(room)
        del players[sid]
    print(f'❌ {sid} disconnected')

@socketio.on('create_room')
def handle_create_room(data):
    sid = request.sid
    name = data.get('name', 'Rabbit')
    room = generate_room_code()
    players[sid]['name'] = name
    players[sid]['room'] = room
    players[sid]['position'] = 0
    rooms[room] = {
        'players': [sid],
        'turn': sid,
        'dice': None
    }
    join_room(room)
    emit('room_created', {
        'room': room,
        'players': get_players_info(room)
    }, room=sid)
    emit('update_players', get_players_info(room), room=room)

@socketio.on('join_room')
def handle_join_room(data):
    sid = request.sid
    room = data.get('room', '').upper()
    name = data.get('name', 'Rabbit')
    if room not in rooms:
        emit('error', {'msg': 'Phòng không tồn tại!'}, room=sid)
        return
    if len(rooms[room]['players']) >= 4:
        emit('error', {'msg': 'Phòng đã đầy (tối đa 4 người)!'}, room=sid)
        return
    players[sid]['name'] = name
    players[sid]['room'] = room
    players[sid]['position'] = 0
    rooms[room]['players'].append(sid)
    join_room(room)
    emit('joined', {
        'room': room,
        'players': get_players_info(room)
    }, room=sid)
    emit('update_players', get_players_info(room), room=room)

@socketio.on('roll_dice')
def handle_roll_dice():
    sid = request.sid
    if sid not in players:
        return
    room = players[sid]['room']
    if not room or room not in rooms:
        return
    # Kiểm tra lượt
    if rooms[room].get('turn') != sid:
        emit('error', {'msg': 'Chưa đến lượt bạn!'}, room=sid)
        return
    dice = random.randint(1, 6)
    rooms[room]['dice'] = dice
    players[sid]['position'] = min(players[sid]['position'] + dice, 30)
    emit('dice_rolled', {
        'player': sid,
        'name': players[sid]['name'],
        'dice': dice,
        'position': players[sid]['position'],
        'winner': players[sid]['position'] == 30
    }, room=room)
    if players[sid]['position'] == 30:
        emit('game_over', {'winner': players[sid]['name']}, room=room)
        return
    next_turn(room)

def next_turn(room):
    players_list = rooms[room]['players']
    if not players_list:
        return
    current = rooms[room].get('turn')
    if current and current in players_list:
        idx = players_list.index(current)
        next_idx = (idx + 1) % len(players_list)
        next_player = players_list[next_idx]
    else:
        next_player = players_list[0]
    rooms[room]['turn'] = next_player
    emit('turn_update', {
        'turn': next_player,
        'name': players[next_player]['name']
    }, room=room)

def get_players_info(room):
    if room not in rooms:
        return []
    return [{
        'id': sid,
        'name': players[sid]['name'],
        'position': players[sid]['position']
    } for sid in rooms[room]['players']]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
