from enum import Enum

class TileType(Enum):
    TRONG = "TRONG"
    VANG = "VANG"
    DO = "DO"
    XANH = "XANH"
    TIM = "TIM"
    CAM = "CAM"
    HONG = "HONG"
    DICH = "DICH"

class ItemType(Enum):
    XUC_XAC_X2 = "XUC_XAC_X2"
    LA_CHAN = "LA_CHAN"
    DAO_GAM = "DAO_GAM"
    BUA_HO_MENH = "BUA_HO_MENH"
    KINH_AP_TRONG = "KINH_AP_TRONG"

ITEM_INFO = {
    "XUC_XAC_X2": {"name": "Xúc Xắc X2", "emoji": "🎲", "price": 7, "desc": "Tung 2 lần, lấy kết quả cao hơn", "max_stock": 3},
    "LA_CHAN": {"name": "Lá Chắn", "emoji": "🛡️", "price": 5, "desc": "Chặn 1 hiệu ứng xấu", "max_stock": 3},
    "DAO_GAM": {"name": "Dao Găm", "emoji": "🔪", "price": 8, "desc": "Đá lùi 4 ô người trong bán kính 3 ô", "max_stock": 2},
    "BUA_HO_MENH": {"name": "Bùa Hộ Mệnh", "emoji": "🪆", "price": 10, "desc": "Được tung thêm 1 lượt", "max_stock": 2},
    "KINH_AP_TRONG": {"name": "Kính Áp Tròng", "emoji": "👁️", "price": 6, "desc": "Điều chỉnh +1/-1 điểm xúc xắc", "max_stock": 3}
}
