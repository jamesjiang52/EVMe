import os
import sys
import subprocess
import dirtyjson
from math import floor


# cutoff % for Pokemon's ability to be considered meta
# mostly used to filter out teambuilding mistakes, e.g. 0.02% Incineroar with Blaze
ABILITY_THRESHOLD = 10

# max number of top items per Pokemon to include
MAX_NUM_ITEMS = 3

# max number of top EV spreads per Pokemon to include
MAX_NUM_SPREADS = 3

# cutoff % for a Pokemon's move to be considered meta
MOVE_THRESHOLD = 20

PERFECT_IVS = (31, 31, 31, 31, 31, 31)
MIN_ATTACK_IVS = (31, 0, 31, 31, 31, 31)
MIN_SPEED_IVS = (31, 31, 31, 31, 31, 0)
MIN_ATTACK_AND_SPEED_IVS = (31, 0, 31, 31, 0)

BLANK_EVS = (0, 0, 0, 0, 0, 0)

HEAL_1_3_ITEMS = ["Aguav Berry", "Figy Berry", "Iapapa Berry", "Mago Berry", "Wiki Berry"]
HEAL_1_4_ITEMS = ["Sitrus Berry"]
HEAL_1_16_ITEMS = ["Leftovers"]

# TODO: (improvement) handle more speed-boosting moves/abilities
PLUS_1_SPEED_ABILITIES = ["Unburden"]
PLUS_2_SPEED_ABILITIES = ["Chlorophyll", "Sand Rush", "Slush Rush", "Swift Swim", "Surge Surfer"]
PLUS_6_SPEED_ABILITIES = ["Steam Engine"]
PLUS_1_SPEED_ITEMS = ["Choice Scarf"]

STAT_OVERRIDE_MOVES = ["Foul Play", "Body Press", "Psyshock", "Psystrike", "Secret Sword"]

# https://bulbapedia.bulbagarden.net/wiki/Nature#Stat-focused_table
NATURE_MATRIX = [
    ["Hardy", "Lonely", "Adamant", "Naughty", "Brave"],
    ["Bold", "Docile", "Impish", "Lax", "Relaxed"],
    ["Modest", "Mild", "Bashful", "Rash", "Quiet"],
    ["Calm", "Gentle", "Careful", "Quirky", "Sassy"],
    ["Timid", "Hasty", "Jolly", "Naive", "Serious"]
]

STAT_NAMES = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]


def get_move_category(move_name):
    result = subprocess.run([
        "run-func",
        "src/calc.js",
        "get_move_category",
        move_name
    ], stdout=subprocess.PIPE, shell=True)
    return result.stdout.decode("utf-8")


def convert_stats_to_tuple(stats):
    return (stats["hp"], stats["atk"], stats["def"], stats["spa"], stats["spd"], stats["spe"])


def get_stats_from_base(base_stats, EVs, nature):
    stats = list(base_stats)
    
    for i in range(len(NATURE_MATRIX)):
        for j in range(len(NATURE_MATRIX[0])):
            if nature == NATURE_MATRIX[i][j]:
                boosting_index = i + 1
                harmful_index = j + 1
    
    for i in range(len(stats)):
        if EVs[i]:
            if boosting_index == i:
                stats[i] = floor(1.1*(stats[i] + 1 + (EVs[i] - 4)/8))
            elif harmful_index == i:
                stats[i] = floor(0.9*(stats[i] + 1 + (EVs[i] - 4)/8))
            else:
                stats[i] += 1 + (EVs[i] - 4)/8
    
    return tuple(stats)


def get_stats(mon_name, IVs, EVs, level, nature):
    result = subprocess.run([
        "run-func",
        "src/calc.js",
        "get_stats",
        mon_name,
        *[str(i) for i in IVs],
        *[str(i) for i in EVs],
        str(level),
        nature
    ], stdout=subprocess.PIPE, shell=True)
    return convert_stats_to_tuple(dirtyjson.loads(result.stdout.decode("utf-8")))


# https://bulbapedia.bulbagarden.net/wiki/Stat_modifier
def modify_stat(stat, stat_stage):
    num = max(2, 2 + stat_stage)
    denom = max(2, 2 - stat_stage)
    return floor(stat*num/denom)


def do_damage_calc(move_name, attack_mon_name, attack_ability, attack_item, attack_EVs, attack_nature, defend_mon_name, defend_ability, defend_item, defend_EVs, defend_nature, level):
    result = subprocess.run([
        "run-func",
        "src/calc.js",
        "do_damage_calc",
        move_name,
        attack_mon_name,
        attack_ability,
        attack_item,
        attack_nature,
        *[str(EV) for EV in attack_EVs],
        defend_mon_name,
        defend_ability,
        defend_item,
        defend_nature,
        *[str(EV) for EV in defend_EVs],
        str(level)
    ], stdout=subprocess.PIPE, shell=True)

    #print(result.stdout.decode("utf-8"))
    result = dirtyjson.loads(result.stdout.decode("utf-8"))
    result["Attacker stats"] = convert_stats_to_tuple(result["Attacker stats"])
    result["Defender stats"] = convert_stats_to_tuple(result["Defender stats"])
    return result


if __name__ == "__main__":
    print(get_stats("Flutter Mane", MIN_ATTACK_IVS, (0, 0, 4, 252, 0, 252), 50, "Timid"))
    #print(do_damage_calc("Moonblast", "Flutter Mane", "Protosynthesis", "Choice Specs", (0, 0, 4, 252, 0, 252), "Modest", "Ninetales-Alola", "Snow Warning", "Light Clay", (4, 0, 0, 252, 0, 252), "Timid", 50))
    print(do_damage_calc("Body Press", "Goodra-Hisui", "Shell Armor", "Lefovers", (252, 0, 252, 0, 4, 0), "Bold", "Ninetales-Alola", "Snow Warning", "Light Clay", (4, 0, 0, 252, 0, 252), "Timid", 50))
