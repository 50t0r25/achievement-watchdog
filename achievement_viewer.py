import os
import sys
import json
import glob
import argparse
from datetime import datetime
from colorama import init, Fore
from dotenv import load_dotenv # type: ignore

# Load environment variables from the .env file
load_dotenv()

# Initialize colorama for colored output
init(autoreset=True)

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-nohide", action="store_true", help="Show hidden achievements descriptions")
parser.add_argument("-nocolor", action="store_true", help="Disable colored output")
args = parser.parse_args()

# If the -nocolor argument is provided, set all colors to white or empty
if args.nocolor:
    Fore.GREEN = ""
    Fore.CYAN = ""
    Fore.YELLOW = ""
    Fore.LIGHTRED_EX = ""
    Fore.WHITE = ""
else:
    Fore.GREEN = Fore.GREEN
    Fore.CYAN = Fore.CYAN
    Fore.YELLOW = Fore.YELLOW
    Fore.LIGHTRED_EX = Fore.LIGHTRED_EX
    Fore.WHITE = Fore.WHITE

# Function to convert Unix time to a readable format
def convert_from_unixtime(unix_time):
    return (Fore.GREEN + datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
            if unix_time > 0 else Fore.CYAN + "Not Earned")

# Load paths from environment variables (with defaults)
local_achievements_path = os.getenv("LOCAL_ACHIEVEMENTS_PATH", r"%appdata%\GSE saves")
games_paths = os.getenv("GAMES_PATH", r"C:\games").split(';')  # Support multiple paths separated by ';'

# Load the preferred language from the environment variable (default to 'english')
preferred_language = os.getenv('LANGUAGE', 'english')

# Resolve environment variables like %appdata% to actual paths
local_achievements_path = os.path.expandvars(local_achievements_path)
games_paths = [os.path.expandvars(path.strip()) for path in games_paths]

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Function to get the achievement text in the preferred language, with a fallback to English
def get_achievement_text(recent_achievement, key):
    return recent_achievement.get(key, {}).get(preferred_language) or \
           recent_achievement.get(key, {}).get('english', 'Unknown')

# Find matching games with steam_appid.txt in all game paths
matching_games = []

for game_path in games_paths:
    appid_files = glob.glob(f"{game_path}/**/steam_appid.txt", recursive=True)

    for folder in os.listdir(local_achievements_path):
        folder_name = folder
        for appid_file in appid_files:
            with open(appid_file, 'r', encoding='utf-8') as f:
                if f.read().strip() == folder_name:
                    root_folder = os.path.relpath(os.path.dirname(appid_file), game_path).split(os.sep)[0]
                    matching_games.append({
                        "name": folder_name,
                        "root_folder": root_folder,
                        "local_folder": os.path.join(local_achievements_path, folder_name),
                        "game_achievements_path": os.path.join(os.path.dirname(appid_file), "achievements.json")
                    })

# Display the list of matching games or exit if none found
if not matching_games:
    print(Fore.LIGHTRED_EX + "No games found with matching steam_appid.txt files.")
    input(Fore.WHITE + "\nPress Enter to exit...")
    sys.exit()

print(Fore.WHITE + "Found achievements support for the following installed games:")
for i, game in enumerate(matching_games, 1):
    print(Fore.WHITE + f"{i}. " + Fore.CYAN + f"{game['root_folder']} ({game['name']})")

# Ask the user to select a game
try:
    selected_game = matching_games[int(input(Fore.WHITE + "\nChoose game to view achievements for: ")) - 1]
except (ValueError, IndexError):
    print(Fore.LIGHTRED_EX + "\nInvalid selection.")
    input(Fore.WHITE + "\nPress Enter to exit...")
    sys.exit()

# Load local and game achievements
local_achievements_path = os.path.join(selected_game['local_folder'], "achievements.json")
if not os.path.exists(local_achievements_path) or not os.path.exists(selected_game['game_achievements_path']):
    print(Fore.LIGHTRED_EX + "\nMissing achievements.json in local or games folder.")
    input(Fore.WHITE + "\nPress Enter to exit...")
    sys.exit()

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

        # Display achievement details using the preferred language with a fallback to English
        print(Fore.WHITE + "Achievement: " + Fore.CYAN + get_achievement_text(game_achievement, 'displayName'))

        if game_achievement.get('hidden', 0) == 1 and not earned and not args.nohide:
            print(Fore.YELLOW + "This achievement is hidden.")
        else:
            print(Fore.WHITE + "Description: " + Fore.CYAN + get_achievement_text(game_achievement, 'description'))

        # Check for progress tracking
        if 'progress' in local_achievement and 'max_progress' in local_achievement:
            max_progress = local_achievement['max_progress']
            progress = max_progress if earned else local_achievement['progress']
            progress_percent = 100.0 if earned else (progress / max_progress) * 100
            print(Fore.WHITE + "Progress: " + (Fore.GREEN if earned else Fore.LIGHTRED_EX) + f"{progress_percent:.1f}% ({progress}/{max_progress})")

        print(Fore.WHITE + "Earned: " + (Fore.GREEN if earned else Fore.LIGHTRED_EX) + ('Yes' if earned else 'No') + Fore.WHITE + " | Earned Time: " + (Fore.GREEN if earned else Fore.CYAN) + earned_time)
        print(Fore.WHITE + "\n--------------------------------------\n")

# Display the percentage of achievements earned
print(Fore.WHITE + f"Earned: {Fore.YELLOW}{earned_achievements / total_achievements * 100:.1f}% " +
      Fore.WHITE + f"({earned_achievements}/{total_achievements})")

input(Fore.WHITE + "\nPress Enter to exit...")