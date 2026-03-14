from enum import IntEnum

class SupLeftTiles(IntEnum):
    PC = 121
    PARTY_MENU = 127
    PKM_DETAIL = 42
    POKEDEX = 52
    POKEDEX_DETAIL = 51
    BAG = 40
    PKGEAR = 70
    TRAINER_CARD = 35
    TRADE_SCREEN = 63

FULL_SCREEN_CASES = (
    SupLeftTiles.PC, 
    SupLeftTiles.PARTY_MENU, 
    SupLeftTiles.PKM_DETAIL, 
    SupLeftTiles.POKEDEX_DETAIL, 
    SupLeftTiles.BAG, 
    SupLeftTiles.PKGEAR, 
    SupLeftTiles.TRAINER_CARD,
    SupLeftTiles.TRADE_SCREEN
)

class Tiles(IntEnum):
    TEXTBOX_INF_RIGHT = 126
    MENU_SUP_CENTER = 121
    SAVING_MENU_SUP_CENTER = 122