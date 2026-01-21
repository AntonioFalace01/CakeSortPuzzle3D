import pygame

class Button:
    def __init__(self,x,y,width, height):
        self.rect = pygame.Rect(x,y,width,height)
        self.color = (0, 128, 255)
        self.text= ""

    def draw(self, window):
        pygame.draw.rect(window, self.color, self.rect)