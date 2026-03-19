import os
import re

from embasp.specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from embasp.languages.asp.asp_input_program import ASPInputProgram
from embasp.languages.asp.asp_mapper import ASPMapper
from embasp.platforms.desktop.desktop_handler import DesktopHandler

from ai.asp_predicates import Empty, Occ, OccType, OccCount, Opt, OptOrient, OptSize, OptPiece, Choose

# Estrae l'ultima mossa choose(O,R,C) da una stringa, se presente. Utile come fallback se il parsing degli answer set fallisce.
def _extract_choose_from_string(s):
    matches = re.findall(r"choose\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", s)
    if not matches:
        return None
    last = matches[-1]
    return int(last[0]), int(last[1]), int(last[2])


class CakeSortASPSolver:
    def __init__(self, project_root):
        self.project_root = project_root
        self.solver_path = os.path.join(project_root, "Solvers", "dlv2.exe")
        self.encoding_path = os.path.join(project_root, "asp", "cakesort_ia.lp")

        if not os.path.exists(self.solver_path):
            raise FileNotFoundError("DLV2 non trovato: " + self.solver_path)
        if not os.path.exists(self.encoding_path):
            raise FileNotFoundError("Encoding non trovata: " + self.encoding_path)
        #handler  che comunica col solver
        self.handler = DesktopHandler(DLV2DesktopService(self.solver_path))

        mapper = ASPMapper.get_instance()
        mapper.register_class(Empty)
        mapper.register_class(Occ)
        mapper.register_class(OccType)
        mapper.register_class(OccCount)
        mapper.register_class(Opt)
        mapper.register_class(OptOrient)
        mapper.register_class(OptSize)
        mapper.register_class(OptPiece)
        mapper.register_class(Choose)

#legge il file asp e lo restituisce come stringa, per poi aggiungerlo al programma di input da dare al solver
    def _read_encoding(self):
        with open(self.encoding_path, "r", encoding="utf-8") as f:
            return f.read()

    def choose_move(self, state, current_options, debug=False):
        self.handler.remove_all()

        program = ASPInputProgram()
        enc = self._read_encoding()
        program.add_program(enc)

#aggiunge domini della griglia
        program.add_program("row(0..{}).".format(state.rows - 1))
        program.add_program("col(0..{}).".format(state.cols - 1))

#scorre la griglia e aggiunge fatti per celle vuote, occupate, tipi di pezzi e conteggi
        for r in range(state.rows):
            for c in range(state.cols):
                plate = state.grid[r][c]
                if plate is None:
                    e = Empty()
                    e.set_R(r)
                    e.set_C(c)
                    program.add_object_input(e)
                else:
                    o = Occ()
                    o.set_R(r)
                    o.set_C(c)
                    program.add_object_input(o)

                    for piece in plate.pieces:
                        if piece.count > 0:
                            ot = OccType()
                            ot.set_R(r)
                            ot.set_C(c)
                            ot.set_T(piece.tipo)
                            program.add_object_input(ot)

                            oc = OccCount()
                            oc.set_R(r)
                            oc.set_C(c)
                            oc.set_T(piece.tipo)
                            oc.set_K(piece.count)
                            program.add_object_input(oc)

#lista vuota che prenderà indici di opzioni valide
        valid_solver_indices = []

#scorre opzioni e controlla se c'è posto sulla griglia, se i la mette nella lista
        for oi, opt in enumerate(current_options):
            has_legal = False
            for r in range(state.rows):
                for c in range(state.cols):
                    if state.can_place_block(opt, r, c):
                        has_legal = True
                        break
                if has_legal:
                    break

            if not has_legal:
                if debug:
                    print("Solver: opzione {} non ha mosse legali, saltata".format(oi))
                continue

            valid_solver_indices.append(oi)

#registra opzione nel programma asp
            op = Opt()
            op.set_O(oi)
            program.add_object_input(op)
#verifica l'orientamento dell'opzione e lo registra come fatto
            orient = opt.get("orientation", "NONE")
            if orient == "H":
                orc = "h"
            elif orient == "V":
                orc = "v"
            else:
                orc = "n"

            oo = OptOrient()
            oo.set_O(oi)
            oo.set_OR(orc)
            program.add_object_input(oo)
#conta quanti piatti ha l'opzione
            osz = OptSize()
            osz.set_O(oi)
            osz.set_S(len(opt["plates"]))
            program.add_object_input(osz)
#registra il contenuto di ogni piatto
            for pi, plate_obj in enumerate(opt["plates"]):
                for piece in plate_obj.pieces:
                    if piece.count > 0:
                        pp = OptPiece()
                        pp.set_O(oi)
                        pp.set_P(pi)
                        pp.set_T(piece.tipo)
                        pp.set_K(piece.count)
                        program.add_object_input(pp)

        if not valid_solver_indices:
            if debug:
                print("Solver: nessuna opzione con mosse legali")
            return None

        self.handler.add_program(program)
#lancia il solver e prende gli answer set
        answer_sets = self.handler.start_sync()
        ans_str = answer_sets.get_answer_sets_string()

        if debug:
            print("=== RAW OUTPUT ===")
            print(ans_str)
            print("==================")

#tengono traccia della miglior mossa trovata
        best = None
        best_score = -1

        try:
            oas = answer_sets.get_answer_sets()
            for ans in oas:
                for atom in ans.get_atoms():
                    if isinstance(atom, Choose):#filtra atomi choose
                        candidate = (atom.get_O(), atom.get_R(), atom.get_C()) #estrae i valori e li mette in una tupla
                        score = self._evaluate_move(state, current_options, candidate)
                        if score > best_score:
                            best_score = score
                            best = candidate
        except Exception as ex:
            if debug:
                print("Errore parsing:", ex)

#se non trova nulla, prova ad estrarre una mossa choose direttamente dalla stringa di output
        if best is None:
            best = _extract_choose_from_string(ans_str)

#controlla se l'opzione è nella lista e se è legale
        if best is not None:
            oi, r, c = best
            if oi < len(current_options):
                if not state.can_place_block(current_options[oi], r, c):
                    if debug:
                        print("Mossa choose({},{},{}) illegale!".format(oi, r, c))
                    best = None
#ennesimo fallback, se non c'è nulla di valido, prova a valutare tutte le mosse legali e scegliere la migliore secondo la funzione di valutazione
        if best is None:
            best = self._fallback_smart(state, current_options)

        if debug:
            print("SCELTA:", best)

        return best

    def _evaluate_move(self, state, current_options, move):
        oi, r, c = move#prende la mossa e la divide in opzione, riga e colonna
        if oi >= len(current_options):
            return -1
#verifica se la mossa è legale
        opt = current_options[oi]
        if not state.can_place_block(opt, r, c):
            return -1

        score = 0
        orientation = opt["orientation"]
        plates = opt["plates"]

        if orientation == "H":
            positions = [(r, c + i) for i in range(len(plates))]
        elif orientation == "V":
            positions = [(r + i, c) for i in range(len(plates))]
        else:
            positions = [(r, c)]

#raccoglie in set tutti  i tipi di pezzi che ci sono
        types_in_grid = set()
        for rr in range(state.rows):
            for cc in range(state.cols):
                pl = state.grid[rr][cc]
                if pl:
                    for piece in pl.pieces:
                        types_in_grid.add(piece.tipo)
#stessa cosa ma per opzione da piazzare
        option_types = set()
        for plate_obj in plates:
            for piece in plate_obj.pieces:
                if piece.count > 0:
                    option_types.add(piece.tipo)
#confronta i tipi nella griglia con quelli del'opzione, la mossa è inutile
        is_useless = bool(types_in_grid) and option_types.isdisjoint(types_in_grid)

        if is_useless:
            # Controlla se la posizione è isolata (nessun vicino occupato)
            is_isolated_pos = True
            for pr, pc in positions:
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = pr + dr, pc + dc
                    if 0 <= nr < state.rows and 0 <= nc < state.cols:
                        if state.grid[nr][nc] is not None:
                            is_isolated_pos = False
                            break
                if not is_isolated_pos:
                    break

            if not is_isolated_pos:
                # Penalità pesantissima: mossa inutile vicino ad altri piatti
                score -= 300
            else:
                # Bonus: mossa inutile correttamente isolata
                score += 20
            # Non ha senso calcolare altro per una mossa inutile
            return score
#condizioone attuale della griglia: totale celle, occupate, libere e rapporto di occupazione
        total_cells = state.rows * state.cols
        occupied = sum(1 for rr in range(state.rows) for cc in range(state.cols) if state.grid[rr][cc] is not None)
        free_cells = total_cells - occupied
        occupancy_ratio = occupied / total_cells

        # Quante celle libere restano DOPO questa mossa
        new_plates_count = len(positions)
        free_after = free_cells - new_plates_count
        if free_after <= 2:
            score -= 200  # quasi game over, fortissima penalità
        elif free_after <= 4:
            score -= 80
        elif free_after <= 6:
            score -= 30

        pressure_bonus = 0
        if occupancy_ratio >= 0.6:
            pressure_bonus = 30
        if occupancy_ratio >= 0.75:
            pressure_bonus = 60
#totale pezzi per tipo portati dall'opzione
        types_brought = {}
        for pi, plate_obj in enumerate(plates):
            for piece in plate_obj.pieces:
                if piece.count > 0:
                    types_brought[piece.tipo] = types_brought.get(piece.tipo, 0) + piece.count

        can_complete_any = False
        for idx, (pr, pc) in enumerate(positions):
            plate_obj = plates[idx] if idx < len(plates) else plates[0]

            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = pr + dr, pc + dc
                if not (0 <= nr < state.rows and 0 <= nc < state.cols):
                    continue
                if (nr, nc) in positions:
                    continue

                neighbor = state.grid[nr][nc]
                if neighbor is None:
                    continue
#per ogni piatto cerca lo stesso tipo nel vicino, se c'è -->merge
                for piece in plate_obj.pieces:
                    np = neighbor.get_piece(piece.tipo)
                    if np is not None:
                        score += 30  # match tipo

                        total = np.count + piece.count
                        if total >= 6:
                            score += 100 + pressure_bonus  # completamento + bonus pressione
                            can_complete_any = True
                        elif total >= 4:
                            score += 40
                        elif total >= 3:
                            score += 15

                        if neighbor.is_pure():
                            score += 25

                        if len(plate_obj.pieces) == 1:
                            score += 15

        # Se la griglia è sotto pressione e NON completi niente, penalizza
        if occupancy_ratio >= 0.6 and not can_complete_any:
            score -= 25
        if occupancy_ratio >= 0.75 and not can_complete_any:
            score -= 50

        if len(types_brought) == 1:
            score += 10
#premia opzione con piu pezzi
        total_slices = sum(types_brought.values())
        score += total_slices * 2
#controlla se il blocco ha almeno un vicino occupato
        has_any_neighbor = False
        for pr, pc in positions:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = pr + dr, pc + dc
                if not (0 <= nr < state.rows and 0 <= nc < state.cols):
                    continue
                if (nr, nc) in positions:
                    continue
                if state.grid[nr][nc] is not None:
                    has_any_neighbor = True
                    break
            if has_any_neighbor:
                break

        if occupied > 0 and not has_any_neighbor:
            score -= 20
#premia posizionamento verso il centro
        center_r = state.rows / 2.0
        center_c = state.cols / 2.0
        for pr, pc in positions:
            dist = abs(pr - center_r) + abs(pc - center_c)
            if dist <= 1.5:
                score += 5
            elif dist <= 2.5:
                score += 2
#set con celle occupate
        occupied_set = set()
        for rr in range(state.rows):
            for cc in range(state.cols):
                if state.grid[rr][cc] is not None:
                    occupied_set.add((rr, cc))
        for pos in positions:
            occupied_set.add(pos)
#calcola quanti slot doppi (orizzontali o verticali) rimangono dopo la mossa, più ce ne sono meglio è per la sopravvivenza a lungo termine
        double_slots = 0
        for rr in range(state.rows):
            for cc in range(state.cols):
                if (rr, cc) not in occupied_set:
                    # controlla H
                    if cc + 1 < state.cols and (rr, cc + 1) not in occupied_set:
                        double_slots += 1
                    # controlla V
                    if rr + 1 < state.rows and (rr + 1, cc) not in occupied_set:
                        double_slots += 1

        if double_slots == 0 and free_after > 1:
            score -= 40  # nessun posto per blocchi doppi = rischio game over
        elif double_slots <= 2:
            score -= 15

        return score

#metodo chiamato solo quando il solver non ha prodotto nulla
    def _fallback_smart(self, state, current_options):
        best = None
        best_score = -999

        for oi, opt in enumerate(current_options):
            for r in range(state.rows):
                for c in range(state.cols):
                    if state.can_place_block(opt, r, c):
                        score = self._evaluate_move(state, current_options, (oi, r, c))
                        if score > best_score:
                            best_score = score
                            best = (oi, r, c)

        return best