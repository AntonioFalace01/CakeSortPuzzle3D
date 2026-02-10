import pygame
from assets import Assets

class PlateSprite:
    def __init__(self, plate, x, y, image_path="Sprites/plate.png", cell_size=(60,60)):
        self.plate = plate
        self.cell_size = cell_size
        # Crea una superficie vuota che conterrà il disegno del piatto
        self.surface = pygame.Surface(cell_size, pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=(x, y))
        self.start_pos = (x, y)
        self.dragging = False
        self.offset = (0, 0)
        self.placed = False

    def _render(self):
        """Disegna il piatto e le fette sulla surface interna dello sprite"""
        self.surface.fill((0,0,0,0)) # Pulisci trasparenza
        cx = self.cell_size[0] // 2
        cy = self.cell_size[1] // 2
        plate_size = min(self.cell_size)
        Assets.draw_plate(self.surface, self.plate, cx, cy, plate_size=plate_size)

    def start_drag(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos) and not self.placed:
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

    def draw(self, surface):
        """Questo è il metodo che mancava!"""
        self._render() # Aggiorna la grafica (fette, rotazioni)
        surface.blit(self.surface, self.rect)
