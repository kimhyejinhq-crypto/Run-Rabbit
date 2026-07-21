// ========== Kết nối Socket.IO ==========
const socket = io(window.location.origin, {
    transports: ['websocket', 'polling']
});

// DOM elements
const loginSection = document.getElementById('login-section');
const gameSection = document.getElementById('game-section');
const errorMsg = document.getElementById('error-msg');

const chars = document.querySelectorAll('.char');
const createBtn = document.getElementById('create-room-btn');
const joinBtn = document.getElementById('join-room-btn');
const roomInput = document.getElementById('room-code-input');
const roomCodeDisplay = document.getElementById('room-code-display');
const playerCountSpan = document.getElementById('player-count');
const playersList = document.getElementById('players-list');
const board = document.getElementById('board');
const rollBtn = document.getElementById('roll-btn');
const diceResult = document.getElementById('dice-result');
const turnIndicator = document.getElementById('turn-indicator');
const leaveBtn = document.getElementById('leave-room-btn');

let selectedChar = null;          // tên nhân vật
let currentRoom = null;           // mã phòng hiện tại
let playersData = [];             // danh sách người chơi trong phòng
let myId = null;                  // socket.id của mình

// ========== Chọn nhân vật ==========
chars.forEach(char => {
    char.addEventListener('click', function() {
        chars.forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        selectedChar = this.dataset.name;
        // Cập nhật UI: enable buttons
        updateLoginButtons();
    });
});

function updateLoginButtons() {
    const hasChar = selectedChar !== null;
    createBtn.disabled = !hasChar;
    joinBtn.disabled = !hasChar;
}

// ========== Tạo phòng ==========
createBtn.addEventListener('click', function() {
    if (!selectedChar) {
        showError('Vui lòng chọn nhân vật!');
        return;
    }
    socket.emit('create_room', { name: selectedChar });
});

// ========== Tham gia phòng ==========
joinBtn.addEventListener('click', function() {
    if (!selectedChar) {
        showError('Vui lòng chọn nhân vật!');
        return;
    }
    const code = roomInput.value.trim().toUpperCase();
    if (!code) {
        showError('Nhập mã phòng!');
        return;
    }
    socket.emit('join_room', { room: code, name: selectedChar });
});

// ========== Sự kiện Socket ==========
socket.on('connect', () => {
    myId = socket.id;
    console.log('✅ Đã kết nối server');
});

socket.on('room_created', (data) => {
    currentRoom = data.room;
    roomCodeDisplay.textContent = currentRoom;
    enterGame(data.players);
    showError(''); // xóa lỗi
});

socket.on('joined', (data) => {
    currentRoom = data.room;
    roomCodeDisplay.textContent = currentRoom;
    enterGame(data.players);
    showError('');
});

socket.on('update_players', (players) => {
    playersData = players;
    updatePlayersUI(players);
    updateBoard(players);
    // Cập nhật số người
    playerCountSpan.textContent = players.length;
    // Cho phép tung xúc xắc nếu đến lượt mình (sẽ được cập nhật qua turn_update)
});

socket.on('turn_update', (data) => {
    const isMyTurn = (data.turn === myId);
    rollBtn.disabled = !isMyTurn;
    if (isMyTurn) {
        turnIndicator.textContent = '🎯 Lượt của bạn!';
        turnIndicator.style.color = '#ffd700';
    } else {
        const name = data.name || 'Người khác';
        turnIndicator.textContent = `⏳ Lượt của ${name}`;
        turnIndicator.style.color = '#aaa';
    }
});

socket.on('dice_rolled', (data) => {
    // Cập nhật vị trí nhân vật
    const player = playersData.find(p => p.id === data.player);
    if (player) {
        player.position = data.position;
    } else {
        // Nếu chưa có, thêm mới (trường hợp join sau)
        playersData.push({
            id: data.player,
            name: data.name,
            position: data.position
        });
    }
    updatePlayersUI(playersData);
    updateBoard(playersData);
    // Hiển thị kết quả xúc xắc
    diceResult.innerHTML = `🎲 ${data.name} tung được <strong>${data.dice}</strong>`;
    if (data.winner) {
        setTimeout(() => {
            alert(`🏆 ${data.name} đã về đích! Chiến thắng!`);
        }, 300);
    }
});

socket.on('game_over', (data) => {
    alert(`🏆 ${data.winner} đã chiến thắng!`);
    // Có thể reset hoặc reload
});

socket.on('error', (data) => {
    showError(data.msg);
});

// ========== Rời phòng ==========
leaveBtn.addEventListener('click', function() {
    if (currentRoom) {
        socket.emit('leave_room', { room: currentRoom });
        // Reload lại trang để reset
        location.reload();
    }
});

// ========== Tung xúc xắc ==========
rollBtn.addEventListener('click', function() {
    if (rollBtn.disabled) return;
    socket.emit('roll_dice');
});

// ========== UI Helpers ==========
function showError(msg) {
    errorMsg.textContent = msg;
}

function enterGame(players) {
    loginSection.style.display = 'none';
    gameSection.style.display = 'block';
    playersData = players;
    updatePlayersUI(players);
    updateBoard(players);
    playerCountSpan.textContent = players.length;
    // Yêu cầu cập nhật lượt (server sẽ gửi turn_update)
    socket.emit('request_turn', { room: currentRoom });
    // Tạo board 30 ô
    board.innerHTML = '';
    for (let i = 0; i < 30; i++) {
        const cell = document.createElement('div');
        cell.className = 'board-cell';
        cell.dataset.index = i;
        cell.textContent = i + 1;
        board.appendChild(cell);
    }
}

function updatePlayersUI(players) {
    playersList.innerHTML = players.map(p => {
        const isMe = (p.id === myId);
        return `<li>${p.name} ${isMe ? '👈 (bạn)' : ''} - vị trí ${p.position}/30</li>`;
    }).join('');
}

function updateBoard(players) {
    // Xóa các icon cũ
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
                // Gán emoji theo tên (có thể đơn giản)
                icon.textContent = '🐇'; // default
                if (p.name.includes('Thỏ')) icon.textContent = '🐇';
                else if (p.name.includes('Sóc')) icon.textContent = '🐿️';
                else if (p.name.includes('Mèo')) icon.textContent = '🐈';
                else if (p.name.includes('Chó')) icon.textContent = '🐕';
                else icon.textContent = '🐾';
                cell.appendChild(icon);
            }
        }
    });
}

// ========== Yêu cầu lượt ban đầu ==========
socket.on('turn_update', (data) => {
    // đã xử lý ở trên, nhưng cần đảm bảo khi vào phòng
    // Chúng ta sẽ emit request_turn sau khi vào game
});

// Thêm sự kiện yêu cầu lượt
socket.on('connect', () => {
    // Sau khi kết nối, nếu đã trong phòng (reload) thì request turn
    if (currentRoom) {
        socket.emit('request_turn', { room: currentRoom });
    }
});

// ========== Xử lý reload / mất kết nối ==========
socket.on('disconnect', () => {
    showError('Mất kết nối server! Đang thử kết nối lại...');
});

socket.on('reconnect', () => {
    showError('');
    if (currentRoom) {
        // Gửi lại thông tin phòng để cập nhật
        socket.emit('rejoin', { room: currentRoom });
    }
});

// Thêm xử lý leave_room (server sẽ xử lý)
socket.on('left_room', () => {
    location.reload();
});

// ========== Khởi tạo ==========
// Mặc định disable các nút cho đến khi chọn nhân vật
createBtn.disabled = true;
joinBtn.disabled = true;

// Thêm sự kiện cho phím Enter trong ô nhập mã
roomInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') joinBtn.click();
});
