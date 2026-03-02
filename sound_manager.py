import pygame
from button import Button


class VolumeSlider:
    def __init__(self, x, y, w, h, initial_value=0.5, knob_path="Sprites/pomello.png", label="Volume"):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = float(initial_value)
        self.label = label
        self.dragging = False
        self.font = pygame.font.SysFont("Arial", 22, bold=True)

        # --- Pomello ---
        self.knob_img = None
        try:
            raw_knob = pygame.image.load(knob_path).convert_alpha()
            # altezza pomello (regola pure: 2.0–4.0 * h)
            target_h = int(h * 4)
            scale_ratio = target_h / raw_knob.get_height()
            target_w = int(raw_knob.get_width() * scale_ratio)
            self.knob_img = pygame.transform.smoothscale(raw_knob, (target_w, target_h))
        except Exception as e:
            print("Errore caricamento pomello:", e)
            self.knob_img = None

        # --- Track interna (solo disegnata) ---
        pad_x = int(w * 0.05)
        pad_y = int(h * 0.20)
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

        # stile barra disegnata
        self.fill_color = (255, 160, 220)
        self.fill_back = (255, 210, 240)
        self.radius = max(1, self.track_rect.height // 2)

        # hitbox facilitata
        self.hit_rect = self.rect.inflate(12, 12)

    def draw(self, window):
        # Etichetta
        text_str = f"{self.label}: {int(self.value * 100)}%"
        text_surf = self.font.render(text_str, True, (255, 255, 255))
        window.blit(text_surf, (self.rect.x, self.rect.y - 30))

        # Contenitore (facoltativo, puoi anche rimuoverlo se vuoi solo track)
        pygame.draw.rect(window, (240, 180, 210), self.rect, border_radius=20)

        # Track chiara
        pygame.draw.rect(window, self.fill_back, self.track_rect, border_radius=self.radius)

        # Riempimento
        fill_w = int(self.track_rect.width * self.value)
        fill_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, fill_w, self.track_rect.height)
        prev = window.get_clip()
        window.set_clip(self.track_rect)
        pygame.draw.rect(window, self.fill_color, fill_rect, border_radius=self.radius)
        window.set_clip(prev)

        # Pomello
        knob_cx = self.track_rect.x + fill_w
        knob_cy = self.track_rect.centery+5

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
        self.sounds = {}

        # Slider Musica
        self.slider_music = VolumeSlider(
            200, 180, 300, 30,
            initial_value=0.4,
            knob_path="Sprites/pomello.png",
            label="Musica"
        )

        self.button_resume = Button(250, 200, 200, 90, "Sprites/Button/button_resume.png")

        self.update_volumes()

    def update_volumes(self):
        pygame.mixer.music.set_volume(self.slider_music.value)

        # Se in futuro aggiungi slider_sfx, qui imposti anche i suoni.
        for sound in self.sounds.values():
            sound.set_volume(1.0)

    def play_sfx(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def draw(self, window):
        self.slider_music.draw(window)
        self.button_resume.draw(window)

    def gest_eventi(self, event):
        change_music = self.slider_music.handle_event(event)
        if change_music:
            self.update_volumes()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_resume.is_clicked(event.pos):
                return "resume_settings"

        return None


class SFX:
    pickup = None
    place = None

    @classmethod
    def init(cls):
        cls.pickup = pygame.mixer.Sound("Audio/pickup.wav")
        cls.place = pygame.mixer.Sound("Audio/place.wav")
