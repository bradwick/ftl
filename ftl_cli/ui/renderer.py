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
        # Use a buffer or just print directly with minimal flickering
        # For simplicity in this environment, we'll use term.home + content

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
        header = f" HULL: [{self._progress_bar(ship.hull, ship.max_hull, 20)}] | SCRAP: {ship.scrap} | PWR: {ship.reactor_used}/{ship.reactor_max} | DIFF: {state.difficulty}"
        return self.term.move_xy(0, 0) + self.term.blue(header)

    def _progress_bar(self, current, max_val, width):
        if max_val <= 0: return " " * width
        filled = int((max(0, current) / max_val) * width)
        return "#" * filled + "-" * (width - filled)

    def _render_ships(self, state: GameState):
        out = ""
        # Render Player Ship
        out += self._draw_ship_ascii(state.player_ship, 2, 3, "PLAYER")

        # Render Enemy Ship if exists
        if state.enemy_ship:
            out += self._draw_ship_ascii(state.enemy_ship, 80, 3, "ENEMY", is_enemy=True, target_room=state.selected_target_room)
        else:
            out += self.term.move_xy(80, 10) + "NO ENEMY DETECTED"
        return out

    def _draw_ship_ascii(self, ship: Ship, start_x, start_y, label, is_enemy=False, target_room=None):
        out = self.term.move_xy(start_x, start_y - 1) + self.term.bold(label + f" ({ship.name})")

        scale_x, scale_y = 4, 2

        for r in ship.rooms:
            for dy in range(r.h * scale_y):
                for dx in range(r.w * scale_x):
                    char = " "
                    if dy == 0 or dy == r.h * scale_y - 1: char = "-"
                    if dx == 0 or dx == r.w * scale_x - 1: char = "|"
                    if (dx == 0 or dx == r.w * scale_x - 1) and (dy == 0 or dy == r.h * scale_y - 1): char = "+"

                    char_to_draw = char
                    if is_enemy and r == target_room:
                        char_to_draw = self.term.bold_red(char)

                    if 1 <= dx < r.w * scale_x - 1 and 1 <= dy < r.h * scale_y - 1:
                        if dy == 1 and dx == 1:
                            char_to_draw = r.id[0]
                        elif r.system and dy == 1 and dx == 3:
                            char_to_draw = r.system.type.name[0]
                        elif r.crew_members and dy == (r.h * scale_y)//2 and dx == (r.w * scale_x)//2:
                            char_to_draw = "C"
                        elif r.fire_level > 0:
                            char_to_draw = "F"

                    out += self.term.move_xy(start_x + r.x * scale_x + dx, start_y + r.y * scale_y + dy) + char_to_draw
        return out

    def _render_footer(self, state: GameState):
        ship = state.player_ship
        y = 18
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
            w_str = f"{w.name:15}: [{self._progress_bar(w.cooldown_current, w.cooldown_max, 10)}] {'READY' if w.is_ready else ''}"
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
        out += self.term.move_xy(2, y + 12) + "u: Upgrade Reactor (20s) | h: Heal (10s) | SPACE: Pause/Unpause | q: Quit"

        out += self.term.move_xy(0, y + 14) + self.term.bold("ROOMS: ")
        for i, r in enumerate(ship.rooms):
            out += f"{i+4}: {r.id} | "

        return out
