#---------------------------------------------------------------
# Project         : eDeploy
# File            : matcher.py
# Copyright       : (C) 2013 by eNovance
# Author          : Frederic Lepied
# Created On      : Fri May 31 23:16:40 2013
#---------------------------------------------------------------

'''Functions to match according to a requirement specification.'''


def _adder(array, index, value):
    'Auxiliary function to add a value to an array.'
    array[index] = value


def _appender(array, index, value):
    'Auxiliary function to append a value to an array.'
    try:
        array[index].append(value)
    except KeyError:
        array[index] = [value, ]


def match_spec(spec, lines, arr, adder=_adder):
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
                if adder == _adder and spec[idx][1:] in arr:
                    if arr[spec[idx][1:]] != line[idx]:
                        break
                varidx.append(idx)
            elif line[idx] != spec[idx]:
                break
        else:
            for i in varidx:
                adder(arr, spec[i][1:], line[i])
            del lines[lidx]
            return True
    return False


def match_all(lines, specs, arr):
    'Match all lines according to a spec and store variables in <var>.'
    # Work on a copy of lines to avoid changing the real lines because
    # match_spec removes the matched line to not match it again on next
    # calls.
    lines = list(lines)
    for spec in specs:
        if not match_spec(spec, lines, arr):
            return(False)
    return True


def match_multiple(lines, spec, arr):
    'Use spec to find all the matching lines and gather variables.'
    ret = False
    lines = list(lines)
    while match_spec(spec, lines, arr, adder=_appender):
        ret = True
        print spec, lines
    return ret

# matcher.py ends here
