﻿# YARG Archipelago Randomizer Setup Guide

## Required Software

- **[Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases)**.
- **[YARG](https://yarg.in/)**  
  - Available via the **[YARC Launcher](https://github.com/YARC-Official/YARC-Launcher/releases/latest)**.
- **[BepInEx](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.2)**  
  - Use version: `BepInEx_win_x64_5.4.23.2`.
- **[The YARG Archipelago Plugin](https://github.com/Thedrummonger/YargArchipelagoClient/releases/latest)**  
- **[The YARG Archipelago Client](https://github.com/Thedrummonger/YargArchipelagoClient/releases/latest)**  
- **[The YARG APWorld](https://github.com/Thedrummonger/YargArchipelagoClient/releases/latest)**  

## Installation Procedures

### Windows Setup

1. **Install [Archipelago](https://archipelago.gg/tutorial/Archipelago/setup_en) and the Yarg APWorld**  
   - Unless you are the one hosting the game, this is only required to generate your YAML. The Archipelago program is not required to connect YARG to an arhcipelago server.

2. **Install the YARC Launcher**  

3. **Install YARG via the launcher**  
   - Open the **YARC Launcher** and install **YARG**.  
   - Both the **nightly** and **stable** versions are supported, just be sure to use the corresponding plugin. 
     - Note: the nightly updates frequently and requires reinstalling BepInEx and the AP plugin after each update.  
     - Currently the only difference between nightly and Stable is that nightly supports "failing" a song which supports deathlink if enabled.  
   - It’s recommended to create a separate install of **YARG** specifically for **Archipelago** and use it only for that purpose.
     - This can be done through the YARC launcher, or by downloading a portable version of YARG [here](https://github.com/YARC-Official/YARG/releases/latest)  

4. **Install BepInEx**  
   - Locate your YARG installation folder:  
     - In the YARC Launcher, click on your YARG install.  
     - Click the menu to the right of **Launch** and select **Open Install Folder**.  
     - Open the **installation** folder.
   - Extract **BepInEx_win_x64_5.4.23.2** into this folder so that **winhttp.dll** is in the same folder as **YARG.exe**.

5. **Launch YARG & Import Songs**  
   - Open YARG and import the songs you want in your seed.  
     - It’s recommended to create a separate folder with only the songs you want in your seed and set that as your only active song folder in yarg.  
   - Navigate to **Settings → Songs** and select **Scan Songs** at least once after updating your song directory.
   - Ensure you have done this step and scanned your songs at least once before opening and configuring the client

6. **Install the YARG Archipelago Plugin**  
   - Go to your YARG installation folder.  
   - Move `YargArchipelagoPlugin.dll` to the **BepInEx\plugins** directory.

7. **Launch the YARG Archipelago Client & Configure Your Seed**  
   - This must be done **after** the world is generated.  

### Linux Setup

Not yet supported, though you may be able to install the linux version of YARG and BepInEx
and then run the client through [Mono](https://www.mono-project.com/).

## Create a Config (.yaml) File

### What is a config file and why do I need one?

See the guide on setting up a basic YAML at the Archipelago setup guide: [Basic Multiworld Setup Guide](/tutorial/Archipelago/setup/en)

### Where do I get a config file?

The Player Options page on the website allows you to configure your personal 
options and export a config file from them.

Alternatively, you can run `ArchipelagoLauncher.exe` and click on `Generate Template Options` to create a set of template YAMLs for each game in your Archipelago install. 
These will be placed in your Players/Templates folder.

### Verifying your config file

If you would like to validate your config file to make sure it works, you may do so on the YAML Validator page. YAML
validator page: [YAML Validation page](/mysterycheck)

## Difference between the YAML config and the YARG client config settings

### **The YAML Config**
- Created **before** the multiworld is generated.
- Defines the number and types of items and locations in your world as well as your victory condition.
- **Does NOT** specify what songs these locations require you to play or what is required to clear them.

### **The Client Config**
- Created **after** the multiworld is generated when you first connect the client to the server.
- Determines which songs from your YARG setlist are assigned to each Archipelago location.
- Uses **Song Pools** to define the requirements such as instruments, difficulty, and minimum score for each song location.

## Configuring a Song Pool

### **Adding a Song Pool**
1. **Instrument** – Select the required instrument for this pool.
2. **Name** – Choose a unique name (displayed alongside each song in the list).

### **Configuring a Song Pool**
- **Amount in Pool** – The total number of songs in this pool.  
  _(All pools combined must equal the total locations in your Archipelago world.)_
- **Song Selection**
  - **Min Difficulty** – Only songs **at or above** this difficulty for the selected instrument are included.
  - **Max Difficulty** – Only songs **at or below** this difficulty for the selected instrument  are included.
- **Song Requirements**
  - **Min Score** – The minimum required score to pass the check.
  - **Min Difficulty** – The minimum difficulty you must play the song at to complete the check.

Reward 1 specifies the difficulty for the first location check attached to this song while Reward 2 specifies 
the second location check (if applicable) 

## Joining a MultiWorld Game


### Connect and configure the client
  
1. Open the YARG Archipelago Client and connect to the Archipelago server when prompted 
2. Configure your client settings as mentioned above.
3. Open your YARG install, you should see a message in the client confirming YARG is connected. 
    - To test the connection, start playing any song. you should see the title of the client update to display the song name.
