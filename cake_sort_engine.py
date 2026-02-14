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

        def neighbors4_cells(r, c):
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    yield rr, cc

        def build_cluster():
            """Trova tutti i cluster connessi per 'tipo'. Ritorna lista di cluster, ciascuno lista di (r,c)."""
            visited = [[False] * self.cols for _ in range(self.rows)]
            clusters = []
            for r in range(self.rows):
                for c in range(self.cols):
                    plate = self.grid[r][c]
                    if not plate or not plate.get_piece(tipo) or visited[r][c]:
                        continue
                    # BFS/DFS
                    comp = []
                    stack = [(r, c)]
                    visited[r][c] = True
                    while stack:
                        cr, cc = stack.pop()
                        comp.append((cr, cc))
                        for nr, nc in neighbors4_cells(cr, cc):
                            if visited[nr][nc]:
                                continue
                            nplate = self.grid[nr][nc]
                            if nplate and nplate.get_piece(tipo):
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                    if len(comp) >= 2:
                        clusters.append(comp)
            return clusters

        def choose_cluster_target(cluster):
            """Scegli un target “migliore” dentro al cluster.
               Criteri:
               - più fette del tipo
               - tie: piatto più “puro” (meno tipi)
               - tie: posizione più alta/sinistra
            """
            best = None
            for (r, c) in cluster:
                plate = self.grid[r][c]
                p = plate.get_piece(tipo)
                if not p:
                    continue
                score_tuple = (p.count, -len(plate.pieces), -r, -c)
                if best is None or score_tuple > best[0]:
                    best = (score_tuple, (r, c))
            return best[1] if best else None

        while changed:
            changed = False

            # costruisci cluster per questo tipo
            clusters = build_cluster()
            if not clusters:
                break

            for cluster in clusters:
                # scegli target del cluster
                tgt_pos = choose_cluster_target(cluster)
                if not tgt_pos:
                    continue
                tr, tc = tgt_pos

                # nel caso il target sia stato rimosso (sicurezza)
                if self.grid[tr][tc] is None:
                    continue

                # ordina le sorgenti: prima quelle con più fette del tipo
                sources = [(r, c) for (r, c) in cluster if (r, c) != (tr, tc)]
                sources.sort(
                    key=lambda pos: self.grid[pos[0]][pos[1]].get_piece(tipo).count if self.grid[pos[0]][pos[1]] else 0,
                    reverse=True)

                target_plate = self.grid[tr][tc]
                tp = target_plate.get_piece(tipo)
                if not tp:
                    continue

                # merge multi-sorgente verso target
                for sr, sc in sources:
                    src_plate = self.grid[sr][sc]
                    if not src_plate:
                        continue
                    sp = src_plate.get_piece(tipo)
                    if not sp:
                        continue

                    # se target già rimosso (per completamento precedente), fermati
                    if self.grid[tr][tc] is None:
                        break

                    # calcola totale se spostassimo tutto
                    tp_now = target_plate.get_piece(tipo)
                    total = tp_now.count + sp.count

                    if total > 6:
                        # sposta solo quanto serve per arrivare a 6
                        needed = 6 - tp_now.count
                        moved = src_plate.remove(tipo, needed)
                        target_plate.add(tipo, moved)

                        # torta completata: rimuovi target subito, punteggio
                        self.score += 10
                        self.grid[tr][tc] = None
                        target_plate = None  # non usarlo più

                        # se source diventa vuota, rimuovila subito
                        if src_plate.is_empty():
                            self.grid[sr][sc] = None

                        changed = True
                        break  # target non esiste più, finito cluster
                    else:
                        # sposta tutto dalla source al target
                        moved = src_plate.remove(tipo, sp.count)
                        target_plate.add(tipo, moved)

                        # se la source è vuota: rimuovi subito
                        if src_plate.is_empty():
                            self.grid[sr][sc] = None

                        # se target raggiunge 6: rimuovi subito e assegna punteggio
                        tp_after = target_plate.get_piece(tipo)
                        if tp_after and tp_after.count == 6:
                            self.grid[tr][tc] = None
                            target_plate = None
                            self.score += 10
                            changed = True
                            break
                        else:
                            changed = True

                # Se non abbiamo completato il target (non rimosso), prova anche a fondere tra target e vicini rimanenti
                # Il ciclo sopra in genere basta; lasciamo la logica pairwise per eventuali catene residue.

            # pulizia finale di sicurezza
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


