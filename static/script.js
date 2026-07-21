// =====================================================================
// scripts.js - Hành Tinh Xiếc (Client)
// =====================================================================

// ===== STATE =====
let socket = null;
let roomCode = '';
let playerId = null;
let state = null;
let myPlayer = null;
let isMyTurn = false;
let selectedCharacter = 'tho';
let isGameStarted = false;

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
// Mặc định chọn Thỏ
document.querySelector('.char-option[data-char="tho"]')?.classList.add('selected');

// ===== ROOM CODE =====
$('btn-random-code').addEventListener('click', () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars[Math.floor(Math.random() * chars.length)];
    }
    $('room-code').value = code;
});

// ===== SOCKET =====
function connectSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('🟢 Đã kết nối server');
    });
    
    socket.on('disconnect', () => {
        console.log('🔴 Mất kết nối');
        showPopup('Mất kết nối', 'Đã ngắt kết nối với server. Vui lòng tải lại trang.');
    });
    
    socket.on('error', (data) => {
        showPopup('Lỗi', data.message || 'Có lỗi xảy ra');
    });
    
    socket.on('game_created', (data) => {
        roomCode = data.room_code;
        playerId = data.player_id;
        state = data.state;
        myPlayer = state.players.find(p => p.id === playerId);
        enterWaitingRoom();
    });
    
    socket.on('game_joined', (data) => {
        playerId = data.player_id;
        state = data.state;
        myPlayer = state.players.find(p => p.id === playerId);
        enterWaitingRoom();
    });
    
    socket.on('player_joined', (data) => {
        state = data.state;
        renderWaitingPlayers();
        showPopup('🚀 Có người mới!', `${data.player.name} đã tham gia!`);
    });
    
    socket.on('game_started', (data) => {
        state = data.state;
        isGameStarted = true;
        enterGame();
        showPopup('🚀 Bắt đầu!', 'Cuộc phiêu lưu vũ trụ bắt đầu!');
    });
    
    socket.on('state_update', (data) => {
        state = data.state;
        if (isGameStarted) {
            renderGame();
        } else {
            renderWaitingPlayers();
        }
    });
    
    socket.on('dice_result', (data) => {
        animateDice(data.dice);
        if (data.finished) {
            showPopup('🏆 Về đích!', `Bạn đã về đích và chiến thắng!`);
        }
    });
}

// ===== LOBBY =====
$('btn-create-room').addEventListener('click', () => {
    const name = $('player-name').value.trim() || 'Phi hành gia';
    const code = $('room-code').value.trim().toUpperCase() || undefined;
    
    if (!socket) connectSocket();
    
    socket.emit('create_game', {
        player_name: name,
        character: selectedCharacter,
        room_code: code
    });
});

$('btn-join-room').addEventListener('click', () => {
    const name = $('player-name').value.trim() || 'Phi hành gia';
    const code = $('room-code').value.trim().toUpperCase();
    
    if (!code) {
        $('lobby-error').textContent = 'Vui lòng nhập mã phòng!';
        return;
    }
    
    if (!socket) connectSocket();
    
    socket.emit('join_game', {
        player_name: name,
        character: selectedCharacter,
        room_code: code
    });
});

// ===== WAITING ROOM =====
function enterWaitingRoom() {
    $('screen-lobby').classList.add('hidden');
    $('screen-waiting').classList.remove('hidden');
    $('waiting-room-code').textContent = roomCode;
    renderWaitingPlayers();
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
            <span class="status ${p.id === playerId ? 'ready' : ''}">
                ${p.id === playerId ? '⭐ Bạn' : '🟢 Sẵn sàng'}
            </span>
        `;
        list.appendChild(div);
    });
    
    // Hiển thị nút bắt đầu nếu là chủ phòng
    const isOwner = state.players.length > 0 && state.players[0].id === playerId;
    $('btn-start-game').style.display = isOwner && state.players.length >= 2 ? 'block' : 'none';
}

$('btn-start-game').addEventListener('click', () => {
    if (!socket) return;
    socket.emit('start_game', {
        room_code: roomCode,
        player_id: playerId
    });
});

$('btn-leave').addEventListener('click', () => {
    window.location.reload();
});

// ===== GAME =====
function enterGame() {
    $('screen-waiting').classList.add('hidden');
    $('screen-game').classList.remove('hidden');
    renderGame();
}

function renderGame() {
    if (!state) return;
    
    // Cập nhật topbar
    myPlayer = state.players.find(p => p.id === playerId);
    $('stat-gold').textContent = myPlayer ? myPlayer.gold : 0;
    $('stat-turn').textContent = state.turn_count;
    
    // Timer
    if (state.started_at) {
        const elapsed = Date.now() / 1000 - state.started_at;
        const remain = Math.max(0, state.time_limit_seconds - elapsed);
        const m = String(Math.floor(remain / 60)).padStart(2, '0');
        const s = String(Math.floor(remain % 60)).padStart(2, '0');
        $('stat-timer').textContent = `${m}:${s}`;
    }
    
    // Turn indicator
    const current = state.players[state.current_player_index];
    if (current) {
        const isMe = current.id === playerId;
        $('turn-indicator').textContent = isMe ? '🎯 Lượt của bạn!' : `⏳ Đợi ${current.name}...`;
        $('turn-indicator').style.color = isMe ? '#4ECDC4' : 'var(--text-secondary)';
        isMyTurn = isMe && !state.game_over;
    }
    
    // Board
    renderBoard();
    
    // Players
    renderPlayers();
    
    // Log
    renderLog();
    
    // Dice
    renderDiceState();
    
    // Modals
    renderShopModal();
    renderPendingModal();
    renderEndModal();
}

function renderBoard() {
    const board = $('board');
    board.innerHTML = '';
    
    // Layout snake: 10x10, bắt đầu từ 100 xuống 1
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
    
    const characterEmojis = {
        'tho': '🐰', 'chim': '🐧', 'cao': '🦊', 'qua': '🐦‍⬛'
    };
    
    grid.forEach(num => {
        const tile = tilesByIndex[num];
        if (!tile) return;
        
        const div = document.createElement('div');
        div.className = `tile tile-${tile.type}`;
        
        const number = document.createElement('span');
        number.className = 'tile-number';
        number.textContent = num;
        div.appendChild(number);
        
        // Tokens (người chơi)
        const tokWrap = document.createElement('div');
        tokWrap.className = 'tile-tokens';
        const playersHere = playersByPos[num] || [];
        playersHere.forEach(p => {
            const tok = document.createElement('span');
            tok.className = 'tok';
            tok.title = p.name;
            tok.textContent = characterEmojis[p.character] || '🤡';
            tokWrap.appendChild(tok);
        });
        div.appendChild(tokWrap);
        
        // Highlight ô của người chơi hiện tại
        if (myPlayer && myPlayer.position === num) {
            div.classList.add('has-player');
        }
        
        board.appendChild(div);
    });
    
    // Camera follow: di chuyển board để focus vào người chơi
    if (myPlayer) {
        const viewport = $('board-viewport');
        const tileSize = board.querySelector('.tile')?.offsetWidth || 40;
        const pos = myPlayer.position;
        const row = Math.floor((pos - 1) / 10);
        const col = (pos - 1) % 10;
        const isEvenRow = row % 2 === 0;
        const actualCol = isEvenRow ? col : 9 - col;
        
        const boardWidth = board.offsetWidth || 600;
        const boardHeight = board.offsetHeight || 400;
        const cols = 10;
        const rows = 10;
        const tileW = boardWidth / cols;
        const tileH = boardHeight / rows;
        
        const targetX = -(actualCol * tileW - viewport.offsetWidth / 2 + tileW / 2);
        const targetY = -((9 - row) * tileH - viewport.offsetHeight / 2 + tileH / 2);
        
        board.style.transform = `translate(${Math.min(0, Math.max(-boardWidth + viewport.offsetWidth, targetX))}px, ${Math.min(0, Math.max(-boardHeight + viewport.offsetHeight, targetY))}px)`;
    }
}

function renderPlayers() {
    const panel = $('players-panel');
    panel.innerHTML = '<h3>🎭 Phi hành gia</h3>';
    
    const colorMap = { 'Đỏ': '#FF6B6B', 'Xanh': '#4ECDC4', 'Vàng': '#FFD93D', 'Tím': '#6C5CE7' };
    const characterEmojis = { 'tho': '🐰', 'chim': '🐧', 'cao': '🦊', 'qua': '🐦‍⬛' };
    
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
                ${characterEmojis[p.character] || '🤡'} ${p.name} ${p.finished ? '🏆' : ''} ${p.offline ? '📴' : ''}
            </div>
            <div class="p-row"><span>📍 Ô</span><span>${p.position}</span></div>
            <div class="p-row"><span>🪙 Vàng</span><span>${p.gold}${p.debt > 0 ? ` (nợ ${p.debt})` : ''}</span></div>
            <div class="p-row"><span>📦 Vật phẩm</span><span>${itemText}</span></div>
        `;
        
        // Nút sử dụng vật phẩm
        if (p.id === playerId && isMyTurn && !state.game_over && p.items.length > 0) {
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

function renderDiceState() {
    const btn = $('btn-roll');
    const luckyPicker = $('lucky-picker');
    
    const isBlocked = state.game_over || state.pending_action || state.pending_shop_tile || !isMyTurn;
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

function animateDice(value) {
    const face = $('dice-face');
    const val = $('dice-value');
    face.classList.add('rolling');
    val.textContent = value;
    setTimeout(() => face.classList.remove('rolling'), 600);
}

// ===== DICE =====
$('btn-roll').addEventListener('click', () => {
    if (!socket || !roomCode || !playerId) return;
    socket.emit('roll_dice', {
        room_code: roomCode,
        player_id: playerId
    });
});

document.querySelectorAll('.lucky-numbers button').forEach(btn => {
    btn.addEventListener('click', () => {
        if (!socket || !roomCode || !playerId) return;
        socket.emit('roll_dice', {
            room_code: roomCode,
            player_id: playerId,
            chosen_number: Number(btn.dataset.n)
        });
    });
});

// ===== ITEMS =====
async function handleUseItem(itemType) {
    if (!socket || !roomCode || !playerId) return;
    
    const info = state.item_info[itemType];
    if (!info) return;
    
    // Dao Găm cần chọn mục tiêu
    if (itemType === 'DAO_GAM') {
        const targets = state.players.filter(p => p.id !== playerId && !p.finished && !p.offline);
        if (targets.length === 0) {
            showPopup('Không có mục tiêu', 'Không có người chơi nào để làm mục tiêu!');
            return;
        }
        // Hiển thị modal chọn mục tiêu
        showTargetModal(targets, (targetId) => {
            socket.emit('use_item', {
                room_code: roomCode,
                player_id: playerId,
                item_type: itemType,
                target_id: targetId
            });
        });
        return;
    }
    
    // Kính Áp Tròng cần chọn +1/-1
    if (itemType === 'KINH_AP_TRONG') {
        showDeltaModal((delta) => {
            socket.emit('use_item', {
                room_code: roomCode,
                player_id: playerId,
                item_type: itemType,
                delta: delta
            });
        });
        return;
    }
    
    // Các item khác
    socket.emit('use_item', {
        room_code: roomCode,
        player_id: playerId,
        item_type: itemType
    });
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
            socket.emit('buy_item', {
                room_code: roomCode,
                player_id: playerId,
                item_type: key
            });
        });
        div.appendChild(btn);
        wrap.appendChild(div);
    });
}

$('btn-skip-shop').addEventListener('click', () => {
    if (!socket || !roomCode || !playerId) return;
    socket.emit('skip_shop', {
        room_code: roomCode,
        player_id: playerId
    });
});

// ===== PENDING ACTION =====
function renderPendingModal() {
    const modal = $('modal-pending');
    if (!state.pending_action) {
        modal.classList.add('hidden');
        return;
    }
    modal.classList.remove('hidden');
    
    const pa = state.pending_action;
    $('pending-title').textContent = `🃏 ${pa.card_name || 'Sự kiện'}`;
    $('pending-desc').textContent = pa.card_desc || 'Chọn một lựa chọn:';
    
    const optWrap = $('pending-options');
    optWrap.innerHTML = '';
    
    if (pa.await === 'confirm') {
        const btn = document.createElement('button');
        btn.textContent = '✅ Xác nhận';
        btn.addEventListener('click', () => {
            socket.emit('resolve_pending', {
                room_code: roomCode,
                player_id: playerId,
                choice: { confirm: true }
            });
        });
        optWrap.appendChild(btn);
    } else {
        // Các trường hợp khác có thể mở rộng
        const btn = document.createElement('button');
        btn.textContent = 'OK';
        btn.addEventListener('click', () => {
            socket.emit('resolve_pending', {
                room_code: roomCode,
                player_id: playerId,
                choice: {}
            });
        });
        optWrap.appendChild(btn);
    }
}

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

// ===== TARGET MODAL =====
function showTargetModal(targets, callback) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'modal-item-target';
    modal.innerHTML = `
        <div class="modal-card">
            <h2 id="item-target-title">🎯 Chọn mục tiêu</h2>
            <div id="item-target-options" style="display:flex;flex-direction:column;gap:0.5rem;"></div>
            <button class="btn-ghost" id="btn-cancel-target">Hủy</button>
        </div>
    `;
    document.body.appendChild(modal);
    const opt = document.getElementById('item-target-options');
    targets.forEach(p => {
        const btn = document.createElement('button');
        btn.textContent = `${p.name} (Ô ${p.position})`;
        btn.addEventListener('click', () => {
            modal.remove();
            callback(p.id);
        });
        opt.appendChild(btn);
    });
    document.getElementById('btn-cancel-target').addEventListener('click', () => {
        modal.remove();
    });
    modal.classList.remove('hidden');
}

// ===== DELTA MODAL =====
function showDeltaModal(callback) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'modal-item-target';
    modal.innerHTML = `
        <div class="modal-card">
            <h2 id="item-target-title">👁️ Chọn điều chỉnh</h2>
            <div id="item-target-options" style="display:flex;gap:0.5rem;justify-content:center;margin:1rem 0;"></div>
            <button class="btn-ghost" id="btn-cancel-target">Hủy</button>
        </div>
    `;
    document.body.appendChild(modal);
    const opt = document.getElementById('item-target-options');
    [1, -1].forEach(d => {
        const btn = document.createElement('button');
        btn.textContent = d > 0 ? '+1' : '-1';
        btn.addEventListener('click', () => {
            modal.remove();
            callback(d);
        });
        opt.appendChild(btn);
    });
    document.getElementById('btn-cancel-target').addEventListener('click', () => {
        modal.remove();
    });
    modal.classList.remove('hidden');
}

// ===== HELPERS =====
function getCharacterEmoji(char) {
    const map = { 'tho': '🐰', 'chim': '🐧', 'cao': '🦊', 'qua': '🐦‍⬛' };
    return map[char] || '🤡';
}

// ===== TIMER LOOP =====
setInterval(() => {
    if (state && isGameStarted) {
        renderGame();
    }
}, 1000);

// ===== INIT =====
connectSocket();
