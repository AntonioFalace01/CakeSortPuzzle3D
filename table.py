import pygame
import math
import random


class Table:
    def __init__(
            self,
            x,
            y,
            righe=6,
            colonne=8,
            larg_cella=60,
            alt_cella=60,
            padding=12,
            seme=42,
            mostra_griglia=False,
            mostra_gambe=True,
            stile_legno="caldo",  # Ho impostato un nuovo stile "caldo" di default
    ):
        self.x = x
        self.y = y
        self.righe = righe
        self.colonne = colonne
        self.larg_cella = larg_cella
        self.alt_cella = alt_cella
        self.padding = padding
        self.mostra_griglia = mostra_griglia
        self.mostra_gambe = mostra_gambe
        self._rng = random.Random(seme)

        self.w = self.colonne * self.larg_cella + 2 * self.padding
        self.h = self.righe * self.alt_cella + 2 * self.padding

        # ================================================================= #
        # ===== COLORI DEL LEGNO MODIFICATI PER UN ASPETTO PIÙ CALDO  ===== #
        # ================================================================= #
        # I colori sono in formato (R, G, B).

        if stile_legno == "scuro":
            # Un legno scuro, tipo noce
            self._base = (139, 69, 19)  # Marrone "SaddleBrown"
            self._dark = (101, 67, 33)  # Marrone più scuro
            self._grain = (80, 50, 20, 45)  # Venature scure e semi-trasparenti
            self._edge = (61, 43, 31)  # Bordo molto scuro
        else:  # Stile "caldo" (default)
            # Un legno chiaro e caldo, tipo rovere o pino
            self._base = (210, 180, 140)  # Marrone chiaro "Tan"
            self._dark = (184, 134, 11)  # Tonalità più scura "DarkGoldenrod"
            self._grain = (139, 90, 43, 35)  # Venature marroni semi-trasparenti
            self._edge = (139, 69, 19)  # Bordo marrone più definito

        self._grid_color = (self._edge[0], self._edge[1], self._edge[2], 80)

        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self._ridisegna()

    def draw(self, screen):
        self._disegna_ombra(screen)
        if self.mostra_gambe:
            self._disegna_gambe(screen)
        screen.blit(self.surface, (self.x, self.y))

    def get_cell_at(self, pos):
        mx, my = pos
        px = mx - (self.x + self.padding)
        py = my - (self.y + self.padding)
        if not (0 <= px < self.colonne * self.larg_cella and 0 <= py < self.righe * self.alt_cella):
            return None
        return int(py // self.alt_cella), int(px // self.larg_cella)

    def _ridisegna(self):
        s = self.surface
        s.fill((0, 0, 0, 0))
        pygame.draw.rect(s, self._base, s.get_rect(), border_radius=16)
        self._gradiente_legno(s)
        self._assi_verticali(s)
        self._venature(s)
        self._disegna_incavi(s)
        if self.mostra_griglia:
            self._griglia(s)
        self._bordo(s)
        self._highlight_superiore(s)

    # ===================================================================== #
    # ===== COLORI DELLE RIENTRANZE (INCavi) LEGGERMENTE MODIFICATI ===== #
    # ===================================================================== #
    def _disegna_incavi(self, s):
        raggio = min(self.larg_cella, self.alt_cella) // 2 - 4
        for r in range(self.righe):
            for c in range(self.colonne):
                cx = self.padding + c * self.larg_cella + self.larg_cella // 2
                cy = self.padding + r * self.alt_cella + self.alt_cella // 2

                rect_arc = pygame.Rect(cx - raggio, cy - raggio, raggio * 2, raggio * 2)

                # 1. Ombra generale sul fondo dell'incavo
                colore_fondo_incavo = (0, 0, 0, 50)  # Leggermente più scura
                pygame.draw.circle(s, colore_fondo_incavo, (cx, cy), raggio)

                # 2. Ombra del bordo interno (più marcata)
                colore_ombra_interna = (0, 0, 0, 90)
                pygame.draw.arc(s, colore_ombra_interna, rect_arc, math.radians(80), math.radians(200), 3)

                # 3. Luce riflessa sul bordo opposto (più sottile)
                colore_luce_interna = (255, 255, 255, 50)
                pygame.draw.arc(s, colore_luce_interna, rect_arc, math.radians(280), math.radians(350), 2)

    # --- Funzioni di disegno (invariate) ---

    def _lerp(self, a, b, t):
        return int(a + (b - a) * t)

    def _gradiente_legno(self, s):
        temp_surface = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            col = (
                self._lerp(self._base[0], self._dark[0], 0.3 * t),
                self._lerp(self._base[1], self._dark[1], 0.3 * t),
                self._lerp(self._base[2], self._dark[2], 0.3 * t),
                255,
            )
            pygame.draw.line(temp_surface, col, (0, y), (self.w, y))
        mask = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=16)
        temp_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        s.blit(temp_surface, (0, 0))

    def _assi_verticali(self, s):
        for c in range(self.colonne):
            x0 = self.padding + c * self.larg_cella
            rect = pygame.Rect(x0, self.padding, self.larg_cella, self.righe * self.alt_cella)
            pygame.draw.rect(s, (0, 0, 0, 10), rect)
            pygame.draw.line(s, (255, 255, 255, 15), (rect.left, rect.top), (rect.left, rect.bottom))
            pygame.draw.line(s, (0, 0, 0, 25), (rect.right, rect.top), (rect.right, rect.bottom))

    def _venature(self, s, num=22):
        for _ in range(num):
            y0 = self._rng.randint(self.padding + 8, self.h - self.padding - 8)
            amp = self._rng.uniform(2.0, 6.0)
            freq = self._rng.uniform(0.010, 0.028)
            phase = self._rng.uniform(0, 6.28)
            last = None
            for x in range(self.padding, self.w - self.padding):
                yy = y0 + math.sin(x * freq + phase) * amp
                if last:
                    pygame.draw.aaline(s, self._grain, last, (x, yy))
                last = (x, yy)

    def _griglia(self, s):
        for c in range(self.colonne + 1):
            x = self.padding + c * self.larg_cella
            pygame.draw.line(s, self._grid_color, (x, self.padding), (x, self.h - self.padding), 1)
        for r in range(self.righe + 1):
            y = self.padding + r * self.alt_cella
            pygame.draw.line(s, self._grid_color, (self.padding, y), (self.w - self.padding, y), 1)

    def _bordo(self, s):
        pygame.draw.rect(s, self._edge, s.get_rect(), width=8, border_radius=16)

    def _highlight_superiore(self, s):
        shine = pygame.Surface((self.w - 12, 22), pygame.SRCALPHA)
        for i in range(22):
            alpha = max(0, 90 - i * 4)
            pygame.draw.rect(shine, (255, 255, 255, alpha), (0, i, self.w - 12, 1))
        s.blit(shine, (6, 6))

    def _disegna_ombra(self, screen, offset=6, intensita=14, passaggi=10, raggio=18):
        shadow = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        base_rect = shadow.get_rect()
        for i in range(passaggi, 0, -1):
            a = int(intensita * i)
            pygame.draw.rect(shadow, (0, 0, 0, a), base_rect.inflate(i * 2, i * 2), border_radius=raggio)
        screen.blit(shadow, (self.x + offset, self.y + offset))

    def _disegna_gambe(self, screen):
        gambe_col = (self._edge[0] - 10, self._edge[1] - 10, self._edge[2] - 10)
        spessore, altezza, raggio = 16, 60, 6
        tx, ty, tw, th = self.x, self.y, self.w, self.h
        pos_gambe = [
            (tx + 20, ty + th - 10), (tx + tw - 20 - spessore, ty + th - 10),
            (tx + tw // 2 - 50, ty + th - 10), (tx + tw // 2 + 50 - spessore, ty + th - 10)
        ]
        for (gx, gy) in pos_gambe:
            g_rect = pygame.Rect(gx, gy, spessore, altezza)
            ombra = pygame.Surface((spessore + 8, altezza + 8), pygame.SRCALPHA)
            for i in range(6, 0, -1):
                pygame.draw.rect(ombra, (0, 0, 0, 20 * i), ombra.get_rect().inflate(i, i), border_radius=raggio)
            screen.blit(ombra, (gx + 2, gy + 2))
            pygame.draw.rect(screen, gambe_col, g_rect, border_radius=raggio)
            pygame.draw.rect(screen, (255, 255, 255, 30), (gx + 2, gy, 4, altezza), border_radius=raggio)
