from dataclasses import dataclass
from Options import StartInventoryPool, DeathLink, Choice, Range, PerGameCommonOptions

# Maximum number of songs available.
maxSongs: int = 500

# ------------------------------------------------------------------------------
# Song Check Options
# ------------------------------------------------------------------------------
class SongCheckAmount(Range):
    """Specifies the total number of song checks to add to the item pool."""
    display_name = "Check Amount"
    range_start = 1
    range_end = maxSongs
    default = 50
    
class SongCheckExtra(Range):
    """Determines the percentage of songs that award an extra check upon completion."""
    display_name = "Extra Check Percentage"
    range_start = 0
    range_end = 100
    default = 50

# ------------------------------------------------------------------------------
# Victory and Fame Settings
# ------------------------------------------------------------------------------
class VictoryCondition(Choice):
    """
    Select the game's victory condition:
      - World Tour: Complete every song on the setlist.
      - Get Famous: Accumulate a set number of fame points and complete the Victory Song.
    """
    display_name = "Victory Condition"
    option_world_tour = 0
    option_get_famous = 1
    default = 1
    
class FamePointsAdded(Range):
    """Sets the number of Fame Point items to include in the pool."""
    display_name = "Fame Point Amount"
    range_start = 0
    range_end = maxSongs
    default = 50
    
class FamePointsNeeded(Range):
    """Specifies the percentage of Fame Points from the pool required to unlock the Victory Song."""
    display_name = "Fame Point Percentage"
    range_start = 0
    range_end = 100
    default = 50

# ------------------------------------------------------------------------------
# Starting Songs Option
# ------------------------------------------------------------------------------
class StartingSongs(Range):
    """Specifies how many songs you begin with in your setlist."""
    display_name = "Starting Songs"
    range_start = 0
    range_end = maxSongs
    default = 3

# ------------------------------------------------------------------------------
# DeathLink Option
# ------------------------------------------------------------------------------
class YargDeathLink(DeathLink):
    """
    If enabled, failing a song will send a deathlink.
    Additionally, if a deathlink is sent to you, you immediately fail your current song.
    """

# ------------------------------------------------------------------------------
# Combined Game Options
# ------------------------------------------------------------------------------
@dataclass
class YargOptions(PerGameCommonOptions):
    victory_condition: VictoryCondition
    fame_point_amount: FamePointsAdded
    fame_point_needed: FamePointsNeeded
    song_checks: SongCheckAmount
    song_check_extra: SongCheckExtra
    starting_songs: StartingSongs
    death_link: YargDeathLink
    start_inventory_from_pool: StartInventoryPool
