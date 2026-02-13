import random


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


# =========================
#  GAME STATE
# =========================

class GameState:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.score = 0

    def print_grid(self):
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                row.append(str(self.grid[r][c]) if self.grid[r][c] else ".")
            print(" | ".join(row))
        print(f"Punteggio: {self.score}\n")

    def neighbors4(self, r, c):
        for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
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

        if orientation == "H":
            positions = [(start_r, start_c + i) for i in range(len(plates))]
        elif orientation == "V":
            positions = [(start_r + i, start_c) for i in range(len(plates))]
        else:
            positions = [(start_r, start_c)]

        # controllo validità
        for r, c in positions:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                return False
            if self.grid[r][c] is not None:
                return False

        # piazza i piatti
        placed_positions = []
        for (r, c), plate in zip(positions, plates):
            self.grid[r][c] = plate
            placed_positions.append((r, c))

        # tipi coinvolti
        tipi_coinvolti = {
            p.tipo
            for plate in plates
            for p in plate.pieces
        }

        # merge per ogni tipo
        for tipo in tipi_coinvolti:
            self.chain_merge_from_type(tipo, placed_positions)

        self.resolve_groups()
        return True

    # =========================
    #  TARGET SELECTION (FIX)
    # =========================

    def choose_target(self, plate_a, plate_b, tipo, pos_a, pos_b, placed_positions):
        pa = plate_a.get_piece(tipo)
        pb = plate_b.get_piece(tipo)

        a_is_new = pos_a in placed_positions
        b_is_new = pos_b in placed_positions

        a_pure = len(plate_a.pieces) == 1
        b_pure = len(plate_b.pieces) == 1

        # ⭐ Regola calamita del gioco originale

        if a_is_new and not b_is_new:
            if a_pure:
                return plate_a, plate_b
            else:
                return plate_b, plate_a

        if b_is_new and not a_is_new:
            if b_pure:
                return plate_b, plate_a
            else:
                return plate_a, plate_b

        # comportamento normale (combo tra vecchi piatti)
        if pa.count > pb.count:
            return plate_a, plate_b
        if pb.count > pa.count:
            return plate_b, plate_a

        # tie breaker spaziale
        (ra, ca) = pos_a
        (rb, cb) = pos_b
        if rb > ra or (rb == ra and cb > ca):
            return plate_b, plate_a
        return plate_a, plate_b

    # =========================
    #  MERGE LOGIC
    # =========================

    def chain_merge_from_type(self, tipo, placed_positions):
        changed = True

        while changed:
            changed = False

            cells = [
                (r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self.grid[r][c] and self.grid[r][c].get_piece(tipo)
            ]

            for cr, cc in cells:
                current = self.grid[cr][cc]
                if not current:
                    continue

                cp = current.get_piece(tipo)
                if not cp:
                    continue

                for nr, nc in self.neighbors4(cr, cc):
                    neighbor = self.grid[nr][nc]
                    if not neighbor:
                        continue

                    np = neighbor.get_piece(tipo)
                    if not np:
                        continue

                    target, source = self.choose_target(
                        current, neighbor, tipo,
                        (cr, cc), (nr, nc),
                        placed_positions
                    )

                    source_pos = (cr, cc) if source is current else (nr, nc)

                    tp = target.get_piece(tipo)
                    sp = source.get_piece(tipo)

                    if not tp or not sp:
                        continue

                    total = tp.count + sp.count

                    # =====================
                    # CASO OVERFLOW (completa torta)
                    # =====================
                    if total > 6:
                        needed = 6 - tp.count  # fette necessarie per completare

                        # sposta solo quelle necessarie
                        source.remove(tipo, needed)
                        target.add(tipo, needed)

                        # completa torta
                        # completa torta
                        self.score += 10

                        # rimuovi il piatto COMPLETAMENTE
                        tr, tc = (cr, cc) if target is current else (nr, nc)
                        self.grid[tr][tc] = None

                        # se la source è vuota libera la cella
                        if source.is_empty():
                            sr, sc = source_pos
                            self.grid[sr][sc] = None

                        # sicurezza: se anche il target è rimasto vuoto rimuovilo
                        if target.is_empty():
                            tr, tc = (cr, cc) if target is current else (nr, nc)
                            self.grid[tr][tc] = None

                        changed = True

                    # =====================
                    # CASO NORMALE
                    # =====================
                    else:
                        moved = source.remove(tipo, sp.count)
                        target.add(tipo, moved)

                        # 🔥 se raggiunge 6 → torta completata
                        tp_after = target.get_piece(tipo)
                        if tp_after and tp_after.count == 6:
                            tr, tc = (cr, cc) if target is current else (nr, nc)
                            self.grid[tr][tc] = None
                            self.score += 10
                        else:
                            if source.is_empty():
                                sr, sc = source_pos
                                self.grid[sr][sc] = None

                        changed = True

                    # pulizia finale celle vuote (sicurezza assoluta)
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if plate and plate.is_empty():
                    self.grid[r][c] = None


    # =========================
    #  CLEANUP
    # =========================

    def resolve_groups(self):
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if not plate:
                    continue

                if plate.is_empty():
                    self.grid[r][c] = None
                    continue

                for p in plate.pieces:
                    if p.count >= 6:
                        self.grid[r][c] = None
                        self.score += 10
                        break

def generate_random_plate_active(active_types):
    tipi = list(active_types)
    if not tipi:
        tipi = ["C", "S", "V"]
    if random.random() < 0.4 and len(tipi) >= 2:
        scelte = random.sample(tipi, 2)
        return Plate([ Piece(scelte[0], random.randint(1, 2)), Piece(scelte[1], random.randint(1, 2)) ])
    else:
        tipo = random.choice(tipi)
        return Plate([Piece(tipo, random.randint(1, 3))])

def generate_single_option_active(active_types):
    return {"plates": [generate_random_plate_active(active_types)], "orientation": "NONE"}

def generate_double_option_active(active_types):
    return { "plates": [generate_random_plate_active(active_types), generate_random_plate_active(active_types)], "orientation": random.choice(["H", "V"]) }

def generate_three_options_active(active_types):
    options = []
    if random.random() < 0.25: options.append(generate_double_option_active(active_types))
    while len(options) < 3:
        options.append(generate_single_option_active(active_types))

    random.shuffle(options)
    return options


