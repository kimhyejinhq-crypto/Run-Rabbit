# -*- coding: utf-8 -*-
import uuid
from .game_engine import GameEngine

class GameRoom:
    def __init__(self):
        self.room_id = str(uuid.uuid4())[:8]
        self.engine = GameEngine(self.room_id)
        self.max_players = 4
        self.is_full = False

    def add_player(self, player_id, name, character):
        if len(self.engine.players) >= self.max_players:
            return False
        return self.engine.add_player(player_id, name, character)

    def get_state(self):
        return self.engine.get_state()

# Lưu trữ các phòng đang hoạt động (trong bộ nhớ)
rooms = {}

def create_room():
    room = GameRoom()
    rooms[room.room_id] = room
    return room

def get_room(room_id):
    return rooms.get(room_id)

def delete_room(room_id):
    if room_id in rooms:
        del rooms[room_id]
