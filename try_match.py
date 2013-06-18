#!/usr/bin/python
import sys
import matcher

specs = eval(open(sys.argv[2], 'r').read(-1))
hw_items = eval(open(sys.argv[1], 'r').read(-1))

var = {}
var2 = {}
if matcher.match_all(hw_items, specs, var, var2):
    print var
else:
    print False

