#---------------------------------------------------------------
# Project         : eDeploy
# File            : matcher.py
# Copyright       : (C) 2013 by eNovance
# Author          : Frederic Lepied
# Created On      : Fri May 31 23:16:40 2013
#---------------------------------------------------------------

'''Functions to match according to a requirement specification.'''

import re
import sys
try:
    import ipaddr2
    _HAS_IPADDR = True
except ImportError:
    _HAS_IPADDR = False

_FUNC_REGEXP = re.compile(r'^(.*)\((.*)\)')


def _adder(array, index, value):
    'Auxiliary function to add a value to an array.'
    array[index] = value


def _appender(array, index, value):
    'Auxiliary function to append a value to an array.'
    try:
        array[index].append(value)
    except KeyError:
        array[index] = [value, ]


def _gt(left, right):
    'Helper for match_spec.'
    return int(left) > int(right)


def _ge(left, right):
    'Helper for match_spec.'
    return int(left) >= int(right)


def _lt(left, right):
    'Helper for match_spec.'
    return int(left) < int(right)


def _le(left, right):
    'Helper for match_spec.'
    return int(left) <= int(right)


def _network(left, right):
    'Helper for match_spec.'
    if _HAS_IPADDR:
        return ipaddr.IPv4Address(left) in ipaddr.IPv4Network(right)
    else:
        return False

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
            # Match a variable
            if spec[idx][0] == '$':
                if adder == _adder and spec[idx][1:] in arr:
                    if arr[spec[idx][1:]] != line[idx]:
                        break
                varidx.append(idx)
            # Match a function
            elif spec[idx][-1] == ')':
                res = _FUNC_REGEXP.search(spec[idx])
                if res:
                    func_name = '_' + res.group(1)
                    if not (func_name in globals() and
                            globals()[func_name](line[idx], res.group(2))):
                        break
            # Match the full string
            elif line[idx] != spec[idx]:
                break
        else:
            for i in varidx:
                adder(arr, spec[i][1:], line[i])
            del lines[lidx]
            return True
    return False


def match_all(lines, specs, arr, arr2, debug=False):
    '''Match all lines according to a spec and store variables in
<arr>. Variables starting with 2 $ like $$vda are stored in arr and
arr2.'''
    # Work on a copy of lines to avoid changing the real lines because
    # match_spec removes the matched line to not match it again on next
    # calls.
    lines = list(lines)
    for spec in specs:
        if not match_spec(spec, lines, arr):
            if debug:
                sys.stderr.write('spec: %s not matched\n' % str(spec))
            return(False)
    for key in arr:
        if key[0] == '$':
            nkey = key[1:]
            arr[nkey] = arr[key]
            arr2[nkey] = arr[key]
            del arr[key]
    return True


def match_multiple(lines, spec, arr):
    'Use spec to find all the matching lines and gather variables.'
    ret = False
    lines = list(lines)
    while match_spec(spec, lines, arr, adder=_appender):
        ret = True
    return ret

# matcher.py ends here
