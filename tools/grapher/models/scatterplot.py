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

"""Basic scatter plot"""

from basegraph import BaseGraph
from basegraph import localpath


template = localpath + '/gnuplot_templates/scatterplot.template'

class ScatterPlot(BaseGraph):
    def __init__(self, data, keys):
        super(ScatterPlot, self).__init__(template, data, keys)

    def prepare_data(self, data, keys):
        clean_data = []
#        xaxis = {}
#        xcounter = 0
        for element in data:
            if all(map(lambda x,y: x.startswith(y),
                       element[1:-1],
                       keys)):
#                if ' '.join(element[:-1]) not in xaxis:
#                    xcounter +=1
#                    xaxis[' '.join(element[:-1])] = xcounter
                #TODO better x axis naming
                clean_data.append((' '.join(element[:-1]),
                                   float(element[-1])))
        return clean_data

    def __call__(self):
        values = "\n".join('"%s" %s' % u for u in self.data)
        dic = {'title': ' '.join(self.keys),
               'plot_title': self.keys[-1],
               'values' : values}
        return self.template % dic
