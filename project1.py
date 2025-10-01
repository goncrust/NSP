#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from pysat.examples.rc2 import RC2
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool, WCNF

@dataclass
class Nurse:
    is_mngr: bool
    l_min: int
    l_max: int
    h: int


def parse_input():
    # D S -> num. days, num. shifts per day
    line = sys.stdin.readline().strip().split()
    assert len(line) == 2
    D = int(line[0])
    S = int(line[1])

    # R_{s,d} -> num. required nurses for shift (d,s)
    R = []
    for _ in range(D):
        line = sys.stdin.readline().strip().split()
        assert len(line) == S
        R.append([int(r) for r in line])

    # n -> num. nurses
    line = sys.stdin.readline().strip().split()
    assert len(line) == 1
    n = int(line[0])

    # Y/N L_k^min L_k^max H_k -> manager, min/max num. shifts per day, max total num. shifts
    N = []
    for _ in range(n):
        line = sys.stdin.readline().strip().split()
        assert len(line) == 4
        N.append(Nurse(line[0] == "Y", int(line[1]), int(line[2]), int(line[3])))

    # P_{k,s,d} -> cost of assign. nurse N_k to shift (d,s)
    P = []
    for _ in range(D):
        P_d = []
        for _ in range(S):
            line = sys.stdin.readline().strip().split()
            assert len(line) == n
            P_d.append([int(p) for p in line])
        P.append(P_d)

    return D, S, R, n, N, P


if __name__ == "__main__":
    D, S, R, n, N, P = parse_input()
    solver = RC2(WCNF())

    # create variables v_{d,s,k} (nurse N_k, shift (d,s))
    v = [[[i+1 + j*D + k*S*D for k in range(n)] for j in range(S)] for i in range(D)]
    vpool = IDPool()
    vpool.top = 60

    for d in range(D):
        for s in range(S):
            # Constraint 1: Each shift s of day d has at least R_{s,d} nurses assigned
            r = R[d][s]
            enc = CardEnc.atleast(lits=v[d][s], bound=r, vpool=vpool, encoding=EncType.mtotalizer)
            for clause in enc.clauses:
                solver.add_clause(clause)

            # Constraint 2: Each shift s of day d has at least one nurse with managerial qualification
            solver.add_clause([v[d][s][k] for k in range(n) if N[k].is_mngr])  

            for k in range(n):
                cost = P[d][s][k]

                # Constraint 6: A nurse N_k is never assigned to a shift where it is declared as unavailable
                if cost == -1:
                    solver.add_clause([-v[d][s][k]])

                # Constraint 7: The total cost of assigning nurses to shifts is minimized
                if cost > 0:
                    solver.add_clause([-v[d][s][k]], weight=cost)
                

        for k in range(n):
            # Constraint 3: The workload of a nurse in a given day is continuous
            for s in range(S):
                for m in range(s+2, S):
                    solver.add_clause([-v[d][s][k], v[d][s+1][k], -v[d][m][k]])

            # Constraint 4: During a day, the number of shifts for a nurse N_k is always between L_k^min and L_k^max
            l_min = N[k].l_min
            l_max = N[k].l_max

            v_d_k = [v[d][s][k] for s in range(S)]
            enc_min = CardEnc.atleast(lits=v_d_k, bound=l_min, vpool=vpool, encoding=EncType.mtotalizer)
            for clause in enc_min:
                solver.add_clause(clause)

            enc_max = CardEnc.atmost(lits=v_d_k, bound=l_max, vpool=vpool, encoding=EncType.mtotalizer)
            for clause in enc_max:
                solver.add_clause(clause)


    # Constraint 5: A nurse N_k is never assigned more than H_k shiifts in the period
    for k in range(n):
        v_k = [v[d][s][k] for d in range(D) for s in range(S)]
        h = N[k].h
        enc = CardEnc.atmost(lits=v_k, bound=h, vpool=vpool, encoding=EncType.mtotalizer)
        for clause in enc:
            solver.add_clause(clause)

    print("Model", solver.compute())
    print("Cost:", solver.cost)
