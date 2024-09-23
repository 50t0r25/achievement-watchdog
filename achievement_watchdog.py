import os
import json
import sys
import time
import glob
import threading
import logging
from datetime import datetime, timezone
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

# Function to find the most recent earned achievement
def find_recent_achievement(local_achievements):
    return max(
        (ach for ach in local_achievements.items() if ach[1]['earned']),
        key=lambda x: x[1]['earned_time'], default=(None, None)
    )[0]

# Function to scan and map local folders to their corresponding achievements paths in the games directory
def map_local_folders_to_games():
    game_cache = {}
    appid_files = glob.glob(f"{games_path}/**/steam_appid.txt", recursive=True)

    for folder in os.listdir(local_achievements_path):
        folder_name = folder
        folder_path = os.path.join(local_achievements_path, folder)
        if not os.path.isdir(folder_path):
            continue

        # Search for the matching appid in the games folder
        for appid_file in appid_files:
            with open(appid_file, 'r', encoding='utf-8') as f:
                if f.read().strip() == folder_name:
                    game_achievements_path = os.path.join(os.path.dirname(appid_file), "achievements.json")
                    game_cache[folder_name] = game_achievements_path
                    break  # Exit loop once found
    return game_cache

# Watchdog handler class
class AchievementHandler(FileSystemEventHandler):
    def __init__(self, game_cache):
        super().__init__()
        self.game_cache = game_cache
        self.last_achievement = None
        self.last_notification_time = 0

    def on_modified(self, event):
        self.process_achievement_file(event)

    def on_created(self, event):
        self.process_achievement_file(event)

    def process_achievement_file(self, event):
        # Check if what was modified/created is a folder
        if event.is_directory or os.path.basename(event.src_path) != "achievements.json":
            return
        
        # Log every file modification/creation event
        logging.info(f"File created/modified: {event.src_path}")

        folder_name = os.path.basename(os.path.dirname(event.src_path))

        # Check if the folder is in our cache
        if folder_name not in self.game_cache:
            # If the folder is not in the cache, attempt to add it
            logging.info(f"Folder {folder_name} not in cache. Attempting to add.")
            appid_files = glob.glob(f"{games_path}/**/steam_appid.txt", recursive=True)
            for appid_file in appid_files:
                with open(appid_file, 'r', encoding='utf-8') as f:
                    if f.read().strip() == folder_name:
                        game_achievements_path = os.path.join(os.path.dirname(appid_file), "achievements.json")
                        self.game_cache[folder_name] = game_achievements_path
                        logging.info(f"Added {folder_name} to cache with achievements path {game_achievements_path}")
                        break
            else:
                logging.error(f"Unable to find matching appid for folder {folder_name}. Skipping.")
                return

        # Process achievements in the cached folder
        game_achievements_path = self.game_cache[folder_name]
        local_achievements = load_json(event.src_path)
        recent_achievement_name = find_recent_achievement(local_achievements)

        if not recent_achievement_name:
            logging.warning("No recent achievement found in the achievements.json file.")
            return  # No recent achievement found
        
        try:
            game_achievements = load_json(game_achievements_path)
        except Exception as e:
            logging.error(f"Error loading achievements.json for folder {folder_name}: {e}")
            return
        
        recent_achievement = next((ach for ach in game_achievements if ach['name'] == recent_achievement_name), None)

        if recent_achievement and self._check_duplicate(recent_achievement_name):
            icon_path = recent_achievement.get('icon', None)
            if icon_path:
                icon_path = os.path.join(os.path.dirname(game_achievements_path), icon_path)
            asyncio.run(self.send_notification(
                recent_achievement['displayName']['english'],
                recent_achievement['description']['english'],
                icon_path
            ))

    def _check_duplicate(self, achievement_name):
        current_time = time.time()
        if self.last_achievement == achievement_name and current_time - self.last_notification_time < 2:
            logging.info(f"Skipping duplicate notification for {achievement_name}")
            return False
        self.last_achievement, self.last_notification_time = achievement_name, current_time
        return True

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

# Function to start system tray
def resource_path(relative_path):
    """ Get absolute path to resource, works for both dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
    logging.info("Running in Watchdog mode, monitoring for achievement changes...")

    # Scan the existing folders and create the cache
    game_cache = map_local_folders_to_games()

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
games_path = os.getenv("GAMES_PATH", r"C:\games")

# Resolve environment variables like %appdata% to actual paths
local_achievements_path = os.path.expandvars(local_achievements_path)
games_path = os.path.expandvars(games_path)

# Run the watchdog mode by default
run_watchdog_mode()