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


class GameState:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.score = 0

    def print_grid(self):
        for r in range(self.rows):
            line = []
            for c in range(self.cols):
                plate = self.grid[r][c]
                if plate:
                    s = " + ".join([f"{p.tipo}{p.count}" for p in plate.pieces])
                    line.append(s)
                else:
                    line.append(".")
            print(" | ".join(line))
        print(f"Punteggio: {self.score}\n")

    def neighbors4(self, r, c):
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < self.rows and 0 <= cc < self.cols:
                yield rr, cc

    def place_block(self, block, start_r, start_c):
        orientation = block["orientation"]
        plates = block["plates"]
        positions = []

        # calcola posizioni del blocco
        if orientation == "H":
            positions = [(start_r, start_c + i) for i in range(len(plates))]
        else:
            positions = [(start_r + i, start_c) for i in range(len(plates))]

        # verifica celle libere
        for r, c in positions:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                print("Blocco fuori griglia!")
                return False
            if self.grid[r][c] is not None:
                print(f"Cella ({r},{c}) occupata!")
                return False

        # piazza i piatti
        for (r, c), plate in zip(positions, plates):
            self.grid[r][c] = plate

        # mappa dei tipi nelle celle piazzate
        tipo_to_cells = {}
        for (r, c), plate in zip(positions, plates):
            for p in plate.pieces:
                tipo_to_cells.setdefault(p.tipo, []).append((r, c))

        # merge globale per ogni tipo
        for tipo, cells in tipo_to_cells.items():
            self.chain_merge_from_type(tipo, cells)

        # risolvi gruppi da 6 fette
        self.resolve_groups()
        return True

    def choose_target(self, plate_a, plate_b, tipo, pos_a, pos_b):
        pa = plate_a.get_piece(tipo)
        pb = plate_b.get_piece(tipo)
        a_pure = len(plate_a.pieces) == 1
        b_pure = len(plate_b.pieces) == 1

        # puro batte misto
        if a_pure and not b_pure:
            return plate_a, plate_b
        if b_pure and not a_pure:
            return plate_b, plate_a

        # più quantità vince
        if pa.count > pb.count:
            return plate_a, plate_b
        if pb.count > pa.count:
            return plate_b, plate_a

        # gravità: più in basso / più a destra
        ra, ca = pos_a
        rb, cb = pos_b
        if rb > ra or (rb == ra and cb > ca):
            return plate_b, plate_a
        else:
            return plate_a, plate_b

    def chain_merge_from_type(self, tipo, starting_cells):
        """
        Merge globale per un tipo con limite 6 fette per cella.
        Overflow propagate alle celle vicine.
        """
        queue = list(starting_cells)
        in_queue = set(queue)

        while queue:
            cr, cc = queue.pop(0)
            in_queue.discard((cr, cc))

            current = self.grid[cr][cc]
            if current is None or current.get_piece(tipo) is None:
                continue

            for nr, nc in self.neighbors4(cr, cc):
                neighbor = self.grid[nr][nc]
                if neighbor is None or neighbor.get_piece(tipo) is None:
                    continue

                target, source = self.choose_target(current, neighbor, tipo, (cr, cc), (nr, nc))
                sp = source.get_piece(tipo)
                if not sp:
                    continue

                moved = source.remove(tipo, sp.count)
                tp = target.get_piece(tipo)
                if tp is None:
                    target.add(tipo, 0)
                    tp = target.get_piece(tipo)

                # gestisci limite massimo 6
                overflow = 0
                if tp.count + moved > 6:
                    allowed = 6 - tp.count
                    tp.count = 6
                    overflow = moved - allowed
                    # punteggio
                    self.score += 10
                    target.remove(tipo, 6)
                else:
                    tp.count += moved

                # overflow → propagate
                if overflow > 0:
                    for rr, cc2 in self.neighbors4(cr, cc):
                        if overflow <= 0:
                            break
                        other = self.grid[rr][cc2]
                        if other is None:
                            other = Plate([])
                            self.grid[rr][cc2] = other
                        moved_to_other = min(overflow, 6 - (other.get_piece(tipo).count if other.get_piece(tipo) else 0))
                        if moved_to_other > 0:
                            other.add(tipo, moved_to_other)
                            overflow -= moved_to_other
                            if (rr, cc2) not in in_queue:
                                queue.append((rr, cc2))
                                in_queue.add((rr, cc2))

                # svuota celle vuote
                if source.is_empty():
                    if source is current:
                        self.grid[cr][cc] = None
                    else:
                        self.grid[nr][nc] = None

                for pos in [(cr, cc), (nr, nc)]:
                    if pos not in in_queue:
                        queue.append(pos)
                        in_queue.add(pos)

    def resolve_groups(self, K=6):
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if not plate:
                    continue
                to_remove = []
                for p in plate.pieces:
                    if p.count >= K:
                        print(f"Torta completata! Tipo: {p.tipo} in ({r},{c})")
                        self.score += 10
                        to_remove.append(p.tipo)
                for t in to_remove:
                    plate.remove(t, K)
                if plate.is_empty():
                    self.grid[r][c] = None

    def valid_moves(self, block_length=1, orientation="H"):
        moves = []
        for r in range(self.rows):
            for c in range(self.cols):
                ok = True
                for i in range(block_length):
                    rr, cc = (r, c+i) if orientation=="H" else (r+i, c)
                    if not (0 <= rr < self.rows and 0 <= cc < self.cols):
                        ok = False
                        break
                    if self.grid[rr][cc] is not None:
                        ok = False
                        break
                if ok:
                    moves.append((r,c))
        return moves

    def is_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] is not None:
                    return False
        return True



