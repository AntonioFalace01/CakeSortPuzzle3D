import pygame
import math
import random
from assets import Assets

CAKE_THEME_COLORS = {
    "C": [(200, 50,  90), (240, 120, 150), (255, 200, 215)],
    "S": [(230, 70,  60), (255, 150,  90), (255, 220, 190)],
    "V": [(130, 55, 175), (185, 105, 230), (230, 185, 255)],
    "L": [(215, 190,  20), (255, 235,  70), (255, 250, 200)],
    "A": [(155, 100,  35), (210, 155,  75), (255, 220, 160)],
    "B": [(35,  75, 210), (75, 135, 255), (175, 210, 255)],
    "D": [(50,  20,  70), (125,  55, 150), (205, 155, 230)],
    "E": [(25, 155,  85), (75, 215, 135), (175, 255, 210)],
}


class _Confetto:
    def __init__(self, cx, cy, colors, box_w, box_h):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(40, 160)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(30, 90)
        self.x  = float(cx)
        self.y  = float(cy)
        self.gravity = random.uniform(120, 220)
        self.life    = random.uniform(1.1, 2.0)
        self.age     = 0.0
        self.color   = random.choice(colors)
        self.w = random.randint(4, 8)
        self.h = random.randint(3, 5)
        self.rot     = random.uniform(0, 360)
        self.rot_spd = random.uniform(-280, 280)
        self._bx  = cx - box_w // 2 + 6
        self._by  = cy - box_h // 2 + 6
        self._bx2 = cx + box_w // 2 - 6
        self._by2 = cy + box_h // 2 - 6

    def update(self, dt):
        self.age += dt
        self.vy  += self.gravity * dt
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.rot += self.rot_spd * dt
        if self.x < self._bx:   self.x = self._bx;  self.vx =  abs(self.vx) * 0.5
        if self.x > self._bx2:  self.x = self._bx2; self.vx = -abs(self.vx) * 0.5
        if self.y > self._by2:  self.y = self._by2; self.vy = -abs(self.vy) * 0.4

    @property
    def alive(self):
        return self.age < self.life

    def draw(self, surface):
        alpha = max(0, int(255 * (1.0 - self.age / self.life) ** 1.4))
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s.fill((*self.color, alpha))
        rot = pygame.transform.rotate(s, self.rot)
        surface.blit(rot, rot.get_rect(center=(int(self.x), int(self.y))))

class _Sparkle:
    def __init__(self, cx, cy, color, box_w, box_h):
        bx = cx - box_w // 2 + 15
        by = cy - box_h // 2 + 15
        self.x     = random.uniform(bx, cx + box_w // 2 - 15)
        self.y     = random.uniform(by, cy + box_h // 2 - 15)
        self.color = color
        self.life  = random.uniform(0.5, 1.2)
        self.age   = random.uniform(0, 0.4)
        self.size  = random.uniform(2.5, 5.5)
        self.pulse = random.uniform(3, 7)

    @property
    def alive(self):
        return self.age < self.life

    def update(self, dt):
        self.age += dt

    def draw(self, surface):
        t = self.age / self.life
        alpha = int(255 * math.sin(t * math.pi) *
                    (0.6 + 0.4 * math.sin(self.age * self.pulse * math.pi * 2)))
        alpha = max(0, min(255, alpha))
        r = int(self.size)
        if r < 1:
            return
        sp = pygame.Surface((r * 4 + 2, r * 4 + 2), pygame.SRCALPHA)
        cx, cy = r * 2 + 1, r * 2 + 1
        arm = r * 2
        for angle in [0, 45, 90, 135]:
            rad = math.radians(angle)
            for d in range(1, arm + 1):
                a = max(0, int(alpha * (1 - d / arm)))
                for dx, dy in [(math.cos(rad), math.sin(rad)),
                               (-math.cos(rad), -math.sin(rad))]:
                    px = int(cx + dx * d)
                    py = int(cy + dy * d)
                    if 0 <= px < r * 4 + 2 and 0 <= py < r * 4 + 2:
                        sp.set_at((px, py), (*self.color, a))
        surface.blit(sp, (int(self.x) - r * 2 - 1, int(self.y) - r * 2 - 1))

class UnlockEffect:
    BOX_W = 260
    BOX_H = 310

    FADE_IN_END  = 0.40
    HOLD_END     = 3.80
    FADE_OUT_END = 4.40

    def __init__(self, screen_w, screen_h, cake_tipo):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.cx = screen_w // 2
        self.cy = screen_h // 2

        self.tipo   = cake_tipo
        self.colors = CAKE_THEME_COLORS.get(
            cake_tipo, [(200, 100, 150), (255, 180, 210), (255, 230, 240)])
        self.accent = self.colors[0]
        self.mid    = self.colors[1]
        self.light  = self.colors[2]

        self.age = 0.0
        self._confetti: list[_Confetto] = []
        self._sparkles: list[_Sparkle]  = []
        self._burst_done    = False
        self._sparkle_timer = 0.0

        try:
            self.font_title = pygame.font.Font("Font/Milk Cake.otf", 26)
            self.font_sub   = pygame.font.Font("Font/Milk Cake.otf", 15)
        except Exception:
            self.font_title = pygame.font.SysFont("Arial", 26, bold=True)
            self.font_sub   = pygame.font.SysFont("Arial", 15)

        self._slice_surf  = self._make_slice(88)
        self._card_base   = self._build_card_base()
        self._card_border = self._build_card_border()

    def _make_slice(self, size):
        key = Assets.TYPE_TO_SLICE.get(self.tipo)
        if not key:
            return None
        raw = Assets._slice_src.get(key)
        if not raw:
            return None
        return pygame.transform.smoothscale(raw, (size, size))

    def _build_card_base(self):
        """Sfondo rosa pastello: da rosa caldo in alto a bianco rosato in basso."""
        w, h = self.BOX_W, self.BOX_H
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        top = (255, 205, 220)   # rosa pastello caldo
        bot = (255, 238, 244)   # quasi bianco rosato

        for y in range(h):
            t = (y / h) ** 0.65
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(surf, (r, g, b, 252), (0, y), (w, y))

        # Vignetta rosata interna per profondità
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(16):
            a = int(22 * (1 - i / 16) ** 2)
            if a > 0:
                pygame.draw.rect(vig, (210, 80, 120, a), (i, i, w - i * 2, h - i * 2),
                                 border_radius=max(1, 28 - i))
        surf.blit(vig, (0, 0))

        # Angoli arrotondati con maschera
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=28)
        for y in range(h):
            for x in range(w):
                if mask.get_at((x, y))[3] == 0:
                    surf.set_at((x, y), (0, 0, 0, 0))
        return surf

    def _build_card_border(self):
        w, h = self.BOX_W, self.BOX_H
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (230, 130, 160, 220), (0, 0, w, h), width=3, border_radius=28)
        pygame.draw.rect(surf, (255, 255, 255, 80), (5, 5, w - 10, h - 10), width=1, border_radius=23)
        return surf


    def update(self, dt):
        self.age += dt

        if not self._burst_done and self.age >= self.FADE_IN_END:
            self._burst_done = True
            for _ in range(55):
                self._confetti.append(
                    _Confetto(self.cx, self.cy, self.colors, self.BOX_W, self.BOX_H))

        if self.FADE_IN_END < self.age < self.HOLD_END:
            self._sparkle_timer += dt
            while self._sparkle_timer > 0.09:
                self._sparkle_timer -= 0.09
                col = random.choice([self.light, (255, 255, 255), self.mid])
                self._sparkles.append(
                    _Sparkle(self.cx, self.cy, col, self.BOX_W - 20, self.BOX_H - 20))

        for c in self._confetti:
            c.update(dt)
        self._confetti = [c for c in self._confetti if c.alive]
        for s in self._sparkles:
            s.update(dt)
        self._sparkles = [s for s in self._sparkles if s.alive]


    def _card_transform(self):
        if self.age < self.FADE_IN_END:
            t = self.age / self.FADE_IN_END
            ease = 1 - (1 - t) ** 3
            scale = ease * 1.07
            alpha = int(255 * ease)
        elif self.age < self.HOLD_END:
            scale = 1.0 + 0.007 * math.sin(self.age * math.pi * 1.8)
            alpha = 255
        elif self.age < self.FADE_OUT_END:
            t = (self.age - self.HOLD_END) / (self.FADE_OUT_END - self.HOLD_END)
            ease_out = t ** 2
            scale = 1.0 - ease_out * 0.10
            alpha = int(255 * (1.0 - ease_out))
        else:
            scale, alpha = 0.0, 0
        return scale, alpha

    def _draw_shadow(self, surface, scale, alpha):
        sw = int(self.BOX_W * scale) + 44
        sh = int(self.BOX_H * scale) + 44
        shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for i in range(22, 0, -2):
            a = int(alpha * 0.22 * (1 - i / 22) ** 1.5)
            if a <= 0: continue
            pygame.draw.rect(shadow, (0, 0, 0, a),
                             (i, i, sw - i * 2, sh - i * 2),
                             border_radius=max(1, 30 + i))
        surface.blit(shadow, shadow.get_rect(center=(self.cx + 6, self.cy + 10)))

    def _draw_glow(self, surface, scale, alpha):
        pulse = 0.5 + 0.5 * math.sin(self.age * math.pi * 2.4)
        gw = int(self.BOX_W * scale) + 64
        gh = int(self.BOX_H * scale) + 64
        glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
        pink = (235, 130, 160)
        for i in range(30, 0, -3):
            a = int(alpha * (0.18 + 0.12 * pulse) * (1 - i / 30) ** 1.2)
            if a <= 0: continue
            pygame.draw.rect(glow, (*pink, a),
                             (i, i, gw - i * 2, gh - i * 2),
                             border_radius=max(1, 34 + i))
        surface.blit(glow, glow.get_rect(center=(self.cx, self.cy)))

    def _draw_card_body(self, surface, scale, alpha):
        w = int(self.BOX_W * scale)
        h = int(self.BOX_H * scale)
        if w < 4 or h < 4 or alpha <= 0:
            return None
        base   = pygame.transform.smoothscale(self._card_base,   (w, h))
        border = pygame.transform.smoothscale(self._card_border, (w, h))
        base.set_alpha(alpha)
        border.set_alpha(alpha)
        rect = base.get_rect(center=(self.cx, self.cy))
        surface.blit(base,   rect)
        surface.blit(border, rect)
        return rect

    def _draw_accent_bar(self, surface, card_rect, alpha):
        if not card_rect or alpha <= 0:
            return
        bar_h = max(5, int(card_rect.height * 0.020))
        bar_w = card_rect.width - 8
        bar_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        # Bianco semi-trasparente su sfondo colorato
        for x in range(bar_w):
            t = abs(x / bar_w - 0.5) * 2
            a = int(alpha * (1 - t ** 2) * 0.5)
            if a > 0:
                pygame.draw.line(bar_surf, (255, 255, 255, a), (x, 0), (x, bar_h - 1))
        surface.blit(bar_surf, (card_rect.x + 4, card_rect.y + 4))

    def _draw_slice(self, surface, card_rect, alpha):
        if not self._slice_surf or not card_rect or alpha <= 0:
            return
        if self.age < self.FADE_IN_END:
            t = self.age / self.FADE_IN_END
            ease = 1 - (1 - t) ** 3
            drop = int((1 - ease) * -55)
            sl_alpha = int(255 * ease)
            sc = 0.72 + ease * 0.38
        else:
            drop = 0
            sl_alpha = alpha
            sc = 1.0 + 0.022 * math.sin(self.age * math.pi * 1.6)

        rot = math.sin(self.age * 0.85) * 5
        size = int(88 * sc)
        if size < 4: return
        scaled  = pygame.transform.smoothscale(self._slice_surf, (size, size))
        rotated = pygame.transform.rotate(scaled, rot)

        slice_cx = self.cx
        slice_cy = card_rect.centery - int(card_rect.height * 0.12) + drop

        # Alone pulsante rosa
        halo_r = size // 2 + 20
        hp = 0.5 + 0.5 * math.sin(self.age * math.pi * 2.8)
        halo_a = int(sl_alpha * (0.30 + 0.18 * hp))
        pink_halo = (235, 140, 170)
        halo = pygame.Surface((halo_r * 2, halo_r * 2), pygame.SRCALPHA)
        for ri in range(halo_r, 0, -3):
            a = int(halo_a * (1 - ri / halo_r) ** 1.2)
            if a > 0:
                pygame.draw.circle(halo, (*pink_halo, a), (halo_r, halo_r), ri)
        surface.blit(halo, halo.get_rect(center=(slice_cx, slice_cy)))

        # Piatto bianco con bordo rosa
        pr = size // 2 + 5
        plate = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
        pygame.draw.circle(plate, (255, 255, 255, min(sl_alpha, 235)), (pr, pr), pr)
        pygame.draw.circle(plate, (220, 120, 155, min(sl_alpha, 160)), (pr, pr), pr, 2)
        surface.blit(plate, plate.get_rect(center=(slice_cx, slice_cy)))

        rotated.set_alpha(sl_alpha)
        surface.blit(rotated, rotated.get_rect(center=(slice_cx, slice_cy)))

    def _draw_divider(self, surface, x, y, w, alpha, color=None):
        """Linea orizzontale con fade ai bordi."""
        col = color if color else self.mid
        ls = pygame.Surface((w, 2), pygame.SRCALPHA)
        for px in range(w):
            t = abs(px / w - 0.5) * 2
            a = int(alpha * (1 - t ** 1.8))
            if a > 0:
                ls.set_at((px, 0), (*col, a))
                ls.set_at((px, 1), (*col, a // 2))
        surface.blit(ls, ls.get_rect(center=(x, y)))

    def _draw_text(self, surface, card_rect, alpha):
        if not card_rect or alpha <= 0:
            return
        t_start = self.FADE_IN_END + 0.10
        if self.age < t_start:
            return

        t_prog = min(1.0, (self.age - t_start) / 0.26)
        ease   = 1 - (1 - t_prog) ** 3
        ta     = int(alpha * ease)
        slide  = int((1 - ease) * 16)

        base_y = card_rect.centery + int(card_rect.height * 0.30) + slide
        div_w  = int(card_rect.width * 0.62)

        # Colori testo su sfondo rosa pastello
        dark       = (90, 35, 55)
        white      = (255, 255, 255)
        accent_txt = (185, 60, 100)

        # Divisore superiore
        self._draw_divider(surface, self.cx, base_y - 36, div_w, ta, (255, 255, 255))

        l1 = self.font_title.render("Nuova torta", True, dark)
        l1_sh = self.font_title.render("Nuova torta", True, white)
        l1_sh.set_alpha(min(ta, 120))
        l1.set_alpha(ta)
        y1 = base_y - 14
        surface.blit(l1_sh, l1_sh.get_rect(center=(self.cx + 1, y1 + 1)))
        surface.blit(l1,    l1.get_rect(center=(self.cx, y1)))

        accent_dark = accent_txt
        l2 = self.font_title.render("sbloccata!", True, accent_dark)
        l2.set_alpha(ta)
        y2 = y1 + l1.get_height() + 2
        surface.blit(l2, l2.get_rect(center=(self.cx, y2)))

        # Divisore inferiore
        div_y2 = y2 + l2.get_height() + 8
        self._draw_divider(surface, self.cx, div_y2, div_w, ta, (255, 255, 255))

        if self.age > self.HOLD_END - 1.3:
            bt = (self.age - (self.HOLD_END - 1.3)) / 1.3
            ba = int(ta * (0.35 + 0.65 * math.sin(bt * math.pi * 4.5)))
            ba = max(0, ba)
            hint = self.font_sub.render("continua…", True, dark)
            hint.set_alpha(ba)
            surface.blit(hint, hint.get_rect(center=(self.cx, div_y2 + 16)))

    def _draw_particles_clipped(self, surface, card_rect, alpha):
        if not card_rect or alpha <= 0:
            return
        cw, ch = card_rect.width, card_rect.height
        if cw < 1 or ch < 1:
            return
        clip = pygame.Surface((cw, ch), pygame.SRCALPHA)
        ox, oy = card_rect.x, card_rect.y
        for c in self._confetti:
            ox_c, oy_c = c.x, c.y
            c.x -= ox; c.y -= oy
            c.draw(clip)
            c.x, c.y = ox_c, oy_c
        for s in self._sparkles:
            ox_s, oy_s = s.x, s.y
            s.x -= ox; s.y -= oy
            s.draw(clip)
            s.x, s.y = ox_s, oy_s
        # maschera angoli
        mask = pygame.Surface((cw, ch), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, cw, ch), border_radius=28)
        clip.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        clip.set_alpha(alpha)
        surface.blit(clip, card_rect.topleft)


    def draw(self, surface):
        scale, alpha = self._card_transform()
        if alpha <= 0:
            return
        self._draw_shadow(surface, scale, alpha)
        self._draw_glow(surface, scale, alpha)
        card_rect = self._draw_card_body(surface, scale, alpha)
        if not card_rect:
            return
        self._draw_accent_bar(surface, card_rect, alpha)
        self._draw_particles_clipped(surface, card_rect, alpha)
        self._draw_slice(surface, card_rect, alpha)
        self._draw_text(surface, card_rect, alpha)

    def is_done(self):
        return self.age >= self.FADE_OUT_END