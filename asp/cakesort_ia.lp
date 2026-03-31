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
1 { choose(O,R,C) : legal(O,R,C) } 1.

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

pure_plate(O,P)        :- type_in_plate(O,P,_),
                         not (type_in_plate(O,P,T1), type_in_plate(O,P,T2), T1 != T2).
pure_plate_type(O,P,T) :- pure_plate(O,P), type_in_plate(O,P,T).

neighbor_pure(Rn,Cn,T) :- occ(Rn,Cn), occ_type(Rn,Cn,T),
                         not (occ_type(Rn,Cn,T1), occ_type(Rn,Cn,T2), T1 != T2).

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

sum_type(O,R,C,T,S) :-
    choose(O,R,C), direct_match(O,R,C,_,T),
    S = #sum{K,P      : brings(O,R,C,P,T,K)}
      + #sum{Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn)}.

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
    N < 6.

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
% FINISHER
% -------------------------------------------------------------
finishes_big(O,R,C) :-
    sum_type(O,R,C,T,S),
    S >= 6.

% -------------------------------------------------------------
% VINCOLI DEBOLI
% -------------------------------------------------------------
:~ choose(O,R,C), not can_complete(O,R,C).                      [80@11,O,R,C]
:~ choose(O,R,C), can_complete(O,R,C), not creates_space(O,R,C). [20@10,O,R,C]

:~ choose(O,R,C), blocks_vital(O,R,C,T), not can_complete(O,R,C). [60@13,O,R,C,T]

:~ choose(O,R,C), not direct_match(O,R,C,_,_).                  [15@7,O,R,C]

:~ choose(O,R,C), best_consolidation(O,R,C,M), M = 0.           [25@7,O,R,C]
:~ choose(O,R,C), best_consolidation(O,R,C,M), M < 4.           [10@6,O,R,C]

:~ choose(O,R,C), not pure_plate_matches(O,R,C).                [30@9,O,R,C]
:~ choose(O,R,C), not pure_touch(O,R,C).                        [20@8,O,R,C]

:~ fragmented_space(O,R,C).                                     [20@9,O,R,C]

:~ choose(O,R,C), min_dist_center(O,R,C,MD), MD > 2.            [3@3,O,R,C]

:~ not finishes_big(O,R,C), can_complete(O,R,C).                [10@10,O,R,C]

:~ choose(O,R,C), pure_opt(O).                                  [-5@2,O,R,C]

#show choose/3.