from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from math import ceil
from BaseClasses import CollectionState, Region, Tutorial, MultiWorld
from worlds.AutoWorld import WebWorld, World
from .Options import YargOptions, VALID_INSTRUMENTS
from .Locations import YargLocation
from .Items import WeightedItem, StaticItems, pick_weighted_item, YargItem
from Options import OptionError
from .data_register import YargAPImportData, ImportAndCreateItemLocationData, nice_name, YargSongData
from .yarg_song_data_helper import YargExportSongData, deserialize_song_data, loadDefaultSongList
from .song_distribution import SongDistributor

class yargWebWorld(WebWorld):
    theme = "partyTime"
    
    setup_en = Tutorial(
        tutorial_name="Start Guide",
        description="A guide to playing Yarg.",
        language="English",
        file_name="guide_en.md",
        link="guide/en",
        authors=["Thedrummonger"],
    )
    
    tutorials = [setup_en]

class AssignedSongData:
    def __init__(self, hash: str, pool: str):
        self.SongHash: str = hash
        self.SongPool: str = pool
        self.ExtraCheck: bool = False
        self.Starting: bool = False
        self.Goal: bool = False
        self.SongPack: str = None

    def GetData(self, item_location_data: YargAPImportData) -> YargSongData:
        return item_location_data.hash_to_song_data[self.SongHash]
    
    def GetPool(self, Pools: dict[str, dict[str, Any]]) -> dict[str, Any]:
        return Pools[self.SongPool]
    
    def GetInstrument(self, Pools: dict[str, dict[str, Any]]) -> str:
        return self.GetPool(Pools)["instrument"]
    
    def GetInstrumentItemName(self, Pools: dict[str, dict[str, Any]]) -> str:
        return nice_name(self.GetInstrument(Pools))
    
    def GetStandardCheck(self, Pools: dict[str, dict[str, Any]], item_location_data: YargAPImportData) -> str:
        return item_location_data.hash_to_song_data[self.SongHash].main_locations[self.GetInstrument(Pools)]
    
    def GetExtraCheck(self, Pools: dict[str, dict[str, Any]], item_location_data: YargAPImportData) -> str:
        return item_location_data.hash_to_song_data[self.SongHash].extra_locations[self.GetInstrument(Pools)]
    
    def GetCompletionCheck(self, Pools: dict[str, dict[str, Any]], item_location_data: YargAPImportData) -> str:
        return item_location_data.hash_to_song_data[self.SongHash].completion_locations[self.GetInstrument(Pools)]
    
    def GetUnlockSongItem(self, Pools: dict[str, dict[str, Any]], item_location_data: YargAPImportData) -> str:
        return self.SongPack if self.SongPack else item_location_data.hash_to_song_data[self.SongHash].unlock_items[self.GetInstrument(Pools)]
    
class yargWorld(World):
    """
    YARG (a.k.a. Yet Another Rhythm Game) is a free, open-source, plastic guitar game still in development.
    It supports guitar (five fret), drums (plastic or e-kit), vocals, pro-guitar, and more!
    """
    game = "YAYARG"
    required_client_version = (0, 6, 1)
    web = yargWebWorld()
    options_dataclass = YargOptions
    options: YargOptions

    item_location_data: YargAPImportData = ImportAndCreateItemLocationData()
    location_name_to_id = item_location_data.location_name_to_id
    item_name_to_id = item_location_data.item_name_to_id
    
    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)

        self.AssignedSongs: list[AssignedSongData] = []
        self.starting_instrument: str = None
        self.startingSongs: list[AssignedSongData] = []
        self.SongWithExtraChecks: list[AssignedSongData] = []
        self.SongsWithUnlockItems: list[AssignedSongData] = []
        self.SongsWithItemLocations: list[AssignedSongData] = []
        self.GoalSong: AssignedSongData = None

        self.fillerItems = []

        self.famePointsNeeded: int = 0
        self.SongCompletionsNeeded: int = 0

    def generate_early(self) -> None:

        self.CreateFillerItems()

        for _, pool in self.options.song_pools.value.items():
            base = int(pool.get("amount_in_pool", 0))
            variance = int(pool.get("random_variance", 0))

            if variance > 0:
                low = max(0, base - variance)
                high = base + variance
                pool["amount_in_pool"] = self.random.randint(low, high)


        SerializedSongList = self.options.songList.value
        print(SerializedSongList)
        if (SerializedSongList == 'None' or SerializedSongList == '' or SerializedSongList == None):
            user_songs = loadDefaultSongList()
        else:
            user_songs = deserialize_song_data(SerializedSongList)

        if not user_songs:
            raise OptionError(f'Failed to read song data for user {self.player_name}')

        for hash, data in user_songs.items():
            if hash not in self.item_location_data.hash_to_song_data:
                raise OptionError(f"Fatal Error, Player {self.player_name} song {data.Title} was not added to master data list. Ensure the SongList Hash is not a weighted option.")

        goalSongPlando = self.options.goal_song_plando.value if self.options.goal_song_plando.value is not None else None
        goalPoolPlando = self.options.goal_pool_plando.value if self.options.goal_pool_plando.value is not None else None

        if goalPoolPlando and goalPoolPlando in self.options.song_pools.value and self.options.song_pools.value[goalPoolPlando]["amount_in_pool"] <= 0:
            self.options.song_pools.value[goalPoolPlando]["amount_in_pool"] = 1

        inclusion_list, exclusion_list = self.build_song_pool_inclusion_exclusion_dicts()

        distributor = (SongDistributor(self.random)
            .with_available_songs(user_songs)
            .with_pools(self.options.song_pools.value)
            .with_reuse_songs(self.options.reuse_songs.value == 1)
            .with_inclusion_lists(inclusion_list)
            .with_exclusion_lists(exclusion_list)
            .with_goal_song(goalSongPlando, goalPoolPlando)
        )
        
        result = distributor.distribute()
        all_assignments = result.pool_assignments

        if self.options.max_setlist_time.value > 0:
            self.trim_setlist_to_max_time(result.pool_assignments, user_songs, self.options.max_setlist_time.value, goalSongPlando)
    
        # A list of AssignedSongData, each entry represents a single song, containing it's location unlock items and song pool
        for pool, assignedHashes in all_assignments.items():
            for hash in assignedHashes:
                AssignmentData = AssignedSongData(hash, pool)
                self.AssignedSongs.append(AssignmentData)

        #if we plando our goal song on anything, set it before starting songs so instrument rando can take it into account
        if goalSongPlando or goalPoolPlando:
            goal_candidates = self.AssignedSongs.copy()

            if goalSongPlando:
                goal_candidates = [song for song in goal_candidates if song.SongHash == goalSongPlando]

            if goalPoolPlando:
                goal_candidates = [song for song in goal_candidates if song.SongPool == goalPoolPlando]

            if not goal_candidates:
                error_msg = "Goal song not found"
                if goalSongPlando and goalPoolPlando:
                    error_msg = f"Goal song '{goalSongPlando}' was not assigned to pool '{goalPoolPlando}'"
                elif goalSongPlando:
                    error_msg = f"Goal song '{goalSongPlando}' was not assigned to any pool"
                elif goalPoolPlando:
                    error_msg = f"No songs found in pool '{goalPoolPlando}'"
                raise OptionError(error_msg)
            self.GoalSong = self.random.choice(goal_candidates)
            self.GoalSong.Goal = True

        # If we are shuffling instruments, pick a starting instrument that will allow us enough songs to fill 
        # our starting songs 
        if self.options.instrument_shuffle.value == 1:
            distinct_instruments = {pool_data["instrument"] for pool_data in self.options.song_pools.value.values()}
            songs_per_instrument = {}
            for instrument in distinct_instruments:
                count = len([song for song in self.AssignedSongs if not song.Goal and song.GetInstrument(self.options.song_pools.value) == instrument])
                songs_per_instrument[instrument] = count
            
            valid_starting_instruments = [
                instrument 
                for instrument, count in songs_per_instrument.items()
                if count >= self.options.starting_songs.value
            ]
            if not valid_starting_instruments:
                raise OptionError(
                    f"No instrument has enough songs to satisfy starting_songs requirement ({self.options.starting_songs.value}). "
                    f"Available songs per instrument: {songs_per_instrument}. "
                    f"Please reduce starting_songs or increase songs in your pools."
                )
            self.starting_instrument = self.random.choice(valid_starting_instruments)

        # Select starting songs
        eligible_starting_songs = [song for song in self.AssignedSongs if not song.Goal]
        if self.starting_instrument:
            eligible_starting_songs = [song for song in eligible_starting_songs if self.options.song_pools.value[song.SongPool]["instrument"] == self.starting_instrument]

        if self.options.starting_songs.value > len(eligible_starting_songs):
                raise OptionError(f"No enough eligable starting songs {len(eligible_starting_songs)} to satisfy starting song requirement {self.options.starting_songs.value}")

        self.startingSongs = self.random.sample(eligible_starting_songs, self.options.starting_songs.value)
        for song in self.startingSongs:
            song.Starting = True

        if not self.GoalSong:
            goal_candidates = [song for song in self.AssignedSongs if not song.Starting]
            if not goal_candidates:
                raise OptionError("No valid goal songs available")
            self.GoalSong = self.random.choice(goal_candidates)
            self.GoalSong.Goal = True
        
        # Technically Goal Song can have an unlock item, but we handle it differently
        self.SongsWithUnlockItems = [song for song in self.AssignedSongs if not song.Starting and not song.Goal]
        self.SongsWithItemLocations = [song for song in self.AssignedSongs if not song.Goal]

        extra_check_amount = ceil(len(self.SongsWithItemLocations) * self.options.song_check_extra.value / 100)
        self.SongWithExtraChecks = self.random.sample(self.SongsWithItemLocations, extra_check_amount)
        for song in self.SongWithExtraChecks:
            song.ExtraCheck = True

        if self.options.song_pack_percentage.value > 0:
            song_pack_amount = ceil(len(self.SongsWithUnlockItems) * self.options.song_pack_percentage.value / 100)
            SongsInPacks = self.random.sample(self.SongsWithUnlockItems, song_pack_amount)
            SongPacksNeeded = ceil(len(SongsInPacks) / self.options.song_pack_size.value) 
            SongPackItems = [self.item_location_data.song_pack_id_to_name[pack] for pack in range(1, SongPacksNeeded + 1)]
            pack_pool = [pack for pack in SongPackItems for _ in range(self.options.song_pack_size.value)]
            self.random.shuffle(pack_pool)
            for i, song in enumerate(SongsInPacks):
                song.SongPack = pack_pool[i]

        self.SongCompletionsNeeded = ceil(len(self.SongsWithItemLocations) * (self.options.setlist_needed.value / 100))
        self.famePointsNeeded = ceil(self.options.fame_point_amount.value * (self.options.fame_point_needed.value / 100))
        

    def create_item(self, name: str) -> YargItem:
        classification = self.item_location_data.item_name_to_classification[name]
        id = self.item_location_data.item_name_to_id[name]
        return YargItem(name, classification, id, self.player)
    
    def create_items(self) -> None:

        # Add starting songs to precollected
        startingSongItems: set[str] = set()
        for entry in self.startingSongs:
            startingSongItems.add(entry.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data))
        for item in startingSongItems:
            self.multiworld.push_precollected(self.create_item(item))
        
        # Add Fame Points to Pool
        fame_points_in_pool = self.options.fame_point_amount.value if self.options.fame_point_needed.value > 0 else 0
        if fame_points_in_pool > 0:
            self.multiworld.itempool += [self.create_item(StaticItems.FamePoint.nice_name) for _ in range(fame_points_in_pool)]

        # Add Unlock Items for all songs that need them
        unlockItems: set[str] = set()
        for entry in self.SongsWithUnlockItems:
            unlockItems.add(entry.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data))
        self.multiworld.itempool += [self.create_item(song) for song in unlockItems]

        # Add Instrument Unlock Items
        instrumentItems: set[str] = set()
        if self.starting_instrument:
            for entry in self.AssignedSongs:
                instrument = entry.GetInstrument(self.options.song_pools.value)
                instName = entry.GetInstrumentItemName(self.options.song_pools.value)
                if self.starting_instrument != instrument: # Add it to the pool if it's not our starting instrument
                    instrumentItems.add(instName)
            self.multiworld.push_precollected(self.create_item(nice_name(self.starting_instrument)))
            self.multiworld.itempool += [self.create_item(inst) for inst in instrumentItems]
        else: # We push all as precollected if we don't shuffle them
            for entry in VALID_INSTRUMENTS:
                self.multiworld.push_precollected(self.create_item(nice_name(entry)))

        goal_unlock = self.GoalSong.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data)
        if self.options.goal_song_item_needed.value == 1:
            self.multiworld.itempool.append(self.create_item(goal_unlock))
        else:
            self.multiworld.push_precollected(self.create_item(goal_unlock))
        
        totalChecks = 0
        for entry in self.SongsWithItemLocations:
            totalChecks += 1
            if entry.ExtraCheck:
                totalChecks += 1
        
        totalItems = fame_points_in_pool + len(unlockItems) + len(instrumentItems) + self.options.goal_song_item_needed.value

        if totalItems < totalChecks:
            items_to_add = totalChecks - totalItems
            extra_unlocks = ceil(len(unlockItems) * self.options.extra_song_unlock.value / 100)
            extra_unlocks = min(extra_unlocks, items_to_add)
            if extra_unlocks > 0:
                chosen = self.random.sample(list(unlockItems), extra_unlocks)
                self.multiworld.itempool += [self.create_item(name) for name in chosen]
            items_to_add = items_to_add - extra_unlocks
            if items_to_add > 0:
                self.multiworld.itempool += [self.create_item(self.get_filler_item_name()) for _ in range(items_to_add)]
        elif totalItems > totalChecks:
            raise OptionError(f"Not enough locations {totalChecks} to place all items {totalItems}. Reduce the number of items or increase the number of song checks.")
        
                
    def create_regions(self) -> None:
        # Create the menu region. Only one we need
        self.multiworld.regions.append(Region("Menu", self.player, self.multiworld))
        menuRegion = self.multiworld.get_region("Menu", self.player)
        allLocations: Dict[str, int] = {}
        CompletionChecks: list[str] = []
        for entry in self.SongsWithItemLocations:
            standardCheck = entry.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
            allLocations[standardCheck] = self.location_name_to_id[standardCheck]
            if entry.ExtraCheck:
                ExtraCheck = entry.GetExtraCheck(self.options.song_pools.value, self.item_location_data)
                allLocations[ExtraCheck] = self.location_name_to_id[ExtraCheck]
            if self.options.setlist_needed.value > 0:
                CompletionCheck = entry.GetCompletionCheck(self.options.song_pools.value, self.item_location_data)
                allLocations[CompletionCheck] = self.location_name_to_id[CompletionCheck]
                CompletionChecks.append(CompletionCheck)
        GoalSongLocation = self.GoalSong.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
        allLocations[GoalSongLocation] = self.location_name_to_id[GoalSongLocation]

        menuRegion.add_locations(allLocations, YargLocation)

        for check in CompletionChecks:
            self.multiworld.get_location(check, self.player).place_locked_item(self.create_item(StaticItems.SongCompletion.nice_name))
        
        self.multiworld.get_location(GoalSongLocation, self.player).place_locked_item(self.create_item(StaticItems.Victory.nice_name))
        
    def set_rules(self) -> None:
        for entry in self.SongsWithItemLocations:
            unlockitem = entry.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data)
            instrument = entry.GetInstrumentItemName(self.options.song_pools.value)

            standardCheck = entry.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
            standardLoc = self.multiworld.get_location(standardCheck, self.player)
            standardLoc.access_rule = lambda state, I=instrument, P=unlockitem: state.has(I, self.player) and state.has(P, self.player)

            if entry.ExtraCheck:
                ExtraCheck = entry.GetExtraCheck(self.options.song_pools.value, self.item_location_data)
                ExtraLoc = self.multiworld.get_location(ExtraCheck, self.player)
                ExtraLoc.access_rule = lambda state, I=instrument, P=unlockitem: state.has(I, self.player) and state.has(P, self.player)

            if self.options.setlist_needed.value > 0:
                CompletionCheck = entry.GetCompletionCheck(self.options.song_pools.value, self.item_location_data)
                CompletionLoc = self.multiworld.get_location(CompletionCheck, self.player)
                CompletionLoc.access_rule = lambda state, I=instrument, P=unlockitem: state.has(I, self.player) and state.has(P, self.player)

        # Goal song access rule
        goal_instrument = self.GoalSong.GetInstrumentItemName(self.options.song_pools.value)
        goal_unlockitem = self.GoalSong.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data)
        GoalSongCheck = self.GoalSong.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
        GoalSongLocation = self.multiworld.get_location(GoalSongCheck, self.player)
        GoalSongLocation.access_rule = lambda state, I=goal_instrument, P=goal_unlockitem: self.can_complete_goal(state, I, P)
        self.multiworld.completion_condition[self.player] = lambda state: state.has(StaticItems.Victory.nice_name, self.player)

    def can_complete_goal(self, state: CollectionState, instrument: str, unlockItem: str) -> bool:
        SongLocationUnlocked = state.has(instrument, self.player) and state.has(unlockItem, self.player)
        MetFameGoal = self.famePointsNeeded == 0 or state.has(StaticItems.FamePoint.nice_name, self.player, self.famePointsNeeded)
        MetSetlistGoal = self.SongCompletionsNeeded == 0 or state.has(StaticItems.SongCompletion.nice_name, self.player, self.SongCompletionsNeeded)
        return SongLocationUnlocked and MetFameGoal and MetSetlistGoal
            
    def get_filler_item_name(self) -> str:
        if not self.fillerItems:
            return StaticItems.Nothing.nice_name
        return pick_weighted_item(self.random, self.fillerItems).name
    
    def fill_slot_data(self) -> Dict[str, Any]:
        # dict[song_hash, dict[pool_name, tuple[main_loc_id, extra_loc_id, completion_loc_id, unlock_item_id]]]
        song_data: dict[str, dict[str, tuple[int, int, int, int]]] = defaultdict(dict)

        for entry in self.SongsWithItemLocations:
            mainLocation = entry.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
            ExtraLocation = entry.GetExtraCheck(self.options.song_pools.value, self.item_location_data)
            completionLocation = entry.GetCompletionCheck(self.options.song_pools.value, self.item_location_data)
            unlockItem = entry.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data)

            mainLocationID = self.location_name_to_id[mainLocation]
            extraLocationID = self.location_name_to_id[ExtraLocation] if entry.ExtraCheck else -1
            completionLocationID = self.location_name_to_id[completionLocation] if self.options.setlist_needed.value > 0 else -1
            unlockItemID = self.item_name_to_id[unlockItem]

            song_data[entry.SongHash][entry.SongPool] = (mainLocationID, extraLocationID, completionLocationID, unlockItemID)

        GoalLocation = self.GoalSong.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
        GoalLocationID = self.location_name_to_id[GoalLocation]
        unlockItem = self.GoalSong.GetUnlockSongItem(self.options.song_pools.value, self.item_location_data)
        unlockItemID = self.item_name_to_id[unlockItem]
        # string, string, long, long
        goal_data = (self.GoalSong.SongHash, self.GoalSong.SongPool, GoalLocationID, unlockItemID)

        return {
            "fame_points_for_goal": self.famePointsNeeded,
            "setlist_needed_for_goal": self.SongCompletionsNeeded,
            "goal_data": goal_data,
            "death_link": self.options.death_link.value,
            "energy_link": self.options.energy_link.value,
            "pools": self.options.song_pools.value,
            "song_data": dict(song_data),
            "apworld_version": self.item_location_data.manifest["world_version"]
        }
    
    def extend_hint_information(self, hint_data: Dict[int, Dict[int, str]]) -> None:
        song_pack_hint_data = {}
        for entry in self.SongsWithItemLocations:
            if not entry.SongPack:
                continue
            standardCheck = entry.GetStandardCheck(self.options.song_pools.value, self.item_location_data)
            standardCheckID = self.location_name_to_id[standardCheck]
            song_pack_hint_data[standardCheckID] = entry.SongPack
            if entry.ExtraCheck:
                ExtraCheck = entry.GetExtraCheck(self.options.song_pools.value, self.item_location_data)
                ExtraCheckID = self.location_name_to_id[ExtraCheck]
                song_pack_hint_data[ExtraCheckID] = entry.SongPack
                
        hint_data.update({self.player: song_pack_hint_data})
                
    
    def CreateFillerItems(self):
        if self.options.star_power.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.StarPower.nice_name, self.options.star_power.value))
        if self.options.swap_song_random.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.SwapRandom.nice_name, self.options.swap_song_random.value))
        if self.options.swap_song_choice.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.SwapPick.nice_name, self.options.swap_song_choice.value))
        if self.options.lower_difficulty.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.LowerDifficulty.nice_name, self.options.lower_difficulty.value))
        if self.options.restart_trap.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.TrapRestart.nice_name, self.options.restart_trap.value))
        if self.options.rock_meter_trap.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.TrapRockMeter.nice_name, self.options.rock_meter_trap.value))
        if self.options.fail_prevention.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.FailPrevention.nice_name, self.options.fail_prevention.value))
        if self.options.nothing_item.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.Nothing.nice_name, self.options.nothing_item.value))
        if not self.fillerItems:
            self.fillerItems.append(WeightedItem(StaticItems.Nothing.nice_name, 1))

    def build_song_pool_inclusion_exclusion_dicts(self) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    
        pool_inclusions: Dict[str, List[str]] = defaultdict(list)
        pool_exclusions: Dict[str, List[str]] = defaultdict(list)

        pool_names = self.options.song_pools.value.keys()

        for song_hash in self.options.song_exclusion_list.value:
            for pool_name in pool_names:
                pool_exclusions[pool_name].append(song_hash)

        for song_hash, pools in self.options.exclusions_per_pool.value.items():
            for pool_name in pools:
                pool_exclusions[pool_name].append(song_hash)

        for song_hash, pools in self.options.inclusions_per_pool.value.items():
            for pool_name in pools:
                pool_inclusions[pool_name].append(song_hash)

        return dict(pool_inclusions), dict(pool_exclusions)
    
    def trim_setlist_to_max_time(self, pool_assignments: Dict[str, List[str]], user_songs: Dict[str, "YargExportSongData"], max_time: float, goalPlando: Optional[str]) -> None:

        # Snapshot original pool sizes, we want to avoid removing more than like 50% of of agiven pool
        original_pool_sizes = {pool: len(songs) for pool, songs in pool_assignments.items()}
        removed_per_pool = {pool: 0 for pool in pool_assignments.keys()}

        total_time = 0.0
        song_count = 0
        for songs in pool_assignments.values():
            song_count += len(songs)
            for song in songs:
                total_time += float(user_songs[song].Time)

        minimumNeededSongs = self.options.starting_songs + 1  # starting + goal

        def pool_can_remove(pool: str) -> bool:
            orig = original_pool_sizes.get(pool, 0)
            if orig <= 0:
                return False
            return removed_per_pool[pool] < (orig / 2.0)

        while total_time > max_time and song_count > minimumNeededSongs:
            over = total_time - max_time

            best_fit: Optional[Tuple[float, str, str]] = None   # (time, song, pool)
            longest: Optional[Tuple[float, str, str]] = None    # (time, song, pool)

            for pool, songs in pool_assignments.items():
                if not pool_can_remove(pool):
                    continue

                for song in songs:
                    if goalPlando and song == goalPlando:
                        continue

                    t = float(user_songs[song].Time)

                    if longest is None or t > longest[0]:
                        longest = (t, song, pool)

                    if t >= over:
                        if best_fit is None or t < best_fit[0]:
                            best_fit = (t, song, pool)

            if longest is None:
                break

            t_remove, song_remove, pool_remove = best_fit if best_fit is not None else longest

            pool_assignments[pool_remove].remove(song_remove)
            removed_per_pool[pool_remove] += 1
            song_count -= 1
            total_time -= t_remove
