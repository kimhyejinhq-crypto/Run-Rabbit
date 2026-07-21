# backend/models.py
# -*- coding: utf-8 -*-

"""
Models - Định nghĩa dữ liệu
"""

from typing import List, Optional, Dict, Any
from .constants import TileType, ItemType

class Player:
    def __init__(self, id: int, name: str, color: str, character: str,
                 position: int = 1, gold: int = 10, debt: int = 0,
                 items: List[str] = None, statuses: List[Dict] = None,
                 finished: bool = False, offline: bool = False):
        self.id = id
        self.name = name
        self.color = color
        self.character = character
        self.position = position
        self.gold = gold
        self.debt = debt
        self.items = items or []
        self.statuses = statuses or []
        self.finished = finished
        self.offline = offline
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'character': self.character,
            'position': self.position,
            'gold': self.gold,
            'debt': self.debt,
            'items': self.items,
            'statuses': self.statuses,
            'finished': self.finished,
            'offline': self.offline
        }

class Tile:
    def __init__(self, index: int, type: TileType, jump_target: Optional[int] = None):
        self.index = index
        self.type = type
        self.jump_target = jump_target
    
    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'type': self.type.value,
            'jump_target': self.jump_target
        }

class GameState:
    def __init__(self, players: List[Player], board: List[Tile],
                 current_player_index: int, turn_count: int,
                 started: bool, game_over: bool, winner_id: Optional[int],
                 started_at: float, pending_action: Optional[Dict],
                 pending_shop_tile: bool, item_stock: Dict[str, int],
                 log: List[str]):
        self.players = players
        self.board = board
        self.current_player_index = current_player_index
        self.turn_count = turn_count
        self.started = started
        self.game_over = game_over
        self.winner_id = winner_id
        self.started_at = started_at
        self.pending_action = pending_action
        self.pending_shop_tile = pending_shop_tile
        self.item_stock = item_stock
        self.log = log
    
    def to_dict(self) -> Dict:
        return {
            'players': [p.to_dict() for p in self.players],
            'board': [t.to_dict() for t in self.board],
            'current_player_index': self.current_player_index,
            'turn_count': self.turn_count,
            'started': self.started,
            'game_over': self.game_over,
            'winner_id': self.winner_id,
            'started_at': self.started_at,
            'pending_action': self.pending_action,
            'pending_shop_tile': self.pending_shop_tile,
            'item_stock': self.item_stock,
            'log': self.log
        }
