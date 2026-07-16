# -*- coding: utf-8 -*-
from enum import Enum

class TileType(Enum):
    TRONG = "TRONG"         # xuất phát
    DICH = "DICH"           # đích
    VANG = "VANG"           # vàng
    DO = "DO"               # đỏ
    XANH = "XANH"           # xanh
    TIM = "TIM"             # tím
    CAM = "CAM"             # cam
    HONG = "HONG"           # hồng
    DEN = "DEN"             # đen (bẫy)
    TRANG = "TRANG"         # trắng (cửa hàng)

# Số lượng ô mỗi loại trong túi 150 thẻ
TILE_POOL_COUNTS = {
    TileType.VANG: 30,
    TileType.DO: 25,
    TileType.XANH: 20,
    TileType.TIM: 20,
    TileType.CAM: 15,
    TileType.HONG: 10,
    TileType.DEN: 15,
    TileType.TRANG: 10,
    # TRONG và DICH không nằm trong túi, sẽ được đặt cố định
}

TILES_TO_DRAW = 100
BOARD_SIZE = 100
START_TILE = 1
FINISH_TILE = 100

# Màu sắc hiển thị cho từng loại ô (cho frontend)
TILE_COLORS = {
    TileType.TRONG: "#4CAF50",  # xanh lá
    TileType.DICH: "#FFD700",   # vàng
    TileType.VANG: "#FFC107",
    TileType.DO: "#F44336",
    TileType.XANH: "#2196F3",
    TileType.TIM: "#9C27B0",
    TileType.CAM: "#FF9800",
    TileType.HONG: "#E91E63",
    TileType.DEN: "#212121",
    TileType.TRANG: "#FFFFFF",
}
