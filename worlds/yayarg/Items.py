from dataclasses import dataclass
from random import Random
from typing import Dict, NamedTuple, List
from BaseClasses import Item, ItemClassification
from .Options import maxSongs

# ------------------------------------------------------------------------------
# Item Classes and Helpers
# ------------------------------------------------------------------------------

class YargItem(Item):
    game: str = "Yarg"
    
class YargItemData(NamedTuple):
    code: int
    itemName: str
    classification: ItemClassification

class YargItemHelpers:
    @staticmethod
    def CreateSongItemName(index: int) -> str:
        return f"Song {index}"
    @staticmethod
    def CreateSongPackName(index: int) -> str:
        return f"Song Pack {index}"

class StaticItems:
    Victory: str    = "Victory"
    FamePoint: str  = "Fame Point"
    SongCompletion: str  = "Song Completion"
    StarPower: str  = "Star Power"
    SwapRandom: str = "Swap Song (Random)"
    SwapPick: str   = "Swap Song (Pick)"
    LowerDifficulty: str = "Lower Difficulty"
    TrapRestart: str = "Restart Trap"
    TrapRockMeter: str = "Rock Meter Trap"

# ------------------------------------------------------------------------------
# Global Item Data and Song Pool Initialization
# ------------------------------------------------------------------------------

ItemIndex: int = 5874530000

def get_next_item_code() -> int:
    global ItemIndex
    code = ItemIndex
    ItemIndex += 1
    return code

item_data_table: Dict[str, YargItemData] = {
    StaticItems.Victory: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.Victory,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.FamePoint: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.FamePoint,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.SongCompletion: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.SongCompletion,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.StarPower: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.StarPower,
        classification=ItemClassification.filler
    ),
    StaticItems.SwapRandom: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.SwapRandom,
        classification=ItemClassification.filler
    ),
    StaticItems.SwapPick: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.SwapPick,
        classification=ItemClassification.useful
    ),
    StaticItems.LowerDifficulty: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.LowerDifficulty,
        classification=ItemClassification.useful
    ),
    StaticItems.TrapRestart: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.TrapRestart,
        classification=ItemClassification.trap
    ),
    StaticItems.TrapRockMeter: YargItemData(
        code=get_next_item_code(),
        itemName=StaticItems.TrapRockMeter,
        classification=ItemClassification.trap
    ),
}

song_pool: List[str] = []

# Create all of our song unlock items
for x in range(1, maxSongs + 1):
    song_name = YargItemHelpers.CreateSongItemName(x)
    item_data_table[song_name] = YargItemData(
        code=get_next_item_code(),
        itemName=song_name,
        classification=ItemClassification.progression
    )
    song_pool.append(song_name)

# Create all of our song pack unlock items
for x in range(1, (maxSongs // 2) + 1):
    song_name = YargItemHelpers.CreateSongPackName(x)
    item_data_table[song_name] = YargItemData(
        code=get_next_item_code(),
        itemName=song_name,
        classification=ItemClassification.progression
    )
    song_pool.append(song_name)


item_table: Dict[str, int] = {
    name: data.code for name, data in item_data_table.items() if data.code is not None
}

# ------------------------------------------------------------------------------
# Weighted Item and Helper Function
# ------------------------------------------------------------------------------

@dataclass
class WeightedItem:
    name: str
    weight: float

def pick_weighted_item(seeded_random: Random, items: List[WeightedItem]) -> WeightedItem:
    """
    Picks one item from the list based on its weight.
    The higher the weight, the more likely the item is chosen.
    """
    return seeded_random.choices(items, weights=[item.weight for item in items], k=1)[0]
