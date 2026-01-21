import pygame
from table import Table



from button import Button


class MenuStart:
    def __init__(self):
        x_pos_button = 300
        w_button = 100
        h_button = 50
        self.table = Table(100,100)
        self.button_start= Button(x_pos_button,300, w_button, h_button,"Start")
        self.button_quit= Button(x_pos_button,370, w_button, h_button,"Quit")

    def draw(self, window):
        self.table.draw(window)
        #self.button_start.draw(window)
        #self.button_quit.draw(window)
