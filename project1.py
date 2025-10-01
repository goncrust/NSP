#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from pysat.formula import WCNF, IDPool
from pysat.pb import PBEnc
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


# For each shift:
#   0. Participation of a Nurse N in shift s is a variable xi
#   1. check SUM(N[i]) >= R{s,d}
#   2. check SUM(Mng[i]) >= 1
#   3. For Nurse N, for day d, cannot participate in shift x and y, being y > x+1 (y is any value greater than x+1)
#   4. For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
#   5. For Nurse N, SUM(x[i]) <= H(N)
#   6. For Nurse N, for shift s in day d, if Nurse is unavailable, associated var is set to False
#   7. The SUM of positive values in P is minimized

def get_vals_x(vpool: IDPool, x: int):
    return vpool.obj(abs(x))

def print_output(model,cost,vpool):
    participants = [[[] for _ in range(S)] for _ in range(D)]
    for lit in model:
        if lit > 0:
            key = get_vals_x(vpool,lit)
            if key:

                day,shift,nurse_id = key
                participants[day][shift].append(nurse_id+1)
    print(cost)
    for d in range(D):
        for s in range (S):
            listToStr = ' '.join([str(element) for element in participants[d][s]])
            print(len(participants[d][s]), listToStr)


def solve(D,S,R,N,P):
    formula = WCNF()
    vpool = IDPool(start_from=1)
    n = len(N)

    def x(d,s,n):
        return vpool.id((d,s,n))
    
    # ::Constraint 0::
    # Create the base variables: Participation of Nurse_k in shift s in day d
    nurse_in_shift = []
    for nurse in range(n):
        day = []
        for d in range(D):
            shift = []
            for s in range(S):
                shift.append(x(d,s,nurse))
            day.append(shift)
        nurse_in_shift.append(day)
        
    #print("Nurses:", nurse_in_shift)
    #print("List P:", P)

######################################################
######################################################

    cycles = 0      # IMPROVE BY REDUCING CYCLES
    nurse_shift_cost = []

    # Create the Constraints
    for i_day in range(D):
        for i_shift in range(S):
            managers = []
            literals = []
            for i_nurse in range(n):
                cycles += 1         # IMPROVE BY REDUCING CYCLES
                nurse_id = x(i_day,i_shift,i_nurse)
                
                # ::Constraint 6::
                # If P{i_nurse,i_shift,i_day} < 0, Nurse is unavailable in this shift in this day
                if P[i_day][i_shift][i_nurse] < 0:
                    formula.append([-nurse_id])

                # ::Constraint 7::
                # Minimize cost of assignment
                formula.append([-nurse_id], weight=P[i_day][i_shift][i_nurse])
                
                literals.append(nurse_id)

                if N[i_nurse].is_mngr:
                    managers.append(nurse_id)
                
                # ::Constraint 3::
                # Nurses can only do continuous shifts, so no 1-0-...-0-1 shift scheme in a day (~xi[s-1] \/ xi[s] \/ xi[s+1])
                if i_shift != (S-1):
                    for d in range(i_shift+2,S):
                        formula.append([-x(i_day,i_shift,i_nurse),x(i_day,i_shift+1,i_nurse),-x(i_day,d,i_nurse)])
                
                nurse_day = []
                if (i_shift == 0):
                    l_min, l_max = N[i_nurse].l_min, N[i_nurse].l_max
                    for j in range(S):
                        cycles += 1         # IMPROVE BY REDUCING CYCLES
                        nurse_day.append(x(i_day,i_shift+j,i_nurse))
                    
                    # ::Constraint 4::
                    # For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
                    formula.extend(CardEnc.atleast(lits=nurse_day, vpool=vpool, bound=l_min, encoding=EncType.seqcounter).clauses)
                    formula.extend(CardEnc.atmost(lits=nurse_day, vpool=vpool, bound=l_max, encoding=EncType.seqcounter).clauses)
                    
                
                nurse_total = []
                if (i_shift == 0 and i_day == 0):
                    total_max = N[i_nurse].h
                    #print("First shift of the Nurse:",nurse_id)
                    for j in range(D*S):
                        cycles += 1         # IMPROVE BY REDUCING CYCLES
                        nurse_total.append(nurse_id+j)

                    # ::Constraint 5::
                    # For Nurse N, SUM(x[i]) <= H(N)
                    formula.extend(CardEnc.atmost(lits=nurse_total, vpool=vpool, bound=total_max, encoding=EncType.seqcounter).clauses)

            #print("Literals:", literals)

            # ::Constraint 1::
            # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift}
            formula.extend(CardEnc.atleast(lits=literals, vpool=vpool, bound=R[i_day][i_shift], encoding=EncType.seqcounter).clauses)

            # ::Contraint 2::
            # For shift s in day d, add constraint: SUM(Mng[i]) >= 1
            formula.extend(CardEnc.atleast(lits=managers, vpool=vpool, bound=1, encoding=EncType.seqcounter).clauses)

    #print("Hard Clauses:", formula.hard)
    #print("Soft Clauses:", formula.soft)
    #print("Number of Vars:", formula.nv)
    #print("Number of Hard Clauses:", len(formula.hard))
    #print("Number of Soft Clauses:", len(formula.soft))
    #print("Number of cycles:", cycles)   # IMPROVE BY REDUCING CYCLES

######################################################
######################################################

    solver = RC2(formula)

    model = solver.compute()
    cost = solver.cost
    print_output(model,cost, vpool)
    
    solver.add_clause([-model[i] for i in range(len(model))])
    model = solver.compute()
    cost = solver.cost
    print_output(model,cost,vpool)


    
    #print("Model:", model)
    #print("Cost:", cost)
    


D,S,R,N,P = parse_input()
solve(D,S,R,N,P)
