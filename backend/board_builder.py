# -*- coding: utf-8 -*-
import random
from .constants import TileType, TILE_POOL_COUNTS, TILES_TO_DRAW, BOARD_SIZE, START_TILE, FINISH_TILE
from .models import Tile

def _build_tile_pool():
    pool = []
    for tile_type, count in TILE_POOL_COUNTS.items():
        pool.extend([tile_type] * count)
    random.shuffle(pool)
    return pool

def build_board():
    pool = _build_tile_pool()
    drawn_types = pool[:TILES_TO_DRAW]
    reserve_types = pool[TILES_TO_DRAW:]

    board = [None] * (BOARD_SIZE + 1)
    for i in range(1, BOARD_SIZE + 1):
        t_type = drawn_types[i - 1]
        board[i] = Tile(index=i, type=t_type)

    board[START_TILE] = Tile(index=START_TILE, type=TileType.TRONG)
    board[FINISH_TILE] = Tile(index=FINISH_TILE, type=TileType.DICH)

    for i in range(1, BOARD_SIZE + 1):
        if board[i].type == TileType.XANH:
            choices = [x for x in range(1, BOARD_SIZE + 1) if x != i]
            board[i].jump_target = random.choice(choices)

    reserve_pool = [Tile(index=-1, type=t) for t in reserve_types]
    return board, reserve_pool
