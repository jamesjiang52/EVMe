import os
import sys
from pprint import pprint
from tqdm import tqdm
from math import floor, ceil
from util import *


def get_speed_benchmarks(mons):
    """
    Returns list of tuples with following structure:
    (speed stat, benchmark_mon_name, benchmark mon_data)

    List is sorted in ascending order of speed stats.
    """
    speeds = []
    for mon_name, mon_data in tqdm(mons.items()):
        for nature, spread in mon_data["Spreads"]:
            stats = get_stats(mon_name, PERFECT_IVS, spread, 50, nature)
            mon_data_out = {
                "Item": "",
                "Ability": "",
                "Spread": (nature, spread)
            }
            speeds.append((stats[5], mon_name, mon_data_out))

            for ability in mon_data["Abilities"]:
                boost = 0
                if ability in PLUS_1_SPEED_ABILITIES:
                    boost = 1
                elif ability in PLUS_2_SPEED_ABILITIES:
                    boost = 2
                elif ability in PLUS_6_SPEED_ABILITIES:
                    boost = 6

                if boost == 0:
                    continue

                mon_data_out = {
                    "Item": "",
                    "Ability": ability,
                    "Spread": (nature, spread)
                }
                speeds.append((modify_stat(stats[5], boost), mon_name, mon_data_out))

            for item in mon_data["Items"]:
                boost = 0
                if item in PLUS_1_SPEED_ITEMS:
                    boost = 1

                if boost == 0:
                    continue

                mon_data_out = {
                    "Item": item,
                    "Ability": "",
                    "Spread": (nature, spread)
                }
                speeds.append((modify_stat(stats[5], boost), mon_name, mon_data_out))

            # handle booster speed
            if max(*stats) == stats[5] and "Protosynthesis" in mon_data["Abilities"] and "Booster Energy Capsule" in mon_data["Items"]:
                mon_data_out = {
                    "Item": "Booster Energy",
                    "Ability": "Protosynthesis",
                    "Spread": (nature, spread)
                }
                speeds.append((modify_stat(stats[5], 1), mon_name, mon_data_out))

    # remove speed ties... probably a more Pythonic way
    seen_speeds = set()
    speeds_uniq = []
    for speed in speeds:
        if speed[0] not in seen_speeds:
            speeds_uniq.append(speed)
            seen_speeds.add(speed[0])

    return sorted(speeds_uniq, key=lambda x: x[0])


def allocate_speed_EVs(mon_name, mon_data, speed_benchmarks, tailwind=False, trick_room=False):
    """
    Returns list of tuples with following structure:
    (speed EVs, boosting nature required?, benchmark mon_name, benchmark mon_data)
    """
    # TODO: (improvement) handle trick room option better
    if trick_room:
        return []  # just allocate 0 speed EVs

    boost = 0
    if "Ability" in mon_data and mon_data["Ability"] in PLUS_1_SPEED_ABILITIES:
        boost = 1
    elif "Ability" in mon_data and mon_data["Ability"] in PLUS_2_SPEED_ABILITIES:
        boost = 2
    elif "Ability" in mon_data and mon_data["Ability"] in PLUS_6_SPEED_ABILITIES:
        boost = 6
    elif "Item" in mon_data and mon_data["Item"] in PLUS_1_SPEED_ITEMS:
        boost = 1

    if tailwind:
        max_speed = 2*modify_stat(get_stats(mon_name, PERFECT_IVS, (0, 0, 0, 0, 0, 252), 50, "Timid")[5], boost)
        min_speed = 2*(ceil(max_speed/1.1) - 32)
    else:
        max_speed = modify_stat(get_stats(mon_name, PERFECT_IVS, (0, 0, 0, 0, 0, 252), 50, "Timid")[5], boost)
        min_speed = (ceil(max_speed/1.1) - 32)

    max_speed_index = -1
    min_speed_index = -1
    for i in range(len(speed_benchmarks)):
        if min_speed <= speed_benchmarks[i][0]:
            if min_speed_index == -1:
                min_speed_index = i

        if max_speed <= speed_benchmarks[i][0]:
            break
        else:
            max_speed_index = i

    if min_speed_index == -1 or max_speed_index == -1 or max_speed_index < min_speed_index:
        # speed can't be optimized, leave 0 EVs in speed
        # either the next speed benchmark is too high, or is non-existent (Pokemon already outspeeds everything)
        return []

    speed_EVs = []
    speed_benchmarks = speed_benchmarks[min_speed_index:max_speed_index + 1]

    for i in range(len(speed_benchmarks)):
        benchmark = speed_benchmarks[i][0]
        speed_diff = benchmark - min_speed
        if speed_diff > 31:  # can't reach benchmark speed with neutral nature
            break

        EVs = 4 + 8*speed_diff
        speed_EVs.append((EVs, False, *speed_benchmarks[i][1:3]))

    for i in range(len(speed_benchmarks)):
        benchmark = speed_benchmarks[i][0]
        min_speed_boost = floor(1.1*(ceil(max_speed/1.1) - 32))
        speed_diff = benchmark - min_speed_boost
        if speed_diff <= 0:
            continue
        
        speed_diff = ceil((benchmark + 1)/1.1) - min_speed
        EVs = 4 + 8*(speed_diff - 1)
        speed_EVs.append((EVs, True, *speed_benchmarks[i][1:3]))

    return speed_EVs


if __name__ == "__main__":
    meta_mons = {
        "Flutter Mane": {
            "Abilities": ["Protosynthesis"],
            "Items": ["Booster Energy", "Choice Specs"],
            "Spreads": [("Modest", (0, 0, 4, 252, 0, 252)), ("Timid", (204, 0, 116, 148, 4, 36))],
            "Moves": ["Moonblast", "Dazzling Gleam", "Shadow Ball", "Icy Wind", "Thunderbolt"]
        },
        "Landorus-Therian": {
            "Abilities": ["Intimidate"],
            "Items": ["Choice Scarf", "Assault Vest"],
            "Spreads": [("Adamant", (4, 252, 0, 0, 0, 252)), ("Jolly", (4, 252, 0, 0, 0, 252))],
            "Moves": ["Stomping Tantrum", "Rock Slide", "U-turn"]
        }
    }
    mon_name = "Ninetales-Alola"
    mon_data = {"Ability": "Snow Warning", "Item": "Light Clay"}
    
    speed_benchmarks = get_speed_benchmarks(meta_mons)
    #pprint(speed_benchmarks)
    pprint(allocate_speed_EVs(mon_name, mon_data, speed_benchmarks, tailwind=False))
    pprint(allocate_speed_EVs(mon_name, mon_data, speed_benchmarks, tailwind=True))
