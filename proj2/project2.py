#!/usr/bin/python3
# alc25 - 5 - project2 
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from z3 import Solver
from z3 import Bool, Int, sat, IntVal
from z3 import Or, And, If


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

def create_variables(n,D,S):
    variables = [[[] for _ in range(D)] for _ in range(n)]
    for i_nurse in range(n):
        for i_day in range(D):
            for i_shift in range(S):
                name = f'{i_nurse}{i_day}{i_shift}'
                variables[i_nurse][i_day] += [Bool(name)]
    
    return variables

def create_constraints(solver, variables, D, S, R, N, P):

    # ::Constraint 1::
    # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift}

    # ::Contraint 2::
    # For shift s in day d, add constraint: SUM(Mng[i]) >= 1

    # ::Constraint 3::
    # Nurses can only do continuous shifts, so no 1-0-...-0-1 shift scheme in a day (~xi[s-1] \/ xi[s] \/ xi[s+1])

    # ::Constraint 4::
    # For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax

    # ::Constraint 5::
    # For Nurse N, SUM(x[i]) <= H(N)

    # ::Constraint 6::
    # If P{i_nurse,i_shift,i_day} < 0, Nurse is unavailable in this shift in this day

    # ::Constraint 7::
    # Minimize cost of assignment

    return solver


if __name__ == "__main__":
    solver = Solver()

    D, S, R, N, P = parse_input()
    variables = create_variables(len(N),D,S)
    print(variables)

    solver = create_constraints(solver, variables, D, S, R, N ,P)

    if solver.check() == sat:
        model = solver.model()
        print(model)
    else:
        print("Unsatisfiable Formula.")
