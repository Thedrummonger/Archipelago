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


class SongDistributor:
    def __init__(self, rnd: random.Random):
        self.random = rnd
        self.assigned_songs: Set[str] = set()
        self.assigned_song_instruments: Dict[str, Set[str]] = defaultdict(set)
        self.pool_assignments: Dict[str, List[str]] = {}
        self.goal_placed = False
        
        self.available_songs: Dict[str, YargExportSongData] = {}
        self.song_pools: Dict[str, Dict] = {}
        self.reuse_songs_across_instruments = False
        self.inclusion_lists: Dict[str, List[str]] = {}
        self.exclusion_lists: Dict[str, List[str]] = {}
        self.goal_song: str = None
        self.goal_pool: str = None
    
    def with_available_songs(self, available_songs: Dict[str, YargExportSongData]) -> 'SongDistributor':
        self.available_songs = available_songs
        return self
    
    def with_pools(self, song_pools: Dict[str, Dict]) -> 'SongDistributor':
        self.song_pools = song_pools
        return self
    
    def with_reuse_songs(self, reuse: bool) -> 'SongDistributor':
        self.reuse_songs_across_instruments = reuse
        return self
    
    def with_inclusion_lists(self, inclusion_lists: Dict[str, List[str]]) -> 'SongDistributor':
        self.inclusion_lists = inclusion_lists
        return self
    
    def with_exclusion_lists(self, exclusion_lists: Dict[str, List[str]]) -> 'SongDistributor':
        self.exclusion_lists = exclusion_lists
        return self
    
    def with_goal_song(self, goal_song: str, goal_pool: str = None) -> 'SongDistributor':
        self.goal_song = goal_song
        self.goal_pool = goal_pool
        return self
    
    def distribute(self) -> SongDistributionResult:
        pools = self._parse_pools(self.song_pools)
        
        self._process_goal_song(pools)
        
        sorted_pools = self._sort_pools(pools)
        for pool in sorted_pools:
            self._process_inclusion_list(pool)
        
        for pool in sorted_pools:
            self._assign_songs_to_pool(pool)
        
        self._backfill_shortages(sorted_pools)
        
        if self.goal_song and not self.goal_placed:
            raise OptionError(f"Could not place goal song '{self.goal_song}' in any pool")
        
        result = SongDistributionResult()
        result.pool_assignments = self.pool_assignments
        return result
    
    def _parse_pools(self, pools_dict: Dict[str, Dict]) -> List[SongPoolConfig]:
        return [SongPoolConfig(
            name=name,
            instrument=data["instrument"],
            amount_in_pool=data["amount_in_pool"],
            min_difficulty=data["min_difficulty"],
            max_difficulty=data["max_difficulty"]
        ) for name, data in pools_dict.items()]
    
    def _sort_pools(self, pools: List[SongPoolConfig]) -> List[SongPoolConfig]:
        return sorted(
            [p for p in pools if p.amount_in_pool > 0],
            key=lambda p: (p.max_difficulty - p.min_difficulty, -p.amount_in_pool)
        )
    
    def _song_would_create_duplicate_instrument(self, song_hash: str, pool: SongPoolConfig) -> bool:
        """Hard check: We can never have a song appear in more than one pool with the same instrument."""
        return pool.instrument in self.assigned_song_instruments[song_hash]
    
    def _song_already_used(self, song_hash: str, pool: SongPoolConfig) -> bool:
        if self.reuse_songs_across_instruments:
            return False  # Can reuse across different instruments
        else:
            return song_hash in self.assigned_songs  # Cannot reuse at all
    
    def _process_goal_song(self, pools: List[SongPoolConfig]):
        if not self.goal_song or self.goal_placed:
            return
        
        if self.goal_song not in self.available_songs:
            raise OptionError(f"Goal song '{self.goal_song}' is not in the available songs")
        
        song_data = self.available_songs[self.goal_song]
        
        if self.goal_pool:
            target_pool = next((p for p in pools if p.name == self.goal_pool), None)
            if not target_pool:
                raise OptionError(f"Goal pool '{self.goal_pool}' does not exist in song pools")
            
            if target_pool.instrument not in song_data.Difficulties:
                raise OptionError(
                    f"Goal song '{self.goal_song}' does not have instrument '{target_pool.instrument}' "
                    f"required by goal pool '{self.goal_pool}'"
                )
            
            self._assign_song_to_pool_internal(self.goal_song, target_pool)
            self.goal_placed = True
        else:
            shuffled_pools = pools.copy()
            self.random.shuffle(shuffled_pools)
            
            for pool in shuffled_pools:
                if (pool.instrument in song_data.Difficulties 
                    and not self._song_would_create_duplicate_instrument(self.goal_song, pool)):
                    self._assign_song_to_pool_internal(self.goal_song, pool)
                    self.goal_placed = True
                    return
    
    def _process_inclusion_list(self, pool: SongPoolConfig):
        if pool.name not in self.inclusion_lists:
            return
        
        included_songs = list(set(self.inclusion_lists[pool.name]))
        
        current_count = len(self.pool_assignments.get(pool.name, []))
        songs_to_include = min(len(included_songs), pool.amount_in_pool - current_count)
        
        for song_hash in included_songs[:songs_to_include]:
            if song_hash not in self.available_songs:
                raise OptionError(f"Inclusion list for pool '{pool.name}' contains unknown song hash: {song_hash}")
            
            song_data = self.available_songs[song_hash]
            
            if pool.instrument not in song_data.Difficulties:
                raise OptionError(
                    f"Inclusion list for pool '{pool.name}' contains song '{song_hash}' "
                    f"which does not have instrument '{pool.instrument}'"
                )
            
            if self._song_would_create_duplicate_instrument(song_hash, pool):
                continue
            
            self._assign_song_to_pool_internal(song_hash, pool)
    
    def _assign_songs_to_pool(self, pool: SongPoolConfig):
        exclusion_set = set(self.exclusion_lists.get(pool.name, []))
        
        eligible = [
            song_hash for song_hash in self.available_songs.keys()
            if not self._song_already_used(song_hash, pool)
            and song_hash not in exclusion_set
            and self._song_fits_pool(song_hash, pool)
        ]
        
        self.random.shuffle(eligible)
        
        current_count = len(self.pool_assignments.get(pool.name, []))
        needed = pool.amount_in_pool - current_count
        
        if len(eligible) < needed:
            print(f"Pool '{pool.name}' ({pool.instrument}, difficulty {pool.min_difficulty}-{pool.max_difficulty}): "
                  f"Requested {needed} more songs but only {len(eligible)} eligible songs available")
            selected = eligible
        else:
            selected = eligible[:needed]
        
        for song_hash in selected:
            self._assign_song_to_pool_internal(song_hash, pool)
    
    def _backfill_shortages(self, pools: List[SongPoolConfig]):
        for pool in pools:
            while len(self.pool_assignments.get(pool.name, [])) < pool.amount_in_pool:
                found_donor = self._try_steal_one_song(pool, pools)
                
                if not found_donor:
                    current_count = len(self.pool_assignments.get(pool.name, []))
                    raise OptionError(
                        f"Pool '{pool.name}' ({pool.instrument}, difficulty {pool.min_difficulty}-{pool.max_difficulty}): "
                        f"Cannot fulfill request for {pool.amount_in_pool} songs. Only {current_count} songs available after backfilling. "
                        f"Please reduce amount_in_pool, expand difficulty range, or ensure more songs are available."
                    )
    
    def _try_steal_one_song(self, recipient_pool: SongPoolConfig, all_pools: List[SongPoolConfig]) -> bool:
        for donor_pool in all_pools:
            if donor_pool.name == recipient_pool.name:
                continue
            
            donor_current = len(self.pool_assignments.get(donor_pool.name, []))
            if donor_current < donor_pool.amount_in_pool:
                continue
            
            donor_song_hashes = self.pool_assignments.get(donor_pool.name, [])
            if not donor_song_hashes:
                continue
            
            for song_hash in donor_song_hashes:
                if not self._song_fits_pool(song_hash, recipient_pool):
                    continue
                
                # If we are stealing from a song with the same instrument, we know we are safe to move the song
                # But if its a differnt instrument, we have to check that it does not already exist in a pool with this same instrument
                if donor_pool.instrument != recipient_pool.instrument and self._song_would_create_duplicate_instrument(song_hash, recipient_pool):
                    continue
                
                refill_song = self._find_refill_for_donor(donor_pool)
                if refill_song is None:
                    continue
                
                self.pool_assignments[donor_pool.name].remove(song_hash)
                self.pool_assignments[donor_pool.name].append(refill_song)
                self.assigned_songs.add(refill_song)
                
                if recipient_pool.name not in self.pool_assignments:
                    self.pool_assignments[recipient_pool.name] = []
                self.pool_assignments[recipient_pool.name].append(song_hash)
                
                return True
        
        return False
    
    def _song_fits_pool(self, song_hash: str, pool: SongPoolConfig) -> bool:
        song_data = self.available_songs[song_hash]
        return (pool.instrument in song_data.Difficulties
                and pool.min_difficulty <= song_data.Difficulties[pool.instrument] <= pool.max_difficulty)
    
    def _find_refill_for_donor(self, donor_pool: SongPoolConfig) -> str:
        exclusion_set = set(self.exclusion_lists.get(donor_pool.name, []))
        
        candidates = [
            song_hash for song_hash, song_data in self.available_songs.items()
            if not self._song_already_used(song_hash, donor_pool)
            and song_hash not in exclusion_set
            and self._song_fits_pool(song_hash, donor_pool)
        ]
        
        if not candidates:
            return None
        
        return self.random.choice(candidates)
    
    def _assign_song_to_pool_internal(self, song_hash: str, pool: SongPoolConfig):
        if pool.name not in self.pool_assignments:
            self.pool_assignments[pool.name] = []
        
        self.pool_assignments[pool.name].append(song_hash)
        self.assigned_songs.add(song_hash)
        self.assigned_song_instruments[song_hash].add(pool.instrument)