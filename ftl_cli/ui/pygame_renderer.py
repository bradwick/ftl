import pygame
from ftl_cli.models.base import Ship, Room, SystemType, Crew
from ftl_cli.engine import GameState

# Constants
WIDTH, HEIGHT = 1200, 800
FPS = 60
ROOM_SCALE = 40

# Colors
COLOR_BG = (10, 10, 20)
COLOR_SHIP_BG = (30, 30, 40)
COLOR_ROOM_BORDER = (100, 100, 120)
COLOR_SYSTEM_OK = (0, 200, 0)
COLOR_SYSTEM_DAMAGED = (200, 0, 0)
COLOR_HULL = (0, 255, 0)
COLOR_SCRAP = (255, 215, 0)
COLOR_POWER = (0, 255, 255)
COLOR_TEXT = (220, 220, 220)
COLOR_FIRE = (255, 69, 0)
COLOR_OXYGEN_LOW = (0, 100, 255, 100)

class PygameRenderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("FTL-CLI: GUI Edition")
        self.font = pygame.font.SysFont("monospace", 16)
        self.bold_font = pygame.font.SysFont("monospace", 18, bold=True)

    def render(self, state: GameState):
        self.screen.fill(COLOR_BG)

        self._draw_header(state)
        self._draw_ship(state.player_ship, 50, 100, "PLAYER")
        if state.enemy_ship:
            target = state.selected_target_room
            self._draw_ship(state.enemy_ship, 700, 100, "ENEMY", is_enemy=True, target_room=target)
        elif state.is_jumping:
            self._draw_text("FTL JUMP IN PROGRESS...", 700, 200, COLOR_POWER)
        else:
            self._draw_text("NO ENEMY DETECTED. Press 'j' to Jump.", 700, 200, COLOR_TEXT)

        self._draw_footer(state)

        if state.is_paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
            self._draw_text("PAUSED", WIDTH // 2 - 50, HEIGHT // 2, (255, 255, 255), True)

        if state.game_over:
            self._draw_text("GAME OVER", WIDTH // 2 - 80, HEIGHT // 2 + 40, (255, 50, 50), True)

        pygame.display.flip()

    def _draw_text(self, text, x, y, color=COLOR_TEXT, bold=False):
        f = self.bold_font if bold else self.font
        img = f.render(text, True, color)
        self.screen.blit(img, (x, y))

    def _draw_header(self, state: GameState):
        ship = state.player_ship
        # Hull
        pygame.draw.rect(self.screen, (50, 50, 50), (20, 20, 200, 20))
        hull_w = int((ship.hull / ship.max_hull) * 200)
        pygame.draw.rect(self.screen, COLOR_HULL, (20, 20, hull_w, 20))
        self._draw_text(f"HULL: {ship.hull}/{ship.max_hull}", 20, 45)

        # Resources
        self._draw_text(f"SCRAP: {ship.scrap}", 250, 20, COLOR_SCRAP)
        self._draw_text(f"POWER: {ship.reactor_used}/{ship.reactor_max}", 400, 20, COLOR_POWER)
        self._draw_text(f"SECTOR: {state.sector} | BEACON: {state.current_beacon+1}/{state.beacons_in_sector}", 600, 20)

    def _draw_ship(self, ship: Ship, start_x, start_y, label, is_enemy=False, target_room=None):
        self._draw_text(f"{label}: {ship.name}", start_x, start_y - 30, bold=True)

        for r in ship.rooms:
            rect = (start_x + r.x * ROOM_SCALE, start_y + r.y * ROOM_SCALE, r.w * ROOM_SCALE, r.h * ROOM_SCALE)

            # Room BG
            pygame.draw.rect(self.screen, COLOR_SHIP_BG, rect)

            # Highlights
            border_color = COLOR_ROOM_BORDER
            if is_enemy and r == target_room:
                border_color = (255, 0, 0)
                pygame.draw.rect(self.screen, (50, 0, 0), rect)

            pygame.draw.rect(self.screen, border_color, rect, 2)

            # System
            if r.system:
                sys_color = COLOR_SYSTEM_OK if r.system.is_functional else COLOR_SYSTEM_DAMAGED
                self._draw_text(r.system.type.name[:4], rect[0] + 5, rect[1] + 5, sys_color)
                # System Power/HP
                hp_w = int((r.system.health / r.system.max_power) * (rect[2] - 10))
                pygame.draw.rect(self.screen, (50, 50, 50), (rect[0] + 5, rect[1] + 25, rect[2] - 10, 5))
                pygame.draw.rect(self.screen, sys_color, (rect[0] + 5, rect[1] + 25, hp_w, 5))

            # Fire
            if r.fire_level > 5:
                pygame.draw.circle(self.screen, COLOR_FIRE, (rect[0] + rect[2] - 15, rect[1] + 15), 10)

            # Oxygen
            if r.oxygen < 50:
                oxy_surface = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
                alpha = int((1.0 - r.oxygen / 100.0) * 150)
                oxy_surface.fill((0, 100, 255, alpha))
                self.screen.blit(oxy_surface, (rect[0], rect[1]))

            # Crew
            for i, c in enumerate(r.crew_members):
                # Simple circle for crew
                pygame.draw.circle(self.screen, (255, 255, 255), (rect[0] + rect[2]//2, rect[1] + rect[3]//2), 8)
                self._draw_text(c.name[0], rect[0] + rect[2]//2 - 4, rect[1] + rect[3]//2 - 8, (0, 0, 0))

    def _draw_footer(self, state: GameState):
        ship = state.player_ship
        y = 550

        # Combat Log
        self._draw_text("COMBAT LOG:", 50, y, bold=True)
        for i, entry in enumerate(state.log[-8:]):
            self._draw_text(entry, 60, y + 25 + i * 20)

        # Weapons
        self._draw_text("WEAPONS:", 500, y, bold=True)
        for i, w in enumerate(ship.weapons):
            w_color = COLOR_SYSTEM_OK if w.is_ready else COLOR_TEXT
            self._draw_text(f"{w.name}", 510, y + 25 + i * 30, w_color)
            pygame.draw.rect(self.screen, (50, 50, 50), (650, y + 25 + i * 30, 100, 15))
            charge_w = int((w.cooldown_current / w.cooldown_max) * 100)
            pygame.draw.rect(self.screen, w_color, (650, y + 25 + i * 30, charge_w, 15))

        # Crew
        self._draw_text("CREW:", 800, y, bold=True)
        for i, c in enumerate(ship.crew):
            skill_str = f"P:{c.skills['pilot']:.1f} E:{c.skills['engines']:.1f} S:{c.skills['shields']:.1f} W:{c.skills['weapons']:.1f}"
            self._draw_text(f"{c.name}: HP {int(c.health)} | {skill_str}", 810, y + 25 + i * 20)

        # Commands
        self._draw_text("COMMANDS: SPACE:Pause | 1/!:Weapons | 2/\":Shields | c:Crew | 4-9:Move | t:Target | j:Jump | q:Quit", 20, HEIGHT - 30, (150, 150, 150))
