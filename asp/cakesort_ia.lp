% -------------------------------------------------------------
% CELLE E CANDIDATI
% -------------------------------------------------------------
cell(R,C) :- row(R), col(C).
cand(O,R,C) :- opt(O), row(R), col(C).

% -------------------------------------------------------------
% POSIZIONI E COPERTURA
% -------------------------------------------------------------
plate_pos(O,R,C,0,R,C)  :- cand(O,R,C), opt_orient(O,n).
plate_pos(O,R,C,0,R,C)  :- cand(O,R,C), opt_orient(O,h).
plate_pos(O,R,C,1,R,C2) :- cand(O,R,C), opt_orient(O,h), C2=C+1, col(C2).
plate_pos(O,R,C,0,R,C)  :- cand(O,R,C), opt_orient(O,v).
plate_pos(O,R,C,1,R2,C) :- cand(O,R,C), opt_orient(O,v), R2=R+1, row(R2).

covers(O,R,C,Rp,Cp) :- plate_pos(O,R,C,_,Rp,Cp).

% -------------------------------------------------------------
% LEGALITA'
% -------------------------------------------------------------
illegal(O,R,C) :- cand(O,R,C), opt_orient(O,h), opt_size(O,2), C2=C+1, not col(C2).
illegal(O,R,C) :- cand(O,R,C), opt_orient(O,v), opt_size(O,2), R2=R+1, not row(R2).
illegal(O,R,C) :- cand(O,R,C), covers(O,R,C,R2,C2), not empty(R2,C2).

legal(O,R,C) :- cand(O,R,C), not illegal(O,R,C).

% -------------------------------------------------------------
% SCELTA
% -------------------------------------------------------------
choose(O,R,C) | not_choose(O,R,C) :- legal(O,R,C).
:- #count { O,R,C : choose(O,R,C) } != 1.

% -------------------------------------------------------------
% VICINI ESTERNI
% -------------------------------------------------------------
ext_neigh(O,R,C,Rn,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp),
                         Rn=Rp+1, row(Rn), Cn=Cp, not covers(O,R,C,Rn,Cn).
ext_neigh(O,R,C,Rn,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp),
                         Rn=Rp-1, row(Rn), Cn=Cp, not covers(O,R,C,Rn,Cn).
ext_neigh(O,R,C,Rn,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp),
                         Cn=Cp+1, col(Cn), Rn=Rp, not covers(O,R,C,Rn,Cn).
ext_neigh(O,R,C,Rn,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp),
                         Cn=Cp-1, col(Cn), Rn=Rp, not covers(O,R,C,Rn,Cn).

% -------------------------------------------------------------
% TIPI E PUREZZA
% -------------------------------------------------------------
type_in_plate(O,P,T)   :- opt_piece(O,P,T,K), K > 0.
type_in_opt(O,T)       :- type_in_plate(O,_,T).

two_types_in_opt(O)    :- type_in_opt(O,T1), type_in_opt(O,T2), T1 != T2.
pure_opt(O)            :- opt(O), not two_types_in_opt(O).
% Esiste almeno una coppia di tipi diversi nello stesso piatto
two_types_in_plate(O,P) :-
    type_in_plate(O,P,T1),
    type_in_plate(O,P,T2),
    T1 != T2.

% Piatto puro: c'è almeno un tipo, e non ci sono due tipi diversi
pure_plate(O,P) :-
    type_in_plate(O,P,_),
    not two_types_in_plate(O,P).

pure_plate_type(O,P,T) :- pure_plate(O,P), type_in_plate(O,P,T).

% Esistono almeno due tipi diversi nello stesso piatto (R,C)
two_types_in_cell(R,C) :-
    occ_type(R,C,T1),
    occ_type(R,C,T2),
    T1 != T2.

% Cella "pura" se ha almeno un tipo ma non due diversi
cell_pure(R,C) :-
    occ(R,C),
    occ_type(R,C,_),
    not two_types_in_cell(R,C).

% Vicino puro del tipo T
neighbor_pure(Rn,Cn,T) :-
    cell_pure(Rn,Cn),
    occ_type(Rn,Cn,T).

% -------------------------------------------------------------
% MATCH E COMPLETAMENTO
% -------------------------------------------------------------
direct_match(O,R,C,P,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    ext_neigh(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

brings(O,R,C,P,T,K) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    opt_piece(O,P,T,K), K > 0.

neighbor_has(O,R,C,P,T,Rn,Cn,Kn) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    ext_neigh(O,R,C,Rn,Cn),
    occ_count(Rn,Cn,T,Kn),
    type_in_plate(O,P,T).

% Somma solo il contributo che porta il blocco
sb_type(O,R,C,T,SB) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    SB = #sum{ K,P : brings(O,R,C,P,T,K) }.

% Somma solo il contributo già presente nei vicini
sn_type(O,R,C,T,SN) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    SN = #sum{ Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn) }.

% Somma totale SB + SN (DLV2 non fa l’addizione dentro l’aggregato,
% quindi la facciamo in una regola separata senza altri aggregati)
sum_type(O,R,C,T,S) :-
    sb_type(O,R,C,T,SB),
    sn_type(O,R,C,T,SN),
    S = SB + SN.

can_complete(O,R,C) :- sum_type(O,R,C,_,S), S >= 6.
will_complete(O,R,C) :- can_complete(O,R,C).

% -------------------------------------------------------------
% CONSOLIDAMENTO
% -------------------------------------------------------------
nearby_same(O,R,C,T,S) :-
    choose(O,R,C), type_in_opt(O,T),
    S = #sum{Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn)}.

best_consolidation(O,R,C,M) :-
    choose(O,R,C),
    M = #max{S : nearby_same(O,R,C,_,S)}.

% -------------------------------------------------------------
% PURE MATCH
% -------------------------------------------------------------
pure_touch(O,R,C) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    ext_neigh(O,R,C,Rn,Cn),
    neighbor_pure(Rn,Cn,T).

pure_plate_matches(O,R,C) :-
    choose(O,R,C),
    pure_plate(O,P),
    pure_plate_type(O,P,T),
    plate_pos(O,R,C,P,Rp,Cp),
    ext_neigh(O,R,C,Rn,Cn),
    neighbor_pure(Rn,Cn,T).

% -------------------------------------------------------------
% SPAZIO
% -------------------------------------------------------------
free_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{Rf,Cf : cell(Rf,Cf),
                        not occ(Rf,Cf),
                        not covers(O,R,C,Rf,Cf)}.

fragmented_space(O,R,C) :-
    choose(O,R,C),
    free_count(O,R,C,N),
    N < 3,
    grid_crowded,
    not grid_very_crowded.

creates_space(O,R,C) :-
    will_complete(O,R,C).

% -------------------------------------------------------------
% ANTI-BLOCK
% -------------------------------------------------------------
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

% -------------------------------------------------------------
% CENTRALITA'
% -------------------------------------------------------------
dist_center(O,R,C,D) :-
    choose(O,R,C),
    covers(O,R,C,Rp,Cp),
    D = (Rp-2)*(Rp-2) + (Cp-2)*(Cp-2).

min_dist_center(O,R,C,MD) :-
    choose(O,R,C),
    MD = #min{D : dist_center(O,R,C,D)}.

% -------------------------------------------------------------
% BRIDGE / COLLEGAMENTI TRA GRUPPI DELLO STESSO TIPO
% -------------------------------------------------------------

has_type(R,C,T) :- occ_type(R,C,T).

neigh_has_type(R,C,Rn,Cn,T) :-
    has_type(R,C,T),
    Rn = R+1, Cn = C, row(Rn), col(Cn), has_type(Rn,Cn,T).

neigh_has_type(R,C,Rn,Cn,T) :-
    has_type(R,C,T),
    Rn = R-1, Cn = C, row(Rn), col(Cn), has_type(Rn,Cn,T).

neigh_has_type(R,C,Rn,Cn,T) :-
    has_type(R,C,T),
    Rn = R, Cn = C+1, row(Rn), col(Cn), has_type(Rn,Cn,T).

neigh_has_type(R,C,Rn,Cn,T) :-
    has_type(R,C,T),
    Rn = R, Cn = C-1, row(Rn), col(Cn), has_type(Rn,Cn,T).

pos_with_type(O,R,C,Rp,Cp,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,_,Rp,Cp),
    type_in_opt(O,T).

bridge_pure_mixed(O,R,C,T) :-
    choose(O,R,C),
    pos_with_type(O,R,C,Rp,Cp,T),
    ext_neigh(O,R,C,Rp1,Cp1),
    cell_pure(Rp1,Cp1),
    occ_type(Rp1,Cp1,T),
    ext_neigh(O,R,C,Rp2,Cp2),
    Rp2 != Rp1,
    Cp2 != Cp1,
    occ_type(Rp2,Cp2,T),
    not cell_pure(Rp2,Cp2).

bridge_two_groups(O,R,C,T) :-
    choose(O,R,C),
    pos_with_type(O,R,C,Rp,Cp,T),
    2 <= #count { Rn,Cn :
        ext_neigh(O,R,C,Rn,Cn),
        occ_type(Rn,Cn,T)
    }.

:~ choose(O,R,C), bridge_pure_mixed(O,R,C,T). [-15@6,O,R,C,T]
:~ choose(O,R,C), bridge_two_groups(O,R,C,T). [-10@6,O,R,C,T]

% -------------------------------------------------------------
% VINCOLI DEBOLI
% -------------------------------------------------------------
:~ choose(O,R,C), not can_complete(O,R,C).                      [80@11,O,R,C]
:~ choose(O,R,C), can_complete(O,R,C), not creates_space(O,R,C). [20@10,O,R,C]

:~ choose(O,R,C), blocks_vital(O,R,C,T), not can_complete(O,R,C). [60@13,O,R,C,T]

some_direct_match(O,R,C) :-
    direct_match(O,R,C,P,T).

:~ choose(O,R,C), not some_direct_match(O,R,C). [15@7,O,R,C]

:~ choose(O,R,C), best_consolidation(O,R,C,M), M = 0.           [25@7,O,R,C]
:~ choose(O,R,C), best_consolidation(O,R,C,M), M < 4.           [10@6,O,R,C]

:~ choose(O,R,C), not pure_plate_matches(O,R,C).                [30@9,O,R,C]
:~ choose(O,R,C), not pure_touch(O,R,C).                        [20@8,O,R,C]

:~ fragmented_space(O,R,C).                                      [20@5,O,R,C]

:~ choose(O,R,C), min_dist_center(O,R,C,MD), MD > 2.            [3@3,O,R,C]

:~ choose(O,R,C), pure_opt(O).                                  [-5@2,O,R,C]

#show choose/3.