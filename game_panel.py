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
        x_pos_button = 830
        w_button = 70
        h_button = 70

        self.tavolo = Table(
            280, 170,
            righe=5,
            colonne=4,
            larg_cella=75,
            alt_cella=75,
            padding=12
        )

        self.button_pause = Button(x_pos_button, 20, w_button, h_button,
                                   "Sprites/Button/button_pause.png")

        self.state = GameState(rows=5, cols=4)

        self.unlock = UnlockManager()
        self.score_bar = ScoreBar(x=315, y=65, width=260, height=170, image_path="Sprites/barra.png")

        next_thr = self.unlock.get_next_threshold()
        if next_thr is None:
            next_thr = 1
        self.score_bar.set_progress(self.unlock.total_score, next_thr)

        # distanza tra opzione i e opzione i+1 (verticale)
        self.options_row_step = 170

        # distanza tra i 2 piatti di un doppio H e doppio V
        self.block_h_spacing = 75
        self.block_v_spacing = 75

        self.options_area = (40, 120)

        self.last_time = pygame.time.get_ticks()

        self.current_options = []
        self.sprites = []
        self.used_options = set()
        self.cell_size = (75, 75)

        self.drag_sprite = None
        self.drag_group = None
        self._group_offsets = None

        # ---------------------------------------------------------------
        # Coda animazioni: ogni elemento è un dict con:
        #   "anim"         -> oggetto MovingSlice
        #   "grid_before"  -> snapshot griglia DA mostrare DURANTE l'animazione
        #   "grid_after"   -> snapshot griglia DA applicare DOPO l'animazione
        # ---------------------------------------------------------------
        self.slice_queue = []    # coda di step ancora da fare
        self.active_slice = None  # step corrente in riproduzione

        # Griglia "visiva" separata da quella logica:
        # viene aggiornata un passo alla volta seguendo le animazioni.
        self.display_grid = None  # None = usa self.state.grid direttamente
        self._pending_grid_after = None
        self._completed_cake_delay = None   # secondi trascorsi nel delay torta, None = inattivo
        self.COMPLETED_CAKE_DELAY = 0.5    # durata pausa visiva torta completa

        self.generate_options()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ai_solver = CakeSortASPSolver(BASE_DIR)

        self.ai_pending = None
        self.ai_animating = False
        self.ai_anim_sprites = []
        self.ai_anim_duration = 0.75
        self.ai_game_over = False
        # Autoplay
        self.autoplay = False
        self.autoplay_delay = 1.0        # secondi tra una mossa e l'altra
        self.autoplay_timer = 0.0

        self.button_autoplay = Button(x_pos_button, 100, w_button, h_button,
                                      "Sprites/Button/button_quit.png")


    def _mark_option_used(self, opt_index):
        self.used_options.add(opt_index)
        for sp in self.sprites:
            if sp.opt_index == opt_index:
                sp.visible = False  # sparisce dalla colonna opzioni

    def _all_options_used(self):
        for oi in range(len(self.current_options)):
            if oi not in self.used_options:
                return False
        return True

    def _get_available_options(self):
        available = []
        for oi, opt in enumerate(self.current_options):
            if oi not in self.used_options:
                available.append((oi, opt))
        return available

    def _do_ai_move(self):
        """Esegue una singola mossa IA. Ritorna True se è partita, False se impossibile."""
        if self.ai_animating:
            return False

        available = self._get_available_options()
        if not available:
            if self._all_options_used():
                self.generate_options()
                available = self._get_available_options()
            if not available:
                return False

        available_opts = [opt for (oi, opt) in available]
        available_indices = [oi for (oi, opt) in available]

        move = self.ai_solver.choose_move(self.state, available_opts, debug=False)
        if move is None:
            return False

        solver_oi, r, c = move
        if solver_oi >= len(available_indices):
            return False

        real_oi = available_indices[solver_oi]
        started = self._start_ai_drag(real_oi, r, c)
        return started


    def _start_ai_drag(self, opt_index, start_r, start_c):
        group = [s for s in self.sprites if s.opt_index == opt_index and s.visible]

        if not group:
            self._rebuild_sprites_from_current_options()
            group = [s for s in self.sprites if s.opt_index == opt_index and s.visible]

        if not group:
            print("IA: sprites non trovati per opzione", opt_index)
            return False

        opt = self.current_options[opt_index]
        _, _, coords = self._block_cells_for_drop(opt, start_r, start_c, dragged_plate_index=0)

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
        placed_desc = " | ".join(
            "".join(f"{p.tipo}{p.count}" for p in pl.pieces) for pl in opt["plates"]
        )
        print("\n================ AI MOVE ================")
        print(f"IA: piazzo BLOCCO [{placed_desc}] orient={opt['orientation']} start=({start_r},{start_c})")
        print("SCORE prima:", before_score)

        ok = self.state.place_block(opt, start_r, start_c)

        after_score = self.state.score
        print("OK:", ok, "| SCORE dopo:", after_score, "| delta:", after_score - before_score)
        print("=========================================\n")

        if ok:
            self._spawn_slice_animations_from_snapshots()
            self._handle_score_unlocks(prev_score, self.state.score)
            SFX.place.play()

            for s in self.ai_anim_sprites:
                rr, cc = coords[s.plate_index]
                s.snap_to_cell_topleft(self._cell_topleft(rr, cc))
                s.placed_cell = (rr, cc)
                s.placed = True

            self._mark_option_used(opt_index)

            if self._all_options_used():
                self.generate_options()

        else:
            for s in self.ai_anim_sprites:
                s.reset_to_start()

        self.ai_pending = None
        self.ai_animating = False
        self.ai_anim_sprites = []

        if not self._has_any_move():
            self.ai_game_over = True

    def _rebuild_sprites_from_current_options(self):
        self.sprites = []
        x, y = self.options_area

        for opt_index, opt in enumerate(self.current_options):
            plates = opt["plates"]
            orient = opt["orientation"]

            if orient == "H" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x + self.block_h_spacing, y, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1

                if opt_index in self.used_options:
                    sp0.visible = False
                    sp1.visible = False

                self.sprites.extend([sp0, sp1])
                y += self.options_row_step

            elif orient == "V" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x, y + self.block_v_spacing, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1

                if opt_index in self.used_options:
                    sp0.visible = False
                    sp1.visible = False

                self.sprites.extend([sp0, sp1])
                y += self.options_row_step

            else:
                sp = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp.opt_index = opt_index
                sp.plate_index = 0

                if opt_index in self.used_options:
                    sp.visible = False

                self.sprites.append(sp)
                y += self.options_row_step

    def generate_options(self):
        self.current_options = generate_three_options_active(self.unlock.active_types)
        self.used_options = set()
        self.sprites = []

        x, y = self.options_area

        for opt_index, opt in enumerate(self.current_options):
            plates = opt["plates"]
            orient = opt["orientation"]

            if orient == "H" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x + self.block_h_spacing, y, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1
                self.sprites.extend([sp0, sp1])
                y += self.options_row_step

            elif orient == "V" and len(plates) == 2:
                sp0 = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp1 = PlateSprite(plates[1], x, y + self.block_v_spacing, cell_size=self.cell_size)
                sp0.opt_index = opt_index
                sp1.opt_index = opt_index
                sp0.plate_index = 0
                sp1.plate_index = 1
                self.sprites.extend([sp0, sp1])
                y += self.options_row_step

            else:
                sp = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp.opt_index = opt_index
                sp.plate_index = 0
                self.sprites.append(sp)
                y += self.options_row_step

    # ------------------------------------------------------------------
    # ANIMAZIONI SLICE — versione con snapshot intermedi
    # ------------------------------------------------------------------

    def _spawn_slice_animations_from_snapshots(self):
        """
        Costruisce la coda di animazioni dagli snapshot prodotti da GameState.
        Ogni step della coda:
          - anim:         oggetto MovingSlice
          - grid_during:  snapshot da mostrare DURANTE il volo
                          (source già svuotato, target non ancora aggiornato)
          - grid_after:   snapshot da applicare DOPO la fine dell'animazione
                          (target aggiornato, torta completa ancora visibile)
        """
        self.slice_queue = []

        for snap in self.state.animation_snapshots:
            ev = snap["event"]
            tipo = ev["tipo"]
            count = ev["count"]
            r0, c0 = ev["from"]
            r1, c1 = ev["to"]

            sx, sy = self._cell_center(r0, c0)
            ex, ey = self._cell_center(r1, c1)

            anim = MovingSlice(
                tipo, (sx, sy), (ex, ey),
                duration=0.75,
                count=count,
                plate_size=self.tavolo.larg_cella
            )

            self.slice_queue.append({
                "anim":         anim,
                "grid_during":  snap["grid_during"],
                "grid_after":   snap["grid_after"],
            })

        if self.slice_queue:
            step = self.slice_queue.pop(0)
            self.active_slice = step["anim"]
            self.display_grid = step["grid_during"]
            self._pending_grid_after = step["grid_after"]
        else:
            self.active_slice = None
            self.display_grid = None
            self._pending_grid_after = None

        # Timer per il delay della torta completata (None = nessuna torta da aspettare)
        self._completed_cake_delay = None

    def _advance_slice_queue(self):
        """
        Chiamato quando l'animazione corrente finisce.
        Applica grid_after (target aggiornato), poi:
          - se la torta è appena stata completata → attiva un delay visivo
            prima di passare al prossimo step
          - altrimenti → parte subito il prossimo step (o finalize se è l'ultimo)
        """
        # Applica lo stato "dopo" dell'animazione appena conclusa
        if self._pending_grid_after is not None:
            self.display_grid = self._pending_grid_after
            self._pending_grid_after = None

        # Controlla se in questo grid_after c'è una torta appena completata
        # (cella ancora presente in display_grid ma in plates_to_remove)
        has_completed = any(
            self.display_grid is not None
            and self.display_grid[r][c] is not None
            for r, c in self.state.plates_to_remove
        ) if self.display_grid is not None else False

        if has_completed and not self.slice_queue:
            # Ultima animazione + torta completa: aspetta un po' prima di rimuovere
            self._completed_cake_delay = 0.0  # avvia timer
            self.active_slice = None
        else:
            self._start_next_slice_or_finalize()

    def _start_next_slice_or_finalize(self):
        if self.slice_queue:
            step = self.slice_queue.pop(0)
            self.active_slice = step["anim"]
            self.display_grid = step["grid_during"]
            self._pending_grid_after = step["grid_after"]
        else:
            self.active_slice = None
            self.display_grid = None
            self._pending_grid_after = None
            self.state.finalize_removals()

    # ------------------------------------------------------------------
    # HELPERS LAYOUT
    # ------------------------------------------------------------------

    def _has_any_move(self):
        for oi, opt in enumerate(self.current_options):
            if oi in self.used_options:
                continue
            for r in range(self.state.rows):
                for c in range(self.state.cols):
                    if self.state.can_place_block(opt, r, c):
                        return True
        return False

    def _draw_double_links_in_options(self, window):
        """
        Rettangolino bianco tra i 2 piatti di un'opzione doppia (H/V),
        SOLO nell'area opzioni (sinistra). Non viene disegnato in griglia.
        """
        link_color = (255, 255, 255)

        thickness = 15   # spessore del rettangolino
        inset = 10       # quanto entra dentro i piatti

        # raggruppa sprite visibili per opt_index
        by_opt = {}
        for sp in self.sprites:
            if not sp.visible:
                continue
            if sp.opt_index is None:
                continue
            if sp.opt_index in self.used_options:
                continue
            by_opt.setdefault(sp.opt_index, []).append(sp)

        for opt_index, group in by_opt.items():
            if len(group) != 2:
                continue

            opt = self.current_options[opt_index]
            orient = opt["orientation"]
            if orient not in ("H", "V"):
                continue

            # ordina per plate_index: 0 e 1
            group.sort(key=lambda s: s.plate_index)
            a, b = group[0], group[1]
            ra, rb = a.rect, b.rect

            if orient == "H":
                x1 = ra.right - inset
                x2 = rb.left + inset
                if x2 <= x1:
                    continue
                cy = (ra.centery + rb.centery) // 2
                rect = pygame.Rect(x1, cy - thickness // 2, x2 - x1, thickness)

            else:  # orient == "V"
                y1 = ra.bottom - inset
                y2 = rb.top + inset
                if y2 <= y1:
                    continue
                cx = (ra.centerx + rb.centerx) // 2
                rect = pygame.Rect(cx - thickness // 2, y1, thickness, y2 - y1)

            pygame.draw.rect(window, link_color, rect)

    def draw(self, window):
        now = pygame.time.get_ticks()
        dt = (now - self.last_time) / 1000.0

        # Aggiorna animazione AI sprite
        if self.ai_animating and self.ai_anim_sprites:
            finished_all = True
            for s in self.ai_anim_sprites:
                done = s.update_ai_move(dt)
                if not done:
                    finished_all = False
            if finished_all:
                self._finish_ai_drop()
        # ---- AUTOPLAY ----
        if self.autoplay and not self.ai_animating and self.active_slice is None and self._completed_cake_delay is None:
            self.autoplay_timer += dt
            if self.autoplay_timer >= self.autoplay_delay:
                self.autoplay_timer = 0.0
                moved = self._do_ai_move()
                if not moved:
                    self.autoplay = False  # nessuna mossa possibile, disattiva


        self.last_time = now

        # Nascondi sprite piazzati se la cella logica è vuota
        for sp in self.sprites:
            if sp.placed and sp.placed_cell:
                r, c = sp.placed_cell
                if self.state.grid[r][c] is None and (r, c) not in self.state.plates_to_remove:
                    sp.visible = False

        self.tavolo.draw(window)
        self.button_pause.draw(window)
        self.button_autoplay.draw(window)


        for sp in self.sprites:
            sp.draw(window, dt)
            self._draw_double_links_in_options(window)

        # ---------------------------------------------------------------
        # Rendering griglia: usa display_grid (snapshot intermedio) se
        # un'animazione è in corso, altrimenti usa la griglia logica reale.
        # ---------------------------------------------------------------
        grid_to_render = self.display_grid if self.display_grid is not None else self.state.grid

        for r in range(self.state.rows):
            for c in range(self.state.cols):
                plate = grid_to_render[r][c]
                if plate is not None:
                    cx_cell = self.tavolo.x + self.tavolo.padding + c * self.tavolo.larg_cella
                    cy_cell = self.tavolo.y + self.tavolo.padding + r * self.tavolo.alt_cella
                    center_x = cx_cell + self.tavolo.larg_cella // 2
                    center_y = cy_cell + self.tavolo.alt_cella // 2
                    plate_size = min(self.tavolo.larg_cella, self.tavolo.alt_cella)
                    Assets.draw_plate(window, plate, center_x, center_y, plate_size=plate_size)

        # ---------------------------------------------------------------
        # Animazione slice attiva: riproduce una alla volta.
        # Quando finisce, avanza alla prossima (che aggiorna display_grid).
        # ---------------------------------------------------------------
        if self.active_slice:
            self.active_slice.update(dt)
            self.active_slice.draw(window)
            if not self.active_slice.alive:
                self._advance_slice_queue()
        elif self._completed_cake_delay is not None:
            # Pausa visiva: la torta completa è visibile, aspettiamo prima di rimuoverla
            self._completed_cake_delay += dt
            if self._completed_cake_delay >= self.COMPLETED_CAKE_DELAY:
                self._completed_cake_delay = None
                self._start_next_slice_or_finalize()

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


    # ------------------------------------------------------------------
    # EVENTI
    # ------------------------------------------------------------------

    def gest_eventi(self, posizione_mouse, event=None):
        if self.ai_game_over:
            self.ai_game_over = False
            return "game_over"

        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"
        if self.button_autoplay.is_clicked(posizione_mouse):
            self.autoplay = not self.autoplay
            self.autoplay_timer = 0.0
            return None

        if event and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                if self.ai_animating:
                    return None

                available = self._get_available_options()
                if not available:
                    print("IA: tutte le opzioni gia usate")
                    return None

                available_opts = [opt for (oi, opt) in available]
                available_indices = [oi for (oi, opt) in available]

                move = self.ai_solver.choose_move(
                    self.state, available_opts, debug=False
                )
                if move is None:
                    print("IA: nessuna mossa trovata")
                    return None

                solver_oi, r, c = move
                if solver_oi >= len(available_indices):
                    print("IA: indice solver fuori range")
                    return None

                real_oi = available_indices[solver_oi]

                started = self._start_ai_drag(real_oi, r, c)
                if not started:
                    print("IA: impossibile avviare animazione per mossa", move)
                return None

        if not event:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            for sp in reversed(self.sprites):
                # FIX: non controllare sp.placed qui, perché un'opzione "usata"
                # viene gestita con used_options + visible=False
                if not sp.visible:
                    continue
                if sp.opt_index in self.used_options:
                    continue

                sp.start_drag(posizione_mouse)
                if sp.dragging:
                    self.drag_sprite = sp
                    self.drag_group = [s for s in self.sprites
                                       if s.opt_index == sp.opt_index
                                       and s.visible
                                       and (s.opt_index not in self.used_options)]

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
                    placed_desc = " | ".join(
                        "".join(f"{p.tipo}{p.count}" for p in pl.pieces) for pl in opt["plates"]
                    )
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
                        self._spawn_slice_animations_from_snapshots()
                        self._handle_score_unlocks(prev_score, self.state.score)
                        SFX.place.play()

                        # snap in griglia e marca come piazzati (questo è "placed" vero)
                        for s in self.drag_group:
                            rr, cc = coords[s.plate_index]
                            s.snap_to_cell_topleft(self._cell_topleft(rr, cc))
                            s.placed_cell = (rr, cc)
                            s.placed = True

                        self._mark_option_used(self.drag_sprite.opt_index)

                        if self._all_options_used():
                            self.generate_options()

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

                if not self._has_any_move():
                    return "game_over"

        return None
