import os

from embasp.specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from embasp.languages.asp.asp_input_program import ASPInputProgram
from embasp.languages.asp.asp_mapper import ASPMapper
from embasp.platforms.desktop.desktop_handler import DesktopHandler
from ai.asp_predicates import (
    Empty, Occ, OccType, OccCount,
    Opt, OptOrient, OptSize, OptPiece,
    Choose
)

TYPE_MAP = {
    "C": "c", "S": "s", "V": "v", "L": "l", "A": "a",
    "B": "b", "D": "d", "E": "e",
}


class CakeSortASPSolver:
    def __init__(self, project_root):
        self.project_root = project_root
        self.solver_path = os.path.join(project_root, "Solvers", "dlv2.exe")
        self.encoding_path = os.path.join(project_root, "asp", "cakesort_ia.lp")

        if not os.path.exists(self.solver_path):
            raise FileNotFoundError("DLV2 non trovato: " + self.solver_path)
        if not os.path.exists(self.encoding_path):
            raise FileNotFoundError("Encoding non trovata: " + self.encoding_path)

        self.handler = DesktopHandler(DLV2DesktopService(self.solver_path))

        ASPMapper.get_instance().register_class(Empty)
        ASPMapper.get_instance().register_class(Occ)
        ASPMapper.get_instance().register_class(OccType)
        ASPMapper.get_instance().register_class(OccCount)
        ASPMapper.get_instance().register_class(Opt)
        ASPMapper.get_instance().register_class(OptOrient)
        ASPMapper.get_instance().register_class(OptSize)
        ASPMapper.get_instance().register_class(OptPiece)
        ASPMapper.get_instance().register_class(Choose)

    def _read_encoding(self) -> str:
        with open(self.encoding_path, "r", encoding="utf-8") as f:
            return f.read()

    def choose_move(self, state, current_options, debug=False):
        self.handler.remove_all()

        program = ASPInputProgram()
        enc = self._read_encoding()
        program.add_program(enc)

        # domini — sintassi ASP pura, nessun oggetto
        program.add_program(f"row(0..{state.rows - 1}).")
        program.add_program(f"col(0..{state.cols - 1}).")

        # griglia tramite oggetti
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
                            t = TYPE_MAP.get(piece.tipo, piece.tipo.lower())

                            ot = OccType()
                            ot.set_R(r)
                            ot.set_C(c)
                            ot.set_T(t)
                            program.add_object_input(ot)

                            oc = OccCount()
                            oc.set_R(r)
                            oc.set_C(c)
                            oc.set_T(t)
                            oc.set_K(piece.count)
                            program.add_object_input(oc)

        valid_solver_indices = []

        # opzioni tramite oggetti
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
                    print(f"[AI] Solver: opzione {oi} non ha mosse legali, saltata")
                continue

            valid_solver_indices.append(oi)

            op = Opt()
            op.set_O(oi)
            program.add_object_input(op)

            orient = opt.get("orientation", "NONE")
            orc = "h" if orient == "H" else "v" if orient == "V" else "n"
            oo = OptOrient()
            oo.set_O(oi)
            oo.set_OR(orc)
            program.add_object_input(oo)

            os_ = OptSize()
            os_.set_O(oi)
            os_.set_S(len(opt["plates"]))
            program.add_object_input(os_)

            for pi, plate_obj in enumerate(opt["plates"]):
                for piece in plate_obj.pieces:
                    if piece.count > 0:
                        t = TYPE_MAP.get(piece.tipo, piece.tipo.lower())
                        op_piece = OptPiece()
                        op_piece.set_O(oi)
                        op_piece.set_P(pi)
                        op_piece.set_T(t)
                        op_piece.set_K(piece.count)
                        program.add_object_input(op_piece)

        if not valid_solver_indices:
            if debug:
                print("[AI] Solver: nessuna opzione con mosse legali -> ritorno None")
            return None

        if debug:
            tmp_path = os.path.join(self.project_root, "asp_debug_instance.lp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(enc)
                if not enc.endswith("\n"):
                    f.write("\n")
                f.write(program.get_programs())

        if debug:
            print("=== FATTI PASSATI A DLV2 ===")
            print(program.get_programs())
            print("=== FINE FATTI ===")

        self.handler.add_program(program)
        answer_sets = self.handler.start_sync()

        if debug:
            print("=== RAW OUTPUT DLV2 ===")
            print(answer_sets.get_answer_sets_string())
            print("=== FINE RAW OUTPUT ===")

            if debug:
                print("=== TUTTI GLI ANSWER SETS ===")
                all_as = answer_sets.get_answer_sets()
                for ans in all_as:
                    print(ans.get_atoms(), "COST:", ans.get_cost() if hasattr(ans, 'get_cost') else "?")
                print("=== FINE TUTTI ===")
            else:
                print("Nessun answer set ottimale trovato")
            print("=== FINE ANSWER SETS ===")

        self.handler.add_program(program)
        answer_sets = self.handler.start_sync()

        best = None
        optimal = answer_sets.get_optimal_answer_sets()
        if optimal:
            for obj in optimal[-1].get_atoms():
                if isinstance(obj, Choose):
                    best = (obj.get_O(), obj.get_R(), obj.get_C())
                    if debug:
                        print(f"[AI] Candidato da ASP (object): {best}")
                    break

        if best is None:
            if debug:
                print("[AI] Nessun oggetto Choose trovato nell'answer set ottimale")
            return None

        oi, r, c = best
        if oi >= len(current_options):
            if debug:
                print(f"[AI] Mossa {best} fuori range -> annullata")
            return None

        if not state.can_place_block(current_options[oi], r, c):
            if debug:
                print(f"[AI] Mossa {best} illegale -> annullata")
            return None

        if debug:
            print(f"[AI] SCELTA FINALE: {best} (source=ASP-object)")

        return best