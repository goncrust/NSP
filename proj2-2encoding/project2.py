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


def print_output(variables, model, cost, D, S, N):
    n = len(N)
    participants = [[[] for _ in range(S)] for _ in range(D)]
    for d in range(D):
        for s in range(S):
            for i_nurse in range(n):
                var = variables[d][s][i_nurse]
                val = is_true(model.evaluate(var, model_completion=True))
                if val:
                    participants[d][s].append(i_nurse + 1)

    print(cost)
    for d in range(D):
        for s in range(S):
            listToStr = " ".join([str(element) for element in participants[d][s]])
            print(len(participants[d][s]), listToStr)


def create_variables(N, D, S):
    n = len(N)
    variables = [[[] for _ in range(S)] for _ in range(D)]
    managers = [[[] for _ in range(S)] for _ in range(D)]
    for i_day in range(D):
        for i_shift in range(S):
            for i_nurse in range(n):
                var = Bool(f"x{i_nurse}{i_day}{i_shift}")
                variables[i_day][i_shift] += [var]

                if N[i_nurse].is_mngr:
                    managers[i_day][i_shift] += [var]

    return variables, managers


def create_constraints(solver: Optimize, variables, managers, D, S, R, N, P):
    n = len(N)

    # ::Constraint 1::
    # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift}
    for i_day in range(D):
        for i_shift in range(S):
            solver.add(AtLeast(*variables[i_day][i_shift], R[i_day][i_shift]))

    # ::Contraint 2::
    # For shift s in day d, add constraint: SUM(Mng[i]) >= 1
    for i_day in range(D):
        for i_shift in range(S):
            solver.add(AtLeast(*managers[i_day][i_shift], 1))

    # ::Constraint 3::
    # Nurses can only do continuous shifts, if nurse has done a shift in a day and she's not assigned to the next one,
    #  set variable "can_be_assigned_this_day" to false
    for d in range(D):
        for s in range(S):
            for i_nurse in range(n):
                if s != S - 1 and N[i_nurse].l_max > 1:
                    for later in range(s + 2, S):
                        solver.add(
                            Or(
                                variables[d][s][i_nurse] == False,
                                variables[d][s + 1][i_nurse] == True,
                                variables[d][later][i_nurse] == False,
                            )
                        )

    # ::Constraint 4::
    # For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
    for i_day in range(D):
        for i_nurse in range(n):
            lits = [variables[i_day][s][i_nurse] for s in range(S)]
            solver.add(AtLeast(*lits, N[i_nurse].l_min))
            solver.add(AtMost(*lits, N[i_nurse].l_max))

    # ::Constraint 5::
    # For Nurse N, SUM(x[i]) <= H(N)
    for i_nurse in range(n):
        lits = [variables[d][s][i_nurse] for d in range(D) for s in range(S)]
        solver.add(AtMost(*lits, N[i_nurse].h))

    terms = []
    for d in range(D):
        for s in range(S):
            for i_nurse in range(n):
                # ::Constraint 6::
                # If P{i_nurse,i_shift,i_day} < 0, Nurse is unavailable in this shift in this day
                if (P[d][s][i_nurse]) < 0:
                    solver.add(variables[d][s][i_nurse] == False)
                else:
                    terms.append(
                        If(
                            variables[d][s][i_nurse],
                            IntVal(P[d][s][i_nurse]),
                            IntVal(0),
                        )
                    )

    # ::Constraint 7::
    # Minimize cost of assignment
    opt_cost = solver.minimize(Sum(terms))
    return solver, opt_cost


if __name__ == "__main__":
    z3.set_param("sat.core.minimize_partial", True)
    z3.set_param("sat.smt", True)
    z3.set_param("sat.cardinality.solver", True)
    z3.set_param("sat.pb.solver", "sorting")
    z3.set_param("parallel.enable", True)
    z3.set_param("sat.threads", 4)
    z3.set_param("sat.lookahead_simplify", True)
    z3.set_param("auto_config", False)
    z3.set_param("smt.induction", True)
    z3.set_param("sat.phase", "caching")
    z3.set_param("opt.enable_sat", True)
    z3.set_param("sat.bce", True)

    D, S, R, N, P = parse_input()
    variables, managers = create_variables(N, D, S)

    solver = Optimize()
    solver.set(priority="pareto")
    solver, cost = create_constraints(solver, variables, managers, D, S, R, N, P)

    if solver.check() == sat:
        model = solver.model()
        print_output(variables, model, cost.value(), D, S, N)
    else:
        print("UNSAT.")
