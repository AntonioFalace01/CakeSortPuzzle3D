% -------------------------------------------------------------
%DEFINIZIONE GRIGLIA E SUPPORTI TECNICI
% -------------------------------------------------------------
row(0..4).
col(0..3).
idx(0..10).
max_row(4).
max_col(3).
total_cells(20).

% -------------------------------------------------------------
% 1. GENERATE (Scelta della mossa)
% -------------------------------------------------------------
{ choose(O, R, C) : opt(O), row(R), col(C) } = 1.

% -------------------------------------------------------------
% 2. POSIZIONI E LEGALITA (Sintassi DLV2)
% -------------------------------------------------------------
place(O, R, C, 0) :- choose(O, R, C), opt_orient(O, n).

place(O, R, CP, P) :-
    choose(O, R, C), opt_orient(O, h), opt_size(O, S),
    idx(P), P < S, CP = C + P.

place(O, RP, C, P) :-
    choose(O, R, C), opt_orient(O, v), opt_size(O, S),
    idx(P), P < S, RP = R + P.

:- place(_, R, C, _), not row(R).
:- place(_, R, C, _), not col(C).
:- place(_, R, C, _), occ(R, C).

% -------------------------------------------------------------
% 3. ANALISI VICINATO SPECIFICO PER PIASTRA
% -------------------------------------------------------------
adj(R, C, R, C1) :- row(R), col(C), C1 = C + 1, col(C1).
adj(R, C, R, C1) :- row(R), col(C), C1 = C - 1, col(C1).
adj(R, C, R1, C) :- row(R), col(C), R1 = R + 1, row(R1).
adj(R, C, R1, C) :- row(R), col(C), R1 = R - 1, row(R1).

is_covered(O, R, C) :- place(O, R, C, _).

% MODIFICA CHIAVE: Calcoliamo i vicini esterni della SPECIFICA piastra P
plate_neigh(O, R, C, P, Rn, Cn) :-
    choose(O, R, C),
    place(O, Rp, Cp, P),
    adj(Rp, Cp, Rn, Cn),
    not is_covered(O, Rn, Cn).

% (Manteniamo ext_neigh globale se dovesse servire per fallback, ma usiamo plate_neigh)
ext_neigh(O, R, C, Rn, Cn) :- plate_neigh(O, R, C, _, Rn, Cn).

% -------------------------------------------------------------
% 4. LOGICA STRATEGICA (Match e Bridge per piastra)
% -------------------------------------------------------------

% Match diretto: la specifica piastra P porta T e tocca FISICAMENTE un vicino con T
plate_direct_match(O, R, C, P, T) :-
    opt_piece(O, P, T, K), K > 0,
    plate_neigh(O, R, C, P, Rn, Cn),
    occ_type(Rn, Cn, T).

% Mappiamo a livello globale per retrocompatibilità dei weak constraints
direct_match(O, R, C, T) :- plate_direct_match(O, R, C, _, T).

% La piastra P contiene T
plate_has_type(O, P, T) :- opt_piece(O, P, T, K), K > 0.
has_type(O, T) :- plate_has_type(O, _, T).

% Bridge per singola piastra
plate_bridge(O, R, C, P, T) :-
    choose(O, R, C),
    plate_has_type(O, P, T),
    N = #count{ Rn, Cn : plate_neigh(O, R, C, P, Rn, Cn), occ_type(Rn, Cn, T) },
    N >= 2.

bridge(O, R, C, T) :- plate_bridge(O, R, C, _, T).

grid_type(T) :- occ_type(_, _, T).

% Bridge "puro" per singola piastra
plate_bridge_pure(O, R, C, P, T) :-
    choose(O, R, C),
    place(O, _, _, P),
    grid_type(T),
    N = #count{ Rn, Cn : plate_neigh(O, R, C, P, Rn, Cn), occ_type(Rn, Cn, T) },
    N >= 2.

bridge_pure(O, R, C, T) :- plate_bridge_pure(O, R, C, _, T).

% -------------------------------------------------------------
% 5. COMPLETAMENTO TORTA (Per piastra)
% -------------------------------------------------------------

plate_brought(O, P, T, Brought) :-
    plate_has_type(O, P, T),
    opt_piece(O, P, T, Brought).

% Calcolo totale fette per mosse con direct_match verificato SU QUELLA PIASTRA
sum_fette_plate(O, R, C, P, T, Total) :-
    plate_direct_match(O, R, C, P, T),
    plate_brought(O, P, T, Brought),
    InGrid = #sum{ Kn, Rn, Cn : plate_neigh(O, R, C, P, Rn, Cn), occ_count(Rn, Cn, T, Kn) },
    Total = Brought + InGrid.

% Calcolo totale fette per bridge puro su specifica piastra
sum_fette_bridge_plate(O, R, C, P, T, Total) :-
    plate_bridge_pure(O, R, C, P, T),
    not plate_has_type(O, P, T),
    Total = #sum{ Kn, Rn, Cn : plate_neigh(O, R, C, P, Rn, Cn), occ_count(Rn, Cn, T, Kn) }.

can_complete(O, R, C) :- sum_fette_plate(O, R, C, _, _, Tot), Tot >= 6.
can_complete(O, R, C) :- sum_fette_bridge_plate(O, R, C, _, _, Tot), Tot >= 6.

some_completion_exists :- can_complete(_, _, _).
:- some_completion_exists, choose(O, R, C), not can_complete(O, R, C).

% -------------------------------------------------------------
% 6. VITAL SPACE (Anti-Block) - RAFFINATO PER PIASTRA
% -------------------------------------------------------------

near_complete(R, C, T) :- occ_count(R, C, T, K), K >= 4, K < 6.

free_adj_nc(R, C, T, Rn, Cn) :-
    near_complete(R, C, T),
    adj(R, C, Rn, Cn),
    not occ(Rn, Cn).

free_adj_count(R, C, T, N) :-
    near_complete(R, C, T),
    N = #count{ Rn, Cn : free_adj_nc(R, C, T, Rn, Cn) }.

vital_space(Rn, Cn, R, C, T) :-
    free_adj_nc(R, C, T, Rn, Cn),
    free_adj_count(R, C, T, 1).

% Tracciamo QUALE piastra occupa lo spazio
occupies_cell_plate(O, R, C, Rp, Cp, P) :-
    choose(O, R, C),
    place(O, Rp, Cp, P).

% La mossa blocca lo spazio se la SPECIFICA PIASTRA che cade nel buco vitale
% NON fa match diretto su quella torta near complete
blocks_vital(O, R, C) :-
    occupies_cell_plate(O, R, C, Rp, Cp, P),
    vital_space(Rp, Cp, Rnc, Cnc, T),
    not direct_match_on_nc_plate(O, R, C, P, Rnc, Cnc, T).

% La piastra P fa match diretto o bridge_pure con la torta NC
direct_match_on_nc_plate(O, R, C, P, Rnc, Cnc, T) :-
    choose(O, R, C),
    plate_has_type(O, P, T),
    plate_neigh(O, R, C, P, Rnc, Cnc),
    occ_type(Rnc, Cnc, T).

direct_match_on_nc_plate(O, R, C, P, Rnc, Cnc, T) :-
    choose(O, R, C),
    plate_bridge_pure(O, R, C, P, T),
    plate_neigh(O, R, C, P, Rnc, Cnc),
    occ_type(Rnc, Cnc, T).

% -------------------------------------------------------------
% 7. CENTRALITA E UTILITA
% -------------------------------------------------------------
diff_r(R, V) :- choose(_, R, _), max_row(MR), V = R * 2 - MR.
abs_r(R, V)  :- diff_r(R, V), V >= 0.
abs_r(R, NV) :- diff_r(R, V), V < 0, NV = -V.
diff_c(C, V) :- choose(_, _, C), max_col(MC), V = C * 2 - MC.
abs_c(C, V)  :- diff_c(C, V), V >= 0.
abs_c(C, NV) :- diff_c(C, V), V < 0, NV = -V.
dist_center(O, R, C, D) :- choose(O, R, C), abs_r(R, AR), abs_c(C, AC), D = AR + AC.

has_any_match(O, R, C) :- direct_match(O, R, C, _).
has_any_match(O, R, C) :- bridge_pure(O, R, C, _).

% -------------------------------------------------------------
% 8. WEAK CONSTRAINTS (LIVELLI DI PRIORITA)
% -------------------------------------------------------------

:~ choose(O,R,C), blocks_vital(O,R,C). [80@9, O]

:~ choose(O,R,C), not has_any_match(O, R, C). [50@11, O]

:~ choose(O,R,C), bridge(O,R,C, _). [-60@10, O]

:~ choose(O,R,C), opt_size(O,2), #count{ T : direct_match(O,R,C,T) } >= 2. [-40@9, O]

% Modificato per usare il calcolo specifico per piastra (evita duplicazioni e safety error)
:~ choose(O,R,C), sum_fette_plate(O,R,C,P,T,S). [-S@7, O, P, T]

:~ choose(O,R,C), dist_center(O,R,C,D). [D@4, O]

#show choose/3.