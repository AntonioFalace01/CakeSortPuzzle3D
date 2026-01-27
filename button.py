import pygame


class Button:
    def __init__(self, x, y, larghezza, altezza, image_path=None,
                 use_full_hitbox=False):
        self.rect_disegno = pygame.Rect(x, y, larghezza, altezza)
        altezza_click = altezza * 0.51
        offset_y = (altezza - altezza_click) // 2.2
        larghezza_click = larghezza * 0.70
        offset_x = (larghezza - larghezza_click) // 2
        self.rect = pygame.Rect(x + offset_x, y + offset_y,larghezza_click, altezza_click)
        self.image_normal = None
        self.image_hover = None
        self.rect_hover_disegno = None

        self.use_full_hitbox = use_full_hitbox
       # self.border_color = (255, 0, 0)
       # self.border_width = 2
        if image_path:
            try:
                # Carica l'immagine e scala a larghezza e altezza desiderate
                raw_image = pygame.image.load(image_path).convert_alpha()
                self.image_normal = pygame.transform.scale(raw_image, (larghezza,altezza))

                # Crea l'immagine hover leggermente più piccola
                w_hover =larghezza * 0.95
                h_hover = altezza * 0.95
                self.image_hover = pygame.transform.scale(raw_image, (w_hover, h_hover))

                # Rettangolo per centrare l'immagine hover dentro quella normale
                self.rect_hover_disegno = self.image_hover.get_rect(center=self.rect_disegno.center)

            except pygame.error:
                #se file non valido o mancante stampa errore e usa fallback senza immagine
                print(f"ERRORE: Immagine bottone non trovata: {image_path}")
                self.image_normal = None

    def _is_hovered(self, mouse_pos):
        # Se vogliamo usare l'intera immagine come hitbox:
        if self.use_full_hitbox:
            return self.rect_disegno.collidepoint(mouse_pos)
        return self.rect.collidepoint(mouse_pos)

    def draw(self, window):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self._is_hovered(mouse_pos)

        if self.image_normal:
            if is_hovered and self.image_hover:
                #disegna immagine hover
                window.blit(self.image_hover, self.rect_hover_disegno)
            else:
                #disegna immagine normale
                window.blit(self.image_normal, self.rect_disegno)
        click_rect = self.rect_disegno if self.use_full_hitbox else self.rect
        #pygame.draw.rect(window, self.border_color, click_rect, self.border_width, border_radius=10)


    def is_clicked(self, posizione_mouse):
        # Se vogliamo cliccare tutta l'immagine usa rect_disegno, altrimenti usa click_rect
        if self.use_full_hitbox:
            return self.rect_disegno.collidepoint(posizione_mouse)
        return self.rect.collidepoint(posizione_mouse)

