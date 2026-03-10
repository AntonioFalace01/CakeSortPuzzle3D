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

        # ----------------------------
        # OPTIONS PANEL LAYOUT (FIXED)
        # ----------------------------
        self.options_area = (40, 120)          # top-left del pannello
        self.options_count = 3
        self.cell_size = (75, 75)
        self.options_panel_extend_top = 80  # px, quanto vuoi allungare verso l'alto

        # distanza tra opzione i e opzione i+1 (verticale)
        self.options_row_step = 170

        # distanza tra i 2 piatti di un doppio H e doppio V
        self.block_h_spacing = 85
        self.block_v_spacing = 95

        # padding interno del pannello
        self.options_panel_pad = 25

        self.last_time = pygame.time.get_ticks()

        self.current_options = []
        self.sprites = []
        self.used_options = set()

        self.drag_sprite = None
        self.drag_group = None
        self._group_offsets = None

        self.slice_animations = []

        self.generate_options()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ai_solver = CakeSortASPSolver(BASE_DIR)

        self.ai_pending = None
        self.ai_animating = False
        self.ai_anim_sprites = []
        self.ai_anim_duration = 0.75
        self.ai_game_over = False

    def _mark_option_used(self, opt_index):
        self.used_options.add(opt_index)
        for sp in self.sprites:
            if sp.opt_index == opt_index:
                sp.placed = True

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

    def _start_ai_drag(self, opt_index, start_r, start_c):
        group = [s for s in self.sprites if s.opt_index == opt_index and s.visible and not s.placed]

        if not group:
            group = [s for s in self.sprites if s.opt_index == opt_index]

        if not group:
            self._rebuild_sprites_from_current_options()
            group = [s for s in self.sprites if s.opt_index == opt_index and not s.placed]

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
            self._spawn_slice_animations_from_events()
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
        x0, y0 = self.options_area
        pad = self.options_panel_pad
        x = x0 + pad
        y = y0 + pad

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
                    sp0.placed = True
                    sp0.visible = False
                    sp1.placed = True
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
                    sp0.placed = True
                    sp0.visible = False
                    sp1.placed = True
                    sp1.visible = False
                self.sprites.extend([sp0, sp1])
                y += self.options_row_step

            else:
                sp = PlateSprite(plates[0], x, y, cell_size=self.cell_size)
                sp.opt_index = opt_index
                sp.plate_index = 0
                if opt_index in self.used_options:
                    sp.placed = True
                    sp.visible = False
                self.sprites.append(sp)
                y += self.options_row_step

    def generate_options(self):
        self.current_options = generate_three_options_active(self.unlock.active_types)
        self.used_options = set()
        self.sprites = []

        x0, y0 = self.options_area
        pad = self.options_panel_pad
        x = x0 + pad
        y = y0 + pad

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
                duration=0.75,
                count=count,
                plate_size=self.tavolo.larg_cella
            )
            self.slice_animations.append(anim)

    def _options_panel_rect(self):
        x0, y0 = self.options_area
        pad = self.options_panel_pad

        # larghezza: contenere un doppio H
        panel_w = pad * 2 + (self.cell_size[0] + self.block_h_spacing)

        # altezza: deve contenere anche un doppio V su una riga
        row_h_single = self.cell_size[1]
        row_h_double_v = self.block_v_spacing + self.cell_size[1]
        row_h = max(row_h_single, row_h_double_v)

        panel_h = pad * 2 + (self.options_count - 1) * self.options_row_step + row_h

        rect = pygame.Rect(x0, y0, panel_w, panel_h)

        # estendi SOLO verso l'alto
        extra = self.options_panel_extend_top
        rect.y -= extra
        rect.h += extra

        return rect

    def _has_any_move(self):
        for oi, opt in enumerate(self.current_options):
            if oi in self.used_options:
                continue
            for r in range(self.state.rows):
                for c in range(self.state.cols):
                    if self.state.can_place_block(opt, r, c):
                        return True
        return False

    def _draw_options_panel(self, window):
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
            sp.draw(window, dt)

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
        if self.ai_game_over:
            self.ai_game_over = False
            return "game_over"

        if event and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_pause.is_clicked(posizione_mouse):
                return "pause_game"

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

                move = self.ai_solver.choose_move(self.state, available_opts, debug=False)
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
                if sp.placed or not sp.visible:
                    continue
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
                    ok = self.state.place_block(opt, start_r, start_c)

                    if ok:
                        self._spawn_slice_animations_from_events()
                        self._handle_score_unlocks(prev_score, self.state.score)
                        SFX.place.play()

                        for s in self.drag_group:
                            rr, cc = coords[s.plate_index]
                            s.snap_to_cell_topleft(self._cell_topleft(rr, cc))
                            s.placed_cell = (rr, cc)

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
