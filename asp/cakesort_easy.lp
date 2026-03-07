% =========================
% CakeSort - DLV2 COMPATIBLE
% =========================

cell(R,C) :- row(R), col(C).

% -------------------------
% Dominio delle ancore
% -------------------------
cand(O,R,C) :- opt(O), row(R), col(C).

% -------------------------
% plate_pos: dove finisce ogni piatto del blocco
% -------------------------
plate_pos(O,R,C,0,R,C) :- cand(O,R,C), opt_orient(O,n).

plate_pos(O,R,C,0,R,C)   :- cand(O,R,C), opt_orient(O,h).
plate_pos(O,R,C,1,R,C2)  :- cand(O,R,C), opt_orient(O,h), C2 = C + 1, col(C2).

plate_pos(O,R,C,0,R,C)   :- cand(O,R,C), opt_orient(O,v).
plate_pos(O,R,C,1,R2,C)  :- cand(O,R,C), opt_orient(O,v), R2 = R + 1, row(R2).

% covers per compatibilita
covers(O,R,C,Rp,Cp) :- plate_pos(O,R,C,P,Rp,Cp).

% -------------------------
% Legalita
% -------------------------
bad_bounds(O,R,C) :- cand(O,R,C), opt_orient(O,h), C2 = C + 1, not col(C2).
bad_bounds(O,R,C) :- cand(O,R,C), opt_orient(O,v), R2 = R + 1, not row(R2).
bad_cell(O,R,C) :- cand(O,R,C), covers(O,R,C,R2,C2), not empty(R2,C2).

illegal(O,R,C) :- bad_bounds(O,R,C).
illegal(O,R,C) :- bad_cell(O,R,C).

legal(O,R,C) :- cand(O,R,C), not illegal(O,R,C).

% -------------------------
% Scelta: esattamente 1 mossa
% -------------------------
choose(O,R,C) | not_choose(O,R,C) :- legal(O,R,C).
:- choose(O1,R1,C1), choose(O2,R2,C2), O1 != O2.
:- choose(O1,R1,C1), choose(O1,R2,C2), R1 != R2.
:- choose(O1,R1,C1), choose(O1,R1,C2), C1 != C2.
has_choice :- choose(O,R,C).
:- not has_choice.

% -------------------------
% Vicini delle celle coperte
% -------------------------
neigh_of(O,R,C,Rp,Cp,Rn,Cp) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Rn = Rp+1, row(Rn).
neigh_of(O,R,C,Rp,Cp,Rn,Cp) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Rn = Rp-1, row(Rn).
neigh_of(O,R,C,Rp,Cp,Rp,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Cn = Cp+1, col(Cn).
neigh_of(O,R,C,Rp,Cp,Rp,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Cn = Cp-1, col(Cn).

% -------------------------
% EURISTICA 1: Match di tipo (la piu importante)
% -------------------------
type_in_plate(O,P,T) :- opt_piece(O,P,T,K), K > 0.

has_type_match(O,R,C) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    occ_type(Rn,Cn,T).

% -------------------------
% EURISTICA 2: Adiacenza generica
% -------------------------
has_adj(O,R,C) :- choose(O,R,C), neigh_of(O,R,C,Rp,Cp,Rn,Cn), occ(Rn,Cn).

% -------------------------
% EURISTICA 3: Opzione pura
% -------------------------
type_in_opt(O,T) :- opt_piece(O,P,T,K), K > 0.
two_types(O) :- type_in_opt(O,T1), type_in_opt(O,T2), T1 != T2.
pure_opt(O) :- opt(O), not two_types(O).

% -------------------------
% EURISTICA 4: Forza blocco
% -------------------------
tot(O,S) :- opt(O), S = #sum{K,P,T : opt_piece(O,P,T,K)}.

% =========================================
% WEAK CONSTRAINTS
% =========================================

% @5: Preferisci match di tipo
:~ choose(O,R,C), not has_type_match(O,R,C). [10@5,O,R,C]

% @4: Preferisci adiacenza a occupate
:~ choose(O,R,C), not has_adj(O,R,C). [5@4,O,R,C]

% @3: Preferisci opzioni pure
:~ choose(O,R,C), not pure_opt(O). [3@3,O,R,C]

% @2: Preferisci piu fette
:~ choose(O,R,C), tot(O,S). [-S@2,O,R,C]

#show choose/3.
