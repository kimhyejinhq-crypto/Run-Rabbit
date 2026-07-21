from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import eventlet
import uuid
import random
from models import Player
from game import Game
from constants import ITEM_INFO

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

games = {}
COLORS = ['Đỏ', 'Xanh', 'Vàng', 'Tím']

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('create_game')
def handle_create_game(data):
    player_name = data.get('player_name', 'Phi hành gia')
    character = data.get('character', 'tho')
    room_code = data.get('room_code', '').upper()
    if not room_code:
        room_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    if room_code in games:
        emit('error', {'message': 'Mã phòng đã tồn tại'})
        return
    player = Player(
        id=str(uuid.uuid4()),
        name=player_name,
        color=COLORS[0],
        character=character,
        position=1,
        gold=10
    )
    game = Game(room_code, player)
    games[room_code] = game
    join_room(room_code)
    emit('game_created', {
        'room_code': room_code,
        'player_id': player.id,
        'state': game.get_state().to_dict()
    }, room=request.sid)

@socketio.on('join_game')
def handle_join_game(data):
    room_code = data.get('room_code', '').upper()
    player_name = data.get('player_name', 'Phi hành gia')
    character = data.get('character', 'tho')
    if room_code not in games:
        emit('error', {'message': 'Phòng không tồn tại'})
        return
    game = games[room_code]
    if game.started:
        emit('error', {'message': 'Trò chơi đã bắt đầu'})
        return
    if len(game.players) >= 4:
        emit('error', {'message': 'Phòng đã đầy'})
        return
    existing_colors = [p.color for p in game.players]
    available_colors = [c for c in COLORS if c not in existing_colors]
    color = available_colors[0] if available_colors else random.choice(COLORS)
    player = Player(
        id=str(uuid.uuid4()),
        name=player_name,
        color=color,
        character=character,
        position=1,
        gold=10
    )
    game.add_player(player)
    join_room(room_code)
    emit('game_joined', {
        'player_id': player.id,
        'state': game.get_state().to_dict()
    }, room=request.sid)
    emit('player_joined', {
        'player': player.to_dict(),
        'state': game.get_state().to_dict()
    }, room=room_code, include_self=False)

@socketio.on('start_game')
def handle_start_game(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    if room_code not in games:
        return
    game = games[room_code]
    if game.players[0].id != player_id:
        emit('error', {'message': 'Chỉ chủ phòng mới có thể bắt đầu'})
        return
    if len(game.players) < 2:
        emit('error', {'message': 'Cần ít nhất 2 người chơi'})
        return
    game.start_game()
    emit('game_started', {'state': game.get_state().to_dict()}, room=room_code)

@socketio.on('roll_dice')
def handle_roll_dice(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    chosen_number = data.get('chosen_number')
    if room_code not in games:
        return
    game = games[room_code]
    current = game.players[game.current_player_index]
    if current.id != player_id:
        return
    if game.pending_action or game.pending_shop_tile:
        return
    result = game.roll_dice(player_id, chosen_number)
    if result == 0:
        return
    game.move_player(player_id, result)
    tile = game.board[current.position - 1]
    if tile.type.value == "VANG" and not game.game_over:
        game.pending_shop_tile = True
        emit('state_update', {'state': game.get_state().to_dict()}, room=room_code)
        return
    if not game.game_over:
        game.next_turn()
    emit('dice_result', {'dice': result, 'state': game.get_state().to_dict()}, room=room_code)
    emit('state_update', {'state': game.get_state().to_dict()}, room=room_code)

@socketio.on('use_item')
def handle_use_item(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    item_type = data.get('item_type')
    target_id = data.get('target_id')
    delta = data.get('delta')
    if room_code not in games:
        return
    game = games[room_code]
    current = game.players[game.current_player_index]
    if current.id != player_id:
        return
    if game.pending_action or game.pending_shop_tile:
        return
    success = game.use_item(player_id, item_type, target_id, delta)
    if success:
        if not game.pending_action and not game.game_over:
            game.next_turn()
        emit('state_update', {'state': game.get_state().to_dict()}, room=room_code)

@socketio.on('buy_item')
def handle_buy_item(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    item_type = data.get('item_type')
    if room_code not in games:
        return
    game = games[room_code]
    if game.pending_shop_tile:
        success = game.buy_item(player_id, item_type)
        if success:
            emit('state_update', {'state': game.get_state().to_dict()}, room=room_code)
        else:
            emit('error', {'message': 'Không thể mua vật phẩm'})

@socketio.on('skip_shop')
def handle_skip_shop(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    if room_code not in games:
        return
    game = games[room_code]
    game.skip_shop(player_id)
    emit('state_update', {'state': game.get_state().to_dict()}, room=room_code)

@socketio.on('resolve_pending')
def handle_resolve_pending(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    choice = data.get('choice', {})
    if room_code not in games:
        return
    game = games[room_code]
    if game.pending_action:
        game.resolve_pending(player_id, choice)
        emit('state_update', {'state': game.get_state().to_dict()}, room=room_code)

@socketio.on('get_state')
def handle_get_state(data):
    room_code = data.get('room_code')
    if room_code in games:
        emit('state_update', {'state': games[room_code].get_state().to_dict()}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
