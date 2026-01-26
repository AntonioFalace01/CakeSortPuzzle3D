import pygame
from table import Table
from button import Button


class MenuStart:
    def __init__(self):
        x_pos_button = 250
        w_button = 190
        h_button = 90
        self.table = Table(100,100)
        self.button_start= Button(x_pos_button,220, w_button, h_button,"Sprites/button_start.png")
        self.button_quit= Button(x_pos_button,280, w_button, h_button,"Sprites/button_start.png")

    def draw(self, window):
        #self.table.draw(window)
        self.button_start.draw(window)
        self.button_quit.draw(window)

    def gest_eventi(self, posizione_mouse):
        if self.button_start.is_clicked(posizione_mouse):
            return "game"
        if self.button_quit.is_clicked(posizione_mouse):
            return "quit_game"
        return None

class MenuPause(MenuStart):
    def __init__(self):
        super().__init__()


    def gest_eventi(self, posizione_mouse):
        if self.button_start.is_clicked(posizione_mouse):
            return "resume_game"
        if self.button_quit.is_clicked(posizione_mouse):
            return "quit_game"
        return None


