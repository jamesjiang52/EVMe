import os
import sys
import requests
from pprint import pprint
from itertools import product
from util import *


def get_mons(file_url, num_mons=12):
    """
    Parse required mon data from a Smogon moveset URL.
    """
    resp = requests.get(file_url)
    lines = [line.strip()[1:-1].strip() for line in resp.text.split("\n")]
    lines = lines[1:]  # skip first line

    mons = {}
    mon_curr = {}
    mon_curr_name = None
    mon_curr_abilities = []
    mon_curr_items = []
    mon_curr_spreads = []
    mon_curr_moves = []
    num_items_seen = 0
    num_spreads_seen = 0
    num_mons_seen = 0
    num_separators_seen = 0

    for line in lines:
        if "-----" in line:
            if num_separators_seen == 8:
                mon_curr["Abilities"] = mon_curr_abilities
                mon_curr["Items"] = mon_curr_items
                mon_curr["Spreads"] = mon_curr_spreads
                mon_curr["Moves"] = mon_curr_moves
                mons[mon_curr_name] = mon_curr

                num_mons_seen += 1
                if num_mons_seen >= num_mons:
                    break

                mon_curr = {}
                mon_curr_name = None
                mon_curr_abilities = []
                mon_curr_items = []
                mon_curr_spreads = []
                mon_curr_moves = []
                num_items_seen = 0
                num_spreads_seen = 0
                num_separators_seen = 0
            else:
                num_separators_seen += 1

            continue

        if num_separators_seen == 0:  # name
            mon_curr_name = line

        elif num_separators_seen == 1:  # misc meta data
            continue

        elif num_separators_seen == 2:  # abilities
            if line != "Abilities":
                words = line.split()
                percent = float(words[-1][:-1])
                ability = " ".join(words[:-1])
                if percent > ABILITY_THRESHOLD and ability != "Other":
                    mon_curr_abilities.append(ability)

        elif num_separators_seen == 3:  # items
            if line != "Items":
                if num_items_seen < MAX_NUM_ITEMS:
                    item = " ".join(line.split()[:-1])
                    if item != "Other":
                        mon_curr_items.append(item)
                        num_items_seen += 1

        elif num_separators_seen == 4:  # EV spreads
            if line != "Spreads":
                if num_spreads_seen < MAX_NUM_SPREADS:
                    spread = line.split()[0]
                    if spread != "Other":
                        nature, spread = tuple(spread.split(":"))
                        spread = tuple([int(i) for i in spread.split("/")])
                        mon_curr_spreads.append((nature, spread))
                        num_spreads_seen += 1

        elif num_separators_seen == 5:  # moves
            if line != "Moves":
                words = line.split()
                percent = float(words[-1][:-1])
                move = " ".join(words[:-1])
                if percent > MOVE_THRESHOLD and move != "Other":
                    mon_curr_moves.append(move)

        else:  # teammates, checks + counters
            continue

    # assume NUM_MONS < number of Pokemon listed in file
    # if not, need to manually add last Pokemon

    return mons


def process_damage_rolls(max_hp, damage_rolls, hko_level, sitrus_berry=False, leftovers=False):
    """
    Extract useful percentages from raw damage rolls from damage calc.
    """
    min_percent = round(100*damage_rolls[0]/max_hp, 1)
    max_percent = round(100*damage_rolls[-1]/max_hp, 1)

    if hko_level == 1:
        pass
    else:
        if sitrus_berry:
            recovery_factor = 1/4
        elif leftovers:
            recovery_factor = 1/16
        else:
            recovery_factor = 0
    
        damage_rolls = product(damage_rolls, repeat=2)
        damage_rolls = sorted([sum(damage) for damage in damage_rolls])
        max_hp += floor(max_hp*recovery_factor)

    if damage_rolls[-1] < max_hp:
        kill_percent = 0.0
    else:  # OHKO/2HKO still possible (but barely)
        kill_percent = round(100*len([roll for roll in damage_rolls if roll >= max_hp])/len(damage_rolls), 1)

    return (min_percent, max_percent, kill_percent)


def print_EV_calcs(mon_name, mon_data, nature, spread, remaining_EVs, attack_EVs, defense_EVs, special_attack_EVs, special_defense_EVs, speed_EVs):
    """
    Print relevant offensive/defensive/speed calcs for the specified EV spread.
    """
    print("="*80)
    print("Suggested nature:           {}".format(nature))
    print("Suggested EV spread:        {} HP / {} Atk / {} Def / {} SpA / {} SpD / {} Spe".format(*spread))
    print("Remaining EVs:              {}\n".format(remaining_EVs))

    attack_benchmark_data = attack_EVs[5]
    if attack_benchmark_data:
        calc = do_damage_calc(
            attack_EVs[3],
            mon_name,
            mon_data["Ability"],
            mon_data["Item"],
            spread,
            nature,
            attack_EVs[4],
            attack_benchmark_data["Ability"],
            attack_benchmark_data["Item"],
            attack_benchmark_data["Spread"][1],
            attack_benchmark_data["Spread"][0],
            50
        )

        # TODO: (improvement) account for Body Press, Foul Play, etc.
        hp = attack_benchmark_data["Spread"][1][0]
        A = spread[1]
        if nature in NATURE_MATRIX[0][1:]:
            modifier_A = "+"
        elif nature in [row[0] for row in NATURE_MATRIX[1:]]:
            modifier_A = "-"
        else:
            modifier_A = ""

        D = attack_benchmark_data["Spread"][1][2]
        if attack_benchmark_data["Spread"][0] in NATURE_MATRIX[1][:1] + NATURE_MATRIX[1][2:]:
            modifier_D = "+"
        elif attack_benchmark_data["Spread"][0] in [row[1] for row in NATURE_MATRIX[:1] + NATURE_MATRIX[2:]]:
            modifier_D = "-"
        else:
            modifier_D = ""
        
        sitrus_berry = False
        leftovers = False
        if attack_benchmark_data["Item"] in HEAL_1_16_ITEMS:
            leftovers = True
        elif attack_benchmark_data["Item"] in HEAL_1_4_ITEMS:
            sitrus_berry = True

        min_percent, max_percent, kill_percent = process_damage_rolls(calc["Defender stats"][0], calc["Damage rolls"], attack_EVs[2], sitrus_berry=sitrus_berry, leftovers=leftovers)
        if attack_EVs[2] == 1:
            hko = "O"
        else:
            hko = "2"

        print("Attack benchmark:           {}{} Atk {} {} {} {} vs. {} HP / {}{} Def {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
            A,
            modifier_A,
            mon_data["Item"],
            mon_data["Ability"],
            mon_name,
            attack_EVs[3],
            hp,
            D,
            modifier_D,
            attack_benchmark_data["Ability"],
            attack_benchmark_data["Item"],
            attack_EVs[4],
            min_percent,
            max_percent,
            kill_percent,
            hko
        ))
    else:
        print("Attack benchmark:           N/A")

    defense_benchmark_data = defense_EVs[5]
    if defense_benchmark_data:
        calc = do_damage_calc(
            defense_EVs[3],
            defense_EVs[4],
            defense_benchmark_data["Ability"],
            defense_benchmark_data["Item"],
            defense_benchmark_data["Spread"][1],
            defense_benchmark_data["Spread"][0],
            mon_name,
            mon_data["Ability"],
            mon_data["Item"],
            spread,
            nature,
            50
        )

        # TODO: (improvement) account for Body Press, Foul Play, etc.
        hp = spread[0]
        A = defense_benchmark_data["Spread"][1][1]
        if defense_benchmark_data["Spread"][0] in NATURE_MATRIX[0][1:]:
            modifier_A = "+"
        elif defense_benchmark_data["Spread"][0] in [row[0] for row in NATURE_MATRIX[1:]]:
            modifier_A = "-"
        else:
            modifier_A = ""

        D = spread[2]
        if nature in NATURE_MATRIX[1][:1] + NATURE_MATRIX[1][2:]:
            modifier_D = "+"
        elif nature in [row[1] for row in NATURE_MATRIX[:1] + NATURE_MATRIX[2:]]:
            modifier_D = "-"
        else:
            modifier_D = ""
        
        sitrus_berry = False
        leftovers = False
        if mon_data["Item"] in HEAL_1_16_ITEMS:
            leftovers = True
        elif mon_data["Item"] in HEAL_1_4_ITEMS:
            sitrus_berry = True

        min_percent, max_percent, kill_percent = process_damage_rolls(calc["Defender stats"][0], calc["Damage rolls"], defense_EVs[2], sitrus_berry=sitrus_berry, leftovers=leftovers)
        if defense_EVs[2] == 1:
            hko = "O"
        else:
            hko = "2"

        print("Defense benchmark:          {}{} Atk {} {} {} {} vs. {} HP / {}{} Def {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
            A,
            modifier_A,
            defense_benchmark_data["Ability"],
            defense_benchmark_data["Item"],
            defense_EVs[4],
            defense_EVs[3],
            hp,
            D,
            modifier_D,
            mon_data["Item"],
            mon_data["Ability"],
            mon_name,
            min_percent,
            max_percent,
            kill_percent,
            hko
        ))
    else:
        print("Defense benchmark:          N/A")

    special_attack_benchmark_data = special_attack_EVs[5]
    if special_attack_benchmark_data:
        calc = do_damage_calc(
            special_attack_EVs[3],
            mon_name,
            mon_data["Ability"],
            mon_data["Item"],
            spread,
            nature,
            special_attack_EVs[4],
            special_attack_benchmark_data["Ability"],
            special_attack_benchmark_data["Item"],
            special_attack_benchmark_data["Spread"][1],
            special_attack_benchmark_data["Spread"][0],
            50
        )

        # TODO: (improvement) account for Body Press, Foul Play, etc.
        hp = special_attack_benchmark_data["Spread"][1][0]
        A = spread[3]
        if nature in NATURE_MATRIX[2][:2] + NATURE_MATRIX[2][3:]:
            modifier_A = "+"
        elif nature in [row[2] for row in NATURE_MATRIX[:2] + NATURE_MATRIX[3:]]:
            modifier_A = "-"
        else:
            modifier_A = ""

        D = special_attack_benchmark_data["Spread"][1][4]
        if special_attack_benchmark_data["Spread"][0] in NATURE_MATRIX[3][:3] + NATURE_MATRIX[3][4:]:
            modifier_D = "+"
        elif special_attack_benchmark_data["Spread"][0] in [row[3] for row in NATURE_MATRIX[:3] + NATURE_MATRIX[4:]]:
            modifier_D = "-"
        else:
            modifier_D = ""
        
        sitrus_berry = False
        leftovers = False
        if special_attack_benchmark_data["Item"] in HEAL_1_16_ITEMS:
            leftovers = True
        elif special_attack_benchmark_data["Item"] in HEAL_1_4_ITEMS:
            sitrus_berry = True

        min_percent, max_percent, kill_percent = process_damage_rolls(calc["Defender stats"][0], calc["Damage rolls"], special_attack_EVs[2], sitrus_berry=sitrus_berry, leftovers=leftovers)
        if special_attack_EVs[2] == 1:
            hko = "O"
        else:
            hko = "2"

        print("Special attack benchmark:   {}{} SpA {} {} {} {} vs. {} HP / {}{} SpD {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
            A,
            modifier_A,
            mon_data["Item"],
            mon_data["Ability"],
            mon_name,
            special_attack_EVs[3],
            hp,
            D,
            modifier_D,
            special_attack_benchmark_data["Ability"],
            special_attack_benchmark_data["Item"],
            special_attack_EVs[4],
            min_percent,
            max_percent,
            kill_percent,
            hko
        ))
    else:
        print("Special attack benchmark:   N/A")

    special_defense_benchmark_data = special_defense_EVs[5]
    if special_defense_benchmark_data:
        calc = do_damage_calc(
            special_defense_EVs[3],
            special_defense_EVs[4],
            special_defense_benchmark_data["Ability"],
            special_defense_benchmark_data["Item"],
            special_defense_benchmark_data["Spread"][1],
            special_defense_benchmark_data["Spread"][0],
            mon_name,
            mon_data["Ability"],
            mon_data["Item"],
            spread,
            nature,
            50
        )

        # TODO: (improvement) account for Body Press, Foul Play, etc.
        hp = spread[0]
        A = special_defense_benchmark_data["Spread"][1][3]
        if special_defense_benchmark_data["Spread"][0] in NATURE_MATRIX[2][:2] + NATURE_MATRIX[2][3:]:
            modifier_A = "+"
        elif special_defense_benchmark_data["Spread"][0] in [row[2] for row in NATURE_MATRIX[:2] + NATURE_MATRIX[3:]]:
            modifier_A = "-"
        else:
            modifier_A = ""

        D = spread[4]
        if nature in NATURE_MATRIX[3][:3] + NATURE_MATRIX[3][4:]:
            modifier_D = "+"
        elif nature in [row[3] for row in NATURE_MATRIX[:3] + NATURE_MATRIX[4:]]:
            modifier_D = "-"
        else:
            modifier_D = ""
        
        sitrus_berry = False
        leftovers = False
        if mon_data["Item"] in HEAL_1_16_ITEMS:
            leftovers = True
        elif mon_data["Item"] in HEAL_1_4_ITEMS:
            sitrus_berry = True

        min_percent, max_percent, kill_percent = process_damage_rolls(calc["Defender stats"][0], calc["Damage rolls"], special_defense_EVs[2], sitrus_berry=sitrus_berry, leftovers=leftovers)
        if special_defense_EVs[2] == 1:
            hko = "O"
        else:
            hko = "2"

        print("Special defense benchmark:  {}{} SpA {} {} {} {} vs. {} HP / {}{} SpD {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
            A,
            modifier_A,
            special_defense_benchmark_data["Ability"],
            special_defense_benchmark_data["Item"],
            special_defense_EVs[4],
            special_defense_EVs[3],
            hp,
            D,
            modifier_D,
            mon_data["Item"],
            mon_data["Ability"],
            mon_name,
            min_percent,
            max_percent,
            kill_percent,
            hko
        ))
    else:
        print("Special defense benchmark:  N/A")

    speed_benchmark_data = speed_EVs[3]
    if speed_benchmark_data:
        if speed_benchmark_data["Spread"][0] in NATURE_MATRIX[4][:-1]:
            modifier = "+"
        elif speed_benchmark_data["Spread"][0] in [row[4] for row in NATURE_MATRIX[:-1]]:
            modifier = "-"
        else:
            modifier = ""
        
        if speed_benchmark_data["Item"]:
            speed_benchmark_data["Item"] = " " + speed_benchmark_data["Item"]
        if speed_benchmark_data["Ability"]:
            speed_benchmark_data["Ability"] = " " + speed_benchmark_data["Ability"]

        print("Speed benchmark:            Outspeed {}{} Spe{}{} {}".format(speed_benchmark_data["Spread"][1][5], modifier, speed_benchmark_data["Item"], speed_benchmark_data["Ability"], speed_EVs[2]))
    else:
        print("Speed benchmark:            N/A")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    pprint(get_mons("https://www.smogon.com/stats/2023-10/moveset/gen9vgc2023regulationebo3-1760.txt"))
