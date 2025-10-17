#!/usr/bin/python3
# alc25 - 5 - project2
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
import z3
from z3 import Solver, Optimize
from z3 import Bool, Int, sat, IntVal
from z3 import Or, And, If, Sum, is_true, AtLeast, Implies, AtMost, Not
from z3 import PbEq, PbGe, PbLe


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


def print_output(model, cost, D, S, N, start_shift, num_shifts):
    n = len(N)
    participants = [[[] for _ in range(S)] for _ in range(D)]
    for d in range(D):
        for k in range(n):
            ns = model.eval(num_shifts[k][d]).as_long()
            if ns > 0:
                ss = model.eval(start_shift[k][d]).as_long()
                for s in range(ss, ss + ns):
                    participants[d][s].append(k + 1)

    print(cost)
    for d in range(D):
        for s in range(S):
            listToStr = " ".join([str(element) for element in participants[d][s]])
            print(len(participants[d][s]), listToStr)


def create_constraints(solver: Optimize, D, S, R, N, P):
    n = len(N)

    start_shift = [[Int(f"start_{k}_{d}") for d in range(D)] for k in range(n)]
    num_shifts = [[Int(f"num_{k}_{d}") for d in range(D)] for k in range(n)]

    # check validity variables
    for k in range(n):
        for d in range(D):
            solver.add(start_shift[k][d] >= 0)
            solver.add(start_shift[k][d] < S)
            solver.add(num_shifts[k][d] >= 0)
            solver.add(num_shifts[k][d] <= S)
            solver.add(num_shifts[k][d] + start_shift[k][d] <= S)

    # ::Constraint 1::
    # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift}
    for d in range(D):
        for s in range(S):
            aux_list = []
            for k in range(n):
                aux_list.append(If(And(start_shift[k][d] <= s, start_shift[k][d] + num_shifts[k][d] > s), 1, 0))
            solver.add(Sum(aux_list) >= R[d][s])


    # ::Contraint 2::
    # For shift s in day d, add constraint: SUM(Mng[i]) >= 1
    for d in range(D):
        for s in range(S):
            aux_list = []
            for k in range(n):
                if N[k].is_mngr:
                    aux_list.append(If(And(start_shift[k][d] <= s, start_shift[k][d] + num_shifts[k][d] > s), 1, 0))
            solver.add(Sum(aux_list) >= 1)

    # ::Constraint 3::
    # Nurses can only do continuous shifts, if nurse has done a shift in a day and she's not assigned to the next one,
    # This is already satisfied by the enconding

    # ::Constraint 4::
    # For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
    for k in range(n):
        for d in range(D):
            solver.add(And(num_shifts[k][d] >= N[k].l_min, num_shifts[k][d] <= N[k].l_max))

    # ::Constraint 5::
    # For Nurse N, SUM(x[i]) <= H(N)
    for k in range(n):
        aux_list = [num_shifts[k][d] for d in range(D)]
        solver.add(Sum(aux_list) <= N[k].h)

    terms = []
    for d in range(D):
        for s in range(S):
            for k in range(n):
                # ::Constraint 6::
                # If P{i_nurse,i_shift,i_day} == -1, Nurse is unavailable in this shift in this day
                if P[d][s][k] == -1:
                    solver.add(Not(And(start_shift[k][d] <= s, start_shift[k][d] + num_shifts[k][d] > s)))
                else:
                    # Add term to the total cost expression
                    terms.append(If(And(start_shift[k][d] <= s, start_shift[k][d] + num_shifts[k][d] > s), P[d][s][k], 0))
    
    # ::Constraint 7::
    # Minimize cost of assignment
    opt_cost = solver.minimize(Sum(terms))
    return solver, opt_cost, start_shift, num_shifts


if __name__ == "__main__":
    z3.set_param("parallel.enable", True)

    D, S, R, N, P = parse_input()

    solver = Optimize()
    solver.set(priority="pareto")
    solver, cost, start_shift, num_shifts = create_constraints(solver, D, S, R, N, P)

    if solver.check() == sat:
        model = solver.model()
        print_output(model, cost.value(), D, S, N, start_shift, num_shifts)
    else:
        print("UNSAT.")
