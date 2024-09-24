# Achievement Watchdog

Achievement Watchdog is a program designed to provide real-time achievement notifications for games using the Goldberg Steam Emulator. It allows users to view their game achievements offline and locally, offering a seamless experience without the need for an internet connection, the official Steam client, or any kind of Steam API keys. Currently, it only supports Goldberg Steam Emulator, as other emulators may use different achievement formats.

This program was originally created for personal use, but I welcome feedback and suggestions. Feel free to use it however you wish! If anyone is interested in adding a GUI for the Achievement Viewer, that would be great, as I won't be focusing on that.

**Disclaimer:** This software is provided "as is" without any warranties or guarantees. I can't guarantee it will work perfectly in all cases, so use it at your own risk.

## Features

- **Real-time Achievement Notifications:** Get native Windows toast notifications as you unlock achievements while playing.
- **Offline Achievement Viewing:** View achievements for your games locally, even when you're offline.
- **Custom Notification Sounds:** Easily customize the achievement notification sound.
- **System Tray Support:** Run in the background with a system tray icon for easy access and management.

## Setup Instructions

### 1. Download and Configure Goldberg Emulator

1. Download the Goldberg Steam Emulator from [Detanup01/gbe_fork](https://github.com/Detanup01/gbe_fork/releases).
   - Download the file `emu-win-release.7z`.
   - Extract it and locate the emulator inside the `experimental` folder (either `steam_api.dll` or `steam_api64.dll`).
   - Download `generate_emu_config-win.7z` from the same page and extract it.
   
2. Generate the `steam_settings` folder for your game:
   - Open a terminal (Command Prompt or PowerShell).
   - Navigate to the folder where `generate_emu_config.exe` is located and open a terminal there.
   - Run the following command (replace `<game_id>` with your game's ID, you can find the game ID of any game through SteamDB):
     ```bash
     generate_emu_config.exe <game_id>
     ```
   - This will generate a `steam_settings` folder.
   
3. Apply the emulator to your game:
   - Go to the game folder where you want to enable achievements.
   - Locate the existing `steam_api.dll` or `steam_api64.dll` file.
   - Replace it with the emulator version from the `experimental` folder (keep a backup of the original by renaming it).
   - Copy the generated `steam_settings` folder to the same location.
   **Important Note:** If the game has any alternative emulators (often found in "NoDVD" or similar folders in repacks), they need to be either removed or zipped. Having multiple emulators present can confuse Achievement Watchdog and cause issues with achievement tracking.

4. **Troubleshooting:** If the game doesn't start or there are issues with the emulator (Especially if the game didn't have any steam emulator prior), check [this guide](https://rentry.co/goldberg_emulator) for additional setup instructions, as you might need to bypass SteamStubDRM for certain cases.

### 2. Set Up Achievement Watchdog

1. Download the latest release of Achievement Watchdog from the [**releases page**](https://github.com/50t0r25/achievement-watchdog/releases).
2. Extract the files to a folder of your choice.
3. Open the `.env` file (using Notepad or any text editor) and set your game directories. The file looks like this by default:
   ```bash
   LOCAL_ACHIEVEMENTS_PATH=%appdata%\GSE saves\
   GAMES_PATH=C:\games
   ```
   - **LOCAL_ACHIEVEMENTS_PATH** should not be changed if you followed the Goldberg setup steps.
   - **GAMES_PATH** should point to the folder where your games are installed.

4. You can also customize the notification sound by replacing the `achievement_sound.mp3` file (keep the same name).

### 3. Using Achievement Watchdog

- **To view achievements:** Run `Achievement Viewer.exe`. This opens a terminal where you can view your achievements.
   - You can add `-nohide` as an argument (either in a shortcut or via the terminal) to reveal hidden descriptions of certain achievements.
- **To enable achievement notifications:** Run `Achievement Watchdog.exe`. This will launch the program in the background, with an icon appearing in the system tray. As you unlock achievements, you'll receive notifications on your desktop.

---

## Usage Notes

1. **Disable Do Not Disturb:** Ensure that Windows notifications are not blocked while gaming. Go to:
   - **Settings > System > Notifications** 
   - Disable "Turn on do not disturb automatically when playing a game."
   - Notifications will not appear if this setting is enabled.

2. **Achievements Viewer Requires At Least One Achievement Unlocked:** The Achievement Viewer will not display achievements for a game until you have unlocked at least one achievement.

3. **Notifications Work Independently:** Achievement Watchdog does **not** need to be running to unlock achievements. It only serves to send notifications when you unlock achievements during gameplay.

---

## Requirements

- **Operating System:** Windows 10 or Windows 11.
- **Notifications:** Uses native Windows toast notifications for real-time achievement alerts.