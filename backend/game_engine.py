# -*- coding: utf-8 -*-
import random
from .constants import TileType, BOARD_SIZE, START_TILE, FINISH_TILE
from .models import Player, Tile
from .board_builder import build_board

class GameEngine:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = {}  # player_id -> Player object
        self.board, self.reserve_pool = build_board()
        self.turn_order = []  # danh sách player_id theo thứ tự chơi
        self.current_turn_index = 0
        self.dice_value = None
        self.last_action = None
        self.game_over = False
        self.notifications = []  # lưu thông báo để gửi cho client

    def add_player(self, player_id, name, character):
        if player_id in self.players:
            return False
        # Kiểm tra nhân vật đã được chọn chưa
        for p in self.players.values():
            if p.character == character:
                return False
        player = Player(player_id, name, character)
        self.players[player_id] = player
        self.turn_order.append(player_id)
        # Nếu chưa có ai, set là lượt của người này
        if len(self.turn_order) == 1:
            self.current_turn_index = 0
        return True

    def get_current_player(self):
        if not self.turn_order:
            return None
        return self.players[self.turn_order[self.current_turn_index]]

    def next_turn(self):
        # Chuyển sang người tiếp theo, nếu đã hết thì quay lại
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        # Bỏ qua những người đã về đích
        while self.players[self.turn_order[self.current_turn_index]].is_finished:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            if all(p.is_finished for p in self.players.values()):
                self.game_over = True
                break

    def roll_dice(self, player_id):
        if self.game_over:
            self.add_notification("Game đã kết thúc!", "error")
            return None
        player = self.players.get(player_id)
        if not player:
            self.add_notification("Không tìm thấy người chơi!", "error")
            return None
        if player.is_finished:
            self.add_notification("Bạn đã về đích!", "info")
            return None
        current = self.get_current_player()
        if current.id != player_id:
            self.add_notification("Chưa đến lượt bạn!", "error")
            return None

        # Tung xúc xắc (1-6)
        dice = random.randint(1, 6)
        self.dice_value = dice
        self.add_notification(f"{player.name} tung được {dice}!", "dice")
        # Di chuyển
        new_pos = player.position + dice
        if new_pos >= FINISH_TILE:
            new_pos = FINISH_TILE
            player.is_finished = True
            self.add_notification(f"{player.name} đã về đích! 🎉", "finish")
            self.game_over = all(p.is_finished for p in self.players.values())
        else:
            # Xử lý sự kiện ô
            tile = self.board[new_pos]
            self.add_notification(f"{player.name} đáp vào ô {tile.type.value}", "tile")
            # Xử lý theo loại ô
            self.handle_tile_effect(player, tile)
            player.position = new_pos
            # Cập nhật vị trí (nếu có nhảy cóc hoặc lùi)
            # Xử lý ô XANH (nhảy cóc) đã được xử lý trong handle_tile_effect

        # Chuyển lượt
        self.next_turn()
        return {
            'dice': dice,
            'new_position': player.position,
            'is_finished': player.is_finished,
            'game_over': self.game_over,
        }

    def handle_tile_effect(self, player, tile):
        # Xử lý hiệu ứng khi đáp vào ô
        if tile.type == TileType.VANG:
            # Nhận vàng
            gold = random.randint(1, 5)
            player.gold += gold
            self.add_notification(f"{player.name} nhận được {gold} vàng!", "gold")
        elif tile.type == TileType.DO:
            # Mất vàng hoặc lùi
            if player.gold >= 3:
                player.gold -= 3
                self.add_notification(f"{player.name} mất 3 vàng!", "loss")
            else:
                # Lùi 2 ô
                old_pos = player.position
                player.position = max(1, player.position - 2)
                self.add_notification(f"{player.name} bị lùi 2 ô!", "loss")
        elif tile.type == TileType.XANH:
            # Nhảy cóc (đã có jump_target)
            if tile.jump_target:
                old_pos = player.position
                player.position = tile.jump_target
                self.add_notification(f"{player.name} nhảy cóc đến ô {player.position}!", "jump")
        elif tile.type == TileType.TIM:
            # Rút một thẻ từ reserve_pool (bẫy)
            if self.reserve_pool:
                trap = self.reserve_pool.pop()
                # Áp dụng hiệu ứng của thẻ bẫy (đơn giản là mất vàng hoặc lùi)
                if trap.type == TileType.DEN:
                    player.gold = max(0, player.gold - 2)
                    self.add_notification(f"{player.name} rút thẻ ĐEN: mất 2 vàng!", "trap")
                elif trap.type == TileType.DO:
                    player.position = max(1, player.position - 3)
                    self.add_notification(f"{player.name} rút thẻ ĐỎ: lùi 3 ô!", "trap")
                else:
                    player.gold += 1
                    self.add_notification(f"{player.name} rút thẻ {trap.type.value}: nhận 1 vàng!", "trap")
            else:
                self.add_notification(f"{player.name} rút thẻ nhưng túi hết!", "info")
        elif tile.type == TileType.CAM:
            # Cửa hàng
            self.shop(player)
        elif tile.type == TileType.HONG:
            # Tặng vàng
            player.gold += 2
            self.add_notification(f"{player.name} nhận 2 vàng từ ô HỒNG!", "gold")
        elif tile.type == TileType.DEN:
            # Mất lượt
            player.turn_skipped = True
            self.add_notification(f"{player.name} bị mất lượt kế tiếp!", "loss")
        elif tile.type == TileType.TRANG:
            # Cửa hàng (tương tự CAM)
            self.shop(player)
        # Các ô khác không có hiệu ứng

    def shop(self, player):
        # Cửa hàng: hiển thị danh sách món, cho phép mua
        # Ở đây ta sẽ gửi thông báo và để client xử lý
        # Vì đây là logic server, ta chỉ đưa ra các lựa chọn và client gọi API mua
        items = [
            {'name': 'Bùa hộ mệnh', 'price': 5, 'effect': 'miễn nhiễm 1 lần mất lượt'},
            {'name': 'Xúc xắc may mắn', 'price': 3, 'effect': 'được tung thêm 1 lần'},
            {'name': 'Vàng', 'price': 2, 'effect': 'nhận 2 vàng'},
        ]
        # Lưu thông tin shop vào player để client hiển thị
        player.shop_items = items
        self.add_notification(f"{player.name} đã vào cửa hàng!", "shop")

    def buy_item(self, player_id, item_index):
        player = self.players.get(player_id)
        if not player:
            return False
        if not hasattr(player, 'shop_items') or item_index >= len(player.shop_items):
            return False
        item = player.shop_items[item_index]
        if player.gold < item['price']:
            self.add_notification(f"{player.name} không đủ vàng!", "error")
            return False
        player.gold -= item['price']
        player.items.append(item['name'])
        self.add_notification(f"{player.name} mua {item['name']}!", "shop")
        return True

    def add_notification(self, message, category='info'):
        self.notifications.append({
            'message': message,
            'category': category,
            'timestamp': len(self.notifications),
        })
        # Giới hạn số thông báo để tránh tràn
        if len(self.notifications) > 50:
            self.notifications.pop(0)

    def get_state(self):
        # Trả về toàn bộ trạng thái game dưới dạng dict
        players_state = {pid: p.to_dict() for pid, p in self.players.items()}
        board_state = [None] * (BOARD_SIZE + 1)
        for i in range(1, BOARD_SIZE + 1):
            if self.board[i]:
                board_state[i] = self.board[i].to_dict()
        return {
            'room_id': self.room_id,
            'players': players_state,
            'board': board_state,
            'turn_order': self.turn_order,
            'current_turn_index': self.current_turn_index,
            'current_player_id': self.turn_order[self.current_turn_index] if self.turn_order else None,
            'game_over': self.game_over,
            'notifications': self.notifications[-10:],  # gửi 10 thông báo gần nhất
        }
