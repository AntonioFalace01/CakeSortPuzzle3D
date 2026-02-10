import pygame
from cake_sort_engine import generate_three_options, GameState
from plate_sprite import PlateSprite
from button import Button
from table import Table
from assets import Assets


class Game:
    def __init__(self):
        x_pos_button = 620
        w_button = 50
        h_button = 50
        self.tavolo = Table(
            210,
            100,
            righe=5,
            colonne=4,
            larg_cella=60,
            alt_cella=60,
            padding=12
        )

        self.button_pause = Button(x_pos_button, 20, w_button, h_button,
                                   "Sprites/Button/button_pause.png")
        # Stato logico del gioco
        self.state = GameState(rows=5, cols=4)

        # Area opzioni
        self.options_area = (40, 120)
        self.options_spacing = 80
        self.cell_size = (58, 58)

        self.current_options = []
        self.sprites = []
        self.drag_sprite = None

        self.generate_options()

    def generate_options(self):
        self.current_options = generate_three_options()
        self.sprites = []
        x0, y0 = self.options_area
        y = y0

        for opt in self.current_options:
            for plate in opt["plates"]:
                sp = PlateSprite(plate, x0, y, cell_size=self.cell_size)
                self.sprites.append(sp)
                y += self.options_spacing

    def draw(self, window):
        # 1. Disegna Tavolo
        self.tavolo.draw(window)
        self.button_pause.draw(window)

        # 2. Disegna gli sprite (le opzioni trascinabili)
        for sp in self.sprites:
            sp.draw(window)

        # 3. Disegna i piatti PIAZZATI sulla griglia
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                plate = self.state.grid[r][c]
                if plate is not None:
                    # Calcola centro cella
                    cx_cell = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
                    cy_cell = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
                    center_x = cx_cell + self.tavolo.larg_cella // 2
                    center_y = cy_cell + self.tavolo.alt_cella // 2

                    plate_size = min(self.tavolo.larg_cella, self.tavolo.alt_cella)

                    # Usa la classe Assets per disegnare
                    Assets.draw_plate(window, plate, center_x, center_y, plate_size=plate_size)

    def _cell_topleft(self, r, c):
        cx = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
        cy = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
        return (cx, cy)

    def gest_eventi(self, posizione_mouse, event=None):
        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"

        if not event:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Drag inverso per prendere quello più in alto
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
                cell = self.tavolo.get_cell_at(posizione_mouse)
                if cell:
                    r, c = cell
                    # Se la cella è libera
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

                # Se tutti sono piazzati, rigenera
                if all(sp.placed for sp in self.sprites):
                    self.generate_options()

        return None
