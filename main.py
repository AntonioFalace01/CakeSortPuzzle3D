import  pygame
from button import Button
from menu_start import MenuStart

pygame.init()
pygame.display.set_caption("Cake Sort Puzzle")
#pygame.display.set_icon(pygame.image.load("Sprites/icon.png")) #da metter l'icona che vogliamo
window = pygame.display.set_mode((700, 500))
img_menu_start = pygame.image.load("Sprites/menu_start.png")
sfondo_menu_start = pygame.transform.scale(img_menu_start, (700, 500))

def main(window):
    run = True
    stato = "menu_start"
    menu_start = MenuStart()
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        if stato == "menu_start":
            window.blit(sfondo_menu_start,(0,0))
            menu_start.draw(window)
        pygame.display.update()

    pygame.quit()
    quit()



#condizione molto importante, serve per accertarsi di richiamare esattamente la funzione main, del file con nome main.
if __name__ == "__main__":
    main(window)