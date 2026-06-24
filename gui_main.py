import pygame
import sys
import time
from ftl_cli.models.base import Ship, Room, System, SystemType, Crew, Weapon
from ftl_cli.engine import GameState, GameEngine
from ftl_cli.ui.pygame_renderer import PygameRenderer

def create_initial_ship():
    rooms = [
        Room("Pilot", 8, 2, 2, 2, System(SystemType.PILOT, 1)),
        Room("Shields", 4, 2, 2, 2, System(SystemType.SHIELDS, 2)),
        Room("Weapons", 4, 0, 2, 2, System(SystemType.WEAPONS, 2)),
        Room("Engines", 2, 2, 2, 2, System(SystemType.ENGINES, 2)),
        Room("Medbay", 4, 4, 2, 2, System(SystemType.MEDBAY, 1)),
        Room("Oxygen", 6, 2, 2, 2, System(SystemType.OXYGEN, 1)),
    ]
    ship = Ship("The Kestrel", rooms)
    ship.systems[SystemType.PILOT].current_power = 1
    ship.systems[SystemType.SHIELDS].current_power = 2
    ship.systems[SystemType.WEAPONS].current_power = 2
    ship.systems[SystemType.ENGINES].current_power = 1
    ship.systems[SystemType.OXYGEN].current_power = 1
    ship.reactor_used = 7
    ship.weapons.append(Weapon("Burst Laser", 1, 3.0, 2, shots=3))
    c1 = Crew("Jules")
    c1.room = rooms[0]
    rooms[0].crew_members.append(c1)
    ship.crew.append(c1)
    return ship

def create_enemy_ship():
    rooms = [
        Room("Pilot", 0, 1, 2, 2, System(SystemType.PILOT, 1)),
        Room("Shields", 2, 1, 2, 2, System(SystemType.SHIELDS, 2)),
        Room("Weapons", 2, 3, 2, 2, System(SystemType.WEAPONS, 1)),
    ]
    ship = Ship("Rebel Scout", rooms)
    ship.systems[SystemType.PILOT].current_power = 1
    ship.systems[SystemType.SHIELDS].current_power = 2
    ship.systems[SystemType.WEAPONS].current_power = 1
    ship.weapons.append(Weapon("Basic Laser", 1, 5.0, 1))
    return ship

def get_available_weapons():
    return [
        Weapon("Burst Laser II", 1, 3.0, 2, shots=3, weapon_type=WeaponType.LASER, scrap_cost=80),
        Weapon("Artemis Missile", 2, 4.0, 1, weapon_type=WeaponType.MISSILE, scrap_cost=50),
        Weapon("Ion Blast", 1, 2.0, 1, weapon_type=WeaponType.ION, scrap_cost=40),
        Weapon("Mini Beam", 2, 5.0, 1, weapon_type=WeaponType.BEAM, scrap_cost=60),
        Weapon("Flak I", 1, 4.0, 2, shots=3, weapon_type=WeaponType.LASER, scrap_cost=65),
    ]

def main():
    FPS = 60
    player_ship = create_initial_ship()
    state = GameState(player_ship)
    state.enemy_ship = create_enemy_ship()

    engine = GameEngine(state)
    renderer = PygameRenderer()

    clock = pygame.time.Clock()
    selection = {"crew": None}

    running = True
    while running:
        # Handle Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if state.is_paused:
                    mouse_pos = pygame.mouse.get_pos()
                    ship = state.player_ship
                    enemy = state.enemy_ship

                    # Logic to handle clicks on rooms or systems
                    # For now, let's keep it simple with keyboard,
                    # but we could add mouse selection here.
                    pass
            elif event.type == pygame.KEYDOWN:
                key = event.key
                ship = state.player_ship

                if key == pygame.K_SPACE:
                    state.is_paused = not state.is_paused
                elif key == pygame.K_q:
                    running = False

                # Input handling
                if state.is_paused:
                    mods = pygame.key.get_mods()
                    is_shift = mods & pygame.KMOD_SHIFT

                    # Unified power handler
                    def adjust_power(sys_type, delta):
                        sys = ship.systems.get(sys_type)
                        if not sys: return
                        if delta > 0:
                            if sys.current_power < sys.health and ship.reactor_available > 0:
                                sys.current_power += 1
                                ship.reactor_used += 1
                        else:
                            if sys.current_power > 0:
                                sys.current_power -= 1
                                ship.reactor_used -= 1

                    if key == pygame.K_w:
                        adjust_power(SystemType.WEAPONS, -1 if is_shift else 1)
                    elif key == pygame.K_s:
                        adjust_power(SystemType.SHIELDS, -1 if is_shift else 1)
                    elif key == pygame.K_e:
                        adjust_power(SystemType.ENGINES, -1 if is_shift else 1)
                    elif key == pygame.K_o:
                        adjust_power(SystemType.OXYGEN, -1 if is_shift else 1)
                    elif key == pygame.K_m:
                        adjust_power(SystemType.MEDBAY, -1 if is_shift else 1)
                    elif key == pygame.K_p:
                        adjust_power(SystemType.PILOT, -1 if is_shift else 1)
                    elif key == pygame.K_u:
                        if ship.scrap >= 20:
                            ship.scrap -= 20
                            ship.reactor_max += 1
                            state.add_log("Upgraded Reactor (+1 Power)")
                    elif key == pygame.K_h:
                        if ship.scrap >= 10 and ship.hull < ship.max_hull:
                            ship.scrap -= 10
                            ship.hull = min(ship.max_hull, ship.hull + 5)
                            state.add_log("Healed Hull (+5)")
                    elif key == pygame.K_c:
                        if not selection["crew"]:
                            selection["crew"] = ship.crew[0] if ship.crew else None
                        else:
                            idx = ship.crew.index(selection["crew"])
                            selection["crew"] = ship.crew[(idx + 1) % len(ship.crew)]
                        state.add_log(f"Selected: {selection['crew'].name if selection['crew'] else 'None'}")
                    elif pygame.K_4 <= key <= pygame.K_9:
                        if selection["crew"]:
                            room_idx = key - pygame.K_4
                            if 0 <= room_idx < len(ship.rooms):
                                target = ship.rooms[room_idx]
                                selection["crew"].move_to(target)
                                state.add_log(f"Moving {selection['crew'].name} to {target.id}")
                    elif key == pygame.K_t and state.enemy_ship:
                        enemy = state.enemy_ship
                        if not state.selected_target_room or state.selected_target_room not in enemy.rooms:
                            state.selected_target_room = enemy.rooms[0]
                        else:
                            idx = enemy.rooms.index(state.selected_target_room)
                            state.selected_target_room = enemy.rooms[(idx + 1) % len(enemy.rooms)]
                        state.add_log(f"Targeting enemy {state.selected_target_room.id}")
                    elif key == pygame.K_j and not state.enemy_ship and not state.is_jumping:
                        state.is_jumping = True
                        state.is_paused = False
                        state.add_log("Initiating FTL Jump...")
                    elif key == pygame.K_s and not state.enemy_ship:
                        # Simple Shop
                        available = get_available_weapons()
                        # Buy the first one you don't have and can afford
                        for w in available:
                            if w.name not in [pw.name for pw in ship.weapons] and ship.scrap >= w.scrap_cost:
                                ship.scrap -= w.scrap_cost
                                ship.weapons.append(w)
                                state.add_log(f"Purchased {w.name} for {w.scrap_cost} scrap.")
                                break

        # Update
        engine.update()

        # Render
        renderer.render(state)

        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
