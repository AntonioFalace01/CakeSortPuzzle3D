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

    def draw(self, surface):
        if not self.visible:
            return
        self._render()
        surface.blit(self.surface, self.rect)
