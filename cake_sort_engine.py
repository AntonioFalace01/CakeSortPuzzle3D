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
        # 1) bridge merge: il piatto appena piazzato fa da "ponte" e convoglia verso un target
        for (pr, pc) in placed_positions:
            for tipo in tipi_coinvolti:
                self._merge_bridge_for_type(pr, pc, tipo, placed_positions)

        # 2) poi risolvi eventuali merge residui a catena
        for tipo in tipi_coinvolti:
            self.chain_merge_from_type(tipo, placed_positions)


        self.resolve_groups()
        return True

    # ---------------- MERGE DIRECTION RULE ----------------

    def _pick_target_source(self, pos_a, pos_b, tipo, placed_positions):
        """
        Decide direzione source->target per NON far mescolare puro/misto come richiesto.
        Regola:
        - Se uno dei due è PURO e appena piazzato: quello è TARGET
        - Altrimenti, se uno dei due è PURO: quello è TARGET
        - Altrimenti: target = quello con più count di quel tipo
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
            return pos_a, pos_b  # target=a
        if b_pure and b_new and not (a_pure and a_new):
            return pos_b, pos_a  # target=b

        # 2) puro pre-esistente
        if a_pure and not b_pure:
            return pos_a, pos_b
        if b_pure and not a_pure:
            return pos_b, pos_a

        # 3) fallback: più count
        if pa.count > pb.count:
            return pos_a, pos_b
        if pb.count > pa.count:
            return pos_b, pos_a

        # Calamita logica (solo se nessuno dei due è puro):
        # preferisci come TARGET il piatto appena piazzato
        if not a_pure and not b_pure:
            if a_new and not b_new:
                return pos_a, pos_b
            if b_new and not a_new:
                return pos_b, pos_a


        # tie-break stabile
        if rb > ra or (rb == ra and cb > ca):
            return pos_b, pos_a
        return pos_a, pos_b

    def _move_tipo(self, source_pos, target_pos, tipo):
        """
        Muove quante fette possibili di 'tipo' da source a target rispettando:
        - cap totale 6 nel target
        - cap tipo 6 nel target
        Ritorna moved (0 se niente).
        """
        sr, sc = source_pos
        tr, tc = target_pos
        source = self.grid[sr][sc]
        target = self.grid[tr][tc]
        if not source or not target:
            return 0

        sp = source.get_piece(tipo)
        tp = target.get_piece(tipo)
        if not sp or not tp:
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

    def _merge_bridge_for_type(self, br, bc, tipo, placed_positions):
        """
        'Bridge merge': la cella (br,bc) è il piatto appena piazzato (spesso misto).
        Per 'tipo', convoglia tutte le fette dai vicini che hanno quel tipo verso un target unico:
        - se esiste un PURO appena piazzato (raramente qui): target quello
        - altrimenti target = PURO pre-esistente tra i vicini (scegli quello con count più alto)
        - altrimenti target = il vicino con count più alto
        Poi:
        - muove prima dal bridge -> target
        - poi prova a muovere anche dagli altri vicini -> target
        Ripete finché non cambia più.
        """
        if not self.grid[br][bc]:
            return

        bridge = self.grid[br][bc]
        if not bridge.get_piece(tipo):
            return

        # raccogli vicini contenenti tipo
        neigh = []
        for nr, nc in self.neighbors4(br, bc):
            pl = self.grid[nr][nc]
            if pl and pl.get_piece(tipo) and not self._is_marked_to_remove((nr, nc)):
                neigh.append((nr, nc))

        if not neigh:
            return

        # scegli target unico
        def piece_count_at(pos):
            r, c = pos
            return self.grid[r][c].get_piece(tipo).count

        # preferisci puro pre-esistente tra i vicini
        pure_neigh = [pos for pos in neigh if self.grid[pos[0]][pos[1]].is_pure() and (pos not in placed_positions)]
        if pure_neigh:
            target_pos = max(pure_neigh, key=piece_count_at)
        else:
            target_pos = max(neigh, key=piece_count_at)

        # loop di convogliamento
        changed = True
        while changed:
            changed = False

            # 1) bridge -> target (così il bridge perde quel tipo e resta l'altro, es V)
            moved = self._move_tipo((br, bc), target_pos, tipo)
            if moved > 0:
                changed = True

            # 2) ogni vicino -> target
            for pos in neigh:
                if pos == target_pos:
                    continue
                moved2 = self._move_tipo(pos, target_pos, tipo)
                if moved2 > 0:
                    changed = True


    def chain_merge_from_type(self, tipo, placed_positions):
        """
        Risolve TUTTI i merge possibili per quel tipo finché la griglia si stabilizza.
        Questo permette effetto "ponte": il piatto piazzato può far partire una cascata
        che unisce più piatti dello stesso tipo.
        """
        changed = True

        while changed:
            changed = False

            # Scansiona tutte le celle e prova a fare merge su tutte le adiacenze.
            # Se fa almeno un movimento, ricomincia da capo (perché la griglia è cambiata).
            for r in range(self.rows):
                for c in range(self.cols):
                    if self._is_marked_to_remove((r, c)):
                        continue

                    plate = self.grid[r][c]
                    if not plate or plate.get_piece(tipo) is None:
                        continue

                    for nr, nc in self.neighbors4(r, c):
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
                            # restart scan: evita problemi di ordine e permette cascade pulita
                            break

                    if changed:
                        break
                if changed:
                    break

        # pulizia piatti vuoti
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] and self.grid[r][c].is_empty():
                    self.grid[r][c] = None


    # ---------------- CLEANUP ----------------

    def resolve_groups(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] and self.grid[r][c].is_empty():
                    self.grid[r][c] = None

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
