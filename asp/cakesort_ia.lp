% -------------------------------------------------------------
% 0. DEFINIZIONE GRIGLIA E SUPPORTI TECNICI
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
% Scegliamo esattamente una mossa legale tra le opzioni disponibili
{ choose(O, R, C) : opt(O), row(R), col(C) } = 1.

% -------------------------------------------------------------
% 2. POSIZIONI E LEGALITÀ (Sintassi DLV2)
% -------------------------------------------------------------
% Calcolo celle coperte dal blocco scelto
place(O, R, C, 0) :- choose(O, R, C), opt_orient(O, n).

place(O, R, CP, P) :-
    choose(O, R, C), opt_orient(O, h), opt_size(O, S),
    idx(P), P < S, CP = C + P.

place(O, RP, C, P) :-
    choose(O, R, C), opt_orient(O, v), opt_size(O, S),
    idx(P), P < S, RP = R + P.

% Vincoli di integrità: la mossa deve stare in griglia e non sovrapporsi
:- place(_, R, C, _), not row(R).
:- place(_, R, C, _), not col(C).
:- place(_, R, C, _), occ(R, C).

% -------------------------------------------------------------
% 3. ANALISI VICINATO (Sostituto di #abs e tuple)
% -------------------------------------------------------------
adj(R, C, R, C1) :- row(R), col(C), C1 = C + 1, col(C1).
adj(R, C, R, C1) :- row(R), col(C), C1 = C - 1, col(C1).
adj(R, C, R1, C) :- row(R), col(C), R1 = R + 1, row(R1).
adj(R, C, R1, C) :- row(R), col(C), R1 = R - 1, row(R1).

% Vicini esterni al blocco piazzato
% 1. Crea un predicato d'appoggio per 'estrarre' solo le coordinate occupate
is_covered(O, R, C) :- place(O, R, C, _).

% 2. Usa questo predicato nella regola del vicinato
ext_neigh(O, R, C, Rn, Cn) :-
    place(O, Rp, Cp, _),
    adj(Rp, Cp, Rn, Cn),
    not is_covered(O, Rn, Cn),
    choose(O, R, C).

% -------------------------------------------------------------
% 4. LOGICA STRATEGICA (Match, Bridge, Vital Space)
% -------------------------------------------------------------

% Match diretto
direct_match(O, R, C, T) :-
    place(O, Rp, Cp, P), opt_piece(O, P, T, K), K > 0,
    ext_neigh(O, R, C, Rn, Cn), occ_type(Rn, Cn, T).

% Bridge: la mossa unisce due gruppi dello stesso tipo
% 1. Usiamo una versione semplificata che dice solo "la mossa O contiene il tipo T"
has_type(O, T) :- opt_piece(O, P, T, K), K > 0.

% 2. Riscriviamo la regola del Bridge
bridge(O, R, C, T) :-
    choose(O, R, C),              % Vincoliamo la mossa
    has_type(O, T),               % Vincoliamo il tipo T (senza wildcard _)
    N = #count{ Rn, Cn : ext_neigh(O, R, C, Rn, Cn), occ_type(Rn, Cn, T) },
    N >= 2.

% Completamento Torta (Livello 14)
sum_fette(O, R, C, T, Total) :-
    direct_match(O, R, C, T),
    Brought = #sum{ K, P : opt_piece(O, P, T, K) },
    InGrid = #sum{ Kn, Rn, Cn : ext_neigh(O, R, C, Rn, Cn), occ_count(Rn, Cn, T, Kn) },
    Total = Brought + InGrid.

can_complete(O, R, C) :- sum_fette(O, R, C, _, Tot), Tot >= 6.

% Vital Space (Anti-Block)
near_complete(R, C, T) :- occ_count(R, C, T, K), K >= 4, K < 6.
vital_space(Rn, Cn, T) :- near_complete(R, C, T), adj(R, C, Rn, Cn), not occ(Rn, Cn).

% Definiamo prima COSA occupa la mossa scelta, legandola a O, R, C
occupies_cell(O, R, C, Rp, Cp) :-
    choose(O, R, C),
    place(O, Rp, Cp, _).

% Ora usiamo questo legame nella regola blocks_vital
blocks_vital(O, R, C) :-
    occupies_cell(O, R, C, Rp, Cp),
    vital_space(Rp, Cp, T),
    not has_type(O, T).

% Centralità (Manhattan manuale per DLV2)
diff_r(R, V) :- choose(_, R, _), max_row(MR), V = R * 2 - MR.
abs_r(R, V)  :- diff_r(R, V), V >= 0.
abs_r(R, NV) :- diff_r(R, V), V < 0, NV = -V.
diff_c(C, V) :- choose(_, _, C), max_col(MC), V = C * 2 - MC.
abs_c(C, V)  :- diff_c(C, V), V >= 0.
abs_c(C, NV) :- diff_c(C, V), V < 0, NV = -V.
dist_center(O, R, C, D) :- choose(O, R, C), abs_r(R, AR), abs_c(C, AC), D = AR + AC.
% Questo predicato dice semplicemente: la mossa O in R,C fa ALMENO un match
has_any_match(O, R, C) :- direct_match(O, R, C, T).
% -------------------------------------------------------------
% 5. WEAK CONSTRAINTS (I 14 LIVELLI DI PRIORITÀ)
% -------------------------------------------------------------
% @14: Completamento
:~ choose(O,R,C), can_complete(O,R,C). [-100@14, O]

% @13: Spazio Vitale
:~ choose(O,R,C), blocks_vital(O,R,C). [80@13, O]

% @11: Penalizza se NON ha alcun match (usando il predicato sicuro)
:~ choose(O,R,C), not has_any_match(O, R, C). [50@11, O]

% @10: Bridge
:~ choose(O,R,C), bridge(O,R,C, _). [-60@10, O]

% @9: Multi-match
:~ choose(O,R,C), opt_size(O,2), #count{ T : direct_match(O,R,C,T) } >= 2. [-40@9, O]

% @7: Consolidamento
:~ choose(O,R,C), sum_fette(O,R,C,T,S). [-S@7, O, T]

% @4: Centralità
:~ choose(O,R,C), dist_center(O,R,C,D). [D@4, O]

#show choose/3.