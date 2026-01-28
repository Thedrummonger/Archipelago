# YARG Archipelago Randomizer Setup Guide

## Required Software

- **[Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases)**.
    - Only if you are hosting the seed or playing solo.
- **[YARG](https://yarg.in/)**
    - Available via the **[YARC Launcher](https://github.com/YARC-Official/YARC-Launcher/releases/latest)**.
- **[BepInEx 5](https://github.com/BepInEx/BepInEx/releases)**
    - Use the latest version of `BepInEx 5.x.x` NOT `BepInEx 6.x.x`.
- **[The YARG Archipelago Plugin](https://github.com/Thedrummonger/YargArchipelagoPluginV2/releases/latest)**
- **[The YARG AP YAML Creator](https://github.com/Thedrummonger/YargArchipelagoPluginV2/releases/latest)**
- **[The YARG APWorld](https://github.com/Thedrummonger/YargArchipelagoPluginV2/releases/latest)**

## Installation

### Setup

1. **Install [Archipelago](https://archipelago.gg/tutorial/Archipelago/setup_en) and the Yarg APWorld**
    - Unless you are the one generating the seed, this is not required. The Archipelago program is not required to connect YARG to an AP server.

2. **Install YARG**
    - Download and install the [**YARC Launcher**](https://github.com/YARC-Official/YARC-Launcher/releases/latest) and use it to install **YARG**. You can also download a portable build directly from [YARG releases](https://github.com/YARC-Official/YARG/releases/latest).
    - Both the **nightly** and **stable** versions are supported, just be sure to use the corresponding plugin.
        - Note: the nightly updates frequently and requires reinstalling BepInEx and the AP plugin after each update.
        - Currently, the only difference between nightly and Stable is that nightly supports "failing" a song which triggers deathlink if enabled.
    - It’s recommended to create a separate installation of **YARG** specifically for **Archipelago** and use it only for that purpose which can be done through the YARC launcher, or by using a portable version of YARG.

3. **Install BepInEx 5**
    - Download the latest version of `BepInEx 5` for your OS and follow the installation instruction.
    - Run the game with bepin installed at least once so the proper folders are generated.

4. **Install the YARG Archipelago Plugin**
    - Go to your YARG installation folder.
    - Open the YargAPPlugin.zip file downloaded from github
    - Move `YargArchipelagoPlugin.dll` and `Archipelago.MultiClient.Net.dll` to the `BepInEx\plugins` directory.

5. **Launch YARG & Import Songs**
    - Open YARG and import the songs you want in your seed.
        - It’s recommended to create a separate folder with only the songs you want in your seed and set that as your only active song folder in yarg.
    - Navigate to **Settings → Songs** and select **Scan Songs** at least once after updating your song directory.
    - Ensure you have done this step and scanned your songs at least once before opening the YAML Creator and configuring your YAML.

6. **Generate Your YAML File**
    - See `Create a Config (.yaml) File` below for instruction. This is not the normal setup process!

7. **Launch the YARG and Connect!**
    - Once you have launched yarg with the plugin loaded, you will see a connection window. This window can be opened
    or closed at any time with F10.


## Create a Config (.yaml) File

> **Important:** READ THIS!!! This is **not** the usual Archipelago setup process!

### What is a config file and why do I need one?

See the guide on setting up a basic YAML at the Archipelago setup guide: [Basic Multiworld Setup Guide](/tutorial/Archipelago/setup/en)

### Where do I get a config file?

Unlike most Archipelago games, you **do not manually create** a YAML file for YARG.

Instead, you must use the **included YAML Creator application** to generate your config file.

This is required because the YARG APWorld generates a **unique hash** based on the songs you currently have installed in YARG. That hash is used to build a **custom location list** for your seed. Without it, the generator has no way to know which songs exist in your library.


## What is a Song Pool?

Song pools are the system this YARG Archipelago implimentation uses to decide **which songs are included in your seed**.

Each song pool defines a set of restrictions (instrument, difficulty range, clear requirements, etc.) and then adds a **specific number of songs** that match those rules to the seed. Your final song list is created by combining the results of *all* enabled song pools.

For example, you could create:
- A **Guitar** song pool that adds **20 songs** with difficulties between **3–5**
- A **Drums** song pool that adds **20 songs** with difficulties between **1–4**

Each song pool operates independently, allowing you to mix and match instruments and difficulty ranges freely.

You can also create **multiple song pools for the same instrument**. For example:
- A Guitar pool with difficulties **1–4** that requires a **Full Combo** to complete the check
- Another Guitar pool with difficulties **4–6** that only requires **4 stars** for the main check and **3 stars** for the extra check

This makes it possible to design very specific progression rules. Easier songs can demand high accuracy, while harder songs can allow more room for mistakes.


### **Adding a Song Pool**
1. **Instrument** – Select the required instrument for this pool.
2. **Name** – Choose a unique name (displayed alongside each song in the list).

### **Configuring a Song Pool**
- **Amount in Pool** – The total number of songs in this pool.
- **Song Selection**
    - **Min Difficulty** – Only songs **at or above** this difficulty for the selected instrument are included.
    - **Max Difficulty** – Only songs **at or below** this difficulty for the selected instrument  are included.
- **Song Requirements**
    - **Min Score** – The minimum score (stars) required to pass the check.
    - **Min Difficulty** – The minimum difficulty you must play the song at to complete the check.
  - Reward 1 specifies the difficulty for the first location check attached to this song while Reward 2 specifies
  the second location check (if applicable)

## Joining a MultiWorld Game


### Connecting to the AP Server

1. Open YARG with the bepin plugins installed and connect to the Archipelago server using the f10 menu
2. Your available songs will be displayed in a custom header in the music library.
