# YARG Archipelago Randomizer Setup Guide

## Required Software

- **[Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases)**.
- **[YARG](https://yarg.in/)**  
  - Available via the **[YARC Launcher](https://github.com/YARC-Official/YARC-Launcher/releases/latest)**.
- **[BepInEx](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.2)**  
  - Use version: `BepInEx_win_x64_5.4.23.2`.
- **[The YARG Archipelago Plugin](https://github.com/Thedrummonger/YargArchipelagoClient)**  
  - Also included in the APWorld Release.
- **[The YARG Archipelago Client](https://github.com/Thedrummonger/YargArchipelagoClient)**  
  - Also included in the APWorld Release.

## Installation Procedures

### Windows Setup

1. **Install Archipelago**  

2. **Install the YARC Launcher**  

3. **Install YARG via the launcher**  
   - Open the **YARC Launcher** and install **YARG**.  
   - Both the **nightly** and **stable** versions are supported, just be sure to use the corresponding plugin. 
     - Note: the nightly updates frequently and requires reinstalling BepInEx and the AP plugin after each update.  
   - It’s recommended to create a separate install of **YARG** specifically for **Archipelago** and use it only for that purpose.

4. **Install BepInEx**  
   - Locate your YARG installation folder:  
     - In the YARC Launcher, click on your YARG install.  
     - Click the menu to the right of **Launch** and select **Open Install Folder**.  
     - Open the **installation** folder.
   - Extract **BepInEx_win_x64_5.4.23.2** into this folder.  
   - Ensure **winhttp.dll** is in the same folder as **YARG.exe**.

5. **Launch YARG & Import Songs**  
   - Open YARG and import the songs you want in your seed.  
   - **Tip:** It’s recommended to create a separate folder with only the songs you want in your seed before importing.  
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

See the guide on setting up a basic YAML at the Archipelago setup
guide: [Basic Multiworld Setup Guide](/tutorial/Archipelago/setup/en)

### Where do I get a config file?

The Player Options page on the website allows you to configure your personal 
options and export a config file from them.

### Verifying your config file

If you would like to validate your config file to make sure it works, you may do so on the YAML Validator page. YAML
validator page: [YAML Validation page](/mysterycheck)

## Difference between the YAML config and the YARG client config settings

### **The YAML Config**
- Defines **the number of items and locations** in your world.
- **Does NOT** specify what songs these locations represent or what is required to clear them.

### **The Client Config**
- Determines **which songs** from your YARG library are assigned to each Archipelago location.
- Uses **Song Pools** to define requirements such as instruments, difficulty, and minimum score.

## Configuring a Song Pool

### **Adding a Song Pool**
1. **Instrument** – Select the required instrument for this pool.
2. **Name** – Choose a unique name (displayed alongside each song in the list).

### **Configuring a Song Pool**
- **Amount in Pool** – The total number of songs in this pool.  
  _(All pools combined must equal the total locations in your Archipelago world.)_
- **Min Difficulty** – Only songs **at or above** this difficulty for the selected instrument are included.
- **Max Difficulty** – Only songs **at or below** this difficulty for the selected instrument  are included.
- **Min Score** – The minimum required score to pass the check.
- **Mix Difficulty** – The minimum difficulty you must play the song at to complete the check.

Reward 1 specifies the difficulty for the first location check attached to this song while Reward 2 specifies 
the second location check (if applicable) 

## Joining a MultiWorld Game


### Connect and configure the client
  
1. Open the YARG Archipelago Client and connect to the Archipelago server when prompted 
2. Configure your client settings as mentioned above.
3. Open your YARG Nightly install, you should see a message in the client confirming YARG is connected. To test connection,
   load into any song, you should see the title of the client update to match 

### Play the game

When the client shows you are connected to YARG, you're ready to begin playing. Congratulations on
successfully joining a multiworld game!

## Hosting a MultiWorld game

The recommended way to host a game is to use our hosting service. The process is relatively simple:

1. Collect config files from your players.
2. Create a zip file containing your players' config files.
3. Upload that zip file to the Generate page above.
    - Generate page: [WebHost Seed Generation Page](/generate)
4. Wait a moment while the seed is generated.
5. When the seed is generated, you will be redirected to a "Seed Info" page.
6. Click "Create New Room". This will take you to the server page. Provide the link to this page to your players, so
   they may download their patch files from there.
7. Note that a link to a MultiWorld Tracker is at the top of the room page. The tracker shows the progress of all
   players in the game. Any observers may also be given the link to this page.
8. Once all players have joined, you may begin playing.
