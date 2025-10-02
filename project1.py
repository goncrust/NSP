#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from pysat.formula import WCNF, IDPool
from pysat.card import EncType, CardEnc
from pysat.examples.rc2 import RC2


@dataclass
class Nurse:
    is_mngr: bool
    l_min: int
    l_max: int
    h: int


def read_line():
    return sys.stdin.readline().strip().split()


def parse_input():
    # D S -> num. days, num. shifts per day
    line = read_line()
    assert len(line) == 2
    D = int(line[0])
    S = int(line[1])

    # R_{s,d} -> num. required nurses for shift (d,s)
    R = []
    for _ in range(D):
        line = read_line()
        assert len(line) == S
        R.append([int(r) for r in line])

    # n -> num. nurses
    line = read_line()
    assert len(line) == 1
    n = int(line[0])

    # Y/N L_k^min L_k^max H_k -> manager, min/max num. shifts per day, max total num. shifts
    N = []
    for _ in range(n):
        line = read_line()
        assert len(line) == 4
        N.append(Nurse(line[0] == "Y", int(line[1]), int(line[2]), int(line[3])))

    # P_{k,s,d} -> cost of assign. nurse N_k to shift (d,s)
    P = []
    for _ in range(D):
        P_d = []
        for _ in range(S):
            line = read_line()
            assert len(line) == n
            P_d.append([int(p) for p in line])
        P.append(P_d)

    return D, S, R, N, P


def get_vals_x(vpool: IDPool, x: int):
    return vpool.obj(abs(x))


def print_output(model, cost, vpool, D, S, n):
    participants = [[[] for _ in range(S)] for _ in range(D)]
    for idx in range(D * S * n):
        if model[idx] > 0:
            key = get_vals_x(vpool, model[idx])
            if key:
                day, shift, nurse_id = key
                participants[day][shift].append(nurse_id + 1)

    print(cost)
    for d in range(D):
        for s in range(S):
            listToStr = " ".join([str(element) for element in participants[d][s]])
            print(len(participants[d][s]), listToStr)


def solve(D, S, R, N, P):
    formula = WCNF()
    vpool = IDPool(start_from=1)
    n = len(N)
    CARD = EncType.mtotalizer

    def x(d, s, n):
        return vpool.id((d, s, n))

    for i_nurse in range(n):
        for d in range(D):
            for s in range(S):
                x(d, s, i_nurse)

    available = [
        [[P[d][s][i_nurse] >= 0 for i_nurse in range(n)] for s in range(S)]
        for d in range(D)
    ]
    managers_ids = [i for i, info in enumerate(N) if info.is_mngr]

    for i_day in range(D):
        for i_shift in range(S):
            managers = [
                x(i_day, i_shift, i)
                for i in managers_ids
                if available[i_day][i_shift][i]
            ]
            literals = []
            for i_nurse in range(n):
                nurse_id = x(i_day, i_shift, i_nurse)

                # ::Constraint 3::
                # Nurses can only do continuous shifts, so no 1-0-...-0-1 shift scheme in a day (~xi[s-1] \/ xi[s] \/ xi[s+1])
                if i_shift != (S - 1) and N[i_nurse].l_max > 1:
                    for d in range(i_shift + 2, S):
                        formula.append(
                            [
                                -x(i_day, i_shift, i_nurse),
                                x(i_day, i_shift + 1, i_nurse),
                                -x(i_day, d, i_nurse),
                            ]
                        )

                # ::Constraint 6::
                # If P{i_nurse,i_shift,i_day} < 0, Nurse is unavailable in this shift in this day
                if not available[i_day][i_shift][i_nurse]:
                    formula.append([-nurse_id])
                    continue

                # ::Constraint 7::
                # Minimize cost of assignment
                if P[i_day][i_shift][i_nurse] > 0:
                    formula.append([-nurse_id], weight=P[i_day][i_shift][i_nurse])

                literals.append(nurse_id)

            # ::Constraint 1::
            # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift}
            formula.extend(
                CardEnc.atleast(
                    lits=literals, vpool=vpool, bound=R[i_day][i_shift], encoding=CARD
                ).clauses
            )

            # ::Contraint 2::
            # For shift s in day d, add constraint: SUM(Mng[i]) >= 1
            formula.extend(
                CardEnc.atleast(
                    lits=managers, vpool=vpool, bound=1, encoding=CARD
                ).clauses
            )

    for i_nurse in range(n):
        l_min, l_max = N[i_nurse].l_min, N[i_nurse].l_max
        for i_day in range(D):
            # ::Constraint 4::
            # For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
            nurse_day = [x(i_day, s, i_nurse) for s in range(S)]
            formula.extend(
                CardEnc.atleast(
                    lits=nurse_day, vpool=vpool, bound=l_min, encoding=CARD
                ).clauses
            )
            formula.extend(
                CardEnc.atmost(
                    lits=nurse_day, vpool=vpool, bound=l_max, encoding=CARD
                ).clauses
            )

    for i_nurse in range(n):
        total_max = N[i_nurse].h
        # ::Constraint 5::
        # For Nurse N, SUM(x[i]) <= H(N)
        nurse_total = [x(d, s, i_nurse) for d in range(D) for s in range(S)]
        formula.extend(
            CardEnc.atmost(
                lits=nurse_total, vpool=vpool, bound=total_max, encoding=CARD
            ).clauses
        )

    solver = RC2(formula, solver="cadical153")
    model = solver.compute()
    cost = solver.cost
    print_output(model, cost, vpool, D, S, n)


D, S, R, N, P = parse_input()
solve(D, S, R, N, P)
