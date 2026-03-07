import os
import re

from embasp.specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from embasp.languages.asp.asp_input_program import ASPInputProgram
from embasp.languages.asp.asp_mapper import ASPMapper
from embasp.platforms.desktop.desktop_handler import DesktopHandler

from ai.asp_predicates import Empty, Occ, Opt, OptOrient, OptSize, OptPiece, Choose


def _extract_choose_from_string(s: str):
    """
    Fallback: prende choose(O,R,C) dall'output testuale del solver.
    Gestisce sia formati con spazi sia senza.
    """
    m = re.search(r"choose\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


class CakeSortASPSolver:
    def __init__(self, project_root: str):
        """
        project_root: cartella che contiene Solvers/ e asp/
        es: CakeSortPuzzle3D/
        """
        self.project_root = project_root
        self.solver_path = os.path.join(project_root, "Solvers", "dlv2.exe")
        self.encoding_path = os.path.join(project_root, "asp", "cakesort_easy.lp")

        if not os.path.exists(self.solver_path):
            raise FileNotFoundError(f"DLV2 non trovato: {self.solver_path}")
        if not os.path.exists(self.encoding_path):
            raise FileNotFoundError(f"Encoding non trovata: {self.encoding_path}")

        self.handler = DesktopHandler(DLV2DesktopService(self.solver_path))

        # Register class mapping (IMPORTANTE: una volta sola)
        mapper = ASPMapper.get_instance()
        mapper.register_class(Empty)
        mapper.register_class(Occ)
        mapper.register_class(Opt)
        mapper.register_class(OptOrient)
        mapper.register_class(OptSize)
        mapper.register_class(OptPiece)
        mapper.register_class(Choose)

    def _read_encoding(self) -> str:
        with open(self.encoding_path, "r", encoding="utf-8") as f:
            return f.read()

    def choose_move(self, state, current_options, debug: bool = False):
        """
        return: (opt_index, r, c) oppure None
        """
        self.handler.remove_all()

        program = ASPInputProgram()
        enc = self._read_encoding()
        program.add_program(enc)

        # (opzionale) aggiungo anche i domini da Python
        # così non dipendi da row(0..4)/col(0..3) nel file lp.
        program.add_program(f"row(0..{state.rows - 1}).")
        program.add_program(f"col(0..{state.cols - 1}).")

        # --------------------------
        # 1) Fatti griglia: empty/occ
        # --------------------------
        empty_count = 0
        occ_count = 0

        for r in range(state.rows):
            for c in range(state.cols):
                if state.grid[r][c] is None:
                    e = Empty()
                    e.set_R(r)
                    e.set_C(c)
                    program.add_object_input(e)
                    empty_count += 1
                else:
                    o = Occ()
                    o.set_R(r)
                    o.set_C(c)
                    program.add_object_input(o)
                    occ_count += 1

        # --------------------------
        # 2) Fatti opzioni (blocchi)
        # --------------------------
        for oi, opt in enumerate(current_options):
            op = Opt()
            op.set_O(oi)
            program.add_object_input(op)

            orient = opt.get("orientation", "NONE")
            if orient == "H":
                orc = "h"
                size = 2
            elif orient == "V":
                orc = "v"
                size = 2
            else:
                orc = "n"
                size = 1

            oo = OptOrient()
            oo.set_O(oi)
            oo.set_OR(orc)
            program.add_object_input(oo)

            osz = OptSize()
            osz.set_O(oi)
            osz.set_S(size)
            program.add_object_input(osz)

            for pi, plate in enumerate(opt["plates"]):
                for piece in plate.pieces:
                    pp = OptPiece()
                    pp.set_O(oi)
                    pp.set_P(pi)
                    pp.set_T(piece.tipo)
                    pp.set_K(piece.count)
                    program.add_object_input(pp)

        self.handler.add_program(program)

        answer_sets = self.handler.start_sync()
        ans_str = answer_sets.get_answer_sets_string()

        # --- DEBUG ---
        if debug:
            print("=== DEBUG INFO ===")
            print("empty:", empty_count, "occ:", occ_count, "options:", len(current_options))
            print("=== ANSWER SETS STRING ===")
            print(ans_str)
            print("==========================")
            print("=== ANSWER SETS RAW OBJECTS ===")
            for a in answer_sets.get_answer_sets():
                print(a)
            print("===============================")

        # --------------------------
        # 3) Estrai choose(O,R,C) via mapping EmbASP
        # --------------------------
        best = None
        oas = answer_sets.get_answer_sets()

        # prendi l'ultimo answer set (tipicamente OPTIMUM)
        for ans in reversed(oas):
            for atom in ans.get_atoms():
                if isinstance(atom, Choose):
                    best = (atom.get_O(), atom.get_R(), atom.get_C())
                    break
            if best is not None:
                break

        if best is None:
            best = _extract_choose_from_string(answer_sets.get_answer_sets_string())

        if debug:
            print("DEBUG GRID:")
            for r in range(state.rows):
                row = []
                for c in range(state.cols):
                    row.append("." if state.grid[r][c] is None else "X")
                print(" ".join(row))

        return best

