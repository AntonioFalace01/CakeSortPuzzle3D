from embasp.languages.predicate import Predicate


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


class OccType(Predicate):
    """occ_type(R, C, T) — la cella (R,C) contiene fette di tipo T."""
    predicate_name = "occ_type"

    def __init__(self):
        self.R = 0
        self.C = 0
        self.T = ""
        super().__init__([("R", int), ("C", int), ("T", str)])

    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v
    def get_T(self): return self.T
    def set_T(self, v): self.T = v


class Opt(Predicate):
    predicate_name = "opt"

    def __init__(self):
        self.O = 0
        super().__init__([("O", int)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v


class OptOrient(Predicate):
    predicate_name = "opt_orient"

    def __init__(self):
        self.O = 0
        self.OR = ""
        super().__init__([("O", int), ("OR", str)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v
    def get_OR(self): return self.OR
    def set_OR(self, v): self.OR = v


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


class OptPiece(Predicate):
    predicate_name = "opt_piece"

    def __init__(self):
        self.O = 0
        self.P = 0
        self.T = ""
        self.K = 0
        super().__init__([("O", int), ("P", int), ("T", str), ("K", int)])

    def get_O(self): return self.O
    def set_O(self, v): self.O = v
    def get_P(self): return self.P
    def set_P(self, v): self.P = v
    def get_T(self): return self.T
    def set_T(self, v): self.T = v
    def get_K(self): return self.K
    def set_K(self, v): self.K = v


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

class OccCount(Predicate):
    """occ_count(R, C, T, K) — la cella (R,C) ha K fette di tipo T."""
    predicate_name = "occ_count"

    def __init__(self):
        self.R = 0
        self.C = 0
        self.T = ""
        self.K = 0
        super().__init__([("R", int), ("C", int), ("T", str), ("K", int)])

    def get_R(self): return self.R
    def set_R(self, v): self.R = v
    def get_C(self): return self.C
    def set_C(self, v): self.C = v
    def get_T(self): return self.T
    def set_T(self, v): self.T = v
    def get_K(self): return self.K
    def set_K(self, v): self.K = v
