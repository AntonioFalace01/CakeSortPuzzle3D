import pygame
from button import Button


class VolumeSlider:
    def __init__(self, x, y, w, h, initial_value=0.5,
                 knob_path="Sprites/pomello.png", label="Volume",font_path="Font/Milk Cake.otf", font_size=20):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = float(initial_value)
        self.label = label
        self.dragging = False
        self.font = pygame.font.Font(font_path, font_size)

        self.knob_img = None
        try:
            raw_knob = pygame.image.load(knob_path).convert_alpha()
            target_h = int(h * 3)
            scale_ratio = target_h / raw_knob.get_height()
            target_w = int(raw_knob.get_width() * scale_ratio)
            self.knob_img = pygame.transform.smoothscale(raw_knob, (target_w, target_h))
        except Exception as e:
            print("Errore caricamento pomello:", e)
            self.knob_img = None

        pad_x = int(w * 0.10)
        pad_y = int(h * 0.30)
        inner_w = w - 2 * pad_x
        inner_h = h - 2 * pad_y
        self.inner_rect = pygame.Rect(x + pad_x, y + pad_y, inner_w, inner_h)

        track_margin_y = int(self.inner_rect.height * 0.18)
        self.track_rect = pygame.Rect(
            self.inner_rect.x,
            self.inner_rect.y + track_margin_y,
            self.inner_rect.width,
            self.inner_rect.height - 2 * track_margin_y
        )

        self.fill_color = (255, 160, 220)
        self.fill_back = (255, 210, 240)
        self.radius = max(1, self.track_rect.height // 2)

        self.hit_rect = self.rect.inflate(12, 12)

    def draw(self, window):
        txt = f"{self.label}: {int(self.value * 100)}%"
        surf = self.font.render(txt, True, (255, 255, 255))
        window.blit(surf, (self.rect.x, self.rect.y - 30))

        pygame.draw.rect(window, (240, 180, 210), self.rect, border_radius=20)
        pygame.draw.rect(window, self.fill_back, self.track_rect, border_radius=self.radius)

        fill_w = int(self.track_rect.width * self.value)
        fill_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, fill_w, self.track_rect.height)

        prev = window.get_clip()
        window.set_clip(self.track_rect)
        pygame.draw.rect(window, self.fill_color, fill_rect, border_radius=self.radius)
        window.set_clip(prev)

        knob_cx = self.track_rect.x + fill_w
        knob_cy = self.track_rect.centery+4

        if self.knob_img:
            knob_rect = self.knob_img.get_rect(center=(knob_cx, knob_cy))
            window.blit(self.knob_img, knob_rect)
        else:
            r = self.track_rect.height // 2 + 6
            pygame.draw.circle(window, (255, 255, 255), (knob_cx, knob_cy), r)
            pygame.draw.circle(window, (120, 120, 120), (knob_cx, knob_cy), r, 2)

    def handle_event(self, event):
        changed = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hit_rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
                changed = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])
            changed = True

        return changed

    def update_value(self, mouse_x):
        rel = mouse_x - self.track_rect.x
        val = rel / self.track_rect.width
        self.value = max(0.0, min(1.0, val))


class SoundManager:
    def __init__(self):

        self.slider_music = VolumeSlider(
            250, 250, 400, 45,
            initial_value=0.4,
            knob_path="Sprites/pomello.png",
            label="Musica"
        )

        self.slider_sfx = VolumeSlider(
            250, 350, 400, 45,
            initial_value=0.7,
            knob_path="Sprites/pomello.png",
            label="Effetti"
        )

        self.button_resume = Button(335, 400, 220, 120, "Sprites/Button/button_resume.png")

        self.update_volumes()

    def update_volumes(self):
        pygame.mixer.music.set_volume(self.slider_music.value)

        if SFX.pickup:
            SFX.pickup.set_volume(self.slider_sfx.value)
        if SFX.place:
            SFX.place.set_volume(self.slider_sfx.value)


    def draw(self, window):
        self.slider_music.draw(window)
        self.slider_sfx.draw(window)
        self.button_resume.draw(window)

    def gest_eventi(self, event):
        changed_music = self.slider_music.handle_event(event)
        changed_sfx = self.slider_sfx.handle_event(event)

        if changed_music or changed_sfx:
            self.update_volumes()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_resume.is_clicked(event.pos):
                return "resume_settings"

        return None


class SFX:
    pickup = None
    place = None
    spawn = None
    complete = None
    unlock = None

    @classmethod
    def init(cls):
        cls.pickup = pygame.mixer.Sound("Audio/pickup.wav")
        cls.place = pygame.mixer.Sound("Audio/place.wav")
        cls.spawn = pygame.mixer.Sound("Audio/spawn.wav")
        cls.complete = pygame.mixer.Sound("Audio/complete.wav")
        cls.unlock = pygame.mixer.Sound("Audio/unlock2.wav")
        cls.spawn.set_volume(0.6)
        cls.pickup.set_volume(0.7)
        cls.place.set_volume(0.7)
        cls.complete.set_volume(0.7)
        cls.unlock.set_volume(0.7)
