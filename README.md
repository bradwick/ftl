# FTL-CLI

An FTL clone for the command line.

## Requirements

- Python 3.x
- `blessed` library

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python3 main.py
```

### GUI Version (Recommended)

```bash
python3 gui_main.py
```

## Controls (Paused)

- `SPACE`: Pause / Unpause
- `1` / `!`: Power / Unpower Weapons
- `2` / `"`: Power / Unpower Shields
- `c`: Cycle selected crew member
- `4-9`: Move selected crew to specified room (see ROOMS list)
- `t`: Cycle target enemy room
- `u`: Upgrade Reactor (20 Scrap)
- `h`: Heal Hull (10 Scrap)
- `q`: Quit

## Gameplay

Manage your ship's systems and crew in real-time. Power your weapons to fire at the enemy, and your shields to absorb incoming fire. As you destroy enemies, you gain scrap which can be used to upgrade your reactor or repair your hull.

Crew members gain skills in the systems they man, providing bonuses to recharge rates and evasion.
