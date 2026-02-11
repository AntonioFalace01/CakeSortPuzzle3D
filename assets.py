import pygame
import math


class Assets:
    # Path base
    PATH_PLATE = "Sprites/plate.png"
    PATH_SLICES = {
        # Assicurati che questi percorsi siano corretti sul tuo PC
        "raspberry_choco": "Sprites/slices/cakeSlice1.png",
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
            try:
                cls._plate_src = pygame.image.load(cls.PATH_PLATE)
            except pygame.error:
                print(f"Errore caricamento piatto: {cls.PATH_PLATE}")
                cls._plate_src = pygame.Surface((100, 100))  # Fallback

        if not cls._slice_src:
            for key, path in cls.PATH_SLICES.items():
                try:
                    cls._slice_src[key] = pygame.image.load(path)
                except pygame.error:
                    print(f"Errore caricamento slice: {path}")
                    cls._slice_src[key] = pygame.Surface((50, 50))  # Fallback

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
            # --- CALIBRAZIONE DIMENSIONE ---
            # Per la tua fetta al lime, deve essere circa metà del piatto
            # Valore consigliato: 0.50 - 0.55
            target = int(plate_size * 0.52)

            src_img = cls._slice_src[slice_key]

            # Manteniamo l'aspect ratio originale per non deformarla
            aspect_ratio = src_img.get_width() / src_img.get_height()
            target_w = int(target * aspect_ratio)
            target_h = target

            scaled = pygame.transform.smoothscale(src_img, (target_w, target_h))
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

        # --- CORREZIONE DISTANZA (PUSH OUT) ---
        # Aumentiamo questo valore per "spingere" le fette dal centro verso il bordo.
        # Poiché ruotiamo le fette, il loro centro geometrico deve allontanarsi dal centro del piatto.
        # Prova 0.22. Se sono troppo esterne, scendi a 0.18. Se si sovrappongono troppo, sali a 0.25.
        distanza_dal_centro = plate_size * 0.22

        for piece in plate.pieces:
            slice_key = cls.TYPE_TO_SLICE.get(piece.tipo)
            if not slice_key:
                continue

            img = cls._get_slice_image(slice_key, plate_size)

            for _ in range(piece.count):
                # --- CORREZIONE ROTAZIONE (+180) ---
                # Aggiungiamo 180 gradi per far girare la punta verso l'interno (il centro del piatto)
                # Invece che verso l'esterno.
                rotated = pygame.transform.rotate(img, -current_angle + 180)

                # --- CALCOLO POSIZIONE ---
                radianti = math.radians(current_angle)

                # Calcolo offset: Spostiamo il centro dell'immagine lungo l'angolo
                offset_x = math.sin(radianti) * distanza_dal_centro
                offset_y = -math.cos(radianti) * distanza_dal_centro

                # Posizioniamo
                rect = rotated.get_rect(center=(center_x + offset_x, center_y + offset_y))

                surface.blit(rotated, rect)
                current_angle += angle_step

    @classmethod
    def draw_plate_only(cls, surface, x, y, size=60):
        plate_img = cls._get_plate_image(size)
        rect = plate_img.get_rect(center=(x, y))
        surface.blit(plate_img, rect)
