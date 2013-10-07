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

import sys
sys.path.append('../models')
import os
from tempfile import mkstemp
import subprocess
import atexit

from models import models


class BaseReport:
    def __init__(self, items):
        self.items = items
        
    def __add__(self, other):
        """Ability to concatenate easily reports"""
        return BaseReport(self.items + other.items)
        
    def generate_report(self, output_prefix):
        """generates the report"""
        for i in range(len(self.items)):
            item = self.items[i]
            output = output_prefix + "_%i.png" % i
            self._generate_graph(item, output)

        
    def _generate_graph(self, item, output):
        """generates a single graph"""
        s = models[item[0]](self.data, list(item[1]))
        gnuplot_script = s()
        output_line = "set output '%s'\n" % output
        gnuplot_script = output_line + gnuplot_script
        fd, filename = mkstemp(text = True)
        f = open(filename, 'w')
        f.write(gnuplot_script)
        f.close()
        os.close(fd)
        cmd = subprocess.Popen('gnuplot %s' % filename,
                               shell=True,
                               stdout=subprocess.PIPE)
#        while True:
#            cmd.poll()
#            if cmd.returncode is not None:
#                os.unlink(filename)
#                break
