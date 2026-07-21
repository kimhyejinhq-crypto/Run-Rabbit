const socket = io();
let myId = null;
let selectedChar = null;
let playersData = [];

const loginSection = document.getElementById('login-section');
const gameSection = document.getElementById('game-section');
const chars = document.querySelectorAll('.char');
const joinBtn = document.getElementById('join-btn');
const errorMsg = document.getElementById('error-msg');
const playersList = document.getElementById('players-list');
const board = document.getElementById('board');
const rollBtn = document.getElementById('roll-btn');
const diceResult = document.getElementById('dice-result');
const playerCountSpan = document.getElementById('player-count');

chars.forEach(char => {
    char.addEventListener('click', function() {
        chars.forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        selectedChar = this.dataset.name;
        joinBtn.disabled = false;
    });
});

joinBtn.addEventListener('click', function() {
    if (!selectedChar) {
        showError('Chọn nhân vật!');
        return;
    }
    socket.emit('set_name', { name: selectedChar });
    loginSection.style.display = 'none';
    gameSection.style.display = 'block';
    board.innerHTML = '';
    for (let i = 0; i < 30; i++) {
        const cell = document.createElement('div');
        cell.className = 'board-cell';
        cell.dataset.index = i;
        cell.textContent = i + 1;
        board.appendChild(cell);
    }
});

socket.on('connect', () => {
    myId = socket.id;
    console.log('✅ Kết nối');
});

socket.on('room_joined', (data) => {
    playersData = data.players;
    updatePlayersUI(playersData);
    updateBoard(playersData);
    playerCountSpan.textContent = playersData.length;
});

socket.on('update_players', (players) => {
    playersData = players;
    updatePlayersUI(players);
    updateBoard(players);
    playerCountSpan.textContent = players.length;
});

socket.on('dice_rolled', (data) => {
    const player = playersData.find(p => p.id === data.player);
    if (player) {
        player.position = data.position;
    } else {
        playersData.push({ id: data.player, name: data.name, position: data.position });
    }
    updatePlayersUI(playersData);
    updateBoard(playersData);
    diceResult.innerHTML = `🎲 ${data.name} tung được <strong>${data.dice}</strong>`;
    if (data.winner) {
        setTimeout(() => alert(`🏆 ${data.name} về đích!`), 300);
    }
});

socket.on('game_over', (data) => {
    alert(`🏆 ${data.winner} chiến thắng!`);
});

rollBtn.addEventListener('click', function() {
    socket.emit('roll_dice');
});

function showError(msg) {
    errorMsg.textContent = msg;
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
