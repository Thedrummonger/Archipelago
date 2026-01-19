import os
import sys
from typing import List, Any, Optional

from attr import dataclass
from Utils import parse_yamls, user_path, get_settings

DEFAULT_GAME_NAME = "YAYARG"
DEFAULT_OPTION_NAME = "songList"

def collect_all_option_values(game_name: str = DEFAULT_GAME_NAME, option_name: str = DEFAULT_OPTION_NAME, verbose: bool = True) -> List[str]:
    
    try:
        settings = get_settings()
        folder_path = user_path(settings["generator"]["player_files_path"])
        
        if "--player_files_path" in sys.argv:
            idx = sys.argv.index("--player_files_path")
            if idx + 1 < len(sys.argv):
                folder_path = sys.argv[idx + 1]
    except Exception as e:
        if verbose:
            print(f"[{game_name}] Error getting player files path: {e}")
        return []
    
    if not os.path.isdir(folder_path):
        if verbose:
            print(f"[{game_name}] Warning: Not a directory: {folder_path}")
        return []
    
    if verbose:
        print(f"[{game_name}] Collecting all '{option_name}' values from YAMLs...")
    
    all_values = []
    files_processed = 0
    values_found = 0
    
    for file in os.scandir(folder_path):
        fname = file.name
        
        if not file.is_file():
            continue
        if fname.startswith("."):
            continue
        if fname.lower().endswith(".ini"):
            continue
        
        path = os.path.join(folder_path, fname)
        files_processed += 1
        
        try:
            with open(path, 'rb') as f:
                yaml_content = str(f.read(), "utf-8-sig")
            
            for doc_idx, yaml_doc in enumerate(parse_yamls(yaml_content)):
                if yaml_doc is None:
                    continue
                
                game_value = yaml_doc.get('game')
                is_our_game = False
                
                if game_value == game_name:
                    is_our_game = True
                
                elif isinstance(game_value, dict) and game_name in game_value:
                    is_our_game = True
                
                elif isinstance(game_value, list) and game_name in game_value:
                    is_our_game = True
                
                if is_our_game:
                    value = _extract_option_from_yaml(yaml_doc, game_name, option_name)
                    
                    if value is not None:
                        if ',' in value:
                            for item in value.split(','):
                                item = item.strip()
                                if item:
                                    all_values.append(item)
                                    values_found += 1
                                    if verbose:
                                        print(f"  Found in {fname}: '{item}'")
                        else:
                            all_values.append(value)
                            values_found += 1
                            if verbose:
                                print(f"  Found in {fname}: '{value}'")
        
        except Exception as e:
            if verbose:
                print(f"  Warning: Error reading {fname}: {e}")
            continue
    
    if verbose:
        print(f"[{game_name}] Processed {files_processed} files, found {values_found} values")
    
    return all_values


def _extract_option_from_yaml(yaml_doc: dict, game_name: str, option_name: str) -> Optional[str]:
    
    if game_name in yaml_doc:
        game_options = yaml_doc[game_name]
        if isinstance(game_options, dict) and option_name in game_options:
            return _process_option_value(game_options[option_name])
    
    if option_name in yaml_doc:
        return _process_option_value(yaml_doc[option_name])
    
    return None


def _process_option_value(value: Any) -> Optional[str]:

    if value is None:
        return None
    
    if isinstance(value, str):
        return value if value.lower() != 'random' else None
    
    if isinstance(value, dict):
        keys = list(value.keys())
        return ','.join(str(k) for k in keys) if keys else None
    
    if isinstance(value, list):
        return ','.join(str(v) for v in value) if value else None
    
    return str(value)

def test_scanner():
    print("Testing YAML Scanner")
    print("=" * 70)
    
    all_values = collect_all_option_values(
        game_name=DEFAULT_GAME_NAME,
        option_name=DEFAULT_OPTION_NAME,
        verbose=True
    )
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if not all_values:
        print("No values found!")
        print(f"\nMake sure you have YAMLs with:")
        print(f"  game: {DEFAULT_GAME_NAME}")
        print(f"  {DEFAULT_OPTION_NAME}: <value>")
    else:
        print(f"All values (including duplicates): {all_values}")
        print(f"\nTotal values collected: {len(all_values)}")
        
        unique = list(set(all_values))
        print(f"Unique values: {unique}")
        print(f"Unique count: {len(unique)}")
    
    print("=" * 70)
    return all_values


if __name__ == "__main__":
    try:
        test_scanner()
    except ModuleNotFoundError as e:
        print("="*70)
        print(f"Missing module: {e}")
        print("\nRun from Archipelago root:")
        print("  python -m worlds.yayarg.yaml_scanner")
        print("="*70)