import pygame
import math
from assets import Assets

class MovingSlice:
    def __init__(self, tipo, start_px, end_px, duration=0.50, count=1, plate_size=60):

        self.tipo = tipo
        self.start_x, self.start_y = start_px
        self.end_x, self.end_y = end_px
        self.duration = max(0.01, duration)
        self.t = 0.0  # tempo accumulato
        self.count = max(1, count)
        self.alive = True

        # recupera la chiave della fetta
        slice_key = Assets.TYPE_TO_SLICE.get(tipo)
        if slice_key:
            target = int(plate_size * 0.5)
            base_img = pygame.transform.smoothscale(
                Assets._slice_src[slice_key], (target, target)
            )

            offset = 8
            width = target + (self.count - 1) * offset
            height = target

            self.img = pygame.Surface((width, height), pygame.SRCALPHA)

            for i in range(self.count):
                self.img.blit(base_img, (i * offset, 0))
        else:
            self.img = None

    def update(self, dt):
        self.t += dt
        if self.t >= self.duration:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return

        raw_alpha = self.t / self.duration
        alpha = 1 - (1 - raw_alpha) ** 3

        x = self.start_x + (self.end_x - self.start_x) * alpha
        y = self.start_y + (self.end_y - self.start_y) * alpha

        arc_height = -20
        y += arc_height * math.sin(alpha * math.pi)
        if self.img:
            rect = self.img.get_rect(center=(x, y))
            surface.blit(self.img, rect)
        else:
            r = 6
            pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), r)
