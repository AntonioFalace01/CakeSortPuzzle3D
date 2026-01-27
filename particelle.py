import pygame
import random

#particelle sullo sfondo del menu principale
class ParticellaMagica:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.reset()

    def reset(self):
        # Parte da una posizione casuale
        self.x = random.randint(0, self.w)
        self.y = random.randint(0, self.h)

        #sale piano piano verso l'alto
        self.vel_x = random.uniform(-0.2, 0.2)
        self.vel_y = random.uniform(-0.5, -0.1)

        # Dimensione variabile
        self.raggio_base = random.randint(1, 3)
        self.timer = random.uniform(0, 100)  # Per l'effetto pulsazione
        # Colori: Azzurro chiaro, Bianco, Viola chiaro
        colori_possibili = [
            (100, 200, 255),  # Azzurro
            (200, 200, 255),  # Bianco/Viola
            (50, 100, 255)  # Blu elettrico
        ]
        self.colore = random.choice(colori_possibili)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.timer += 0.1

        # Se esce dallo schermo in alto, ricompare sotto
        if self.y < 0:
            self.y = self.h
            self.x = random.randint(0, self.w)

    def draw(self, window):
        # Effetto pulsazione (il raggio cambia leggermente nel tempo)
        import math
        pulsazione = math.sin(self.timer) * 0.5
        raggio_attuale = max(0, self.raggio_base + pulsazione)

        # per farla sembrare luminosa disegniamo un alone trasparente
        pygame.draw.circle(window, self.colore, (int(self.x), int(self.y)), int(raggio_attuale))


class GestoreParticelle:
    def __init__(self, quantita, width, height):
        self.particelle = []
        for _ in range(quantita): # uso il tratto basso per evitare di usare l'indice
            self.particelle.append(ParticellaMagica(width, height))

    def update_and_draw(self, window):
        for p in self.particelle:
            p.update()
            p.draw(window)
