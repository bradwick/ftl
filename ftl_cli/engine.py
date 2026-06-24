import time
import random
from typing import List, Optional, Callable
from ftl_cli.models.base import Ship, Crew, SystemType, Room, WeaponType
from ftl_cli.utils.pathfinding import find_path
from ftl_cli.utils.generators import generate_enemy

class GameState:
    def __init__(self, player_ship: Ship):
        self.player_ship = player_ship
        self.enemy_ship: Optional[Ship] = None
        self.is_paused = True
        self.game_over = False
        self.log: List[str] = ["Welcome to FTL-CLI!", "Press SPACE to pause/unpause."]
        self.time_acc = 0.0
        self.difficulty = 1
        self.encounters_won = 0
        self.selected_target_room: Optional[Room] = None
        self.sector = 1
        self.beacons_in_sector = 5
        self.current_beacon = 0
        self.is_jumping = False
        self.jump_timer = 0.0

    def add_log(self, message: str):
        self.log.append(message)
        if len(self.log) > 100:
            self.log.pop(0)

class GameEngine:
    def __init__(self, state: GameState):
        self.state = state
        self.last_update = time.time()

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        if self.state.is_paused or self.state.game_over:
            return

        # Jump Logic
        if self.state.is_jumping:
            self.state.jump_timer += dt
            if self.state.jump_timer >= 3.0:
                self.state.is_jumping = False
                self.state.jump_timer = 0.0
                self.state.current_beacon += 1
                if self.state.current_beacon >= self.state.beacons_in_sector:
                    self.state.sector += 1
                    self.state.current_beacon = 0
                    self.state.add_log(f"Entering Sector {self.state.sector}...")

                # Boss check
                if self.state.sector == 3 and self.state.current_beacon == self.state.beacons_in_sector - 1:
                    self.state.enemy_ship = self._generate_boss()
                    self.state.selected_target_room = None
                    self.state.add_log("WARNING: REBEL FLAGSHIP DETECTED!")
                else:
                    self.state.enemy_ship = generate_enemy(self.state.difficulty)
                    self.state.selected_target_room = None
                    self.state.add_log(f"Jump complete! Warning: {self.state.enemy_ship.name} detected!")
            return # Don't update ships while jumping

        # Progression: Spawn enemy if none exists and not jumping
        if not self.state.enemy_ship and not self.state.is_jumping:
            # Player needs to initiate jump
            pass

        self._update_ship(self.state.player_ship, dt)
        if self.state.enemy_ship:
            self._update_ship(self.state.enemy_ship, dt)

        # Handle Combat logic here
        self._handle_combat(dt)

    def _update_ship(self, ship: Ship, dt: float):
        # Update Crew movement
        for crew in ship.crew:
            if crew.target_room and crew.target_room != crew.room:
                # Find path if not already on it
                path = find_path(crew.room, crew.target_room, ship.rooms)
                if path and len(path) > 1:
                    next_room = path[1]
                    crew.movement_progress += dt * crew.movement_speed
                    if crew.movement_progress >= 1.0:
                        # Arrived at next room
                        crew.room.crew_members.remove(crew)
                        crew.room = next_room
                        crew.room.crew_members.append(crew)
                        crew.movement_progress = 0.0
                        if crew.room == crew.target_room:
                            crew.target_room = None
                else:
                    crew.target_room = None # Unreachable or already there

        # Update Systems
        for system in ship.systems.values():
            # Oxygen logic
            if system.type == SystemType.OXYGEN:
                oxygen_change = dt * 3.0 if system.is_functional else -dt * 1.5
                for room in ship.rooms:
                    room.oxygen = max(0.0, min(100.0, room.oxygen + oxygen_change))
                    if room.oxygen < 10.0:
                        for c in room.crew_members:
                            c.health -= dt * 3.0 # Suffocation damage

            # Medbay logic
            if system.type == SystemType.MEDBAY and system.is_functional:
                for room in ship.rooms:
                    if room.system and room.system.type == SystemType.MEDBAY:
                        for c in room.crew_members:
                            c.health = min(c.max_health, c.health + dt * 15.0)

            # Update Crew skills if manning
            for crew in ship.crew:
                if crew.room and crew.room.system == system and not self.state.is_paused:
                    skill_map = {
                        SystemType.PILOT: "pilot",
                        SystemType.ENGINES: "engines",
                        SystemType.SHIELDS: "shields",
                        SystemType.WEAPONS: "weapons"
                    }
                    if system.type in skill_map:
                        skill_name = skill_map[system.type]
                        crew.skills[skill_name] = min(1.0, crew.skills[skill_name] + dt * 0.01) # 100 seconds to master

            # Shield recharge logic
            if system.type == SystemType.SHIELDS:
                if not hasattr(system, 'bubbles'):
                    system.bubbles = system.current_power // 2
                    system.recharge = 0.0

                max_bubbles = system.current_power // 2
                if system.bubbles < max_bubbles and system.is_functional:
                    system.recharge += dt
                    recharge_time = 2.0 # 2 seconds per bubble
                    if system.is_manned: recharge_time *= 0.8
                    if system.recharge >= recharge_time:
                        system.bubbles += 1
                        system.recharge = 0.0
                elif system.bubbles > max_bubbles:
                    system.bubbles = max_bubbles

            # Check if manned
            system.is_manned = any(c.room.system == system for c in ship.crew if c.room and c.room.system)

            # Repair logic
            if system.health < system.max_power:
                crew_repairing = [c for c in ship.crew if c.room and c.room.system == system]
                if crew_repairing and not self.state.is_paused:
                    repair_rate = 0.5 * len(crew_repairing) * dt # 0.5 HP per second per crew
                    system.repair(repair_rate)
            # FTL logic: manning provides bonuses
            if system.is_manned:
                # Find the best crew member for this system
                best_skill = 0.0
                skill_map = {SystemType.PILOT: "pilot", SystemType.ENGINES: "engines", SystemType.SHIELDS: "shields", SystemType.WEAPONS: "weapons"}
                if system.type in skill_map:
                    skill_name = skill_map[system.type]
                    best_skill = max([c.skills[skill_name] for c in ship.crew if c.room and c.room.system == system] + [0.0])

                system.manned_bonus = 0.1 + best_skill * 0.1 # 10% base + up to 10% skill bonus
            else:
                system.manned_bonus = 0.0

            # Fire logic (simplified for now)
            for room in ship.rooms:
                if room.fire_level > 0:
                    # Fire damages system in room
                    if room.system:
                        power_lost = room.system.take_damage(dt * 0.1) # Fire damage rate
                        ship.reactor_used -= power_lost
                    # Fire damages crew in room
                    for c in room.crew_members:
                        c.health -= dt * 5.0
                    # Fire spreads? (later)

                    # Crew fight fire
                    crew_in_room = len(room.crew_members)
                    if crew_in_room > 0:
                        room.fire_level -= dt * 20.0 * crew_in_room
                        if room.fire_level < 0: room.fire_level = 0

        # Update Weapons
        weapon_system = ship.systems.get(SystemType.WEAPONS)
        if weapon_system and weapon_system.is_functional:
            # Simple power allocation: power first N weapons that fit in current_power
            power_remaining = weapon_system.current_power
            for w in ship.weapons:
                if power_remaining >= w.power_req:
                    w.is_active = True
                    power_remaining -= w.power_req
                    # Weapon charge bonus from manning
                    w.update(dt * (1.0 + weapon_system.manned_bonus), True)
                else:
                    w.is_active = False
                    w.update(dt, False)
        else:
            for w in ship.weapons:
                w.is_active = False
                w.update(dt, False)

    def _handle_combat(self, dt: float):
        if not self.state.enemy_ship:
            return

        # Player firing
        self._fire_weapons(self.state.player_ship, self.state.enemy_ship)

        # Check if enemy survived
        if not self.state.enemy_ship:
            return

        # Enemy firing
        self._fire_weapons(self.state.enemy_ship, self.state.player_ship)

    def _generate_boss(self) -> Ship:
        # Boss is a very beefy ship
        ship = generate_enemy(10) # High difficulty
        ship.name = "REBEL FLAGSHIP"
        ship.hull = 100
        ship.max_hull = 100
        return ship

    def _fire_weapons(self, attacker: Ship, target: Ship):
        for w in attacker.weapons:
            if w.is_active and w.is_ready:
                w.fire()
                self.state.add_log(f"{attacker.name} fires {w.name}!")

                # Player targeting
                target_room = None
                if attacker == self.state.player_ship:
                    target_room = self.state.selected_target_room

                # Impact logic: each shot can be evaded or shielded
                for _ in range(w.shots):
                    if target.hull > 0:
                        self._apply_damage(target, w.damage, target_room, w.type)

    def _apply_damage(self, target: Ship, damage: int, forced_target_room: Optional[Room] = None, weapon_type: WeaponType = WeaponType.LASER):
        # Evasion check (Engines + Pilot)
        # Beams cannot be evaded
        evasion = 0.0
        engine_sys = target.systems.get(SystemType.ENGINES)
        pilot_sys = target.systems.get(SystemType.PILOT)

        if pilot_sys and pilot_sys.is_functional:
            evasion += 0.05 # Base 5%
            if engine_sys and engine_sys.is_functional:
                evasion += engine_sys.current_power * 0.05 # 5% per power bar
                evasion += engine_sys.manned_bonus # Engine manning bonus

            evasion += pilot_sys.manned_bonus # Pilot manning bonus

        if weapon_type != WeaponType.BEAM and random.random() < evasion:
            self.state.add_log(f"Miss! ({target.name} evaded)")
            return

        # Shields first
        shield_sys = target.systems.get(SystemType.SHIELDS)
        if shield_sys and shield_sys.is_functional and weapon_type != WeaponType.MISSILE:
            if not hasattr(shield_sys, 'bubbles'):
                shield_sys.bubbles = shield_sys.current_power // 2
                shield_sys.recharge = 0.0

            if shield_sys.bubbles > 0:
                if weapon_type == WeaponType.ION:
                    # Ion damages shields directly
                    shield_sys.take_damage(1)
                    target.reactor_used -= 1

                shield_sys.bubbles -= 1
                self.state.add_log(f"Shields absorbed damage!")
                return

        # Hull damage
        target.hull = max(0, target.hull - damage)
        self.state.add_log(f"{target.name} hit for {damage} damage!")

        # System damage
        if target.rooms:
            hit_room = forced_target_room if forced_target_room and forced_target_room in target.rooms else random.choice(target.rooms)
            if hit_room.system:
                power_lost = hit_room.system.take_damage(1) # Systems take 1 damage per hit
                target.reactor_used -= power_lost
                self.state.add_log(f"{hit_room.id} system damaged!")

            # Fire chance
            if random.random() < 0.1: # 10% fire chance
                hit_room.fire_level = 100.0
                self.state.add_log(f"Fire started in {hit_room.id}!")

        if target.hull <= 0:
            target.hull = 0
            self.state.add_log(f"{target.name} destroyed!")
            if target == self.state.player_ship:
                self.state.game_over = True
            else:
                # Enemy destroyed, player gets scrap
                scrap_gain = 10 + self.state.difficulty * 5
                self.state.player_ship.scrap += scrap_gain
                self.state.encounters_won += 1
                self.state.difficulty = 1 + self.state.encounters_won // 2
                self.state.enemy_ship = None
                self.state.add_log(f"Enemy destroyed! Received {scrap_gain} scrap.")
                self.state.add_log("Searching for next jump...")
                # In a real game, we'd wait for a jump.
                # Here, let's just spawn a new one after a short delay or immediately.
                # For simplicity, we'll spawn it in the next update if enemy_ship is None.
