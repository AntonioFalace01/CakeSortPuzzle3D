import pygame

from button import Button


class Game:
    def __init__(self):
        x_pos_button = 620
        w_button = 50
        h_button = 50
        self.button_pause = Button(x_pos_button, 20, w_button, h_button,
                                   "Sprites/Button/button_pause.png")

    def draw(self, window):
        self.button_pause.draw(window)

    def gest_eventi(self, posizione_mouse):
        if self.button_pause.is_clicked(posizione_mouse):
            return "pause_game"
        return None
