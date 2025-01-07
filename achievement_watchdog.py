import os
import json
import sys
import time
import glob
import threading
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
from pystray import Icon, MenuItem # type: ignore
from PIL import Image # type: ignore
from win11toast import toast
from dotenv import load_dotenv # type: ignore

# Load environment variables from the .env file
load_dotenv()

# Set up logging to a file, clearing the previous log at each launch
logging.basicConfig(filename="achievement_watchdog.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s", filemode='w')

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Function to get the display text for a specific language, with fallback to English
def get_display_text(recent_achievement, key, language):
    # Attempt to get the text in the specified language; fallback to English if not available
    return recent_achievement.get(key, {}).get(language) or recent_achievement.get(key, {}).get('english', 'Unknown')

# Function to find the most recent earned achievement
def find_recent_achievement(local_achievements):
    return max(
        (ach for ach in local_achievements.items() if ach[1]['earned']),
        key=lambda x: x[1]['earned_time'], default=(None, None)
    )

# Function to scan and map local folders to their corresponding achievements paths in the games directories
def map_local_folders_to_games():
    global local_achievements_path, games_paths
    game_cache = {}

    # Loop through each game path in the list
    for game_path in games_paths:
        # Find all steam_appid.txt files in the current game path
        appid_files = glob.glob(f"{game_path}/**/steam_appid.txt", recursive=True)

        # Go through each folder in the local achievements path
        for folder in os.listdir(local_achievements_path):
            folder_name = folder
            folder_path = os.path.join(local_achievements_path, folder)

            # Ensure it's a directory and has an achievements.json file inside it
            local_achievements_file = os.path.join(folder_path, "achievements.json")
            if not os.path.isdir(folder_path) or not os.path.exists(local_achievements_file):
                continue  # Skip folders without achievements.json

            # Find the corresponding steam_appid.txt in the games folder
            for appid_file in appid_files:
                with open(appid_file, 'r', encoding='utf-8') as f:
                    appid = f.read().strip()

                    # Check if the appid matches the local achievements folder name
                    if appid == folder_name:
                        # Find the achievements.json in the same folder as steam_appid.txt
                        game_achievements_file = os.path.join(os.path.dirname(appid_file), "achievements.json")
                        if os.path.exists(game_achievements_file):
                            # Load the local achievements.json and find the most recent earned achievement
                            local_achievements = load_json(local_achievements_file)
                            recent_achievement = find_recent_achievement(local_achievements)
                            last_earned_time = recent_achievement[1]['earned_time'] if recent_achievement[1] else 0

                            # Cache the path to the game's achievements.json and the last earned timestamp
                            game_cache[folder_name] = {
                                "achievements_path": game_achievements_file,
                                "last_earned_time": last_earned_time
                            }

                            # Move on to the next local folder once the match is found
                            break

    # Log the game cache or log a message if no games were found
    if game_cache:
        logging.info(f"Game Cache loaded - {game_cache}")
    else:
        logging.warning("No games to map have been found. Game Cache is empty.")

    return game_cache

# Watchdog handler class
class AchievementHandler(FileSystemEventHandler):
    def __init__(self, game_cache):
        super().__init__()
        self.game_cache = game_cache
        self.language = os.getenv('LANGUAGE', 'english')  # Load the language from the environment variable

    def on_modified(self, event):
        self.process_achievement_file(event)

    def on_created(self, event):
        self.process_achievement_file(event)

    def process_achievement_file(self, event):
        # Check if what was modified/created is a folder
        if event.is_directory or os.path.basename(event.src_path) != "achievements.json":
            return
        
        # Log every file modification/creation event
        logging.info(f"File modified: {event.src_path}")

        folder_name = os.path.basename(os.path.dirname(event.src_path))

        # Check if the folder is in our cache
        if folder_name not in self.game_cache:
            # If the folder is not in the cache, attempt to add it
            logging.info(f"Folder {folder_name} not in cache. Attempting to add.")

            # Loop through each game path to find the steam_appid.txt file
            for game_path in games_paths:
                appid_files = glob.glob(f"{game_path}/**/steam_appid.txt", recursive=True)
                for appid_file in appid_files:
                    with open(appid_file, 'r', encoding='utf-8') as f:
                        if f.read().strip() == folder_name:
                            game_achievements_path = os.path.join(os.path.dirname(appid_file), "achievements.json")

                            # Cache the achievements path and last earned achievement's timestamp
                            self.game_cache[folder_name] = {
                                "achievements_path": game_achievements_path,
                                "last_earned_time": 0  # Always attempt sending a notification for newly added achievements files
                            }
                            logging.info(f"Added {folder_name} to cache with achievements path {game_achievements_path}")
                            break
                else:
                    # Continue to the next game path if not found in the current one
                    continue
                # If found, break out of the outer loop
                break
            else:
                logging.error(f"Unable to find matching appid for folder {folder_name}. Skipping.")
                return

        # Process achievements in the cached folder
        game_data = self.game_cache[folder_name]
        local_achievements = load_json(event.src_path)

        # Loop through all achievements and find those that are newly earned
        new_achievements = [
            (name, data) for name, data in local_achievements.items()
            if data['earned'] and data['earned_time'] > game_data['last_earned_time']
        ]

        if not new_achievements:
            logging.info(f"No new achievements found for {folder_name}. Last earned achievement is up to date.")
            return  # No new achievements found
        
        try:
            game_achievements = load_json(game_data["achievements_path"])

            for achievement_name, achievement_data in new_achievements:
                recent_achievement = next((ach for ach in game_achievements if ach['name'] == achievement_name), None)
                
                if recent_achievement:
                    icon_path = recent_achievement.get('icon', None)
                    if icon_path:
                        icon_path = os.path.join(os.path.dirname(game_data["achievements_path"]), icon_path)

                    title = get_display_text(recent_achievement, 'displayName', self.language)
                    description = get_display_text(recent_achievement, 'description', self.language)

                    asyncio.run(self.send_notification(title, description, icon_path))

                    # Update the last earned timestamp in cache to the latest achievement
                    if achievement_data['earned_time'] > game_data['last_earned_time']:
                        self.game_cache[folder_name]['last_earned_time'] = achievement_data['earned_time']

        except Exception as e:
            logging.error(f"Error loading achievements.json for folder {folder_name}: {e}")

    # Async function to display toast notifications
    async def send_notification(self, title, description, icon_path=None):
        try:
            icon = {'src': icon_path, 'placement': 'appLogoOverride'} if icon_path else None
            toast(title, description, icon=icon, audio=r"achievement_sound.mp3", app_id="Achievement Unlocked")
            logging.info(f"Notification sent: {title} - {description}")
        except Exception as e:
            logging.error(f"Error displaying notification: {e}")

# Function to stop watchdog observer and exit
def stop_watchdog(observer, icon):
    logging.info("Stopping Watchdog...")
    observer.stop()
    observer.join()
    icon.stop()

def resource_path(relative_path):
    """ Get absolute path to resource, works for both dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Function to start system tray
def start_tray(observer):
    # Load the tray icon image
    image_path = resource_path("achievement.png")
    image = Image.open(image_path)

    # System tray quit action
    def on_quit(icon, item):
        stop_watchdog(observer, icon)

    # Create system tray icon
    menu = (MenuItem('Quit', on_quit),)
    icon = Icon("achievement_icon", image, title="Achievement Watchdog", menu=menu)
    icon.run()

# Main watchdog function
def run_watchdog_mode():
    # Scan the existing folders and create the cache
    game_cache = map_local_folders_to_games()

    logging.info("Running Watchdog, monitoring for achievement changes...")

    observer = Observer()
    event_handler = AchievementHandler(game_cache)

    # Watch the entire local achievements path for changes
    observer.schedule(event_handler, path=local_achievements_path, recursive=True)
    observer.start()

    # Run the system tray icon in a separate thread
    tray_thread = threading.Thread(target=start_tray, args=(observer,), daemon=True)
    tray_thread.start()

    try:
        while tray_thread.is_alive():
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_watchdog(observer, None)

# Load paths from environment variables (with defaults)
local_achievements_path = os.getenv("LOCAL_ACHIEVEMENTS_PATH", r"%appdata%\GSE saves")
games_paths = os.getenv("GAMES_PATH", r"C:\games").split(';')

# Resolve environment variables like %appdata% to actual paths
local_achievements_path = os.path.expandvars(local_achievements_path)
games_paths = [os.path.expandvars(path.strip()) for path in games_paths]

# Run the watchdog mode by default
run_watchdog_mode()