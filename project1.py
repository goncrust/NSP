#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from pysat.solvers import Glucose4
from pysat.card import CardEnc, EncType

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
    solver = Glucose4()

    # create variables v_{d,s,k} (nurse N_k, shift (d,s))
    v = [[[i+1 + j*D + k*S*D for k in range(n)] for j in range(S)] for i in range(D)]
    top_v = n*S*D

    for d in range(D):
        for s in range(S):
            # Constraint 1: Each shift s of day d has at least R_{s,d} nurses assigned
            r = R[d][s]
            enc = CardEnc.atleast(lits=v[d][s], bound=r, top_id=top_v, encoding=EncType.mtotalizer)
            for clause in enc.clauses:
                solver.add_clause(clause)

            # Constraint 2: Each shift s of day d has at least one nurse with managerial qualification
            solver.add_clause([v[d][s][k] for k in range(n) if N[k].is_mngr])  

        # Constraint 3: The workload of a nurse in a given day is continuous
        for k in range(n):
            for s in range(S):
                for m in range(s+2, S):
                    print([-v[d][s][k], v[d][s+1][k], -v[d][m][k]])
                    solver.add_clause([-v[d][s][k], v[d][s+1][k], -v[d][m][k]])
