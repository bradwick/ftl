from enum import Enum, auto
from typing import List, Tuple, Dict, Optional

class SystemType(Enum):
    PILOT = auto()
    SHIELDS = auto()
    WEAPONS = auto()
    ENGINES = auto()
    OXYGEN = auto()
    MEDBAY = auto()
    SENSORS = auto()
    DOORS = auto()

class System:
    def __init__(self, system_type: SystemType, max_power: int):
        self.type = system_type
        self.max_power = max_power
        self.current_power = 0
        self.health = max_power  # 1 health point per power bar
        self.is_manned = False
        self.manned_bonus = 0.0

    @property
    def is_functional(self) -> bool:
        return self.health > 0 and self.current_power > 0

    def take_damage(self, amount: int) -> int:
        """Returns the amount of power lost due to damage."""
        old_power = self.current_power
        self.health = max(0.0, float(self.health) - amount)
        self.current_power = min(self.current_power, int(self.health))
        return old_power - self.current_power

    def repair(self, amount: float):
        self.health = min(self.max_power, self.health + amount)

class Room:
    def __init__(self, id: str, x: int, y: int, w: int, h: int, system: Optional[System] = None):
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.system = system
        self.crew_members = []
        self.fire_level = 0.0  # 0 to 100
        self.oxygen = 100.0    # 0 to 100

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def contains_point(self, px: int, py: int) -> bool:
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h

class Crew:
    def __init__(self, name: str, race: str = "Human"):
        self.name = name
        self.race = race
        self.health = 100.0
        self.max_health = 100.0
        self.room: Optional[Room] = None
        self.target_room: Optional[Room] = None
        self.movement_progress = 0.0
        self.movement_speed = 1.0 # rooms per second roughly

        # Skills (0.0 to 1.0)
        self.skills = {
            "pilot": 0.0,
            "engines": 0.0,
            "shields": 0.0,
            "weapons": 0.0,
            "repair": 0.0,
            "combat": 0.0
        }

    def move_to(self, target_room: Room):
        self.target_room = target_room

class WeaponType(Enum):
    LASER = auto()
    MISSILE = auto()
    ION = auto()
    BEAM = auto()

class Weapon:
    def __init__(self, name: str, damage: int, cooldown: float, power_req: int, shots: int = 1, weapon_type: WeaponType = WeaponType.LASER, scrap_cost: int = 50):
        self.name = name
        self.damage = damage
        self.cooldown_max = cooldown
        self.cooldown_current = 0.0
        self.power_req = power_req
        self.shots = shots
        self.type = weapon_type
        self.is_active = False
        self.scrap_cost = scrap_cost

    def update(self, dt: float, powered: bool):
        if powered:
            self.cooldown_current = min(self.cooldown_max, self.cooldown_current + dt)
        else:
            # Maybe slowly drain cooldown if unpowered? FTL resets it or drains it.
            # Let's say it stays where it is for now but can't fire.
            pass

    @property
    def is_ready(self) -> bool:
        return self.cooldown_current >= self.cooldown_max

    def fire(self):
        self.cooldown_current = 0.0

class Ship:
    def __init__(self, name: str, rooms: List[Room]):
        self.name = name
        self.hull = 30
        self.max_hull = 30
        self.rooms = rooms
        self.systems: Dict[SystemType, System] = {}
        for r in rooms:
            if r.system:
                self.systems[r.system.type] = r.system

        self.crew: List[Crew] = []
        self.weapons: List[Weapon] = []

        self.scrap = 0
        self.fuel = 10
        self.missiles = 0
        self.drone_parts = 0

        self.reactor_max = 10
        self.reactor_used = 0

    @property
    def reactor_available(self) -> int:
        return self.reactor_max - self.reactor_used

    def get_room_at(self, x: int, y: int) -> Optional[Room]:
        for r in self.rooms:
            if r.contains_point(x, y):
                return r
        return None
