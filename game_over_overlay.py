import pygame
import random

class GameOverOverlay:
    """Overlay game over con animazione fade-in, pannello rosa uniforme e confetti."""

    FADE_DURATION  = 1.6   # fade scuro più lento
    SLIDE_DURATION = 1.3   # pannello più lento
    SLIDE_DELAY    = 0.9   # aspetta di più prima di far salire il pannello
    SCORE_DURATION = 1.1   # count-up più lento
    SCORE_DELAY    = 1.8   # aspetta che il pannello sia ben visibile

    CONFETTI_COLORS = [
        (255, 182, 213),  # rosa chiaro
        (255, 105, 180),  # hot pink
        (255,  20, 147),  # deep pink
        (255, 230, 240),  # rosa pallido
        (255, 160, 200),  # rosa medio
        (255, 200,  80),  # giallo caldo
        (255, 255, 255),  # bianco
        (252, 100, 160),  # fucsia
    ]

    def __init__(self, final_score: int):
        self.final_score = final_score
        self.age = 0.0
        self.confetti = []
        self._spawn_confetti(48)

    # -- confetti --------------------------------------------------------------

    def _spawn_confetti(self, n):
        for _ in range(n):
            self.confetti.append({
                "x":     random.uniform(200, 700),
                "y":     random.uniform(-30, -5),
                "vx":    random.uniform(-35, 35),
                "vy":    random.uniform(55, 145),
                "w":     random.randint(5, 10),
                "h":     random.randint(3, 6),
                "rot":   random.uniform(0, 360),
                "rot_v": random.uniform(-260, 260),
                "color": random.choice(self.CONFETTI_COLORS),
                "born":  random.uniform(0.8, 3.2),   # partono più tardi
            })

    def update(self, dt):
        self.age += dt
        for c in self.confetti:
            if self.age < c["born"]:
                continue
            c["y"]   += c["vy"]  * dt
            c["x"]   += c["vx"]  * dt
            c["rot"] += c["rot_v"] * dt
            if c["y"] > 750:
                c["x"]   = random.uniform(200, 700)
                c["y"]   = random.uniform(-30, -5)
                c["born"] = self.age + random.uniform(0.1, 1.0)

    # -- easing ----------------------------------------------------------------

    @staticmethod
    def _ease_out_cubic(t):
        return 1 - (1 - t) ** 3

    @staticmethod
    def _ease_out_back(t):
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    # -- draw ------------------------------------------------------------------

    def draw(self, surface):
        W, H = surface.get_size()
        cx = W // 2

        # 1. overlay scuro con tinta rosata (fade lento)
        fade_t = min(1.0, self.age / self.FADE_DURATION)
        overlay_alpha = int(self._ease_out_cubic(fade_t) * 160)
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((90, 10, 45, overlay_alpha))
        surface.blit(overlay, (0, 0))

        # 2. confetti
        for c in self.confetti:
            if self.age < c["born"]:
                continue
            life = self.age - c["born"]
            alpha = max(0, min(255, int(255 * (1.0 - max(0.0, life - 2.5) / 0.8))))
            surf = pygame.Surface((c["w"], c["h"]), pygame.SRCALPHA)
            surf.fill((*c["color"], alpha))
            rotated = pygame.transform.rotate(surf, c["rot"])
            rect = rotated.get_rect(center=(int(c["x"]), int(c["y"])))
            surface.blit(rotated, rect)

        # 3. pannello slide-up
        panel_progress = max(0.0, self.age - self.SLIDE_DELAY)
        panel_t = min(1.0, panel_progress / self.SLIDE_DURATION)
        ease_t  = self._ease_out_back(panel_t)
        # alpha sale lentamente nella prima metà del viaggio
        panel_alpha = int(min(1.0, panel_t / 0.6) * 255)

        box_w, box_h = 420, 310
        box_x = cx - box_w // 2
        BASE_Y = H // 2 - box_h // 2
        offset_y = int((1.0 - ease_t) * 60)
        box_y = BASE_Y + offset_y

        # ── pannello: un solo rect arrotondato, colore uniforme rosa cipria ──
        # Disegniamo tutto su panel_surf, poi la posizioniamo.
        # NON sovrapponiamo rect secondari: evita la linea di divisione visibile.
        panel_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)

        # riempimento uniforme rosa cipria
        pygame.draw.rect(
            panel_surf,
            (255, 232, 243, panel_alpha),
            (0, 0, box_w, box_h),
            border_radius=24
        )
        # bordo rosa caldo (sopra al fill, stessa border_radius)
        pygame.draw.rect(
            panel_surf,
            (240, 100, 160, panel_alpha),
            (0, 0, box_w, box_h),
            width=3,
            border_radius=24
        )

        surface.blit(panel_surf, (box_x, box_y))

        if panel_t < 0.05:
            return

        # font
        try:
            font_title = pygame.font.Font("Font/Milk Cake.otf", 46)
            font_mid   = pygame.font.Font("Font/Milk Cake.otf", 20)
            font_score = pygame.font.Font("Font/Milk Cake.otf", 38)
            font_small = pygame.font.Font("Font/Milk Cake.otf", 16)
        except Exception:
            font_title = pygame.font.SysFont("Arial", 46, bold=True)
            font_mid   = pygame.font.SysFont("Arial", 20)
            font_score = pygame.font.SysFont("Arial", 38, bold=True)
            font_small = pygame.font.SysFont("Arial", 16)

        txt_alpha = panel_alpha

        def blit_alpha(txt_surf, pos):
            tmp = txt_surf.copy()
            tmp.set_alpha(txt_alpha)
            surface.blit(tmp, pos)

        # "Game Over!"
        title = font_title.render("Game Over!", True, (185, 30, 90))
        blit_alpha(title, (cx - title.get_width() // 2, box_y + 22))

        # sottotitolo
        sub = font_mid.render("Nessuna mossa disponibile", True, (220, 80, 130))
        blit_alpha(sub, (cx - sub.get_width() // 2, box_y + 82))

        # badge punteggio con count-up
        score_progress = max(0.0, self.age - self.SCORE_DELAY)
        score_t   = min(1.0, score_progress / self.SCORE_DURATION)
        displayed = int(self._ease_out_cubic(score_t) * self.final_score)

        badge_w, badge_h = 200, 66
        badge_x = cx - badge_w // 2
        badge_y = box_y + 120
        badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(
            badge_surf,
            (255, 105, 180, panel_alpha // 4),
            (0, 0, badge_w, badge_h),
            border_radius=12
        )
        pygame.draw.rect(
            badge_surf,
            (240, 100, 160, panel_alpha // 2),
            (0, 0, badge_w, badge_h),
            width=2,
            border_radius=12
        )
        surface.blit(badge_surf, (badge_x, badge_y))

        lbl = font_small.render("Punteggio finale", True, (200, 50, 110))
        lbl.set_alpha(txt_alpha)
        surface.blit(lbl, (cx - lbl.get_width() // 2, badge_y + 8))

        score_txt = font_score.render(str(displayed), True, (185, 30, 90))
        score_txt.set_alpha(txt_alpha)
        surface.blit(score_txt, (cx - score_txt.get_width() // 2, badge_y + 28))

        # linea separatrice
        line_y = box_y + 210
        sep_surf = pygame.Surface((box_w - 60, 1), pygame.SRCALPHA)
        sep_surf.fill((240, 160, 200, panel_alpha // 2))
        surface.blit(sep_surf, (cx - (box_w - 60) // 2, line_y))

        # hint
        hint = font_small.render("Premi RESTART per una nuova partita", True, (210, 100, 150))
        hint.set_alpha(panel_alpha // 2)
        surface.blit(hint, (cx - hint.get_width() // 2, line_y + 12))