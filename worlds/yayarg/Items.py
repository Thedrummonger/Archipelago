from dataclasses import dataclass
from random import Random
from typing import Dict, NamedTuple, List
from BaseClasses import Item, ItemClassification
from .Options import VALID_INSTRUMENTS
from .data_register import nice_name

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

# ------------------------------------------------------------------------------
# Global Item Data and Song Pool Initialization
# ------------------------------------------------------------------------------

static_item_data: Dict[str, YargItemData] = {
    StaticItems.Victory: YargItemData(
        itemName=StaticItems.Victory,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.FamePoint: YargItemData(
        itemName=StaticItems.FamePoint,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.SongCompletion: YargItemData(
        itemName=StaticItems.SongCompletion,
        classification=ItemClassification.progression_skip_balancing
    ),
    StaticItems.StarPower: YargItemData(
        itemName=StaticItems.StarPower,
        classification=ItemClassification.filler
    ),
    StaticItems.SwapRandom: YargItemData(
        itemName=StaticItems.SwapRandom,
        classification=ItemClassification.filler
    ),
    StaticItems.SwapPick: YargItemData(
        itemName=StaticItems.SwapPick,
        classification=ItemClassification.useful
    ),
    StaticItems.LowerDifficulty: YargItemData(
        itemName=StaticItems.LowerDifficulty,
        classification=ItemClassification.useful
    ),
    StaticItems.TrapRestart: YargItemData(
        itemName=StaticItems.TrapRestart,
        classification=ItemClassification.trap
    ),
    StaticItems.TrapRockMeter: YargItemData(
        itemName=StaticItems.TrapRockMeter,
        classification=ItemClassification.trap
    ),
}

for inst in VALID_INSTRUMENTS:
    static_item_data[nice_name(inst)] = YargItemData(
        itemName=nice_name(inst),
        classification=ItemClassification.progression
    )

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

