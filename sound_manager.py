import pygame
from button import Button


class VolumeSlider:
    def __init__(self, x, y, w, h, initial_value=0.5, label="Volume"):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = initial_value  # Valore float da 0.0 a 1.0
        self.label = label
        self.dragging = False
        self.font = pygame.font.SysFont("Arial", 22, bold=True)

        # Stile Grafico
        self.color_bg = (200, 200, 200)  # Grigio chiaro (sfondo barra)
        self.color_fill = (100, 220, 100)  # Verde acceso (parte piena)
        self.color_knob = (255, 255, 255)  # Bianco (pomello)
        self.color_text = (255, 255, 255)  # Bianco (testo)

    def draw(self, window):
        # 1. Disegna Etichetta (Es. "Musica: 50%")
        text_str = f"{self.label}: {int(self.value * 100)}%"
        text_surf = self.font.render(text_str, True, self.color_text)
        window.blit(text_surf, (self.rect.x, self.rect.y - 30))

        # 2. Barra Sfondo (vuota)
        pygame.draw.rect(window, self.color_bg, self.rect, border_radius=6)

        # 3. Barra Riempimento (piena)
        fill_width = int(self.rect.width * self.value)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(window, self.color_fill, fill_rect, border_radius=6)

        # 4. Pomello (cerchio)
        cx = self.rect.x + fill_width
        cy = self.rect.centery
        radius = self.rect.height // 2 + 5
        pygame.draw.circle(window, self.color_knob, (cx, cy), radius)
        pygame.draw.circle(window, (100, 100, 100), (cx, cy), radius, 2)  # Bordo pomello

    def handle_event(self, event):
        """Gestisce click e trascinamento. Ritorna True se il valore cambia."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_over(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_value(event.pos[0])
                return True

        return False

    def update_value(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        val = relative_x / self.rect.width
        self.value = max(0.0, min(1.0, val))  # Limita tra 0.0 e 1.0

    def is_over(self, pos):
        # Hitbox leggermente più grande per facilitare la presa
        expanded_rect = self.rect.inflate(20, 20)
        return expanded_rect.collidepoint(pos)


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
