#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from pysat.formula import WCNF, IDPool
from pysat.pb import PBEnc, EncType

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


# Each shift s of day d has at least R{s,d} Nurses assigned to it
# R{s,d} generates a Shift Table with requirements, for each one of them, there are n variables associated with participation 
# For each shift s:
#   0. Participation of a Nurse N in shift s is a variable xi
#   1. check SUM(N[i]) >= R{s,d}
#   2. check SUM(Mng[i]) >= 1
#  
# For each Nurse N:
#   0. Participation of a Nurse N in shift s is a variable xi, the same variable as before
#   1. For Nurse N, for day d, cannot participate in shift x and y, being y > x+1 (y is any value greater than x+1)
#   2. For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
#   3. For Nurse N, SUM(x[i]) <= H(N)
#   4. For Nurse N, for shift s in day d, if Nurse is unavailable, associated var is set to False
#
# Variables to use:
# Participation of Nurse n in shift s of day d. For example, for 3 days with 2 shifts each, there's gonna be 6 total shifts. For 4 Nurses, there's 24 variables
# Additionaly, there's n more variables, associated with the managerial property of some nurses, i.e. x25 indicates if Nurse 1 is a Manager
# Also, each of the initial s*d*n vars has an associated weight, this being the cost of turning it to 1

def hard_constraints(D,S,R,N,P):
    formula = WCNF()
    vpool = IDPool(start_from=1)
    n = len(N)

    def x(d,s,n):
        return vpool.id(('x',d,s,n))
    
    #nurse_in_shift = lambda i,j,k:  vpool.id('nurse_in_shift{0}@{1}@{2}'.format(i,j,k))
    nurse_in_shift = []

    for nurse in range(n):
        day = []
        for d in range(D):
            shift = []
            for s in range(S):
                shift.append(x(d,s,nurse))
            day.append(shift)
        nurse_in_shift.append(day)
        
    print("Nurses:", nurse_in_shift)
    #print("Shift 10:", [vpool.id((1,0,n)) for n in range(n)])

    for i_day in range(D):
        for i_shift in range(S):
            print("Day " + str(i_day) + ", Shift " +  str(i_shift) + ", Req. " + str(R[i_day][i_shift]))

            managers = []
            literals = []
            for i_nurse in range(n):
                literals.append(x(i_day,i_shift,i_nurse))
                if N[i_nurse].is_mngr:
                    managers.append(x(i_day,i_shift,i_nurse))
            
            # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift} (atleast, for literals in reference with shift s of day d)
            enc = PBEnc.atleast(lits=literals, vpool=vpool, bound=R[i_day][i_shift], encoding=EncType.seqcounter)   # Encoding Type could be another!
            print("Minimum Required:", enc.clauses)
            formula.extend(enc.clauses)

            
            # For shift s in day d, add constraint: SUM(Mng[i]) >= 1 (for the nurses possibly involved in the shift, the sum of the manager variables is at least 1)
            enc = PBEnc.atleast(lits=managers, vpool=vpool, bound=1, encoding=EncType.seqcounter)   # Encoding Type could be another!
            print("Managers:", enc.clauses)
            formula.extend(enc.clauses)

            
        
        
    

D,R,S,N,P = parse_input()
hard_constraints(D,R,S,N,P)
