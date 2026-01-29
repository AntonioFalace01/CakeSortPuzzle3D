import pygame

class PlateSprite:
    def __init__(self, plate, x, y, image_path="piatto.png", cell_size=(60,60)):
        self.plate = plate
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, cell_size)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_pos = (x, y)
        self.dragging = False
        self.offset = (0, 0)
        self.placed = False

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
        surface.blit(self.image, self.rect)

