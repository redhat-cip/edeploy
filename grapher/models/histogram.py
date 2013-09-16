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

"""Basic bar chart"""

from scatterplot import ScatterPlot
from basegraph import localpath


template = localpath + '/gnuplot_templates/histogram.template'

class Histogram(ScatterPlot):
    def __init__(self, data, keys):
        super(ScatterPlot, self).__init__(template, data, keys)

    def prepare_data(self, data, keys):
        dic = {}
        for element in data:
            if all(map(lambda x,y: x.startswith(y),
                       element[:-1],
                       keys)):
#TODO Assuming elements always have 4 elements. This sucks and should be
# generalized.
                dic[element[1]] = dic.get(element[1], {})
                dic[element[1]][element[2]] = element[-1]
        tmp_dict = {}
        for v in dic:
            tmp_dict.update(dict([(u,0) for u in dic[v].keys()]))
        columns = tmp_dict.keys()
        clean_data = [ ['"%s"' % ' '.join(keys),] + columns ]
        for u in dic.keys():
            clean_data.append([u,] + [dic[u][c] for c in columns])
        
        return clean_data        
        
    def __call__(self):
        values = "\n".join(" ".join(u) for u in self.data)
        dic = {'title': ' '.join(self.keys),
               'extras': '',
               'values' : values}
        columns = self.data[0]
        col_count = 3
        for i in columns[2:]:
            dic['extras'] += ", '' u %i ti col" % col_count
            col_count += 1
        return self.template % dic
