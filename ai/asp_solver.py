import os
import re

from embasp.specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from embasp.languages.asp.asp_input_program import ASPInputProgram
from embasp.languages.asp.asp_mapper import ASPMapper
from embasp.platforms.desktop.desktop_handler import DesktopHandler

from ai.asp_predicates import Empty, Occ, OccType, Opt, OptOrient, OptSize, OptPiece, Choose


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
        mapper.register_class(Opt)
        mapper.register_class(OptOrient)
        mapper.register_class(OptSize)
        mapper.register_class(OptPiece)
        mapper.register_class(Choose)

    def _read_encoding(self):
        with open(self.encoding_path, "r", encoding="utf-8") as f:
            return f.read()

    def choose_move(self, state, current_options, debug=False):
        """
        current_options: lista di opzioni DISPONIBILI (non usate).
        Gli indici O nel solver vanno da 0 a len(current_options)-1.
        Il chiamante si occupa di rimappare l'indice al vero opt_index.
        """
        self.handler.remove_all()

        program = ASPInputProgram()
        enc = self._read_encoding()
        program.add_program(enc)

        program.add_program("row(0..{}).".format(state.rows - 1))
        program.add_program("col(0..{}).".format(state.cols - 1))

        # --------------------------
        # 1) Fatti griglia
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

        # --------------------------
        # 2) Fatti opzioni — solo quelle con almeno una mossa legale
        # --------------------------
        valid_solver_indices = []

        for oi, opt in enumerate(current_options):
            # Verifica che almeno una posizione sia legale
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
        # 3) Estrai choose
        # --------------------------
        best = None

        try:
            oas = answer_sets.get_answer_sets()
            for ans in reversed(oas):
                for atom in ans.get_atoms():
                    if isinstance(atom, Choose):
                        best = (atom.get_O(), atom.get_R(), atom.get_C())
                        break
                if best is not None:
                    break
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

        # Fallback
        if best is None:
            best = self._fallback_first_legal(state, current_options)

        if debug:
            print("SCELTA:", best)

        return best

    def _fallback_first_legal(self, state, current_options):
        for oi, opt in enumerate(current_options):
            for r in range(state.rows):
                for c in range(state.cols):
                    if state.can_place_block(opt, r, c):
                        return (oi, r, c)
        return None
