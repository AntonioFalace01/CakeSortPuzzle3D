import random
from sound_manager import SFX

MAX_SLICES = 6


class Piece:
    def __init__(self, tipo, count=1):
        self.tipo = tipo
        self.count = count

    def __repr__(self):
        return f"{self.tipo}{self.count}"


class Plate:
    def __init__(self, pieces=None):
        self.pieces = pieces or []

    def get_piece(self, tipo):
        for p in self.pieces:
            if p.tipo == tipo:
                return p
        return None

    def add(self, tipo, count):
        if count <= 0:
            return
        p = self.get_piece(tipo)
        if p:
            p.count += count
        else:
            self.pieces.append(Piece(tipo, count))

    def remove(self, tipo, count):
        p = self.get_piece(tipo)
        if not p:
            return 0
        taken = min(count, p.count)
        p.count -= taken
        if p.count == 0:
            self.pieces.remove(p)
        return taken

    def is_empty(self):
        return len(self.pieces) == 0

    def total_slices(self):
        return sum(p.count for p in self.pieces)

    def free_slots(self, max_slices=MAX_SLICES):
        return max(0, max_slices - self.total_slices())

    def is_pure(self):
        return len(self.pieces) == 1

    def is_completed_pure(self, max_slices=MAX_SLICES):
        return (
            self.total_slices() == max_slices
            and len(self.pieces) == 1
            and self.pieces[0].count == max_slices
        )

    def __repr__(self):
        return " + ".join(str(p) for p in self.pieces)


class GameState:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.score = 0
        self.last_animation_events = []
        self.plates_to_remove = []

    # ---------------- DEBUG ----------------

    def snapshot_grid_deep(self):
        snap = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if plate is None:
                    snap[r][c] = None
                else:
                    new_pieces = [Piece(p.tipo, p.count) for p in plate.pieces]
                    snap[r][c] = Plate(new_pieces)
        return snap

    def _cell_str(self, r, c, plate=None):
        if plate is None:
            plate = self.grid[r][c]
        if plate is None:
            return "."
        return "".join(f"{p.tipo}{p.count}" for p in plate.pieces) or "EMPTY"

    def print_grid_compact(self, title="GRID"):
        print(f"\n--- {title} ---")
        for r in range(self.rows):
            print(" | ".join(self._cell_str(r, c).ljust(10) for c in range(self.cols)))
        print("Score:", self.score)
        print("plates_to_remove:", self.plates_to_remove if self.plates_to_remove else [])
        if self.last_animation_events:
            print("events:")
            for e in self.last_animation_events:
                print("   ", e)
        else:
            print("events: []")

    def _connected_component_of_type_from(self, start_r, start_c, tipo):
        """
        Ritorna l'insieme di celle (r,c) connesse 4-dir che contengono 'tipo',
        partendo da start. Se start non contiene tipo -> insieme vuoto.
        """
        if not (0 <= start_r < self.rows and 0 <= start_c < self.cols):
            return set()
        start_plate = self.grid[start_r][start_c]
        if not start_plate or start_plate.get_piece(tipo) is None:
            return set()

        visited = set()
        stack = [(start_r, start_c)]
        visited.add((start_r, start_c))

        while stack:
            r, c = stack.pop()
            for nr, nc in self.neighbors4(r, c):
                if (nr, nc) in visited:
                    continue
                pl = self.grid[nr][nc]
                if pl and pl.get_piece(tipo) is not None and not self._is_marked_to_remove((nr, nc)):
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        return visited


    def grid_to_strings(self, grid_snapshot=None):
        g = grid_snapshot if grid_snapshot is not None else self.grid
        out = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                pl = g[r][c]
                row.append("." if pl is None else ("".join(f"{p.tipo}{p.count}" for p in pl.pieces) or "EMPTY"))
            out.append(row)
        return out

    def print_diff(self, before_snap, after_snap, title="DIFF"):
        b = self.grid_to_strings(before_snap)
        a = self.grid_to_strings(after_snap)
        print(f"\n--- {title} ---")
        any_change = False
        for r in range(self.rows):
            for c in range(self.cols):
                if b[r][c] != a[r][c]:
                    any_change = True
                    print(f"({r},{c}): {b[r][c]}  ->  {a[r][c]}")
        if not any_change:
            print("nessuna differenza")

    # ---------------- CORE HELPERS ----------------

    def _is_marked_to_remove(self, pos):
        return pos in self.plates_to_remove

    def _add_anim_event(self, tipo, count, from_pos, to_pos):
        if from_pos == to_pos or count <= 0:
            return
        self.last_animation_events.append({"tipo": tipo, "count": count, "from": from_pos, "to": to_pos})

    def neighbors4(self, r, c):
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < self.rows and 0 <= cc < self.cols:
                yield rr, cc

    # ---------------- PLACE BLOCK ----------------

    def place_block(self, block, start_r, start_c):
        orientation = block["orientation"]
        plates = block["plates"]

        self.last_animation_events = []
        self.plates_to_remove = []

        if orientation == "H":
            positions = [(start_r, start_c + i) for i in range(len(plates))]
        elif orientation == "V":
            positions = [(start_r + i, start_c) for i in range(len(plates))]
        else:
            positions = [(start_r, start_c)]

        for r, c in positions:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                return False
            if self.grid[r][c] is not None:
                return False

        placed_positions = []
        for (r, c), plate in zip(positions, plates):
            self.grid[r][c] = plate
            placed_positions.append((r, c))

        tipi_coinvolti = {p.tipo for plate in plates for p in plate.pieces}

        # 0a) SPLIT ATOMICO: risolvi coppie misto/misto adiacenti PRIMA di tutto
        for (pr, pc) in placed_positions:
            for nr, nc in self.neighbors4(pr, pc):
                if self._is_marked_to_remove((nr, nc)):
                    continue
                nplate = self.grid[nr][nc]
                if nplate and not nplate.is_pure():
                    plate = self.grid[pr][pc]
                    if plate and not plate.is_pure():
                        self._split_mixed_pair((pr, pc), (nr, nc), placed_positions)  # <-- aggiunto placed_positions

        # 0b) CALAMITA (solo se nuovo piatto è PURO)
        for (pr, pc) in placed_positions:
            self._magnet_new_pure_plate(pr, pc, placed_positions)

        # 1) BRIDGE merge
        for (pr, pc) in placed_positions:
            for tipo in tipi_coinvolti:
                self._merge_bridge_for_type(pr, pc, tipo, placed_positions)

        # 2) Merge a catena standard
        for tipo in tipi_coinvolti:
            self.chain_merge_from_type(tipo, placed_positions)

        self.resolve_groups()
        return True

    # ---------------- MERGE DIRECTION RULE ----------------

    def _pick_target_source(self, pos_a, pos_b, tipo, placed_positions):
        """
        Direzione source->target:
        - se uno è puro appena piazzato => target quello
        - altrimenti se uno è puro => target quello
        - altrimenti (misto/misto): preferisci target = appena piazzato (effetto calamita logico)
        - altrimenti fallback: target = chi ha più count di quel tipo
        """
        ra, ca = pos_a
        rb, cb = pos_b
        a = self.grid[ra][ca]
        b = self.grid[rb][cb]
        if not a or not b:
            return None, None

        pa = a.get_piece(tipo)
        pb = b.get_piece(tipo)
        if not pa or not pb:
            return None, None

        a_pure = a.is_pure()
        b_pure = b.is_pure()
        a_new = pos_a in placed_positions
        b_new = pos_b in placed_positions

        # 1) puro appena piazzato
        if a_pure and a_new and not (b_pure and b_new):
            return pos_a, pos_b
        if b_pure and b_new and not (a_pure and a_new):
            return pos_b, pos_a

        # 2) puro pre-esistente
        if a_pure and not b_pure:
            return pos_a, pos_b
        if b_pure and not a_pure:
            return pos_b, pos_a

        # 3) calamita logica (solo misto/misto)
        if not a_pure and not b_pure:
            if a_new and not b_new:
                return pos_a, pos_b
            if b_new and not a_new:
                return pos_b, pos_a

        # 4) fallback: più count
        if pa.count > pb.count:
            return pos_a, pos_b
        if pb.count > pa.count:
            return pos_b, pos_a

        # tie-break stabile
        if rb > ra or (rb == ra and cb > ca):
            return pos_b, pos_a
        return pos_a, pos_b

    def can_place_block(self, block, start_r, start_c):
        """Controlla SOLO se il blocco entra e le celle sono libere (nessun merge)."""
        orientation = block["orientation"]
        plates = block["plates"]

        if orientation == "H":
            positions = [(start_r, start_c + i) for i in range(len(plates))]
        elif orientation == "V":
            positions = [(start_r + i, start_c) for i in range(len(plates))]
        else:
            positions = [(start_r, start_c)]

        for r, c in positions:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                return False
            if self.grid[r][c] is not None:
                return False
        return True

    def _magnet_new_pure_plate(self, pr, pc, placed_positions):
        """
        Se il piatto appena piazzato è PURO, attrae dai vicini tutte le fette dello stesso tipo.
        Isola i tipi: il vicino perde quel tipo e mantiene gli altri.
        """
        plate = self.grid[pr][pc]
        if not plate:
            return
        if (pr, pc) not in placed_positions:
            return
        if not plate.is_pure():
            return

        tipo = plate.pieces[0].tipo

        changed = True
        while changed:
            changed = False
            for nr, nc in self.neighbors4(pr, pc):
                if self._is_marked_to_remove((nr, nc)):
                    continue
                nplate = self.grid[nr][nc]
                if not nplate or nplate.get_piece(tipo) is None:
                    continue

                moved = self._move_tipo((nr, nc), (pr, pc), tipo)
                if moved > 0:
                    changed = True

    def _move_tipo(self, source_pos, target_pos, tipo):
        """
        Sposta fette 'tipo' da source a target rispettando:
        - cap totale 6 nel target
        - cap tipo 6 nel target
        - NON crea nuovi tipi in un piatto misto già esistente
        """
        sr, sc = source_pos
        tr, tc = target_pos
        source = self.grid[sr][sc]
        target = self.grid[tr][tc]
        if not source or not target:
            return 0

        sp = source.get_piece(tipo)
        tp = target.get_piece(tipo)

        if not sp:
            return 0

        # se target ha già il tipo, va bene
        if tp is None:
            # se target è vuoto, crea il tipo
            if target.is_empty():
                tp = Piece(tipo, 0)
                target.pieces.append(tp)
            else:
                # target ha altri tipi diversi, non possiamo aggiungere
                return 0

        free_total = target.free_slots(MAX_SLICES)
        free_tipo = MAX_SLICES - tp.count
        can_take = min(sp.count, free_total, free_tipo)

        if can_take <= 0:
            return 0

        moved = source.remove(tipo, can_take)
        if moved > 0:
            self._add_anim_event(tipo, moved, (sr, sc), (tr, tc))
            target.add(tipo, moved)

            if source.is_empty():
                self.grid[sr][sc] = None

            if target.is_completed_pure(MAX_SLICES):
                if (tr, tc) not in self.plates_to_remove:
                    self.plates_to_remove.append((tr, tc))
                self.score += 10

        return moved

    def _count_neighbors_with_tipo(self, r, c, tipo, exclude_pos=None):
        """Conta i vicini che hanno 'tipo', escludendo opzionalmente una posizione."""
        count = 0
        for nr, nc in self.neighbors4(r, c):
            if exclude_pos and (nr, nc) == exclude_pos:
                continue
            if self._is_marked_to_remove((nr, nc)):
                continue
            pl = self.grid[nr][nc]
            if pl and pl.get_piece(tipo) is not None:
                count += 1
        return count

    def _split_mixed_pair(self, pos_a, pos_b, placed_positions):
        """
        Gestisce il caso in cui due piatti misti adiacenti condividono gli stessi tipi.

        IMPORTANTE: se uno dei due piatti (quello appena piazzato) ha altri vicini
        con lo stesso tipo oltre all'altro piatto, deve fare da PONTE → non splittiamo
        quel tipo, lo lasciamo per il bridge/chain merge.
        """
        a = self.grid[pos_a[0]][pos_a[1]]
        b = self.grid[pos_b[0]][pos_b[1]]
        if not a or not b:
            return False
        if a.is_pure() or b.is_pure():
            return False

        tipos_a = sorted(p.tipo for p in a.pieces)
        tipos_b = sorted(p.tipo for p in b.pieces)

        shared = sorted(set(tipos_a) & set(tipos_b))
        if not shared:
            return False

        pos_min = min(pos_a, pos_b)
        pos_max = max(pos_a, pos_b)

        any_moved = False
        for idx, tipo in enumerate(shared):
            # Controlla se pos_a è un ponte per questo tipo
            # (ha altri vicini con tipo, oltre a pos_b)
            a_is_bridge = (
                    pos_a in placed_positions and
                    self._count_neighbors_with_tipo(pos_a[0], pos_a[1], tipo, exclude_pos=pos_b) > 0
            )
            # Controlla se pos_b è un ponte per questo tipo
            b_is_bridge = (
                    pos_b in placed_positions and
                    self._count_neighbors_with_tipo(pos_b[0], pos_b[1], tipo, exclude_pos=pos_a) > 0
            )

            # Se uno dei due è un ponte, NON splittiamo questo tipo —
            # sarà il bridge/chain merge a gestirlo
            if a_is_bridge or b_is_bridge:
                continue

            if idx % 2 == 0:
                target, source = pos_min, pos_max
            else:
                target, source = pos_max, pos_min

            moved = self._move_tipo(source, target, tipo)
            if moved > 0:
                any_moved = True

        return any_moved

    def _merge_bridge_for_type(self, br, bc, tipo, placed_positions):
        bridge = self.grid[br][bc]
        if not bridge or bridge.get_piece(tipo) is None:
            return
        if self._is_marked_to_remove((br, bc)):
            return

        neigh = []
        for nr, nc in self.neighbors4(br, bc):
            if self._is_marked_to_remove((nr, nc)):
                continue
            pl = self.grid[nr][nc]
            if pl and pl.get_piece(tipo) is not None:
                neigh.append((nr, nc))

        if not neigh:
            return

        # ---------------- TYPE SPLIT (misto vs misto, singolo vicino) ----------------
        # Questo caso è già gestito da place_block via _split_mixed_pair PRIMA
        # di chiamare _merge_bridge_for_type. Se siamo qui e il vicino è misto,
        # il tipo potrebbe già essere stato spostato — ricontrolliamo lo stato.
        if len(neigh) == 1:
            nr, nc = neigh[0]
            neighbor = self.grid[nr][nc]
            bridge = self.grid[br][bc]  # rileggi dopo eventuali split
            if not bridge or bridge.get_piece(tipo) is None:
                return

            if neighbor and not neighbor.is_pure() and bridge and not bridge.is_pure():
                # già gestito da _split_mixed_pair, non fare nulla
                return

        def piece_count_at(pos):
            r, c = pos
            pl = self.grid[r][c]
            if not pl:
                return 0
            p = pl.get_piece(tipo)
            return p.count if p else 0

        def can_receive(pos):
            r, c = pos
            pl = self.grid[r][c]
            if not pl:
                return False
            tp = pl.get_piece(tipo)
            if not tp:
                return False
            return pl.free_slots(MAX_SLICES) > 0 and (MAX_SLICES - tp.count) > 0

        # ---------- MODALITÀ GATHER (preferita se c'è un puro) ----------
        pure_targets = [pos for pos in neigh if self.grid[pos[0]][pos[1]].is_pure() and can_receive(pos)]
        if pure_targets:
            target_pos = max(pure_targets, key=piece_count_at)

            changed = True
            while changed:
                changed = False
                moved = self._move_tipo((br, bc), target_pos, tipo)
                if moved > 0:
                    changed = True
                for pos in neigh:
                    if pos == target_pos:
                        continue
                    if not can_receive(target_pos):
                        break
                    moved2 = self._move_tipo(pos, target_pos, tipo)
                    if moved2 > 0:
                        changed = True
            return

        # ---------- MODALITÀ SPLIT (nessun puro disponibile) ----------
        neigh = [pos for pos in neigh if can_receive(pos)]
        if not neigh:
            return

        def score(pos):
            r, c = pos
            pl = self.grid[r][c]
            tp = pl.get_piece(tipo)
            free_total = pl.free_slots(MAX_SLICES)
            free_tipo = MAX_SLICES - tp.count
            can_complete = (tp.count + min(free_total, free_tipo) >= MAX_SLICES)
            return (1 if can_complete else 0, tp.count, free_total)

        neigh.sort(key=score, reverse=True)

        changed = True
        while changed:
            changed = False
            bridge = self.grid[br][bc]
            if not bridge or bridge.get_piece(tipo) is None:
                break
            for target_pos in neigh:
                moved = self._move_tipo((br, bc), target_pos, tipo)
                if moved > 0:
                    changed = True


    def chain_merge_from_type(self, tipo, placed_positions):
        """
        Risolve TUTTI i merge possibili per quel tipo, ma dando priorità assoluta
        alla componente connessa che parte dalle celle piazzate (così il vicino V2 sopra
        si unisce subito al V appena piazzato).
        """
        # costruisci l'insieme di celle da risolvere: unione delle componenti connesse
        # di tipo 'tipo' che partono dalle celle piazzate
        active_cells = set()
        for (pr, pc) in placed_positions:
            active_cells |= self._connected_component_of_type_from(pr, pc, tipo)

        # se non c'è niente connesso al piazzato, fallback: niente da fare
        if not active_cells:
            return

        changed = True
        while changed:
            changed = False

            # importa: lista stabile (così possiamo break/ricominciare)
            cell_list = list(active_cells)

            for r, c in cell_list:
                if self._is_marked_to_remove((r, c)):
                    continue
                plate = self.grid[r][c]
                if not plate or plate.get_piece(tipo) is None:
                    continue

                for nr, nc in self.neighbors4(r, c):
                    if (nr, nc) not in active_cells:
                        continue
                    if self._is_marked_to_remove((nr, nc)):
                        continue
                    nplate = self.grid[nr][nc]
                    if not nplate or nplate.get_piece(tipo) is None:
                        continue

                    target_pos, source_pos = self._pick_target_source((r, c), (nr, nc), tipo, placed_positions)
                    if target_pos is None:
                        continue

                    moved = self._move_tipo(source_pos, target_pos, tipo)
                    if moved > 0:
                        changed = True
                        # dopo un movimento la componente può cambiare (celle svuotate),
                        # ricalcoliamo active_cells ripartendo dai piazzati
                        active_cells = set()
                        for (pr, pc) in placed_positions:
                            active_cells |= self._connected_component_of_type_from(pr, pc, tipo)
                        break

                if changed:
                    break

        # pulizia piatti vuoti
        for r, c in list(active_cells):
            if self.grid[r][c] and self.grid[r][c].is_empty():
                self.grid[r][c] = None

    # ---------------- CLEANUP ----------------

    def resolve_groups(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] and self.grid[r][c].is_empty():
                    self.grid[r][c] = None

    def finalize_removals(self):
        # Rimuovi SOLO se davvero completo puro (anti-bug)
        for r, c in self.plates_to_remove:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                pl = self.grid[r][c]
                if pl and pl.is_completed_pure(MAX_SLICES):
                    self.grid[r][c] = None
        self.plates_to_remove.clear()


# =========================
#  GENERATORS
# =========================

def generate_random_plate_active(active_types):
    tipi = list(active_types)
    if not tipi:
        tipi = ["C", "S", "V"]
    if random.random() < 0.4 and len(tipi) >= 2:
        scelte = random.sample(tipi, 2)
        return Plate([Piece(scelte[0], random.randint(1, 2)),
                      Piece(scelte[1], random.randint(1, 2))])
    else:
        tipo = random.choice(tipi)
        return Plate([Piece(tipo, random.randint(1, 3))])


def generate_single_option_active(active_types):
    return {"plates": [generate_random_plate_active(active_types)], "orientation": "NONE"}


def generate_double_option_active(active_types):
    return {"plates": [generate_random_plate_active(active_types),
                       generate_random_plate_active(active_types)],
            "orientation": random.choice(["H", "V"])}


def generate_three_options_active(active_types):
    options = []
    if random.random() < 0.25:
        options.append(generate_double_option_active(active_types))
    while len(options) < 3:
        options.append(generate_single_option_active(active_types))
    random.shuffle(options)
    return options
