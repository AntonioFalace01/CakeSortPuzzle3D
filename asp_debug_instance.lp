% ============================================================
% CELLE E CANDIDATI
% ============================================================
cell(R,C) :- row(R), col(C).
cand(O,R,C) :- opt(O), row(R), col(C).

% ============================================================
% POSIZIONI E COPERTURA
% ============================================================
plate_pos(O,R,C,0,R,C)  :- cand(O,R,C), opt_orient(O,n).
plate_pos(O,R,C,0,R,C)  :- cand(O,R,C), opt_orient(O,h).
plate_pos(O,R,C,1,R,C2) :- cand(O,R,C), opt_orient(O,h), C2=C+1, col(C2).
plate_pos(O,R,C,0,R,C)  :- cand(O,R,C), opt_orient(O,v).
plate_pos(O,R,C,1,R2,C) :- cand(O,R,C), opt_orient(O,v), R2=R+1, row(R2).

covers(O,R,C,Rp,Cp) :- plate_pos(O,R,C,_,Rp,Cp).

% ============================================================
% LEGALITA'
% ============================================================
illegal(O,R,C) :- cand(O,R,C), opt_orient(O,h), opt_size(O,2), C2=C+1, not col(C2).
illegal(O,R,C) :- cand(O,R,C), opt_orient(O,v), opt_size(O,2), R2=R+1, not row(R2).
illegal(O,R,C) :- cand(O,R,C), covers(O,R,C,R2,C2), not empty(R2,C2).

legal(O,R,C) :- cand(O,R,C), not illegal(O,R,C).

% ============================================================
% SCELTA - esattamente una mossa legale
% ============================================================
{ choose(O,R,C) : legal(O,R,C) }.

some_choose :- choose(_,_,_).
:- not some_choose.

%:- choose(O1,R1,C1), choose(O2,R2,C2), O1 < O2.
%:- choose(O1,R1,C1), choose(O2,R2,C2), O1 = O2, R1 < R2.
%:- choose(O1,R1,C1), choose(O2,R2,C2), O1 = O2, R1 = R2, C1 < C2.
:- #count{ O,R,C : choose(O,R,C) } > 1.
% ============================================================
% VICINI ESTERNI
% ============================================================
ext_neigh(O,R,C,Rn,Cn) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Rn=Rp+1, row(Rn), Cn=Cp, not covers(O,R,C,Rn,Cn).
ext_neigh(O,R,C,Rn,Cn) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Rn=Rp-1, row(Rn), Cn=Cp, not covers(O,R,C,Rn,Cn).
ext_neigh(O,R,C,Rn,Cn) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Cn=Cp+1, col(Cn), Rn=Rp, not covers(O,R,C,Rn,Cn).
ext_neigh(O,R,C,Rn,Cn) :-
    choose(O,R,C), covers(O,R,C,Rp,Cp),
    Cn=Cp-1, col(Cn), Rn=Rp, not covers(O,R,C,Rn,Cn).

% ============================================================
% TIPI E PUREZZA
% ============================================================
type_in_plate(O,P,T) :- opt_piece(O,P,T,K), K > 0.
type_in_opt(O,T)     :- type_in_plate(O,_,T).

pure_plate(O,P) :-
    opt(O), type_in_plate(O,P,_),
    #count{ T2 : type_in_plate(O,P,T2) } = 1.

pure_plate_type(O,P,T) :- pure_plate(O,P), type_in_plate(O,P,T).

pure_opt(O) :-
    opt(O),
    #count{ T : type_in_opt(O,T) } = 1.

neighbor_pure(R,C,T) :-
    occ(R,C), occ_type(R,C,T),
    #count{ T2 : occ_type(R,C,T2) } = 1.

% ============================================================
% MATCH DIRETTO
% ============================================================
direct_match(O,R,C,P,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,_,_),
    type_in_plate(O,P,T),
    ext_neigh(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

some_direct_match(O,R,C) :- direct_match(O,R,C,_,_).

% Tocca almeno un vicino occupato (qualsiasi tipo)
touches_any(O,R,C) :-
    choose(O,R,C),
    ext_neigh(O,R,C,Rn,Cn),
    occ(Rn,Cn).

% ============================================================
% QUANTITA' PORTATE E PRESENTI NEI VICINI
% ============================================================
brings(O,R,C,P,T,K) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,_,_),
    opt_piece(O,P,T,K), K > 0.

neighbor_has(O,R,C,P,T,Rn,Cn,Kn) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,_,_),
    ext_neigh(O,R,C,Rn,Cn),
    occ_count(Rn,Cn,T,Kn),
    type_in_plate(O,P,T).

% ============================================================
% COMPLETAMENTO
% ============================================================
brings_sum(O,R,C,T,SB) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    SB = #sum{ K,P : brings(O,R,C,P,T,K) }.

neighbor_sum(O,R,C,T,SN) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    SN = #sum{ Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn) }.

total_sum(O,R,C,T,S) :-
    brings_sum(O,R,C,T,SB),
    neighbor_sum(O,R,C,T,SN),
    S = SB + SN.

can_complete(O,R,C)    :- total_sum(O,R,C,_,S), S >= 6.
will_complete(O,R,C)   :- can_complete(O,R,C).
almost_complete(O,R,C) :- total_sum(O,R,C,_,S), S >= 4, S < 6.

% ============================================================
% CONSOLIDAMENTO - senza #max, versione safe per DLV2
% ============================================================
has_neighbor_type(O,R,C,T) :-
    choose(O,R,C),
    type_in_opt(O,T),
    ext_neigh(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

% Predicato ausiliario safe per la negazione (no _ in not)
has_any_neighbor_type(O,R,C) :- has_neighbor_type(O,R,C,_).

nearby_same(O,R,C,T,SN) :-
    has_neighbor_type(O,R,C,T),
    SN = #sum{ Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn) }.

good_consolidation(O,R,C) :-
    nearby_same(O,R,C,_,SN), SN >= 3.

poor_consolidation(O,R,C) :-
    choose(O,R,C),
    has_any_neighbor_type(O,R,C),
    not good_consolidation(O,R,C).

no_consolidation(O,R,C) :-
    choose(O,R,C),
    not has_any_neighbor_type(O,R,C).

% ============================================================
% PURE MATCH
% ============================================================
pure_touch(O,R,C) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,_,_),
    type_in_plate(O,P,T),
    ext_neigh(O,R,C,Rn,Cn),
    neighbor_pure(Rn,Cn,T).

pure_plate_matches(O,R,C) :-
    choose(O,R,C),
    pure_plate(O,P),
    pure_plate_type(O,P,T),
    plate_pos(O,R,C,P,_,_),
    ext_neigh(O,R,C,Rn,Cn),
    neighbor_pure(Rn,Cn,T).

% ============================================================
% SPAZIO LIBERO
% ============================================================
free_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{ Rf,Cf : cell(Rf,Cf),
                        not occ(Rf,Cf),
                        not covers(O,R,C,Rf,Cf) }.

fragmented_space(O,R,C) :-
    choose(O,R,C),
    free_count(O,R,C,N), N < 3.

creates_space(O,R,C) :- will_complete(O,R,C).

% ============================================================
% ANTI-BLOCK
% ============================================================
near_complete_cell(R,C,T) :- occ_count(R,C,T,K), K >= 4, K < 6.

vital_space(Rn,Cn,T) :-
    near_complete_cell(R,C,T), empty(Rn,Cn),
    Rn=R+1, Cn=C, row(Rn), col(Cn).
vital_space(Rn,Cn,T) :-
    near_complete_cell(R,C,T), empty(Rn,Cn),
    Rn=R-1, Cn=C, row(Rn), col(Cn).
vital_space(Rn,Cn,T) :-
    near_complete_cell(R,C,T), empty(Rn,Cn),
    Rn=R, Cn=C+1, row(Rn), col(Cn).
vital_space(Rn,Cn,T) :-
    near_complete_cell(R,C,T), empty(Rn,Cn),
    Rn=R, Cn=C-1, row(Rn), col(Cn).

blocks_vital(O,R,C,T) :-
    choose(O,R,C),
    covers(O,R,C,Rp,Cp),
    vital_space(Rp,Cp,T),
    not type_in_opt(O,T).

% ============================================================
% CENTRALITA' - pesi statici per griglia 5x4
% Centro: (2,1) e (2,2) hanno peso 0
% Angoli: peso 6
% DLV2 minimizza -> preferisce peso basso -> preferisce centro
% ============================================================
cell_weight(0,0,6). cell_weight(0,1,4). cell_weight(0,2,4). cell_weight(0,3,6).
cell_weight(1,0,4). cell_weight(1,1,1). cell_weight(1,2,1). cell_weight(1,3,4).
cell_weight(2,0,3). cell_weight(2,1,0). cell_weight(2,2,0). cell_weight(2,3,3).
cell_weight(3,0,4). cell_weight(3,1,1). cell_weight(3,2,1). cell_weight(3,3,4).
cell_weight(4,0,6). cell_weight(4,1,4). cell_weight(4,2,4). cell_weight(4,3,6).

placement_weight(O,R,C,W) :-
    choose(O,R,C),
    W = #sum{ Wc,Rp,Cp : covers(O,R,C,Rp,Cp), cell_weight(Rp,Cp,Wc) }.

% ============================================================
% GUARDIA: la griglia non e' vuota
% Serve per non penalizzare le prime mosse dove non ci sono
% vicini ne' match possibili
% ============================================================
grid_not_empty :- occ(_,_).

% ============================================================
% VINCOLI DEBOLI
%
% Gerarchia priorita' (decrescente):
%   @13  blocca spazio vitale senza completare  <- piu' grave
%   @12  non completa nessuna torta
%   @11  non quasi-completa neanche
%   @10  nessun match diretto di tipo
%   @9   non tocca nessun vicino (mossa isolata)
%   @8   nessun pure_plate_match
%   @7   nessun pure_touch
%   @6   consolidamento nullo o scarso
%   @5   completa ma non libera spazio
%   @4   spazio critico post-piazzamento
%   @3   posizione periferica (peso statico)
%   @2   opzione non pura
% ============================================================

% P13 - Occupa spazio vitale di torta quasi completa col tipo sbagliato
:~ choose(O,R,C), blocks_vital(O,R,C,T), not can_complete(O,R,C).      [90@13,O,R,C,T]

% P12 - Non completa nessuna torta
:~ choose(O,R,C), not can_complete(O,R,C).                              [80@12,O,R,C]

% P11 - Non si avvicina nemmeno a un completamento (total < 4)
:~ choose(O,R,C), not will_complete(O,R,C), not almost_complete(O,R,C). [50@11,O,R,C]

% P10 - Nessun match diretto (solo se griglia non vuota)
:~ choose(O,R,C), grid_not_empty, not some_direct_match(O,R,C).         [30@10,O,R,C]

% P9 - Non tocca nessun vicino occupato (solo se griglia non vuota)
:~ choose(O,R,C), grid_not_empty, not touches_any(O,R,C).               [25@9,O,R,C]

% P8 - Nessuna plate pura tocca cella pura compatibile
:~ choose(O,R,C), grid_not_empty, not pure_plate_matches(O,R,C).        [20@8,O,R,C]

% P7 - Nessun contatto con cella pura dello stesso tipo
:~ choose(O,R,C), grid_not_empty, not pure_touch(O,R,C).                [15@7,O,R,C]

% P6 - Consolidamento scarso (vicini dello stesso tipo ma pochi)
:~ choose(O,R,C), grid_not_empty, poor_consolidation(O,R,C).            [15@6,O,R,C]

% P6 - Nessun vicino dello stesso tipo (consolidamento zero)
:~ choose(O,R,C), grid_not_empty, no_consolidation(O,R,C).              [25@6,O,R,C]

% P5 - Completa ma non libera spazio
:~ choose(O,R,C), can_complete(O,R,C), not creates_space(O,R,C).        [10@5,O,R,C]

% P4 - Spazio critico: meno di 3 celle libere dopo il piazzamento
:~ fragmented_space(O,R,C).                                             [10@4,O,R,C]

% P3 - Posizione periferica: peso statico della cella
:~ choose(O,R,C), placement_weight(O,R,C,W), W > 0.                     [W@3,O,R,C]

% P2 - Opzione non pura (piu' tipi = piu' entropia)
:~ choose(O,R,C), not pure_opt(O).                                       [5@2,O,R,C]

#show choose/3.
row(0..4).
col(0..3).
occ(0,0).
occ_type(0,0,c).
occ_count(0,0,c,1).
empty(0,1).
empty(0,2).
empty(0,3).
occ(1,0).
occ_type(1,0,s).
occ_count(1,0,s,2).
occ_type(1,0,v).
occ_count(1,0,v,1).
empty(1,1).
empty(1,2).
empty(1,3).
empty(2,0).
empty(2,1).
empty(2,2).
empty(2,3).
occ(3,0).
occ_type(3,0,c).
occ_count(3,0,c,4).
empty(3,1).
empty(3,2).
empty(3,3).
empty(4,0).
empty(4,1).
empty(4,2).
empty(4,3).
opt(0).
opt_orient(0,v).
opt_size(0,2).
opt_piece(0,0,c,1).
opt_piece(0,1,c,1).
opt_piece(0,1,s,1).
opt(1).
opt_orient(1,n).
opt_size(1,1).
opt_piece(1,0,s,1).
opt_piece(1,0,v,2).
opt(2).
opt_orient(2,n).
opt_size(2,1).
opt_piece(2,0,v,2).
opt_piece(2,0,s,1).
