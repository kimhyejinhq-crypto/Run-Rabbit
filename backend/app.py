# backend/app.py
# -*- coding: utf-8 -*-
"""
Flask + SocketIO Server - Game Vũ Trụ Đa Người Chơi
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import json
import os
import random
import threading
import time

from .game_engine import GameEngine
from .constants import BOARD_SIZE

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Lưu trữ các phòng game
games = {}
game_threads = {}

# ==================== ROUTES ====================

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

@socketio.on('create_game')
def handle_create_game(data):
    """Tạo phòng game mới"""
    room_code = data.get('room_code', '').upper().strip()
    if not room_code:
        room_code = generate_room_code()
    
    player_name = data.get('player_name', 'Phi hành gia')
    character = data.get('character', 'tho')
    
    if room_code in games:
        emit('error', {'message': 'Mã phòng đã tồn tại!'})
        return
    
    # Tạo game mới
    engine = GameEngine()
    player_id = engine.add_player(player_name, character)
    games[room_code] = {
        'engine': engine,
        'players': {player_id: request.sid},
        'owner': player_id
    }
    
    join_room(room_code)
    
    emit('game_created', {
        'room_code': room_code,
        'player_id': player_id,
        'state': engine.get_state(player_id)
    }, room=request.sid)

@socketio.on('join_game')
def handle_join_game(data):
    """Tham gia phòng game"""
    room_code = data.get('room_code', '').upper().strip()
    player_name = data.get('player_name', 'Phi hành gia')
    character = data.get('character', 'tho')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    game_data = games[room_code]
    engine = game_data['engine']
    
    if engine.is_full():
        emit('error', {'message': 'Phòng đã đầy (tối đa 4 người)!'})
        return
    
    player_id = engine.add_player(player_name, character)
    game_data['players'][player_id] = request.sid
    
    join_room(room_code)
    
    # Thông báo cho tất cả trong phòng
    emit('player_joined', {
        'player_id': player_id,
        'player': engine.get_player_info(player_id),
        'state': engine.get_state()
    }, room=room_code)
    
    emit('game_joined', {
        'player_id': player_id,
        'state': engine.get_state(player_id)
    }, room=request.sid)

@socketio.on('start_game')
def handle_start_game(data):
    """Bắt đầu game"""
    room_code = data.get('room_code', '').upper().strip()
    player_id = data.get('player_id')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    game_data = games[room_code]
    engine = game_data['engine']
    
    if game_data['owner'] != player_id:
        emit('error', {'message': 'Chỉ chủ phòng mới có thể bắt đầu!'})
        return
    
    if len(engine.players) < 2:
        emit('error', {'message': 'Cần ít nhất 2 người chơi!'})
        return
    
    engine.start_game()
    
    # Khởi chạy thread game loop
    if room_code not in game_threads or not game_threads[room_code].is_alive():
        thread = threading.Thread(target=game_loop, args=(room_code,))
        thread.daemon = True
        thread.start()
        game_threads[room_code] = thread
    
    emit('game_started', {
        'state': engine.get_state()
    }, room=room_code)

@socketio.on('roll_dice')
def handle_roll_dice(data):
    """Tung xúc xắc"""
    room_code = data.get('room_code', '').upper().strip()
    player_id = data.get('player_id')
    chosen_number = data.get('chosen_number')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    engine = games[room_code]['engine']
    
    try:
        result = engine.roll_dice(player_id, chosen_number)
        broadcast_state(room_code)
        emit('dice_result', result, room=room_code)
    except Exception as e:
        emit('error', {'message': str(e)}, room=request.sid)

@socketio.on('use_item')
def handle_use_item(data):
    """Sử dụng vật phẩm"""
    room_code = data.get('room_code', '').upper().strip()
    player_id = data.get('player_id')
    item_type = data.get('item_type')
    target_id = data.get('target_id')
    delta = data.get('delta')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    engine = games[room_code]['engine']
    
    try:
        engine.use_item(player_id, item_type, target_id, delta)
        broadcast_state(room_code)
    except Exception as e:
        emit('error', {'message': str(e)}, room=request.sid)

@socketio.on('buy_item')
def handle_buy_item(data):
    """Mua vật phẩm từ cửa hàng"""
    room_code = data.get('room_code', '').upper().strip()
    player_id = data.get('player_id')
    item_type = data.get('item_type')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    engine = games[room_code]['engine']
    
    try:
        engine.buy_item(player_id, item_type)
        broadcast_state(room_code)
    except Exception as e:
        emit('error', {'message': str(e)}, room=request.sid)

@socketio.on('skip_shop')
def handle_skip_shop(data):
    """Bỏ qua cửa hàng"""
    room_code = data.get('room_code', '').upper().strip()
    player_id = data.get('player_id')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    engine = games[room_code]['engine']
    engine.skip_shop(player_id)
    broadcast_state(room_code)

@socketio.on('resolve_pending')
def handle_resolve_pending(data):
    """Giải quyết hành động đang chờ"""
    room_code = data.get('room_code', '').upper().strip()
    player_id = data.get('player_id')
    choice = data.get('choice')
    
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
    
    engine = games[room_code]['engine']
    
    try:
        engine.resolve_pending(player_id, choice)
        broadcast_state(room_code)
    except Exception as e:
        emit('error', {'message': str(e)}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Xử lý ngắt kết nối"""
    for room_code, game_data in games.items():
        for player_id, sid in game_data['players'].items():
            if sid == request.sid:
                # Đánh dấu người chơi offline
                engine = game_data['engine']
                engine.set_player_offline(player_id)
                broadcast_state(room_code)
                break

# ==================== HELPERS ====================

def generate_room_code():
    """Tạo mã phòng ngẫu nhiên"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(6))

def broadcast_state(room_code):
    """Gửi trạng thái game cho tất cả trong phòng"""
    if room_code not in games:
        return
    engine = games[room_code]['engine']
    state = engine.get_state()
    # Thêm thông tin người chơi offline
    state['offline_players'] = engine.get_offline_players()
    socketio.emit('state_update', {'state': state}, room=room_code)

def game_loop(room_code):
    """Vòng lặp game chạy nền"""
    while room_code in games:
        engine = games[room_code]['engine']
        
        # Kiểm tra game over
        if engine.is_game_over():
            broadcast_state(room_code)
            break
        
        # Kiểm tra timeout lượt
        engine.check_turn_timeout()
        broadcast_state(room_code)
        
        time.sleep(1)

# ==================== MAIN ====================

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
