import pygame

pygame.init()
pygame.display.set_mode((700, 500))

from Sprites.assets import draw_plate, draw_plate_only
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

        self.game_state = GameState(5, 4)

        # OPZIONI
        self.options = generate_three_options()
        self.selected_option = None


    def draw(self, window):
        self.tavolo.draw(window)
        self.button_pause.draw(window)

        x_positions = [260, 360, 460]
        y = 440
        for x in x_positions:
            draw_plate_only(window, x, y)

        '''
        # disegna piatti nella griglia
        for r in range(self.game_state.rows):
            for c in range(self.game_state.cols):
                plate = self.game_state.grid[r][c]
                if not plate:
                    continue

                cx = (
                        self.tavolo.x
                        + self.tavolo.padding
                        + c * self.tavolo.larg_cella
                        + self.tavolo.larg_cella // 2
                )
                cy = (
                        self.tavolo.y
                        + self.tavolo.padding
                        + r * self.tavolo.alt_cella
                        + self.tavolo.alt_cella // 2
                )

                draw_plate(window, plate, cx, cy)

        # disegna le 3 opzioni
        self.draw_options(window)
        '''

    def gest_eventi(self, posizione_mouse):
        if self.button_pause.is_clicked(posizione_mouse):
            return "pause_game"
            # 1️⃣ click sulle opzioni
        for i in range(len(self.options)):
            rect = pygame.Rect(230 + i * 100, 410, 80, 80)
            if rect.collidepoint(posizione_mouse):
                self.selected_option = i
                return None

            # 2️⃣ click sulla griglia
        if self.selected_option is not None:
            cell = self.tavolo.get_cell_at(posizione_mouse)
            if cell:
                r, c = cell
                option = self.options[self.selected_option]

                if self.game_state.place_block(option, r, c):
                    self.options.pop(self.selected_option)
                    self.selected_option = None

                    if not self.options:
                        self.options = generate_three_options()

        return None

    def draw_options(self, window):
        base_y = 440
        xs = [260, 360, 460]

        for i, option in enumerate(self.options):
            x = xs[i]

            if option["orientation"] == "NONE":
                draw_plate(window, option["plates"][0], x, base_y)

            elif option["orientation"] == "H":
                draw_plate(window, option["plates"][0], x - 30, base_y)
                draw_plate(window, option["plates"][1], x + 30, base_y)

            elif option["orientation"] == "V":
                draw_plate(window, option["plates"][0], x, base_y - 30)
                draw_plate(window, option["plates"][1], x, base_y + 30)

