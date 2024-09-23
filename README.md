# Achievement Watchdog

Achievement Watchdog is a program designed to provide real-time achievement notifications for games using the Goldberg Steam Emulator. It allows users to view their game achievements offline and locally, offering a seamless experience without the need for an internet connection, the official Steam client or any kind of Steam api keys. Currently, it only supports Goldberg Steam Emulator, as other emulators may use different achievement formats.

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
   - Navigate to the folder where `generate_emu_config.exe` is located.
   - Run the following command (replace `<game_id>` with your game's ID):
     ```bash
     generate_emu_config.exe <game_id>
     ```
   - This will generate a `steam_settings` folder.
   
3. Apply the emulator to your game:
   - Go to the game folder where you want to enable achievements.
   - Locate the existing `steam_api.dll` or `steam_api64.dll` file.
   - Replace it with the emulator version from the `experimental` folder (keep a backup of the original by renaming it).
   - Copy the generated `steam_settings` folder to the same location.

4. **Troubleshooting:** If the game doesn't start or there are issues with the emulator, check [this guide](https://rentry.co/goldberg_emulator) for additional setup instructions.

### 2. Set Up Achievement Watchdog

1. Download the latest release of Achievement Watchdog from the **releases page** (URL pending).
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