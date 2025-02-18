from random import Random
from typing import Any, Dict
from BaseClasses import Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from .Options import YargOptions
from .Locations import location_table, YargLocationType, YargLocationHelpers, location_data_table, YargLocation
from .Items import WeightedItem, item_table, item_data_table, StaticItems, pick_weighted_item, YargItem

# ------------------------------------------------------------------------------
# Web World Definition
# ------------------------------------------------------------------------------
class yargWebWorld(WebWorld):
    theme = "partyTime"
    
    setup_en = Tutorial(
        tutorial_name="Start Guide",
        description="A guide to playing Yarg/CloneHero.",
        language="English",
        file_name="guide_en.md",
        link="guide/en",
        authors=["Thedrummonger"],
    )
    
    tutorials = [setup_en]
    
# ------------------------------------------------------------------------------
# Main Yarg World
# ------------------------------------------------------------------------------
class yargWorld(World):
    """
    YARG (a.k.a. Yet Another Rhythm Game) is a free, open-source, plastic guitar game still in development.
    It supports guitar (five fret), drums (plastic or e-kit), vocals, pro-guitar, and more!
    """
    game = "Yarg"
    required_client_version = (0, 5, 1)
    web = yargWebWorld()
    options_dataclass = YargOptions
    options: YargOptions
    location_name_to_id = location_table
    item_name_to_id = item_table

    # Lists to store location keys by check type.
    songChecks: list[str] = []
    songExtraChecks: list[str] = []
    songFamePointsChecks: list[str] = []
    
    famePointsForGoal = 0
    famePointsInPool = 0
    
    startingSongs: list[str] = []
    poolSongs: list[str] = []
    
    #Todo: add an option for these weights
    fillerItems = [
        WeightedItem(StaticItems.SwapRandom, 6),
        WeightedItem(StaticItems.SwapPick, 3),
        WeightedItem(StaticItems.TrapRestart, 1),
    ]
    
    # --------------------------------------------------------------------------
    # Early Generation: Setup Locations and Items
    # --------------------------------------------------------------------------
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
            self.famePointsInPool = 0  # Fame points are solely tied to Fame Checks.
            for location_key in self.songChecks:
                self.songFamePointsChecks.append(YargLocationHelpers.GetLinkedCheck(location_key, YargLocationType.Fame))
                self.famePointsForGoal += 1
        else:  # Get Famous mode.
            self.famePointsInPool = self.options.fame_point_amount.value
            self.famePointsForGoal = round(self.famePointsInPool * self.options.fame_point_needed.value / 100)
            
        # Divide song locations into starting songs and standard pool songs.
        starting_song_amount = self.options.starting_songs.value
        songs_for_starting_pool = self.random.sample(self.songChecks, starting_song_amount)
        songs_for_standard_pool = [song for song in self.songChecks if song not in songs_for_starting_pool]
        
        # Process starting songs: add precollected items.
        for location_key in songs_for_starting_pool:
            start_item_name: str = YargLocationHelpers.GetUnlockItem(location_key)
            self.startingSongs.append(start_item_name)
            self.multiworld.push_precollected(self.create_item(start_item_name))
            
        # Process standard songs: add to the item pool later.
        for location_key in songs_for_standard_pool:
            self.poolSongs.append(YargLocationHelpers.GetUnlockItem(location_key))
        
    # --------------------------------------------------------------------------
    # Item Creation
    # --------------------------------------------------------------------------
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
            for _ in range(items_to_add):
                filler = pick_weighted_item(self.random, self.fillerItems).name
                self.multiworld.itempool.append(self.create_item(filler))
                
    # --------------------------------------------------------------------------
    # Region Creation
    # --------------------------------------------------------------------------
    def create_regions(self) -> None:
        # Create the menu region. Only one we need
        self.multiworld.regions.append(Region("Menu", self.player, self.multiworld))
        menuRegion = self.get_region("Menu")
            
        # Create a Location Names to Address dictionary for all locations in the pool
        allLocations: Dict[str, int] = {}
        for location_key in self.songChecks:
            allLocations[location_key] = location_data_table[location_key].address
        for location_key in self.songExtraChecks:
            allLocations[location_key] = location_data_table[location_key].address
        for location_key in self.songFamePointsChecks:
            allLocations[location_key] = location_data_table[location_key].address
        allLocations["Goal Song"] = location_data_table["Goal Song"].address
            
        menuRegion.add_locations(allLocations, YargLocation)
        
        # Place locked items for Fame Points and the Goal Song.
        for location_key in self.songFamePointsChecks:
            self.get_location(location_key).place_locked_item(self.create_item(StaticItems.FamePoint))
        self.get_location("Goal Song").place_locked_item(self.create_item(StaticItems.Victory))
        
    # --------------------------------------------------------------------------
    # Rule Setting
    # --------------------------------------------------------------------------
    def set_rules(self) -> None:
        
        for location_key in self.songChecks:
            unlock = YargLocationHelpers.GetUnlockItem(location_key)
            self.get_location(location_key).access_rule = lambda state, I=unlock: state.has(I, self.player)
            
        for location_key in self.songExtraChecks:
            unlock = YargLocationHelpers.GetUnlockItem(location_key)
            self.get_location(location_key).access_rule = lambda state, I=unlock: state.has(I, self.player)
            
        for location_key in self.songFamePointsChecks:
            unlock = YargLocationHelpers.GetUnlockItem(location_key)
            self.get_location(location_key).access_rule = lambda state, I=unlock: state.has(I, self.player)
        
        self.get_location("Goal Song").access_rule = lambda state: state.has(StaticItems.FamePoint, self.player, self.famePointsForGoal)
        self.multiworld.completion_condition[self.player] = lambda state: state.has(StaticItems.Victory, self.player)
            
    # --------------------------------------------------------------------------
    # Additional World Data
    # --------------------------------------------------------------------------
    def get_filler_item_name(self) -> str:
        return StaticItems.SwapRandom
    
    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "starting_songs": self.startingSongs,
            "fame_points_for_goal": self.famePointsForGoal,
            "victory_condition": self.options.victory_condition,
            "death_link": self.options.death_link,
        }
