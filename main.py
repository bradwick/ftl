import time
import sys
from blessed import Terminal
from ftl_cli.models.base import Ship, Room, System, SystemType, Crew, Weapon
from ftl_cli.engine import GameState, GameEngine
from ftl_cli.ui.renderer import Renderer

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

def main():
    term = Terminal()
    player_ship = create_initial_ship()
    state = GameState(player_ship)
    state.enemy_ship = create_enemy_ship()

    engine = GameEngine(state)
    renderer = Renderer(term)

    selection = {"crew": None}

    def handle_input(val, state):
        ship = state.player_ship
        if val == ' ':
            state.is_paused = not state.is_paused
        elif val == 'u' and state.is_paused:
            # Simple Upgrade Menu
            if ship.scrap >= 20:
                ship.scrap -= 20
                ship.reactor_max += 1
                state.add_log("Upgraded Reactor (+1 Power)")
        elif val == 'h' and state.is_paused:
            # Simple Heal
            if ship.scrap >= 10 and ship.hull < ship.max_hull:
                ship.scrap -= 10
                ship.hull = min(ship.max_hull, ship.hull + 5)
                state.add_log("Healed Hull (+5)")
        elif val == '1' and state.is_paused:
            # Power weapons
            sys = ship.systems.get(SystemType.WEAPONS)
            if sys and sys.current_power < sys.max_power and ship.reactor_available > 0:
                sys.current_power += 1
                ship.reactor_used += 1
        elif val == '!' and state.is_paused:
            # Unpower weapons
            sys = ship.systems.get(SystemType.WEAPONS)
            if sys and sys.current_power > 0:
                sys.current_power -= 1
                ship.reactor_used -= 1
        elif val == 'j' and state.is_paused and not state.enemy_ship and not state.is_jumping:
            # Jump
            state.is_jumping = True
            state.is_paused = False
            state.add_log("Initiating FTL Jump...")
        elif val == 'c' and state.is_paused:
            # Cycle crew selection
            if not selection["crew"]:
                selection["crew"] = ship.crew[0] if ship.crew else None
            else:
                idx = ship.crew.index(selection["crew"])
                selection["crew"] = ship.crew[(idx + 1) % len(ship.crew)]
            state.add_log(f"Selected: {selection['crew'].name if selection['crew'] else 'None'}")
        elif val.isdigit() and int(val) >= 4 and state.is_paused:
            # Move selected crew to room index
            if selection["crew"]:
                room_idx = int(val) - 4
                if 0 <= room_idx < len(ship.rooms):
                    target = ship.rooms[room_idx]
                    selection["crew"].move_to(target)
                    state.add_log(f"Moving {selection['crew'].name} to {target.id}")
        elif val == 't' and state.is_paused and state.enemy_ship:
            # Cycle enemy target room
            enemy = state.enemy_ship
            if not state.selected_target_room:
                state.selected_target_room = enemy.rooms[0]
            else:
                idx = enemy.rooms.index(state.selected_target_room)
                state.selected_target_room = enemy.rooms[(idx + 1) % len(enemy.rooms)]
            state.add_log(f"Targeting enemy {state.selected_target_room.id}")
        elif val == '2' and state.is_paused:
            # Power shields
            sys = ship.systems.get(SystemType.SHIELDS)
            if sys and sys.current_power < sys.max_power and ship.reactor_available > 0:
                sys.current_power += 1
                ship.reactor_used += 1
        elif val == '"' and state.is_paused:
            # Unpower shields
            sys = ship.systems.get(SystemType.SHIELDS)
            if sys and sys.current_power > 0:
                sys.current_power -= 1
                ship.reactor_used -= 1

    # Check if we are in a non-interactive environment (like a test)
    if not sys.stdout.isatty():
        print("Non-interactive terminal detected, running headless test...")
        state.is_paused = False
        for _ in range(10):
            engine.update()
            renderer.render(state)
            time.sleep(0.01)
        print("Headless test complete.")
        return

    with term.cbreak(), term.hidden_cursor():
        print(term.clear)
        while not state.game_over:
            val = term.inkey(timeout=0.05)
            if val.lower() == 'q':
                break

            handle_input(val, state)

            engine.update()
            renderer.render(state)
            time.sleep(0.01)

    print(term.clear)
    print("Thanks for playing FTL-CLI!")

if __name__ == "__main__":
    main()
