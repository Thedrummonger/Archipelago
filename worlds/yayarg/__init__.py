from typing import Any, Dict
from math import ceil
from BaseClasses import Region, Tutorial, MultiWorld
from worlds.AutoWorld import WebWorld, World
from .Options import YargOptions, maxSongs
from .Locations import StaticLocations, location_table, YargLocationType, YargLocationHelpers, location_data_table, YargLocation
from .Items import WeightedItem, item_table, item_data_table, StaticItems, pick_weighted_item, YargItem
from Options import OptionError
from .item_location import YargAPImportData, ImportAndCreateItemLocationData, nice_name
from .yarg_song_data_helper import deserialize_song_data, YargSongData
from .song_distribution import distribute_songs_to_pools

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
        self.CompletionCheck: bool = False
        self.Starting: bool = False
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

    location_name_to_id = None
    item_name_to_id = None
    item_location_data: YargAPImportData = None

    AssignedSongs: list[AssignedSongData]

    fillerItems = []
    
    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)

        self.AssignedSongs = []
        
        if self.item_location_data is None:
            self.item_location_data = ImportAndCreateItemLocationData()
            self.location_name_to_id = self.item_location_data.location_name_to_id
            self.item_name_to_id = self.item_location_data.item_name_to_id

    
    def generate_early(self) -> None:
        SerializedSongList = self.options.songList.value
        user_songs = deserialize_song_data(SerializedSongList)

        for hash, data in user_songs.items():
            if hash not in self.item_location_data.hash_to_song_data:
                raise OptionError(f"Fatal Error, Player {self.player_name} song {data.Title} was not added to master data list. Ensure the SongList Hash is not a weighted option.")
            
        result = distribute_songs_to_pools(self.options.song_pools.value, user_songs)

        if not result.success:
            error_message = "Failed to Fill Song pools:\n\n".join(result.errors)
            raise OptionError(error_message)
        
        # A list of AssignedSongData, each entry represents a single song, containing it's location unlock items and song pool
        for pool, assignedHashes in result.pool_assignments.items():
            for hash in assignedHashes:
                AssignmentData = AssignedSongData(hash, pool)
                AssignmentData.CompletionCheck = self.options.setlist_needed.value > 0
                self.AssignedSongs.append(AssignmentData)

        startingSongs = self.random.sample(self.AssignedSongs, self.options.starting_songs.value)
        for song in startingSongs:
            song.Starting = True
            
        extra_check_amount = round(len(self.AssignedSongs) * self.options.song_check_extra.value / 100)
        SongWithExtraChecks = self.random.sample(self.AssignedSongs, extra_check_amount)
        for song in SongWithExtraChecks:
            song.ExtraCheck = True

        NonStartingSong = [song for song in self.AssignedSongs if not song.Starting]
        songPackSize = self.options.song_pack_size.value
        if self.options.song_pack_size.value > 1:
            SongPacksNeeded = ceil(len(NonStartingSong) / songPackSize) 
            SongPackItems = [self.item_location_data.song_pack_id_to_name[pack] for pack in range(SongPacksNeeded)]
            pack_pool = [pack for pack in SongPackItems for _ in range(songPackSize)]
            self.random.shuffle(pack_pool)
            for i, song in enumerate(NonStartingSong):
                song.SongPack = pack_pool[i]
        

    def create_item(self, name: str) -> YargItem:
        classification = self.item_location_data.item_name_to_classification[name]
        id = self.item_location_data.item_name_to_id[name]
        return YargItem(name, classification, id, self.player)
    
    def create_items(self) -> None:
        #Fill The item Pool
        return
                
    def create_regions(self) -> None:
        # Create the menu region. Only one we need
        self.multiworld.regions.append(Region("Menu", self.player, self.multiworld))
        menuRegion = self.multiworld.get_region("Menu", self.player)
        
    def set_rules(self) -> None:
        return
            
    def get_filler_item_name(self) -> str:
        if not self.fillerItems:
            return StaticItems.StarPower
        return pick_weighted_item(self.random, self.fillerItems).name
    
    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "starting_songs": self.startingSongs,
            "fame_points_for_goal": self.famePointsForGoal,
            "song_pack_size": self.options.song_pack_size.value,
            "victory_condition": self.options.victory_condition.value,
            "death_link": self.options.death_link.value,
            "energy_link": self.options.energy_link.value,
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