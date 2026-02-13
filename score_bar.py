import pygame

class ScoreBar:
    def __init__(self, x, y, width, height,image_path="Sprites/barra.png"):
        self.rect = pygame.Rect(x, y, width, height)
        # Carica sfondo
        try:
            raw = pygame.image.load(image_path).convert_alpha()
            self.bg = pygame.transform.smoothscale(raw, (width, height))
        except:
            self.bg = None

        # Padding più generoso per non toccare i bordi arrotondati
        pad_x = int(width * 0.16)  # prima era ~0.06
        pad_y = int(height * 0.40)  # prima era ~0.22

        inner_w = width - 2 * pad_x
        inner_h = height - 2 * pad_y
        self.inner_rect = pygame.Rect(self.rect.x + pad_x+2, self.rect.y + pad_y-6, inner_w, inner_h)

        # Il riempimento sarà un po’ più basso e centrato verticalmente nell’inner_rect
        fill_margin_x = int(inner_w * 0.01)  # piccolo margine laterale
        fill_margin_y = int(inner_h * 0.18)  # riduce altezza per stare dentro
        self.fill_area = pygame.Rect(
            self.inner_rect.x + fill_margin_x,
            self.inner_rect.y + fill_margin_y,
            self.inner_rect.width - 2 * fill_margin_x,
            self.inner_rect.height - 2 * fill_margin_y
        )

        # Stile riempimento
        self.fill_color = (255, 160, 220)
        self.fill_back = (255, 210, 240)  # “pista” chiara sotto
        self.border_radius = self.fill_area.height // 2  # arrotondato

        # Testo
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.text_color = (255, 255, 255)

        # valori
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
        # Sfondo
        if self.bg:
            window.blit(self.bg, self.rect)
        else:
            pygame.draw.rect(window, (240, 180, 210), self.rect, border_radius=20)

        # Disegna la “pista” chiara (non piena) per dare margine
        pygame.draw.rect(window, self.fill_back, self.fill_area, border_radius=self.border_radius)

        # Riempimento: calcola larghezza e resta dentro fill_area
        fill_w = max(0, int(self.fill_area.width * self.smooth))
        fill_rect = pygame.Rect(self.fill_area.x, self.fill_area.y, fill_w, self.fill_area.height)

        # Clip per evitare che eventuali arrotondamenti escano
        prev_clip = window.get_clip()
        window.set_clip(self.fill_area)
        pygame.draw.rect(window, self.fill_color, fill_rect, border_radius=self.border_radius)
        window.set_clip(prev_clip)

        # Testo
        txt = f"{label}: {min(self.current, self.target)}/{self.target}"
        surf = self.font.render(txt, True, self.text_color)
        window.blit(surf, (self.rect.centerx - surf.get_width() // 2, self.inner_rect.y - 24))
