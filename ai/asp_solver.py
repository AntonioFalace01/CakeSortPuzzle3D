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
            print(f"[AI] Programma ASP scritto in: {tmp_path}")
            print("=== PROGRAMMA ASP COMPLETO (encoding + fatti) ===")
            print(enc)
            print(self._facts_debug_text)
            print("=== FINE PROGRAMMA COMPLETO ===")
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

        # fallback se ASP non dà nulla di valido
        if best is None:
            if debug:
                print("[AI] Nessuna mossa valida da ASP -> uso fallback_smart (solo Python).")
            best = self._fallback_smart(state, current_options)
            source = "fallback-smart"

        if debug:
            print(f"[AI] SCELTA FINALE: {best} (source={source})")

        return best


    def _evaluate_move(self, state, current_options, move):
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

        types_in_grid = set()
        for rr in range(state.rows):
            for cc in range(state.cols):
                pl = state.grid[rr][cc]
                if pl:
                    for piece in pl.pieces:
                        types_in_grid.add(piece.tipo)

        option_types = set()
        for plate_obj in plates:
            for piece in plate_obj.pieces:
                if piece.count > 0:
                    option_types.add(piece.tipo)

        is_useless = bool(types_in_grid) and option_types.isdisjoint(types_in_grid)

        if is_useless:
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
                score -= 300
            else:
                score += 20
            return score

        total_cells = state.rows * state.cols
        occupied = sum(
            1
            for rr in range(state.rows)
            for cc in range(state.cols)
            if state.grid[rr][cc] is not None
        )
        free_cells = total_cells - occupied
        occupancy_ratio = occupied / total_cells

        new_plates_count = len(positions)
        free_after = free_cells - new_plates_count
        if free_after <= 2:
            score -= 200
        elif free_after <= 4:
            score -= 80
        elif free_after <= 6:
            score -= 30

        pressure_bonus = 0
        if occupancy_ratio >= 0.6:
            pressure_bonus = 30
        if occupancy_ratio >= 0.75:
            pressure_bonus = 60

        types_brought = {}
        for plate_obj in plates:
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

                for piece in plate_obj.pieces:
                    np = neighbor.get_piece(piece.tipo)
                    if np is not None:
                        score += 30

                        total = np.count + piece.count
                        if total >= 6:
                            score += 100 + pressure_bonus
                            can_complete_any = True
                        elif total >= 4:
                            score += 40
                        elif total >= 3:
                            score += 15

                        if neighbor.is_pure():
                            score += 25

                        if len(plate_obj.pieces) == 1:
                            score += 15

        if occupancy_ratio >= 0.6 and not can_complete_any:
            score -= 25
        if occupancy_ratio >= 0.75 and not can_complete_any:
            score -= 50

        if len(types_brought) == 1:
            score += 10

        total_slices = sum(types_brought.values())
        score += total_slices * 2

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

        center_r = state.rows / 2.0
        center_c = state.cols / 2.0
        for pr, pc in positions:
            dist = abs(pr - center_r) + abs(pc - center_c)
            if dist <= 1.5:
                score += 5
            elif dist <= 2.5:
                score += 2

        occupied_set = set()
        for rr in range(state.rows):
            for cc in range(state.cols):
                if state.grid[rr][cc] is not None:
                    occupied_set.add((rr, cc))
        for pos in positions:
            occupied_set.add(pos)

        double_slots = 0
        for rr in range(state.rows):
            for cc in range(state.cols):
                if (rr, cc) not in occupied_set:
                    if cc + 1 < state.cols and (rr, cc + 1) not in occupied_set:
                        double_slots += 1
                    if rr + 1 < state.rows and (rr + 1, cc) not in occupied_set:
                        double_slots += 1

        if double_slots == 0 and free_after > 1:
            score -= 40
        elif double_slots <= 2:
            score -= 15

        return score

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
