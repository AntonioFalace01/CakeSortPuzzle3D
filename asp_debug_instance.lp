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

two_types_in_plate(O,P) :-
    type_in_plate(O,P,T1),
    type_in_plate(O,P,T2),
    T1 != T2.

pure_plate(O,P) :-
    type_in_plate(O,P,_),
    not two_types_in_plate(O,P).

pure_plate_type(O,P,T) :- pure_plate(O,P), type_in_plate(O,P,T).

two_types_in_cell(R,C) :-
    occ_type(R,C,T1),
    occ_type(R,C,T2),
    T1 != T2.

cell_pure(R,C) :-
    occ(R,C),
    occ_type(R,C,_),
    not two_types_in_cell(R,C).

neighbor_pure(Rn,Cn,T) :-
    cell_pure(Rn,Cn),
    occ_type(Rn,Cn,T).

% -------------------------------------------------------------
% TIPI PRESENTI NELLA GRIGLIA
% -------------------------------------------------------------
% Tipi che esistono gia' nella griglia
grid_type(T) :- occ_type(_,_,T).

% Un tipo dell'opzione non ha corrispondenti nella griglia
opt_type_foreign(O,T) :-
    type_in_opt(O,T),
    not grid_type(T).

% Tutti i tipi dell'opzione sono estranei alla griglia
all_types_foreign(O) :-
    opt(O),
    type_in_opt(O,_),
    not has_grid_matching_type(O).

has_grid_matching_type(O) :-
    type_in_opt(O,T),
    grid_type(T).

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

sb_type(O,R,C,T,SB) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    SB = #sum{ K,P : brings(O,R,C,P,T,K) }.

sn_type(O,R,C,T,SN) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    SN = #sum{ Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn) }.

sum_type(O,R,C,T,S) :-
    sb_type(O,R,C,T,SB),
    sn_type(O,R,C,T,SN),
    S = SB + SN.

can_complete(O,R,C) :- sum_type(O,R,C,_,S), S >= 6.
will_complete(O,R,C) :- can_complete(O,R,C).

% -------------------------------------------------------------
% MULTI-MERGE: premia piatti che matchano piu' tipi distinti
% (es. piatto misto A+B adiacente a cella-A e cella-B)
% -------------------------------------------------------------

% Tipi dell'opzione che hanno almeno un match in un vicino esterno
matched_type_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{ T : type_in_opt(O,T), ext_neigh(O,R,C,Rn,Cn), occ_type(Rn,Cn,T) }.

% Matchano almeno 2 tipi distinti con vicini diversi
multi_type_match(O,R,C) :-
    choose(O,R,C),
    matched_type_count(O,R,C,N),
    N >= 2.

% Per i blocchi doppi: entrambe le plate matchano qualcosa
% (plate 0 e plate 1 hanno almeno un vicino con tipo compatibile)
plate0_has_match(O,R,C) :-
    choose(O,R,C),
    type_in_plate(O,0,T),
    ext_neigh(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

plate1_has_match(O,R,C) :-
    choose(O,R,C),
    type_in_plate(O,1,T),
    ext_neigh(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

both_plates_match(O,R,C) :-
    choose(O,R,C),
    opt_size(O,2),
    plate0_has_match(O,R,C),
    plate1_has_match(O,R,C).

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
% ISOLAMENTO DI TIPI ESTRANEI
% (problema 1: piatti non mergiabili messi adiacenti)
% -------------------------------------------------------------

% Un vicino del blocco ha un tipo non presente nell'opzione
neighbor_incompatible_type(O,R,C,Rn,Cn,T) :-
    choose(O,R,C),
    ext_neigh(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T),
    not type_in_opt(O,T).

% Conta quante coppie (vicino, tipo incompatibile) esistono
incompatible_neigh_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{ Rn,Cn,T : neighbor_incompatible_type(O,R,C,Rn,Cn,T) }.

% Penalizza se l'opzione non ha NESSUN tipo compatibile con i vicini
% ma viene comunque messa adiacente ad essi
% (situazione in cui tutti i tipi dell'opt sono estranei alla griglia
%  ma la posizione e' adiacente a celle occupate)
useless_adjacent(O,R,C) :-
    choose(O,R,C),
    all_types_foreign(O),
    incompatible_neigh_count(O,R,C,N),
    N > 0.

% Conta celle occupate adiacenti al blocco
occupied_neigh_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{ Rn,Cn : ext_neigh(O,R,C,Rn,Cn), occ(Rn,Cn) }.

% Blocco isolato: nessun vicino occupato
is_isolated(O,R,C) :-
    choose(O,R,C),
    occupied_neigh_count(O,R,C,0).

% Blocco con tipi estranei e adiacente a celle occupate (nessun merge possibile)
% e' peggio di un blocco isolato
foreign_and_adjacent(O,R,C) :-
    choose(O,R,C),
    all_types_foreign(O),
    occupied_neigh_count(O,R,C,N),
    N > 0.

% -------------------------------------------------------------
% SPAZIO
% -------------------------------------------------------------
free_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{Rf,Cf : cell(Rf,Cf),
                        not occ(Rf,Cf),
                        not covers(O,R,C,Rf,Cf)}.

% Celle totali occupate prima del piazzamento
total_occupied(N) :-
    N = #count{R,C : occ(R,C)}.

% Celle totali della griglia (rows * cols, ricavato dai fatti)
total_cells(N) :-
    N = #count{R,C : row(R), col(C)}.

% Griglia considerata "quasi piena": piu' di meta' occupata
grid_crowded :-
    total_occupied(Occ),
    total_cells(Tot),
    Tot > 0,
    Occ * 2 > Tot.

% Griglia molto piena: piu' di 3/4 occupata
grid_very_crowded :-
    total_occupied(Occ),
    total_cells(Tot),
    Tot > 0,
    Occ * 4 > Tot * 3.

% fragmented_space scatta solo se la griglia NON e' gia' quasi piena
% (soglia assoluta < 6 ha senso solo a meta' partita)
fragmented_space(O,R,C) :-
    choose(O,R,C),
    free_count(O,R,C,N),
    N < 6,
    not grid_crowded.

% Quando la griglia e' quasi piena, soglia piu' bassa (< 3)
fragmented_space(O,R,C) :-
    choose(O,R,C),
    free_count(O,R,C,N),
    N < 3,
    grid_crowded,
    not grid_very_crowded.

% Quando la griglia e' molto piena il vincolo spazio non si applica affatto
% (lascia decidere solo i merge)

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

bridge_two_groups(O,R,C,T) :-
    choose(O,R,C),
    type_in_opt(O,T),
    plate_pos(O,R,C,_,Rp,Cp),
    2 <= #count { Rn,Cn :
        ext_neigh(O,R,C,Rn,Cn),
        occ_type(Rn,Cn,T)
    }.

bridge_pure_mixed(O,R,C,T) :-
    choose(O,R,C),
    type_in_opt(O,T),
    plate_pos(O,R,C,_,Rp,Cp),
    ext_neigh(O,R,C,Rp1,Cp1),
    cell_pure(Rp1,Cp1),
    occ_type(Rp1,Cp1,T),
    ext_neigh(O,R,C,Rp2,Cp2),
    Rp2 != Rp1,
    Cp2 != Cp1,
    occ_type(Rp2,Cp2,T),
    not cell_pure(Rp2,Cp2).

:~ choose(O,R,C), bridge_pure_mixed(O,R,C,T). [-15@6,O,R,C,T]
:~ choose(O,R,C), bridge_two_groups(O,R,C,T). [-10@6,O,R,C,T]

% -------------------------------------------------------------
% VINCOLI DEBOLI (ordinati per priorita')
% -------------------------------------------------------------

% --- Priorita' 13: completamento e blocco vitale ---
:~ choose(O,R,C), not can_complete(O,R,C).                       [80@11,O,R,C]
:~ choose(O,R,C), can_complete(O,R,C), not creates_space(O,R,C). [20@10,O,R,C]
:~ choose(O,R,C), blocks_vital(O,R,C,T), not can_complete(O,R,C). [60@13,O,R,C,T]

% --- Problema 1: piatti estranei adiacenti a celle occupate ---
% Forte penalita' se si mette un tipo estraneo adiacente (non isolato)
:~ choose(O,R,C), foreign_and_adjacent(O,R,C).                   [90@12,O,R,C]

% --- Problema 2 e 3: multi-merge e blocchi doppi ---
% Premio forte per matchare piu' tipi distinti con una sola mossa
:~ choose(O,R,C), not multi_type_match(O,R,C).                   [35@9,O,R,C]

% Premio per blocchi doppi che matchano entrambe le plate
:~ choose(O,R,C), opt_size(O,2), not both_plates_match(O,R,C).   [40@9,O,R,C]

% --- Match diretto ---
some_direct_match(O,R,C) :-
    direct_match(O,R,C,P,T).

:~ choose(O,R,C), not some_direct_match(O,R,C).                  [15@7,O,R,C]

% --- Consolidamento ---
:~ choose(O,R,C), best_consolidation(O,R,C,M), M = 0.            [25@7,O,R,C]
:~ choose(O,R,C), best_consolidation(O,R,C,M), M < 4.            [10@6,O,R,C]

% --- Pure match ---
:~ choose(O,R,C), not pure_plate_matches(O,R,C).                 [30@9,O,R,C]
:~ choose(O,R,C), not pure_touch(O,R,C).                         [20@8,O,R,C]

% --- Spazio ---
:~ fragmented_space(O,R,C).                                      [20@5,O,R,C]

% --- Centralita' ---
:~ choose(O,R,C), min_dist_center(O,R,C,MD), MD > 2.             [3@3,O,R,C]

% --- Opt pura (leggero bonus) ---
:~ choose(O,R,C), pure_opt(O).                                   [-5@2,O,R,C]

% --- Penalita' extra per tipi estranei con molti vicini incompatibili ---
% (rafforza problema 1: piu' vicini incompatibili = peggio)
:~ choose(O,R,C), incompatible_neigh_count(O,R,C,N), N >= 2.    [40@8,O,R,C]
:~ choose(O,R,C), incompatible_neigh_count(O,R,C,N), N >= 1,
   all_types_foreign(O).                                          [70@10,O,R,C]

#show choose/3.
row(0..4).
col(0..3).
occ(0,0).
occ_type(0,0,v).
occ_count(0,0,v,1).
occ(0,1).
occ_type(0,1,b).
occ_count(0,1,b,2).
occ(0,2).
occ_type(0,2,s).
occ_count(0,2,s,1).
occ(0,3).
occ_type(0,3,a).
occ_count(0,3,a,3).
occ(1,0).
occ_type(1,0,b).
occ_count(1,0,b,1).
occ(1,1).
occ_type(1,1,l).
occ_count(1,1,l,1).
occ(1,2).
occ_type(1,2,v).
occ_count(1,2,v,4).
empty(1,3).
empty(2,0).
occ(2,1).
occ_type(2,1,a).
occ_count(2,1,a,5).
empty(2,2).
occ(2,3).
occ_type(2,3,b).
occ_count(2,3,b,2).
occ(3,0).
occ_type(3,0,d).
occ_count(3,0,d,2).
occ_type(3,0,s).
occ_count(3,0,s,2).
occ(3,1).
occ_type(3,1,l).
occ_count(3,1,l,1).
occ(3,2).
occ_type(3,2,c).
occ_count(3,2,c,2).
occ(3,3).
occ_type(3,3,l).
occ_count(3,3,l,2).
occ(4,0).
occ_type(4,0,l).
occ_count(4,0,l,2).
occ(4,1).
occ_type(4,1,v).
occ_count(4,1,v,3).
occ(4,2).
occ_type(4,2,d).
occ_count(4,2,d,1).
occ(4,3).
occ_type(4,3,a).
occ_count(4,3,a,2).
opt(1).
opt_orient(1,n).
opt_size(1,1).
opt_piece(1,0,l,3).
