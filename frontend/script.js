// -------------------- Global state --------------------
const state = {
    socket: null,
    roomId: null,
    playerId: null,
    gameState: null,
    currentPlayerId: null,
    selectedCharacter: 'quang',
    playerName: 'Player',
};

// DOM elements
const $ = id => document.getElementById(id);
const loginScreen = $('login-screen');
const gameScreen = $('game-screen');
const playerNameInput = $('player-name');
const charOptions = document.querySelectorAll('.char-option');
const btnCreateRoom = $('btn-create-room');
const btnJoinRoom = $('btn-join-room');
const roomIdInput = $('room-id-input');
const loginError = $('login-error');
const roomIdDisplay = $('room-id-display');
const boardEl = $('board');
const playersInfoEl = $('players-info');
const notificationsEl = $('notifications');
const btnRoll = $('btn-roll');
const turnIndicator = $('turn-indicator');
const shopPanel = $('shop-panel');
const shopItemsEl = $('shop-items');
const btnCloseShop = $('btn-close-shop');
const helpModal = $('help-modal');
const btnHelp = $('btn-help');
const closeHelp = document.querySelector('#help-modal .close');

// -------------------- Character selection --------------------
charOptions.forEach(el => {
    el.addEventListener('click', () => {
        charOptions.forEach(opt => opt.classList.remove('selected'));
        el.classList.add('selected');
        state.selectedCharacter = el.dataset.char;
    });
});
// Mặc định chọn quang
document.querySelector('.char-option[data-char="quang"]').classList.add('selected');

// -------------------- Socket connection --------------------
function connectSocket(roomId, playerId) {
    state.socket = io();
    state.socket.on('connect', () => {
        console.log('Socket connected');
        state.socket.emit('join', { room_id: roomId, player_id: playerId });
    });
    state.socket.on('state_update', (data) => {
        state.gameState = data;
        renderGame(data);
    });
    state.socket.on('notification', (data) => {
        addNotification(data.message, data.category);
    });
    state.socket.on('error', (data) => {
        alert(data.message);
    });
}

// -------------------- API calls (HTTP) --------------------
async function createRoom() {
    const name = playerNameInput.value.trim() || 'Player';
    state.playerName = name;
    const response = await fetch('/api/create_room', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, character: state.selectedCharacter })
    });
    const data = await response.json();
    if (response.ok) {
        state.roomId = data.room_id;
        state.playerId = data.player_id;
        state.gameState = data.state;
        connectSocket(state.roomId, state.playerId);
        showGame();
    } else {
        loginError.textContent = data.error || 'Lỗi tạo phòng';
    }
}

async function joinRoom() {
    const roomId = roomIdInput.value.trim();
    if (!roomId) {
        loginError.textContent = 'Vui lòng nhập mã phòng';
        return;
    }
    const name = playerNameInput.value.trim() || 'Player';
    state.playerName = name;
    const response = await fetch('/api/join_room', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: roomId, name, character: state.selectedCharacter })
    });
    const data = await response.json();
    if (response.ok) {
        state.roomId = data.room_id;
        state.playerId = data.player_id;
        state.gameState = data.state;
        connectSocket(state.roomId, state.playerId);
        showGame();
    } else {
        loginError.textContent = data.error || 'Lỗi tham gia phòng';
    }
}

// -------------------- UI functions --------------------
function showGame() {
    loginScreen.classList.remove('active');
    gameScreen.classList.add('active');
    roomIdDisplay.textContent = state.roomId;
    // Lưu ý: chưa có state đầy đủ, sẽ render khi nhận state_update
}

function renderGame(gameState) {
    if (!gameState) return;
    renderBoard(gameState.board);
    renderPlayers(gameState.players, gameState.turn_order, gameState.current_turn_index);
    renderNotifications(gameState.notifications);
    // Cập nhật lượt
    const currentId = gameState.current_player_id;
    state.currentPlayerId = currentId;
    const isMyTurn = (currentId === state.playerId);
    btnRoll.disabled = !isMyTurn || gameState.game_over;
    if (gameState.game_over) {
        turnIndicator.textContent = '🏁 Game over!';
    } else if (currentId && gameState.players[currentId]) {
        const p = gameState.players[currentId];
        turnIndicator.textContent = `Lượt của ${p.name} (${p.character})`;
    } else {
        turnIndicator.textContent = 'Đang chờ...';
    }
    // Cửa hàng: hiển thị nếu người chơi hiện tại đang ở ô cửa hàng
    const myPlayer = gameState.players[state.playerId];
    if (myPlayer) {
        const currentTile = gameState.board[myPlayer.position];
        if (currentTile && (currentTile.type === 'CAM' || currentTile.type === 'TRANG')) {
            showShop(gameState);
        } else {
            shopPanel.style.display = 'none';
        }
    }
}

function renderBoard(board) {
    boardEl.innerHTML = '';
    for (let i = 1; i < board.length; i++) {
        const cell = document.createElement('div');
        cell.className = `cell ${board[i] ? board[i].type : ''}`;
        cell.textContent = i;
        // Hiển thị người chơi đang đứng ở ô này
        const playersHere = Object.values(state.gameState.players).filter(p => p.position === i);
        if (playersHere.length) {
            const container = document.createElement('div');
            container.className = 'players-here';
            playersHere.forEach(p => {
                const icon = document.createElement('span');
                icon.textContent = getCharIcon(p.character);
                container.appendChild(icon);
            });
            cell.appendChild(container);
        }
        boardEl.appendChild(cell);
    }
}

function renderPlayers(players, turnOrder, currentIndex) {
    playersInfoEl.innerHTML = '';
    Object.values(players).forEach(p => {
        const div = document.createElement('div');
        div.className = 'player-item';
        if (p.id === turnOrder[currentIndex]) div.classList.add('active');
        div.innerHTML = `
            <span class="char-icon">${getCharIcon(p.character)}</span>
            <span class="name">${p.name}</span>
            <span class="gold">💰 ${p.gold}</span>
            <span>Vị trí: ${p.position}</span>
            ${p.is_finished ? '🏁' : ''}
        `;
        playersInfoEl.appendChild(div);
    });
}

function renderNotifications(notifications) {
    if (!notifications) return;
    notificationsEl.innerHTML = '';
    notifications.forEach(n => {
        const div = document.createElement('div');
        div.className = `noti ${n.category}`;
        div.textContent = n.message;
        notificationsEl.appendChild(div);
    });
    // Tự động cuộn xuống cuối
    notificationsEl.scrollTop = notificationsEl.scrollHeight;
}

function addNotification(message, category) {
    const div = document.createElement('div');
    div.className = `noti ${category}`;
    div.textContent = message;
    notificationsEl.appendChild(div);
    notificationsEl.scrollTop = notificationsEl.scrollHeight;
}

function getCharIcon(char) {
    const map = {
        'quang': '🐧',
        'trang': '🐰',
        'thanh': '🦊',
        'jin': '🐱'
    };
    return map[char] || '🐧';
}

// -------------------- Shop --------------------
function showShop(gameState) {
    shopPanel.style.display = 'block';
    shopItemsEl.innerHTML = '';
    // Lấy danh sách items từ player (nếu có)
    const myPlayer = gameState.players[state.playerId];
    if (!myPlayer || !myPlayer.shop_items) {
        shopItemsEl.innerHTML = '<div>Không có vật phẩm nào</div>';
        return;
    }
    myPlayer.shop_items.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'shop-item';
        div.innerHTML = `
            <span>${item.name} (${item.price}💰) - ${item.effect}</span>
            <button data-index="${index}">Mua</button>
        `;
        shopItemsEl.appendChild(div);
    });
    // Gắn sự kiện mua
    shopItemsEl.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            state.socket.emit('buy_item', { item_index: idx });
        });
    });
}

btnCloseShop.addEventListener('click', () => {
    shopPanel.style.display = 'none';
});

// -------------------- Actions --------------------
btnRoll.addEventListener('click', () => {
    if (state.socket) {
        state.socket.emit('roll_dice', {});
    }
});

// Help modal
btnHelp.addEventListener('click', () => {
    helpModal.classList.add('active');
});
closeHelp.addEventListener('click', () => {
    helpModal.classList.remove('active');
});
window.addEventListener('click', (e) => {
    if (e.target === helpModal) helpModal.classList.remove('active');
});

// -------------------- Event listeners --------------------
btnCreateRoom.addEventListener('click', createRoom);
btnJoinRoom.addEventListener('click', joinRoom);
