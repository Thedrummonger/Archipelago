from dataclasses import dataclass
from Options import StartInventoryPool, DeathLink, Choice, Range, PerGameCommonOptions

# Maximum number of songs available.
maxSongs: int = 500

# ------------------------------------------------------------------------------
# Song Check Options
# ------------------------------------------------------------------------------
class SongCheckAmount(Range):
    """
    Specifies the number of base songs to add to the location pool.

    This is added on top of your starting songs and the one goal song.
    For example: 10 base songs + 3 starting songs + 1 goal song = 14 total songs.
    """
    display_name = "Base Song Pool Amount"
    range_start = 1
    range_end = maxSongs
    default = 50
    
class SongCheckExtra(Range):
    """
    Determines what percentage of song locations will award an extra item when completed. This includes starting songs.
    """
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
        -World Tour: Complete every song location, then finish your goal song.
        -Get Famous: Earn a set number of fame points, then complete the goal song.
    """
    display_name = "Victory Condition"
    option_world_tour = 0
    option_get_famous = 1
    default = 1
    
class FamePointsAdded(Range):
    """Adds the specified number of Fame Point items to the pool. Only used in Get Famous mode."""
    display_name = "Fame Point Amount"
    range_start = 0
    range_end = maxSongs
    default = 50
    
class FamePointsNeeded(Range):
    """Sets the percentage of available Fame Points needed to unlock the goal song. Only applies in Get Famous mode."""
    display_name = "Fame Point Percentage"
    range_start = 0
    range_end = 100
    default = 50

# ------------------------------------------------------------------------------
# Starting Songs Option
# ------------------------------------------------------------------------------
class StartingSongs(Range):
    """Sets the number of songs you start with in your setlist."""
    display_name = "Starting Songs"
    range_start = 0
    range_end = maxSongs
    default = 3

# ------------------------------------------------------------------------------
# Filler Option
# ------------------------------------------------------------------------------
class StarPowerItem(Range):
    """
    Specifies the weight of the Star Power filler item.
    This item adds 1/4 of a Star Power bar when received.

    If all filler/trap items are set to a weight of zero, this value will be forced to 1
    """
    display_name = "Star Power Item Filler Weight"
    range_start = 0
    range_end = 999
    default = 5

class SwapSongRandom(Range):
    """
    Specifies the weight of the Swap Song (Random) filler item.
    This item lets you swap one of your songs with a randomly selected new song.
    """
    display_name = "Swap Song Random Filler Weight"
    range_start = 0
    range_end = 999
    default = 5

class SwapSongChoice(Range):
    """
    Specifies the weight of the Swap Song (Choice) filler item.
    This item lets you swap one of your songs with a new one of your choice.
    """
    display_name = "Swap Song Choice Filler Weight"
    range_start = 0
    range_end = 999
    default = 3

class LowerDifficulty(Range):
    """
    Specifies the weight of the Swap Song (Choice) filler item.
    This item lets you Lower the instrument difficulty or score requirement for a song of your choice.
    """
    display_name = "Lower Difficulty Filler Weight"
    range_start = 0
    range_end = 999
    default = 0

class RestartTrap(Range):
    """
    Specifies the weight of the Restart Trap filler item.
    Getting this item during a song will immediately boot you out of it.
    """
    display_name = "Restart Trap Filler Weight"
    range_start = 0
    range_end = 999
    default = 1
    
class BrokenWhammyTrap(Range):
    """
    Specifies the weight of the Restart Trap filler item.
    Makes the fret icons at the bottom of the board rise up and become unusable until the whammy bar is moved up and down to make the on screen whammy bar disappear.
    """
    display_name = "Broken Whammy Trap Filler Weight"
    range_start = 0
    range_end = 999
    default = 1
    
class LeftyFlipTrap(Range):
    """
    Specifies the weight of the Restart Trap filler item.
    Flips the note chart horizontally.
    """
    display_name = "Lefty Flip Trap Filler Weight"
    range_start = 0
    range_end = 999
    default = 1
    
class AmpOverloadTrap(Range):
    """
    Specifies the weight of the Restart Trap filler item.
    Makes the note gems flash, and the fret board shake making it harder to play.
    """
    display_name = "Amp Overload Trap Filler Weight"
    range_start = 0
    range_end = 999
    default = 1
    
class BrokenStringTrap(Range):
    """
    Specifies the weight of the Restart Trap filler item.
    Makes a certain fret icon rise up, you need to keep tapping the fret button until it works again.
    """
    display_name = "Broken String Trap Filler Weight"
    range_start = 0
    range_end = 999
    default = 1

# ------------------------------------------------------------------------------
# DeathLink Option
# ------------------------------------------------------------------------------
class YargDeathLink(DeathLink):
    """
    Failing a song will send a DeathLink to others.
    If you receive a DeathLink, you will instantly fail your current song.

    Currently YARG does not support "failing" songs, however a death link will still
    trigger if you fail to meet the given requirements for a song check after playing.
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
    star_power: StarPowerItem
    swap_song_random: SwapSongRandom
    swap_song_choice: SwapSongChoice
    lower_difficulty: LowerDifficulty
    restart_trap: RestartTrap
    death_link: YargDeathLink
    start_inventory_from_pool: StartInventoryPool
