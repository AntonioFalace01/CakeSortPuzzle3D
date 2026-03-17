% =============================================================
% CakeSort AI — VERSIONE "ANTI-BLOCK" (SURVIVAL PRO)
% =============================================================

cell(R,C) :- row(R), col(C).
cand(O,R,C) :- opt(O), row(R), col(C).

plate_pos(O,R,C,0,R,C) :- cand(O,R,C), opt_orient(O,n).
plate_pos(O,R,C,0,R,C) :- cand(O,R,C), opt_orient(O,h).
plate_pos(O,R,C,1,R,C2) :- cand(O,R,C), opt_orient(O,h), C2 = C + 1, col(C2).
plate_pos(O,R,C,0,R,C) :- cand(O,R,C), opt_orient(O,v).
plate_pos(O,R,C,1,R2,C) :- cand(O,R,C), opt_orient(O,v), R2 = R + 1, row(R2).

covers(O,R,C,Rp,Cp) :- plate_pos(O,R,C,_,Rp,Cp).

% --- Vincoli di Integrità ---
illegal(O,R,C) :- cand(O,R,C), opt_orient(O,h), opt_size(O,2), C2 = C + 1, not col(C2).
illegal(O,R,C) :- cand(O,R,C), opt_orient(O,v), opt_size(O,2), R2 = R + 1, not row(R2).
illegal(O,R,C) :- cand(O,R,C), covers(O,R,C,R2,C2), not empty(R2,C2).

legal(O,R,C) :- cand(O,R,C), not illegal(O,R,C).
choose(O,R,C) | not_choose(O,R,C) :- legal(O,R,C).
:- not has_choice, has_legal_moves.
has_choice :- choose(_,_,_).
has_legal_moves :- legal(_,_,_).
:- choose(O1,R1,C1), choose(O2,R2,C2), (O1,R1,C1) != (O2,R2,C2).

% --- Logica di Analisi Avanzata ---
ext_neigh(O,R,C,Rn,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp),
    (Rn=Rp+1, Cn=Cp; Rn=Rp-1, Cn=Cp; Rn=Rp, Cn=Cp+1; Rn=Rp, Cn=Cp-1),
    row(Rn), col(Cn), not covers(O,R,C,Rn,Cn).

type_in_opt(O,T) :- opt_piece(O,_,T,K), K > 0.

potential_sum(O,R,C,T,S) :- choose(O,R,C), type_in_opt(O,T),
    S = #sum{K,P : opt_piece(O,P,T,K)} + #sum{Kn,Rn,Cn : ext_neigh(O,R,C,Rn,Cn), occ_count(Rn,Cn,T,Kn)}.

will_complete(O,R,C) :- potential_sum(O,R,C,T,S), S >= 6.

% Definizione di "Piatto Quasi Completo" (già sulla griglia)
is_near_complete(R,C,T) :- occ_count(R,C,T,K), K >= 4, K < 6.

% Una cella è "vitale" se è l'unico spazio libero per completare una torta vicina
is_vital_space(Rn,Cn,T) :- is_near_complete(R,C,T), empty(Rn,Cn),
    (Rn=R+1, Cn=C; Rn=R-1, Cn=C; Rn=R, Cn=C+1; Rn=R, Cn=C-1).

% =============================================================
% WEAK CONSTRAINTS - GERARCHIA REVISIONATA
% =============================================================

% @15: CHIUDERE È VIVERE.
:~ choose(O,R,C), will_complete(O,R,C). [-10000 @15, O,R,C]

% @13: PROTEZIONE SPAZI VITALI (L'ANTI-BLOCCO).
% Se occupi una cella vicina a una torta quasi pronta (T) con un pezzo che NON contiene T,
% ricevi una penalità altissima. Non murare le torte degli altri!
:~ choose(O,R,C), covers(O,R,C,Rp,Cp), is_vital_space(Rp,Cp,T), not type_in_opt(O,T). [7000 @13, O,R,C,T]

% @12: SOPRAVVIVENZA.
:~ choose(O,R,C), total_free(F), F <= 4, not will_complete(O,R,C). [5000 @12, O,R,C]

% @10: CLUSTERING (COLORE CON COLORE).
:~ choose(O,R,C), type_in_opt(O,T), ext_neigh(O,R,C,Rn,Cn), occ_type(Rn,Cn,T2), T != T2. [1500 @10, O,R,C]

% @8: CONSOLIDAMENTO.
:~ choose(O,R,C), potential_sum(O,R,C,T,S), S < 6. [ (6-S)*300 @8, O,R,C,T]

% @6: ANTI-DISPERSIONE.
remote_type(O,R,C,T) :- choose(O,R,C), type_in_opt(O,T), occ_type(R2,C2,T), not ext_neigh(O,R,C,R2,C2).
:~ remote_type(O,R,C,T). [800 @6, O,R,C,T]

% @1: QUANTITÀ.
tot_slices(O,S) :- opt(O), S = #sum{K,P : opt_piece(O,P,T,K)}.
:~ choose(O,R,C), tot_slices(O,S). [-S @1, O,R,C]

#show choose/3.