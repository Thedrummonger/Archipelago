import json
import base64
import re
import zlib
import math
from typing import Dict, Optional
from dataclasses import dataclass, field
from .Options import VALID_INSTRUMENTS
from worlds.yayarg.yaml_scanner import collect_all_option_values

def nice_name(name):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name)

@dataclass
class YargExportSongData:
    Title: str
    Difficulties: Dict[str, int]


def deserialize_song_data(base64_string: str) -> Optional[Dict[str, YargExportSongData]]:
    try:
        base64_string = base64_string.replace('-', '+').replace('_', '/')
        padding = 4 - (len(base64_string) % 4)
        if padding != 4:
            base64_string += '=' * padding
        
        compressed: bytes = base64.b64decode(base64_string)
    except Exception:
        print("  Warning: Base64 decoding failed")
        return None
    
    try:
        decompressed: bytes = zlib.decompress(compressed,-15)
    except zlib.error:
        print("  Warning: Zlib decompression failed")
        return None
    
    try:
        json_string: str = decompressed.decode('utf-8')
    except UnicodeDecodeError:
        print("  Warning: UTF-8 decoding failed")
        return None
    
    try:
        raw_dict: Dict[str, dict] = json.loads(json_string)
    except json.JSONDecodeError:
        print("  Warning: JSON decoding failed")
        return None
    
    if not isinstance(raw_dict, dict):
        print("  Warning: Deserialized data is not a dictionary")
        return None
    
    song_dict: Dict[str, YargExportSongData] = {}
    
    try:
        for checksum, data in raw_dict.items():
            if not isinstance(data, dict):
                print(f"  Warning: Data for checksum {checksum} is not a dictionary")
                return None
            if "Title" not in data or "Difficulties" not in data:
                print(f"  Warning: Missing required fields in data for checksum {checksum}")
                return None
            if not isinstance(data["Title"], str):
                print(f"  Warning: Title for checksum {checksum} is not a string")
                return None
            if not isinstance(data["Difficulties"], dict):
                print(f"  Warning: Difficulties for checksum {checksum} is not a dictionary")
                return None
            
            song_dict[checksum] = YargExportSongData(
                Title=data["Title"],
                Difficulties=data["Difficulties"]
            )
    except (KeyError, TypeError):
        print("  Warning: Error processing song data")
        return None
    
    return song_dict

class YargSongData:
    def __init__(self, Hash: str, Difficulties: Dict[str, int], UnlockItem: str):
        self.Hash: str = Hash
        self.Difficulties: Dict[str, int] = Difficulties
        self.UnlockItem: str = UnlockItem
        self.main_locations: Dict[str, str] = {}
        self.extra_locations: Dict[str, str] = {}
        self.fame_locations: Dict[str, str] = {}

class YargAPImportData:
    def __init__(self):
        self.hash_to_song_data: Dict[str, YargSongData] = {}
        self.location_name_to_song_data: Dict[str, YargSongData] = {}
        self.location_id_to_song_data: Dict[int, YargSongData] = {}
        self.location_name_to_id: Dict[str, int] = {}
        self.item_name_to_id: Dict[str, int] = {}
        self.song_pack_id_to_name: Dict[int, str] = {}

def ReadSongDataFromYAMLs() -> YargAPImportData:
    song_values = collect_all_option_values(verbose=False)

    import_data = YargAPImportData()

    APLocIDCounter = 1
    APItemIDCounter = 1

    SongNum = 1

    for songData in song_values:
        song_dict = deserialize_song_data(songData)
        if song_dict is None:
            raise ValueError("Failed to deserialize song data from YAML")
        
        for checksum, song in song_dict.items():
            if checksum not in import_data.hash_to_song_data:
                data = YargSongData(
                    Hash=checksum,
                    Difficulties=song.Difficulties,
                    UnlockItem=f"{song.Title} [{APItemIDCounter}]",
                )
                import_data.hash_to_song_data[checksum] = data
                
                registered = register_location_set(import_data, data, song, 'none', '', APLocIDCounter, SongNum)
                APLocIDCounter += registered
                
                for instrument in VALID_INSTRUMENTS:
                    inst = nice_name(instrument)
                    registered = register_location_set(import_data, data, song, inst, f' ({inst})', APLocIDCounter, SongNum)
                    APLocIDCounter += registered
                
                import_data.item_name_to_id[data.UnlockItem] = APItemIDCounter
                APItemIDCounter += 1
                SongNum += 1

    for i in range(math.ceil(len(import_data.hash_to_song_data) / 2)):
        songpack = f"Song Pack {i+1}"
        import_data.song_pack_id_to_name[i+1] = songpack
        import_data.item_name_to_id[songpack] = APItemIDCounter
        APItemIDCounter += 1

    return import_data 
   
def register_location_set(
        ImportData: YargAPImportData,
        songData: YargSongData, 
        ExportData: YargExportSongData, 
        instrument_key: str, 
        instrument_display: str, 
        base_id: int, 
        song_num: int) -> int:
    
    locations = [
        (songData.main_locations, f'Song {song_num}: {ExportData.Title}{instrument_display} Reward 1'),
        (songData.extra_locations, f'Song {song_num}: {ExportData.Title}{instrument_display} Reward 2'),
        (songData.fame_locations, f'Song {song_num}: {ExportData.Title}{instrument_display} Fame Point')
    ]
    
    for i, (location_dict, location_name) in enumerate(locations):
        location_dict[instrument_key] = location_name
        loc_id = base_id + i
        ImportData.location_name_to_id[location_name] = loc_id
        ImportData.location_name_to_song_data[location_name] = songData
        ImportData.location_id_to_song_data[loc_id] = songData
    return len(locations)


if __name__ == "__main__":
    data = collect_all_option_values(verbose=False)

    counter = 0
    for songData in data:
        counter += 1
        song_dict = deserialize_song_data(songData)
        if song_dict is not None:
            print("-"*70)
            print(f"YAML {counter} data:")
            for checksum, song in song_dict.items():
                print(f"Checksum: {checksum}, Title: {song.Title}, Difficulties: {song.Difficulties}")
        else:
            print(f"YAML {counter} data could not be deserialized.")