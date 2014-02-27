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
from basegraph import prettify_keys as p_k
from basegraph import comp_fnc


template = localpath + '/gnuplot_templates/histogram.template'


class Histogram(ScatterPlot):
    def __init__(self, data, keys):
        super(ScatterPlot, self).__init__(template, data, keys)

    def prepare_data(self, data, keys):
        dic = {}
        for element in data:
            if all(map(lambda x, y: x.startswith(y),
                       element[1:-1],
                       keys)):
#TODO Assuming elements always have 5 elements. This sucks and should be
# generalized.
# reminder: element0: file name | element1: hardware name | element2: metric
                metric = '"%s"' % (element[2] + ' ' + p_k(element[3]))
                dic[metric] = dic.get(metric, {})
                dic[metric][element[0]] = element[-1]
        tmp_dict = {}
        for v in dic:
            tmp_dict.update(dict([(w, 0) for w in dic[v].keys()]))
        columns = tmp_dict.keys()
        clean_data = [["metric", ] + columns]
        for u in sorted(dic.keys(), key=comp_fnc):
            clean_data.append([u, ] + [dic[u][c] for c in columns])

        return clean_data

    def __call__(self):
        columns = self.data[0]
        values_tmp = []
        for u in self.data:
            values_tmp.append(" ".join(str(v) for v in u))
        value_set = "\n".join(values_tmp)
        #value_set = "\n".join(" ".join(u)for u in self.data)
        # There is something wrong in the way gnuplot handles inline data
        # when used multiple times, the easy fix is to repeat the data as needed

        values = '\nEOF\n'.join(value_set for i in columns[1:])
        col_count = 3
        dic = {'title': ' '.join(self.keys),
               'extras': '',
               'values': values}
        for i in columns[2:]:
            dic['extras'] += ", '-' u %i ti col" % col_count
            col_count += 1
        return self.template % dic
