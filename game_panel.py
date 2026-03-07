import pygame
from cake_sort_engine import GameState, generate_three_options_active
from plate_sprite import PlateSprite
from button import Button
from score_bar import ScoreBar
from slice_animation import MovingSlice
from table import Table
from assets import Assets, UnlockManager
from sound_manager import SFX
import os
from ai.asp_solver import CakeSortASPSolver



class Game:
    def __init__(self):
        x_pos_button = 620
        w_button = 50
        h_button = 50

        self.tavolo = Table(
            210, 100,
            righe=5,
            colonne=4,
            larg_cella=60,
            alt_cella=60,
            padding=12
        )

        self.button_pause = Button(x_pos_button, 20, w_button, h_button,
                                   "Sprites/Button/button_pause.png")

        self.state = GameState(rows=5, cols=4)

        self.unlock = UnlockManager()
        self.score_bar = ScoreBar(x=250, y=40, width=200, height=100, image_path="Sprites/barra.png")

        next_thr = self.unlock.get_next_threshold()
        if next_thr is None:
            next_thr = 1
        self.score_bar.set_progress(self.unlock.total_score, next_thr)

        self.options_area = (40, 120)
        self.options_spacing = 90
        self.block_h_spacing = 60
        self.cell_size = (58, 58)

        # layout pannello opzioni
        self.options_count = 3
        self.options_panel_pad = 14

        self.last_time = pygame.time.get_ticks()

        self.current_options = []
        self.sprites = []

        self.drag_sprite = None
        self.drag_group = None
        self._group_offsets = None

        self.slice_animations = []

        self.generate_options()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ai_solver = CakeSortASPSolver(BASE_DIR)
        # stato animazione IA
        self.ai_pending = None  # (opt_index, start_r, start_c, coords)
        self.ai_animating = False
        self.ai_anim_sprites = []
        self.ai_anim_duration = 0.35

    def apply_ai_move(self, opt_index, start_r, start_c):
        opt = self.current_options[opt_index]

        prev_score = self.state.score
        ok = self.state.place_block(opt, start_r, start_c)
        if ok:
            self._spawn_slice_animations_from_events()
            self._handle_score_unlocks(prev_score, self.state.score)

            # nascondi sprite dell'opzione usata (se vuoi)
            for sp in self.sprites:
                if sp.opt_index == opt_index:
                    sp.visible = False
                    sp.placed = True

            # se tutte le opzioni usate, rigenera
            if all(sp.placed for sp in self.sprites):
                self.generate_options()


    def _start_ai_drag(self, opt_index, start_r, start_c):
        # trova sprite di quell'opzione (solo non piazzati)
        group = [s for s in self.sprites if s.opt_index == opt_index and s.visible and not s.placed]

        # fallback: se per qualche motivo non sono marcati "visible/placed" correttamente,
        # prova a recuperarli comunque per opt_index
        if not group:
            group = [s for s in self.sprites if s.opt_index == opt_index]

        if not group:
            print("IA: sprites non trovati per opzione", opt_index, "| rigenero sprite da current_options")
            # Ricostruisce solo gli sprite, NON cambia current_options
            self._rebuild_sprites_from_current_options()
            group = [s for s in self.sprites if s.opt_index == opt_index and not s.placed]

        if not group:
            print("IA: ancora sprites non trovati per opzione", opt_index)
            return False

        opt = self.current_options[opt_index]

        # calcola celle occupate dal blocco, riusando la tua funzione
        # per coerenza: scegliamo dragged_plate_index=0 (ancora)
        _, _, coords = self._block_cells_for_drop(opt, start_r, start_c, dragged_plate_index=0)

        # avvia movimento verso ogni cella
        for s in group:
            rr, cc = coords[s.plate_index]
            target = self._cell_topleft(rr, cc)
            s.start_ai_move_to(target, duration=self.ai_anim_duration)

        self.ai_pending = (opt_index, start_r, start_c, coords)
        self.ai_animating = True
        self.ai_anim_sprites = group
        return True

    def _finish_ai_drop(self):
        if not self.ai_pending:
            return

        opt_index, start_r, start_c, coords = self.ai_pending
        opt = self.current_options[opt_index]

        prev_score = self.state.score

        before_score = self.state.score
        placed_desc = " | ".join("".join(f"{p.tipo}{p.count}" for p in pl.pieces) for pl in opt["plates"])
        print("\n================ AI MOVE ================")
        print(f"IA: piazzo BLOCCO [{placed_desc}] orient={opt['orientation']} start=({start_r},{start_c})")
        print("SCORE prima:", before_score)

        ok = self.state.place_block(opt, start_r, start_c)

        after_score = self.state.score
        print("OK:", ok, "| SCORE dopo:", after_score, "| delta:", after_score - before_score)
        print("=========================================\n")

        if ok:
            self._spawn_slice_animations_from_events()
            self._handle_score_unlocks(prev_score, self.state.score)
            SFX.place.play()

            # marca sprite come piazzati e allineali esattamente
            for s in self.ai_anim_sprites:
                rr, cc = coords[s.plate_index]
                s.snap_to_cell_topleft(self._cell_topleft(rr, cc))
                s.placed_cell = (rr, cc)
                s.placed = True

        else:
            # se per qualche motivo non è piazzabile, reset
            for s in self.ai_anim_sprites:
                s.reset_to_start()
        self._consume_option(opt_index)

        # pulizia
        self.ai_pending = None
        self.ai_animating = False
        self.ai_anim_sprites = []


    def _rebuild_sprites_from_current_options(self):
        # ricrea gli sprite esattamente come in generate_options, ma senza rigenerare le options
        self.sprites = []

        x0, y0 = self.options_area
        y = y0

        for opt_index, opt in enumerate(self.current_options):
            plates = opt["plates"]
            orient = opt["orientation"]

            if orient == "H" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x0, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x0 + self.block_h_spacing, y, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1
                self.sprites.extend([sp0, sp1])
                y += self.options_spacing

            elif orient == "V" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x0, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x0, y + 62, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1
                self.sprites.extend([sp0, sp1])
                y += self.options_spacing

            else:
                sp = PlateSprite(plates[0], x0, y, cell_size=self.cell_size)
                sp.opt_index = opt_index
                sp.plate_index = 0
                self.sprites.append(sp)
                y += self.options_spacing

    def _consume_option(self, opt_index):
        # 1) rimuovi sprite di quella opzione
        self.sprites = [s for s in self.sprites if s.opt_index != opt_index]

        # 2) rimuovi l'opzione dall'elenco logico
        self.current_options.pop(opt_index)

        # 3) aggiungi una nuova opzione random (1 singola o double) come fai nel generator
        #    Qui riuso generate_three_options_active ma tu hai funzioni già pronte:
        #    - generate_single_option_active / generate_double_option_active
        #    nel cake_sort_engine.py
        from cake_sort_engine import generate_single_option_active, generate_double_option_active
        import random

        if random.random() < 0.25:
            new_opt = generate_double_option_active(self.unlock.active_types)
        else:
            new_opt = generate_single_option_active(self.unlock.active_types)

        self.current_options.append(new_opt)

        # 4) IMPORTANTISSIMO: riallinea gli opt_index degli sprite e ricostruisci pannello
        self._rebuild_sprites_from_current_options()

    def generate_options(self):
        self.current_options = generate_three_options_active(self.unlock.active_types)
        self.sprites = []

        x0, y0 = self.options_area
        y = y0

        for opt_index, opt in enumerate(self.current_options):
            plates = opt["plates"]
            orient = opt["orientation"]

            if orient == "H" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x0, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x0 + self.block_h_spacing, y, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1
                self.sprites.extend([sp0, sp1])
                y += self.options_spacing

            elif orient == "V" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x0, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x0, y + 62, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1
                self.sprites.extend([sp0, sp1])
                y += self.options_spacing

            else:
                sp = PlateSprite(plates[0], x0, y, cell_size=self.cell_size)
                sp.opt_index = opt_index
                sp.plate_index = 0
                self.sprites.append(sp)
                y += self.options_spacing


    def _spawn_slice_animations_from_events(self):
        self.slice_animations = []
        for ev in self.state.last_animation_events:
            tipo = ev["tipo"]
            count = ev["count"]
            (r0, c0) = ev["from"]
            (r1, c1) = ev["to"]

            sx, sy = self._cell_center(r0, c0)
            ex, ey = self._cell_center(r1, c1)

            anim = MovingSlice(
                tipo, (sx, sy), (ex, ey),
                duration=0.50,
                count=count,
                plate_size=self.tavolo.larg_cella
            )
            self.slice_animations.append(anim)


    def _options_panel_rect(self):
        x0, y0 = self.options_area

        h = (self.options_count - 1) * self.options_spacing + self.cell_size[1]


        panel_w = 85

        rect = pygame.Rect(x0, y0, panel_w, h)
        rect = rect.inflate(self.options_panel_pad * 2, self.options_panel_pad * 2)
        return rect

    def _has_any_move(self):
        for opt in self.current_options:
            for r in range(self.state.rows):
                for c in range(self.state.cols):
                    if self.state.can_place_block(opt, r, c):
                        return True
        return False

    def _draw_options_panel(self, window):
        #Pannello tavolino sotto gli sprite opzione (sinistra).
        rect = self._options_panel_rect()

        shadow = rect.move(5, 5)
        pygame.draw.rect(window, (70, 45, 25), shadow, border_radius=16)

        pygame.draw.rect(window, (155, 115, 75), rect, border_radius=16)

        pygame.draw.rect(window, (215, 175, 125), rect, width=3, border_radius=16)

        inner = rect.inflate(-10, -10)
        pygame.draw.rect(window, (175, 135, 95), inner, width=2, border_radius=14)

    def draw(self, window):
        now = pygame.time.get_ticks()
        dt = (now - self.last_time) / 1000.0
        # aggiorna eventuale auto-drag IA
        if self.ai_animating and self.ai_anim_sprites:
            finished_all = True
            for s in self.ai_anim_sprites:
                done = s.update_ai_move(dt)
                if not done:
                    finished_all = False
            if finished_all:
                self._finish_ai_drop()

        self.last_time = now

        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None and (r, c) not in self.state.plates_to_remove:
                    sp.visible = False

        self.tavolo.draw(window)
        self.button_pause.draw(window)
        self._draw_options_panel(window)

        for sp in self.sprites:
            sp.draw(window,dt)

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

        alive_anims = []
        for anim in self.slice_animations:
            anim.update(dt)
            if anim.alive:
                alive_anims.append(anim)

        if self.slice_animations and not alive_anims:
            self.state.finalize_removals()

        self.slice_animations = alive_anims

        for anim in self.slice_animations:
            anim.draw(window)

        # score bar
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
            unlocked = self.unlock.add_score(delta)
            next_thr = self.unlock.get_next_threshold()
            if next_thr is None:
                next_thr = 1
            self.score_bar.set_progress(self.unlock.total_score, next_thr)
            if unlocked:
                self.generate_options()

        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None:
                    sp.visible = False

    def _block_cells_for_drop(self, opt, drop_r, drop_c, dragged_plate_index):
        orient = opt["orientation"]
        plates = opt["plates"]

        start_r, start_c = drop_r, drop_c

        if orient == "H" and len(plates) == 2:
            if dragged_plate_index == 1:
                start_c = drop_c - 1
            coords = [(start_r, start_c), (start_r, start_c + 1)]
            return start_r, start_c, coords

        if orient == "V" and len(plates) == 2:
            if dragged_plate_index == 1:
                start_r = drop_r - 1
            coords = [(start_r, start_c), (start_r + 1, start_c)]
            return start_r, start_c, coords

        coords = [(start_r, start_c)]
        return start_r, start_c, coords

    def gest_eventi(self, posizione_mouse, event=None):
        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"

        if event and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                if self.ai_animating:
                    return None  # evita spam mentre anima

                move = self.ai_solver.choose_move(self.state, self.current_options, debug=False)
                if move is None:
                    print("IA: nessuna mossa trovata")
                    return None

                oi, r, c = move
                started = self._start_ai_drag(oi, r, c)
                if not started:
                    print("IA: impossibile avviare animazione per mossa", move)
                return None


        if not event:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            for sp in reversed(self.sprites):
                sp.start_drag(posizione_mouse)
                if sp.dragging:
                    self.drag_sprite = sp
                    self.drag_group = [s for s in self.sprites if s.opt_index == sp.opt_index and not s.placed]

                    ax, ay = sp.rect.topleft
                    self._group_offsets = []
                    for s in self.drag_group:
                        sx, sy = s.rect.topleft
                        self._group_offsets.append((s, sx - ax, sy - ay))
                    break

        elif event.type == pygame.MOUSEMOTION:
            if self.drag_sprite and self._group_offsets:
                self.drag_sprite.update_drag(posizione_mouse)
                ax, ay = self.drag_sprite.rect.topleft
                for s, ox, oy in self._group_offsets:
                    if s is self.drag_sprite:
                        continue
                    s.rect.topleft = (ax + ox, ay + oy)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.drag_sprite:
                cell = self.tavolo.get_cell_at(posizione_mouse)

                if cell:
                    drop_r, drop_c = cell
                    opt = self.current_options[self.drag_sprite.opt_index]

                    start_r, start_c, coords = self._block_cells_for_drop(
                        opt, drop_r, drop_c, self.drag_sprite.plate_index
                    )

                    prev_score = self.state.score

                    before = self.state.snapshot_grid_deep()
                    before_score = self.state.score
                    placed_desc = " | ".join("".join(f"{p.tipo}{p.count}" for p in pl.pieces) for pl in opt["plates"])
                    print("\n===================================================")
                    print(f"MOSSA: piazzo BLOCCO [{placed_desc}] orient={opt['orientation']} start=({start_r},{start_c})")
                    print("SCORE prima:", before_score)

                    ok = self.state.place_block(opt, start_r, start_c)

                    after = self.state.snapshot_grid_deep()
                    after_score = self.state.score
                    print("OK:", ok, " | SCORE dopo:", after_score, " | delta:", after_score - before_score)
                    self.state.print_grid_compact("GRID DOPO (stato logico)")
                    self.state.print_diff(before, after, "DIFF prima -> dopo")
                    print("===================================================\n")

                    if ok:
                        self._spawn_slice_animations_from_events()
                        self._handle_score_unlocks(prev_score, self.state.score)
                        SFX.place.play()

                        for s in self.drag_group:
                            rr, cc = coords[s.plate_index]
                            s.snap_to_cell_topleft(self._cell_topleft(rr, cc))
                            s.placed_cell = (rr, cc)

                    else:
                        for s in self.drag_group:
                            s.reset_to_start()

                else:
                    for s in (self.drag_group or [self.drag_sprite]):
                        s.reset_to_start()

                for s in (self.drag_group or [self.drag_sprite]):
                    s.stop_drag()

                self.drag_sprite = None
                self.drag_group = None
                self._group_offsets = None

                if all(sp.placed for sp in self.sprites):
                    self.generate_options()
                if not self._has_any_move():
                    return "game_over"

        return None
