import math
import re
from typing import Dict
from worlds.yayarg.yaml_scanner import collect_all_option_values
from worlds.yayarg.yarg_song_data_helper import deserialize_song_data, YargExportSongData
from .Items import InstrumentItems, StaticItems
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

        self.used_base_names: set[str] = set()
        
        self.current_location_id: int = 0
        self.current_item_id: int = 0

def nice_name(name):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name)

def ImportAndCreateItemLocationData() -> YargAPImportData:

    song_values = collect_all_option_values(verbose=False)

    import_data = YargAPImportData()

    CreateStaticItems(import_data)

    for SerializedSongList in song_values:
        song_dict = deserialize_song_data(SerializedSongList)
        if song_dict is None:
            raise ValueError("Failed to deserialize song data from YAML")
        
        for checksum, song in song_dict.items():
            if checksum not in import_data.hash_to_song_data:
                data = YargSongData(Hash=checksum, Difficulties=song.Difficulties)

                import_data.hash_to_song_data[checksum] = data
                
                for instrument in InstrumentItems:
                    register(import_data, data, instrument.name, f'{song.Title} on {instrument.nice_name}')

    for i in range(math.ceil(len(import_data.item_name_to_id) / 2)):
        songpack = f"Song Pack {i+1}"
        import_data.song_pack_id_to_name[i+1] = songpack
        import_data.item_name_to_id[songpack] = import_data.current_item_id
        import_data.item_name_to_classification[songpack] = ItemClassification.progression
        import_data.current_item_id += 1

    return import_data 
   
def register(ImportData: YargAPImportData, songData: YargSongData, instrument_key: str, base_name: str):
    
    # If one or more users have the same song with the same title but a different hash
    # (due to different instruments or difficulties) make sure the names are unique.
    baseName = base_name
    postfix_counter = 0
    while baseName in ImportData.used_base_names:
        postfix_counter += 1
        baseName = f'{base_name} ({postfix_counter})'
    ImportData.used_base_names.add(baseName)

    songData.unlock_items[instrument_key] = baseName
    ImportData.item_name_to_id[baseName] = ImportData.current_item_id
    ImportData.item_name_to_classification[baseName] = ItemClassification.progression
    ImportData.current_item_id += 1
    
    locations = [
        (songData.main_locations, 'Reward 1'),
        (songData.extra_locations, 'Reward 2'),
        (songData.completion_locations, 'Completion')
    ]
    
    for location_dict, location_postfix in locations:
        location_name = f'{baseName} {location_postfix}'
        location_dict[instrument_key] = location_name
        ImportData.location_name_to_id[location_name] = ImportData.current_location_id
        ImportData.location_name_to_song_data[location_name] = songData
        ImportData.location_id_to_song_data[ImportData.current_location_id] = songData
        ImportData.current_location_id += 1
    return len(locations)

def CreateStaticItems(import_data: YargAPImportData):
    for item in StaticItems:
        import_data.item_name_to_id[item.nice_name] = import_data.current_item_id
        import_data.item_name_to_classification[item.nice_name] = item.classification
        import_data.current_item_id += 1
    
    for inst in InstrumentItems:
        import_data.item_name_to_id[inst.nice_name] = import_data.current_item_id
        import_data.item_name_to_classification[inst.nice_name] = inst.classification
        import_data.current_item_id += 1

