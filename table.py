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
        mostra_griglia=True,
        mostra_gambe=True,
        stile_legno="chiaro",
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

        # Dimensioni del piano tavolo (surface)
        self.w = self.colonne * self.larg_cella + 2 * self.padding
        self.h = self.righe * self.alt_cella + 2 * self.padding

        # Palette stile legno
        if stile_legno == "scuro":
            self._base = (155, 115, 75)
            self._dark = (110, 75, 45)
            self._grain = (85, 60, 40, 40)
            self._edge = (70, 45, 30)
        else:
            # chiaro (default)
            self._base = (196, 158, 108)
            self._dark = (150, 110, 70)
            self._grain = (110, 80, 50, 34)
            self._edge = (90, 60, 40)

        self._grid_color = (self._edge[0], self._edge[1], self._edge[2], 120)

        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self._ridisegna()

    # ----------------- API pubblica -----------------
    def draw(self, screen):
        # Ombra soft
        self._disegna_ombra(screen, offset=6, intensita=14, passaggi=10, raggio=18)

        # Gambe (sotto al piano)
        if self.mostra_gambe:
            self._disegna_gambe(screen)

        # Piano del tavolo
        screen.blit(self.surface, (self.x, self.y))

    def get_cell_at(self, pos):
        """
        Restituisce (riga, colonna) se pos (x,y) è sopra una cella della griglia,
        altrimenti None.
        """
        mx, my = pos
        px = mx - (self.x + self.padding)
        py = my - (self.y + self.padding)

        if px < 0 or py < 0:
            return None
        if px >= self.colonne * self.larg_cella or py >= self.righe * self.alt_cella:
            return None

        c = int(px // self.larg_cella)
        r = int(py // self.alt_cella)
        return (r, c)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    # ----------------- Disegno interno -----------------
    def _ridisegna(self):
        s = self.surface
        s.fill((0, 0, 0, 0))

        self._gradiente_legno(s)
        self._assi_verticali(s)
        self._venature(s, num=22)
        if self.mostra_griglia:
            self._griglia(s)
        self._bordo(s)
        self._highlight_superiore(s)

    def _lerp(self, a, b, t):
        return int(a + (b - a) * t)

    def _gradiente_legno(self, s):
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            col = (
                self._lerp(self._base[0], self._dark[0], 0.25 * t),
                self._lerp(self._base[1], self._dark[1], 0.25 * t),
                self._lerp(self._base[2], self._dark[2], 0.25 * t),
                255,
            )
            pygame.draw.line(s, col, (0, y), (self.w, y))

    def _assi_verticali(self, s):
        for c in range(self.colonne):
            x0 = self.padding + c * self.larg_cella
            rect = pygame.Rect(x0, self.padding, self.larg_cella, self.righe * self.alt_cella)
            # leggerissima ombra per differenziare le "assi"
            pygame.draw.rect(s, (0, 0, 0, 14), rect)
            # luci/ombre ai bordi dell'asse
            pygame.draw.line(s, (255, 255, 255, 22), (rect.left, rect.top), (rect.left, rect.bottom))
            pygame.draw.line(s, (0, 0, 0, 35), (rect.right, rect.top), (rect.right, rect.bottom))

    def _venature(self, s, num=22):
        for _ in range(num):
            y0 = self._rng.randint(self.padding + 8, self.h - self.padding - 8)
            amp = self._rng.uniform(2.0, 6.0)
            freq = self._rng.uniform(0.010, 0.028)
            phase = self._rng.uniform(0, 6.28)
            color = self._grain
            last = None
            for x in range(self.padding, self.w - self.padding):
                yy = y0 + math.sin(x * freq + phase) * amp
                if last:
                    pygame.draw.aaline(s, color, last, (x, yy))
                last = (x, yy)

    def _griglia(self, s):
        col = self._grid_color
        # verticali
        for c in range(self.colonne + 1):
            x = self.padding + c * self.larg_cella
            pygame.draw.line(s, col, (x, self.padding), (x, self.h - self.padding), 2)
        # orizzontali
        for r in range(self.righe + 1):
            y = self.padding + r * self.alt_cella
            pygame.draw.line(s, col, (self.padding, y), (self.w - self.padding, y), 2)

    def _bordo(self, s):
        pygame.draw.rect(s, self._edge, s.get_rect(), width=6, border_radius=16)

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
            pygame.draw.rect(
                shadow,
                (0, 0, 0, a),
                base_rect.inflate(i * 2, i * 2),
                border_radius=raggio,
            )
        screen.blit(shadow, (self.x + offset, self.y + offset))

    def _disegna_gambe(self, screen):
        # quattro gambe semplici sotto al piano
        gambe_col = (self._edge[0], self._edge[1], self._edge[2])
        spessore = 14
        altezza = 50
        raggio = 8

        # posizioni (relative al piano)
        gx_left = self.x + 18
        gx_right = self.x + self.w - 18 - spessore
        gy = self.y + self.h - 6  # attaccate sotto il bordo

        gambe = [
            pygame.Rect(gx_left, gy, spessore, altezza),
            pygame.Rect(gx_right, gy, spessore, altezza),
            pygame.Rect(self.x + self.w // 2 - spessore // 2 - 60, gy, spessore, altezza),
            pygame.Rect(self.x + self.w // 2 - spessore // 2 + 60, gy, spessore, altezza),
        ]

        for g in gambe:
            # ombra gambe
            ombra = pygame.Surface((g.w + 10, g.h + 10), pygame.SRCALPHA)
            for i in range(8, 0, -1):
                a = 10 * i
                pygame.draw.rect(ombra, (0, 0, 0, a), ombra.get_rect().inflate(i * 2, i * 2), border_radius=raggio)
            screen.blit(ombra, (g.x + 4, g.y + 4))
            # gamba
            pygame.draw.rect(screen, gambe_col, g, border_radius=raggio)