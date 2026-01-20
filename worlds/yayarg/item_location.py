import math
import re
from typing import Dict
from .Options import VALID_INSTRUMENTS
from worlds.yayarg.yaml_scanner import collect_all_option_values
from worlds.yayarg.yarg_song_data_helper import deserialize_song_data, YargExportSongData
from .Items import static_item_data
from BaseClasses import ItemClassification

class YargSongData:
    def __init__(self, Hash: str, Difficulties: Dict[str, int]):
        self.Hash: str = Hash
        self.Difficulties: Dict[str, int] = Difficulties
        self.main_locations: Dict[str, str] = {} # instrument key -> location name
        self.extra_locations: Dict[str, str] = {}
        self.completion_locations: Dict[str, str] = {}
        self.unlock_items: Dict[str, str] = {} # instrument key -> item name

class YargAPImportData:
    def __init__(self):
        self.hash_to_song_data: Dict[str, YargSongData] = {}
        self.location_name_to_song_data: Dict[str, YargSongData] = {}
        self.location_id_to_song_data: Dict[int, YargSongData] = {}
        self.location_name_to_id: Dict[str, int] = {}
        self.item_name_to_id: Dict[str, int] = {}
        self.song_pack_id_to_name: Dict[int, str] = {}
        self.item_name_to_classification: Dict[str, ItemClassification] = {}

def nice_name(name):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name)

def ImportAndCreateItemLocationData() -> YargAPImportData:
    song_values = collect_all_option_values(verbose=False)

    import_data = YargAPImportData()

    APLocIDCounter = CreateStaticLocations(import_data)
    APItemIDCounter = CreateStaticItems(import_data)

    SongNum = 1

    for SerializedSongList in song_values:
        song_dict = deserialize_song_data(SerializedSongList)
        if song_dict is None:
            raise ValueError("Failed to deserialize song data from YAML")
        
        for checksum, song in song_dict.items():
            if checksum not in import_data.hash_to_song_data:
                data = YargSongData(Hash=checksum, Difficulties=song.Difficulties)

                import_data.hash_to_song_data[checksum] = data
                
                locations_registered = register(import_data, data, song, 'none', '', APLocIDCounter, APItemIDCounter, SongNum)
                APLocIDCounter += locations_registered
                APItemIDCounter += 1
                
                for instrument in VALID_INSTRUMENTS:
                    inst = nice_name(instrument)
                    locations_registered = register(import_data, data, song, inst, f' ({inst})', APLocIDCounter, APItemIDCounter, SongNum)
                    APLocIDCounter += locations_registered
                    APItemIDCounter += 1
                
                SongNum += 1

    for i in range(math.ceil(len(import_data.item_name_to_id) / 2)):
        songpack = f"Song Pack {i+1}"
        import_data.song_pack_id_to_name[i+1] = songpack
        import_data.item_name_to_id[songpack] = APItemIDCounter
        import_data.item_name_to_classification[songpack] = ItemClassification.progression
        APItemIDCounter += 1

    return import_data 
   
def register(
        ImportData: YargAPImportData,
        songData: YargSongData, 
        ExportData: YargExportSongData, 
        instrument_key: str, 
        instrument_display: str, 
        current_location_id: int, 
        current_item_id: int, 
        song_num: int) -> int:

    itemName = f'Song {song_num}: {ExportData.Title}{instrument_display}'
    songData.unlock_items[instrument_key] = itemName
    ImportData.item_name_to_id[itemName] = current_item_id
    ImportData.item_name_to_classification[itemName] = ItemClassification.progression
    
    locations = [
        (songData.main_locations, f'Song {song_num}: {ExportData.Title}{instrument_display} Reward 1'),
        (songData.extra_locations, f'Song {song_num}: {ExportData.Title}{instrument_display} Reward 2'),
        (songData.completion_locations, f'Song {song_num}: {ExportData.Title}{instrument_display} Completion')
    ]
    
    for i, (location_dict, location_name) in enumerate(locations):
        location_dict[instrument_key] = location_name
        loc_id = current_location_id + i
        ImportData.location_name_to_id[location_name] = loc_id
        ImportData.location_name_to_song_data[location_name] = songData
        ImportData.location_id_to_song_data[loc_id] = songData
    return len(locations)

def CreateStaticLocations(import_data: YargAPImportData):
    location_index = 0
    return location_index

def CreateStaticItems(import_data: YargAPImportData):
    item_index = 0
    for name, data in static_item_data.items():
        import_data.item_name_to_id[name] = item_index
        import_data.item_name_to_classification[name] = data.classification
        item_index += 1
    return item_index