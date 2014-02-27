#!/usr/bin/env python
#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Matthieu Huin <mhu@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Graph base class"""

import os
path = os.path.abspath(__file__)
localpath = os.path.dirname(path)

import re

def prettify_keys(string):
    """Utility function used to clean keys with numerical values, so that
       they can be ordered alphabetically the way they should be."""
    r = re.compile("bandwidth_([0-9]{1,3})")
    def replacer(match):
        m = match.groups()[0]
        return "bandwidth " + m
    return r.sub(replacer, string)
       
def comp_fnc(x):
    """Comparison function between keys."""
    r = re.compile("[0-9]+[KMG]")
    units = {"G": 10**9,
             "M": 10**6,
             "K": 10**3}
    if r.search(x):
        size = x.split(" ")[-1]
        prefix = " ".join(x.split(" ")[:-1])
        x_size = int(size[:-2]) * units.get(size[-2], 1)
        return prefix + str(x_size).rjust(10,"0")
    return x            

class BaseGraph(object):
    def __init__(self, template, data, keys):
        """@param template: a gnuplot template file used to draw the data.
           @param data: the data, as formatted by the eDeploy bench tool.
           It is expected to be a list of tuples of the following form:
           (file, hardware type, hardware name, metric, value)
           @param keys: the keys to look for in the data handed over by eDeploy
           formatted as an "ordered" list (meaning order matters).
           Every entry matching the beginning of the keys will be used for
           generating the graph.
           Example: ('cpu', 'logical', 'bandwidth') will pick every bandwidth
           measurement for every logical cpu.
        """
        self.template = open(template, 'r').read()
        self.name = self.__class__.__name__
        self.data = self.prepare_data(data, keys)
        self.keys = keys
        
    def prepare_data(self, data, keys):
        """Format data to a usable form, if needed."""
        if all(len(d) == 4 for d in data):
            clean_data = [('',) + d for d in data]
        return clean_data
    
    def __call__(self):
        """returns a gnuplot file that can be used to draw the graph."""
        raise NotImplementedError
        
