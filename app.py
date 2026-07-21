from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Lưu trữ dữ liệu game
players = {}        # { sid: { 'name': str, 'room': str, 'position': int } }
rooms = {}          # { room: { 'players': [sid, ...], 'turn': sid, 'dice': int } }
room_names = set()  # để tạo mã phòng ngẫu nhiên

def generate_room_code():
    """Tạo mã phòng gồm 4 chữ cái in hoa"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in room_names:
            room_names.add(code)
            return code

# ------------------ Routes ------------------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# ------------------ Socket Events ------------------
@socketio.on('connect')
def handle_connect():
    print(f'🔗 Client connected: {request.sid}')
    players[request.sid] = {
        'name': None,
        'room': None,
        'position': 0
    }

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in players:
        room = players[sid]['room']
        if room and room in rooms:
            # Xóa người chơi khỏi phòng
            if sid in rooms[room]['players']:
                rooms[room]['players'].remove(sid)
            # Nếu phòng trống, xóa phòng
            if not rooms[room]['players']:
                room_names.discard(room)
                del rooms[room]
            else:
                # Cập nhật danh sách người chơi
                emit('update_players', get_players_info(room), room=room)
                # Nếu người rời là lượt hiện tại, chuyển lượt
                if rooms[room].get('turn') == sid:
                    next_turn(room)
        del players[sid]
    print(f'❌ Client disconnected: {sid}')

@socketio.on('create_room')
def handle_create_room(data):
    """Tạo phòng mới với tên nhân vật của người chơi"""
    sid = request.sid
    name = data.get('name', 'Rabbit')
    # Tạo mã phòng ngẫu nhiên
    room = generate_room_code()
    # Lưu thông tin
    players[sid]['name'] = name
    players[sid]['room'] = room
    players[sid]['position'] = 0

    # Tạo phòng
    rooms[room] = {
        'players': [sid],
        'turn': sid,   # người tạo phòng đi trước
        'dice': None
    }
    join_room(room)
    # Gửi mã phòng cho người tạo
    emit('room_created', {'room': room, 'players': [get_player_info(sid)]}, room=sid)
    # Thông báo cập nhật danh sách cho phòng
    emit('update_players', get_players_info(room), room=room)

@socketio.on('join_room')
def handle_join_room(data):
    sid = request.sid
    room = data.get('room').upper()
    name = data.get('name', 'Rabbit')

    if room not in rooms:
        emit('error', {'msg': 'Phòng không tồn tại!'}, room=sid)
        return
    if len(rooms[room]['players']) >= 4:
        emit('error', {'msg': 'Phòng đã đầy (tối đa 4 người)!'}, room=sid)
        return

    # Lưu thông tin
    players[sid]['name'] = name
    players[sid]['room'] = room
    players[sid]['position'] = 0
    rooms[room]['players'].append(sid)
    join_room(room)

    # Gửi xác nhận cho người join
    emit('joined', {'room': room, 'players': get_players_info(room)}, room=sid)
    # Cập nhật cho cả phòng
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

    # Tung xúc xắc (1-6)
    dice_value = random.randint(1, 6)
    rooms[room]['dice'] = dice_value
    # Di chuyển người chơi
    new_pos = players[sid]['position'] + dice_value
    # Giới hạn tối đa 30 ô
    if new_pos > 30:
        new_pos = 30
    players[sid]['position'] = new_pos

    # Thông báo kết quả cho mọi người trong phòng
    emit('dice_rolled', {
        'player': sid,
        'name': players[sid]['name'],
        'dice': dice_value,
        'position': new_pos,
        'winner': new_pos == 30
    }, room=room)

    # Kiểm tra người thắng
    if new_pos == 30:
        emit('game_over', {'winner': players[sid]['name']}, room=room)
        # Xóa phòng sau khi thắng (có thể giữ nguyên để reset)
        # Ở đây ta để nguyên, nhưng có thể thêm chức năng reset
        return

    # Chuyển lượt cho người tiếp theo
    next_turn(room)

def next_turn(room):
    """Chuyển lượt cho người kế tiếp trong danh sách"""
    players_list = rooms[room]['players']
    if not players_list:
        return
    current = rooms[room].get('turn')
    if current in players_list:
        idx = players_list.index(current)
        next_idx = (idx + 1) % len(players_list)
        next_player = players_list[next_idx]
    else:
        next_player = players_list[0]
    rooms[room]['turn'] = next_player
    emit('turn_update', {'turn': next_player, 'name': players[next_player]['name']}, room=room)

def get_player_info(sid):
    """Lấy thông tin 1 người chơi"""
    p = players[sid]
    return {
        'id': sid,
        'name': p['name'],
        'position': p['position']
    }

def get_players_info(room):
    """Lấy thông tin tất cả người chơi trong phòng"""
    if room not in rooms:
        return []
    return [get_player_info(sid) for sid in rooms[room]['players']]

# ------------------ Khởi chạy ------------------
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
