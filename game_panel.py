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

        # LOGICA
        self.state = GameState(rows=5, cols=4)

        # STATO VISUALE (ciò che viene disegnato)
        self.visual_grid_current = [[None for _ in range(self.state.cols)] for _ in range(self.state.rows)]
        self.visual_grid_next = [[None for _ in range(self.state.cols)] for _ in range(self.state.rows)]
        self._sync_visual_with_logical_initial()

        # Unlock + barra
        self.unlock = UnlockManager()
        self.score_bar = ScoreBar(x=250, y=40, width=200, height=100, image_path="Sprites/barra.png")
        next_thr = self.unlock.get_next_threshold() or 1
        self.score_bar.set_progress(self.unlock.total_score, next_thr)

        self.options_area = (40, 120)
        self.options_spacing = 80
        self.cell_size = (58, 58)

        self.current_options = []
        self.sprites = []
        self.drag_sprite = None

        # Animazioni
        self.slice_animations = []
        self.animating = False   # quando True, stiamo giocando una transizione visuale

        # tempo per dt
        self.last_time = pygame.time.get_ticks()

        self.generate_options()

    # ------------------ INIT VISUALE ------------------

    def _sync_visual_with_logical_initial(self):
        """Solo all'inizio: visual = logico (tutto vuoto)."""
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                self.visual_grid_current[r][c] = self.state.grid[r][c]
                self.visual_grid_next[r][c] = self.state.grid[r][c]

    # ------------------ OPZIONI ------------------

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

    # ------------------ COORDINATE CELLE ------------------

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

    # ------------------ SCORE / UNLOCK ------------------

    def _handle_score_unlocks(self, prev_score, new_score):
        delta = max(0, new_score - prev_score)
        if delta > 0:
            unlocked = self.unlock.add_score(delta)
            next_thr = self.unlock.get_next_threshold() or 1
            self.score_bar.set_progress(self.unlock.total_score, next_thr)
            if unlocked:
                self.generate_options()
        # pulizia sprite opzioni
        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None:
                    sp.visible = False

    # ------------------ ANIMAZIONI ------------------

    def _prepare_visual_transition(self, before_grid):
        """
        Costruisce visual_grid_next a partire dal before_grid e dagli eventi di animazione:
        - visual_grid_current = before_grid (stato pre-merge, piatti completi ancora visibili)
        - visual_grid_next = stato logico finale self.state.grid
        L'animazione verrà disegnata mentre visual_grid_current è mostrata;
        al termine, si passerà a visual_grid_next (dove i piatti completati sono spariti).
        """
        # 1) visual corrente diventa lo snapshot 'before_grid'
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                self.visual_grid_current[r][c] = before_grid[r][c]

        # 2) visual_next parte dallo stato logico finale
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                self.visual_grid_next[r][c] = self.state.grid[r][c]

        # 3) crea animazioni in base agli eventi
        self.slice_animations = []
        for ev in self.state.last_animation_events:
            tipo = ev["tipo"]
            count = ev["count"]
            (r0, c0) = ev["from"]
            (r1, c1) = ev["to"]

            sx, sy = self._cell_center(r0, c0)
            ex, ey = self._cell_center(r1, c1)

            anim = MovingSlice(
                tipo,
                (sx, sy),
                (ex, ey),
                duration=0.45,        # velocità animazione
                count=count,
                plate_size=self.tavolo.larg_cella
            )
            self.slice_animations.append(anim)

        self.animating = bool(self.slice_animations)

    # ------------------ DRAW ------------------

    def draw(self, window):
        now = pygame.time.get_ticks()
        dt = (now - self.last_time) / 1000.0
        self.last_time = now

        # sprite opzioni: nascondi se la cella logica è vuota
        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None:
                    sp.visible = False

        self.tavolo.draw(window)
        self.button_pause.draw(window)

        for sp in self.sprites:
            sp.draw(window)

        # Disegna piatti usando SEMPRE la griglia VISUALE CORRENTE
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                plate = self.visual_grid_current[r][c]
                if plate is not None:
                    cx_cell = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
                    cy_cell = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
                    center_x = cx_cell + self.tavolo.larg_cella // 2
                    center_y = cy_cell + self.tavolo.alt_cella // 2
                    plate_size = min(self.tavolo.larg_cella, self.tavolo.alt_cella)
                    Assets.draw_plate(window, plate, center_x, center_y, plate_size=plate_size)

        # aggiorna animazioni
        if self.animating:
            alive = []
            for anim in self.slice_animations:
                anim.update(dt)
                if anim.alive:
                    alive.append(anim)
            self.slice_animations = alive

            # disegna animazioni sopra
            for anim in self.slice_animations:
                anim.draw(window)

            # se non ci sono più animazioni → passa allo stato visuale "next"
            if not self.slice_animations:
                # copia visual_next in visual_current (piatti completati spariscono ora)
                for r in range(self.state.rows):
                    for c in range(self.state.cols):
                        self.visual_grid_current[r][c] = self.visual_grid_next[r][c]
                self.animating = False

        # barra punteggio
        self.score_bar.update(dt)
        label = "Prossima torta" if self.unlock.get_next_threshold() is not None else "Tutte sbloccate"
        self.score_bar.draw(window, label=label)

    # ------------------ EVENTI ------------------

    def gest_eventi(self, posizione_mouse, event=None):
        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"

        if not event:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            # se stiamo animando, non permettiamo di trascinare altre cose
            if self.animating:
                return None

            for sp in reversed(self.sprites):
                sp.start_drag(posizione_mouse)
                if sp.dragging:
                    self.drag_sprite = sp
                    break

        elif event.type == pygame.MOUSEMOTION:
            if self.drag_sprite:
                self.drag_sprite.update_drag(posizione_mouse)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.drag_sprite and not self.animating:
                cell = self.tavolo.get_cell_at(posizione_mouse)
                if cell:
                    r, c = cell
                    if self.state.grid[r][c] is None:
                        block = {"plates": [self.drag_sprite.plate], "orientation": "NONE"}
                        prev_score = self.state.score

                        # snapshot PRIMA del merge (per lo stato visuale corrente)
                        before_grid = [
                            [self.state.grid[rr][cc] for cc in range(self.state.cols)]
                            for rr in range(self.state.rows)
                        ]

                        ok = self.state.place_block(block, r, c)
                        new_score = self.state.score

                        if ok:
                            # prepara transizione visuale (visual_current = before, visual_next = after, animazioni)
                            self._prepare_visual_transition(before_grid)

                        # sblocchi e barra
                        self._handle_score_unlocks(prev_score, new_score)

                        if ok:
                            SFX.place.play()
                            self.drag_sprite.snap_to_cell_topleft(self._cell_topleft(r, c))
                            self.drag_sprite.placed_cell = (r, c)
                        else:
                            self.drag_sprite.reset_to_start()
                    else:
                        self.drag_sprite.reset_to_start()
                else:
                    self.drag_sprite.reset_to_start()

                self.drag_sprite.stop_drag()
                self.drag_sprite = None

                if all(sp.placed for sp in self.sprites):
                    self.generate_options()

        return None
