import pygame
import math
import random


class Table:
    def __init__(
        self,
        x,
        y,
        righe=5,
        colonne=4,
        larg_cella=60,
        alt_cella=60,
        padding=12,
        seme=42,
        mostra_griglia=False,
        stile_legno="quercia",
    ):
        self.x = x
        self.y = y
        self.righe = righe
        self.colonne = colonne
        self.larg_cella = larg_cella
        self.alt_cella = alt_cella
        self.padding = padding
        self.mostra_griglia = mostra_griglia
        self._rng = random.Random(seme)

        self.w = self.colonne * self.larg_cella + 2 * self.padding
        self.h = self.righe * self.alt_cella + 2 * self.padding

        if stile_legno == "quercia":
            self._base = (210, 180, 140)
            self._dark = (196, 156, 90)
            self._grain = (160, 120, 60)
            self._edge = (139, 105, 60)
        else:
            self._base = (210, 180, 140)
            self._dark = (184, 134, 11)
            self._grain = (160, 120, 80)
            self._edge = (139, 69, 19)

        self._grid_color = self._edge

        self.surface = pygame.Surface((self.w, self.h))
        self._ridisegna()

    def draw(self, screen):
        self._disegna_ombra(screen)
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
        s.fill(self._base)
        pygame.draw.rect(s, self._base, s.get_rect(), border_radius=16)
        self._gradiente_legno(s)
        self._assi_verticali(s)
        self._venature(s)
        self._disegna_incavi(s)
        if self.mostra_griglia:
            self._griglia(s)
        self._bordo(s)


    def _lerp(self, a, b, t):
        return int(a + (b - a) * t)

    def _gradiente_legno(self, s):
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            col = (
                self._lerp(self._base[0], self._dark[0], 0.4 * t),
                self._lerp(self._base[1], self._dark[1], 0.4 * t),
                self._lerp(self._base[2], self._dark[2], 0.4 * t),
            )
            pygame.draw.line(s, col, (0, y), (self.w, y))

    def _assi_verticali(self, s):
        for c in range(self.colonne):
            x0 = self.padding + c * self.larg_cella
            rect = pygame.Rect(x0, self.padding, self.larg_cella, self.righe * self.alt_cella)
            pygame.draw.rect(s, (196, 156, 90), rect)
            pygame.draw.line(s, (230, 210, 180), rect.topleft, rect.bottomleft)
            pygame.draw.line(s, (120, 90, 60), rect.topright, rect.bottomright)

    def _venature(self, s, num=22):
        for _ in range(num):
            y0 = self._rng.randint(self.padding + 8, self.h - self.padding - 8)
            amp = self._rng.uniform(2.0, 6.0)
            freq = self._rng.uniform(0.010, 0.028)
            phase = self._rng.uniform(0, 6.28)
            last = None
            for x in range(self.padding, self.w - self.padding):
                yy = int(y0 + math.sin(x * freq + phase) * amp)
                if last:
                    pygame.draw.line(s, self._grain, last, (x, yy))
                last = (x, yy)

    def _disegna_incavi(self, s):
        raggio = min(self.larg_cella, self.alt_cella) // 2 - 4
        for r in range(self.righe):
            for c in range(self.colonne):
                cx = self.padding + c * self.larg_cella + self.larg_cella // 2
                cy = self.padding + r * self.alt_cella + self.alt_cella // 2
                pygame.draw.circle(s, (160, 120, 60), (cx, cy), raggio)
                pygame.draw.circle(s, (120, 90, 60), (cx, cy), raggio, 3)

    def _griglia(self, s):
        for c in range(self.colonne + 1):
            x = self.padding + c * self.larg_cella
            pygame.draw.line(s, self._grid_color, (x, self.padding), (x, self.h - self.padding))
        for r in range(self.righe + 1):
            y = self.padding + r * self.alt_cella
            pygame.draw.line(s, self._grid_color, (self.padding, y), (self.w - self.padding, y))

    def _bordo(self, s):
        pygame.draw.rect(s, self._edge, s.get_rect(), width=8, border_radius=16)


    def _disegna_ombra(self, screen, offset=6):
        shadow_rect = pygame.Rect(self.x + offset, self.y + offset, self.w, self.h)
        pygame.draw.rect(screen, (60, 40, 25), shadow_rect, border_radius=18)
