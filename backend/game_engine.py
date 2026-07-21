# backend/game_engine.py
# -*- coding: utf-8 -*-
"""
Game Engine - Xử lý toàn bộ logic game
"""

import random
import time
from typing import List, Dict, Optional, Any
from .constants import *
from .models import Player, Tile, GameState
from .board_builder import build_board

class GameEngine:
    def __init__(self):
        self.players: List[Player] = []
        self.board: List[Tile] = []
        self.reserve_pool: List[Tile] = []
        self.current_player_index: int = 0
        self.turn_count: int = 0
        self.started: bool = False
        self.game_over: bool = False
        self.winner_id: Optional[int] = None
        self.started_at: float = 0
        self.pending_action: Optional[Dict] = None
        self.pending_shop_tile: bool = False
        self.item_stock: Dict[str, int] = {}
        self.log: List[str] = []
        self.offline_players: List[int] = []
        
        # Khởi tạo bản đồ và kho vật phẩm
        self.board, self.reserve_pool = build_board()
        for item_type in ITEM_INFO:
            self.item_stock[item_type] = ITEM_INFO[item_type]['stock']
    
    def add_player(self, name: str, character: str) -> int:
        """Thêm người chơi mới"""
        if len(self.players) >= 4:
            raise Exception("Đã đủ 4 người chơi!")
        
        # Chọn màu theo thứ tự
        colors = ['Đỏ', 'Xanh', 'Vàng', 'Tím']
        color = colors[len(self.players)]
        
        player = Player(
            id=len(self.players) + 1,
            name=name,
            color=color,
            character=character,
            position=1,
            gold=START_GOLD,
            debt=0,
            items=[],
            statuses=[],
            finished=False,
            offline=False
        )
        self.players.append(player)
        self.log.append(f"🪐 {name} ({character}) đã tham gia phiêu lưu vũ trụ!")
        return player.id
    
    def is_full(self) -> bool:
        return len(self.players) >= 4
    
    def get_player_info(self, player_id: int) -> Optional[Dict]:
        for p in self.players:
            if p.id == player_id:
                return p.to_dict()
        return None
    
    def set_player_offline(self, player_id: int):
        for p in self.players:
            if p.id == player_id:
                p.offline = True
                if p.id not in self.offline_players:
                    self.offline_players.append(p.id)
                break
    
    def get_offline_players(self) -> List[int]:
        return self.offline_players
    
    def start_game(self):
        """Bắt đầu game"""
        if self.started:
            return
        self.started = True
        self.started_at = time.time()
        self.current_player_index = random.randint(0, len(self.players) - 1)
        self.log.append("🚀 Cuộc phiêu lưu vũ trụ bắt đầu!")
        # Xáo trộn thứ tự người chơi
        random.shuffle(self.players)
        for i, p in enumerate(self.players):
            p.id = i + 1
    
    def get_state(self, player_id: Optional[int] = None) -> Dict:
        """Lấy trạng thái game"""
        current_player = self.players[self.current_player_index] if self.players else None
        
        state = {
            'players': [p.to_dict() for p in self.players],
            'board': [t.to_dict() for t in self.board[1:]],
            'current_player_index': self.current_player_index,
            'turn_count': self.turn_count,
            'game_over': self.game_over,
            'winner_id': self.winner_id,
            'started_at': self.started_at,
            'time_limit_seconds': GAME_TIME_LIMIT_SECONDS,
            'common_fund': 0,
            'pending_action': self.pending_action,
            'pending_shop_tile': self.pending_shop_tile,
            'item_stock': self.item_stock,
            'item_info': {k: {'name': v['name'], 'price': v['price'], 
                              'desc': v['desc'], 'emoji': v['emoji']} 
                          for k, v in ITEM_INFO.items()},
            'log': self.log[-50:],
            'offline_players': self.offline_players
        }
        
        # Nếu có player_id, thêm thông tin riêng
        if player_id:
            player = next((p for p in self.players if p.id == player_id), None)
            if player:
                state['my_player'] = player.to_dict()
                state['my_turn'] = (current_player and current_player.id == player_id)
        
        return state
    
    def get_current_player(self) -> Optional[Player]:
        if 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None
    
    def roll_dice(self, player_id: int, chosen_number: Optional[int] = None) -> Dict:
        """Xử lý tung xúc xắc"""
        if not self.started or self.game_over:
            raise Exception("Game chưa bắt đầu hoặc đã kết thúc!")
        
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Không tìm thấy người chơi!")
        
        current = self.get_current_player()
        if not current or current.id != player_id:
            raise Exception("Đến lượt người chơi khác!")
        
        if player.offline:
            raise Exception("Người chơi đã offline!")
        
        # Kiểm tra pending action
        if self.pending_action:
            raise Exception("Cần giải quyết hành động đang chờ!")
        
        # Kiểm tra cửa hàng
        if self.pending_shop_tile:
            raise Exception("Cần mua hàng hoặc bỏ qua!")
        
        # Tính số điểm xúc xắc
        dice_value = random.randint(1, 6)
        
        # Kiểm tra Bùa May Mắn
        lucky_status = next((s for s in player.statuses if s['kind'] == 'lucky_charm'), None)
        if lucky_status and chosen_number is not None:
            if 1 <= chosen_number <= 6:
                dice_value = chosen_number
                player.statuses.remove(lucky_status)
                self.log.append(f"🍀 {player.name} dùng Bùa May Mắn chọn số {dice_value}")
        
        # Kiểm tra Xúc Xắc X2
        x2_status = next((s for s in player.statuses if s['kind'] == 'x2_dice'), None)
        if x2_status:
            dice_value *= 2
            player.statuses.remove(x2_status)
            self.log.append(f"🎲 {player.name} tung xúc xắc x2: {dice_value}")
        
        # Kiểm tra Kính Áp Tròng
        kính_status = next((s for s in player.statuses if s['kind'] == 'kinh_ap_trong'), None)
        if kính_status:
            # Đã được xử lý ở use_item
            pass
        
        # Di chuyển
        new_position = player.position + dice_value
        
        # Nếu vượt quá 100 => thắng
        if new_position >= FINISH_TILE:
            player.position = FINISH_TILE
            player.finished = True
            self.game_over = True
            self.winner_id = player.id
            self.log.append(f"🏆 {player.name} đã về đích và chiến thắng!")
            return {'dice': dice_value, 'position': player.position, 'finished': True}
        
        player.position = new_position
        
        # Xử lý ô đáp
        self._handle_tile_landing(player)
        
        # Chuyển lượt
        self._next_turn()
        
        return {'dice': dice_value, 'position': player.position, 'finished': False}
    
    def _handle_tile_landing(self, player: Player):
        """Xử lý khi người chơi đáp vào ô"""
        tile = self.board[player.position]
        
        # Thông báo ô
        self.log.append(f"📍 {player.name} đáp vào ô {player.position} ({tile.type})")
        
        if tile.type == TileType.TRONG:
            # Ô Trống: cướp 1 vàng nếu có người khác
            others = [p for p in self.players if p.id != player.id and p.position == player.position]
            if others and player.position != START_TILE:
                target = random.choice(others)
                if target.gold > 0:
                    target.gold -= 1
                    player.gold += 1
                    self.log.append(f"💰 {player.name} cướp 1 vàng từ {target.name}")
        
        elif tile.type == TileType.VANG:
            # Ô Vàng: +5 vàng
            player.gold += 5
            self.log.append(f"💰 {player.name} nhận 5 vàng")
        
        elif tile.type == TileType.DO:
            # Ô Đỏ: -3 vàng hoặc lùi 3 ô
            if player.gold >= 3:
                player.gold -= 3
                self.log.append(f"💸 {player.name} mất 3 vàng")
            else:
                new_pos = max(1, player.position - 3)
                if new_pos != player.position:
                    self.log.append(f"⬅️ {player.name} không đủ vàng, lùi 3 ô đến {new_pos}")
                    player.position = new_pos
                    # Xử lý ô mới (tránh đệ quy vô hạn)
                    if player.position != tile.index:
                        self._handle_tile_landing(player)
        
        elif tile.type == TileType.XANH:
            # Ô Xanh: nhảy đến ô đích
            if tile.jump_target:
                old_pos = player.position
                player.position = tile.jump_target
                self.log.append(f"🚀 {player.name} nhảy từ {old_pos} đến {player.position}")
                # Xử lý ô mới
                if player.position != old_pos:
                    self._handle_tile_landing(player)
        
        elif tile.type == TileType.TIM:
            # Ô Tím: rút bài Sự kiện
            self._draw_event_card(player)
        
        elif tile.type == TileType.CAM:
            # Ô Cam: rút bài Bẫy
            self._draw_trap_card(player)
        
        elif tile.type == TileType.HONG:
            # Ô Hồng: cổng, trả phí 2 vàng
            if player.gold >= 2:
                player.gold -= 2
                self.log.append(f"🚪 {player.name} trả 2 vàng qua cổng")
            else:
                player.debt += 2
                self.log.append(f"🚪 {player.name} nợ 2 vàng qua cổng")
        
        elif tile.type == TileType.DICH:
            # Ô Đích
            player.finished = True
            self.game_over = True
            self.winner_id = player.id
            self.log.append(f"🏆 {player.name} đã về đích và chiến thắng!")
    
    def _draw_event_card(self, player: Player):
        """Rút bài Sự kiện"""
        events = [
            {'name': '💫 Sao Băng', 'desc': 'Nhận 5 vàng', 'action': lambda p: setattr(p, 'gold', p.gold + 5)},
            {'name': '🌑 Hố Đen', 'desc': 'Mất 3 vàng', 'action': lambda p: setattr(p, 'gold', max(0, p.gold - 3))},
            {'name': '🔄 Dịch Chuyển', 'desc': 'Đổi chỗ với người chơi gần nhất', 'action': self._action_swap_nearest},
            {'name': '🎯 Bùa May Mắn', 'desc': 'Lần tung tới được chọn số', 'action': self._action_lucky_charm},
            {'name': '🛡️ Lá Chắn', 'desc': 'Nhận 1 lá chắn (chặn hiệu ứng xấu)', 'action': self._action_shield},
        ]
        
        event = random.choice(events)
        self.log.append(f"🃏 {player.name} rút Sự kiện: {event['name']}")
        
        # Hiển thị popup cho người chơi
        self.pending_action = {
            'kind': 'event',
            'card_name': event['name'],
            'card_desc': event['desc'],
            'await': 'confirm',
            'player_id': player.id,
            'action': event['action']
        }
    
    def _draw_trap_card(self, player: Player):
        """Rút bài Bẫy"""
        traps = [
            {'name': '🕸️ Lưới Vũ Trụ', 'desc': 'Mất lượt tới', 'action': self._action_skip_turn},
            {'name': '💥 Thiên Thạch', 'desc': 'Lùi 5 ô', 'action': self._action_move_back},
            {'name': '🌀 Lỗ Xoáy', 'desc': 'Quay ngược thứ tự bàn cờ', 'action': self._action_reverse_board},
            {'name': '🃏 Bài Tarot', 'desc': 'Rút 1 lá bài ngẫu nhiên', 'action': self._action_tarot},
        ]
        
        trap = random.choice(traps)
        self.log.append(f"🃏 {player.name} rút Bẫy: {trap['name']}")
        
        self.pending_action = {
            'kind': 'trap',
            'card_name': trap['name'],
            'card_desc': trap['desc'],
            'await': 'confirm',
            'player_id': player.id,
            'action': trap['action']
        }
    
    def _action_swap_nearest(self, player: Player):
        """Đổi chỗ với người chơi gần nhất"""
        others = [p for p in self.players if p.id != player.id and not p.finished]
        if others:
            nearest = min(others, key=lambda p: abs(p.position - player.position))
            player.position, nearest.position = nearest.position, player.position
            self.log.append(f"🔄 {player.name} đổi chỗ với {nearest.name}")
    
    def _action_lucky_charm(self, player: Player):
        """Thêm Bùa May Mắn"""
        player.statuses.append({'kind': 'lucky_charm', 'value': True})
        self.log.append(f"🍀 {player.name} nhận Bùa May Mắn")
    
    def _action_shield(self, player: Player):
        """Thêm lá chắn"""
        player.statuses.append({'kind': 'shield', 'value': True})
        self.log.append(f"🛡️ {player.name} nhận lá chắn")
    
    def _action_skip_turn(self, player: Player):
        """Mất lượt"""
        player.statuses.append({'kind': 'skip_turn', 'value': True})
        self.log.append(f"⏭️ {player.name} sẽ bị mất lượt tới")
    
    def _action_move_back(self, player: Player):
        """Lùi 5 ô"""
        player.position = max(1, player.position - 5)
        self.log.append(f"⬅️ {player.name} lùi 5 ô đến {player.position}")
    
    def _action_reverse_board(self, player: Player):
        """Đảo ngược thứ tự bàn cờ (mô phỏng)"""
        self.log.append(f"🌀 {player.name} đảo ngược thứ tự bàn cờ!")
        # Đảo ngược vị trí của tất cả người chơi
        for p in self.players:
            if not p.finished:
                p.position = BOARD_SIZE + 1 - p.position
    
    def _action_tarot(self, player: Player):
        """Rút bài Tarot"""
        tarot_cards = [
            '🌞 Mặt Trời - +3 vàng',
            '🌙 Mặt Trăng - -2 vàng',
            '⭐ Sao - +1 vàng',
            '💀 Tử Thần - Mất 1 vật phẩm',
            '🌈 Cầu Vồng - Nhận 1 vật phẩm ngẫu nhiên',
        ]
        card = random.choice(tarot_cards)
        self.log.append(f"🃏 {player.name} rút Tarot: {card}")
        # Xử lý hiệu ứng đơn giản
        if 'Mặt Trời' in card:
            player.gold += 3
        elif 'Mặt Trăng' in card:
            player.gold = max(0, player.gold - 2)
        elif 'Sao' in card:
            player.gold += 1
        elif 'Tử Thần' in card:
            if player.items:
                player.items.pop()
        elif 'Cầu Vồng' in card:
            item_type = random.choice(list(ITEM_INFO.keys()))
            if len(player.items) < MAX_ITEMS_CARRIED:
                player.items.append(item_type)
    
    def resolve_pending(self, player_id: int, choice: Dict):
        """Giải quyết hành động đang chờ"""
        if not self.pending_action:
            raise Exception("Không có hành động đang chờ!")
        
        if self.pending_action['player_id'] != player_id:
            raise Exception("Không phải lượt của bạn!")
        
        action = self.pending_action['action']
        player = next((p for p in self.players if p.id == player_id), None)
        if player:
            action(player)
        
        self.pending_action = None
        self._next_turn()
    
    def _next_turn(self):
        """Chuyển sang lượt tiếp theo"""
        if self.game_over:
            return
        
        # Tìm người chơi tiếp theo
        for i in range(1, len(self.players) + 1):
            idx = (self.current_player_index + i) % len(self.players)
            player = self.players[idx]
            if not player.finished and not player.offline:
                # Kiểm tra skip_turn
                skip = next((s for s in player.statuses if s['kind'] == 'skip_turn'), None)
                if skip:
                    player.statuses.remove(skip)
                    self.log.append(f"⏭️ {player.name} bị mất lượt")
                    continue
                self.current_player_index = idx
                self.turn_count += 1
                return
        
        # Nếu không còn người chơi nào, kết thúc game
        self.game_over = True
        # Tìm người có vàng cao nhất
        if not self.winner_id:
            winner = max(self.players, key=lambda p: p.gold)
            self.winner_id = winner.id
            self.log.append(f"🏆 {winner.name} chiến thắng với {winner.gold} vàng!")
    
    def buy_item(self, player_id: int, item_type: str):
        """Mua vật phẩm"""
        if not self.pending_shop_tile:
            raise Exception("Không ở cửa hàng!")
        
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Không tìm thấy người chơi!")
        
        if item_type not in ITEM_INFO:
            raise Exception("Vật phẩm không tồn tại!")
        
        info = ITEM_INFO[item_type]
        if self.item_stock[item_type] <= 0:
            raise Exception("Vật phẩm đã hết hàng!")
        
        if player.gold < info['price']:
            raise Exception("Không đủ vàng!")
        
        if len(player.items) >= MAX_ITEMS_CARRIED:
            raise Exception("Đã mang đủ 2 vật phẩm!")
        
        player.gold -= info['price']
        player.items.append(item_type)
        self.item_stock[item_type] -= 1
        self.log.append(f"🛒 {player.name} mua {info['emoji']} {info['name']}")
        
        # Tự động chuyển lượt sau khi mua
        self.pending_shop_tile = False
        self._next_turn()
    
    def skip_shop(self, player_id: int):
        """Bỏ qua cửa hàng"""
        if not self.pending_shop_tile:
            raise Exception("Không ở cửa hàng!")
        
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Không tìm thấy người chơi!")
        
        self.log.append(f"🚶 {player.name} bỏ qua cửa hàng")
        self.pending_shop_tile = False
        self._next_turn()
    
    def use_item(self, player_id: int, item_type: str, target_id: Optional[int] = None, delta: Optional[int] = None):
        """Sử dụng vật phẩm"""
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            raise Exception("Không tìm thấy người chơi!")
        
        if item_type not in player.items:
            raise Exception("Không có vật phẩm này!")
        
        # Xử lý từng loại
        if item_type == ItemType.XUC_XAC_X2:
            player.statuses.append({'kind': 'x2_dice', 'value': True})
            self.log.append(f"🎲 {player.name} dùng Xúc Xắc X2")
        
        elif item_type == ItemType.LA_CHAN:
            player.statuses.append({'kind': 'shield', 'value': True})
            self.log.append(f"🛡️ {player.name} dùng Lá Chắn")
        
        elif item_type == ItemType.DAO_GAM:
            if target_id is None:
                raise Exception("Cần chọn mục tiêu!")
            target = next((p for p in self.players if p.id == target_id), None)
            if not target:
                raise Exception("Không tìm thấy mục tiêu!")
            if abs(player.position - target.position) > 3:
                raise Exception("Mục tiêu quá xa (cách > 3 ô)!")
            target.position = max(1, target.position - 4)
            self.log.append(f"🔪 {player.name} đá {target.name} lùi 4 ô đến {target.position}")
        
        elif item_type == ItemType.BUA_HO_MENH:
            # Cho phép tung thêm 1 lần
            player.statuses.append({'kind': 'extra_turn', 'value': True})
            self.log.append(f"🪆 {player.name} dùng Bùa Hộ Mệnh, được thêm lượt")
        
        elif item_type == ItemType.KINH_AP_TRONG:
            if delta is None:
                raise Exception("Cần chọn +1 hoặc -1!")
            player.statuses.append({'kind': 'kinh_ap_trong', 'value': delta})
            self.log.append(f"👁️ {player.name} dùng Kính Áp Tròng, điều chỉnh {delta}")
        
        # Xóa vật phẩm khỏi túi
        player.items.remove(item_type)
        # Trả lại kho
        self.item_stock[item_type] += 1
    
    def check_turn_timeout(self):
        """Kiểm tra timeout lượt"""
        if not self.started or self.game_over:
            return
        
        elapsed = time.time() - self.started_at
        if elapsed > GAME_TIME_LIMIT_SECONDS:
            self.game_over = True
            if not self.winner_id:
                winner = max(self.players, key=lambda p: p.gold)
                self.winner_id = winner.id
                self.log.append(f"⏰ Hết giờ! {winner.name} chiến thắng với {winner.gold} vàng!")
    
    def is_game_over(self) -> bool:
        return self.game_over
