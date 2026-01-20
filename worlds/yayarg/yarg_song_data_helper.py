import json
import base64
import zlib
import math
from typing import Dict, Optional
from dataclasses import dataclass, field

from worlds.yayarg.yaml_scanner import collect_all_option_values


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

@dataclass
class YargSongData:
    Title: str
    Hash: str
    Difficulties: Dict[str, int]
    UnlockItem: str
    main_location: str
    extra_location: str
    fame_location: str

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

    for songData in song_values:
        song_dict = deserialize_song_data(songData)

        if song_dict is None:
            raise ValueError("Failed to deserialize song data from YAML")
    
        for checksum, song in song_dict.items():
            if checksum not in import_data.hash_to_song_data:
                data = YargSongData(
                    Title=f"{song.Title} [{APLocIDCounter}]",
                    Hash=checksum,
                    Difficulties=song.Difficulties,
                    UnlockItem=f"{song.Title} [{APItemIDCounter}]",
                    main_location=f"{song.Title} [{APLocIDCounter}]",
                    extra_location=f"{song.Title} [{APLocIDCounter + 1}]",
                    fame_location=f"{song.Title} [{APLocIDCounter + 2}]"
                )
                
                import_data.hash_to_song_data[checksum] = data

                import_data.location_name_to_id[data.main_location] = APLocIDCounter
                import_data.location_name_to_id[data.extra_location] = APLocIDCounter + 1
                import_data.location_name_to_id[data.fame_location] = APLocIDCounter + 2

                import_data.location_id_to_song_data[APLocIDCounter] = data
                import_data.location_id_to_song_data[APLocIDCounter + 1] = data
                import_data.location_id_to_song_data[APLocIDCounter + 2] = data

                APLocIDCounter += 3

                import_data.location_name_to_song_data[data.main_location] = data
                import_data.location_name_to_song_data[data.extra_location] = data
                import_data.location_name_to_song_data[data.fame_location] = data

                import_data.item_name_to_id[data.UnlockItem] = APItemIDCounter
                APItemIDCounter += 1


    for i in range(math.ceil(len(import_data.hash_to_song_data) / 2)):
        songpack = f"Song Pack {i+1}"
        import_data.song_pack_id_to_name[i+1] = songpack
        import_data.item_name_to_id[songpack] = APItemIDCounter
        APItemIDCounter += 1

    return import_data    


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