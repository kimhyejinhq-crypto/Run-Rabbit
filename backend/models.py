# -*- coding: utf-8 -*-
class Tile:
    def __init__(self, index, type, jump_target=None):
        self.index = index
        self.type = type
        self.jump_target = jump_target  # chỉ dùng cho ô XANH

    def to_dict(self):
        return {
            'index': self.index,
            'type': self.type.value,
            'jump_target': self.jump_target,
        }

class Player:
    def __init__(self, player_id, name, character):
        self.id = player_id
        self.name = name
        self.character = character  # 'quang', 'trang', 'thanh', 'jin'
        self.position = 1
        self.gold = 0
        self.items = []  # danh sách vật phẩm (chuỗi tên)
        self.is_finished = False
        self.turn_skipped = False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'character': self.character,
            'position': self.position,
            'gold': self.gold,
            'items': self.items,
            'is_finished': self.is_finished,
        }
