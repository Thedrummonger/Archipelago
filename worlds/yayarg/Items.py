from dataclasses import dataclass
from random import Random
from typing import NamedTuple, List
from BaseClasses import Item, ItemClassification
from enum import Enum

# ------------------------------------------------------------------------------
# Item Classes and Helpers
# ------------------------------------------------------------------------------

class YargItem(Item):
    game: str = "Yarg"
    
class YargItemData(NamedTuple):
    itemName: str
    classification: ItemClassification

class StaticItems(Enum):
    Victory = ("Victory", ItemClassification.progression_skip_balancing)
    FamePoint = ("Fame Point", ItemClassification.progression_skip_balancing)
    SongCompletion = ("Song Completion", ItemClassification.progression_skip_balancing)
    StarPower = ("Star Power", ItemClassification.filler)
    SwapRandom = ("Swap Song (Random)", ItemClassification.useful)
    SwapPick = ("Swap Song (Pick)", ItemClassification.useful)
    LowerDifficulty = ("Lower Difficulty", ItemClassification.useful)
    TrapRestart = ("Restart Trap", ItemClassification.trap)
    TrapRockMeter = ("Rock Meter Trap", ItemClassification.trap)
    
    def __init__(self, nice_name: str, classification: ItemClassification):
        self.nice_name = nice_name
        self.classification = classification

class InstrumentItems(Enum):
    # Single point of definition - just nice names, all are progression
    FiveFretGuitar = "Five Fret Guitar"
    FiveFretBass = "Five Fret Bass"
    Keys = "Keys"
    SixFretGuitar = "Six Fret Guitar"
    SixFretBass = "Six Fret Bass"
    FourLaneDrums = "Four Lane Drums"
    ProDrums = "Pro Drums"
    FiveLaneDrums = "Five Lane Drums"
    ProKeys = "Pro Keys"
    Vocals = "Vocals"
    Harmony = "Harmony"
    
    def __init__(self, nice_name):
        self.nice_name = nice_name
        self.classification = ItemClassification.progression

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

