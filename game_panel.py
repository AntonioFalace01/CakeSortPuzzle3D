import pygame
from cake_sort_engine import generate_three_options ,GameState
from plate_sprite import PlateSprite
from button import Button
from cake_sort_engine import GameState, generate_three_options
from table import Table

class Game:
    def __init__(self):
        x_pos_button = 620
        w_button = 50
        h_button = 50
        self.tavolo = Table(210, 100)
        self.button_pause = Button(x_pos_button, 20, w_button, h_button,
                                   "Sprites/Button/button_pause.png")
        # Stato logico del gioco (motore)
        self.state = GameState(rows=5, cols=4)

        # Area dove compaiono i piatti generati
        self.options_area = (40, 120)
        self.options_spacing = 80
        self.cell_size = (60, 60)

        # Opzioni correnti (dal motore) e sprite grafici
        self.current_options = []
        self.sprites = []
        self.drag_sprite = None

        self.generate_options()

    def generate_options(self):
        self.current_options = generate_three_options()
        self.sprites = []
        x0, y0 = self.options_area
        y = y0
        # Creiamo uno sprite per OGNI plate di OGNI opzione
        for opt in self.current_options:
            for plate in opt["plates"]:
                sp = PlateSprite(plate, x0, y, image_path="Sprites/piatto.png", cell_size=self.cell_size)
                self.sprites.append(sp)
                y += self.options_spacing

    def draw(self, window):
        self.tavolo.draw(window)
        self.button_pause.draw(window)
        for sp in self.sprites:
            sp.draw(window)
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                plate = self.state.grid[r][c]
                if plate is not None:
                    cx = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
                    cy = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
                    # puoi riusare la stessa immagine: PlateSprite richiede un’istanza, quindi usa una Surface di servizio
                    window.blit(pygame.transform.scale(
                        pygame.image.load("Sprites/piatto.png").convert_alpha(),
                        self.cell_size
                    ), (cx, cy))

    def _cell_topleft(self, r, c):
        cx = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
        cy = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
        return (cx, cy)

    def gest_eventi(self, posizione_mouse, event=None):
        # pausa
        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"

        if not event:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            # avvia drag sul primo sprite “top-most” cliccato
            for sp in reversed(self.sprites):
                sp.start_drag(posizione_mouse)
                if sp.dragging:
                    self.drag_sprite = sp
                    break

        elif event.type == pygame.MOUSEMOTION:
            if self.drag_sprite:
                self.drag_sprite.update_drag(posizione_mouse)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.drag_sprite:
                # tenta aggancio a cella tabella
                cell = self.tavolo.get_cell_at(posizione_mouse)
                if cell:
                    r, c = cell
                    if self.state.grid[r][c] is None:
                        block = {"plates": [self.drag_sprite.plate], "orientation": "NONE"}
                        ok = self.state.place_block(block, r, c)
                        if ok:
                            self.drag_sprite.snap_to_cell_topleft(self._cell_topleft(r, c))
                        else:
                            self.drag_sprite.reset_to_start()
                    else:
                        self.drag_sprite.reset_to_start()
                else:
                    self.drag_sprite.reset_to_start()

                self.drag_sprite.stop_drag()
                self.drag_sprite = None

                # se tutti gli sprite sono placed, rigenera nuove opzioni
                if all(sp.placed for sp in self.sprites):
                    self.generate_options()

        return None
