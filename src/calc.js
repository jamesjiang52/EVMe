import {calculate, Pokemon, Move, Field} from '@smogon/calc';


function get_move_category() {
    const gen = 9;
    var move_name = process.argv[4];
    var move = new Move(gen, move_name);
    console.log(move.category)
}


function get_stats() {
    const gen = 9;

    var mon_name = process.argv[4];
    let hp_ivs = parseInt(process.argv[5]);
    let atk_ivs = parseInt(process.argv[6]);
    let def_ivs = parseInt(process.argv[7]);
    let spa_ivs = parseInt(process.argv[8]);
    let spd_ivs = parseInt(process.argv[9]);
    let spe_ivs = parseInt(process.argv[10]);
    let hp_evs = parseInt(process.argv[11]);
    let atk_evs = parseInt(process.argv[12]);
    let def_evs = parseInt(process.argv[13]);
    let spa_evs = parseInt(process.argv[14]);
    let spd_evs = parseInt(process.argv[15]);
    let spe_evs = parseInt(process.argv[16]);
    let level = parseInt(process.argv[17]);
    var nature = process.argv[18];
    var mon = new Pokemon(gen, mon_name, {
        level: level,
        nature: nature,
        ivs: {"hp": hp_ivs, "atk": atk_ivs, "def": def_ivs, "spa": spa_ivs, "spd": spd_ivs, "spe": spe_ivs},
        evs: {"hp": hp_evs, "atk": atk_evs, "def": def_evs, "spa": spa_evs, "spd": spd_evs, "spe": spe_evs}
    });

    console.log(mon.rawStats);
}

function do_damage_calc() {
    const gen = 9;

    var move_name = process.argv[4];
    var attack_mon_name = process.argv[5];
    var attack_mon_ability = process.argv[6];
    var attack_mon_item = process.argv[7];
    var attack_mon_nature = process.argv[8];
    let attack_mon_hp_evs = parseInt(process.argv[9]);
    let attack_mon_atk_evs = parseInt(process.argv[10]);
    let attack_mon_def_evs = parseInt(process.argv[11]);
    let attack_mon_spa_evs = parseInt(process.argv[12]);
    let attack_mon_spd_evs = parseInt(process.argv[13]);
    let attack_mon_spe_evs = parseInt(process.argv[14]);
    var defend_mon_name = process.argv[15]
    var defend_mon_ability = process.argv[16];
    var defend_mon_item = process.argv[17];
    var defend_mon_nature = process.argv[18];
    let defend_mon_hp_evs = parseInt(process.argv[19]);
    let defend_mon_atk_evs = parseInt(process.argv[20]);
    let defend_mon_def_evs = parseInt(process.argv[21]);
    let defend_mon_spa_evs = parseInt(process.argv[22]);
    let defend_mon_spd_evs = parseInt(process.argv[23]);
    let defend_mon_spe_evs = parseInt(process.argv[24]);
    let level = parseInt(process.argv[25]);
    
    var damage_calc = calculate(
        gen,
        new Pokemon(gen, attack_mon_name, {
            ability: attack_mon_ability,
            abilityOn: true,
            item: attack_mon_item,
            boostedStat: 'auto',  // protosynthesis
            nature: attack_mon_nature,
            evs: {"hp": attack_mon_hp_evs, "atk": attack_mon_atk_evs, "def": attack_mon_def_evs, "spa": attack_mon_spa_evs, "spd": attack_mon_spd_evs, "spe": attack_mon_spe_evs},
            level: level
        }),
        new Pokemon(gen, defend_mon_name, {
            ability: defend_mon_ability,
            abilityOn: true,
            item: defend_mon_item,
            boostedStat: 'auto',  // protosynthesis
            nature: defend_mon_nature,
            evs: {"hp": defend_mon_hp_evs, "atk": defend_mon_atk_evs, "def": defend_mon_def_evs, "spa": defend_mon_spa_evs, "spd": defend_mon_spd_evs, "spe": defend_mon_spe_evs},
            level: level
        }),
        new Move(gen, move_name),
        new Field({gameType: "Doubles"})
    );
    
    var bp;
    if ("moveBP" in damage_calc.rawDesc)
        bp = damage_calc.rawDesc.moveBP;
    else
        bp = damage_calc.move.bp;

    //console.log(damage_calc)
    console.log({
        "Damage rolls": damage_calc.damage,
        "Attacker stats": damage_calc.attacker.stats,
        "Defender stats": damage_calc.defender.stats,
        "Move": [bp, damage_calc.move.category]
    });
}

export {get_move_category, get_stats, do_damage_calc};
