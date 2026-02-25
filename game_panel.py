import pygame
from cake_sort_engine import GameState, generate_three_options_active
from plate_sprite import PlateSprite
from button import Button
from score_bar import ScoreBar
from slice_animation import MovingSlice
from table import Table
from assets import Assets, UnlockManager
from sound_manager import SFX


class Game:
    def __init__(self):
        x_pos_button = 620
        w_button = 50
        h_button = 50
        self.tavolo = Table(
            210,
            100,
            righe=5,
            colonne=4,
            larg_cella=60,
            alt_cella=60,
            padding=12
        )
        self.button_pause = Button(x_pos_button, 20, w_button, h_button,
                                   "Sprites/Button/button_pause.png")
        # Stato logico del gioco
        self.state = GameState(rows=5, cols=4)

        # Sistema sblocchi + barra
        self.unlock = UnlockManager()
        self.score_bar = ScoreBar(x=250, y=40, width=200, height=100, image_path="Sprites/barra.png")

        # imposta barra sulla prossima soglia
        next_thr = self.unlock.get_next_threshold()
        if next_thr is None:
            next_thr = 1
        self.score_bar.set_progress(self.unlock.total_score, next_thr)

        self.options_area = (40, 120)
        self.options_spacing = 80
        self.cell_size = (58, 58)
        self.last_time = pygame.time.get_ticks()
        self.current_options = []
        self.sprites = []
        self.drag_sprite = None
        self.slice_animations = []
        self.generate_options()

    def _spawn_slice_animations_from_events(self):
        """
        Legge self.state.last_animation_events e genera
        una MovingSlice per ciascun evento.
        """
        self.slice_animations = []

        for ev in self.state.last_animation_events:
            tipo = ev["tipo"]
            count = ev["count"]
            (r0, c0) = ev["from"]
            (r1, c1) = ev["to"]

            # converte cella (r,c) in coordinate pixel (centro)
            sx, sy = self._cell_center(r0, c0)
            ex, ey = self._cell_center(r1, c1)

            # la durata puoi regolarla a piacere (0.20–0.35 secondi va bene)
            anim = MovingSlice(tipo, (sx, sy), (ex, ey), duration=0.25, count=count, plate_size=self.tavolo.larg_cella)
            self.slice_animations.append(anim)


    def generate_options(self):
        self.current_options = generate_three_options_active(self.unlock.active_types)
        self.sprites = []
        x0, y0 = self.options_area
        y = y0
        for opt in self.current_options:
            for plate in opt["plates"]:
                sp = PlateSprite(plate, x0, y, cell_size=self.cell_size)
                self.sprites.append(sp)
                y += self.options_spacing

    def draw(self, window):
        # calcolo dt (in secondi)
        now = pygame.time.get_ticks()
        dt = (now - self.last_time) / 1000.0
        self.last_time = now

        # Sincronizza: se uno sprite è piazzato su una cella che ora è vuota, nascondilo
        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None and (r, c) not in self.state.plates_to_remove:
                    sp.visible = False

        self.tavolo.draw(window)
        self.button_pause.draw(window)

        # Disegna opzioni (solo quelle visibili)
        for sp in self.sprites:
            sp.draw(window)

        # Piatti piazzati sulla griglia
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                plate = self.state.grid[r][c]
                if plate is not None:
                    cx_cell = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
                    cy_cell = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
                    center_x = cx_cell + self.tavolo.larg_cella // 2
                    center_y = cy_cell + self.tavolo.alt_cella // 2
                    plate_size = min(self.tavolo.larg_cella, self.tavolo.alt_cella)
                    Assets.draw_plate(window, plate, center_x, center_y, plate_size=plate_size)

        # aggiorna animazioni di fette
        # aggiorna animazioni
        alive_anims = []
        for anim in self.slice_animations:
            anim.update(dt)
            if anim.alive:
                alive_anims.append(anim)

        # se tutte finite → rimuovi piatti completati
        if self.slice_animations and not alive_anims:
            self.state.finalize_removals()

        self.slice_animations = alive_anims

        # disegna animazioni sopra i piatti
        for anim in self.slice_animations:
            anim.draw(window)

        # Barra punteggio
        self.score_bar.update(dt)
        label = "Prossima torta" if self.unlock.get_next_threshold() is not None else "Tutte sbloccate"
        self.score_bar.draw(window, label=label)


    def _cell_topleft(self, r, c):
        cx = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
        cy = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
        return (cx, cy)

    def _cell_center(self, r, c):
        cx_cell = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
        cy_cell = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
        center_x = cx_cell + self.tavolo.larg_cella // 2
        center_y = cy_cell + self.tavolo.alt_cella // 2
        return center_x, center_y


    def _handle_score_unlocks(self, prev_score, new_score):
        delta = max(0, new_score - prev_score)
        if delta > 0:
            # aggiorna cumulativo e controlla sblocco
            unlocked = self.unlock.add_score(delta)
            # aggiorna barra
            next_thr = self.unlock.get_next_threshold()
            if next_thr is None:
                next_thr = 1
            self.score_bar.set_progress(self.unlock.total_score, next_thr)
            # se abbiamo sbloccato una nuova torta, rigenera le opzioni con tipi aggiornati
            if unlocked:
                self.generate_options()
                #SFX.unlock.play()

        # Pulizia immediata sprite piazzati le cui celle sono ora vuote
        # (effetto visivo immediato post-merge/completamento)
        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None:
                    sp.visible = False

    def gest_eventi(self, posizione_mouse, event=None):
        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"

        if not event:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            for sp in reversed(self.sprites):
                sp.start_drag(posizione_mouse)
                if sp.dragging:
                    self.drag_sprite = sp
                    break

        elif event.type == pygame.MOUSEMOTION:
            if self.drag_sprite:
                self.drag_sprite.update_drag(posizione_mouse)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.drag_sprite:
                cell = self.tavolo.get_cell_at(posizione_mouse)
                if cell:
                    r, c = cell
                    if self.state.grid[r][c] is None:
                        block = {"plates": [self.drag_sprite.plate], "orientation": "NONE"}
                        # cattura score prima/dopo per calcolare delta
                        prev_score = self.state.score
                        ok = self.state.place_block(block, r, c)
                        new_score = self.state.score
                        if ok:
                            self._spawn_slice_animations_from_events()
                            # gestisci sblocchi in base al delta di score ottenuto
                            self._handle_score_unlocks(prev_score, new_score)

                        if ok:
                            SFX.place.play()
                            self.drag_sprite.snap_to_cell_topleft(self._cell_topleft(r, c))
                            self.drag_sprite.placed_cell = (r, c)  # lega sprite alla cella
                        else:
                            self.drag_sprite.reset_to_start()
                    else:
                        self.drag_sprite.reset_to_start()
                else:
                    self.drag_sprite.reset_to_start()

                self.drag_sprite.stop_drag()
                self.drag_sprite = None

                # Se tutti sono piazzati, rigenera
                if all(sp.placed for sp in self.sprites):
                    self.generate_options()

        return None


