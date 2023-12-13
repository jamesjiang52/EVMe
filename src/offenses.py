import os
import sys
from pprint import pprint
from tqdm import tqdm
from itertools import product
from math import floor, ceil
from src.util import *


def get_offensive_benchmarks(attack_mon_name, attack_mon_data, defend_mons):
    """
    Returns a two-element tuple of lists of tuples with following structure:
    (attack/special_attack stat, number of hits, move, benchmark mon_name, benchmark mon_data)
    
    First list corresponds to attack benchmarks, second list corresponds to special attack benchmarks.
    
    Lists are sorted in ascending order of offensive stats.
    """
    attacks = []
    special_attacks = []

    physical_moves = set()
    special_moves = set()
    status_moves = set()
    
    for i in range(len(attack_mon_data["Moves"])):
        move = attack_mon_data["Moves"][i]
        category = get_move_category(move).strip()
        if category == "Status":
            status_moves.add(move)
        elif category == "Physical":
            physical_moves.add(move)
        elif category == "Special":
            special_moves.add(move)

    for mon_name, mon_data in tqdm(defend_mons.items()):
        mon_calcs_seen = set()  # avoid redundant calcs as much as possible
        defense_spreads = []
        special_defense_spreads = []
        for spread in mon_data["Spreads"][1]:
            defense_spreads.append((spread[0], (spread[1], 0, spread[2], 0, 0, 0)))
        for spread in mon_data["Spreads"][3]:
            special_defense_spreads.append((spread[0], (spread[1], 0, 0, 0, spread[2], 0)))

        spreads = (defense_spreads, special_defense_spreads)

        for j in range(2):
            if j == 0 and len(physical_moves) == 0:
                continue
            if j == 1 and len(special_moves) == 0:
                continue
            for comb in product(mon_data["Items"], mon_data["Abilities"], spreads[j]):
                item = comb[0]
                ability = comb[1]
                nature, spread = comb[2]
                
                best_move = ""
                best_move_calc = {"Damage rolls": [0]}
                
                skip_calc_eval = False
                
                for i in range(len(attack_mon_data["Moves"])):
                    move = attack_mon_data["Moves"][i]
                
                    if move in status_moves:
                        continue
                    elif j == 0 and move in special_moves:
                        continue
                    elif j == 1 and move in physical_moves:
                        continue
                    
                    # Smogon currently has no data about tera type, so just skip
                    if move == "Tera Blast":
                        continue
    
                    calc = do_damage_calc(
                        move,
                        attack_mon_name,
                        attack_mon_data["Ability"],
                        attack_mon_data["Item"],
                        BLANK_EVS,
                        "Serious",
                        mon_name,
                        ability,
                        item,
                        spread,
                        nature,
                        50
                    )
                    
                    if not calc["Damage rolls"]:
                        continue
    
                    if (tuple(calc["Damage rolls"]), i) in mon_calcs_seen:
                        skip_calc_eval = True
                        break
                    mon_calcs_seen.add((tuple(calc["Damage rolls"]), i))
    
                    if calc["Damage rolls"][0] > best_move_calc["Damage rolls"][0]:  # look at lowest roll for benchmark
                        best_move = move
                        best_move_calc = calc
                
                if skip_calc_eval:
                    continue

                # TODO: (improvement) account for Body Press, Foul Play, etc.
                if best_move_calc["Move"][1] == "Physical":
                    A = best_move_calc["Attacker stats"][1]
                    D = best_move_calc["Defender stats"][2]
                else:  # special
                    A = best_move_calc["Attacker stats"][3]
                    D = best_move_calc["Defender stats"][4]
                
                bp = best_move_calc["Move"][0]
                damage = best_move_calc["Damage rolls"][0]
                initial = floor(2 + 11*bp*A/(25*D))
                
                # could be slightly off, since rounding is done at every step in the damage calc, not once at the very end
                other_mult = damage/initial
                
                # solve for benchmark attack stat for guaranteed OHKO
                # calc already takes into account Choice Specs, Life Orb, etc.
                # doesn't make sense to handle Protosynthesis, since EVs are unknown
                damage_req = best_move_calc["Defender stats"][0]
                A_1 = floor(25*D*(damage_req/other_mult - 2)/(11*bp))  # round down to be aggressive
                
                mon_data_out = {
                    "Item": item,
                    "Ability": ability,
                    "Spread": (nature, spread)
                }
                if item != "Focus Sash":  # ignore OHKO benchmark for sashed mons
                    if best_move_calc["Move"][1] == "Physical":
                        attacks.append((A_1, 1, best_move, mon_name, mon_data_out))
                    else:
                        special_attacks.append((A_1, 1, best_move, mon_name, mon_data_out))
    
                # solve for benchmark attack stat for guaranteed 2HKO
                if item in HEAL_1_16_ITEMS:
                    recovery_factor = 1/16
                elif item in HEAL_1_4_ITEMS:
                    recovery_factor = 1/4
                else:
                    recovery_factor = 0
    
                damage_req = ceil((best_move_calc["Defender stats"][0] + floor(recovery_factor*best_move_calc["Defender stats"][0]))/2)
                A_2 = floor(25*D*(damage_req/other_mult - 2)/(11*bp))  # round down to be aggressive
                
                mon_data_out = {
                    "Item": item,
                    "Ability": ability,
                    "Spread": (nature, spread)
                }
                if best_move_calc["Move"][1] == "Physical":
                    attacks.append((A_2, 2, best_move, mon_name, mon_data_out))
                else:
                    special_attacks.append((A_2, 2, best_move, mon_name, mon_data_out))
                
                # TODO: handle tera type STAB
    
                # TODO: (improvement) maybe add 3HKO in future, but seems excessive
    
    # remove attack / special attack ties... probably a more Pythonic way
    seen_attacks = set()
    attacks_uniq = []
    for attack in attacks:
        if attack[0] not in seen_attacks:
            attacks_uniq.append(attack)
            seen_attacks.add(attack[0])

    seen_special_attacks = set()
    special_attacks_uniq = []
    for special_attack in special_attacks:
        if special_attack[0] not in seen_special_attacks:
            special_attacks_uniq.append(special_attack)
            seen_special_attacks.add(special_attack[0])

    return (sorted(attacks_uniq, key=lambda x: x[0]), sorted(special_attacks_uniq, key=lambda x: x[0]))


def allocate_offensive_EVs(mon_name, mon_data, offensive_benchmarks):
    """
    Returns a two-element tuple of lists of tuples with following structure:
    (attack/special_attack EVs, boosting nature required?, number of hits, move, benchmark mon_name, benchmark mon_data)
    
    First list corresponds to attack EVs, second list corresponds to special attack EVs.
    """
    base_stats = get_stats(mon_name, PERFECT_IVS, (0, 0, 0, 0, 0, 0), 50, "Serious")
    min_attack = base_stats[1]
    min_special_attack = base_stats[3]

    max_attack = floor(1.1*(min_attack + 32))
    max_special_attack = floor(1.1*(min_special_attack + 32))

    max_attack_index = -1
    min_attack_index = -1
    for i in range(len(offensive_benchmarks[0])):
        if min_attack <= offensive_benchmarks[0][i][0]:
            if min_attack_index == -1:
                min_attack_index = i

        if max_attack < offensive_benchmarks[0][i][0]:
            pass
        else:
            max_attack_index = i

    max_special_attack_index = -1
    min_special_attack_index = -1
    for i in range(len(offensive_benchmarks[1])):
        if min_special_attack <= offensive_benchmarks[1][i][0]:
            if min_special_attack_index == -1:
                min_special_attack_index = i

        if max_special_attack < offensive_benchmarks[1][i][0]:
            break
        else:
            max_special_attack_index = i

    if (min_attack_index == -1 or max_attack_index == -1 or max_attack_index < min_attack_index) and \
            (min_special_attack_index == -1 or max_special_attack_index == -1 or max_special_attack_index < min_special_attack_index):
        # offenses can't be optimized, leave 0 EVs in attack + special attack
        # either the next offensive benchmark is too high, or is non-existent (Pokemon already OHKOs everything)
        return ([], [])

    attack_EVs = []
    special_attack_EVs = []

    if not (min_attack_index == -1 or max_attack_index == -1 or max_attack_index < min_attack_index):
        attack_benchmarks = offensive_benchmarks[0][min_attack_index:max_attack_index + 1]
    
        for i in range(len(attack_benchmarks)):
            benchmark = attack_benchmarks[i][0]
            attack_diff = benchmark - min_attack
            if attack_diff > 32:  # can't reach benchmark attack with neutral nature
                break
    
            EVs = max(0, 4 + 8*(attack_diff - 1))
            attack_EVs.append((EVs, False, *attack_benchmarks[i][1:5]))
    
        for i in range(len(attack_benchmarks)):
            benchmark = attack_benchmarks[i][0]
            min_attack_boost = floor(1.1*(min_attack))
            attack_diff = benchmark - min_attack_boost
            if attack_diff <= 0:
                continue
            
            attack_diff = ceil(benchmark/1.1) - min_attack
            EVs = min(252, max(0, 4 + 8*(attack_diff - 1)))
            attack_EVs.append((EVs, True, *attack_benchmarks[i][1:5]))

    if not (min_special_attack_index == -1 or max_special_attack_index == -1 or max_special_attack_index < min_special_attack_index):
        special_attack_benchmarks = offensive_benchmarks[1][min_special_attack_index:max_special_attack_index + 1]
    
        for i in range(len(special_attack_benchmarks)):
            benchmark = special_attack_benchmarks[i][0]
            special_attack_diff = benchmark - min_special_attack
            if special_attack_diff > 32:  # can't reach benchmark special attack with neutral nature
                break
    
            EVs = max(0, 4 + 8*(special_attack_diff - 1))
            special_attack_EVs.append((EVs, False, *special_attack_benchmarks[i][1:5]))
    
        for i in range(len(special_attack_benchmarks)):
            benchmark = special_attack_benchmarks[i][0]
            min_special_attack_boost = floor(1.1*(min_special_attack))
            special_attack_diff = benchmark - min_special_attack_boost
            if special_attack_diff < 0:
                continue
            
            special_attack_diff = ceil(benchmark/1.1) - min_special_attack
            EVs = min(252, max(0, 4 + 8*(special_attack_diff - 1)))
            special_attack_EVs.append((EVs, True, *special_attack_benchmarks[i][1:5]))

    return (attack_EVs, special_attack_EVs)


if __name__ == "__main__":
    meta_mons = {
        "Flutter Mane": {
            "Abilities": ["Protosynthesis"],
            "Items": ["Booster Energy", "Choice Specs"],
            "Spreads": [
                [('Timid', 0), ('Modest', 0), ('Bold', 0)],
                [('Timid', 228, 148), ('Timid', 252, 116), ('Timid', 116, 204)],
                [('Modest', 36), ('Timid', 4), ('Timid', 100)],
                [('Timid', 100, 4), ('Timid', 116, 4), ('Timid', 228, 4)],
                [('Timid', 124), ('Modest', 100), ('Timid', 252)]
            ],
            "Moves": ["Moonblast", "Dazzling Gleam", "Shadow Ball", "Icy Wind", "Thunderbolt"]
        },
        "Landorus-Therian": {
            "Abilities": ["Intimidate"],
            "Items": ["Choice Scarf", "Assault Vest"],
            "Spreads": [
                [('Adamant', 116), ('Adamant', 36), ('Adamant', 196)],
                [('Adamant', 52, 4), ('Adamant', 60, 108), ('Adamant', 164, 52)],
                [('Adamant', 0), ('Jolly', 0), ('Relaxed', 4)],
                [('Jolly', 116, 4), ('Adamant', 164, 4), ('Adamant', 132, 4)],
                [('Adamant', 252), ('Adamant', 212), ('Jolly', 252)]
            ],
            "Moves": ["Stomping Tantrum", "Rock Slide", "U-turn", "Tera Blast"]
        }
    }
    mon_name = "Ninetales-Alola"
    mon_data = {"Ability": "Snow Warning", "Item": "Light Clay", "Moves": ["Aurora Veil", "Blizzard", "Moonblast", "Protect"]}

    offensive_benchmarks = get_offensive_benchmarks(mon_name, mon_data, meta_mons)
    #pprint(offensive_benchmarks)
    pprint(allocate_offensive_EVs(mon_name, mon_data, offensive_benchmarks))
