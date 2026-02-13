import pygame
import math


class Assets:
    # ------------------ PATH ------------------

    PATH_PLATE = "Sprites/plate.png"

    PATH_SLICES = {
        "raspberry_choco": "Sprites/slices/cakeSlice2.png",
        "sprinkles_cherry": "Sprites/slices/cakeSlice8.png",
        "lattice_berry": "Sprites/slices/cakeSlice7.png",
        "lemon_swirl": "Sprites/slices/cakeSlice1.png",
    }

    TYPE_TO_SLICE = {
        "C": "raspberry_choco",
        "S": "sprinkles_cherry",
        "V": "lattice_berry",
        "L": "lemon_swirl",
    }

    # ------------------ CACHE ------------------

    _plate_src = None
    _slice_src = {}
    _plate_cache = {}
    _slice_cache = {}

    # ------------------ INIT ------------------

    @classmethod
    def init(cls):
        if cls._plate_src is None:
            cls._plate_src = pygame.image.load(cls.PATH_PLATE).convert_alpha()

        if not cls._slice_src:
            for key, path in cls.PATH_SLICES.items():
                cls._slice_src[key] = pygame.image.load(path).convert_alpha()

    # ------------------ PLATE IMAGE ------------------

    @classmethod
    def _get_plate_image(cls, plate_size):
        if cls._plate_src is None:
            cls.init()

        img = cls._plate_cache.get(plate_size)

        if img is None:
            img = pygame.transform.smoothscale(cls._plate_src, (plate_size, plate_size))
            cls._plate_cache[plate_size] = img

        return img

    # ------------------ SLICE IMAGE ------------------

    @classmethod
    def _get_slice_image(cls, slice_key, plate_size):
        if not cls._slice_src:
            cls.init()

        key = (slice_key, plate_size)
        img = cls._slice_cache.get(key)

        if img is None:
            # fetta = 60% del piatto
            target = int(plate_size * 0.64)
            img = pygame.transform.smoothscale(cls._slice_src[slice_key], (target, target))
            cls._slice_cache[key] = img

        return img

    # ------------------ DRAW PLATE CON FETTE ------------------

    @classmethod
    def draw_plate(cls, surface, plate, center_x, center_y, plate_size=60):

        # 1️⃣ Disegna il piatto
        plate_img = cls._get_plate_image(plate_size)
        plate_rect = plate_img.get_rect(center=(center_x, center_y))
        surface.blit(plate_img, plate_rect)

        if not plate:
            return

        MAX_SLICES = 6
        angle_step = 360 / MAX_SLICES
        current_angle = 0

        for piece in plate.pieces:

            slice_key = cls.TYPE_TO_SLICE.get(piece.tipo)
            if not slice_key:
                continue

            img = cls._get_slice_image(slice_key, plate_size)

            for _ in range(piece.count):

                # 🔁 Ruota fetta
                rotated = pygame.transform.rotate(img, -current_angle + 180)

                # 🎯 CALCOLO DISTANZA DINAMICA
                # raggio = metà altezza fetta (leggermente ridotto per combaciare meglio)
                r = plate_size * 0.24


                radianti = math.radians(current_angle)

                offset_x = math.sin(radianti) * r
                offset_y = -math.cos(radianti) * r

                rect = rotated.get_rect(
                    center=(center_x + offset_x, center_y + offset_y)
                )

                surface.blit(rotated, rect)

                current_angle += angle_step

    # ------------------ SOLO PIATTO ------------------

    @classmethod
    def draw_plate_only(cls, surface, x, y, size=60):
        plate_img = cls._get_plate_image(size)
        rect = plate_img.get_rect(center=(x, y))
        surface.blit(plate_img, rect)
