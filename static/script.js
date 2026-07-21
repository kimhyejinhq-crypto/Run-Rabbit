// =====================================================================
// scripts.js - Hành Tinh Xiếc (OFFLINE - không cần server)
// =====================================================================

// ===== STATE =====
let state = {
    players: [],
    board: [],
    current_player_index: 0,
    turn_count: 0,
    game_over: false,
    winner_id: null,
    log: [],
    pending_shop_tile: false,
    item_stock: {
        'XUC_XAC_X2': 3,
        'LA_CHAN': 3,
        'DAO_GAM': 2,
        'BUA_HO_MENH': 2,
        'KINH_AP_TRONG': 3
    },
    item_info: {
        'XUC_XAC_X2': { name: 'Xúc Xắc X2', emoji: '🎲', price: 7, desc: 'Tung 2 lần, lấy kết quả cao hơn' },
        'LA_CHAN': { name: 'Lá Chắn', emoji: '🛡️', price: 5, desc: 'Chặn 1 hiệu ứng xấu' },
        'DAO_GAM': { name: 'Dao Găm', emoji: '🔪', price: 8, desc: 'Đá lùi 4 ô người trong bán kính 3 ô' },
        'BUA_HO_MENH': { name: 'Bùa Hộ Mệnh', emoji: '🪆', price: 10, desc: 'Được tung thêm 1 lượt' },
        'KINH_AP_TRONG': { name: 'Kính Áp Tròng', emoji: '👁️', price: 6, desc: 'Điều chỉnh +1/-1 điểm xúc xắc' }
    }
};

let myPlayer = null;
let isMyTurn = true;
let roomCode = '';
let selectedCharacter = 'tho';
let isGameStarted = false;
let diceResult = 0;

// ===== DOM REFS =====
const $ = id => document.getElementById(id);

// ===== CHARACTER SELECTION =====
document.querySelectorAll('.char-option').forEach(el => {
    el.addEventListener('click', () => {
        document.querySelectorAll('.char-option').forEach(c => c.classList.remove('selected'));
        el.classList.add('selected');
        selectedCharacter = el.dataset.char;
    });
});
document.querySelector('.char-option[data-char="tho"]')?.classList.add('selected');

// ===== ROOM CODE =====
$('btn-random-code').addEventListener('click', () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) code += chars[Math.floor(Math.random() * chars.length)];
    $('room-code').value = code;
});

// ===== CREATE BOARD =====
function createBoard() {
    const board = [];
    for (let i = 1; i <= 100; i++) {
        let type = 'TRONG';
        if (i === 100) type = 'DICH';
        else if ([20, 50, 80].includes(i)) type = 'VANG';
        else if ([5, 15, 25, 35, 45, 55, 65, 75, 85, 95].includes(i)) type = 'DO';
        else if ([10, 30, 40, 60, 70, 90].includes(i)) type = 'XANH';
        else if ([7, 17, 27, 37, 47, 57, 67, 77, 87, 97].includes(i)) type = 'TIM';
        else if ([12, 22, 32, 42, 52, 62, 72, 82, 92].includes(i)) type = 'CAM';
        else if ([8, 18, 28, 38, 48, 58, 68, 78, 88, 98].includes(i)) type = 'HONG';
        board.push({ index: i, type });
    }
    return board;
}

// ===== LOBBY =====
$('btn-create-room').addEventListener('click', () => {
    const name = $('player-name').value.trim() || 'Phi hành gia';
    const code = $('room-code').value.trim().toUpperCase() || generateRoomCode();
    roomCode = code;
    
    // Tạo người chơi
    const colors = ['Đỏ', 'Xanh', 'Vàng', 'Tím'];
    const emojis = { 'tho': '🐰', 'chim': '🐧', 'cao': '🦊', 'qua': '🐦‍⬛' };
    myPlayer = {
        id: 'p1',
        name,
        color: colors[0],
        character: selectedCharacter,
        position: 1,
        gold: 10,
        debt: 0,
        items: [],
        statuses: [],
        finished: false,
        offline: false
    };
    
    state.players = [myPlayer];
    state.board = createBoard();
    state.log = ['🚀 Phòng đã được tạo!'];
    state.current_player_index = 0;
    state.turn_count = 0;
    state.game_over = false;
    state.winner_id = null;
    state.pending_shop_tile = false;
    state.item_stock = {
        'XUC_XAC_X2': 3,
        'LA_CHAN': 3,
        'DAO_GAM': 2,
        'BUA_HO_MENH': 2,
        'KINH_AP_TRONG': 3
    };
    
    enterWaitingRoom();
});

$('btn-join-room').addEventListener('click', () => {
    const name = $('player-name').value.trim() || 'Phi hành gia';
    const code = $('room-code').value.trim().toUpperCase();
    if (!code) {
        $('lobby-error').textContent = 'Vui lòng nhập mã phòng!';
        return;
    }
    // Trong offline, tự tạo phòng mới nếu chưa có
    roomCode = code;
    const colors = ['Đỏ', 'Xanh', 'Vàng', 'Tím'];
    myPlayer = {
        id: 'p1',
        name,
        color: colors[0],
        character: selectedCharacter,
        position: 1,
        gold: 10,
        debt: 0,
        items: [],
        statuses: [],
        finished: false,
        offline: false
    };
    state.players = [myPlayer];
    state.board = createBoard();
    state.log = ['🚀 Tham gia phòng thành công!'];
    state.current_player_index = 0;
    state.turn_count = 0;
    state.game_over = false;
    state.pending_shop_tile = false;
    enterWaitingRoom();
});

function generateRoomCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) code += chars[Math.floor(Math.random() * chars.length)];
    return code;
}

// ===== WAITING ROOM =====
function enterWaitingRoom() {
    $('screen-lobby').classList.add('hidden');
    $('screen-waiting').classList.remove('hidden');
    $('waiting-room-code').textContent = roomCode;
    renderWaitingPlayers();
    $('btn-start-game').style.display = 'block';
}

function renderWaitingPlayers() {
    const list = $('waiting-players');
    list.innerHTML = '';
    state.players.forEach(p => {
        const div = document.createElement('div');
        div.className = 'waiting-player';
        div.innerHTML = `
            <span class="emoji">${getCharacterEmoji(p.character)}</span>
            <span class="name">${p.name}</span>
            <span class="status ready">⭐ Bạn</span>
        `;
        list.appendChild(div);
    });
}

$('btn-start-game').addEventListener('click', () => {
    startGame();
});

$('btn-leave').addEventListener('click', () => {
    window.location.reload();
});

// ===== START GAME =====
function startGame() {
    isGameStarted = true;
    $('screen-waiting').classList.add('hidden');
    $('screen-game').classList.remove('hidden');
    state.log.push('🚀 Trò chơi bắt đầu!');
    renderGame();
}

// ===== RENDER GAME =====
function renderGame() {
    if (!state || state.players.length === 0) return;
    
    // Cập nhật topbar
    myPlayer = state.players.find(p => p.id === 'p1');
    if (myPlayer) {
        $('stat-gold').textContent = myPlayer.gold;
        $('stat-turn').textContent = state.turn_count;
    }
    $('stat-timer').textContent = '45:00';
    
    // Turn indicator
    const current = state.players[state.current_player_index];
    if (current) {
        const isMe = current.id === 'p1';
        $('turn-indicator').textContent = isMe ? '🎯 Lượt của bạn!' : `⏳ Đợi ${current.name}...`;
        $('turn-indicator').style.color = isMe ? '#4ECDC4' : 'var(--text-secondary)';
        isMyTurn = isMe && !state.game_over;
    }
    
    // Board, players, log, dice
    renderBoard();
    renderPlayers();
    renderLog();
    renderDiceState();
    renderShopModal();
    renderEndModal();
}

// ===== RENDER BOARD =====
function renderBoard() {
    const board = $('board');
    board.innerHTML = '';
    
    const grid = [];
    for (let row = 9; row >= 0; row--) {
        const start = row * 10 + 1;
        let nums = Array.from({length: 10}, (_, i) => start + i);
        if (row % 2 === 1) nums = nums.reverse();
        grid.push(...nums);
    }
    
    const tilesByIndex = {};
    state.board.forEach(t => tilesByIndex[t.index] = t);
    
    const playersByPos = {};
    state.players.forEach(p => {
        if (!p.finished && !p.offline) {
            if (!playersByPos[p.position]) playersByPos[p.position] = [];
            playersByPos[p.position].push(p);
        }
    });
    
    grid.forEach(num => {
        const tile = tilesByIndex[num];
        if (!tile) return;
        
        const div = document.createElement('div');
        div.className = `tile tile-${tile.type}`;
        
        const number = document.createElement('span');
        number.className = 'tile-number';
        number.textContent = num;
        div.appendChild(number);
        
        const tokWrap = document.createElement('div');
        tokWrap.className = 'tile-tokens';
        const playersHere = playersByPos[num] || [];
        playersHere.forEach(p => {
            const tok = document.createElement('span');
            tok.className = 'tok';
            tok.title = p.name;
            tok.textContent = getCharacterEmoji(p.character);
            tokWrap.appendChild(tok);
        });
        div.appendChild(tokWrap);
        
        if (myPlayer && myPlayer.position === num) {
            div.classList.add('has-player');
        }
        
        board.appendChild(div);
    });
    
    // Camera follow
    if (myPlayer) {
        const viewport = $('board-viewport');
        const pos = myPlayer.position;
        const row = Math.floor((pos - 1) / 10);
        const col = (pos - 1) % 10;
        const isEvenRow = row % 2 === 0;
        const actualCol = isEvenRow ? col : 9 - col;
        
        const tileSize = 50;
        const targetX = -(actualCol * tileSize - viewport.offsetWidth / 2 + tileSize / 2);
        const targetY = -((9 - row) * tileSize - viewport.offsetHeight / 2 + tileSize / 2);
        const boardWidth = 10 * tileSize;
        const boardHeight = 10 * tileSize;
        board.style.transform = `translate(${Math.min(0, Math.max(-boardWidth + viewport.offsetWidth, targetX))}px, ${Math.min(0, Math.max(-boardHeight + viewport.offsetHeight, targetY))}px)`;
    }
}

// ===== RENDER PLAYERS =====
function renderPlayers() {
    const panel = $('players-panel');
    panel.innerHTML = '<h3>🎭 Phi hành gia</h3>';
    
    const colorMap = { 'Đỏ': '#FF6B6B', 'Xanh': '#4ECDC4', 'Vàng': '#FFD93D', 'Tím': '#6C5CE7' };
    
    state.players.forEach(p => {
        const card = document.createElement('div');
        card.className = 'player-card';
        if (p.id === state.players[state.current_player_index]?.id && !state.game_over) {
            card.classList.add('active');
        }
        if (p.finished) card.classList.add('finished');
        if (p.offline) card.classList.add('offline');
        
        const itemText = p.items.length ? p.items.map(i => {
            const info = state.item_info[i];
            return info ? info.emoji : '?';
        }).join(' ') : '—';
        
        card.innerHTML = `
            <div class="p-name">
                <span class="player-dot" style="background:${colorMap[p.color] || '#888'}"></span>
                ${getCharacterEmoji(p.character)} ${p.name} ${p.finished ? '🏆' : ''} ${p.offline ? '📴' : ''}
            </div>
            <div class="p-row"><span>📍 Ô</span><span>${p.position}</span></div>
            <div class="p-row"><span>🪙 Vàng</span><span>${p.gold}${p.debt > 0 ? ` (nợ ${p.debt})` : ''}</span></div>
            <div class="p-row"><span>📦 Vật phẩm</span><span>${itemText}</span></div>
        `;
        
        if (p.id === 'p1' && isMyTurn && !state.game_over && p.items.length > 0) {
            const useWrap = document.createElement('div');
            useWrap.style.marginTop = '0.3rem';
            useWrap.style.display = 'flex';
            useWrap.style.gap = '0.3rem';
            useWrap.style.flexWrap = 'wrap';
            p.items.forEach(itemType => {
                const info = state.item_info[itemType];
                if (!info) return;
                const btn = document.createElement('button');
                btn.className = 'btn-ghost';
                btn.style.fontSize = '0.7rem';
                btn.style.padding = '0.2rem 0.5rem';
                btn.textContent = `${info.emoji} Dùng`;
                btn.addEventListener('click', () => handleUseItem(itemType));
                useWrap.appendChild(btn);
            });
            card.appendChild(useWrap);
        }
        
        panel.appendChild(card);
    });
}

// ===== RENDER LOG =====
function renderLog() {
    const list = $('log-list');
    list.innerHTML = '';
    (state.log || []).slice().reverse().forEach(line => {
        const div = document.createElement('div');
        div.textContent = line;
        if (line.includes('🏆') || line.includes('🚀')) {
            div.style.color = 'var(--text-glow)';
        }
        list.appendChild(div);
    });
}

// ===== DICE =====
function renderDiceState() {
    const btn = $('btn-roll');
    const luckyPicker = $('lucky-picker');
    const isBlocked = state.game_over || state.pending_shop_tile || !isMyTurn;
    btn.disabled = isBlocked;
    
    // Kiểm tra Bùa Hộ Mệnh
    if (myPlayer) {
        const luckyStatus = (myPlayer.statuses || []).find(s => s.kind === 'lucky_charm');
        if (luckyStatus && !isBlocked) {
            btn.classList.add('hidden');
            luckyPicker.classList.remove('hidden');
        } else {
            btn.classList.remove('hidden');
            luckyPicker.classList.add('hidden');
        }
    }
}

$('btn-roll').addEventListener('click', () => {
    if (!myPlayer || state.game_over || state.pending_shop_tile) return;
    const result = rollDice();
    diceResult = result;
    animateDice(result);
    movePlayer(myPlayer, result);
});

document.querySelectorAll('.lucky-numbers button').forEach(btn => {
    btn.addEventListener('click', () => {
        const result = Number(btn.dataset.n);
        diceResult = result;
        animateDice(result);
        movePlayer(myPlayer, result);
    });
});

function rollDice() {
    return Math.floor(Math.random() * 6) + 1;
}

function animateDice(value) {
    const face = $('dice-face');
    const val = $('dice-value');
    face.classList.add('rolling');
    val.textContent = value;
    setTimeout(() => face.classList.remove('rolling'), 600);
}

// ===== MOVE PLAYER =====
function movePlayer(player, steps) {
    if (state.game_over) return;
    const newPos = player.position + steps;
    if (newPos >= 100) {
        player.position = 100;
        player.finished = true;
        state.log.push(`🏁 ${player.name} đã về đích!`);
        state.game_over = true;
        state.winner_id = player.id;
        state.log.push(`🏆 ${player.name} chiến thắng!`);
        renderGame();
        return;
    }
    player.position = newPos;
    applyTileEffect(player);
    if (!state.game_over && !state.pending_shop_tile) {
        nextTurn();
    }
    renderGame();
}

// ===== APPLY TILE EFFECT =====
function applyTileEffect(player) {
    const tile = state.board[player.position - 1];
    switch (tile.type) {
        case 'VANG':
            player.gold += 5;
            state.log.push(`💰 ${player.name} nhận 5 vàng từ ô Vàng`);
            break;
        case 'DO':
            if (player.gold >= 3) {
                player.gold -= 3;
                state.log.push(`💔 ${player.name} mất 3 vàng`);
            } else {
                player.position = Math.max(1, player.position - 3);
                state.log.push(`⬅️ ${player.name} lùi 3 ô`);
            }
            break;
        case 'XANH':
            const target = Math.floor(Math.random() * 100) + 1;
            player.position = target;
            state.log.push(`🌀 ${player.name} nhảy đến ô ${target}`);
            break;
        case 'TIM':
            player.gold += 5;
            state.log.push(`🌟 ${player.name} nhận 5 vàng từ Sự kiện`);
            break;
        case 'CAM':
            player.gold = Math.max(0, player.gold - 3);
            state.log.push(`💥 ${player.name} mất 3 vàng từ Bẫy`);
            break;
        case 'HONG':
            player.gold = Math.max(0, player.gold - 2);
            state.log.push(`🚪 ${player.name} trả 2 vàng`);
            break;
        case 'TRONG':
            for (let other of state.players) {
                if (other.id !== player.id && other.position === player.position && !other.finished) {
                    if (other.gold > 0) {
                        other.gold -= 1;
                        player.gold += 1;
                        state.log.push(`🔪 ${player.name} cướp 1 vàng từ ${other.name}`);
                        break;
                    }
                }
            }
            break;
        case 'DICH':
            state.log.push(`🏁 ${player.name} đã về đích!`);
            player.finished = true;
            state.game_over = true;
            state.winner_id = player.id;
            state.log.push(`🏆 ${player.name} chiến thắng!`);
            break;
    }
    
    // Kiểm tra nếu đang ở ô Vàng (20,50,80) thì mở cửa hàng
    if ([20, 50, 80].includes(player.position) && !state.game_over) {
        state.pending_shop_tile = true;
    }
}

// ===== NEXT TURN =====
function nextTurn() {
    if (state.game_over) return;
    state.current_player_index = (state.current_player_index + 1) % state.players.length;
    state.turn_count++;
    // Nếu người chơi đã finish hoặc offline thì bỏ qua
    let attempts = 0;
    while (state.players[state.current_player_index].finished || state.players[state.current_player_index].offline) {
        state.current_player_index = (state.current_player_index + 1) % state.players.length;
        attempts++;
        if (attempts > state.players.length) {
            state.game_over = true;
            state.log.push('🏆 Tất cả người chơi đã về đích!');
            break;
        }
    }
    if (state.game_over) {
        state.winner_id = state.players.find(p => p.finished)?.id || state.players[0].id;
    }
}

// ===== USE ITEM =====
function handleUseItem(itemType) {
    if (!myPlayer || state.game_over || state.pending_shop_tile) return;
    const player = myPlayer;
    if (!player.items.includes(itemType)) return;
    
    if (itemType === 'XUC_XAC_X2') {
        // Tung 2 lần lấy kết quả cao hơn
        const r1 = rollDice();
        const r2 = rollDice();
        const result = Math.max(r1, r2);
        state.log.push(`🎲 ${player.name} dùng Xúc Xắc X2: ${r1} và ${r2} → lấy ${result}`);
        diceResult = result;
        animateDice(result);
        movePlayer(player, result);
        player.items = player.items.filter(i => i !== itemType);
        return;
    }
    
    if (itemType === 'LA_CHAN') {
        player.statuses.push({ kind: 'shield', value: 1 });
        state.log.push(`🛡️ ${player.name} kích hoạt Lá Chắn`);
        player.items = player.items.filter(i => i !== itemType);
        renderGame();
        return;
    }
    
    if (itemType === 'DAO_GAM') {
        // Tìm mục tiêu gần nhất
        let target = null;
        let minDist = Infinity;
        for (let p of state.players) {
            if (p.id !== player.id && !p.finished && !p.offline) {
                const dist = Math.abs(p.position - player.position);
                if (dist <= 3 && dist < minDist) {
                    minDist = dist;
                    target = p;
                }
            }
        }
        if (target) {
            target.position = Math.max(1, target.position - 4);
            state.log.push(`🔪 ${player.name} đá ${target.name} lùi 4 ô`);
        } else {
            state.log.push(`❌ Không có mục tiêu trong bán kính 3 ô`);
        }
        player.items = player.items.filter(i => i !== itemType);
        renderGame();
        return;
    }
    
    if (itemType === 'BUA_HO_MENH') {
        player.statuses.push({ kind: 'extra_turn', value: 1 });
        state.log.push(`🪆 ${player.name} nhận thêm 1 lượt từ Bùa Hộ Mệnh`);
        player.items = player.items.filter(i => i !== itemType);
        renderGame();
        return;
    }
    
    if (itemType === 'KINH_AP_TRONG') {
        const delta = Math.random() > 0.5 ? 1 : -1;
        player.statuses.push({ kind: 'lens', value: delta });
        state.log.push(`👁️ ${player.name} điều chỉnh xúc xắc ${delta > 0 ? '+' : ''}${delta}`);
        player.items = player.items.filter(i => i !== itemType);
        renderGame();
        return;
    }
}

// ===== SHOP =====
function renderShopModal() {
    const modal = $('modal-shop');
    if (!state.pending_shop_tile || state.game_over) {
        modal.classList.add('hidden');
        return;
    }
    modal.classList.remove('hidden');
    
    const wrap = $('shop-items');
    wrap.innerHTML = '';
    
    Object.entries(state.item_info).forEach(([key, info]) => {
        const stock = state.item_stock[key] || 0;
        const canBuy = stock > 0 && myPlayer && myPlayer.gold >= info.price && myPlayer.items.length < 2;
        
        const div = document.createElement('div');
        div.className = 'shop-item';
        div.innerHTML = `
            <div>
                <strong>${info.emoji} ${info.name}</strong> — ${info.price} vàng (còn ${stock})
                <div class="si-info">${info.desc}</div>
            </div>
        `;
        const btn = document.createElement('button');
        btn.textContent = 'Mua';
        btn.disabled = !canBuy;
        btn.addEventListener('click', () => {
            if (myPlayer.gold >= info.price && stock > 0) {
                myPlayer.gold -= info.price;
                state.item_stock[key]--;
                myPlayer.items.push(key);
                state.log.push(`🛒 ${myPlayer.name} mua ${info.emoji} ${info.name}`);
                renderGame();
            }
        });
        div.appendChild(btn);
        wrap.appendChild(div);
    });
}

$('btn-skip-shop').addEventListener('click', () => {
    state.pending_shop_tile = false;
    state.log.push(`🚶 ${myPlayer.name} bỏ qua cửa hàng`);
    nextTurn();
    renderGame();
});

// ===== END =====
function renderEndModal() {
    const modal = $('modal-end');
    if (!state.game_over) {
        modal.classList.add('hidden');
        return;
    }
    modal.classList.remove('hidden');
    
    const winner = state.players.find(p => p.id === state.winner_id);
    $('end-title').textContent = winner ? `🏆 ${winner.name} chiến thắng!` : '🏆 Kết thúc!';
    $('end-desc').textContent = winner ? `${winner.name} đã về đích và trở thành nhà vô địch vũ trụ!` : 'Cuộc đua đã kết thúc.';
    
    const stats = $('end-stats');
    stats.innerHTML = '';
    state.players.sort((a, b) => b.gold - a.gold).forEach(p => {
        const div = document.createElement('div');
        div.className = 'end-stat';
        div.innerHTML = `
            <div class="name">${p.name}</div>
            <div class="gold">🪙 ${p.gold} vàng</div>
            <div style="font-size:0.7rem;color:var(--text-secondary)">Ô ${p.position}</div>
        `;
        stats.appendChild(div);
    });
}

$('btn-restart').addEventListener('click', () => {
    window.location.reload();
});

// ===== HELP =====
$('btn-help').addEventListener('click', () => {
    $('modal-help').classList.remove('hidden');
});

$('btn-help-close').addEventListener('click', () => {
    $('modal-help').classList.add('hidden');
});

// ===== POPUP =====
function showPopup(title, desc) {
    $('popup-title').textContent = title;
    $('popup-desc').textContent = desc;
    $('modal-popup').classList.remove('hidden');
}

$('btn-popup-close').addEventListener('click', () => {
    $('modal-popup').classList.add('hidden');
});

// ===== HELPERS =====
function getCharacterEmoji(char) {
    const map = { 'tho': '🐰', 'chim': '🐧', 'cao': '🦊', 'qua': '🐦‍⬛' };
    return map[char] || '🤡';
}

// ===== INIT =====
// Không cần gì thêm, chỉ cần DOM sẵn sàng
console.log('🎮 Hành Tinh Xiếc - Offline mode đã sẵn sàng!');
