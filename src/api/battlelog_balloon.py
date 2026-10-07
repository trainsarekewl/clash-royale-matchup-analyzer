import shutil
import urllib.request
import json
from urllib.error import HTTPError
from urllib.parse import quote
from pathlib import Path

from dotenv import load_dotenv
import os

from fsspec.utils import other_paths

load_dotenv()

key = os.getenv("KEY")
player_raw_tags = os.getenv("PLAYER_TAGS")
my_raw_tag = os.getenv("MY_TAG")
my_tag = quote(my_raw_tag)
player_tags_list = []
data = []

for raw_tag in player_raw_tags.split(","):
    player_tags_list.append(quote(raw_tag))

# paths
base_url = "https://api.clashroyale.com/v1"

target_deck = {"Musketeer","Skeletons","Giant Snowball","Bomb Tower",
               "Balloon","Miner","Ice Golem","Barbarian Barrel"}

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ASSETS_DIR = BASE_DIR / "assets"
EXPORTS_DIR = BASE_DIR / "exports"

ASSETS_MASTER = ASSETS_DIR / "battlelog_balloon.json"
EXPORT_MASTER = EXPORTS_DIR / "battlelog_balloon.json"
EXPORT_ME = EXPORTS_DIR / "my_battlelog_balloon.json"
EXPORT_OTHERS = EXPORTS_DIR / "topplayers_battlelog_balloon.json"


def fetch_battlelog(tag_list):
    for tag in tag_list:
        endpoint = f"/players/{tag}/battlelog"

        request = urllib.request.Request(
            base_url + endpoint,
            None,
            headers={
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "User-Agent": "python-urllib"
            }
        )

        try:
            response = urllib.request.urlopen(request).read().decode("utf-8")
        except HTTPError as e:
            print(e.code, e.read().decode())
            continue

        data.extend(json.loads(response))
    return data

def build_master(data):
    # add more to battle log
    if os.path.exists(ASSETS_MASTER):
        with open(ASSETS_MASTER, "r", encoding = "utf-8") as f:
            old_data = json.load(f)

    else:
        old_data = []

    merged = data + old_data
    seen = set()
    unique = []

    # create battle log
    for battle in merged:
        battle_id = battle["team"][0]["tag"] + ": " + battle.get("battleTime")
        battle_type = battle.get("type")

        opponent_battle_deck = {card["name"] for card in battle["opponent"][0]["cards"]}
        battle_deck = {card["name"] for card in battle["team"][0]["cards"]}

        # make sure it is ranked, using the correct deck, opponent using different deck, and not duplicate
        if (battle_id not in seen
            and battle_type == "pathOfLegend"
            and battle_deck == target_deck
            and opponent_battle_deck != target_deck):

            seen.add(battle_id)
            unique.append(battle)

    print(f"Battlelog size: {len(unique)}")
    with open(ASSETS_MASTER, "w", encoding = "utf-8") as f:
        json.dump(unique, f, indent=4)

def export_splits():
    shutil.copyfile(ASSETS_MASTER, EXPORT_MASTER)

    with open(ASSETS_MASTER, "r", encoding = "utf-8") as f:
        data = json.load(f)

    mine = [battle for battle in data if battle["team"][0]["tag"] == my_raw_tag]
    others = [battle for battle in data if battle["team"][0]["tag"] != my_raw_tag]

    with open(EXPORT_ME, "w", encoding="utf-8") as f:
        json.dump(mine, f, indent=4)

    with open(EXPORT_OTHERS, "w", encoding="utf-8") as f:
        json.dump(others, f, indent=4)

    print("Mine:", len(mine), "Others:", len(others))


def getData():
    raw = fetch_battlelog(player_tags_list)
    build_master(raw)
    export_splits()

getData()