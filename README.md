# EV Me

## Overview

EV Me is a command line tool that optimizes EV investment for a Pokémon for a specific metagame, given the Pokémon's desired held item, ability, and moves.

## Installation

Clone this repo:
```
git clone https://github.com/jamesjiang52/EVMe.git
cd EVMe
```

Install required libraries:
```
pip install -r requirements.txt
npm install
```

## Usage

Run:
```
cd src/
python optimize.py input_example
```

```
usage: optimize.py [-h] [--num_mons NUM_MONS] [--num_spreads NUM_SPREADS] [--bias1 BIAS1] [--bias2 BIAS2] [--moveset_url MOVESET_URL] [--chaos_url CHAOS_URL] input_file

positional arguments:
  input_file            paste of mon to allocate EVs for

optional arguments:
  -h, --help            show this help message and exit
  --num_mons NUM_MONS   number of top meta mons to include in EV spread optimization (default: 12)
  --num_spreads NUM_SPREADS
                        number of EV spreads to suggest (default: 5)
  --bias1 BIAS1         first stat to favor, one of (HP, Atk, Def, SpA, SpD, Spe) (default: none) (at least one bias recommended)
  --bias2 BIAS2         second stat to favor, one of (HP, Atk, Def, SpA, SpD, Spe) (default: none)
  --moveset_url MOVESET_URL
                        override the default Smogon metagame moveset file url (default: latest VGC metagame at highest rating)
  --chaos_url CHAOS_URL
                        override the default Smogon metagame chaos file url (default: latest VGC metagame at highest rating)
```

### Input example

The input file should be a valid PokéPaste of a single Pokémon, with its held item, ability, and at least one move specified. Other fields (EVs, level, shiny) will be ignored if present.

```
Ninetales-Alola @ Light Clay  
Ability: Snow Warning  
- Aurora Veil  
- Blizzard  
- Icy Wind  
- Protect
```

### Output example

```
================================================================================
Suggested nature:           Timid
Suggested EV spread:        140 HP / 0 Atk / 244 Def / 20 SpA / 84 SpD / 20 Spe
Remaining EVs:              0

Attack benchmark:           N/A
Defense benchmark:          252+ Atk Unseen Fist Life Orb Urshifu-Rapid-Strike Close Combat vs. 140 HP / 244 Def Light Clay Snow Warning Ninetales-Alola: 84.3 - 99.4% -- 0.0% chance to OHKO
Special attack benchmark:   20 SpA Light Clay Snow Warning Ninetales-Alola Blizzard vs. 244 HP / 44 SpD Grassy Surge Miracle Seed Rillaboom: 49.5 - 58.3% -- 96.5% chance to 2HKO
Special defense benchmark:  100 SpA Protosynthesis Booster Energy Flutter Mane Moonblast vs. 140 HP / 84 SpD Light Clay Snow Warning Ninetales-Alola: 41.6 - 49.4% -- 0.0% chance to 2HKO
Speed benchmark:            212 Spe Urshifu-Rapid-Strike
================================================================================

================================================================================
Suggested nature:           Timid
Suggested EV spread:        52 HP / 0 Atk / 252 Def / 20 SpA / 164 SpD / 20 Spe
Remaining EVs:              0

Attack benchmark:           N/A
Defense benchmark:          156+ Atk Unseen Fist Life Orb Urshifu-Rapid-Strike Close Combat vs. 52 HP / 252 Def Light Clay Snow Warning Ninetales-Alola: 83.9 - 98.7% -- 0.0% chance to OHKO
Special attack benchmark:   20 SpA Light Clay Snow Warning Ninetales-Alola Blizzard vs. 244 HP / 44 SpD Grassy Surge Miracle Seed Rillaboom: 49.5 - 58.3% -- 96.5% chance to 2HKO
Special defense benchmark:  100 SpA Protosynthesis Booster Energy Flutter Mane Moonblast vs. 52 HP / 164 SpD Light Clay Snow Warning Ninetales-Alola: 41.3 - 49.0% -- 0.0% chance to 2HKO
Speed benchmark:            212 Spe Urshifu-Rapid-Strike
================================================================================

================================================================================
Suggested nature:           Bold
Suggested EV spread:        28 HP / 0 Atk / 212 Def / 20 SpA / 196 SpD / 52 Spe
Remaining EVs:              0

Attack benchmark:           N/A
Defense benchmark:          116+ Atk Intimidate Choice Scarf Landorus-Therian Stomping Tantrum vs. 28 HP / 212+ Def Light Clay Snow Warning Ninetales-Alola: 41.4 - 49.3% -- 0.0% chance to 2HKO
Special attack benchmark:   20 SpA Light Clay Snow Warning Ninetales-Alola Blizzard vs. 244 HP / 44 SpD Grassy Surge Miracle Seed Rillaboom: 49.5 - 58.3% -- 96.5% chance to 2HKO
Special defense benchmark:  100 SpA Protosynthesis Booster Energy Flutter Mane Moonblast vs. 28 HP / 196 SpD Light Clay Snow Warning Ninetales-Alola: 41.4 - 49.3% -- 0.0% chance to 2HKO
Speed benchmark:            28 Spe Tornadus
================================================================================
```
