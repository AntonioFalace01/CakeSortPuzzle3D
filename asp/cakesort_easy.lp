% =============================================================
% CakeSort AI — Strategica (DLV2 compatibile)
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

% Vicini esterni (non coperti dalla mossa)
ext_neigh(O,R,C,Rn,Cn) :- neigh_of(O,R,C,_,_,Rn,Cn), not covers(O,R,C,Rn,Cn).

% ---------------------------------------------------------
% Tipi presenti nell'opzione e nella griglia
% ---------------------------------------------------------
type_in_plate(O,P,T) :- opt_piece(O,P,T,K), K > 0.
type_in_opt(O,T)     :- type_in_plate(O,_,T).

% Conteggio fette per tipo in un piatto dell'opzione
slices_in_plate(O,P,T,K) :- opt_piece(O,P,T,K), K > 0.

% Opzione pura (un solo tipo in tutto il blocco)
two_types_in_opt(O) :- type_in_opt(O,T1), type_in_opt(O,T2), T1 != T2.
pure_opt(O)         :- opt(O), not two_types_in_opt(O).

% Totale fette nell'opzione
tot(O,S) :- opt(O), S = #sum{K,P,T : opt_piece(O,P,T,K)}.

% =============================================================
% EURISTICA 1 — Match tipo diretto (piatto tocca vicino stesso tipo)
% =============================================================
direct_match(O,R,C,P,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T).

has_match(O,R,C) :- direct_match(O,R,C,_,_).

% Conta quanti match di tipo diversi ci sono
match_count(O,R,C,N) :- choose(O,R,C),
    N = #count{T : direct_match(O,R,C,_,T)}.

% =============================================================
% EURISTICA 2 — Completamento torta (6 fette stesso tipo raggiungibili)
% =============================================================

% Fette del tipo T che il piatto P porta
brings(O,R,C,P,T,K) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    opt_piece(O,P,T,K), K > 0.

% Fette di tipo T gia presenti in un vicino esterno della cella piazzata
neighbor_has(O,R,C,P,T,Rn,Cn,Kn) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    occ_type(Rn,Cn,T),
    type_in_plate(O,P,T).

% Per ogni tipo T matchato, somma fette portate + fette nei vicini
% Se >= 6 è un completamento!
sum_for_type(O,R,C,T,S) :-
    choose(O,R,C),
    direct_match(O,R,C,_,T),
    S = #sum{K,P : brings(O,R,C,P,T,K)} + #sum{Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn)}.

can_complete(O,R,C,T) :- sum_for_type(O,R,C,T,S), S >= 6.
completions(O,R,C,N)  :- choose(O,R,C), N = #count{T : can_complete(O,R,C,T)}.

% =============================================================
% EURISTICA 3 — Consolidamento (porta fette verso gruppo grande)
% =============================================================

% Fette dello stesso tipo gia raggruppate vicino alla posizione scelta
% (conta quante fette di T ci sono nei vicini esterni)
nearby_same(O,R,C,T,S) :-
    choose(O,R,C),
    type_in_opt(O,T),
    S = #sum{Kn,Rn,Cn : neighbor_has(O,R,C,_,T,Rn,Cn,Kn)}.

% Il massimo raggruppamento ottenibile
best_consolidation(O,R,C,M) :-
    choose(O,R,C),
    M = #max{S : nearby_same(O,R,C,_,S)}.

% =============================================================
% EURISTICA 4 — Vicino puro dello stesso tipo (merge diretto certo)
% =============================================================

% Un vicino è puro di tipo T se ha solo T
neighbor_pure_type(Rn,Cn,T) :-
    occ(Rn,Cn), occ_type(Rn,Cn,T),
    not has_second_type(Rn,Cn).

has_second_type(R,C) :- occ_type(R,C,T1), occ_type(R,C,T2), T1 != T2.

% Il piatto piazzato tocca un vicino puro dello stesso tipo
touches_pure_same(O,R,C,T) :-
    choose(O,R,C),
    plate_pos(O,R,C,P,Rp,Cp),
    type_in_plate(O,P,T),
    neigh_of(O,R,C,Rp,Cp,Rn,Cn),
    not covers(O,R,C,Rn,Cn),
    neighbor_pure_type(Rn,Cn,T).

has_pure_touch(O,R,C) :- touches_pure_same(O,R,C,_).

pure_touch_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{T,Rn,Cn : touches_pure_same(O,R,C,T),
               neigh_of(O,R,C,_,_,Rn,Cn),
               neighbor_pure_type(Rn,Cn,T)}.

% =============================================================
% EURISTICA 5 — Non bloccare: celle libere rimaste dopo la mossa
% =============================================================
occupied_after(O,R,C,Ra,Ca) :- choose(O,R,C), occ(Ra,Ca).
occupied_after(O,R,C,Rp,Cp) :- choose(O,R,C), covers(O,R,C,Rp,Cp).

free_after(O,R,C,Rf,Cf) :- choose(O,R,C), cell(Rf,Cf), not occupied_after(O,R,C,Rf,Cf).

free_count(O,R,C,N) :-
    choose(O,R,C),
    N = #count{Rf,Cf : free_after(O,R,C,Rf,Cf)}.

% =============================================================
% EURISTICA 6 — Centralita (preferisci centro della griglia)
% =============================================================
% Distanza Manhattan dal centro approssimato
% Per griglia 5x4: centro circa (2,1.5) -> usiamo (2,2)
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
% EURISTICA 7 — Opzione con piu fette (preferisci blocchi grossi)
% =============================================================
% gia definito: tot(O,S)

% =============================================================
% EURISTICA 8 — Piatto puro dell'opzione piazzato vicino a stesso tipo
% (merge sicuro, massima priorita dopo completamento)
% =============================================================

% Un piatto P dell'opzione O è puro
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
% EURISTICA 9 — Evita isolamento (non mettere dove non c'e niente vicino)
% =============================================================
any_occ_neighbor(O,R,C) :-
    choose(O,R,C),
    ext_neigh(O,R,C,Rn,Cn),
    occ(Rn,Cn).

isolated(O,R,C) :- choose(O,R,C), not any_occ_neighbor(O,R,C).

% Ma se la griglia è vuota, non penalizzare
grid_empty :- not occ(_,_).
isolated_penalty(O,R,C) :- isolated(O,R,C), not grid_empty.

% =============================================================
% WEAK CONSTRAINTS — Ordinati per priorità
% =============================================================

% @10: COMPLETAMENTO TORTA — massima priorita
%      Penalizza se non completa nessuna torta (se potevi farlo)
:~ choose(O,R,C), completions(O,R,C,0). [50@10,O,R,C]

% @9: PIATTO PURO che matcha vicino (merge certo e pulito)
:~ choose(O,R,C), not pure_plate_matches(O,R,C). [20@9,O,R,C]

% @8: TOCCA PURO STESSO TIPO
:~ choose(O,R,C), not has_pure_touch(O,R,C). [15@8,O,R,C]

% @7: MATCH DI TIPO DIRETTO (il piu importante dopo completamento)
:~ choose(O,R,C), not has_match(O,R,C). [12@7,O,R,C]

% @6: PIU MATCH DIVERSI = MEGLIO
:~ choose(O,R,C), match_count(O,R,C,N), N < 3. [8@6,O,R,C]

% @5: CONSOLIDAMENTO — porta fette verso gruppi grandi
:~ choose(O,R,C), best_consolidation(O,R,C,M), M < 3. [6@5,O,R,C]

% @4: OPZIONE PURA (preferisci opzioni con un solo tipo)
:~ choose(O,R,C), not pure_opt(O). [4@4,O,R,C]

% @3: NON ISOLARE — non mettere dove non c'è niente
:~ isolated_penalty(O,R,C). [10@3,O,R,C]

% @2: CELLE LIBERE — non riempire troppo la griglia
:~ choose(O,R,C), free_count(O,R,C,N), N < 5. [3@2,O,R,C]

% @1: CENTRALITA — preferisci posizioni centrali
:~ choose(O,R,C), min_dist_center(O,R,C,MD), MD > 2. [1@1,O,R,C]

% @0: PIU FETTE — preferisci opzioni piu grosse
:~ choose(O,R,C), tot(O,S). [-S@0,O,R,C]

#show choose/3.
