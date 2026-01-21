from collections import defaultdict
from typing import Dict


def split_pools_by_instrument(song_pools: Dict[str, Dict]) -> Dict[str, Dict[str, Dict]]:
    pools_by_instrument = defaultdict(dict)
    
    for pool_name, pool_data in song_pools.items():
        instrument = pool_data["instrument"]
        pools_by_instrument[instrument][pool_name] = pool_data
    
    return dict(pools_by_instrument)