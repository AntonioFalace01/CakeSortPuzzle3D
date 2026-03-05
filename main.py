import  pygame

import assets
from game_panel import Game
from menu_start import MenuStart, MenuPause
from particelle import GestoreParticelle
from menu_start import MenuStart
from sound_manager import SoundManager

pygame.init()
pygame.mixer.init()

from sound_manager import SFX

SFX.init()
pygame.mixer.music.load("Audio/bg-audio.mp3")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)
pygame.display.set_caption("Cake Sort Puzzle")
fps = 60
#pygame.display.set_icon(pygame.image.load("Sprites/icon.png"))
window = pygame.display.set_mode((700, 500))
assets.Assets.init()
try:
    img_game_over = pygame.image.load("Sprites/Background/game_over.png")
    sfondo_game_over = pygame.transform.scale(img_game_over, (700, 500))
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
    sound = SoundManager()
    while run:
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if stato == "menu_start":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    nuovo_stato = menu_start.gest_eventi(mouse_pos)
                    if nuovo_stato == "game":
                        stato = "game"
                    elif nuovo_stato == "quit_game":
                        run = False
                        break
                    elif nuovo_stato == "settings":
                        stato= "settings"
                        settings_origin= "menu_start"

            elif stato == "game":
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    mouse_pos = event.pos if event.type != pygame.MOUSEMOTION else pygame.mouse.get_pos()
                    nuovo_stato = game_panel.gest_eventi(mouse_pos, event)
                    if nuovo_stato == "pause_game":
                        stato = "pause_game"
                    elif nuovo_stato == "game_over":
                        stato = "game_over"

            elif stato == "pause_game":
                pygame.mixer.music.pause()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    nuovo_stato = menu_pause.gest_eventi(mouse_pos)
                    if nuovo_stato == "resume_game":
                        pygame.mixer.music.unpause()
                        stato = "game"
                    elif nuovo_stato == "quit_game":
                        run = False
                        break
                    elif nuovo_stato == "settings":
                        stato= "settings"
                        settings_origin = "pause_game"

            elif stato == "settings":
                nuovo_stato = sound.gest_eventi(event)

                if nuovo_stato == "resume_settings":
                    if settings_origin == "menu_start":
                        stato = "menu_start"
                    elif settings_origin == "pause_game":
                        pygame.mixer.music.unpause()
                        stato = "game"
                    else:
                        stato = "menu_start"

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

        elif stato == "settings":
            window.blit(sfondo_menu_pause,(0,0))
            sound.draw(window)

        elif stato == "game_over":
            window.blit(sfondo_game_over, (0, 0))

        pygame.display.update()

    pygame.quit()
    quit()



if __name__ == "__main__":
    main(window)

