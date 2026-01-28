import random

# =========================
#  DATA STRUCTURES
# =========================

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

        for r, c in positions:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                return False
            if self.grid[r][c] is not None:
                return False

        for (r, c), plate in zip(positions, plates):
            self.grid[r][c] = plate

        tipo_to_cells = {}
        for (r, c), plate in zip(positions, plates):
            for p in plate.pieces:
                tipo_to_cells.setdefault(p.tipo, []).append((r, c))

        for tipo in set(p.tipo for plate in block["plates"] for p in plate.pieces):
            self.chain_merge_from_type(tipo)

        self.resolve_groups()
        return True

    def choose_target(self, plate_a, plate_b, tipo, pos_a, pos_b):
        pa = plate_a.get_piece(tipo)
        pb = plate_b.get_piece(tipo)

        a_pure = len(plate_a.pieces) == 1
        b_pure = len(plate_b.pieces) == 1

        if a_pure and not b_pure:
            return plate_a, plate_b
        if b_pure and not a_pure:
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

    def chain_merge_from_type(self, tipo):
        """
        Merge globale completo per un tipo.
        Unisce tutte le celle adiacenti contenenti il tipo finché non ci sono più fusioni possibili.
        Gestisce overflow e limite massimo 6 fette per cella.
        """
        changed = True
        while changed:
            changed = False

            # tutte le celle che contengono il tipo
            cells_with_type = [
                (r, c) for r in range(self.rows) for c in range(self.cols)
                if self.grid[r][c] is not None and self.grid[r][c].get_piece(tipo)
            ]

            for cr, cc in cells_with_type:
                current = self.grid[cr][cc]
                if current is None:
                    continue

                cp = current.get_piece(tipo)
                if not cp:
                    continue

                for nr, nc in self.neighbors4(cr, cc):
                    neighbor = self.grid[nr][nc]
                    if neighbor is None:
                        continue

                    np = neighbor.get_piece(tipo)
                    if not np:
                        continue

                    # scegli target / source
                    target, source = self.choose_target(
                        current, neighbor, tipo, (cr, cc), (nr, nc)
                    )

                    # salva posizione source
                    if source is current:
                        source_pos = (cr, cc)
                    else:
                        source_pos = (nr, nc)

                    # rimuovi tutte le fette dalla source
                    sp_count = source.remove(
                        tipo, source.get_piece(tipo).count
                    )

                    if sp_count <= 0:
                        continue

                    tp = target.get_piece(tipo)
                    if not tp:
                        target.add(tipo, 0)
                        tp = target.get_piece(tipo)

                    # --- CASO OVERFLOW ---
                    if tp.count + sp_count > 6:
                        overflow = tp.count + sp_count - 6

                        # torta completata
                        self.score += 10
                        target.remove(tipo, tp.count)

                        # overflow resta nella stessa cella
                        if overflow > 0:
                            target.add(tipo, overflow)

                        changed = True

                    # --- CASO NORMALE ---
                    else:
                        tp.count += sp_count
                        changed = True

                    # se la source è vuota, libera SOLO la sua cella
                    if source.is_empty():
                        sr, sc = source_pos
                        self.grid[sr][sc] = None
                        changed = True

    def resolve_groups(self):
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if not plate:
                    continue
                for p in plate.pieces:
                    if p.count >= 6:
                        self.grid[r][c] = None
                        self.score += 10
                        break


# =========================
#  GENERATION LOGIC
# =========================

TIPI = ["C", "S", "V"]

def generate_random_plate():
    # probabilità di piatto misto
    if random.random() < 0.4:   # 40% misti
        tipi = random.sample(TIPI, 2)
        pieces = [
            Piece(tipi[0], random.randint(1, 2)),
            Piece(tipi[1], random.randint(1, 2))
        ]
        return Plate(pieces)
    else:
        tipo = random.choice(TIPI)
        count = random.randint(1, 3)
        return Plate([Piece(tipo, count)])


def generate_single_option():
    return {
        "plates": [generate_random_plate()],
        "orientation": "NONE"
    }

def generate_double_option():
    return {
        "plates": [generate_random_plate(), generate_random_plate()],
        "orientation": random.choice(["H", "V"])
    }

def generate_three_options():
    options = []
    if random.random() < 0.25:   # blocco doppio più raro
        options.append(generate_double_option())

    while len(options) < 3:
        options.append(generate_single_option())

    random.shuffle(options)
    return options



