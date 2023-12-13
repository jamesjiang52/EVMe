import os
import sys
from pprint import pprint
from tqdm import tqdm
from itertools import product
import dirtyjson
import argparse
from src.util import *
import src.parse
import src.speed
import src.offenses
import src.defenses


def check_EV_optimality(base_stats, nature, spread):
    """
    Check if the nature selection is optimal.
    """
    stats = get_stats_from_base(base_stats, spread, nature)

    for i in range(len(NATURE_MATRIX)):
        for j in range(len(NATURE_MATRIX[0])):
            if nature == NATURE_MATRIX[i][j]:
                boosting_index = i + 1

    max_stat_index = stats[1:].index(max(stats[1:])) + 1

    # nature is not optimal if:
    #   (a) the highest stat (besides HP) is not the nature-boosted stat, AND
    #   (b) the same stat value of the nature-boosted stat can be achieved with a neutral nature
    if max_stat_index != boosting_index:
        if spread[boosting_index]:
            diff = floor(1.1*(base_stats[boosting_index] + 1 + (spread[boosting_index] - 4)/8)) - base_stats[boosting_index]
        else:
            diff = floor(1.1*base_stats[boosting_index]) - base_stats[boosting_index]

        if diff <= 32:
            return False

    return True


def choose_nature(nature_vector, spread):
    """
    Choose a stat to harm, given a stat to boost and all stats' EV investment.

    If nature_vector contains no stat to boost or if all stats require EV investment, return None.
    """
    boosting_index = -1
    harmful_index = -1
    for i in range(len(nature_vector)):
        if nature_vector[i]:
            boosting_index = i
        elif not nature_vector[i] and spread[i + 1] == 0 and harmful_index == -1:  # choose a stat to harm
            if i in [1, 3] and spread[0] != 0:
                # don't choose this defensive stat if there's investment into HP (would change damage calc)
                continue
            # usually choose one of the offensive stats, unless Pokemon is a mixed attacker
            # in the case of a mixed attacker, this has the risk of changing a defense calc such that a particular attack can be survived with no bulk investment,
            # but cannot be survived with a harmful defensive nature
            # ignore this risk for now, mixed attackers are really rare anyways
            harmful_index = i

    # no boosting_nature required
    if boosting_index == -1:
        # ignore this spread, it's far more optimal to have a non-neutral nature
        return None
        #if harmful_index != -1:
        #    # choose a stat to boost
        #    # for now, choose the stat with most EVs invested, but choosing the highest stat after EV investment is more optimal
        #    boosting_index = spread[1:].index(max(spread[1:]))
        #    return NATURE_MATRIX[boosting_index][harmful_index]
        #else:
        #    # all stats need investment, so use neutral nature
        #    return "Serious"

    # all non-boosted stats need investment, so can't use this spread
    if harmful_index == -1:
        return None

    return NATURE_MATRIX[boosting_index][harmful_index]


def optimize_EVs(mon_name, req_offensive_EVs, req_defensive_EVs, req_speed_EVs, num_spreads=5, bias1=None, bias2=None):
    """
    Optimize EV allocation. Optionally, provide 1 or 2 stats to favor when allocating EVs.

    Returns a list of tuples with following structure:
    (remaining EVs, (nature, EV spread), attack EVs benchmark, defense EVs benchmark, special_attack EVs benchmark, special_defense EVs benchmark, speed EVs benchmark)

    List is sorted in ascending order of remaining EVs (less is better), then decreasing order of sum of favored stats (if specified).
    """
    base_stats = get_stats(mon_name, PERFECT_IVS, (0, 0, 0, 0, 0, 0), 50, "Serious")

    req_attack_EVs, req_special_attack_EVs = req_offensive_EVs
    req_defense_EVs, req_special_defense_EVs = req_defensive_EVs

    # add 0 EVs invested into all stats
    req_attack_EVs.append((0, False, None, None, None, None))
    req_special_attack_EVs.append((0, False, None, None, None, None))
    req_defense_EVs.append(((0, 0), False, None, None, None, None))
    req_special_defense_EVs.append(((0, 0), False, None, None, None, None))
    req_speed_EVs.append((0, False, None, None))

    spreads = []

    # just brute force, there aren't that many combinations
    all_EVs_product = list(product(req_attack_EVs, req_special_attack_EVs, req_defense_EVs, req_special_defense_EVs, req_speed_EVs))
    for all_EVs in tqdm(all_EVs_product):
        attack_EVs, special_attack_EVs, defense_EVs, special_defense_EVs, speed_EVs = all_EVs
        if defense_EVs[0][0] > special_defense_EVs[0][0]:
            max_hp_EVs = defense_EVs[0][0]
            defense_EVs_adj = defense_EVs
            special_defense_EVs_adj = src.defenses.adjust_defensive_EVs(max_hp_EVs, special_defense_EVs)
        else:
            max_hp_EVs = special_defense_EVs[0][0]
            defense_EVs_adj = src.defenses.adjust_defensive_EVs(max_hp_EVs, defense_EVs)
            special_defense_EVs_adj = special_defense_EVs
        spread = (max_hp_EVs, attack_EVs[0], defense_EVs_adj[0][1], special_attack_EVs[0], special_defense_EVs_adj[0][1], speed_EVs[0])
        total_EVs = sum(spread)
        nature_vector = (attack_EVs[1], defense_EVs_adj[1], special_attack_EVs[1], special_defense_EVs_adj[1], speed_EVs[1])
        if nature_vector.count(True) <= 1 and total_EVs <= 508:
            nature = choose_nature(nature_vector, spread)
            if nature and check_EV_optimality(base_stats, nature, spread):
                spreads.append((
                    508 - total_EVs,
                    (nature, spread),
                    attack_EVs,
                    defense_EVs_adj,
                    special_attack_EVs,
                    special_defense_EVs_adj,
                    speed_EVs
                ))

    # remove identical spreads.. probably a more Pythonic way
    seen_spreads = set()
    spreads_uniq = []
    for spread in spreads:
        if spread[1] not in seen_spreads:
            spreads_uniq.append(spread)
            seen_spreads.add(spread[1])
    
    # TODO: remove any that are directly worse than another

    # sort by number of remaining EVs (less is better)
    if bias1:
        bias1_index = STAT_NAMES.index(bias1)
        if bias2:
            bias2_index = STAT_NAMES.index(bias2)
            return sorted(spreads_uniq, key=lambda x: (x[0], -(x[1][1][bias1_index] + x[1][1][bias2_index])))[:num_spreads]
        else:
            return sorted(spreads_uniq, key=lambda x: (x[0], -x[1][1][bias1_index]))[:num_spreads]
    else:
        return sorted(spreads_uniq, key=lambda x: x[0])[:num_spreads]


def main(argv):
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("input_file", help="paste of mon to allocate EVs for")
    arg_parser.add_argument("--num_mons", help="number of top meta mons to include in EV spread optimization (default: 12)", default=12, type=int, metavar="NUM_MONS", required=False)
    arg_parser.add_argument("--num_spreads", help="number of EV spreads to suggest (default: 5)", default=5, type=int, metavar="NUM_SPREADS", required=False)
    arg_parser.add_argument("--bias1", help="first stat to favor, one of (HP, Atk, Def, SpA, SpD, Spe) (default: none) (at least one bias recommended)", default=None, metavar="BIAS1", required=False)
    arg_parser.add_argument("--bias2", help="second stat to favor, one of (HP, Atk, Def, SpA, SpD, Spe) (default: none)", default=None, metavar="BIAS2", required=False)
    arg_parser.add_argument("--moveset_url", help="override the default Smogon metagame moveset file url (default: latest VGC metagame at highest rating)",
        default="https://www.smogon.com/stats/2023-11/moveset/gen9vgc2023regulationebo3-1760.txt", metavar="MOVESET_URL", required=False)
    arg_parser.add_argument("--chaos_url", help="override the default Smogon metagame chaos file url (default: latest VGC metagame at highest rating)",
        default="https://www.smogon.com/stats/2023-11/chaos/gen9vgc2023regulationebo3-1760.json", metavar="CHAOS_URL", required=False)

    args = arg_parser.parse_args()

    #mon_name = "Ninetales-Alola"
    #mon_data = {"Ability": "Snow Warning", "Item": "Light Clay", "Moves": ["Aurora Veil", "Blizzard", "Moonblast", "Protect"]}
    #mon_data = dirtyjson.loads(open(args.input_file).read())
    mon_data = parse.import_from_paste(open(args.input_file).read())
    mon_name = mon_data["Name"]

    print("Parsing metagame files...")
    meta_mons = parse.get_mons(args.moveset_url, args.chaos_url, args.num_mons)

    print("Calculating speed benchmarks...")
    speed_benchmarks = speed.get_speed_benchmarks(meta_mons)
    speed_EVs = speed.allocate_speed_EVs(mon_name, mon_data, speed_benchmarks, tailwind=False)
    #pprint(speed_EVs)
    #print(len(speed_EVs))

    print("Calculating offensive benchmarks...")
    offensive_benchmarks = offenses.get_offensive_benchmarks(mon_name, mon_data, meta_mons)
    offensive_EVs = offenses.allocate_offensive_EVs(mon_name, mon_data, offensive_benchmarks)
    #pprint(offensive_EVs)
    #print(len(offensive_EVs[0]), len(offensive_EVs[1]))

    print("Calculating defensive benchmarks...")
    defensive_EVs = defenses.allocate_defensive_EVs(mon_name, mon_data, meta_mons)
    #pprint(defensive_EVs)
    #print(len(defensive_EVs[0]), len(defensive_EVs[1]))

    print("Optimizing EVs...")
    #optimized_EVs = optimize_EVs(offensive_EVs, defensive_EVs, speed_EVs, 5)
    optimized_EVs = optimize_EVs(mon_name, offensive_EVs, defensive_EVs, speed_EVs, args.num_spreads, bias1=args.bias1, bias2=args.bias2)
    #optimized_EVs = optimize_EVs(offensive_EVs, defensive_EVs, speed_EVs, 5, bias1="def", bias2="spd")

    print("Done! Printing suggested EVs spreads...\n")
    #pprint(optimized_EVs)
    for EVs in optimized_EVs:
        parse.print_EV_calcs(mon_name, mon_data, *EVs[1], EVs[0], *EVs[2:])


if __name__ == "__main__":
    main(sys.argv)
