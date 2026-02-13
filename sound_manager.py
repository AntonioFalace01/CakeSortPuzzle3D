import pygame
from button import Button


class VolumeSlider:
    def __init__(self, x, y, w, h, initial_value=0.5, bg_path="Sprites/barra.png", knob_path="Sprites/lollipop.png", label="Volume"):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = initial_value  # Valore float da 0.0 a 1.0
        self.label = label
        self.dragging = False
        self.font = pygame.font.SysFont("Arial", 22, bold=True)

        # Carica sfondo barra
        self.bg = None
        try:
            raw_bg = pygame.image.load(bg_path).convert_alpha()
            self.bg = pygame.transform.smoothscale(raw_bg, (w, h))
        except:
            self.bg = None

        # Carica pomello (lollipop)
        self.knob_img = None
        self.knob_w = self.knob_h = 0
        try:
            raw_knob = pygame.image.load(knob_path).convert_alpha()
            # scala il lollipop: height ~ 70-85% dell’area interna
            # puoi regolare questo fattore
            target_h = int(h * 4)
            scale_ratio = target_h / raw_knob.get_height()
            target_w = int(raw_knob.get_width() * scale_ratio)
            self.knob_img = pygame.transform.smoothscale(raw_knob, (target_w, target_h))
            self.knob_w, self.knob_h = self.knob_img.get_size()
        except:
            pass

        # Definisci l’area interna della barra dove scorre il riempimento e il pomello
        # Padding per restare dentro la cavità rosa della tua immagine
        pad_x = int(w * 0.10)
        pad_y = int(h * 0.30)
        inner_w = w - 2 * pad_x
        inner_h = h - 2 * pad_y
        self.inner_rect = pygame.Rect(x + pad_x, y + pad_y, inner_w, inner_h)

        # Area effettiva del “binario” dentro l’inner, più bassa e centrata
        track_margin_y = int(self.inner_rect.height * 0.18)
        self.track_rect = pygame.Rect(
            self.inner_rect.x,
            self.inner_rect.y + track_margin_y,
            self.inner_rect.width,
            self.inner_rect.height - 2 * track_margin_y
        )

        # Stile riempimento (opzionale)
        self.fill_color = (255, 160, 220)  # rosa
        self.fill_back = (255, 210, 240)  # pista chiara
        self.radius = self.track_rect.height // 2

        # Hitbox facilitata
        self.hit_rect = self.rect.inflate(12, 12)


    def draw(self, window):
        # Etichetta
        text_str = f"{self.label}: {int(self.value * 100)}%"
        text_surf = self.font.render(text_str, True, (255, 255, 255))
        window.blit(text_surf, (self.rect.x, self.rect.y - 30))

        # Sfondo barra
        if self.bg:
            window.blit(self.bg, self.rect)
        else:
            pygame.draw.rect(window, (240, 180, 210), self.rect, border_radius=20)

        # Pista chiara dentro la cavità
        pygame.draw.rect(window, self.fill_back, self.track_rect, border_radius=self.radius)

        # Riempimento rosa (facoltativo, commenta se non lo vuoi)
        fill_w = int(self.track_rect.width * self.value)
        fill_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, fill_w, self.track_rect.height)
        prev = window.get_clip()
        window.set_clip(self.track_rect)
        pygame.draw.rect(window, self.fill_color, fill_rect, border_radius=self.radius)
        window.set_clip(prev)

        # Pomello (lollipop) posizionato lungo la track
        knob_cx = self.track_rect.x + fill_w  # posizione X lungo la track
        knob_cy = self.track_rect.centery

        if self.knob_img:
            # centra l’immagine sul punto (knob_cx, knob_cy)
            knob_rect = self.knob_img.get_rect(center=(knob_cx, knob_cy))
            window.blit(self.knob_img, knob_rect)
        else:
            # fallback: pomello circolare
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
        # mappa il mouse alla track orizzontale
        rel = mouse_x - self.track_rect.x
        val = rel / self.track_rect.width
        self.value = max(0.0, min(1.0, val))


class SoundManager:
    def __init__(self):
        # --- SISTEMA AUDIO ---
        # Dizionario per i suoni (SFX)
        self.sounds = {}

        # Qui puoi caricare i tuoi suoni se ne hai (opzionale per ora)
        # try:
        #     self.sounds["pop"] = pygame.mixer.Sound("Audio/pop.wav")
        #     self.sounds["win"] = pygame.mixer.Sound("Audio/win.wav")
        # except:
        #     pass

        # --- INTERFACCIA (UI) ---
        # Slider Musica (Default 40%)
        self.slider_music = VolumeSlider(200, 180, 300, 15, 0.4, "Musica")

        self.button_resume = Button(250, 200, 200, 90, "Sprites/Button/button_resume.png")

        # Applica i volumi iniziali
        self.update_volumes()

    def update_volumes(self):
        # 1. Imposta volume musica globale
        pygame.mixer.music.set_volume(self.slider_music.value)

        # 2. Imposta volume per tutti gli SFX caricati
        for sound in self.sounds.values():
            sound.set_volume(self.slider_sfx.value)

    def play_sfx(self, name):
        """Chiama questa funzione per suonare un effetto"""
        if name in self.sounds:
            # Riapplica il volume corrente per sicurezza
            self.sounds[name].set_volume(self.slider_sfx.value)
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
