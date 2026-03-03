import pygame
from assets import Assets
from sound_manager import SFX


class PlateSprite:
    def __init__(self, plate, x, y, image_path="Sprites/plate.png", cell_size=(60, 60)):
        self.plate = plate
        self.cell_size = cell_size

        self.surface = pygame.Surface(cell_size, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=(x, y))
        self.start_pos = (x, y)

        self.dragging = False
        self.offset = (0, 0)
        self.placed = False

        # sync con griglia
        self.placed_cell = None
        self.visible = True

        # --- NEW: info blocco/opzione ---
        self.opt_index = None     # indice opzione in current_options
        self.plate_index = 0      # 0 o 1 dentro al blocco
        # --- SPAWN ANIMATION ---
        self.spawning = True
        self.spawn_time = 0.0
        self.spawn_duration = 0.35
        self.spawn_offset_y = 35

    def _render(self):
        self.surface.fill((0, 0, 0, 0))
        cx = self.cell_size[0] // 2
        cy = self.cell_size[1] // 2
        plate_size = min(self.cell_size)
        Assets.draw_plate(self.surface, self.plate, cx, cy, plate_size=plate_size)

    def start_drag(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos) and not self.placed:
            SFX.pickup.play()
            self.dragging = True
            mx, my = mouse_pos
            rx, ry = self.rect.topleft
            self.offset = (rx - mx, ry - my)

    def update_drag(self, mouse_pos):
        if self.dragging:
            mx, my = mouse_pos
            self.rect.topleft = (mx + self.offset[0], my + self.offset[1])

    def stop_drag(self):
        self.dragging = False

    def snap_to_cell_topleft(self, cell_topleft):
        self.rect.topleft = cell_topleft
        self.placed = True

    def reset_to_start(self):
        self.rect.topleft = self.start_pos
        self.placed = False
        self.placed_cell = None
        self.visible = True

    def draw(self, surface, dt):
        if not self.visible:
            return

        self._render()

        rect = self.rect.copy()
        scale = 1.0
        alpha = 255

        if self.spawning:
            self.spawn_time += dt
            progress = min(1.0, self.spawn_time / self.spawn_duration)

            # easing
            ease = 1 - (1 - progress) ** 3

            # SLIDE
            y_offset = self.spawn_offset_y * (1 - ease)
            rect.y += y_offset

            # SCALE POP
            if progress < 0.8:
                scale = 0.8 + 0.25 * ease
            else:
                scale = 1.05 - (progress - 0.8) * 0.25

            # FADE
            alpha = int(255 * ease)

            if progress >= 1.0:
                self.spawning = False

        # Applica scala
        if scale != 1.0:
            w, h = self.surface.get_size()
            scaled = pygame.transform.smoothscale(
                self.surface,
                (int(w * scale), int(h * scale))
            )
            scaled.set_alpha(alpha)
            new_rect = scaled.get_rect(center=rect.center)
            surface.blit(scaled, new_rect)
        else:
            self.surface.set_alpha(alpha)
            surface.blit(self.surface, rect)
