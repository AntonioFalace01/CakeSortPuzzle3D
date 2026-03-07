import os
from ai.asp_solver import CakeSortASPSolver
from cake_sort_engine import GameState, Plate, Piece


# stato finto: tutto vuoto
state = GameState(5, 4)

# opzioni finte
current_options = [
    {"plates": [Plate([Piece("C", 2)])], "orientation": "NONE"},
    {"plates": [Plate([Piece("S", 1)]), Plate([Piece("S", 2)])], "orientation": "H"},
    {"plates": [Plate([Piece("V", 3)]), Plate([Piece("C", 1)])], "orientation": "V"},
]

BASE = os.path.dirname(os.path.abspath(__file__))
solver = CakeSortASPSolver(BASE)
print(solver.choose_move(state, current_options, debug=True))
