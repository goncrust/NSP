#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass
from pysat.formula import WCNF, IDPool
from pysat.pb import PBEnc
from pysat.card import EncType, CardEnc

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
#   3. For Nurse N, for day d, cannot participate in shift x and y, being y > x+1 (y is any value greater than x+1)
#   4. For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
#   5. For Nurse N, SUM(x[i]) <= H(N)
#   6. For Nurse N, for shift s in day d, if Nurse is unavailable, associated var is set to False
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
        
    print("Nurses:", nurse_in_shift)
    #print("List P:", P)

    cycles = 0      # IMPROVE BY REDUCING CYCLES

    # Create the Hard Constraints
    for i_day in range(D):
        for i_shift in range(S):
            #print("Day " + str(i_day) + ", Shift " +  str(i_shift) + ", Req. " + str(R[i_day][i_shift]))

            managers = []
            literals = []
            for i_nurse in range(n):
                cycles += 1         # IMPROVE BY REDUCING CYCLES
                nurse_id = x(i_day,i_shift,i_nurse)
                
                # ::Constraint 6::
                # If P{i_nurse,i_shift,i_day} < 0, Nurse is unavailable in this shift in this day
                if P[i_day][i_shift][i_nurse] < 0:
                    formula.append([-nurse_id])
                    continue

                literals.append(nurse_id)

                if N[i_nurse].is_mngr:
                    managers.append(nurse_id)
                
                # ::Constraint 3::
                # Nurses can only do continuous shifts, so no 1-0-1 shift scheme in a day (~xi[s-1] \/ xi[s] \/ xi[s+1])
                if i_shift not in [0,S-1]:
                    clause = [-(nurse_id-1),nurse_id,-(nurse_id+1)]
                    #print("DEBUG:",i_shift, clause)
                    formula.append(clause)
                
                nurse_day = []
                if (nurse_id % 4 == 1):
                    l_min, l_max = N[i_nurse].l_min, N[i_nurse].l_max
                    for j in range(S):
                        cycles += 1         # IMPROVE BY REDUCING CYCLES
                        nurse_day.append(nurse_id+j)
                    
                    # ::Constraint 4::
                    # For Nurse N, for day d, SUM(x[i]) >= Lmin && SUM(x[i]) <= Lmax
                    enc = CardEnc.atleast(lits=nurse_day, vpool=vpool, bound=l_min, encoding=EncType.seqcounter)   # Encoding Type could be another!
                    #print("Nurse " + str(i_nurse) + " min of " + str(l_min), enc.clauses)
                    formula.extend(enc.clauses)
                    
                    enc = CardEnc.atmost(lits=nurse_day, vpool=vpool, bound=l_max, encoding=EncType.seqcounter)   # Encoding Type could be another!
                    #print("Nurse " + str(i_nurse) + " max of " + str(l_max), enc.clauses)
                    formula.extend(enc.clauses)
                
                nurse_total = []
                if (nurse_id % 12 == 1):
                    total_max = N[i_nurse].h
                    #print("First shift of the Nurse:",nurse_id)
                    for j in range(D*S):
                        cycles += 1         # IMPROVE BY REDUCING CYCLES
                        nurse_total.append(nurse_id+j)

                    # ::Constraint 5::
                    # For Nurse N, SUM(x[i]) <= H(N)
                    enc = CardEnc.atmost(lits=nurse_total, vpool=vpool, bound=total_max, encoding=EncType.seqcounter)   # Encoding Type could be another!
                    #print("Nurse " + str(i_nurse) + " total max of " + str(total_max), enc.clauses)
                    formula.extend(enc.clauses)
               
            #print("Literals:", literals)

            # ::Constraint 1::
            # For R{day,shift}, add constraints: SUM(x{day,shift}) >= R{day,shift} (atleast, for literals in reference with shift s of day d)
            enc = CardEnc.atleast(lits=literals, vpool=vpool, bound=R[i_day][i_shift], encoding=EncType.seqcounter)   # Encoding Type could be another!
            #print("Minimum Required:", enc.clauses)
            formula.extend(enc.clauses)

            # ::Contraint 2::
            # For shift s in day d, add constraint: SUM(Mng[i]) >= 1 (for the nurses possibly involved in the shift, the sum of the manager variables is at least 1)
            enc = CardEnc.atleast(lits=managers, vpool=vpool, bound=1, encoding=EncType.seqcounter)   # Encoding Type could be another!
            #print("Managers:", enc.clauses)
            formula.extend(enc.clauses)

    #print("Hard Clauses:", formula.hard)
    print("Number of Vars:", formula.nv)
    print("Number of Hard Clauses:", len(formula.hard))
    print("Number of Soft Clauses:", len(formula.soft))
    print("Number of cycles:", cycles)   # IMPROVE BY REDUCING CYCLES


        
        
    

D,R,S,N,P = parse_input()
hard_constraints(D,R,S,N,P)
