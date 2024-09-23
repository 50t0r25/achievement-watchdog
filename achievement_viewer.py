import os
import json
import glob
import argparse
from datetime import datetime, timezone
from colorama import init, Fore
from dotenv import load_dotenv # type: ignore

# Load environment variables from the .env file
load_dotenv()

# Initialize colorama for colored output
init(autoreset=True)

# Function to convert Unix time to a readable format
def convert_from_unixtime(unix_time):
    return (Fore.GREEN + datetime.fromtimestamp(unix_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            if unix_time > 0 else Fore.CYAN + "Not Earned")

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-nohide", action="store_true", help="Show hidden achievements descriptions")
args = parser.parse_args()

# Load paths from environment variables (with defaults)
local_achievements_path = os.getenv("LOCAL_ACHIEVEMENTS_PATH", r"%appdata%\GSE saves")
games_path = os.getenv("GAMES_PATH", r"C:\games")

# Resolve environment variables like %appdata% to actual paths
local_achievements_path = os.path.expandvars(local_achievements_path)
games_path = os.path.expandvars(games_path)

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

# Find matching games with steam_appid.txt (normal mode)
matching_games = []
appid_files = glob.glob(f"{games_path}/**/steam_appid.txt", recursive=True)

for folder in os.listdir(local_achievements_path):
    folder_name = folder
    for appid_file in appid_files:
        with open(appid_file, 'r', encoding='utf-8') as f:
            if f.read().strip() == folder_name:
                root_folder = os.path.relpath(os.path.dirname(appid_file), games_path).split(os.sep)[0]
                matching_games.append({
                    "name": folder_name,
                    "root_folder": root_folder,
                    "local_folder": os.path.join(local_achievements_path, folder_name),
                    "game_achievements_path": os.path.join(os.path.dirname(appid_file), "achievements.json")
                })

# Clear the screen
os.system('cls' if os.name == 'nt' else 'clear')

# Display the list of matching games or exit if none found
if not matching_games:
    print(Fore.RED + "No games found with matching steam_appid.txt files.")
    exit()

print(Fore.WHITE + "Found achievements support for the following installed games:")
for i, game in enumerate(matching_games, 1):
    print(Fore.WHITE + f"{i}. " + Fore.CYAN + f"{game['root_folder']} ({game['name']})")

# Ask the user to select a game
try:
    selected_game = matching_games[int(input(Fore.WHITE + "\nChoose game to view achievements for: ")) - 1]
except (ValueError, IndexError):
    print(Fore.RED + "Invalid selection. Exiting.")
    exit()

# Load local and game achievements
local_achievements_path = os.path.join(selected_game['local_folder'], "achievements.json")
if not os.path.exists(local_achievements_path) or not os.path.exists(selected_game['game_achievements_path']):
    print(Fore.RED + "\nMissing achievements.json in local or games folder.")
    exit()

local_achievements = load_json(local_achievements_path)
game_achievements = load_json(selected_game['game_achievements_path'])

# Display achievements and earned status
earned_achievements = sum(1 for ach in local_achievements.values() if ach['earned'])
total_achievements = len(game_achievements)

print(Fore.WHITE + "\n--------------------------------------\n")

for game_achievement in game_achievements:
    achievement_name = game_achievement['name']
    local_achievement = local_achievements.get(achievement_name)

    if local_achievement:
        earned = local_achievement['earned']
        earned_time = convert_from_unixtime(local_achievement['earned_time'])

        # Display achievement details
        print(Fore.WHITE + "Achievement: " + Fore.CYAN + game_achievement['displayName']['english'])

        if game_achievement.get('hidden', 0) == 1 and not earned and not args.nohide:
            print(Fore.YELLOW + "This achievement is hidden.")
        else:
            print(Fore.WHITE + "Description: " + Fore.CYAN + game_achievement['description']['english'])

        print(Fore.WHITE + "Earned: " + (Fore.GREEN if earned else Fore.RED) + ('Yes' if earned else 'No') + Fore.WHITE + " | Earned Time: " + (Fore.GREEN if earned else Fore.CYAN) + earned_time)
        print(Fore.WHITE + "\n--------------------------------------\n")

# Display the percentage of achievements earned
print(Fore.WHITE + f"Earned: {Fore.YELLOW}{earned_achievements / total_achievements * 100:.1f}% " +
      Fore.WHITE + f"({earned_achievements}/{total_achievements})")

input(Fore.WHITE + "\nPress Enter to exit...")