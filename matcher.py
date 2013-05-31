#---------------------------------------------------------------
# Project         : eDeploy
# File            : matcher.py
# Copyright       : (C) 2013 by eNovance
# Author          : Frederic Lepied
# Created On      : Fri May 31 23:16:40 2013
#---------------------------------------------------------------

'''Functions to match according to a requirement specification.'''


def match_line(line, specs, arr):
    'Match a line according to a spec and store variables in <var>.'
    # match a line without variable
    for idx in range(len(specs)):
        if line == specs[idx]:
            del specs[idx]
            return True
    # match a line with a variable
    for sidx in range(len(specs)):
        spec = specs[sidx]
        for idx in range(4):
            if spec[idx][0] == '$':
                varidx = idx
            elif line[idx] != spec[idx]:
                break
        else:
            arr[spec[varidx][1:]] = line[varidx]
            del specs[sidx]
            return arr
    return False


def match_all(lines, specs, arr):
    'Match all lines according to a spec and store variables in <var>.'
    for line in lines:
        match_line(line, specs, arr)
    return (specs == [])

# matcher.py ends here
