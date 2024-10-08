import os
import sys
import re
import requests
import dirtyjson
from pprint import pprint
from itertools import product
from src.util import *


def get_mons(moveset_file_url, chaos_file_url, num_mons=12):
    """
    Parse required mon data from a Smogon moveset URL and chaos URL.
    """
    resp = requests.get(moveset_file_url)
    lines = [line.strip()[1:-1].strip() for line in resp.text.split("\n")]
    lines = lines[1:]  # skip first line

    mons = {}
    mon_curr = {}
    mon_curr_name = None
    mon_curr_abilities = []
    mon_curr_items = []
    #mon_curr_spreads = []
    mon_curr_moves = []
    num_items_seen = 0
    #num_spreads_seen = 0
    num_mons_seen = 0
    num_separators_seen = 0

    for line in lines:
        if "-----" in line:
            if num_separators_seen == 9:
                mon_curr["Abilities"] = mon_curr_abilities
                mon_curr["Items"] = mon_curr_items
                #mon_curr["Spreads"] = mon_curr_spreads
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
            continue
            #if line != "Spreads":
            #    if num_spreads_seen < MAX_NUM_SPREADS:
            #        spread = line.split()[0]
            #        if spread != "Other":
            #            nature, spread = tuple(spread.split(":"))
            #            spread = tuple([int(i) for i in spread.split("/")])
            #            mon_curr_spreads.append((nature, spread))
            #            num_spreads_seen += 1

        elif num_separators_seen == 5:  # moves
            if line != "Moves":
                words = line.split()
                percent = float(words[-1][:-1])
                move = " ".join(words[:-1])
                if percent > MOVE_THRESHOLD and move != "Other":
                    mon_curr_moves.append(move)

        else:  # tera types teammates, checks + counters
            # TODO: can add tera types to optimizer
            continue

    # assume NUM_MONS < number of Pokemon listed in file
    # if not, need to manually add last Pokemon

    chaos = requests.get(chaos_file_url)
    chaos = dirtyjson.loads(chaos.text)

    for mon_name, mon_data in mons.items():
        spreads = chaos["data"][mon_name]["Spreads"]
        attacks = {}
        defenses = {}
        special_attacks = {}
        special_defenses = {}
        speeds = {}
        for spread, percentage in spreads.items():
            nature, spread = tuple(spread.split(":"))
            spread = tuple([int(i) for i in spread.split("/")])
            percentage = float(percentage)

            if (nature, spread[1]) not in attacks:
                attacks[(nature, spread[1])] = percentage
            else:
                attacks[(nature, spread[1])] += percentage

            if (nature, spread[0], spread[2]) not in defenses:
                defenses[(nature, spread[0], spread[2])] = percentage
            else:
                defenses[(nature, spread[0], spread[2])] += percentage

            if (nature, spread[3]) not in special_attacks:
                special_attacks[(nature, spread[3])] = percentage
            else:
                special_attacks[(nature, spread[3])] += percentage

            if (nature, spread[0], spread[4]) not in special_defenses:
                special_defenses[(nature, spread[0], spread[4])] = percentage
            else:
                special_defenses[(nature, spread[0], spread[4])] += percentage

            if (nature, spread[5])not in speeds:
                speeds[(nature, spread[5])] = percentage
            else:
                speeds[(nature, spread[5])] += percentage

        most_attacks = []
        most_defenses = []
        most_special_attacks = []
        most_special_defenses = []
        most_speeds = []
        for i in range(MAX_NUM_SPREADS):
            most_attack = max(attacks, key=attacks.get)
            most_attacks.append(most_attack)
            del attacks[most_attack]

            most_special_attack = max(special_attacks, key=special_attacks.get)
            most_special_attacks.append(most_special_attack)
            del special_attacks[most_special_attack]

            most_defense = max(defenses, key=defenses.get)
            most_defenses.append(most_defense)
            del defenses[most_defense]

            most_special_defense = max(special_defenses, key=special_defenses.get)
            most_special_defenses.append(most_special_defense)
            del special_defenses[most_special_defense]

            most_speed = max(speeds, key=speeds.get)
            most_speeds.append(most_speed)
            del speeds[most_speed]

        mons[mon_name]["Spreads"] = [most_attacks, most_defenses, most_special_attacks, most_special_defenses, most_speeds]

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


def print_EV_calcs(mon_name, mon_data, nature, spread, remaining_EVs, attack_EVs, defense_EVs, special_attack_EVs, special_defense_EVs, speed_EVs, print_to_stdout=True):
    """
    Print relevant offensive/defensive/speed calcs for the specified EV spread.
    """
    if print_to_stdout:
        print("="*80)
        print("Suggested nature:           {}".format(nature))
        print("Suggested EV spread:        {} HP / {} Atk / {} Def / {} SpA / {} SpD / {} Spe".format(*spread))
        print("Remaining EVs:              {}\n".format(remaining_EVs))
    else:
        calcs = ["N/A", "N/A", "N/A", "N/A", "N/A"]

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

        attack_str = "{}{} Atk {} {} {} {} vs. {} HP / {}{} Def {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
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
        )
        if print_to_stdout:
            print("Attack benchmark:           {}".format(attack_str))
        else:
            calcs[0] = attack_str

    else:
        if print_to_stdout:
            print("Attack benchmark:           N/A")

    defense_benchmark_data = defense_EVs[5]
    if defense_benchmark_data:
        if not defense_EVs[6]:
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

            hp = spread[0]

            if defense_EVs[3] in ["Psyshock", "Psystrike", "Secret Sword"]:
                A = defense_benchmark_data["Spread"][1][3]
                A_str = "SpA"
                if defense_benchmark_data["Spread"][0] in NATURE_MATRIX[2][:2] + NATURE_MATRIX[2][3:]:
                    modifier_A = "+"
                elif defense_benchmark_data["Spread"][0] in [row[2] for row in NATURE_MATRIX[:2] + NATURE_MATRIX[3:]]:
                    modifier_A = "-"
                else:
                    modifier_A = ""
            elif defense_EVs[3] == "Body Press":
                A = defense_benchmark_data["Spread"][1][2]
                A_str = "Def"
                if defense_benchmark_data["Spread"][0] in NATURE_MATRIX[1][:1] + NATURE_MATRIX[1][2:]:
                    modifier_A = "+"
                elif defense_benchmark_data["Spread"][0] in [row[1] for row in NATURE_MATRIX[:1] + NATURE_MATRIX[2:]]:
                    modifier_A = "-"
                else:
                    modifier_A = ""
            else:
                A = defense_benchmark_data["Spread"][1][1]
                A_str = "Atk"
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

            defense_str = "{}{} {} {} {} {} {} vs. {} HP / {}{} Def {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
                A,
                modifier_A,
                A_str,
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
            )

        else:  # defense EVs is for Body Press benchmark
            calc = do_damage_calc(
                defense_EVs[3],
                mon_name,
                mon_data["Ability"],
                mon_data["Item"],
                spread,
                nature,
                defense_EVs[4],
                defense_benchmark_data["Ability"],
                defense_benchmark_data["Item"],
                defense_benchmark_data["Spread"][1],
                defense_benchmark_data["Spread"][0],
                50
            )

            hp = defense_benchmark_data["Spread"][1][0]
            A = spread[2]
            if nature in NATURE_MATRIX[1][:1] + NATURE_MATRIX[1][2:]:
                modifier_A = "+"
            elif nature in [row[1] for row in NATURE_MATRIX[:1] + NATURE_MATRIX[2:]]:
                modifier_A = "-"
            else:
                modifier_A = ""

            D = defense_benchmark_data["Spread"][1][2]
            if defense_benchmark_data["Spread"][0] in NATURE_MATRIX[1][:1] + NATURE_MATRIX[1][2:]:
                modifier_D = "+"
            elif defense_benchmark_data["Spread"][0] in [row[1] for row in NATURE_MATRIX[:1] + NATURE_MATRIX[2:]]:
                modifier_D = "-"
            else:
                modifier_D = ""

            sitrus_berry = False
            leftovers = False
            if defense_benchmark_data["Item"] in HEAL_1_16_ITEMS:
                leftovers = True
            elif defense_benchmark_data["Item"] in HEAL_1_4_ITEMS:
                sitrus_berry = True

            min_percent, max_percent, kill_percent = process_damage_rolls(calc["Defender stats"][0], calc["Damage rolls"], defense_EVs[2], sitrus_berry=sitrus_berry, leftovers=leftovers)
            if defense_EVs[2] == 1:
                hko = "O"
            else:
                hko = "2"

            defense_str = "{}{} Def {} {} {} {} vs. {} HP / {}{} Def {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
                A,
                modifier_A,
                mon_data["Item"],
                mon_data["Ability"],
                mon_name,
                defense_EVs[3],
                hp,
                D,
                modifier_D,
                defense_benchmark_data["Ability"],
                defense_benchmark_data["Item"],
                defense_EVs[4],
                min_percent,
                max_percent,
                kill_percent,
                hko
            )

        if print_to_stdout:
            print("Defense benchmark:          {}".format(defense_str))
        else:
            calcs[1] = defense_str

    else:
        if print_to_stdout:
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

        hp = special_attack_benchmark_data["Spread"][1][0]
        A = spread[3]
        if nature in NATURE_MATRIX[2][:2] + NATURE_MATRIX[2][3:]:
            modifier_A = "+"
        elif nature in [row[2] for row in NATURE_MATRIX[:2] + NATURE_MATRIX[3:]]:
            modifier_A = "-"
        else:
            modifier_A = ""

        if special_attack_EVs[3] in ["Psyshock", "Psystrike", "Secret Sword"]:
            D = special_attack_benchmark_data["Spread"][1][2]
            D_str = "Def"
            if special_attack_benchmark_data["Spread"][0] in NATURE_MATRIX[1][:1] + NATURE_MATRIX[1][2:]:
                modifier_D = "+"
            elif special_attack_benchmark_data["Spread"][0] in [row[1] for row in NATURE_MATRIX[:1] + NATURE_MATRIX[2:]]:
                modifier_D = "-"
            else:
                modifier_D = ""
        else:
            D = special_attack_benchmark_data["Spread"][1][4]
            D_str = "SpD"
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

        special_attack_str = "{}{} SpA {} {} {} {} vs. {} HP / {}{} {} {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
            A,
            modifier_A,
            mon_data["Item"],
            mon_data["Ability"],
            mon_name,
            special_attack_EVs[3],
            hp,
            D,
            modifier_D,
            D_str,
            special_attack_benchmark_data["Ability"],
            special_attack_benchmark_data["Item"],
            special_attack_EVs[4],
            min_percent,
            max_percent,
            kill_percent,
            hko
        )
        if print_to_stdout:
            print("Special attack benchmark:   {}".format(special_attack_str))
        else:
            calcs[2] = special_attack_str
    else:
        if print_to_stdout:
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

        special_defense_str = "{}{} SpA {} {} {} {} vs. {} HP / {}{} SpD {} {} {}: {} - {}% -- {}% chance to {}HKO".format(
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
        )
        if print_to_stdout:
            print("Special defense benchmark:  {}".format(special_defense_str))
        else:
            calcs[3] = special_defense_str
    else:
        if print_to_stdout:
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

        speed_str = "Outspeed {}{} Spe{}{} {}".format(speed_benchmark_data["Spread"][1][5], modifier, speed_benchmark_data["Item"], speed_benchmark_data["Ability"], speed_EVs[2])
        if print_to_stdout:
            print("Speed benchmark:            {}".format(speed_str))
        else:
            calcs[4] = speed_str
    else:
        if print_to_stdout:
            print("Speed benchmark:            N/A")

    if print_to_stdout:
        print("="*80 + "\n")
    else:
        return calcs


def import_from_paste(paste):
    """
    Import a single mon in Pokepaste format to a dict expected by optimizer.

    Note that paste is expected to contain all required fields, handling of this should be done by frontend.
    """
    lines = paste.split("\n")

    mon = {}
    moves = []

    paste_start_nickname_gender_re = re.compile("(.*) \((.*)\) \(([MF])\) @ (.*)")
    paste_start_gender_re = re.compile("(.*) \(([MF])\) @ (.*)")
    paste_start_nickname_re = re.compile("(.*) \((.*)\) @ (.*)")
    paste_start_re = re.compile("(.*) @ (.*)")

    for line in lines:
        line = line.strip()
        if m := re.match(paste_start_nickname_gender_re, line):
            mon["Name"] = m.group(2)
            mon["Item"] = m.group(4)
            break
        elif m := re.match(paste_start_gender_re, line):
            mon["Name"] = m.group(1)
            mon["Item"] = m.group(3)
            break
        elif m := re.match(paste_start_nickname_re, line):
            mon["Name"] = m.group(2)
            mon["Item"] = m.group(3)
            break
        elif m := re.match(paste_start_re, line):
            mon["Name"] = m.group(1)
            mon["Item"] = m.group(2)
            break

    for line in lines:
        line = line.strip()
        if "Ability" in line:
            mon["Ability"] = line.split(":")[1].strip()
        elif "EVs" in line:  # don't currently use EVs, but include it anyway
            fixed_EVs = [0, 0, 0, 0, 0, 0]
            EVs = line.split(":")[1].strip().split(" / ")
            for EV in EVs:
                value, name = EV.split()
                fixed_EVs[stat_names.index(name)] = int(value)
            mon["EVs"] = fixed_EVs
        elif "- " in line:  # moves
            moves.append(line[1:].strip())
        elif "Nature" in line:  # don't currently use nature, but include it anyway
            mon["Nature"] = line.split()[0]

    mon["Moves"] = moves
    return mon


if __name__ == "__main__":
    pprint(get_mons("https://www.smogon.com/stats/2023-11/moveset/gen9vgc2023regulationebo3-1760.txt", "https://www.smogon.com/stats/2023-11/chaos/gen9vgc2023regulationebo3-1760.json"))
