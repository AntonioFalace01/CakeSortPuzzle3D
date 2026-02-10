import pygame

PLATE_IMAGE = pygame.image.load("Sprites/plate.png").convert_alpha()

def draw_plate(surface, plate, center_x, center_y):
    """
    Disegna un piatto con le sue fette in vista top-down.
    """
    # 1️⃣ Disegna il piatto
    plate_rect = PLATE_IMAGE.get_rect(center=(center_x, center_y))
    surface.blit(PLATE_IMAGE, plate_rect)

    if not plate or not plate.pieces:
        return

    # 2️⃣ Disegno fette
    MAX_SLICES = 6
    angle_step = 360 / MAX_SLICES
    current_angle = 0

    for piece in plate.pieces:
        img = SLICE_IMAGES.get(TYPE_TO_SLICE.get(piece.tipo))

        if not img:
            continue

        for _ in range(piece.count):
            rotated = pygame.transform.rotate(img, -current_angle)

            rect = rotated.get_rect(center=(center_x, center_y))
            surface.blit(rotated, rect)

            current_angle += angle_step

def draw_plate_only(surface, x, y, size=60):
    """Disegna il piatto centrato in (x, y) e ridimensionato"""
    plate_scaled = pygame.transform.scale(PLATE_IMAGE, (size, size))
    rect = plate_scaled.get_rect(center=(x, y))
    surface.blit(plate_scaled, rect)

