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

from basereport import BaseReport

#TODO define reports accurately. These are just stubs to make sure
# the logic is correctly implemented.

memory_report = BaseReport([['histogram', ('memory', 'DDR', 'tRFC')]])
cpu_report = BaseReport([['histogram', ('cpu', 'logical', 'bandwidth_1M')]])
disk_report = BaseReport([['histogram', ('disk', 'sd', 'standalone_randread')],
                          ['histogram', ('disk', 'sd', 'standalone_read')]])

reports = {"cpu"   : cpu_report,
           "memory": memory_report,
           "disk"  : disk_report,
           "all"   : cpu_report + disk_report + memory_report}
