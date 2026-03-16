% =============================================================
% CakeSort AI — Strategica con gestione spazio (DLV2)
% =============================================================

cell(R,C) :- row(R), col(C).

% ---------------------------------------------------------
% Dominio ancore e posizioni piatti
% ---------------------------------------------------------
cand(O,R,C) :- opt(O), row(R), col(C).

plate_pos(O,R,C,0,R,C) :- cand(O,R,C), opt_orient(O,n).

plate_pos(O,R,C,0,R,C)   :- cand(O,R,C), opt_orient(O,h).
plate_pos(O,R,C,1,R,C2)  :- cand(O,R,C), opt_orient(O,h), C2 = C + 1, col(C2).

plate_pos(O,R,C,0,R,C)   :- cand(O,R,C), opt_orient(O,v).
plate_pos(O,R,C,1,R2,C)  :- cand(O,R,C), opt_orient(O,v), R2 = R + 1, row(R2).

covers(O,R,C,Rp,Cp) :- plate_pos(O,R,C,_,Rp,Cp).

% ---------------------------------------------------------
% Legalita
% ---------------------------------------------------------
bad_bounds(O,R,C) :- cand(O,R,C), opt_orient(O,h), opt_size(O,2), C2 = C + 1, not col(C2).
bad_bounds(O,R,C) :- cand(O,R,C), opt_orient(O,v), opt_size(O,2), R2 = R + 1, not row(R2).
bad_cell(O,R,C)   :- cand(O,R,C), covers(O,R,C,R2,C2), not empty(R2,C2).

illegal(O,R,C) :- bad_bounds(O,R,C).
illegal(O,R,C) :- bad_cell(O,R,C).

legal(O,R,C) :- cand(O,R,C), not illegal(O,R,C).

% ---------------------------------------------------------
% Scelta: esattamente 1 mossa
% ---------------------------------------------------------
choose(O,R,C) | not_choose(O,R,C) :- legal(O,R,C).
:- choose(O1,R1,C1), choose(O2,R2,C2), O1 != O2.
:- choose(O1,R1,C1), choose(O1,R2,C2), R1 != R2.
:- choose(O1,R1,C1), choose(O1,R1,C2), C1 != C2.
has_choice :- choose(_,_,_).
:- not has_choice.

% ---------------------------------------------------------
% Vicini delle celle coperte dalla mossa scelta
% ---------------------------------------------------------
neigh_of(O,R,C,Rp,Cp,Rn,Cp) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Rn = Rp+1, row(Rn).
neigh_of(O,R,C,Rp,Cp,Rn,Cp) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Rn = Rp-1, row(Rn).
neigh_of(O,R,C,Rp,Cp,Rp,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Cn = Cp+1, col(Cn).
neigh_of(O,R,C,Rp,Cp,Rp,Cn) :- choose(O,R,C), covers(O,R,C,Rp,Cp), Cn = Cp-1, col(Cn).

ext_neigh(O,R,C,Rn,Cn) :- neigh_of(O,R,C,_,_,Rn,Cn), not covers(O,R,C,Rn,Cn).

% ---------------------------------------------------------
% Tipi presenti
% ---------------------------------------------------------
type_in_plate(O,P,T) :- opt_piece(O,P,T,K), K > 0.
type_in_opt(O,T)     :- type_in_plate(O,_,T).

two_types_in_opt(O) :- type_in_opt(O,T1), type_in_opt(O,T2), T1 != T2.
pure_opt(O)         :- opt(O), not two_types_in_opt(O).

tot(O,S) :- opt(O), S = #sum{K,P,T : opt_piece(O,P,T,K)}.

% =============================================================
% MATCH TIPO DIRETTO
% =============================================================
direct_match(O,R,C,P,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

has_match(O,R,C) :- direct_match(O,R,C,_,_).

match_count(O,R,C,N) :- choose(O,R,C),
    N = #count{T : direct_match(O,R,C,_,T)}.

% =============================================================
% COMPLETAMENTO TORTA
% =============================================================
brings(O,R,C,P,T,K) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    opt_piece(O,P,T,K), K > 0.

neighbor_has(O,R,C,P,T,Rn,Cn,Kn) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    occ_count(Rn,Cn,T,Kn),
    type_in_plate(O,P,T).

sum_for_type(O,R,C,T,S) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    S = #sum{K,P : brings(O,R,C,P,T,K)} + #sum{Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn)}.

can_complete(O,R,C,T) :- sum_for_type(O,R,C,T,S), S >= 6.
completions(O,R,C,N)  :- choose(O,R,C), N = #count{T : can_complete(O,R,C,T)}.

% =============================================================
% CONSOLIDAMENTO
% =============================================================
nearby_same(O,R,C,T,S) :-
    choose(O,R,C),
    type_in_opt(O,T),
    S = #sum{Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn)}.

best_consolidation(O,R,C,M) :-
    choose(O,R,C),
    M = #max{S : nearby_same(O,R,C,_,S)}.

% =============================================================
% VICINO PURO STESSO TIPO
% =============================================================
has_second_type(R,C) :- occ_type(R,C,T1), occ_type(R,C,T2), T1 != T2.
neighbor_pure_type(Rn,Cn,T) :-
    occ(Rn,Cn), occ_type(Rn,Cn,T),
    not has_second_type(Rn,Cn).

touches_pure_same(O,R,C,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    neighbor_pure_type(Rn,Cn,T).

has_pure_touch(O,R,C) :- touches_pure_same(O,R,C,_).

% =============================================================
% PIATTO PURO CHE MATCHA
% =============================================================
plate_types_count(O,P,N) :- opt(O), N = #count{T : type_in_plate(O,P,T)}.
pure_plate(O,P) :- plate_types_count(O,P,1).
pure_plate_type(O,P,T) :- pure_plate(O,P), type_in_plate(O,P,T).

pure_plate_matches(O,R,C) :-
    choose(O,R,C),
    pure_plate(O,P),
    pure_plate_type(O,P,T),
    plate_pos(O,R,C,P,Rp,Cp),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

% =============================================================
% ISOLAMENTO
% =============================================================
any_occ_neighbor(O,R,C) :-
    choose(O,R,C),
    ext_neigh(O,R,C,Rn,Cn),
    occ(Rn,Cn).

isolated(O,R,C) :- choose(O,R,C), not any_occ_neighbor(O,R,C).
grid_empty :- not occ(_,_).
isolated_penalty(O,R,C) :- isolated(O,R,C), not grid_empty.

% =============================================================
% GESTIONE SPAZIO — celle libere dopo la mossa
% =============================================================
occupied_after(O,R,C,Ra,Ca) :- choose(O,R,C), occ(Ra,Ca).
occupied_after(O,R,C,Rp,Cp) :- choose(O,R,C), covers(O,R,C,Rp,Cp).

free_after(O,R,C,Rf,Cf) :- choose(O,R,C), cell(Rf,Cf), not occupied_after(O,R,C,Rf,Cf).

free_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{Rf,Cf : free_after(O,R,C,Rf,Cf)}.

% Conteggio celle occupate attuali (prima della mossa)
total_occupied(N) :- N = #count{R,C : occ(R,C)}.
total_cells(N) :- N = #count{R,C : cell(R,C)}.

% Griglia quasi piena: piu del 60% occupato
grid_pressure :- total_occupied(Occ), total_cells(Tot), Occ * 10 >= Tot * 6.

% Griglia critica: piu del 75% occupato
grid_critical :- total_occupied(Occ), total_cells(Tot), Occ * 4 >= Tot * 3.

% =============================================================
% MERGE POTENZIALE — la mossa libererà spazio?
% =============================================================
will_free_space(O,R,C) :- can_complete(O,R,C,_).

merge_reduces(O,R,C) :-
    choose(O,R,C),
    pure_plate(O,P),
    pure_plate_type(O,P,T),
    plate_pos(O,R,C,P,Rp,Cp),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    neighbor_pure_type(Rn,Cn,T).

% =============================================================
% CENTRALITA
% =============================================================
dist_center(O,R,C,D) :-
    choose(O,R,C),
    covers(O,R,C,Rp,Cp),
    D1 = Rp - 2, D1abs = D1 * D1,
    D2 = Cp - 2, D2abs = D2 * D2,
    D = D1abs + D2abs.

min_dist_center(O,R,C,MD) :-
    choose(O,R,C),
    MD = #min{D : dist_center(O,R,C,D)}.

% =============================================================
% OPZIONE INUTILE — nessun tipo dell'opzione è presente in griglia
% =============================================================

% Tipo T dell'opzione O è presente da qualche parte nella griglia
opt_type_exists_in_grid(O,T) :-
    opt(O), type_in_opt(O,T), occ_type(_,_,T).

% L'opzione O ha almeno un tipo che esiste in griglia
opt_has_any_match_in_grid(O) :- opt_type_exists_in_grid(O,_).

% L'opzione è completamente inutile: nessuno dei suoi tipi è in griglia
% (ha senso solo se la griglia non è vuota)
useless_opt(O) :- opt(O), not opt_has_any_match_in_grid(O), occ(_,_).

% La mossa scelta usa un'opzione inutile
useless_move(O,R,C) :- choose(O,R,C), useless_opt(O).

% La mossa useless è isolata (nessun vicino occupato)
useless_isolated(O,R,C) :- useless_move(O,R,C), not any_occ_neighbor(O,R,C).

% =============================================================
% WEAK CONSTRAINTS — Bilanciate tra punteggio e sopravvivenza
% =============================================================

% @13: Se l'opzione è inutile, DEVE essere isolata (penalità fortissima se non lo è)
:~ useless_move(O,R,C), not useless_isolated(O,R,C). [150@13,O,R,C]

% @13b: Se l'opzione è inutile ed è isolata, piccolo bonus (penalità negativa)
:~ useless_move(O,R,C), useless_isolated(O,R,C). [-10@13,O,R,C]

% @12: CRITICO — se griglia quasi piena, DEVI liberare spazio
:~ choose(O,R,C), grid_critical, not will_free_space(O,R,C). [80@12,O,R,C]

% @11: PRESSIONE — se griglia sotto pressione, preferisci mosse che liberano
:~ choose(O,R,C), grid_pressure, not will_free_space(O,R,C), not merge_reduces(O,R,C). [40@11,O,R,C]

% @10: COMPLETAMENTO TORTA
:~ choose(O,R,C), completions(O,R,C,0). [50@10,O,R,C]

% @9: PIATTO PURO che matcha vicino
:~ choose(O,R,C), not pure_plate_matches(O,R,C). [20@9,O,R,C]

% @8: TOCCA PURO STESSO TIPO
:~ choose(O,R,C), not has_pure_touch(O,R,C). [15@8,O,R,C]

% @7: MATCH DI TIPO DIRETTO
:~ choose(O,R,C), not has_match(O,R,C). [12@7,O,R,C]

% @6: PIU MATCH DIVERSI
:~ choose(O,R,C), match_count(O,R,C,N), N < 3. [8@6,O,R,C]

% @5: CONSOLIDAMENTO
:~ choose(O,R,C), best_consolidation(O,R,C,M), M < 3. [6@5,O,R,C]

% @4: OPZIONE PURA
:~ choose(O,R,C), not pure_opt(O). [4@4,O,R,C]

% @3: NON ISOLARE (solo per mosse NON inutili)
:~ isolated_penalty(O,R,C), not useless_move(O,R,C). [10@3,O,R,C]

% @2: CELLE LIBERE — penalizza proporzionalmente
:~ choose(O,R,C), free_count(O,R,C,N), N < 8. [5@2,O,R,C]
:~ choose(O,R,C), free_count(O,R,C,N), N < 5. [10@2,O,R,C]
:~ choose(O,R,C), free_count(O,R,C,N), N < 3. [20@2,O,R,C]

% @1: CENTRALITA
:~ choose(O,R,C), min_dist_center(O,R,C,MD), MD > 2. [1@1,O,R,C]

% @0: PIU FETTE
:~ choose(O,R,C), tot(O,S). [-S@0,O,R,C]

#show choose/3.
