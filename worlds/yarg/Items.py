from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import Dict, NamedTuple, Optional, List
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

class StaticItems:
    Victory: str    = "Victory"
    FamePoint: str  = "Fame Point"
    SwapRandom: str = "Swap Song (Random)"
    SwapPick: str   = "Swap Song (Pick)"
    TrapRestart: str = "Restart Trap"

# ------------------------------------------------------------------------------
# Global Item Data and Song Pool Initialization
# ------------------------------------------------------------------------------

ItemIndex: int = 5874530000

item_data_table: Dict[str, YargItemData] = {
    StaticItems.Victory: YargItemData(
        code=5874530000,
        itemName=StaticItems.Victory,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.FamePoint: YargItemData(
        code=5874530001,
        itemName=StaticItems.FamePoint,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.SwapRandom: YargItemData(
        code=5874530002,
        itemName=StaticItems.SwapRandom,
        classification=ItemClassification.filler
    ),
    StaticItems.SwapPick: YargItemData(
        code=5874530003,
        itemName=StaticItems.SwapPick,
        classification=ItemClassification.useful
    ),
    StaticItems.TrapRestart: YargItemData(
        code=5874530004,
        itemName=StaticItems.TrapRestart,
        classification=ItemClassification.trap
    ),
}

ItemIndex += len(item_data_table)

song_pool: List[str] = []

# Create all of our song unlock items
for x in range(1, maxSongs + 1):
    song_name = YargItemHelpers.CreateSongItemName(x)
    item_data_table[song_name] = YargItemData(
        code=ItemIndex,
        itemName=song_name,
        classification=ItemClassification.progression
    )
    song_pool.append(song_name)
    ItemIndex += 1

# I guess all APWorld require this
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
