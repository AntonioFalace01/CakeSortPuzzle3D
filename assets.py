import pygame
import math  # <--- Importante per i calcoli di posizionamento


class Assets:
    # Path base
    PATH_PLATE = "Sprites/plate.png"
    PATH_SLICES = {
        "raspberry_choco": "Sprites/slices/cake-slice3.png",
        "sprinkles_cherry": "Sprites/slices/cake-slice4.png",
        "lattice_berry": "Sprites/slices/cake-slice5.png",
        "lemon_swirl": "Sprites/slices/cake-slice6.png",
    }

    TYPE_TO_SLICE = {
        "C": "raspberry_choco",
        "S": "sprinkles_cherry",
        "V": "lattice_berry",
        "L": "lemon_swirl",
    }

    _plate_src = None
    _slice_src = {}
    _plate_cache = {}
    _slice_cache = {}

    @classmethod
    def init(cls):
        if cls._plate_src is None:
            cls._plate_src = pygame.image.load(cls.PATH_PLATE)
        if not cls._slice_src:
            for key, path in cls.PATH_SLICES.items():
                cls._slice_src[key] = pygame.image.load(path)

    @classmethod
    def _get_plate_image(cls, plate_size):
        if cls._plate_src is None:
            cls.init()
        img = cls._plate_cache.get(plate_size)
        if img is None:
            scaled = pygame.transform.smoothscale(cls._plate_src, (plate_size, plate_size))
            img = scaled.convert_alpha() if pygame.display.get_surface() else scaled
            cls._plate_cache[plate_size] = img
        return img

    @classmethod
    def _get_slice_image(cls, slice_key, plate_size):
        if not cls._slice_src:
            cls.init()
        key = (slice_key, plate_size)
        img = cls._slice_cache.get(key)
        if img is None:
            # --- MODIFICA DIMENSIONE ---
            # Riduciamo la fetta a circa il 60% del piatto (era 0.85)
            # Questo, combinato con lo spostamento (offset), evita sovrapposizioni brutte
            target = int(plate_size * 0.60)
            scaled = pygame.transform.smoothscale(cls._slice_src[slice_key], (target, target))
            img = scaled.convert_alpha() if pygame.display.get_surface() else scaled
            cls._slice_cache[key] = img
        return img

    @classmethod
    def draw_plate(cls, surface, plate, center_x, center_y, plate_size=60):
        # 1. Disegna Piatto
        plate_img = cls._get_plate_image(plate_size)
        plate_rect = plate_img.get_rect(center=(center_x, center_y))
        surface.blit(plate_img, plate_rect)

        if not plate or not plate.pieces:
            return

        # 2. Configurazione Disegno Fette
        MAX_SLICES = 6
        angle_step = 360 / MAX_SLICES
        current_angle = 0

        # --- PARAMETRO DISTANZA ---
        # Questo sposta le fette dal centro verso l'esterno.
        # Se le fette sono ancora sovrapposte, aumenta (es. 0.28).
        # Se c'è un buco troppo grande al centro, diminuisci (es. 0.20).
        distanza_dal_centro = plate_size * 0.15

        for piece in plate.pieces:
            slice_key = cls.TYPE_TO_SLICE.get(piece.tipo)
            if not slice_key:
                continue

            img = cls._get_slice_image(slice_key, plate_size)

            for _ in range(piece.count):
                # Ruota l'immagine
                rotated = pygame.transform.rotate(img, -current_angle+180)

                # --- CALCOLO POSIZIONE CORRETTA (Trigonometria) ---
                # Convertiamo l'angolo in radianti per seno e coseno
                radianti = math.radians(current_angle)

                # Calcoliamo lo spostamento (offset) dal centro del piatto
                # Nota: le coordinate schermo Y sono invertite, e dipende dall'orientamento originale della sprite.
                # Questa formula assume che la sprite punti verso l'alto (o sia standard).
                # Se le fette vanno nella direzione sbagliata, prova a invertire i segni o scambiare sin/cos.
                offset_x = math.sin(radianti) * distanza_dal_centro
                offset_y = -math.cos(radianti) * distanza_dal_centro

                # Posizioniamo il centro della fetta spostato rispetto al centro del piatto
                rect = rotated.get_rect(center=(center_x + offset_x, center_y + offset_y))

                surface.blit(rotated, rect)
                current_angle += angle_step

    @classmethod
    def draw_plate_only(cls, surface, x, y, size=60):
        plate_img = cls._get_plate_image(size)
        rect = plate_img.get_rect(center=(x, y))
        surface.blit(plate_img, rect)
