import json
import base64
import zlib
from typing import Dict, Optional
from dataclasses import dataclass
from worlds.yayarg.yaml_scanner import collect_all_option_values
from Utils import user_path, local_path
import os
import pkgutil
import orjson

@dataclass
class YargExportSongData:
    Title: str
    Difficulties: Dict[str, int]

def _find_song_data_file(filename: str) -> Optional[str]:
    # if the string is greater than most os file length limits, I think we can assume it's not a file
    if len(filename) >= 255:
        return None
    
    user_song_dir = os.path.join(user_path(), 'YAYARG Song Data')
    local_song_dir = os.path.join(local_path(), 'YAYARG Song Data')
    
    os.makedirs(user_song_dir, exist_ok=True)
    file_path = os.path.join(user_song_dir, filename)
    
    if os.path.isfile(file_path):
        return file_path
    elif os.path.isfile(file_path + ".json"):
        return file_path + ".json"
    
    # It shouldn't exist here? but just in case.
    if os.path.isdir(local_song_dir):
        file_path = os.path.join(local_song_dir, filename)
        
        if os.path.isfile(file_path):
            return file_path
        elif os.path.isfile(file_path + ".json"):
            return file_path + ".json"
    
    return None


def _validate_and_convert_song_data(raw_dict: Dict[str, dict]) -> Optional[Dict[str, YargExportSongData]]:
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

def loadDefaultSongList():
    raw = pkgutil.get_data(__name__, "data/DefaultSongExport.json")
    raw_dict = orjson.loads(raw)
    return _validate_and_convert_song_data(raw_dict)

def _deserialize_from_file(file_path: str) -> Optional[Dict[str, YargExportSongData]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_dict: Dict[str, dict] = json.load(f)
        return _validate_and_convert_song_data(raw_dict)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  Warning: Error reading or parsing file: {e}")
        return None


def _deserialize_from_base64(base64_string: str) -> Optional[Dict[str, YargExportSongData]]:
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
        decompressed: bytes = zlib.decompress(compressed, -15)
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
    
    return _validate_and_convert_song_data(raw_dict)


def deserialize_song_data(base64_string: str) -> Optional[Dict[str, YargExportSongData]]:
    file_path = _find_song_data_file(base64_string)
    if file_path:
        return _deserialize_from_file(file_path)
    
    return _deserialize_from_base64(base64_string)


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