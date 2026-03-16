import pygame

class ScoreBar:
    def __init__(self, x, y, width, height, image_path="Sprites/barra.png",
                 font_path="Font/Brown Cake.ttf", font_size=24):
        self.rect = pygame.Rect(x, y, width, height)

        try:
            raw = pygame.image.load(image_path).convert_alpha()
            self.bg = pygame.transform.smoothscale(raw, (width, height))
        except:
            self.bg = None

        pad_x = int(width * 0.16)
        pad_y = int(height * 0.40)

        inner_w = width - 2 * pad_x
        inner_h = height - 2 * pad_y
        self.inner_rect = pygame.Rect(self.rect.x + pad_x + 3, self.rect.y + pad_y - 10, inner_w, inner_h)

        fill_margin_x = int(inner_w * 0.01)
        fill_margin_y = int(inner_h * 0.18)
        self.fill_area = pygame.Rect(
            self.inner_rect.x + fill_margin_x,
            self.inner_rect.y + fill_margin_y,
            self.inner_rect.width - 2 * fill_margin_x,
            self.inner_rect.height - 2 * fill_margin_y
        )

        self.fill_color = (255, 160, 220)
        self.fill_back = (255, 210, 240)
        self.border_radius = self.fill_area.height // 2

        try:
            self.font = pygame.font.Font(font_path, font_size)
        except Exception as e:
            print("Errore caricamento font ScoreBar:", e)
            self.font = pygame.font.SysFont("Arial", font_size, bold=True)

        self.text_color = (255, 255, 255)

        self.current = 0
        self.target = 100
        self.smooth = 0.0

    def set_progress(self, current, target):
        self.current = max(0, current)
        self.target = max(1, target)

    def update(self, dt=0.016):
        target_ratio = min(1.0, self.current / self.target)
        speed = 6.0
        self.smooth += (target_ratio - self.smooth) * min(1.0, speed * dt)

    def draw(self, window, label="Prossima torta"):
        if self.bg:
            window.blit(self.bg, self.rect)
        else:
            pygame.draw.rect(window, (240, 180, 210), self.rect, border_radius=20)

        pygame.draw.rect(window, self.fill_back, self.fill_area, border_radius=self.border_radius)

        fill_w = max(0, int(self.fill_area.width * self.smooth))
        fill_rect = pygame.Rect(self.fill_area.x, self.fill_area.y, fill_w, self.fill_area.height)

        prev_clip = window.get_clip()
        window.set_clip(self.fill_area)
        pygame.draw.rect(window, self.fill_color, fill_rect, border_radius=self.border_radius)
        window.set_clip(prev_clip)

        if self.current >= self.target and self.current == self.target:
            txt = f"{label}"
        else:
            txt = f"{label}: {min(self.current, self.target)}/{self.target}"

        tx = self.rect.centerx - self.font.size(txt)[0] // 2
        ty = self.inner_rect.y - 40

        # Ombra scura per contrasto
        shadow = self.font.render(txt, True, (40, 20, 30))
        window.blit(shadow, (tx + 2, ty + 2))

        # Testo principale
        surf = self.font.render(txt, True, self.text_color)
        window.blit(surf, (tx, ty))
