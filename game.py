import random
import time
from typing import List, Dict, Optional
from constants import TileType, ITEM_INFO
from models import Player, Tile, GameState

def create_board():
    board = []
    for i in range(1, 101):
        if i == 100:
            tile_type = TileType.DICH
        elif i in [20, 50, 80]:
            tile_type = TileType.VANG
        elif i in [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]:
            tile_type = TileType.DO
        elif i in [10, 30, 40, 60, 70, 90]:
            tile_type = TileType.XANH
        elif i in [7, 17, 27, 37, 47, 57, 67, 77, 87, 97]:
            tile_type = TileType.TIM
        elif i in [12, 22, 32, 42, 52, 62, 72, 82, 92]:
            tile_type = TileType.CAM
        elif i in [8, 18, 28, 38, 48, 58, 68, 78, 88, 98]:
            tile_type = TileType.HONG
        else:
            tile_type = TileType.TRONG
        board.append(Tile(i, tile_type))
    return board

class Game:
    def __init__(self, room_code: str, host_player: Player):
        self.room_code = room_code
        self.players: List[Player] = [host_player]
        self.board = create_board()
        self.current_player_index = 0
        self.turn_count = 0
        self.started = False
        self.game_over = False
        self.winner_id: Optional[str] = None
        self.started_at = 0.0
        self.time_limit_seconds = 2700
        self.pending_action: Optional[Dict] = None
        self.pending_shop_tile = False
        self.item_stock = {item: ITEM_INFO[item]["max_stock"] for item in ITEM_INFO}
        self.log: List[str] = []
        self.dice_result = None

    def add_player(self, player: Player):
        self.players.append(player)

    def start_game(self):
        self.started = True
        self.started_at = time.time()
        self.log.append("🚀 Trò chơi bắt đầu!")

    def get_state(self) -> GameState:
        return GameState(
            players=self.players,
            board=self.board,
            current_player_index=self.current_player_index,
            turn_count=self.turn_count,
            started=self.started,
            game_over=self.game_over,
            winner_id=self.winner_id,
            started_at=self.started_at,
            pending_action=self.pending_action,
            pending_shop_tile=self.pending_shop_tile,
            item_stock=self.item_stock,
            log=self.log
        )

    def next_turn(self):
        if self.game_over:
            return
        for i in range(1, len(self.players) + 1):
            idx = (self.current_player_index + i) % len(self.players)
            if not self.players[idx].finished and not self.players[idx].offline:
                self.current_player_index = idx
                self.turn_count += 1
                return
        self.game_over = True
        winners = [p for p in self.players if p.finished]
        if winners:
            self.winner_id = winners[0].id
        else:
            best = max(self.players, key=lambda p: p.gold)
            self.winner_id = best.id
        self.log.append(f"🏆 Trò chơi kết thúc! Người thắng: {self.players[self.winner_id].name}")

    def roll_dice(self, player_id: str, chosen_number: int = None) -> int:
        current = self.players[self.current_player_index]
        if current.id != player_id:
            return 0
        if chosen_number is not None:
            result = chosen_number
        else:
            result = random.randint(1, 6)
        self.dice_result = result
        return result

    def move_player(self, player_id: str, steps: int):
        player = next(p for p in self.players if p.id == player_id)
        new_pos = player.position + steps
        if new_pos >= 100:
            player.position = 100
            player.finished = True
            self.log.append(f"🏁 {player.name} đã về đích!")
            self.game_over = True
            self.winner_id = player.id
            self.log.append(f"🏆 {player.name} chiến thắng!")
            return
        player.position = new_pos
        self.apply_tile_effect(player)

    def apply_tile_effect(self, player: Player):
        tile = self.board[player.position - 1]
        if tile.type == TileType.VANG:
            player.gold += 5
            self.log.append(f"💰 {player.name} nhận 5 vàng từ ô Vàng")
        elif tile.type == TileType.DO:
            if player.gold >= 3:
                player.gold -= 3
                self.log.append(f"💔 {player.name} mất 3 vàng")
            else:
                player.position = max(1, player.position - 3)
                self.log.append(f"⬅️ {player.name} lùi 3 ô")
        elif tile.type == TileType.XANH:
            target = random.randint(1, 100)
            player.position = target
            self.log.append(f"🌀 {player.name} nhảy đến ô {target}")
        elif tile.type == TileType.TIM:
            player.gold += 5
            self.log.append(f"🌟 {player.name} nhận 5 vàng từ Sự kiện")
        elif tile.type == TileType.CAM:
            player.gold = max(0, player.gold - 3)
            self.log.append(f"💥 {player.name} mất 3 vàng từ Bẫy")
        elif tile.type == TileType.HONG:
            player.gold = max(0, player.gold - 2)
            self.log.append(f"🚪 {player.name} trả 2 vàng")
        elif tile.type == TileType.TRONG:
            for other in self.players:
                if other.id != player.id and other.position == player.position and not other.finished:
                    if other.gold > 0:
                        other.gold -= 1
                        player.gold += 1
                        self.log.append(f"🔪 {player.name} cướp 1 vàng từ {other.name}")
                        break

    def use_item(self, player_id: str, item_type: str, target_id: str = None, delta: int = None):
        player = next(p for p in self.players if p.id == player_id)
        if item_type not in player.items:
            return False
        if item_type == "XUC_XAC_X2":
            self.pending_action = {"kind": "dice_double", "player_id": player_id}
            return True
        elif item_type == "LA_CHAN":
            player.statuses.append({"kind": "shield", "value": 1})
            self.log.append(f"🛡️ {player.name} kích hoạt Lá Chắn")
        elif item_type == "DAO_GAM":
            if target_id:
                target = next(p for p in self.players if p.id == target_id)
                if abs(target.position - player.position) <= 3:
                    target.position = max(1, target.position - 4)
                    self.log.append(f"🔪 {player.name} đá {target.name} lùi 4 ô")
                else:
                    self.log.append(f"❌ {target.name} ở ngoài bán kính")
        elif item_type == "BUA_HO_MENH":
            player.statuses.append({"kind": "extra_turn", "value": 1})
            self.log.append(f"🪆 {player.name} nhận thêm 1 lượt từ Bùa Hộ Mệnh")
        elif item_type == "KINH_AP_TRONG":
            if delta is not None:
                player.statuses.append({"kind": "lens", "value": delta})
                self.log.append(f"👁️ {player.name} điều chỉnh xúc xắc {delta:+d}")
        player.items.remove(item_type)
        return True

    def buy_item(self, player_id: str, item_type: str):
        player = next(p for p in self.players if p.id == player_id)
        info = ITEM_INFO.get(item_type)
        if not info:
            return False
        if self.item_stock.get(item_type, 0) <= 0:
            return False
        if player.gold < info["price"]:
            return False
        if len(player.items) >= 2:
            return False
        player.gold -= info["price"]
        player.items.append(item_type)
        self.item_stock[item_type] -= 1
        self.log.append(f"🛒 {player.name} mua {info['emoji']} {info['name']}")
        return True

    def skip_shop(self, player_id: str):
        self.pending_shop_tile = False
        self.log.append(f"🚶 {next(p for p in self.players if p.id == player_id).name} bỏ qua cửa hàng")
        self.next_turn()

    def resolve_pending(self, player_id: str, choice: dict):
        if not self.pending_action:
            return
        self.pending_action = None
        self.next_turn()
