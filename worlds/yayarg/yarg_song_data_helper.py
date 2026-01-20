import json
import base64
import zlib
from typing import Dict, Optional
from dataclasses import dataclass
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