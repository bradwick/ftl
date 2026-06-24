import time
from blessed import Terminal
from ftl_cli.models.base import Ship, Room, SystemType
from ftl_cli.engine import GameState

class Renderer:
    def __init__(self, term: Terminal):
        self.term = term
        self.width = term.width
        self.height = term.height

    def render(self, state: GameState):
        term = self.term
        output = term.home
        output += self._render_header(state)
        output += self._render_ships(state)
        output += self._render_footer(state)

        if state.is_paused:
            output += term.move_xy(term.width // 2 - 4, term.height // 2) + term.black_on_white(" PAUSED ")

        if state.game_over:
            output += term.move_xy(term.width // 2 - 5, term.height // 2 + 1) + term.black_on_white(" GAME OVER ")

        print(output, end='', flush=True)

    def _render_header(self, state: GameState):
        ship = state.player_ship
        hull_color = self.term.green if ship.hull > 15 else (self.term.yellow if ship.hull > 5 else self.term.red)
        header = f" HULL: [{self._progress_bar(ship.hull, ship.max_hull, 20, hull_color)}] | SCRAP: {self.term.yellow(str(ship.scrap))} | PWR: {self.term.cyan(str(ship.reactor_used))}/{self.term.cyan(str(ship.reactor_max))} | SECTOR: {state.sector} | BEACON: {state.current_beacon+1}/{state.beacons_in_sector}"
        return self.term.move_xy(0, 0) + header

    def _progress_bar(self, current, max_val, width, color_func=None):
        if max_val <= 0: return " " * width
        filled = int((max(0, current) / max_val) * width)
        bar = "█" * filled + "░" * (width - filled)
        if color_func:
            return color_func(bar)
        return bar

    def _render_ships(self, state: GameState):
        out = ""
        # Render Player Ship
        out += self._draw_ship_ascii(state.player_ship, 2, 3, "PLAYER")

        # Render Enemy Ship if exists
        if state.enemy_ship:
            out += self._draw_ship_ascii(state.enemy_ship, 80, 3, "ENEMY", is_enemy=True, target_room=state.selected_target_room)
        elif state.is_jumping:
            dots = "." * (int(time.time()*2)%4)
            out += self.term.move_xy(80, 10) + self.term.bold_cyan("FTL JUMP IN PROGRESS" + dots.ljust(3))
        else:
            out += self.term.move_xy(80, 10) + "NO ENEMY DETECTED. Press 'j' to Jump."
        return out

    def _draw_ship_ascii(self, ship: Ship, start_x, start_y, label, is_enemy=False, target_room=None):
        out = self.term.move_xy(start_x, start_y - 1) + self.term.bold(label + f" ({ship.name})")

        scale_x, scale_y = 6, 3

        for r in ship.rooms:
            for dy in range(r.h * scale_y):
                for dx in range(r.w * scale_x):
                    char = " "
                    # Unicode box drawing
                    if dy == 0 and dx == 0: char = "┌"
                    elif dy == 0 and dx == r.w * scale_x - 1: char = "┐"
                    elif dy == r.h * scale_y - 1 and dx == 0: char = "└"
                    elif dy == r.h * scale_y - 1 and dx == r.w * scale_x - 1: char = "┘"
                    elif dy == 0 or dy == r.h * scale_y - 1: char = "─"
                    elif dx == 0 or dx == r.w * scale_x - 1: char = "│"

                    char_to_draw = char
                    if is_enemy and r == target_room:
                        char_to_draw = self.term.bold_red(char)

                    if 1 <= dx < r.w * scale_x - 1 and 1 <= dy < r.h * scale_y - 1:
                        # System name (abbreviated)
                        if r.system and dy == 1 and 1 <= dx <= 4:
                            name = r.system.type.name[:4]
                            if dx - 1 < len(name):
                                sys_color = self.term.green if r.system.is_functional else self.term.red
                                char_to_draw = sys_color(name[dx-1])

                        # Crew
                        elif r.crew_members and dy == scale_y // 2 and dx == scale_x // 2:
                            char_to_draw = "☺"

                        # Fire
                        elif r.fire_level > 5 and (dx + dy) % 2 == 0:
                            char_to_draw = self.term.red("f")

                        # Oxygen level indicator
                        elif dy == scale_y - 2 and 1 <= dx <= 2:
                            if r.oxygen < 50:
                                char_to_draw = self.term.blue_on_black("o")

                    out += self.term.move_xy(start_x + r.x * scale_x + dx, start_y + r.y * scale_y + dy) + char_to_draw
        return out

    def _render_footer(self, state: GameState):
        ship = state.player_ship
        y = 22
        out = self.term.move_xy(0, y) + self.term.bold("SYSTEMS:")
        for i, (stype, sys) in enumerate(ship.systems.items()):
            extra = ""
            if stype == SystemType.SHIELDS:
                bubbles = getattr(sys, 'bubbles', 0)
                extra = f" (B: {bubbles})"
            sys_str = f"{stype.name:8}: [{self._progress_bar(sys.current_power, sys.max_power, sys.max_power)}] {sys.health}/{sys.max_power}{extra}"
            out += self.term.move_xy(2, y + 1 + i) + sys_str

        out += self.term.move_xy(80, y) + self.term.bold("WEAPONS:")
        for i, w in enumerate(ship.weapons):
            w_color = self.term.green if w.is_ready else self.term.normal
            w_str = f"{w.name:15}: [{self._progress_bar(w.cooldown_current, w.cooldown_max, 10, w_color)}] {'READY' if w.is_ready else ''}"
            out += self.term.move_xy(82, y + 1 + i) + w_str

        out += self.term.move_xy(120, y) + self.term.bold("CREW:")
        for i, c in enumerate(ship.crew):
            c_str = f"{c.name:10}: HP: {int(c.health)}/100 | S: P:{c.skills['pilot']:.1f} E:{c.skills['engines']:.1f} S:{c.skills['shields']:.1f} W:{c.skills['weapons']:.1f}"
            out += self.term.move_xy(122, y + 1 + i) + c_str

        out += self.term.move_xy(45, y) + self.term.bold("COMBAT LOG:")
        for i, entry in enumerate(state.log[-10:]):
            out += self.term.move_xy(45, y + 1 + i) + self.term.truncate(entry, 35)

        out += self.term.move_xy(0, y + 10) + self.term.bold("COMMANDS (PAUSED):")
        out += self.term.move_xy(2, y + 11) + "1/!: +/- Weapons | 2/\": +/- Shields | c: Cycle Crew | 4-9: Move Crew to Room | t: Target Enemy Room"
        out += self.term.move_xy(2, y + 12) + "u: Upgrade Reactor (20s) | h: Heal (10s) | j: Jump | SPACE: Pause/Unpause | q: Quit"

        out += self.term.move_xy(0, y + 14) + self.term.bold("ROOMS: ")
        for i, r in enumerate(ship.rooms):
            out += f"{i+4}: {r.id} | "

        return out
