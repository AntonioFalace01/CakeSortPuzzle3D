import pygame
from table import Table
from button import Button


class MenuStart:
    def __init__(self):
        x_pos_button = 250
        w_button = 190
        h_button = 90
        self.table = Table(100,100)
        self.button_start= Button(x_pos_button, 210, w_button, h_button, "Sprites/Button/button_start.png")
        self.button_quit= Button(x_pos_button, 270, w_button, h_button, "Sprites/Button/button_quit.png")
        self.button_settings = Button(x_pos_button, 330, w_button, h_button, "Sprites/Button/button_settings.png")

    def draw(self, window):
        #self.table.draw(window)
        self.button_start.draw(window)
        self.button_quit.draw(window)
        self.button_settings.draw(window)

    def gest_eventi(self, posizione_mouse):
        if self.button_start.is_clicked(posizione_mouse):
            return "game"
        if self.button_quit.is_clicked(posizione_mouse):
            return "quit_game"
        return None

class MenuPause(MenuStart):
    def __init__(self):
        super().__init__()
        x_pos_button = 250
        w_button = 190
        h_button = 90
        self.button_resume = Button(x_pos_button, 130, w_button, h_button, "Sprites/Button/button_start.png")
        self.button_quit = Button(x_pos_button, 190, w_button, h_button, "Sprites/Button/button_quit.png")
        self.button_settings = Button(x_pos_button, 250, w_button, h_button, "Sprites/Button/button_settings.png")

    def draw(self, window):
        # self.table.draw(window)
        self.button_resume.draw(window)
        self.button_quit.draw(window)
        self.button_settings.draw(window)

    def gest_eventi(self, posizione_mouse):
        if self.button_resume.is_clicked(posizione_mouse):
            return "resume_game"
        if self.button_quit.is_clicked(posizione_mouse):
            return "quit_game"
        return None


