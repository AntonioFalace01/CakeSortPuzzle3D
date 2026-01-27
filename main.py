import  pygame
from game_panel import Game
from menu_start import MenuStart, MenuPause
from particelle import GestoreParticelle
from button import Button
from cake_sort_engine import generate_three_options, GameState, Piece, Plate
from menu_start import MenuStart


pygame.init()
pygame.display.set_caption("Cake Sort Puzzle")
fps = 60
#pygame.display.set_icon(pygame.image.load("Sprites/icon.png")) #da metter l'icona che vogliamo
window = pygame.display.set_mode((700, 500))
try:
    img_menu_start = pygame.image.load("Sprites/Background/menu_start.png")
    sfondo_menu_start = pygame.transform.scale(img_menu_start, (700, 500))
    img_game_panel = pygame.image.load("Sprites/Background/game_panel.png")
    sfondo_game_panel = pygame.transform.scale(img_game_panel, (700, 500))
    img_menu_pause = pygame.image.load("Sprites/Background/menu_pausa.png")
    sfondo_menu_pause = pygame.transform.scale(img_menu_pause, (700, 500))
except FileNotFoundError:
    #se manca uno dei file immagine stampa errore e usa sfondo vuoto
    print("ERRORE: Manca sprites/menu.png")

def main(window):
    clock = pygame.time.Clock()

    run = True
    stato = "menu_start"
    menu_start = MenuStart()
    game_panel= Game()
    menu_pause = MenuPause()
    particelle = GestoreParticelle(60, 700, 500)
    while run:
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if stato == "menu_start":
                    nuovo_stato = menu_start.gest_eventi(mouse_pos)
                    if nuovo_stato == "game":
                        stato = "game"
                    elif nuovo_stato == "quit_game":
                        run = False
                        break
                elif stato == "game":
                    nuovo_stato = game_panel.gest_eventi(mouse_pos)
                    if nuovo_stato == "pause_game":
                        stato = "pause_game"
                elif stato == "pause_game":
                    nuovo_stato = menu_pause.gest_eventi(mouse_pos)
                    if nuovo_stato == "resume_game":
                        stato = "game"
                    elif nuovo_stato == "quit_game":
                        run = False
                        break





        if stato == "menu_start":
            window.blit(sfondo_menu_start,(0,0))
            particelle.update_and_draw(window)
            menu_start.draw(window)

        elif stato== "game":
            window.blit (sfondo_game_panel,(0,0))
            game_panel.draw(window)

        elif stato == "pause_game":
            window.blit(sfondo_menu_pause,(0,0))
            menu_pause.draw(window)
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
'''

