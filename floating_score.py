import pygame


class FloatingScore:
    """
    Testo "+10" che appare sulla cella, sale verso l'alto e svanisce.
    """

    def __init__(self, cx, cy, text="+10",
                 font_path="Font/Milk Cake.otf", font_size=36,
                 color=(255, 230, 80), duration=1.5):
        self.x = float(cx)
        self.y = float(cy)
        self.vy = -90          # pixel al secondo verso l'alto
        self.age = 0.0
        self.duration = duration
        self.alive = True

        self.color = color

        try:
            font = pygame.font.Font(font_path, font_size)
        except Exception:
            font = pygame.font.SysFont("Arial", font_size, bold=True)

        self.surf = font.render(text, True, color)
        # Outline scuro per leggibilità su qualsiasi sfondo
        self.surf_shadow = font.render(text, True, (80, 40, 0))

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        # Rallenta salendo (attrito visivo)
        self.vy *= max(0.0, 1.0 - dt * 2.5)
        if self.age >= self.duration:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        # Alpha: pieno per il primo 60%, poi fade out
        fade_start = self.duration * 0.6
        if self.age > fade_start:
            t = (self.age - fade_start) / (self.duration - fade_start)
            alpha = int(255 * (1.0 - t))
        else:
            alpha = 255

        shadow = self.surf_shadow.copy()
        shadow.set_alpha(alpha)
        text  = self.surf.copy()
        text.set_alpha(alpha)

        cx, cy = int(self.x), int(self.y)
        # Ombra offset di 2px
        surface.blit(shadow, shadow.get_rect(center=(cx + 2, cy + 2)))
        surface.blit(text,   text.get_rect(center=(cx, cy)))