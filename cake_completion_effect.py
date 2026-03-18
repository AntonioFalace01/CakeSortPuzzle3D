import pygame
import math
import random


class Confetto:
    COLORI = [
        (255, 100, 150),  # rosa
        (255, 200,  80),  # giallo
        (100, 220, 130),  # verde menta
        (100, 180, 255),  # azzurro
        (220, 120, 255),  # lilla
        (255, 160,  60),  # arancio
        (255, 255, 255),  # bianco
    ]

    def __init__(self, cx, cy):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(60, 200)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(40, 120)  # leggero bias verso l'alto
        self.x = float(cx)
        self.y = float(cy)
        self.gravity = random.uniform(180, 280)
        self.life = random.uniform(0.55, 0.9)   # durata in secondi
        self.age  = 0.0
        self.color = random.choice(self.COLORI)
        self.w = random.randint(4, 9)
        self.h = random.randint(3, 6)
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-300, 300)

    def update(self, dt):
        self.age += dt
        self.vy  += self.gravity * dt
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.rot += self.rot_speed * dt

    @property
    def alive(self):
        return self.age < self.life

    def draw(self, surface):
        alpha = max(0, 1.0 - self.age / self.life)
        a = int(alpha * 255)

        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        surf.fill((*self.color, a))

        rotated = pygame.transform.rotate(surf, self.rot)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class CakeCompletionEffect:
    GLOW_COLOR = (255, 230, 120)   # giallo dorato

    def __init__(self, cx, cy, plate_size=75, n_confetti=28):
        self.cx = cx
        self.cy = cy
        self.plate_size = plate_size
        self.n_confetti = n_confetti
        self.pulse_age  = 0.0
        self.pulse_done = False

        self.burst_triggered = False
        self.confetti: list[Confetto] = []

    def update_pulse(self, dt):
        if not self.pulse_done:
            self.pulse_age += dt

    def draw_pulse(self, surface, cx=None, cy=None, plate_size=None):
        """
        Disegna l'alone pulsante attorno alla torta.
        Usa i parametri passati (o quelli salvati nel costruttore).
        """
        if self.pulse_done:
            return

        cx         = cx         or self.cx
        cy         = cy         or self.cy
        plate_size = plate_size or self.plate_size

        # Oscillazione lenta
        pulse = 0.5 + 0.5 * math.sin(self.pulse_age * math.pi * 4)

        # Alone esterno che si espande e pulsa
        max_radius = int(plate_size * 0.72)
        radius     = int(plate_size * 0.45 + pulse * plate_size * 0.20)
        alpha      = int(80 + pulse * 100)

        glow_surf = pygame.Surface((max_radius * 2 + 4, max_radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf,
            (*self.GLOW_COLOR, alpha),
            (max_radius + 2, max_radius + 2),
            radius
        )
        surface.blit(glow_surf, glow_surf.get_rect(center=(cx, cy)))

        # Ring esterno più sottile
        ring_r = int(plate_size * 0.50 + pulse * plate_size * 0.18)
        ring_surf = pygame.Surface((ring_r * 2 + 6, ring_r * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(
            ring_surf,
            (*self.GLOW_COLOR, int(alpha * 0.5)),
            (ring_r + 3, ring_r + 3),
            ring_r,
            3
        )
        surface.blit(ring_surf, ring_surf.get_rect(center=(cx, cy)))

    def trigger_burst(self):
        if self.burst_triggered:
            return
        self.burst_triggered = True
        self.pulse_done = True
        for _ in range(self.n_confetti):
            self.confetti.append(Confetto(self.cx, self.cy))

    def update_burst(self, dt):
        for c in self.confetti:
            c.update(dt)
        self.confetti = [c for c in self.confetti if c.alive]

    def draw_burst(self, surface):
        for c in self.confetti:
            c.draw(surface)


    def is_done(self):
        return self.pulse_done and not self.confetti