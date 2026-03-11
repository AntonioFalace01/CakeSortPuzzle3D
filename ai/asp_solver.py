import os
import re

from embasp.specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from embasp.languages.asp.asp_input_program import ASPInputProgram
from embasp.languages.asp.asp_mapper import ASPMapper
from embasp.platforms.desktop.desktop_handler import DesktopHandler

from ai.asp_predicates import Empty, Occ, OccType, OccCount, Opt, OptOrient, OptSize, OptPiece, Choose


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
        self.encoding_path = os.path.join(project_root, "asp", "cakesort_easy.lp")

        if not os.path.exists(self.solver_path):
            raise FileNotFoundError("DLV2 non trovato: " + self.solver_path)
        if not os.path.exists(self.encoding_path):
            raise FileNotFoundError("Encoding non trovata: " + self.encoding_path)

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

    def _read_encoding(self):
        with open(self.encoding_path, "r", encoding="utf-8") as f:
            return f.read()

    def choose_move(self, state, current_options, debug=False):
        self.handler.remove_all()

        program = ASPInputProgram()
        enc = self._read_encoding()
        program.add_program(enc)

        program.add_program("row(0..{}).".format(state.rows - 1))
        program.add_program("col(0..{}).".format(state.cols - 1))

        # --------------------------
        # 1) Fatti griglia — ORA con conteggio fette
        # --------------------------
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

                            # NUOVO: passa anche il conteggio
                            oc = OccCount()
                            oc.set_R(r)
                            oc.set_C(c)
                            oc.set_T(piece.tipo)
                            oc.set_K(piece.count)
                            program.add_object_input(oc)

        # --------------------------
        # 2) Fatti opzioni
        # --------------------------
        valid_solver_indices = []

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

            op = Opt()
            op.set_O(oi)
            program.add_object_input(op)

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

            osz = OptSize()
            osz.set_O(oi)
            osz.set_S(len(opt["plates"]))
            program.add_object_input(osz)

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

        answer_sets = self.handler.start_sync()
        ans_str = answer_sets.get_answer_sets_string()

        if debug:
            print("=== RAW OUTPUT ===")
            print(ans_str)
            print("==================")

        # --------------------------
        # 3) Estrai choose — prova TUTTI gli answer set
        # --------------------------
        best = None
        best_score = -1

        try:
            oas = answer_sets.get_answer_sets()
            for ans in oas:
                for atom in ans.get_atoms():
                    if isinstance(atom, Choose):
                        candidate = (atom.get_O(), atom.get_R(), atom.get_C())
                        # Valuta la qualità della mossa
                        score = self._evaluate_move(state, current_options, candidate)
                        if score > best_score:
                            best_score = score
                            best = candidate
        except Exception as ex:
            if debug:
                print("Errore parsing:", ex)

        if best is None:
            best = _extract_choose_from_string(ans_str)

        # Validazione
        if best is not None:
            oi, r, c = best
            if oi < len(current_options):
                if not state.can_place_block(current_options[oi], r, c):
                    if debug:
                        print("Mossa choose({},{},{}) illegale!".format(oi, r, c))
                    best = None

        # Fallback intelligente
        if best is None:
            best = self._fallback_smart(state, current_options)

        if debug:
            print("SCELTA:", best)

        return best

    def _evaluate_move(self, state, current_options, move):
        """
        Valuta una mossa (oi, r, c) con un punteggio numerico.
        Più alto = meglio.
        """
        oi, r, c = move
        if oi >= len(current_options):
            return -1

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

        # Tipi portati dall'opzione
        types_brought = {}
        for pi, plate_obj in enumerate(plates):
            for piece in plate_obj.pieces:
                if piece.count > 0:
                    types_brought[piece.tipo] = types_brought.get(piece.tipo, 0) + piece.count

        # Controlla vicini per ogni posizione piazzata
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

                for piece in plate_obj.pieces:
                    np = neighbor.get_piece(piece.tipo)
                    if np is not None:
                        # Match tipo! Grande bonus
                        score += 30

                        total = np.count + piece.count
                        # Bonus se si avvicina a 6
                        if total >= 6:
                            score += 100  # Completamento!
                        elif total >= 4:
                            score += 40
                        elif total >= 3:
                            score += 15

                        # Bonus se vicino è puro
                        if neighbor.is_pure():
                            score += 25

                        # Bonus se piatto portato è puro
                        if len(plate_obj.pieces) == 1:
                            score += 15

        # Penalizza opzioni miste
        if len(types_brought) == 1:
            score += 10  # bonus puro

        # Bonus per più fette (opzioni grosse)
        total_slices = sum(types_brought.values())
        score += total_slices * 2

        # Penalizza posizioni isolate
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

        # Se la griglia non è vuota e ci isoliamo, penalizza
        grid_has_plates = any(
            state.grid[rr][cc] is not None
            for rr in range(state.rows)
            for cc in range(state.cols)
        )
        if grid_has_plates and not has_any_neighbor:
            score -= 20

        # Bonus centralità
        center_r = state.rows / 2.0
        center_c = state.cols / 2.0
        for pr, pc in positions:
            dist = abs(pr - center_r) + abs(pc - center_c)
            if dist <= 1.5:
                score += 5
            elif dist <= 2.5:
                score += 2

        return score

    def _fallback_smart(self, state, current_options):
        """
        Fallback: valuta TUTTE le mosse possibili e scegli la migliore.
        Non segue l'ordine delle opzioni.
        """
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
