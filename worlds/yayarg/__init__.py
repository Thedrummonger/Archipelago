from collections import defaultdict
from typing import Any, Dict
from math import ceil
from BaseClasses import CollectionState, Region, Tutorial, MultiWorld
from worlds.AutoWorld import WebWorld, World
from .Options import YargOptions, VALID_INSTRUMENTS
from .Locations import YargLocation
from .Items import WeightedItem, StaticItems, pick_weighted_item, YargItem
from Options import OptionError
from .data_register import YargAPImportData, ImportAndCreateItemLocationData, nice_name, YargSongData
from .yarg_song_data_helper import deserialize_song_data
from .song_distribution import distribute_songs_to_pools, split_pools_by_instrument

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

    location_name_to_id = {}
    item_name_to_id = {}
    item_location_data: YargAPImportData = None
    
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
        
        if self.item_location_data is None:
            self.item_location_data = ImportAndCreateItemLocationData()
            self.location_name_to_id = self.item_location_data.location_name_to_id
            self.item_name_to_id = self.item_location_data.item_name_to_id

    
    def generate_early(self) -> None:

        self.CreateFillerItems()

        SerializedSongList = self.options.songList.value
        user_songs = deserialize_song_data(SerializedSongList)

        for hash, data in user_songs.items():
            if hash not in self.item_location_data.hash_to_song_data:
                raise OptionError(f"Fatal Error, Player {self.player_name} song {data.Title} was not added to master data list. Ensure the SongList Hash is not a weighted option.")

        # If we can't share songs across instruments, run all of our song pools through the distributer at once
        song_distribution_groups: Dict[str, Dict[str, Dict]] = {"all": self.options.song_pools.value} 
        # If we can share songs across instruments, separate each song pool into groups of like instruments
        # and run them through the distributer separately
        if (self.options.reuse_songs.value == 1):
            song_distribution_groups = split_pools_by_instrument(self.options.song_pools.value)
        
        all_assignments: Dict[str, list[str]] = {}
        for _, pools in song_distribution_groups.items():
            result = distribute_songs_to_pools(pools, user_songs)
            if not result.success:
                error_message = "Failed to Fill Song pools:\n" + "\n".join(result.errors)
                raise OptionError(error_message)
            all_assignments.update(result.pool_assignments)
        
        # A list of AssignedSongData, each entry represents a single song, containing it's location unlock items and song pool
        for pool, assignedHashes in all_assignments.items():
            for hash in assignedHashes:
                AssignmentData = AssignedSongData(hash, pool)
                self.AssignedSongs.append(AssignmentData)

        # If we are shuffling instruments, pick a starting instrument that will allow us enough songs to fill 
        # our starting songs 
        if self.options.instrument_shuffle.value == 1:
            distinct_instruments = {pool_data["instrument"] for pool_data in self.options.song_pools.value.values()}
            songs_per_instrument = {}
            for instrument in distinct_instruments:
                count = len([song for song in self.AssignedSongs if song.GetInstrument(self.options.song_pools.value) == instrument])
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

        eligible_starting_songs = self.AssignedSongs
        if self.starting_instrument:
            eligible_starting_songs = [song for song in self.AssignedSongs
                if self.options.song_pools.value[song.SongPool]["instrument"] == self.starting_instrument]

        # Select Starting Songs before goal song since starting songs can be picky with instrument rando
        # and we don't want to waste a potential candidate
        self.startingSongs = self.random.sample(eligible_starting_songs, self.options.starting_songs.value)
        for song in self.startingSongs:
            song.Starting = True
        
        self.GoalSong = self.random.choice([song for song in self.AssignedSongs if not song.Starting])
        self.GoalSong.Goal = True
        
        # Technically Goal Song can have an unlock item, but we handle it differently
        self.SongsWithUnlockItems = [song for song in self.AssignedSongs if not song.Starting and not song.Goal]
        self.SongsWithItemLocations = [song for song in self.AssignedSongs if not song.Goal]

        extra_check_amount = round(len(self.SongsWithItemLocations) * self.options.song_check_extra.value / 100)
        self.SongWithExtraChecks = self.random.sample(self.SongsWithItemLocations, extra_check_amount)
        for song in self.SongWithExtraChecks:
            song.ExtraCheck = True

        songPackSize = self.options.song_pack_size.value
        if self.options.song_pack_size.value > 1:
            SongPacksNeeded = ceil(len(self.SongsWithUnlockItems) / songPackSize) 
            SongPackItems = [self.item_location_data.song_pack_id_to_name[pack] for pack in range(1, SongPacksNeeded + 1)]
            pack_pool = [pack for pack in SongPackItems for _ in range(songPackSize)]
            self.random.shuffle(pack_pool)
            for i, song in enumerate(self.SongsWithUnlockItems):
                song.SongPack = pack_pool[i]

        self.SongCompletionsNeeded = ceil(len(self.SongsWithItemLocations) * (self.options.fame_point_needed.value / 100))
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
            self.multiworld.itempool += [self.create_item(StaticItems.FamePoint) for _ in range(fame_points_in_pool)]

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
            self.multiworld.itempool += [self.create_item(self.get_filler_item_name()) for _ in range(items_to_add)]
        elif totalItems > totalChecks:
            raise OptionError(f"Not enough locations {totalChecks} to place all items {totalItems}. Reduce the number of Fame Points or increase the number of song checks.")
        
                
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
            self.multiworld.get_location(check, self.player).place_locked_item(self.create_item(StaticItems.SongCompletion))
        
        self.multiworld.get_location(GoalSongLocation, self.player).place_locked_item(self.create_item(StaticItems.Victory))
        
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
        self.multiworld.completion_condition[self.player] = lambda state: state.has(StaticItems.Victory, self.player)

    def can_complete_goal(self, state: CollectionState, instrument: str, unlockItem: str) -> bool:
        SongLocationUnlocked = state.has(instrument, self.player) and state.has(unlockItem, self.player)
        MetFameGoal = self.famePointsNeeded == 0 or state.has(StaticItems.FamePoint, self.player, self.famePointsNeeded)
        MetSetlistGoal = self.SongCompletionsNeeded == 0 or state.has(StaticItems.SongCompletion, self.player, self.SongCompletionsNeeded)
        return SongLocationUnlocked and MetFameGoal and MetSetlistGoal
            
    def get_filler_item_name(self) -> str:
        if not self.fillerItems:
            return StaticItems.StarPower
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
        unlockItemID = self.item_name_to_id[unlockItem] if self.options.goal_song_item_needed else -1
        # string, string, long, long
        goal_data = (self.GoalSong.SongHash, self.GoalSong.SongPool, GoalLocationID, unlockItemID)

        return {
            "fame_points_for_goal": self.famePointsNeeded,
            "setlist_needed_for_goal": self.SongCompletionsNeeded,
            "goal_data": goal_data,
            "death_link": self.options.death_link.value,
            "energy_link": self.options.energy_link.value,
            "pools": self.options.song_pools.value,
            "song_data": dict(song_data)
        }

    
    def CreateFillerItems(self):
        if self.options.star_power.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.StarPower, self.options.star_power.value))
        if self.options.swap_song_random.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.SwapRandom, self.options.swap_song_random.value))
        if self.options.swap_song_choice.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.SwapPick, self.options.swap_song_choice.value))
        if self.options.lower_difficulty.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.LowerDifficulty, self.options.lower_difficulty.value))
        if self.options.restart_trap.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.TrapRestart, self.options.restart_trap.value))
        if self.options.rock_meter_trap.value > 0:
            self.fillerItems.append(WeightedItem(StaticItems.TrapRockMeter, self.options.rock_meter_trap.value))
        if not self.fillerItems:
            self.fillerItems.append(WeightedItem(StaticItems.StarPower, 1))