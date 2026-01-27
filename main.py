import  pygame
from game_panel import Game
from menu_start import MenuStart, MenuPause
from particelle import GestoreParticelle

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
from cake_sort_engine import GameState, Plate, Piece
import random

TYPES = ["C","S","V"]

def generate_random_plate():
    n = random.randint(1,3)
    pieces = []
    for _ in range(n):
        tipo = random.choice(TYPES)
        found = False
        for p in pieces:
            if p.tipo == tipo:
                p.count += 1
                found = True
        if not found:
            pieces.append(Piece(tipo,1))
    return Plate(pieces)

def generate_block():
    plates = [generate_random_plate()]
    if random.random() < 0.5:
        plates.append(generate_random_plate())
    orientation = random.choice(["H","V"]) if len(plates) > 1 else "NONE"

    return {"plates": plates, "orientation": orientation}

def main():
    rows, cols = 4,4
    game = GameState(rows, cols)
    print("Benvenuto al Cake Sort Puzzle (terminal edition)!\n")
    game.print_grid()

    while True:
        block = generate_block()
        block_len = len(block["plates"])
        orientation = block["orientation"]

        print(f"Blocco orientamento: {orientation}")
        for idx, plate in enumerate(block["plates"]):
            s = " + ".join([f"{p.tipo}{p.count}" for p in plate.pieces])
            print(f"Piatto {idx}: {s}")

        moves = game.valid_moves(block_length=block_len, orientation=orientation)
        if not moves:
            print("Nessuna mossa valida! Game over.")
            break

        print("\nMosse possibili:")
        for idx, (r,c) in enumerate(moves):
            print(f"{idx}: ({r},{c})")

        while True:
            try:
                choice = int(input(f"Scegli la cella iniziale per piazzare il blocco [0-{len(moves)-1}]: "))
                if 0 <= choice < len(moves):
                    r,c = moves[choice]
                    if game.place_block(block, r, c):
                        break
            except ValueError:
                pass
            print("Scelta non valida, riprova.")

        game.print_grid()

        if game.is_win():
            print("Hai completato tutte le torte! 🎉")
            break

if __name__ == "__main__":
    main()
'''