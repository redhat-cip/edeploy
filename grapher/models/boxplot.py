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

"""Boxplot chart. From gnuplot's documentation:

Boxplots are a common way to represent a statistical dis-
tribution of values. Quartile boundaries are determined
such that 1/4 of the points have a value equal or less
than the first quartile boundary, 1/2 of the points have
a value equal or less than the second quartile (median)
value, etc. A box is drawn around the region between
the first and third quartiles, with a horizontal line at
the median value. Whiskers extend from the box to
user-specified limits. Points that lie outside these limits
are drawn individually."""

from scatterplot import ScatterPlot
from basegraph import localpath


template = localpath + '/gnuplot_templates/boxplot.template'


class BoxPlot(ScatterPlot):
    def __init__(self, data, keys):
        super(ScatterPlot, self).__init__(template, data, keys)

    def prepare_data(self, data, keys):
        clean_data = []
        for element in data:
            if all(map(lambda x, y: x.startswith(y),
                       element[1:-1],
                       keys)):
#TODO Assuming elements always have 5 elements. This sucks and should be
# generalized.
                clean_data.append(('"%s"' % element[-2],
                                   element[-1],
                                   element[0]))
        return clean_data

    def __call__(self):
        values = "\n".join(" ".join(u) for u in self.data)
        dic = {'title': ' '.join(self.keys),
               'extras': '',
               'values': values}
        return self.template % dic
