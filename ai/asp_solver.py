import os
import re
import subprocess

from embasp.specializations.dlv2.desktop.dlv2_desktop_service import DLV2DesktopService
from embasp.base.input_program import InputProgram
from embasp.platforms.desktop.desktop_handler import DesktopHandler


# Mappa tipi logici (C,S,V,...) -> costanti ASP minuscole (c,s,v,...)
TYPE_MAP = {
    "C": "c",
    "S": "s",
    "V": "v",
    "L": "l",
    "A": "a",

    "B": "b",
    "D": "d",
    "E": "e",
}

def _extract_choose_from_string(s: str):
    """Estrae l'ultima mossa choose(O,R,C) da una stringa, se presente."""
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

        self.handler = DesktopHandler(DLV2DesktopService(self.solver_path))
        self._facts_debug_text = ""

    def _read_encoding(self) -> str:
        with open(self.encoding_path, "r", encoding="utf-8") as f:
            return f.read()

    def debug_run_dlv2_file(self, instance_path: str):
        cmd = [self.solver_path, instance_path]
        print("[DEBUG] Eseguo:", " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        #print("------ STDOUT DLV2 ------")
        #print(out)
        #print("------ STDERR DLV2 ------")
        #print(err)
        #print("Exit code:", proc.returncode)

    def choose_move(self, state, current_options, debug=False):
        self.handler.remove_all()

        program = InputProgram()
        enc = self._read_encoding()
        program.add_program(enc)

        self._facts_debug_text = ""

        # domini griglia
        fact = f"row(0..{state.rows - 1})."
        program.add_program(fact)
        self._facts_debug_text += fact + "\n"

        fact = f"col(0..{state.cols - 1})."
        program.add_program(fact)
        self._facts_debug_text += fact + "\n"

        # griglia: empty/occ + occ_type/occ_count
        for r in range(state.rows):
            for c in range(state.cols):
                plate = state.grid[r][c]
                print(f"[DEBUG GRID] ({r},{c}) = {'OCC' if plate is not None else 'empty'}")
                if plate is None:
                    fact = f"empty({r},{c})."
                    program.add_program(fact)
                    self._facts_debug_text += fact + "\n"
                else:
                    fact = f"occ({r},{c})."
                    program.add_program(fact)
                    self._facts_debug_text += fact + "\n"
                    for piece in plate.pieces:
                        if piece.count > 0:
                            t = TYPE_MAP.get(piece.tipo, piece.tipo.lower())
                            fact = f"occ_type({r},{c},{t})."
                            program.add_program(fact)
                            self._facts_debug_text += fact + "\n"
                            fact = f"occ_count({r},{c},{t},{piece.count})."
                            program.add_program(fact)
                            self._facts_debug_text += fact + "\n"

        valid_solver_indices = []

        # opzioni
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

            fact = f"opt({oi})."
            program.add_program(fact)
            self._facts_debug_text += fact + "\n"

            orient = opt.get("orientation", "NONE")
            if orient == "H":
                orc = "h"
            elif orient == "V":
                orc = "v"
            else:
                orc = "n"
            fact = f"opt_orient({oi},{orc})."
            program.add_program(fact)
            self._facts_debug_text += fact + "\n"

            fact = f"opt_size({oi},{len(opt['plates'])})."
            program.add_program(fact)
            self._facts_debug_text += fact + "\n"

            for pi, plate_obj in enumerate(opt["plates"]):
                for piece in plate_obj.pieces:
                    if piece.count > 0:
                        t = TYPE_MAP.get(piece.tipo, piece.tipo.lower())
                        fact = f"opt_piece({oi},{pi},{t},{piece.count})."
                        program.add_program(fact)
                        self._facts_debug_text += fact + "\n"

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
                f.write(self._facts_debug_text)
            #print(f"[AI] Programma ASP scritto in: {tmp_path}")
            #print("=== PROGRAMMA ASP COMPLETO (encoding + fatti) ===")
            #print(enc)
            #print(self._facts_debug_text)
            #print("=== FINE PROGRAMMA COMPLETO ===")
            # Per vedere subito errori sintattici DLV2, puoi decommentare:
            # self.debug_run_dlv2_file(tmp_path)

        self.handler.add_program(program)
        answer_sets = self.handler.start_sync()
        ans_str = answer_sets.get_answer_sets_string()

        if debug:
            print("=== RAW OUTPUT DLV2 (via EmbASP) ===")
            print(ans_str)
            print("=======================")

        best = None
        source = None

        # prova a leggere choose(...) dall'output
        best = _extract_choose_from_string(ans_str)
        if best is not None:
            source = "ASP-regex"
            if debug:
                print(f"[AI] Candidato da ASP (regex): {best}")
        else:
            if debug:
                print("[AI] Nessun choose(...) trovato nell'output DLV2")

        # controllo legalità
        if best is not None:
            oi, r, c = best
            if oi < len(current_options):
                if not state.can_place_block(current_options[oi], r, c):
                    if debug:
                        print(f"[AI] Mossa {best} proposta da {source} ma illegale -> annullata")
                    best = None
                    source = None
            else:
                if debug:
                    print(f"[AI] Mossa {best} proposta da {source} ma O fuori range -> annullata")
                best = None
                source = None

        if debug:
            print(f"[AI] SCELTA FINALE: {best} (source={source})")

        return best

