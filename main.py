import  pygame
from button import Button
from cake_sort_engine import generate_three_options, GameState, Piece, Plate
from menu_start import MenuStart

'''
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
'''


if __name__ == "__main__":
    game = GameState(5, 4)

    options = generate_three_options()

    while True:
        game.print_grid()

        # se finite, rigenera
        if not options:
            options = generate_three_options()

        print("Opzioni disponibili:")
        for i, opt in enumerate(options):
            if len(opt["plates"]) == 1:
                print(f"{i}) Singolo: {opt['plates'][0]}")
            else:
                print(f"{i}) Blocco {opt['orientation']}:")
                for p in opt["plates"]:
                    print("   ", p)

        choice = int(input(f"Scegli opzione (0-{len(options)-1}): "))
        r = int(input("Riga: "))
        c = int(input("Colonna: "))

        selected = options[choice]

        if game.place_block(selected, r, c):
            options.pop(choice)
        else:
            print("Mossa non valida!\n")


