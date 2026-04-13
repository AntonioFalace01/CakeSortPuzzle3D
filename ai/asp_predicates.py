from embasp.languages.predicate import Predicate
from embasp.languages.asp.symbolic_constant import SymbolicConstant

# cella vuota nella griglia
class Empty(Predicate):
    predicate_name = "empty"

    def __init__(self):
        self.R = 0
        self.C = 0
        super().__init__([("R", int), ("C", int)])

    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v

# cella occupata nella griglia
class Occ(Predicate):
    predicate_name = "occ"

    def __init__(self):
        self.R = 0
        self.C = 0
        super().__init__([("R", int), ("C", int)])

    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v

# indica che nella cella r,c c'è almeno un pezzo di tipo T
class OccType(Predicate):
    predicate_name = "occ_type"

    def __init__(self):
        self.R = 0
        self.C = 0
        self.T = SymbolicConstant("")
        super().__init__([("R", int), ("C", int), ("T", SymbolicConstant)])

    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v
    def get_T(self): return self.T
    def set_T(self, v): self.T = SymbolicConstant(v)

# opzione di piazzamento
class Opt(Predicate):
    predicate_name = "opt"

    def __init__(self):
        self.O = 0
        super().__init__([("O", int)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v

# opzione o ha orientamento OR
class OptOrient(Predicate):
    predicate_name = "opt_orient"

    def __init__(self):
        self.O = 0
        self.OR = SymbolicConstant("")
        super().__init__([("O", int), ("OR", SymbolicConstant)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v
    def get_OR(self): return self.OR
    def set_OR(self, v): self.OR = SymbolicConstant(v)

# opzione o ha dimensione S
class OptSize(Predicate):
    predicate_name = "opt_size"

    def __init__(self):
        self.O = 0
        self.S = 1
        super().__init__([("O", int), ("S", int)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v
    def get_S(self): return self.S
    def set_S(self, v): self.S = v

# contenuto dell'opzione: pezzo di tipo T e conteggio K
class OptPiece(Predicate):
    predicate_name = "opt_piece"

    def __init__(self):
        self.O = 0
        self.P = 0
        self.T = SymbolicConstant("")
        self.K = 0
        super().__init__([("O", int), ("P", int), ("T", SymbolicConstant), ("K", int)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v
    def get_P(self): return self.P
    def set_P(self, v): self.P = v
    def get_T(self): return self.T
    def set_T(self, v): self.T = SymbolicConstant(v)
    def get_K(self): return self.K
    def set_K(self, v): self.K = v

# mossa scelta
class Choose(Predicate):
    predicate_name = "choose"

    def __init__(self):
        self.O = 0
        self.R = 0
        self.C = 0
        super().__init__([("O", int), ("R", int), ("C", int)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v
    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v

# cella r,c contiene K pezzi di tipo T
class OccCount(Predicate):
    predicate_name = "occ_count"

    def __init__(self):
        self.R = 0
        self.C = 0
        self.T = SymbolicConstant("")
        self.K = 0
        super().__init__([("R", int), ("C", int), ("T", SymbolicConstant), ("K", int)])

    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v
    def get_T(self): return self.T
    def set_T(self, v): self.T = SymbolicConstant(v)
    def get_K(self): return self.K
    def set_K(self, v): self.K = v