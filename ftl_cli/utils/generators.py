import random
from ftl_cli.models.base import Ship, Room, System, SystemType, Weapon

def generate_enemy(difficulty: int) -> Ship:
    # Difficulty scales systems and weapons
    pilot_power = 1
    shield_power = min(8, (difficulty // 2) * 2) # Shields go up in steps of 2
    weapon_power = min(8, difficulty)
    engine_power = min(5, 1 + difficulty // 3)

    rooms = [
        Room("Pilot", 0, 1, 2, 2, System(SystemType.PILOT, pilot_power)),
        Room("Shields", 2, 1, 2, 2, System(SystemType.SHIELDS, max(2, shield_power))),
        Room("Weapons", 2, 3, 2, 2, System(SystemType.WEAPONS, weapon_power)),
        Room("Engines", 0, 3, 2, 2, System(SystemType.ENGINES, engine_power)),
    ]

    name = random.choice(["Rebel Scout", "Auto-Assault", "Pirate Rigger", "Mantis Fighter"])
    ship = Ship(f"{name} (Lvl {difficulty})", rooms)

    # Power systems
    for sys in ship.systems.values():
        sys.current_power = sys.max_power

    # Add weapons based on difficulty
    if difficulty < 3:
        ship.weapons.append(Weapon("Basic Laser", 1, 5.0, 1))
    elif difficulty < 6:
        ship.weapons.append(Weapon("Dual Lasers", 1, 4.0, 1, shots=2))
    elif difficulty < 9:
        ship.weapons.append(Weapon("Burst Laser II", 1, 3.0, 2, shots=3))
    else:
        ship.weapons.append(Weapon("Flak I", 1, 4.0, 2, shots=3))
        ship.weapons.append(Weapon("Heavy Laser", 2, 5.0, 1))

    return ship
