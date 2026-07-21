const socket = io();
let myId = null;
let selectedChar = null;
let playersData = [];
let currentRoom = null;

// DOM
const loginSection = document.getElementById('login-section');
const gameSection = document.getElementById('game-section');
const chars = document.querySelectorAll('.char');
const createBtn = document.getElementById('create-room-btn');
const joinBtn = document.getElementById('join-room-btn');
const roomInput = document.getElementById('room-code-input');
const errorMsg = document.getElementById('error-msg');
const roomCodeDisplay = document.getElementById('room-code-display');
const playerCountSpan = document.getElementById('player-count');
const playersList = document.getElementById('players-list');
const board = document.getElementById('board');
const rollBtn = document.getElementById('roll-btn');
const diceResult = document.getElementById('dice-result');
const turnIndicator = document.getElementById('turn-indicator');
const leaveBtn = document.getElementById('leave-room-btn');

// Chọn nhân vật
chars.forEach(char => {
    char.addEventListener('click', function() {
        chars.forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        selectedChar = this.dataset.name;
    });
});

// Tạo phòng
createBtn.addEventListener('click', function() {
    if (!selectedChar) { showError('Chọn nhân vật trước!'); return; }
    socket.emit('create_room', { name: selectedChar });
});

// Tham gia phòng
joinBtn.addEventListener('click', function() {
    if (!selectedChar) { showError('Chọn nhân vật trước!'); return; }
    const room = roomInput.value.trim().toUpperCase();
    if (!room) { showError('Nhập mã phòng!'); return; }
    socket.emit('join_room', { room: room, name: selectedChar });
});

// Socket events
socket.on('connect', () => {
    myId = socket.id;
    console.log('✅ Đã kết nối');
});

socket.on('room_created', (data) => {
    currentRoom = data.room;
    enterGame(data.players);
});

socket.on('joined', (data) => {
    currentRoom = data.room;
    enterGame(data.players);
});

socket.on('update_players', (players) => {
    playersData = players;
    updatePlayersUI(players);
    updateBoard(players);
    playerCountSpan.textContent = players.length;
});

socket.on('turn_update', (data) => {
    const isMyTurn = (data.turn === myId);
    rollBtn.disabled = !isMyTurn;
    if (isMyTurn) {
        turnIndicator.textContent = '🎯 Lượt của bạn!';
        turnIndicator.style.color = '#ffd700';
    } else {
        turnIndicator.textContent = `⏳ Lượt của ${data.name}`;
        turnIndicator.style.color = '#aaa';
    }
});

socket.on('dice_rolled', (data) => {
    // Cập nhật vị trí
    const player = playersData.find(p => p.id === data.player);
    if (player) player.position = data.position;
    updatePlayersUI(playersData);
    updateBoard(playersData);
    diceResult.innerHTML = `🎲 ${data.name} tung được <strong>${data.dice}</strong>`;
    if (data.winner) {
        setTimeout(() => alert(`🏆 ${data.name} đã về đích!`), 300);
    }
});

socket.on('game_over', (data) => {
    alert(`🏆 ${data.winner} chiến thắng!`);
});

socket.on('error', (data) => {
    showError(data.msg);
});

// Rời phòng
leaveBtn.addEventListener('click', () => {
    if (currentRoom) {
        socket.emit('leave_room', { room: currentRoom });
        location.reload();
    }
});

// Tung xúc xắc
rollBtn.addEventListener('click', () => {
    if (rollBtn.disabled) return;
    socket.emit('roll_dice');
});

// Helper
function showError(msg) { errorMsg.textContent = msg; }

function enterGame(players) {
    loginSection.style.display = 'none';
    gameSection.style.display = 'block';
    roomCodeDisplay.textContent = currentRoom;
    playersData = players;
    updatePlayersUI(players);
    updateBoard(players);
    playerCountSpan.textContent = players.length;
    // Tạo bàn cờ 30 ô
    board.innerHTML = '';
    for (let i = 0; i < 30; i++) {
        const cell = document.createElement('div');
        cell.className = 'board-cell';
        cell.dataset.index = i;
        cell.textContent = i + 1;
        board.appendChild(cell);
    }
    // Yêu cầu cập nhật lượt
    socket.emit('request_turn', { room: currentRoom });
}

function updatePlayersUI(players) {
    playersList.innerHTML = players.map(p => {
        const isMe = (p.id === myId);
        return `<li>${p.name} ${isMe ? '👈 (bạn)' : ''} - vị trí ${p.position}/30</li>`;
    }).join('');
}

function updateBoard(players) {
    document.querySelectorAll('.board-cell .player-icon').forEach(el => el.remove());
    document.querySelectorAll('.board-cell').forEach(cell => cell.classList.remove('has-player'));
    players.forEach(p => {
        const pos = p.position;
        if (pos >= 1 && pos <= 30) {
            const cell = document.querySelector(`.board-cell[data-index="${pos-1}"]`);
            if (cell) {
                cell.classList.add('has-player');
                const icon = document.createElement('span');
                icon.className = 'player-icon';
                if (p.name === 'Thỏ') icon.textContent = '🐇';
                else if (p.name === 'Chim cánh cụt') icon.textContent = '🐧';
                else if (p.name === 'Cáo') icon.textContent = '🦊';
                else if (p.name === 'Quạ') icon.textContent = '🐦‍⬛';
                else icon.textContent = '🐾';
                cell.appendChild(icon);
            }
        }
    });
}
