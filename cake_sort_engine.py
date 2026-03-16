import random

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
        self.animation_snapshots = []
        self.plates_to_remove = []

        # Lista piatta di eventi nell'ordine in cui _move_tipo li esegue.
        # Ogni elemento: (tipo, count, from_pos, to_pos)
        self._raw_events = []
        # Snapshot della griglia DOPO il piazzamento dei nuovi pezzi,
        # PRIMA di qualsiasi merge. Usato per ricostruire gli snapshot visivi.
        self._pre_move_grid = None
        # Celle coinvolte per ogni tipo durante i merge (per il pathfinding)
        self._visited_by_tipo = {}  # {tipo: set of (r,c)}

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

    def _full_component_of_type(self, seed_cells, tipo):
        visited = set()
        stack = []
        for pos in seed_cells:
            r, c = pos
            pl = self.grid[r][c]
            if pl and pl.get_piece(tipo) is not None and not self._is_marked_to_remove(pos):
                if pos not in visited:
                    visited.add(pos)
                    stack.append(pos)
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

    # ---------------- SNAPSHOT VISIVO (POST-MOVE) ----------------

    def _snap_deep(self, grid):
        """Copia profonda di una griglia arbitraria."""
        snap = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                plate = grid[r][c]
                if plate is None:
                    snap[r][c] = None
                else:
                    snap[r][c] = Plate([Piece(p.tipo, p.count) for p in plate.pieces])
        return snap

    def _apply_event_to_grid(self, grid, tipo, count, from_pos, to_pos):
        """Applica un singolo evento di movimento su una griglia-copia."""
        fr, fc = from_pos
        tr, tc = to_pos
        src = grid[fr][fc]
        tgt = grid[tr][tc]
        if src is None or tgt is None:
            return 0

        sp = src.get_piece(tipo)
        tp = tgt.get_piece(tipo)
        if sp is None:
            return 0
        if tp is None:
            if tgt.is_empty():
                tp = Piece(tipo, 0)
                tgt.pieces.append(tp)
            else:
                return 0

        can_take = min(count, sp.count, tgt.free_slots(MAX_SLICES), MAX_SLICES - tp.count)
        if can_take <= 0:
            return 0

        src.remove(tipo, can_take)
        tgt.add(tipo, can_take)
        if src.is_empty():
            grid[fr][fc] = None
        return can_take

    @staticmethod
    def _manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _find_relay_path(self, from_pos, to_pos, tipo, relay_cells):
        """
        Trova il percorso di hop adiacenti da from_pos a to_pos
        passando solo per celle che sono relay reali (appaiono sia come
        from_pos che come to_pos nei raw_events dello stesso tipo).

        Restituisce lista di celle (escluso from_pos, incluso to_pos).
        """
        if self._manhattan(from_pos, to_pos) == 1:
            return [to_pos]

        # BFS limitata a from_pos, to_pos e relay reali
        allowed = relay_cells | {from_pos, to_pos}

        from collections import deque
        queue = deque([[from_pos]])
        seen = {from_pos}

        while queue:
            path = queue.popleft()
            cur = path[-1]
            if cur == to_pos:
                return path[1:]
            r, c = cur
            for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
                npos = (nr, nc)
                if npos in seen:
                    continue
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if npos not in allowed:
                    continue
                seen.add(npos)
                queue.append(path + [npos])

        return [to_pos]  # fallback: salto diretto (non dovrebbe servire)

    def _expand_events_to_hops(self, raw_events, visited_by_tipo=None):
        """
        Espande gli eventi non-adiacenti in hop adiacenti.

        Per un evento (tipo, count, A→C) dove Manhattan(A,C) > 1:
        cerca tra gli altri raw_events un from_pos B tale che:
          - stesso tipo e stesso to_pos C
          - adiacente ad A (Manhattan == 1)
          - adiacente a C (Manhattan == 1)
        Se trovato, spezza in (A→B) e (B→C).

        Poi applica ordinamento topologico: X→Y deve precedere Y→Z.
        """

        def manhattan(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Passo 1: espandi hop non-adiacenti usando relay reali
        raw_hops = []
        for i, (tipo, count, from_pos, to_pos) in enumerate(raw_events):
            if manhattan(from_pos, to_pos) == 1:
                raw_hops.append((tipo, count, from_pos, to_pos))
            else:
                # Cerca relay B: altro raw_event con stesso tipo e stesso to_pos,
                # il cui from_pos è adiacente sia a from_pos che a to_pos
                relay = None
                for j, (t2, c2, fp2, tp2) in enumerate(raw_events):
                    if j == i:
                        continue
                    if t2 != tipo or tp2 != to_pos:
                        continue
                    if manhattan(from_pos, fp2) == 1 and manhattan(fp2, to_pos) == 1:
                        relay = fp2
                        break
                if relay:
                    raw_hops.append((tipo, count, from_pos, relay))
                    raw_hops.append((tipo, count, relay, to_pos))
                else:
                    # Nessun relay trovato: salto diretto (adiacenti ma logica strana)
                    raw_hops.append((tipo, count, from_pos, to_pos))

        # Passo 2: ordinamento topologico
        # hop i dipende da hop j se: raw_hops[j].to_pos == raw_hops[i].from_pos
        # e stesso tipo (j deve precedere i)
        from collections import defaultdict, deque
        n = len(raw_hops)
        in_degree = [0] * n
        rdeps = defaultdict(list)  # rdeps[j] = lista di i che dipendono da j

        for i in range(n):
            ti, ci, fpi, tpi = raw_hops[i]
            for j in range(n):
                if j == i:
                    continue
                tj, cj, fpj, tpj = raw_hops[j]
                if tj == ti and tpj == fpi:
                    # j riempie fpi con tipo ti → i deve aspettare j
                    in_degree[i] += 1
                    rdeps[j].append(i)

        queue = deque(idx for idx in range(n) if in_degree[idx] == 0)
        ordered = []
        while queue:
            idx = queue.popleft()
            ordered.append(raw_hops[idx])
            for dep_i in rdeps[idx]:
                in_degree[dep_i] -= 1
                if in_degree[dep_i] == 0:
                    queue.append(dep_i)

        # Se ci sono cicli (non dovrebbe), aggiungi il resto nell'ordine originale
        if len(ordered) < n:
            emitted_ids = set(id(h) for h in ordered)
            for h in raw_hops:
                if id(h) not in emitted_ids:
                    ordered.append(h)

        # Fondi hop consecutivi con stesso (tipo, from_pos, to_pos):
        # es. [C1:(1,1)->(0,1), C2:(1,1)->(0,1)] -> [C3:(1,1)->(0,1)]
        merged = []
        for hop in ordered:
            tipo, count, fp, tp = hop
            if merged and merged[-1][0] == tipo and merged[-1][2] == fp and merged[-1][3] == tp:
                last = merged[-1]
                merged[-1] = (last[0], last[1] + count, last[2], last[3])
            else:
                merged.append(list(hop))
        # Converti in tuple
        ordered = [tuple(h) for h in merged]

        return ordered

    def _build_animation_snapshots(self, visited_by_tipo):
        """
        Costruisce gli snapshot visivi per le animazioni.

        1. Deduplica i raw_events (elimina cicli, tieni solo delta netto)
        2. Espande hop non-adiacenti e ordina topologicamente
        3. Costruisce grid_during / grid_after per ogni hop sul working grid

        NOTA: score e plates_to_remove sono già stati calcolati in place_block
        prima di chiamare questo metodo. Qui non si toccano.
        """
        self.animation_snapshots = []

        # --- Deduplicazione netta ---
        from collections import defaultdict as _dd
        _net = _dd(int)
        for _t, _c, _f, _p in self._raw_events:
            _net[(_t, _f, _p)] += _c
            _net[(_t, _p, _f)] -= _c

        _seen = set()
        deduped = []
        for _t, _c, _f, _p in self._raw_events:
            _key = (_t, _f, _p)
            _rkey = (_t, _p, _f)
            if _key in _seen or _rkey in _seen:
                continue
            net_fwd = _net.get(_key, 0)
            net_bwd = _net.get(_rkey, 0)
            if net_fwd > 0:
                deduped.append((_t, net_fwd, _f, _p))
                _seen.add(_key)
            elif net_bwd > 0:
                deduped.append((_t, net_bwd, _p, _f))
                _seen.add(_rkey)

        # --- Espansione hop + ordinamento topologico + fusione ---
        expanded = self._expand_events_to_hops(deduped, visited_by_tipo)

        if not expanded:
            return

        # --- Costruzione snapshot sul working grid ---
        # Partiamo dal pre_move_grid. Per ogni hop applichiamo il movimento
        # con il count ESATTO dell'hop (già deduplicato e fuso).
        # Hop consecutivi con stessa (from_pos, to_pos) ma tipo diverso vengono
        # processati insieme in un unico snapshot (es. S3+C1 da (0,0)→(1,0)).
        working = self._snap_deep(self._pre_move_grid)

        # Raggruppa hop consecutivi con stessa (from_pos, to_pos)
        grouped = []
        for hop in expanded:
            tipo, count, from_pos, to_pos = hop
            if grouped and grouped[-1][0][2] == from_pos and grouped[-1][0][3] == to_pos:
                grouped[-1].append(hop)
            else:
                grouped.append([hop])

        for group in grouped:
            from_pos = group[0][2]
            to_pos = group[0][3]
            fr, fc = from_pos
            tr, tc = to_pos

            # Calcola gli actual per ogni hop del gruppo
            actuals = []
            for (tipo, count, fp, tp) in group:
                src = working[fr][fc]
                src_piece = src.get_piece(tipo) if src else None
                available = src_piece.count if src_piece else 0
                if available <= 0:
                    actuals.append(0)
                else:
                    actuals.append(min(count, available))

            # Salta il gruppo se tutti gli actual sono 0
            if all(a == 0 for a in actuals):
                continue

            # grid_during: tutte le sorgenti svuotate (fette in volo), target invariato
            grid_during = self._snap_deep(working)
            for (tipo, count, fp, tp), actual in zip(group, actuals):
                if actual <= 0:
                    continue
                src_d = grid_during[fr][fc]
                if src_d and src_d.get_piece(tipo):
                    src_d.remove(tipo, actual)
                    if src_d.is_empty():
                        grid_during[fr][fc] = None

            # Applica i movimenti sul working grid
            for (tipo, count, fp, tp), actual in zip(group, actuals):
                if actual <= 0:
                    continue
                src = working[fr][fc]
                src_piece = src.get_piece(tipo) if src else None
                if src and src_piece:
                    src.remove(tipo, actual)
                    if src.is_empty():
                        working[fr][fc] = None
                tgt = working[tr][tc]
                if tgt is None:
                    working[tr][tc] = Plate([Piece(tipo, actual)])
                else:
                    tgt.add(tipo, actual)

            # grid_after: stato dopo l'arrivo di tutte le fette del gruppo
            grid_after = self._snap_deep(working)

            # Genera uno snapshot per ogni hop del gruppo con actual > 0,
            # tutti con lo stesso grid_during e grid_after
            for (tipo, count, fp, tp), actual in zip(group, actuals):
                if actual <= 0:
                    continue
                self.animation_snapshots.append({
                    "event": {"tipo": tipo, "count": actual, "from": from_pos, "to": to_pos},
                    "grid_during": grid_during,
                    "grid_after": grid_after,
                })

    def place_block(self, block, start_r, start_c):
        orientation = block["orientation"]
        plates = block["plates"]

        # Se c'è ancora una torta completata pendente (il delay visivo non è ancora
        # finito ma il giocatore ha già piazzato), rimuoviamo subito prima di procedere.
        if self.plates_to_remove:
            self.finalize_removals()

        self.last_animation_events = []
        self.animation_snapshots = []
        self.plates_to_remove = []
        self._raw_events = []
        self._visited_by_tipo = {}

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

        # Piazza i nuovi piatti
        placed_positions = []
        for (r, c), plate in zip(positions, plates):
            self.grid[r][c] = plate
            placed_positions.append((r, c))

        # Snapshot pre-move: include i nuovi piatti appena piazzati
        self._pre_move_grid = self.snapshot_grid_deep()

        tipi_coinvolti = {p.tipo for plate in plates for p in plate.pieces}

        # 0a) SPLIT ATOMICO
        for (pr, pc) in placed_positions:
            for nr, nc in self.neighbors4(pr, pc):
                if self._is_marked_to_remove((nr, nc)):
                    continue
                nplate = self.grid[nr][nc]
                if nplate and not nplate.is_pure():
                    plate = self.grid[pr][pc]
                    if plate and not plate.is_pure():
                        self._split_mixed_pair((pr, pc), (nr, nc), placed_positions)

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

        # --- FIX: calcola score e plates_to_remove UNA SOLA VOLTA
        # sulla griglia logica finale, prima di costruire gli snapshot visivi.
        self.plates_to_remove = []
        for r in range(self.rows):
            for c in range(self.cols):
                pl = self.grid[r][c]
                if pl and pl.is_completed_pure(MAX_SLICES):
                    self.plates_to_remove.append((r, c))
                    self.score += 100

        # Gli snapshot visivi vengono costruiti usando _visited_by_tipo
        # che è stato popolato da _move_tipo durante i merge.
        self._build_animation_snapshots(self._visited_by_tipo)

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
        Se il piatto appena piazzato è PURO, attrae dai vicini le fette dello stesso tipo.
        NON tocca nessun vicino (puro o misto) che ha a sua volta altri vicini con
        lo stesso tipo: quel piatto è un relay e va lasciato al chain_merge.
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

                # Se il vicino (puro O misto) ha altri vicini con lo stesso tipo
                # escluso il piatto corrente, è un relay verso altre celle:
                # NON rubare le sue fette o si crea un gap che blocca il merge.
                is_bridge = self._count_neighbors_with_tipo(nr, nc, tipo, exclude_pos=(pr, pc)) > 0
                if is_bridge:
                    continue

                moved = self._move_tipo((nr, nc), (pr, pc), tipo)
                if moved > 0:
                    changed = True

    def _move_tipo(self, source_pos, target_pos, tipo):
        """
        Sposta fette da source a target. Registra solo l'evento grezzo in
        _raw_events; gli snapshot visivi vengono costruiti dopo in
        _build_animation_snapshots().
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

            # Registra evento grezzo (snapshot costruito dopo)
            self._raw_events.append((tipo, moved, (sr, sc), (tr, tc)))
            # Aggiorna visited_by_tipo per il pathfinding
            if tipo not in self._visited_by_tipo:
                self._visited_by_tipo[tipo] = set()
            self._visited_by_tipo[tipo].add((sr, sc))
            self._visited_by_tipo[tipo].add((tr, tc))

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
            a_is_bridge = (
                    pos_a in placed_positions and
                    self._count_neighbors_with_tipo(pos_a[0], pos_a[1], tipo, exclude_pos=pos_b) > 0
            )
            b_is_bridge = (
                    pos_b in placed_positions and
                    self._count_neighbors_with_tipo(pos_b[0], pos_b[1], tipo, exclude_pos=pos_a) > 0
            )

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

        if len(neigh) == 1:
            nr, nc = neigh[0]
            neighbor = self.grid[nr][nc]
            bridge = self.grid[br][bc]
            if not bridge or bridge.get_piece(tipo) is None:
                return

            if neighbor and not neighbor.is_pure() and bridge and not bridge.is_pure():
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
        # ---------------------------------------------------------------
        # FIX: usa _full_component_of_type invece di _connected_component_of_type_from
        # per raccogliere TUTTE le celle connesse con 'tipo', incluse quelle
        # pre-esistenti sulla griglia (es. il V2 in (2,1) quando piazzo V in (0,1)+(1,1)).
        # Senza questo, la catena su 3+ piatti veniva troncata perché active_cells
        # non includeva le celle già presenti fuori da placed_positions.
        # ---------------------------------------------------------------
        active_cells = self._full_component_of_type(placed_positions, tipo)

        if not active_cells:
            return

        # --- FASE PRE-BRIDGE ---
        def bridge_priority(pos):
            pr, pc = pos
            plate = self.grid[pr][pc]
            if not plate or plate.get_piece(tipo) is None:
                return 0
            if plate.is_pure():
                return -1

            pure_count = 0
            mixed_outer_count = 0
            for nr, nc in self.neighbors4(pr, pc):
                if self._is_marked_to_remove((nr, nc)):
                    continue
                npl = self.grid[nr][nc]
                if not npl or npl.get_piece(tipo) is None:
                    continue
                if npl.is_pure():
                    pure_count += 1
                elif (nr, nc) not in placed_positions:
                    mixed_outer_count += 1

            return pure_count * 2 + mixed_outer_count

        sorted_placed = sorted(placed_positions, key=bridge_priority, reverse=True)

        for (pr, pc) in sorted_placed:
            plate = self.grid[pr][pc]
            if not plate or plate.get_piece(tipo) is None:
                continue
            if self._is_marked_to_remove((pr, pc)):
                continue
            if plate.is_pure():
                continue

            pure_neighbors = []
            mixed_neighbors = []
            for nr, nc in self.neighbors4(pr, pc):
                if self._is_marked_to_remove((nr, nc)):
                    continue
                npl = self.grid[nr][nc]
                if not npl or npl.get_piece(tipo) is None:
                    continue
                if npl.is_pure():
                    pure_neighbors.append((nr, nc))
                else:
                    mixed_neighbors.append((nr, nc))

            # Caso 1: bridge tra misti e un puro
            if pure_neighbors:
                def piece_count_at(pos):
                    pl = self.grid[pos[0]][pos[1]]
                    if not pl: return 0
                    p = pl.get_piece(tipo)
                    return p.count if p else 0

                target_pure = max(pure_neighbors, key=piece_count_at)

                for mn in mixed_neighbors:
                    if self._is_marked_to_remove(mn):
                        continue
                    mpl = self.grid[mn[0]][mn[1]]
                    if mpl and mpl.get_piece(tipo) is not None:
                        self._move_tipo(mn, (pr, pc), tipo)

                changed_inner = True
                while changed_inner:
                    changed_inner = False
                    moved = self._move_tipo((pr, pc), target_pure, tipo)
                    if moved > 0:
                        changed_inner = True
                    for pn in pure_neighbors:
                        if pn == target_pure:
                            continue
                        moved2 = self._move_tipo(pn, target_pure, tipo)
                        if moved2 > 0:
                            changed_inner = True

            # Caso 2: bridge tra due puri, nessun misto
            elif len(pure_neighbors) >= 2:
                def piece_count_at(pos):
                    pl = self.grid[pos[0]][pos[1]]
                    if not pl: return 0
                    p = pl.get_piece(tipo)
                    return p.count if p else 0

                target_pure = max(pure_neighbors, key=piece_count_at)
                changed_inner = True
                while changed_inner:
                    changed_inner = False
                    moved = self._move_tipo((pr, pc), target_pure, tipo)
                    if moved > 0:
                        changed_inner = True
                    for pn in pure_neighbors:
                        if pn == target_pure:
                            continue
                        moved2 = self._move_tipo(pn, target_pure, tipo)
                        if moved2 > 0:
                            changed_inner = True

            # Ricalcola active_cells includendo le celle pre-esistenti
            active_cells = self._full_component_of_type(placed_positions, tipo)

        # --- MERGE A CATENA STANDARD ---
        changed = True
        while changed:
            changed = False
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

                    target_pos, source_pos = self._pick_target_source(
                        (r, c), (nr, nc), tipo, placed_positions
                    )
                    if target_pos is None:
                        continue

                    moved = self._move_tipo(source_pos, target_pos, tipo)
                    if moved > 0:
                        changed = True
                        # Ricalcola usando _full_component_of_type per non perdere celle
                        active_cells = self._full_component_of_type(placed_positions, tipo)
                        break

                if changed:
                    break

        for r, c in list(active_cells):
            if self.grid[r][c] and self.grid[r][c].is_empty():
                self.grid[r][c] = None

    def resolve_groups(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] and self.grid[r][c].is_empty():
                    self.grid[r][c] = None

    def finalize_removals(self):
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