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
python optimize.py input_example.json
```

```
usage: optimize.py [-h] [--num_mons NUM_MONS] [--num_spreads NUM_SPREADS] [--bias1 BIAS1] [--bias2 BIAS2] [--override_url URL] input_file

positional arguments:
  input_file

optional arguments:
  -h, --help            show this help message and exit
  --num_mons NUM_MONS   number of top meta mons to include in EV spread optimization (default: 12)
  --num_spreads NUM_SPREADS
                        number of EV spreads to suggest (default: 5)
  --bias1 BIAS1         first stat to favor, one of (hp, atk, def, spa, spd, spe) (default: none)
  --bias2 BIAS2         second stat to favor, one of (hp, atk, def, spa, spd, spe) (default: none)
  --override_url URL    override the default Smogon metagame moveset file url (default: latest VGC metagame at highest rating)
```

### Input example

```
{
    "Name": "Ninetales-Alola",
    "Ability": "Snow Warning",
    "Item": "Light Clay",
    "Moves": ["Aurora Veil", "Blizzard", "Moonblast", "Protect"]
}
```

### Output example

```
================================================================================
Suggested nature:           Calm
Suggested EV spread:        92 HP / 0 Atk / 132 Def / 20 SpA / 244 SpD / 20 Spe
Remaining EVs:              0

Attack benchmark:           N/A
Defense benchmark:          84 Atk Intimidate Choice Scarf Landorus-Therian Stomping Tantrum vs. 92 HP / 132 Def Light Clay Snow Warning Ninetales-Alola: 41.9 - 49.4% -- 0.0% chance to 2HKO
Special attack benchmark:   20 SpA Light Clay Snow Warning Ninetales-Alola Blizzard vs. 244 HP / 44 SpD Grassy Surge Miracle Seed Rillaboom: 49.5 - 58.3% -- 96.5% chance to 2HKO
Special defense benchmark:  252+ SpA Protosynthesis Focus Sash Flutter Mane Moonblast vs. 92 HP / 244+ SpD Light Clay Snow Warning Ninetales-Alola: 41.9 - 49.4% -- 0.0% chance to 2HKO
Speed benchmark:            Outspeed 0 Spe Tornadus
================================================================================

================================================================================
Suggested nature:           Calm
Suggested EV spread:        92 HP / 0 Atk / 36 Def / 20 SpA / 244 SpD / 116 Spe
Remaining EVs:              0

Attack benchmark:           N/A
Defense benchmark:          252+ Atk Unseen Fist Choice Scarf Urshifu-Rapid-Strike Close Combat vs. 92 HP / 36 Def Light Clay Snow Warning Ninetales-Alola: 84.4 - 100.0% -- 6.2% chance to OHKO
Special attack benchmark:   20 SpA Light Clay Snow Warning Ninetales-Alola Blizzard vs. 244 HP / 44 SpD Grassy Surge Miracle Seed Rillaboom: 49.5 - 58.3% -- 96.5% chance to 2HKO
Special defense benchmark:  252+ SpA Protosynthesis Focus Sash Flutter Mane Moonblast vs. 92 HP / 244+ SpD Light Clay Snow Warning Ninetales-Alola: 41.9 - 49.4% -- 0.0% chance to 2HKO
Speed benchmark:            Outspeed 252 Spe Landorus-Therian
================================================================================

================================================================================
Suggested nature:           Timid
Suggested EV spread:        0 HP / 0 Atk / 212 Def / 236 SpA / 0 SpD / 60 Spe
Remaining EVs:              0

Attack benchmark:           N/A
Defense benchmark:          84 Atk Intimidate Choice Scarf Landorus-Therian Stomping Tantrum vs. 0 HP / 212 Def Light Clay Snow Warning Ninetales-Alola: 41.2 - 49.3% -- 0.0% chance to 2HKO
Special attack benchmark:   236 SpA Light Clay Snow Warning Ninetales-Alola Moonblast vs. 4 HP / 0 SpD Unseen Fist Choice Scarf Urshifu-Rapid-Strike: 100.0 - 119.3% -- 100.0% chance to OHKO
Special defense benchmark:  252 SpA Prankster Covert Cloak Tornadus Bleakwind Storm vs. 0 HP / 0 SpD Light Clay Snow Warning Ninetales-Alola: 41.2 - 49.3% -- 0.0% chance to 2HKO
Speed benchmark:            Outspeed 252 Spe Urshifu-Rapid-Strike
================================================================================
```
