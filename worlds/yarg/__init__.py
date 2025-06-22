from typing import Any, Dict
from math import ceil
from BaseClasses import Region, Tutorial, MultiWorld
from worlds.AutoWorld import WebWorld, World
from .Options import YargOptions
from .Locations import StaticLocations, location_table, YargLocationType, YargLocationHelpers, location_data_table, YargLocation
from .Items import WeightedItem, item_table, item_data_table, StaticItems, pick_weighted_item, YargItem

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
    
class yargWorld(World):
    """
    YARG (a.k.a. Yet Another Rhythm Game) is a free, open-source, plastic guitar game still in development.
    It supports guitar (five fret), drums (plastic or e-kit), vocals, pro-guitar, and more!
    """
    game = "Yarg"
    required_client_version = (0, 6, 1)
    web = yargWebWorld()
    options_dataclass = YargOptions
    options: YargOptions
    location_name_to_id = location_table
    item_name_to_id = item_table
    
    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)

        self.songChecks: list[str] = []
        self.songExtraChecks: list[str] = []
        self.songFamePointsChecks: list[str] = []
        
        self.famePointsForGoal = 0
        self.famePointsInPool = 0
        
        self.startingSongs: list[str] = []
        self.poolSongs: list[str] = []

        self.fillerItems = []

    def generate_early(self) -> None:
        
        normal_check_amount = self.options.song_checks.value
        starting_check_amount = self.options.starting_songs.value
        total_check_amount = normal_check_amount + starting_check_amount
        extra_check_percentage = self.options.song_check_extra.value
        extra_check_amount = round(total_check_amount * extra_check_percentage / 100)
        
        # Build the pool of standard song locations.
        self.songChecks = YargLocationHelpers.get_locations_by_type(YargLocationType.Standard)[:total_check_amount]
    
        # Randomly select songs from the pool to receive extra checks.
        songs_to_add_extra_checks: list[str] = self.random.sample(self.songChecks, extra_check_amount)
        for location_key in self.songChecks: # Do it this way so the songs stay in their correct order
            if not location_key in songs_to_add_extra_checks:
                continue
            self.songExtraChecks.append(YargLocationHelpers.GetLinkedCheck(location_key, YargLocationType.Extra))
            
        # Set up fame points based on the victory condition.
        if self.options.victory_condition.value == 0:  # World Tour mode.
            self.songFamePointsChecks = [YargLocationHelpers.GetLinkedCheck(loc, YargLocationType.Fame) for loc in self.songChecks]  # add a fame check for each song
            self.famePointsForGoal = ceil(len(self.songChecks) * (self.options.fame_point_needed.value / 100)) # Calculate required fame points based on the setting
            self.famePointsInPool = 0  # Fame points are solely tied to Fame Checks.
        else:  # Get Famous mode.
            self.famePointsInPool = self.options.fame_point_amount.value
            self.famePointsForGoal = ceil(self.famePointsInPool * (self.options.fame_point_needed.value / 100))
            
        # Pull some songs out of the pool to make starting songs
        songs_for_starting_pool = self.random.sample(self.songChecks, self.options.starting_songs.value)
        songs_for_standard_pool = [song for song in self.songChecks if song not in songs_for_starting_pool]
        
        # Process starting songs: add precollected items.
        for location_key in songs_for_starting_pool:
            start_item_name: str = YargLocationHelpers.GetUnlockItem(location_key)
            self.startingSongs.append(start_item_name)
            self.multiworld.push_precollected(self.create_item(start_item_name))
            
        # Process standard songs: add to the item pool later.
        for location_key in songs_for_standard_pool:
            self.poolSongs.append(YargLocationHelpers.GetUnlockItem(location_key))

        #Add filler items
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
        if self.fillerItems.__len__ == 0:
            self.fillerItems.append(WeightedItem(StaticItems.StarPower, 1))

        
    def create_item(self, name: str) -> YargItem:
        data = item_data_table[name]
        return YargItem(name, data.classification, data.code, self.player)
    
    def create_items(self) -> None:
        # Add song unlock items.
        self.multiworld.itempool += [self.create_item(song) for song in self.poolSongs]
        
        # Add Fame Point items.
        self.multiworld.itempool += [self.create_item(StaticItems.FamePoint) for _ in range(self.famePointsInPool)]
            
        totalItemsInPool = len(self.poolSongs) + self.famePointsInPool
        totalChecksInPool = len(self.songChecks) + len(self.songExtraChecks)
        items_to_add = totalChecksInPool - totalItemsInPool
        
        # Add filler items to balance the pool if needed.
        if items_to_add > 0:
            self.multiworld.itempool += [self.create_item(self.get_filler_item_name()) for _ in range(items_to_add)]
                
    def create_regions(self) -> None:
        # Create the menu region. Only one we need
        self.multiworld.regions.append(Region("Menu", self.player, self.multiworld))
        menuRegion = self.multiworld.get_region("Menu", self.player)
            
        # Create a Location Names to Address dictionary for all locations in the pool
        allLocations: Dict[str, int] = {}
        for location_key in self.songChecks:
            allLocations[location_key] = location_data_table[location_key].address
        for location_key in self.songExtraChecks:
            allLocations[location_key] = location_data_table[location_key].address
        for location_key in self.songFamePointsChecks:
            allLocations[location_key] = location_data_table[location_key].address
        allLocations[StaticLocations.GoalSong] = location_data_table[StaticLocations.GoalSong].address
            
        menuRegion.add_locations(allLocations, YargLocation)
        
        # Place locked items for Fame Points and the Goal Song.
        for location_key in self.songFamePointsChecks:
            self.multiworld.get_location(location_key, self.player).place_locked_item(self.create_item(StaticItems.FamePoint))
        self.multiworld.get_location(StaticLocations.GoalSong, self.player).place_locked_item(self.create_item(StaticItems.Victory))
        
    def set_rules(self) -> None:
        
        for location_key in self.songChecks:
            unlock = YargLocationHelpers.GetUnlockItem(location_key)
            self.multiworld.get_location(location_key, self.player).access_rule = lambda state, I=unlock: state.has(I, self.player)
            
        for location_key in self.songExtraChecks:
            unlock = YargLocationHelpers.GetUnlockItem(location_key)
            self.multiworld.get_location(location_key, self.player).access_rule = lambda state, I=unlock: state.has(I, self.player)
            
        for location_key in self.songFamePointsChecks:
            unlock = YargLocationHelpers.GetUnlockItem(location_key)
            self.multiworld.get_location(location_key, self.player).access_rule = lambda state, I=unlock: state.has(I, self.player)
        
        self.multiworld.get_location("Goal Song", self.player).access_rule = lambda state: state.has(StaticItems.FamePoint, self.player, self.famePointsForGoal)
        self.multiworld.completion_condition[self.player] = lambda state: state.has(StaticItems.Victory, self.player)
            
    def get_filler_item_name(self) -> str:
        return pick_weighted_item(self.random, self.fillerItems).name
    
    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "starting_songs": self.startingSongs,
            "fame_points_for_goal": self.famePointsForGoal,
            "victory_condition": self.options.victory_condition.value,
            "death_link": self.options.death_link.value,
        }
