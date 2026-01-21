from typing import Dict, List, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass
import random
import logging
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
        self.pool_assignments: Dict[str, List[str]] = {}  # pool_name -> list of song hashes
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.success: bool = True
    
    def add_warning(self, message: str):
        self.warnings.append(message)
        logging.warning(message)
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.success = False
        logging.error(message)


class SongDistributor:
    
    def __init__(self, song_pools: Dict[str, Dict], available_songs: Dict[str, YargExportSongData]):
        self.song_pools = self._parse_pool_configs(song_pools)
        self.available_songs = available_songs
        self.result = SongDistributionResult()
    
    def _parse_pool_configs(self, song_pools: Dict[str, Dict]) -> List[SongPoolConfig]:
        configs = []
        for pool_name, pool_data in song_pools.items():
            configs.append(SongPoolConfig(
                name=pool_name,
                instrument=pool_data["instrument"],
                amount_in_pool=pool_data["amount_in_pool"],
                min_difficulty=pool_data["min_difficulty"],
                max_difficulty=pool_data["max_difficulty"]
            ))
        return configs
    
    def distribute(self) -> SongDistributionResult:
        # Sort all pools by priority (narrow range + high demand first)
        sorted_pools = self._sort_pools_by_priority(self.song_pools)
        
        # Track assigned songs
        assigned_songs: Set[str] = set()  # song titles
        
        # Phase 1: Initial allocation
        for pool in sorted_pools:
            self._assign_songs_to_pool(pool, assigned_songs)
        
        # Phase 2: Backfill for any shortages
        self._backfill_shortages(sorted_pools)
        
        return self.result
    
    def _sort_pools_by_priority(self, pools: List[SongPoolConfig]) -> List[SongPoolConfig]:
        # Filter out disabled pools
        active_pools = [p for p in pools if p.amount_in_pool > 0]
        
        return sorted(
            active_pools,
            key=lambda p: (
                p.max_difficulty - p.min_difficulty,  # Narrower first
                -p.amount_in_pool  # Higher demand first
            )
        )
    
    def _assign_songs_to_pool(
        self,
        pool: SongPoolConfig,
        assigned_songs: Set[str]
    ):
        # Get eligible songs for this pool
        eligible = self._get_eligible_songs(pool, assigned_songs)
        
        # Shuffle for randomness
        random.shuffle(eligible)
        
        # Use the requested amount
        target_count = pool.amount_in_pool
        
        # Check if we have enough songs
        if len(eligible) < target_count:
            self.result.add_warning(
                f"Pool '{pool.name}' ({pool.instrument}, difficulty {pool.min_difficulty}-{pool.max_difficulty}): "
                f"Requested {target_count} songs but only {len(eligible)} eligible songs available"
            )
            selected = eligible
        else:
            selected = eligible[:target_count]
        
        # Assign song hashes to pool
        self.result.pool_assignments[pool.name] = selected
        
        # Mark songs as assigned
        for song_hash in selected:
            assigned_songs.add(song_hash)
    
    def _get_eligible_songs(
        self,
        pool: SongPoolConfig,
        assigned_songs: Set[str]
    ) -> List[str]:
        eligible = []
        
        for song_hash, song_data in self.available_songs.items():
            # Skip if already assigned
            if song_hash in assigned_songs:
                continue
            
            # Check if song has this instrument
            if pool.instrument not in song_data.Difficulties:
                continue
            
            # Check if difficulty is in range
            difficulty = song_data.Difficulties[pool.instrument]
            if not (pool.min_difficulty <= difficulty <= pool.max_difficulty):
                continue
            
            eligible.append(song_hash)
        
        return eligible
    
    def _backfill_shortages(
        self,
        pools: List[SongPoolConfig]
    ):
        for pool in pools:
            current_count = len(self.result.pool_assignments.get(pool.name, []))
            target_count = pool.amount_in_pool
            
            if current_count < target_count:
                shortage = target_count - current_count
                
                # Try to steal from broader pools with excess
                stolen_count = self._steal_from_excess_pools(pool, pools, shortage)
                
                if stolen_count > 0:
                    self.result.add_warning(
                        f"Backfilled {stolen_count} songs for pool '{pool.name}' from other pools"
                    )
                
                # Update current count after stealing
                current_count = len(self.result.pool_assignments.get(pool.name, []))
                remaining_shortage = target_count - current_count
                
                # If still short, raise error
                if remaining_shortage > 0:
                    raise OptionError(
                        f"Pool '{pool.name}' ({pool.instrument}, difficulty {pool.min_difficulty}-{pool.max_difficulty}): "
                        f"Cannot fulfill request for {target_count} songs. Only {current_count} songs available after backfilling. "
                        f"Please reduce amount_in_pool, expand difficulty range, or ensure more songs are available."
                    )
    
    def _steal_from_excess_pools(
        self,
        recipient_pool: SongPoolConfig,
        all_pools: List[SongPoolConfig],
        shortage: int
    ) -> int:
        stolen_count = 0
        
        # Try to steal from broader pools (reverse priority order)
        for donor_pool in reversed(all_pools):
            if donor_pool.name == recipient_pool.name:
                continue
            
            if shortage <= 0:
                break
            
            donor_song_hashes = self.result.pool_assignments.get(donor_pool.name, [])
            if not donor_song_hashes:
                continue
            
            # Find songs that fit recipient's criteria
            stealable = [
                song_hash for song_hash in donor_song_hashes
                if (recipient_pool.instrument in self.available_songs[song_hash].Difficulties and
                    recipient_pool.min_difficulty <= 
                    self.available_songs[song_hash].Difficulties[recipient_pool.instrument] <= 
                    recipient_pool.max_difficulty)
            ]
            
            if not stealable:
                continue
            
            # Check if donor has excess
            donor_target = donor_pool.amount_in_pool
            donor_excess = len(donor_song_hashes) - donor_target
            
            if donor_excess > 0:
                # Steal what we can
                steal_count = min(shortage, donor_excess, len(stealable))
                stolen = random.sample(stealable, steal_count)
                
                # Transfer songs
                for song_hash in stolen:
                    self.result.pool_assignments[donor_pool.name].remove(song_hash)
                    if recipient_pool.name not in self.result.pool_assignments:
                        self.result.pool_assignments[recipient_pool.name] = []
                    self.result.pool_assignments[recipient_pool.name].append(song_hash)
                
                stolen_count += steal_count
                shortage -= steal_count
        
        return stolen_count
    
    def _emergency_allocation(
        self,
        pool: SongPoolConfig,
        assigned_songs: Set[str],
        shortage: int
    ) -> int:
        # Find any unassigned song hashes with this instrument
        emergency_eligible = [
            song_hash for song_hash, song_data in self.available_songs.items()
            if (song_hash not in assigned_songs and
                pool.instrument in song_data.Difficulties)
        ]
        
        if not emergency_eligible:
            return 0
        
        # Take what we can get
        emergency_count = min(shortage, len(emergency_eligible))
        emergency_hashes = random.sample(emergency_eligible, emergency_count)
        
        # Add to pool
        if pool.name not in self.result.pool_assignments:
            self.result.pool_assignments[pool.name] = []
        self.result.pool_assignments[pool.name].extend(emergency_hashes)
        
        # Mark as assigned
        for song_hash in emergency_hashes:
            assigned_songs.add(song_hash)
        
        return emergency_count
    
    def validate_feasibility(self) -> Tuple[bool, List[str]]:
        errors = []
        pools_by_instrument = defaultdict(list)
        
        for pool in self.song_pools:
            if pool.amount_in_pool > 0:  # Only check active pools
                pools_by_instrument[pool.instrument].append(pool)
        
        for instrument, pools in pools_by_instrument.items():
            # Count available songs by difficulty for this instrument
            songs_by_diff = defaultdict(int)
            for song_hash, song_data in self.available_songs.items():
                if instrument in song_data.Difficulties:
                    diff = song_data.Difficulties[instrument]
                    songs_by_diff[diff] += 1
            
            # Check each difficulty tier
            for diff in range(0, 20):  # Support wide range
                # Which pools need songs at this difficulty?
                demanding_pools = [
                    p for p in pools
                    if p.min_difficulty <= diff <= p.max_difficulty
                ]
                
                if not demanding_pools:
                    continue
                
                total_demand = sum(p.amount_in_pool for p in demanding_pools)
                available = songs_by_diff[diff]
                
                if total_demand > available:
                    errors.append(
                        f"Instrument '{instrument}', Difficulty {diff}: "
                        f"Pools demand {total_demand} songs but only {available} available"
                    )
        
        return len(errors) == 0, errors


def split_pools_by_instrument(song_pools: Dict[str, Dict]) -> Dict[str, Dict[str, Dict]]:
    """
    Split song pools into separate dictionaries grouped by instrument.
    Useful when instrument_shares_songs is True.
    
    Args:
        song_pools: Dictionary of all pool configurations
    
    Returns:
        Dictionary mapping instrument name to pools dict for that instrument
    """
    pools_by_instrument = defaultdict(dict)
    
    for pool_name, pool_data in song_pools.items():
        instrument = pool_data["instrument"]
        pools_by_instrument[instrument][pool_name] = pool_data
    
    return dict(pools_by_instrument)


def distribute_songs_to_pools(
    song_pools: Dict[str, Dict],
    available_songs: Dict[str, YargExportSongData]
) -> SongDistributionResult:
    """
    Distribute songs to pools with intelligent allocation and backfilling.
    
    Args:
        song_pools: Dictionary of pool configurations (from YAML options)
        available_songs: Dictionary mapping song hash -> YargExportSongData
    
    Returns:
        SongDistributionResult containing assignments (pool_name -> list of song hashes), warnings, and errors
    """
    distributor = SongDistributor(song_pools, available_songs)
    
    # Validate before attempting distribution
    #is_feasible, errors = distributor.validate_feasibility()
    #if not is_feasible:
    #    error_message = "Song pool configuration is not feasible:\n" + "\n".join(errors)
    #    raise OptionError(error_message)
    
    return distributor.distribute()
