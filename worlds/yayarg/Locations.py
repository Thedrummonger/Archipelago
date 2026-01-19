from enum import Enum
import math
from typing import Dict, List, NamedTuple
from BaseClasses import Location
from .Options import maxSongs
from .Items import YargItemHelpers

# ------------------------------------------------------------------------------
# Location Types and Classes
# ------------------------------------------------------------------------------

class YargLocationType(Enum):
    Standard = 1
    Extra = 2
    Fame = 3
    Goal = 4

class YargLocation(Location):
    game: str = "Yarg"
    
class YargLocationData(NamedTuple):
    address: int
    loc_type: YargLocationType
    song_num: int

# ------------------------------------------------------------------------------
# Helper Functions for Location Names and Unlock Items
# ------------------------------------------------------------------------------

class YargLocationHelpers:
    @staticmethod
    def CreateSongLocationName(index: int, loc_type: YargLocationType) -> str:
        if loc_type == YargLocationType.Standard:
            return f"Song {index} Reward 1"
        elif loc_type == YargLocationType.Extra:
            return f"Song {index} Reward 2"
        elif loc_type == YargLocationType.Fame:
            return f"Song {index} Fame Point"
    
    @staticmethod
    def GetUnlockItem(location: str) -> str:
        data = location_data_table[location]
        return YargItemHelpers.CreateSongItemName(data.song_num)
    
    @staticmethod
    def GetUnlockPack(location: str, packAmount: int) -> str:
        data = location_data_table[location]
        pack_num = math.ceil(data.song_num / packAmount)
        return YargItemHelpers.CreateSongPackName(pack_num)
        
    
    @staticmethod
    def GetLinkedCheck(location: str, loc_type: YargLocationType) -> str:
        data = location_data_table[location]
        return YargLocationHelpers.CreateSongLocationName(data.song_num, loc_type)
            
    @staticmethod
    def get_locations_by_type(loc_type: YargLocationType) -> List[str]:
        return [key for key, value in location_data_table.items() if value.loc_type == loc_type]

# ------------------------------------------------------------------------------
# Global Location Data Initialization
# ------------------------------------------------------------------------------

class StaticLocations:
    GoalSong: str    = "Goal Song"

LocationIndex: int = 5874530000

def get_next_location_code() -> int:
    global LocationIndex
    code = LocationIndex
    LocationIndex += 1
    return code

location_data_table: Dict[str, YargLocationData] = {
    StaticLocations.GoalSong: YargLocationData(address=get_next_location_code(), loc_type=YargLocationType.Goal, song_num=0),
}

# For each song, create Standard, Extra, and Fame locations. Extra is created based on our options and Fame is created for world tour mode
for x in range(1, maxSongs + 1):
    # Standard location
    standard_name = YargLocationHelpers.CreateSongLocationName(x, YargLocationType.Standard)
    location_data_table[standard_name] = YargLocationData(
        address=get_next_location_code(), 
        loc_type=YargLocationType.Standard, 
        song_num=x
    )

    # Extra location
    extra_name = YargLocationHelpers.CreateSongLocationName(x, YargLocationType.Extra)
    location_data_table[extra_name] = YargLocationData(
        address=get_next_location_code(), 
        loc_type=YargLocationType.Extra, 
        song_num=x
    )

    # Fame location
    fame_name = YargLocationHelpers.CreateSongLocationName(x, YargLocationType.Fame)
    location_data_table[fame_name] = YargLocationData(
        address=get_next_location_code(), 
        loc_type=YargLocationType.Fame, 
        song_num=x
    )

location_table = {name: data.address for name, data in location_data_table.items() if data.address is not None}
