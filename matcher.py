#---------------------------------------------------------------
# Project         : eDeploy
# File            : matcher.py
# Copyright       : (C) 2013 by eNovance
# Author          : Frederic Lepied
# Created On      : Fri May 31 23:16:40 2013
#---------------------------------------------------------------

'''Functions to match according to a requirement specification.'''


def match_spec(spec, lines, arr):
    'Match a line according to a spec and store variables in <var>.'
    # match a line without variable
    for idx in range(len(lines)):
        if lines[idx] == spec:
            del lines[idx]
            return True
    # match a line with a variable
    for lidx in range(len(lines)):
        line = lines[lidx]
        varidx = []
        for idx in range(4):
            if spec[idx][0] == '$':
                if spec[idx][1:] in arr:
                    if arr[spec[idx][1:]] != line[idx]:
                        break
                varidx.append(idx)
            elif line[idx] != spec[idx]:
                break
        else:
            for i in varidx:
                arr[spec[i][1:]] = line[i]
            del lines[lidx]
            return True
    return False


def match_all(lines, specs, arr):
    'Match all lines according to a spec and store variables in <var>.'
    for spec in specs:
        if not match_spec(spec, lines, arr):
            return(False)
    return True

# matcher.py ends here
