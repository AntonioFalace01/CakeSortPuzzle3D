import pygame
import math


class UnlockManager:
    def __init__(self):
        self.all_types_ordered=["C", "S", "V", "L","A","B", "D", "E", "F", "G"]
        self.active_types = set(self.all_types_ordered[:3])
        self.unlocked_count = len(self.active_types)
        # soglie di sblocco per ognuna delle 7 nuove torte
        self.unlock_thresholds = [100, 250, 450, 700, 1000, 1350, 1750]

        self.total_score = 0  # cumulativo globale per sblocchi
        self.next_unlock_index = 0  # indice nella lista unlock_thresholds

    def get_next_threshold(self):
        if self.next_unlock_index < len(self.unlock_thresholds):
            return self.unlock_thresholds[self.next_unlock_index]
        return None

    def add_score(self, amount):
        #Aggiorna punteggio cumulativo e ritorna True se si sblocca una nuova torta
        if amount <= 0:
            return False
        self.total_score += amount
        threshold = self.get_next_threshold()
        if threshold is not None and self.total_score >= threshold:
            # sblocca una nuova torta
            next_type = self.all_types_ordered[self.unlocked_count]  # prendi il prossimo tipo
            self.active_types.add(next_type)
            self.unlocked_count += 1
            self.next_unlock_index += 1
            return True
        return False

    def is_type_active(self, t):
        return t in self.active_types

    def get_active_types_list(self):
        return list(self.active_types)


class Assets:

    PATH_PLATE = "Sprites/plate.png"

    PATH_SLICES = {"raspberry_choco": "Sprites/slices/cakeSlice2.png",
                   "sprinkles_cherry": "Sprites/slices/cakeSlice8.png",
                    "lattice_berry": "Sprites/slices/cakeSlice7.png",
                   "lemon_swirl": "Sprites/slices/cakeSlice1.png",
                    "almond_crunch": "Sprites/slices/cakeSlice3.png",
                    "blueberry_glaze": "Sprites/slices/cakeSlice4.png",
                    "dark_forest": "Sprites/slices/cakeSlice5.png",
                    "emerald_mint": "Sprites/slices/cakeSlice6.png",
                   "frost_vanilla": "Sprites/slices/cakeSlice9.png",
                   "golden_honey": "Sprites/slices/cakeSlice10.png"}

    TYPE_TO_SLICE = {"C": "raspberry_choco", "S": "sprinkles_cherry", "V": "lattice_berry", "L": "lemon_swirl",
                     "A": "almond_crunch", "B": "blueberry_glaze", "D": "dark_forest", "E": "emerald_mint",
                     "F": "frost_vanilla", "G": "golden_honey", }


    _plate_src = None
    _slice_src = {}
    _plate_cache = {}
    _slice_cache = {}


    @classmethod
    def init(cls):
        if cls._plate_src is None:
            cls._plate_src = pygame.image.load(cls.PATH_PLATE).convert_alpha()

        if not cls._slice_src:
            for key, path in cls.PATH_SLICES.items():
                cls._slice_src[key] = pygame.image.load(path).convert_alpha()


    @classmethod
    def _get_plate_image(cls, plate_size):
        if cls._plate_src is None:
            cls.init()

        img = cls._plate_cache.get(plate_size)

        if img is None:
            img = pygame.transform.smoothscale(cls._plate_src, (plate_size, plate_size))
            cls._plate_cache[plate_size] = img

        return img

    @classmethod
    def _get_slice_image(cls, slice_key, plate_size):
        if not cls._slice_src:
            cls.init()

        key = (slice_key, plate_size)
        img = cls._slice_cache.get(key)

        if img is None:
            target = int(plate_size * 0.64)
            img = pygame.transform.smoothscale(cls._slice_src[slice_key], (target, target))
            cls._slice_cache[key] = img

        return img


    @classmethod
    def draw_plate(cls, surface, plate, center_x, center_y, plate_size=60):

        plate_img = cls._get_plate_image(plate_size)
        plate_rect = plate_img.get_rect(center=(center_x, center_y))
        surface.blit(plate_img, plate_rect)

        if not plate:
            return

        MAX_SLICES = 6
        angle_step = 360 / MAX_SLICES
        current_angle = 0
        drawn = 0

        for piece in plate.pieces:

            slice_key = cls.TYPE_TO_SLICE.get(piece.tipo)
            if not slice_key:
                continue

            img = cls._get_slice_image(slice_key, plate_size)

            for _ in range(piece.count):

                if drawn >= MAX_SLICES:
                    break

                rotated = pygame.transform.rotate(img, -current_angle + 180)

                r = plate_size * 0.24
                radianti = math.radians(current_angle)
                offset_x = math.sin(radianti) * r
                offset_y = -math.cos(radianti) * r

                rect = rotated.get_rect(
                    center=(center_x + offset_x, center_y + offset_y)
                )

                surface.blit(rotated, rect)

                current_angle += angle_step
                drawn += 1

            if drawn >= MAX_SLICES:
                break

    @classmethod
    def draw_plate_only(cls, surface, x, y, size=60):
        plate_img = cls._get_plate_image(size)
        rect = plate_img.get_rect(center=(x, y))
        surface.blit(plate_img, rect)
