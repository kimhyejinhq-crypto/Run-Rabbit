# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import eventlet
from .game_room import create_room, get_room, delete_room
import uuid

app = Flask(__name__, static_folder='../frontend')
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Lưu trữ mapping socket_id -> player_id và room_id
sessions = {}

# ------------------- Routes HTTP -------------------
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

@app.route('/api/create_room', methods=['POST'])
def api_create_room():
    data = request.json
    player_name = data.get('name', 'Player')
    character = data.get('character', 'quang')
    room = create_room()
    player_id = str(uuid.uuid4())
    success = room.add_player(player_id, player_name, character)
    if not success:
        return jsonify({'error': 'Không thể thêm người chơi'}), 400
    return jsonify({
        'room_id': room.room_id,
        'player_id': player_id,
        'state': room.get_state()
    })

@app.route('/api/join_room', methods=['POST'])
def api_join_room():
    data = request.json
    room_id = data.get('room_id')
    player_name = data.get('name', 'Player')
    character = data.get('character', 'quang')
    room = get_room(room_id)
    if not room:
        return jsonify({'error': 'Phòng không tồn tại'}), 404
    player_id = str(uuid.uuid4())
    success = room.add_player(player_id, player_name, character)
    if not success:
        return jsonify({'error': 'Không thể thêm người chơi'}), 400
    return jsonify({
        'room_id': room.room_id,
        'player_id': player_id,
        'state': room.get_state()
    })

@app.route('/api/room/<room_id>/state')
def api_get_state(room_id):
    room = get_room(room_id)
    if not room:
        return jsonify({'error': 'Phòng không tồn tại'}), 404
    return jsonify(room.get_state())

# ------------------- SocketIO Events -------------------
@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)
    # Không tự động tham gia phòng, client sẽ gửi 'join'

@socketio.on('join')
def handle_join(data):
    room_id = data.get('room_id')
    player_id = data.get('player_id')
    if not room_id or not player_id:
        return
    room = get_room(room_id)
    if not room:
        emit('error', {'message': 'Phòng không tồn tại'})
        return
    # Kiểm tra player_id có trong phòng không
    if player_id not in room.engine.players:
        emit('error', {'message': 'Người chơi không tồn tại trong phòng'})
        return
    join_room(room_id)
    sessions[request.sid] = {'room_id': room_id, 'player_id': player_id}
    # Gửi trạng thái hiện tại cho người vừa join
    emit('state_update', room.get_state(), room=room_id)
    # Thông báo cho mọi người
    player_name = room.engine.players[player_id].name
    emit('notification', {'message': f'{player_name} đã tham gia!', 'category': 'info'}, room=room_id)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in sessions:
        room_id = sessions[sid]['room_id']
        player_id = sessions[sid]['player_id']
        leave_room(room_id)
        # Xóa người chơi khỏi phòng (có thể giữ lại hoặc xóa)
        # Ở đây ta xóa người chơi, nếu phòng trống thì xóa phòng
        room = get_room(room_id)
        if room:
            if player_id in room.engine.players:
                del room.engine.players[player_id]
                # Cập nhật turn_order
                room.engine.turn_order = [pid for pid in room.engine.turn_order if pid in room.engine.players]
                if not room.engine.players:
                    delete_room(room_id)
                else:
                    # Nếu người chơi hiện tại bị xóa, chuyển lượt
                    if room.engine.current_turn_index >= len(room.engine.turn_order):
                        room.engine.current_turn_index = 0
                    emit('state_update', room.get_state(), room=room_id)
        del sessions[sid]

@socketio.on('roll_dice')
def handle_roll_dice(data):
    sid = request.sid
    if sid not in sessions:
        return
    room_id = sessions[sid]['room_id']
    player_id = sessions[sid]['player_id']
    room = get_room(room_id)
    if not room:
        return
    # Kiểm tra lượt
    current = room.engine.get_current_player()
    if not current or current.id != player_id:
        emit('error', {'message': 'Chưa đến lượt bạn!'}, room=sid)
        return
    # Roll dice
    result = room.engine.roll_dice(player_id)
    if result:
        # Gửi trạng thái mới cho tất cả trong phòng
        emit('state_update', room.get_state(), room=room_id)
    else:
        emit('error', {'message': 'Không thể tung xúc xắc!'}, room=sid)

@socketio.on('buy_item')
def handle_buy_item(data):
    sid = request.sid
    if sid not in sessions:
        return
    room_id = sessions[sid]['room_id']
    player_id = sessions[sid]['player_id']
    item_index = data.get('item_index')
    room = get_room(room_id)
    if not room:
        return
    success = room.engine.buy_item(player_id, item_index)
    if success:
        emit('state_update', room.get_state(), room=room_id)
    else:
        emit('error', {'message': 'Không thể mua vật phẩm!'}, room=sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
