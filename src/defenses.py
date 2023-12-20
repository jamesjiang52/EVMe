import os
import sys
from pprint import pprint
from tqdm import tqdm
from scipy import optimize as opt
import numpy as np
from itertools import product
from math import floor, ceil
from src.util import *


def adjust_defensive_EVs(req_hp_EVs, defensive_EVs):
    """
    Used to adjust (i.e. lower) a defensive stat in the actual optimization phase for specific HP investments.
    
    Modifies the first element (HP EVs, defense/special_defense EVs) in defensive_EVs.
    """
    D_EVs, boosting_nature_required, hko_level, best_move, attack_mon_name, attack_mon_data_out = defensive_EVs
    if not attack_mon_data_out:
        return defensive_EVs

    hp, A, D, bp, category, other_mult, recovery_factor = attack_mon_data_out["__adjust_data"]

    if req_hp_EVs:
        max_hp = hp + 1 + int((req_hp_EVs - 4)/8)
    else:
        max_hp = hp

    if hko_level == 1:
        new_D_req = floor(1/(25*(max_hp/other_mult - 2)/(11*bp*A)))
    else:
        new_D_req = floor(1/(25*(max_hp*(recovery_factor + 1)/(2*other_mult) - 2)/(11*bp*A)))

    if boosting_nature_required:
        D_diff = ceil(new_D_req/1.1) - D
    else:
        D_diff = new_D_req - D

    new_D_EVs = (req_hp_EVs, max(0, 4 + 8*(D_diff - 1)))
    return (new_D_EVs, *defensive_EVs[1:])


def get_lowest_defensive_EVs(defend_stats, attack_stats, bp, move_category, other_mult, level, hko_level=1, recovery_factor=0):
    """
    Given the attacker and defender stats and a few other params,
    get the lowest total amount of EVs invested into HP and defense/special_defense to guarantee that the attack is survived,
    for both neutral and boosting natures.

    Returns a two-element tuple of lists of tuples with following structure:
    ((HP EVs, defense/special_defense EVs), boosting nature required?)
    
    First list corresponds to HP/defense EVs, second list corresponds to HP/special_defense EVs.
    """
    # currently support only surviving OHKOs and 2HKOs
    # TODO: (improvement) 3HKOs, seems excessive so probably won't support
    
    base_hp = defend_stats[0]
    if move_category == "Physical":
        attack = attack_stats[1]
        base_def = defend_stats[2]
    else:  # special
        attack = attack_stats[3]
        base_def = defend_stats[4]
    
    defense_EVs = []
    special_defense_EVs = []

    if hko_level == 1:
        nlc = opt.NonlinearConstraint(lambda x: other_mult*((2*level/5 + 2)*bp*attack/(x[1]*50)+2) - x[0], -np.inf, -1)
    else:
        nlc = opt.NonlinearConstraint(lambda x: 2*other_mult*((2*level/5 + 2)*bp*attack/(x[1]*50)+2) - (x[0] + x[0]*recovery_factor), -np.inf, -1)

    bounds = ((base_hp, base_hp + 32), (base_def, base_def + 32))
    obj = lambda x: 8*(x[0] - base_hp - 1) + 4 + 8*(x[1] - base_def - 1) + 4
    x0 = (base_hp + 16, base_def + 16)  # use midpoint as initial guess, doesn't really matter
    res = opt.minimize(obj, x0, bounds=bounds, constraints=nlc)
    
    # round down to be aggressive
    best_hp = floor(res.x[0])
    best_def = floor(res.x[1])
    best_obj = obj((best_hp, best_def))

    if hko_level == 1:
        remaining_hp = best_hp - round(round((2*level/5 + 2)*bp*attack/(best_def*50)+2)*other_mult)
    else:
        remaining_hp = best_hp - 2*round(round((2*level/5 + 2)*bp*attack/(best_def*50)+2)*other_mult) + floor(best_hp*recovery_factor)

    cant_survive_with_neutral = False
    if remaining_hp >= -2:  # conservative estimate for if guaranteed to survive
        # additional heuristic for determining if survival is actually guaranteed
        if best_hp >= base_hp + 31 and best_def >= base_def + 31 and remaining_hp < 2:
            cant_survive_with_neutral = True
        # heuristic for determining if attack can be survived with no bulk investment
        elif best_hp <= base_hp + 1 and best_def <= base_def + 1 and remaining_hp >= 2:
            return (defense_EVs, special_defense_EVs)
        else:
            hp_EVs = max(0, 8*(best_hp - base_hp - 1) + 4)
            def_EVs = max(0, 8*(best_def - base_def - 1) + 4)

            if move_category == "Physical":
                defense_EVs.append(((hp_EVs, def_EVs), False))
            else:
                special_defense_EVs.append(((hp_EVs, def_EVs), False))
    else:
        cant_survive_with_neutral = True

    # check boosting nature
    bounds = ((base_hp, base_hp + 32), (floor(1.1*base_def), floor(1.1*(base_def + 32))))
    obj = lambda x: 8*(x[0] - base_hp - 1) + 4 + 8*(x[1]/1.1 - base_def - 1) + 4
    res = opt.minimize(obj, x0, bounds=bounds, constraints=nlc)

    # round down to be aggressive
    best_hp = floor(res.x[0])
    best_def = floor(res.x[1])
    best_obj = obj((best_hp, best_def))

    if hko_level == 1:
        remaining_hp = best_hp - round(round((2*level/5 + 2)*bp*attack/(best_def*50)+2)*other_mult)
    else:
        remaining_hp = best_hp - 2*round(round((2*level/5 + 2)*bp*attack/(best_def*50)+2)*other_mult) + floor(best_hp*recovery_factor)

    if remaining_hp >= -2:  # conservative estimate for if guaranteed to survive
        # additional heuristic for determining if survival is actually guaranteed
        if best_hp >= base_hp + 31 and best_def >= floor(1.1*(base_def + 32)) and remaining_hp < 2:
            return (defense_EVs, special_defense_EVs)
        # heuristic for determining if attack can be survived with no bulk investment
        elif best_hp <= base_hp + 1 and best_def <= floor(1.1*base_def) + 1 and remaining_hp >= 2:
            if cant_survive_with_neutral:
                if move_category == "Physical":
                    defense_EVs.append(((0, 0), True))
                else:
                    special_defense_EVs.append(((0, 0), True))
        else:
            hp_EVs = max(0, 8*(best_hp - base_hp - 1) + 4)
            def_EVs = max(0, 8*(ceil(best_def/1.1) - base_def - 1) + 4)
        
            if move_category == "Physical":
                defense_EVs.append(((hp_EVs, def_EVs), True))
            else:
                special_defense_EVs.append(((hp_EVs, def_EVs), True))

    return (defense_EVs, special_defense_EVs)


def allocate_defensive_EVs(mon_name, mon_data, attack_mons):
    """
    Returns a two-element tuple of lists of tuples with following structure:
    ((HP EVs, defense/special_defense EVs), boosting nature required?, number of hits, move, benchmark mon_name, benchmark mon_data)
    
    First list corresponds to defense benchmarks, second list corresponds to special defense benchmarks.
    """
    defense_EVs = []
    special_defense_EVs = []

    status_moves = set()
    for attack_mon_name, attack_mon_data in tqdm(attack_mons.items()):
        mon_calcs_seen = set()  # avoid redundant calcs as much as possible
        spreads = []
        for spread in attack_mon_data["Spreads"][0]:
            if spread[1] > 4:
                spreads.append((spread[0], (0, spread[1], 0, 0, 0, 0)))
        for spread in attack_mon_data["Spreads"][2]:
            if spread[1] > 4:
                spreads.append((spread[0], (0, 0, 0, spread[1], 0, 0)))
        
        for comb in product(attack_mon_data["Items"], attack_mon_data["Abilities"], spreads):
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

                # Smogon currently has no data about tera type, so just skip
                if move == "Tera Blast":
                    continue

                calc = do_damage_calc(
                    move,
                    attack_mon_name,
                    ability,
                    item,
                    spread,
                    nature,
                    mon_name,
                    mon_data["Ability"],
                    mon_data["Item"],
                    BLANK_EVS,
                    "Serious",
                    50
                )
                
                if not calc["Damage rolls"]:  # is status move OR defending mon is immune
                    status_moves.add(move)
                    continue
                
                if (tuple(calc["Damage rolls"]), i) in mon_calcs_seen:
                    skip_calc_eval = True
                    break
                mon_calcs_seen.add((tuple(calc["Damage rolls"]), i))
                
                if calc["Damage rolls"][-1] > best_move_calc["Damage rolls"][-1]:  # look at highest roll for benchmark
                    best_move = move
                    best_move_calc = calc
            
            if skip_calc_eval or "Move" not in best_move_calc:
                continue

            bp = best_move_calc["Move"][0]
            category = best_move_calc["Move"][1]
            
            # TODO: handle Tera Blast
            
            # TODO: (improvement) account for Body Press, Foul Play, etc.
            if category == "Physical":
                A = best_move_calc["Attacker stats"][1]
                D = best_move_calc["Defender stats"][2]
            else:  # special
                A = best_move_calc["Attacker stats"][3]
                D = best_move_calc["Defender stats"][4]

            damage = best_move_calc["Damage rolls"][-1]
            initial = floor(2 + 11*bp*A/(25*D))
            
            # could be slightly off, since rounding is done at every step in the damage calc, not once at the very end
            other_mult = damage/initial
            
            recovery_factor = 0
            if mon_data["Item"] in HEAL_1_16_ITEMS:
                recovery_factor = 1/16
            elif mon_data["Item"] in HEAL_1_4_ITEMS:
                recovery_factor = 1/4

            attack_mon_data_out = {
                "Item": item,
                "Ability": ability,
                "Spread": (nature, spread),
                "__adjust_data": (best_move_calc["Defender stats"][0], A, D, bp, category, other_mult, recovery_factor)  # used to adjust stats when optimizing
            }
            for hko_level in [1, 2]:
                defenses, special_defenses = get_lowest_defensive_EVs(best_move_calc["Defender stats"], best_move_calc["Attacker stats"], bp, category, other_mult, 50, hko_level=hko_level, recovery_factor=recovery_factor)
                for defense in defenses:
                    defense_EVs.append((*defense, hko_level, best_move, attack_mon_name, attack_mon_data_out))
                for special_defense in special_defenses:
                    special_defense_EVs.append((*special_defense, hko_level, best_move, attack_mon_name, attack_mon_data_out))
    
    return (defense_EVs, special_defense_EVs)


if __name__ == "__main__":
    # survive OHKO only with boosting nature
    #print(get_lowest_defensive_EVs((150, 0, 90, 0, 0, 0), (0, 170, 0, 0, 0, 0), 100, "Physical", 3, 50))
    # survive OHKO with neutral nature
    #print(get_lowest_defensive_EVs((150, 0, 90, 0, 0, 0), (0, 120, 0, 0, 0, 0), 100, "Physical", 3, 50))
    # survive OHKO without any defensive investment
    #print(get_lowest_defensive_EVs((150, 0, 90, 0, 0, 0), (0, 90, 0, 0, 0, 0), 80, "Physical", 3, 50))
    # survive 2HKO with neutral nature, without berry
    #print(get_lowest_defensive_EVs((150, 0, 90, 0, 0, 0), (0, 90, 0, 0, 0, 0), 80, "Physical", 3, 50, hko_level=2))
    # survive 2HKO with neutral nature, with berry
    #print(get_lowest_defensive_EVs((150, 0, 90, 0, 0, 0), (0, 90, 0, 0, 0, 0), 80, "Physical", 3, 50, hko_level=2, sitrus_berry=True))

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
    mon_data = {"Ability": "Snow Warning", "Item": "Light Clay"}
    defense_EVs, special_defense_EVs = allocate_defensive_EVs(mon_name, mon_data, meta_mons)
    pprint((defense_EVs, special_defense_EVs))
    
    #pprint(defense_EVs[0])
    #req_hp_EVs = min(252, defense_EVs[0][0][0] + 28)
    #pprint(adjust_defensive_EVs(req_hp_EVs, defense_EVs[0]))
