from typing import Dict, List, Set
from collections import defaultdict
from dataclasses import dataclass
import random
from Options import OptionError
from worlds.yayarg.yarg_song_data_helper import YargExportSongData


@dataclass
class SongPoolConfig:
    name: str
    instrument: str
    amount_in_pool: int
    min_difficulty: int
    max_difficulty: int


class SongDistributionResult:
    def __init__(self):
        self.pool_assignments: Dict[str, List[str]] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.success: bool = True
        self.goal_placed: bool = False


class SongDistributor:
    def __init__(self, rnd: random.Random, song_pools: Dict[str, Dict], available_songs: Dict[str, YargExportSongData],
                 inclusion_lists: Dict[str, List[str]] = None, exclusion_lists: Dict[str, List[str]] = None,
                 goal_song: str = None, goal_pool: str = None):
        self.random = rnd
        self.song_pools = [SongPoolConfig(
            name=name,
            instrument=data["instrument"],
            amount_in_pool=data["amount_in_pool"],
            min_difficulty=data["min_difficulty"],
            max_difficulty=data["max_difficulty"]
        ) for name, data in song_pools.items()]
        self.available_songs = available_songs
        self.inclusion_lists = inclusion_lists or {}
        self.exclusion_lists = exclusion_lists or {}
        self.goal_song = goal_song
        self.goal_pool = goal_pool
        self.result = SongDistributionResult()
    
    def distribute(self) -> SongDistributionResult:
        active_pools = [p for p in self.song_pools if p.amount_in_pool > 0]

        assigned_songs: Set[str] = set()
        assigned_song_instruments: Dict[str, Set[str]] = defaultdict(set)

        if self._try_place_goal_song(active_pools, assigned_songs, assigned_song_instruments):
            self.result.goal_placed = True

        sorted_pools = sorted(active_pools, key=lambda p: (p.max_difficulty - p.min_difficulty, -p.amount_in_pool))

        for pool in sorted_pools:
            self._process_inclusion_list(pool, assigned_songs, assigned_song_instruments)

        for pool in sorted_pools:
            self._assign_songs_to_pool(pool, assigned_songs)

        self._backfill_shortages(sorted_pools)

        return self.result
    
    def _try_place_goal_song(self, pools: List[SongPoolConfig], assigned_songs: Set[str], assigned_song_instruments: Dict[str, Set[str]]) -> bool:
        
        if self.goal_song and self.goal_song not in self.available_songs:
            raise OptionError(f"Goal song '{self.goal_song}' is not in the available songs")
        
        if self.goal_pool and self.goal_song:
            target_pool = next((p for p in pools if p.name == self.goal_pool), None)
            if not target_pool:
                return False # Target Pool wasn't in this passthrough
            
            song_data = self.available_songs[self.goal_song]
            if target_pool.instrument not in song_data.Difficulties:
                raise OptionError(
                    f"Goal song '{self.goal_song}' does not have instrument '{target_pool.instrument}' "
                    f"required by goal pool '{self.goal_pool}'"
                )
            
            if target_pool.name not in self.result.pool_assignments:
                self.result.pool_assignments[target_pool.name] = []
            
            self.result.pool_assignments[target_pool.name].append(self.goal_song)
            assigned_songs.add(self.goal_song)
            assigned_song_instruments[self.goal_song].add(target_pool.instrument)
            return True
        elif self.goal_song:
            song_data = self.available_songs[self.goal_song]
            
            shuffled_pools = pools.copy()
            self.random.shuffle(shuffled_pools)

            for pool in shuffled_pools:
                if (pool.instrument in song_data.Difficulties and pool.instrument not in assigned_song_instruments[self.goal_song]):
                    
                    if pool.name not in self.result.pool_assignments:
                        self.result.pool_assignments[pool.name] = []
                    
                    self.result.pool_assignments[pool.name].append(self.goal_song)
                    assigned_songs.add(self.goal_song)
                    assigned_song_instruments[self.goal_song].add(pool.instrument)
                    return True
            
            return False # Goal Song did not have the instrument for any pool in this pass
        
        return True # We didn't define a goal song se we are done.
    
    def _process_inclusion_list(self, pool: SongPoolConfig, assigned_songs: Set[str], 
                                 assigned_song_instruments: Dict[str, Set[str]]):
        if pool.name not in self.inclusion_lists:
            return
        
        included_songs = list(set(self.inclusion_lists[pool.name]))
        
        if pool.name not in self.result.pool_assignments:
            self.result.pool_assignments[pool.name] = []
        
        songs_to_include = min(len(included_songs), pool.amount_in_pool)
        
        for song_hash in included_songs[:songs_to_include]:
            if song_hash not in self.available_songs:
                raise OptionError(f"Inclusion list for pool '{pool.name}' contains unknown song hash: {song_hash}")
            
            song_data = self.available_songs[song_hash]
            
            if pool.instrument not in song_data.Difficulties:
                raise OptionError(
                    f"Inclusion list for pool '{pool.name}' contains song '{song_hash}' "
                    f"which does not have instrument '{pool.instrument}'"
                )
            
            if pool.instrument in assigned_song_instruments[song_hash]:
                continue
            
            self.result.pool_assignments[pool.name].append(song_hash)
            assigned_songs.add(song_hash)
            assigned_song_instruments[song_hash].add(pool.instrument)
    
    def _assign_songs_to_pool(self, pool: SongPoolConfig, assigned_songs: Set[str]):
        exclusion_set = set(self.exclusion_lists.get(pool.name, []))
        
        eligible = [
            song_hash for song_hash in self.available_songs.keys()
            if song_hash not in assigned_songs
            and song_hash not in exclusion_set
            and self._song_fits_pool(song_hash, pool)
        ]
        
        self.random.shuffle(eligible)
        
        current_count = len(self.result.pool_assignments.get(pool.name, []))
        needed = pool.amount_in_pool - current_count
        
        if len(eligible) < needed:
            print(f"Pool '{pool.name}' ({pool.instrument}, difficulty {pool.min_difficulty}-{pool.max_difficulty}): "
                  f"Requested {needed} more songs but only {len(eligible)} eligible songs available")
            selected = eligible
        else:
            selected = eligible[:needed]
        
        if pool.name not in self.result.pool_assignments:
            self.result.pool_assignments[pool.name] = []
        
        self.result.pool_assignments[pool.name].extend(selected)
        assigned_songs.update(selected)
    
    def _backfill_shortages(self, pools: List[SongPoolConfig]):
        assigned_songs = set()
        for p in pools:
            assigned_songs.update(self.result.pool_assignments.get(p.name, []))
        
        for pool in pools:
            while len(self.result.pool_assignments.get(pool.name, [])) < pool.amount_in_pool:
                found_donor = self._try_steal_one_song(pool, pools, assigned_songs)
                
                if not found_donor:
                    current_count = len(self.result.pool_assignments.get(pool.name, []))
                    raise OptionError(
                        f"Pool '{pool.name}' ({pool.instrument}, difficulty {pool.min_difficulty}-{pool.max_difficulty}): "
                        f"Cannot fulfill request for {pool.amount_in_pool} songs. Only {current_count} songs available after backfilling. "
                        f"Please reduce amount_in_pool, expand difficulty range, or ensure more songs are available."
                    )
    
    def _try_steal_one_song(self, recipient_pool: SongPoolConfig, all_pools: List[SongPoolConfig], 
                            assigned_songs: Set[str]) -> bool:
        for donor_pool in all_pools:
            if donor_pool.name == recipient_pool.name:
                continue
            
            donor_current = len(self.result.pool_assignments.get(donor_pool.name, []))
            if donor_current < donor_pool.amount_in_pool:
                continue
            
            donor_song_hashes = self.result.pool_assignments.get(donor_pool.name, [])
            if not donor_song_hashes:
                continue
            
            for song_hash in donor_song_hashes:
                if not self._song_fits_pool(song_hash, recipient_pool):
                    continue
                
                refill_song = self._find_refill_for_donor(donor_pool, assigned_songs)
                if refill_song is None:
                    continue
                
                self.result.pool_assignments[donor_pool.name].remove(song_hash)
                self.result.pool_assignments[donor_pool.name].append(refill_song)
                assigned_songs.add(refill_song)
                
                if recipient_pool.name not in self.result.pool_assignments:
                    self.result.pool_assignments[recipient_pool.name] = []
                self.result.pool_assignments[recipient_pool.name].append(song_hash)
                
                return True
        
        return False
    
    def _song_fits_pool(self, song_hash: str, pool: SongPoolConfig) -> bool:
        song_data = self.available_songs[song_hash]
        return (pool.instrument in song_data.Difficulties
                and pool.min_difficulty <= song_data.Difficulties[pool.instrument] <= pool.max_difficulty)
    
    def _find_refill_for_donor(self, donor_pool: SongPoolConfig, assigned_songs: Set[str]) -> str:
        exclusion_set = set(self.exclusion_lists.get(donor_pool.name, []))
        
        candidates = [
            song_hash for song_hash, song_data in self.available_songs.items()
            if song_hash not in assigned_songs
            and song_hash not in exclusion_set
            and self._song_fits_pool(song_hash, donor_pool)
        ]
        
        if not candidates:
            return None
        
        return self.random.choice(candidates)


def distribute_songs_to_pools(
    rnd: random.Random,
    song_pools: Dict[str, Dict],
    available_songs: Dict[str, YargExportSongData],
    inclusion_lists: Dict[str, List[str]] = None,
    exclusion_lists: Dict[str, List[str]] = None,
    goal_song: str = None,
    goal_pool: str = None
) -> SongDistributionResult:
    distributor = SongDistributor(rnd, song_pools, available_songs, inclusion_lists, exclusion_lists, goal_song, goal_pool)
    return distributor.distribute()
