class Piece:
    def __init__(self, tipo, count=1):
        self.tipo = tipo
        self.count = count

class Plate:
    def __init__(self, pieces):
        self.pieces = pieces  # lista di Piece

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

    def place_block(self, block, start_r, start_c):
        orientation = block["orientation"]
        plates = block["plates"]
        positions = []

        # calcola posizioni del blocco
        if orientation == "H":
            positions = [(start_r, start_c + i) for i in range(len(plates))]
        else:
            positions = [(start_r + i, start_c) for i in range(len(plates))]

        # verifica che tutte le celle siano libere
        for r, c in positions:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                print("Blocco fuori griglia!")
                return False
            if self.grid[r][c] is not None:
                print(f"Cella ({r},{c}) occupata!")
                return False

        # piazza i piatti e merge
        for (r, c), plate in zip(positions, plates):
            self.grid[r][c] = plate
            self.merge_adjacent_safe_by_type(r, c)

        # risolvi gruppi di 6 o più
        self.resolve_groups()
        return True

    def merge_adjacent_safe_by_type(self, r, c):
        """BFS sicuro che unisce tutte le celle adiacenti dello stesso tipo"""
        plate = self.grid[r][c]
        if plate is None:
            return

        queue = [(r, c)]
        visited = set()

        while queue:
            r0, c0 = queue.pop(0)
            visited.add((r0, c0))
            current = self.grid[r0][c0]
            if current is None:
                continue

            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                rr, cc = r0 + dr, c0 + dc
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    neighbor = self.grid[rr][cc]
                    if neighbor and (rr, cc) not in visited:
                        # Somma solo i tipi uguali
                        for p in current.pieces:
                            for np in neighbor.pieces:
                                if np.tipo == p.tipo:
                                    np.count += p.count
                                    p.count = 0  # già unito, non spostare

                        # Aggiungi eventuali nuovi tipi dal current che non esistono in neighbor
                        for p in current.pieces:
                            if p.count > 0 and all(p.tipo != np.tipo for np in neighbor.pieces):
                                neighbor.pieces.append(p)
                                p.count = 0

                        # rimuovi i pezzi ormai uniti
                        current.pieces = [p for p in current.pieces if p.count > 0]

                        # continua BFS dalla cella vicina
                        queue.append((rr, cc))

    def resolve_groups(self, K=6):
        for r in range(self.rows):
            for c in range(self.cols):
                plate = self.grid[r][c]
                if plate:
                    to_remove = []
                    for p in plate.pieces:
                        if p.count >= K:
                            print(f"Torta completata! Tipo: {p.tipo}")
                            self.score += 10
                            to_remove.append(p)
                    for p in to_remove:
                        plate.pieces.remove(p)
                    if not plate.pieces:
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

