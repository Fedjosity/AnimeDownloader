# grequests removed - causes gevent conflicts with ThreadPoolExecutor
# import grequests
import tqdm
import os
import kwik_token   # Import kwik_token module
import pahe         # Import animepahe module
from colorama import Fore

from simple_term_menu import TerminalMenu



# Function to extract anime titles and year to show in menu
def get_titles_from_result(list_of_anime):
    """
    Horimiya - 2021 (TV)
    """
    return [ f"{anime[0]} - {anime[4]} ({anime[1]})" for anime in list_of_anime ]


# Function to replace special characters in a string
def replace_special_characters(input_string, replacement="_"):
    special_characters = "!@#$%^&*()_+{}[]|\\:;<>,.?/~` "
    for char in special_characters:
        input_string = input_string.replace(char, replacement)
    return input_string



# Set the Current Working Directory to this script directory
script_directory = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_directory)

# Input: Search for anime
query = input("Search anime : ")
list_of_anime = pahe.search_apahe(query)

# exit if no anime found. 
if len(list_of_anime) == 0:
    print("No anime found.!")
    exit()


# Display search results
list_of_titles = get_titles_from_result(list_of_anime)

# menu to select searched anime
terminal_menu = TerminalMenu(menu_entries=list_of_titles)
choice = terminal_menu.show()
# get the selected anime of choice
selected_anime = list_of_anime[choice]


# get the selected anime_id
anime_id = selected_anime[6]

# get the actual total number of episodes from the release API
print("Fetching actual episode count...")
total_episodes = pahe.get_actual_episode_count(session_id=anime_id)
if total_episodes == 0:
    # Fallback to search API value if we can't get actual count
    total_episodes = selected_anime[2]
    print(f"Using search API episode count: {total_episodes}")
else:
    print(f"Actual episode count: {total_episodes}")


# print the selected anime details to terminal
print("Search Result:")
print(Fore.MAGENTA + selected_anime[0], 
    " - ", selected_anime[4],
    "\n" + Fore.CYAN + "Type:", selected_anime[1],
    "\n" + Fore.YELLOW + "Rating:", + selected_anime[5], 
    "\n" + Fore.GREEN + "Episodes:",Fore.GREEN + str(total_episodes)
)
# reset the foreground text color
print(Fore.RESET, end="")

# loop until valid episode range is provided. 
is_not_valid_range = True
while is_not_valid_range:

    # Input: Choose episode range
    episode_range = input("Enter Range of Episodes (default all) : ")


    # if no range is provided, default to all episodes
    if episode_range == '' or episode_range.lower() == 'all'.lower():
        episode_range = [1, total_episodes]
    # else parse the range to a list
    else:
        episode_range = episode_range.split('-')


    # convert list to tuple of integers
    episode_range = (
        # if two values are provided, use them as start and end
        [int(episode_range[0]), int(episode_range[1])]
        if len(episode_range) == 2 
        # if one value is provided, use it as start and end
        else [int(episode_range[0]), int(episode_range[0])]
    )

    # check if episode_range is valid
    if episode_range[0] < 1 or episode_range[0] > total_episodes or episode_range[1] > total_episodes :
        print(f"{Fore.RED}Episode range exceeds total number of episodes. \nSelect a valid range.")
        print(Fore.RESET, end="")
    else:
        is_not_valid_range = False


# show the selected episode range
print("Episode Range : ", episode_range)



# Fetch episode IDs
# mid_apahe now returns list of tuples: [(episode_number, session_id), ...]
episode_data = pahe.mid_apahe(session_id=anime_id, episode_range=episode_range)

print(f"Found {len(episode_data)} episode(s) in API response")

# Extract session IDs and create mapping from index to episode number
episode_ids = []
episode_index_to_number = {}  # Maps index in episode_ids to actual episode number
for idx, (ep_num, session_id) in enumerate(episode_data):
    episode_ids.append(session_id)
    episode_index_to_number[idx] = ep_num

print(f"Fetching download links for {len(episode_ids)} episode(s)...")

# Fetch episode download links
episodes_data = pahe.dl_apahe1(anime_id=anime_id, episode_ids=episode_ids)

print(f"Successfully fetched download links for {len(episodes_data)} episode(s)")
if len(episodes_data) < len(episode_ids):
    failed_indices = set(range(len(episode_ids))) - set(episodes_data.keys())
    failed_episodes = [episode_index_to_number[idx] for idx in failed_indices if idx in episode_index_to_number]
    print(f"Warning: {len(failed_indices)} episode(s) failed to fetch: {failed_episodes}")


# Organize episode data
# episodes_data keys are indices (0, 1, 2, ...) corresponding to episode_ids list
# We need to map these indices to actual episode numbers using episode_index_to_number
episodes = {}
# Sort the keys to ensure we process episodes in order
for key in sorted(episodes_data.keys()):
    # key is the index in episode_ids list (0-based)
    # Map it to the actual episode number using our mapping
    if key in episode_index_to_number:
        episode_number = episode_index_to_number[key]
        value = episodes_data[key]
        sorted_links = {}
        for link_info in value:
            link, size, lang = link_info
            size = int(size.split('p')[0])
            if lang == '':
                lang = 'jpn'
            if lang not in sorted_links:
                sorted_links[lang] = {}
            if size not in sorted_links[lang]:
                sorted_links[lang][size] = []
            sorted_links[lang][size].append(link)
        episodes[episode_number] = sorted_links



# Input: Choose language and quality
available_langs=list(episodes[episode_range[0]].keys())
print("Languages Available :")
terminal_menu = TerminalMenu(menu_entries=available_langs)
lang = terminal_menu.show()
lang = available_langs[lang]


available_quality = list(episodes[episode_range[0]][lang])
# sorting the quality list to show the highest quality first
available_quality.sort(reverse=True)
available_quality = [ str(i) for i in available_quality ]


print("Quality Available :")
terminal_menu = TerminalMenu(menu_entries=available_quality)
quality = int(terminal_menu.show())
quality = available_quality[quality]


# Update episodes dictionary to contain selected download link
for key, items in episodes.items():
    backup_quality=list(episodes[key][lang])[-1]
    try:
        episodes[key] = episodes[key][lang][quality][0]
    except:
        try:
            episodes[key] = episodes[key][lang][backup_quality][0]
        except:
            pass


# Fetch video links
for key, value in tqdm.tqdm(episodes.items(), desc="Parsing links... "):
    episodes[key] = pahe.dl_apahe2(value)


# Confirmation and download initiation
_ = input("\nStarting To Download in current directory. Make sure to connect to Wifi. \nPress Enter to continue...")



# Create a directory for the anime in Downloads directory if it doesn't exist 
title = replace_special_characters(list_of_anime[choice][0])
os.mkdir("Downloads") if not os.path.exists("Downloads") else None, os.chdir("Downloads")
if not os.path.exists(title):
    os.makedirs(title)

print("\nDownloading in ", os.getcwd() + os.sep + title + "\n")

# Download episodes
for key, value in tqdm.tqdm(episodes.items(), desc="Downloading Episodes"):
    destination = os.path.join(title,f"{key}_{lang}_{quality}.mp4")
    download_link = kwik_token.get_dl_link(value)
    pahe.download_file(url=download_link, destination=destination)

