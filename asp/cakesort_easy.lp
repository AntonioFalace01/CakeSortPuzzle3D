% =========================
% CakeSort - EASY (DLV2 safe)
% =========================

% Il dominio row/col viene aggiunto anche da Python:
% row(0..4). col(0..3).
% Qui lo lascio comunque nel caso tu voglia usarlo standalone:
% row(0..4). col(0..3).

cell(R,C) :- row(R), col(C).

% Fatti da Python:
% empty(R,C).  occ(R,C).
% opt(O).
% opt_orient(O,h). opt_orient(O,v). opt_orient(O,n).
% opt_piece(O,P,T,K).

% -------------------------
% Dominio delle ancore
% -------------------------
cand(O,R,C) :- opt(O), row(R), col(C).

% -------------------------
% Copertura celle in base all'orientamento (SAFE)
% -------------------------
covers(O,R,C,R,C) :- cand(O,R,C), opt_orient(O,n).

covers(O,R,C,R,C)   :- cand(O,R,C), opt_orient(O,h).
covers(O,R,C,R,C2)  :- cand(O,R,C), opt_orient(O,h), C2 = C + 1, col(C2).

covers(O,R,C,R,C)   :- cand(O,R,C), opt_orient(O,v).
covers(O,R,C,R2,C)  :- cand(O,R,C), opt_orient(O,v), R2 = R + 1, row(R2).

% -------------------------
% Legalità: tutte le celle coperte devono essere vuote
% -------------------------
illegal(O,R,C) :- cand(O,R,C), covers(O,R,C,R2,C2), not empty(R2,C2).
legal(O,R,C) :- cand(O,R,C), not illegal(O,R,C).

% -------------------------
% Scelta mossa: esattamente 1
% -------------------------
{ choose(O,R,C) : legal(O,R,C) } = 1.

% -------------------------
% Euristiche semplici
% -------------------------

% adiacenza a celle occupate (4-dir) per una qualsiasi cella coperta dal blocco
adj_occ(O,R,C) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Rn = Rp + 1, row(Rn), occ(Rn,Cp).
adj_occ(O,R,C) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Rn = Rp - 1, row(Rn), occ(Rn,Cp).
adj_occ(O,R,C) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Cn = Cp + 1, col(Cn), occ(Rp,Cn).
adj_occ(O,R,C) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Cn = Cp - 1, col(Cn), occ(Rp,Cn).

has_adj(O,R,C) :- adj_occ(O,R,C).

% opzione "pura" = compare un solo tipo tra tutti i pezzi dell'opzione
type_in_opt(O,T) :- opt_piece(O,_,T,_).
two_types(O) :- type_in_opt(O,T1), type_in_opt(O,T2), T1 != T2.
pure_opt(O) :- opt(O), not two_types(O).

% "forza" blocco: somma fette nell'opzione
tot(O,S) :- opt(O), S = #sum { K,P,T : opt_piece(O,P,T,K) }.

% -------------------------
% weak constraints (ottimizzazione)
% -------------------------
% 1) preferisci mosse adiacenti a qualcosa
:~ choose(O,R,C), not has_adj(O,R,C). [5@3,O,R,C]

% 2) preferisci opzioni pure
:~ choose(O,R,C), not pure_opt(O). [3@2,O,R,C]

% 3) preferisci opzioni con più fette (massimizza S => minimizza -S)
:~ choose(O,R,C), tot(O,S). [-S@1,O,R,C]

#show choose/3.
