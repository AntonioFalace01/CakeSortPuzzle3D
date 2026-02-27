import random
from sound_manager import SFX


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

    # =========================
    #  DEBUG / LOGGING
    # =========================

    def _cell_str(self, r, c, plate=None):
        """Rappresentazione compatta di una cella."""
        if plate is None:
            plate = self.grid[r][c]
        if plate is None:
            return "."
        # es: C4S2 (senza spazi)
        s = "".join(f"{p.tipo}{p.count}" for p in plate.pieces)
        return s if s else "EMPTY"

    def grid_to_strings(self, grid_snapshot=None):
        """Ritorna matrice di stringhe per stampa/diff."""
        g = grid_snapshot if grid_snapshot is not None else self.grid
        out = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                plate = g[r][c]
                if plate is None:
                    row.append(".")
                else:
                    row.append("".join(f"{p.tipo}{p.count}" for p in plate.pieces) or "EMPTY")
            out.append(row)
        return out

    def snapshot_grid_shallow(self):
        """
        Snapshot leggero: copia la struttura riga/colonna ma NON fa deepcopy dei Plate.
        Per debug di ALTO LIVELLO può bastare, ma se vuoi precisione usa snapshot_grid_deep().
        """
        return [[self.grid[r][c] for c in range(self.cols)] for r in range(self.rows)]

    def snapshot_grid_deep(self):
        """Snapshot profondo: Plate/Piece copiati per evitare che il merge modifichi anche il 'prima'."""
        snap = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if plate is None:
                    snap[r][c] = None
                else:
                    # copia manuale (più sicura di deepcopy)
                    new_pieces = [Piece(p.tipo, p.count) for p in plate.pieces]
                    snap[r][c] = Plate(new_pieces)
        return snap

    def print_grid_compact(self, title="GRID"):
        print(f"\n--- {title} ---")
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                row.append(self._cell_str(r, c).ljust(10))
            print(" | ".join(row))
        print(f"Score: {self.score}")
        if self.plates_to_remove:
            print("plates_to_remove:", self.plates_to_remove)
        else:
            print("plates_to_remove: []")
        if self.last_animation_events:
            print("events:")
            for ev in self.last_animation_events:
                print("   ", ev)
        else:
            print("events: []")

    def print_diff(self, before_snap, after_snap, title="DIFF"):
        """
        before_snap / after_snap: snapshot deep (consigliato).
        Stampa celle cambiate.
        """
        b = self.grid_to_strings(before_snap)
        a = self.grid_to_strings(after_snap)

        changes = []
        for r in range(self.rows):
            for c in range(self.cols):
                if b[r][c] != a[r][c]:
                    changes.append((r, c, b[r][c], a[r][c]))

        print(f"\n--- {title} ---")
        if not changes:
            print("nessuna differenza")
            return

        for r, c, old, new in changes:
            print(f"({r},{c}): {old}  ->  {new}")


    def _is_marked_to_remove(self, pos):
        return pos in self.plates_to_remove

    def _add_anim_event(self, tipo, count, from_pos, to_pos):
        if from_pos == to_pos or count <= 0:
            return
        self.last_animation_events.append({
            "tipo": tipo,
            "count": count,
            "from": from_pos,   # (r, c)
            "to": to_pos        # (r, c)
        })

    def neighbors4(self, r, c):
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < self.rows and 0 <= cc < self.cols:
                yield rr, cc

    # =========================
    #  PLACE BLOCK
    # =========================

    def place_block(self, block, start_r, start_c):
        orientation = block["orientation"]
        plates = block["plates"]
        positions = []

        # reset per la mossa
        self.last_animation_events = []
        self.plates_to_remove = []  # IMPORTANTISSIMO: evita stati sporchi

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

        tipi_coinvolti = {
            p.tipo
            for plate in plates
            for p in plate.pieces
        }

        for tipo in tipi_coinvolti:
            self.chain_merge_from_type(tipo, placed_positions)

        self.resolve_groups()
        return True

    # =========================
    #  TARGET SELECTION
    # =========================

    def count_matching_neighbors(self, r, c, tipo):
        count = 0
        for nr, nc in self.neighbors4(r, c):
            if self._is_marked_to_remove((nr, nc)):
                continue
            plate = self.grid[nr][nc]
            if plate and plate.get_piece(tipo):
                count += 1
        return count

    def choose_target(self, plate_a, plate_b, tipo, pos_a, pos_b, placed_positions):
        pa = plate_a.get_piece(tipo)
        pb = plate_b.get_piece(tipo)

        a_is_new = pos_a in placed_positions
        b_is_new = pos_b in placed_positions

        a_pure = len(plate_a.pieces) == 1
        b_pure = len(plate_b.pieces) == 1

        if a_is_new and not b_is_new:
            if self.count_matching_neighbors(*pos_a, tipo) > 1:
                return plate_a, plate_b
        if b_is_new and not a_is_new:
            if self.count_matching_neighbors(*pos_b, tipo) > 1:
                return plate_b, plate_a

        if a_pure and not b_pure:
            return plate_a, plate_b
        if b_pure and not a_pure:
            return plate_b, plate_a

        if a_pure and b_pure:
            if a_is_new and not b_is_new:
                return plate_a, plate_b
            if b_is_new and not a_is_new:
                return plate_b, plate_a

        if pa.count > pb.count:
            return plate_a, plate_b
        if pb.count > pa.count:
            return plate_b, plate_a

        (ra, ca) = pos_a
        (rb, cb) = pos_b
        if rb > ra or (rb == ra and cb > ca):
            return plate_b, plate_a

        return plate_a, plate_b

    # =========================
    #  MERGE LOGIC (anti-freeze definitivo)
    # =========================

    def chain_merge_from_type(self, tipo, placed_positions):
        changed = True

        while changed:
            changed = False

            # Celle che hanno quel tipo e NON sono marcate per rimozione
            cells = [
                (r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if not self._is_marked_to_remove((r, c))
                and self.grid[r][c]
                and self.grid[r][c].get_piece(tipo)
            ]

            merge_done = False

            for cr, cc in cells:
                if merge_done:
                    break

                if self._is_marked_to_remove((cr, cc)):
                    continue
                current = self.grid[cr][cc]
                if not current:
                    continue

                cp = current.get_piece(tipo)
                if not cp:
                    continue

                for nr, nc in self.neighbors4(cr, cc):
                    if merge_done:
                        break

                    if self._is_marked_to_remove((nr, nc)):
                        continue

                    neighbor = self.grid[nr][nc]
                    if not neighbor:
                        continue

                    np = neighbor.get_piece(tipo)
                    if not np:
                        continue

                    target, source = self.choose_target(
                        current, neighbor, tipo,
                        (cr, cc), (nr, nc), placed_positions
                    )

                    tr, tc = (cr, cc) if target is current else (nr, nc)
                    sr, sc = (cr, cc) if source is current else (nr, nc)

                    # se target o source sono marcati, non fare merge
                    if self._is_marked_to_remove((tr, tc)) or self._is_marked_to_remove((sr, sc)):
                        continue

                    if (tr, tc) == (sr, sc):
                        continue
                    if self.grid[tr][tc] is None or self.grid[sr][sc] is None:
                        continue
                    if self.grid[tr][tc] is self.grid[sr][sc]:
                        continue

                    tp = self.grid[tr][tc].get_piece(tipo)
                    sp = self.grid[sr][sc].get_piece(tipo)
                    if not tp or not sp:
                        continue

                    total = tp.count + sp.count

                    # completamento (con overflow conservato)
                    if total >= 6:
                        needed = 6 - tp.count
                        if needed <= 0:
                            # target già completo -> segna e stop
                            self.plates_to_remove.append((tr, tc))
                            self.score += 10
                            changed = True
                            merge_done = True
                            break

                        moved = self.grid[sr][sc].remove(tipo, needed)
                        if moved > 0:
                            self._add_anim_event(tipo, moved, (sr, sc), (tr, tc))
                            self.grid[tr][tc].add(tipo, moved)

                        tp_after = self.grid[tr][tc].get_piece(tipo)
                        if tp_after and tp_after.count == 6:
                            self.plates_to_remove.append((tr, tc))
                            self.score += 10

                        if self.grid[sr][sc] and self.grid[sr][sc].is_empty():
                            self.grid[sr][sc] = None

                        changed = True
                        merge_done = True
                        break

                    # merge normale
                    moved = self.grid[sr][sc].remove(tipo, sp.count)
                    if moved > 0:
                        self._add_anim_event(tipo, moved, (sr, sc), (tr, tc))
                        self.grid[tr][tc].add(tipo, moved)

                    tp_after = self.grid[tr][tc].get_piece(tipo)
                    if tp_after and tp_after.count == 6:
                        self.plates_to_remove.append((tr, tc))
                        self.score += 10

                    if self.grid[sr][sc] and self.grid[sr][sc].is_empty():
                        self.grid[sr][sc] = None

                    changed = True
                    merge_done = True
                    break

        # pulizia piatti vuoti
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] and self.grid[r][c].is_empty():
                    self.grid[r][c] = None

    # =========================
    #  CLEANUP (solo piatti vuoti)
    # =========================

    def resolve_groups(self):
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if plate and plate.is_empty():
                    self.grid[r][c] = None

    # =========================
    #  RIMOZIONI A FINE ANIMAZIONE
    # =========================

    def finalize_removals(self):
        for r, c in self.plates_to_remove:
            if 0 <= r < self.rows and 0 <= c < self.cols:
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
