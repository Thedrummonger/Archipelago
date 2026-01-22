from dataclasses import dataclass
from random import Random
from typing import NamedTuple, List
from BaseClasses import Item, ItemClassification

# ------------------------------------------------------------------------------
# Item Classes and Helpers
# ------------------------------------------------------------------------------

class YargItem(Item):
    game: str = "Yarg"
    
class YargItemData(NamedTuple):
    itemName: str
    classification: ItemClassification

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

static_item_data = {
    ItemClassification.progression_skip_balancing: [
        StaticItems.Victory,
        StaticItems.FamePoint,
        StaticItems.SongCompletion
    ],
    ItemClassification.filler: [
        StaticItems.StarPower,
        StaticItems.SwapRandom,
        StaticItems.SwapPick
    ],
    ItemClassification.useful:[
        StaticItems.SwapRandom,
        StaticItems.SwapPick,
        StaticItems.LowerDifficulty
    ],
    ItemClassification.trap: [
        StaticItems.TrapRestart,
        StaticItems.TrapRockMeter
    ]
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

