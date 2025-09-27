#!/usr/bin/python3
# alc25 - 5 - project1
# DO NOT remove or edit the lines above. Thank you.

import sys
from dataclasses import dataclass


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

    return D, S, R, N, P
