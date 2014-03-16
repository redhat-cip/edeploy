#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Erwan Velu <erwan.velu@enovance.com>
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

import unittest

import perf_cpu_tables


class TestPerfLevel(unittest.TestCase):

    def test_cpu(self):
        cpu_type = "Intel(R) Xeon(R) CPU E5-2650 0 @ 2.00GHz"
        cpu_perf = perf_cpu_tables.get_cpu_min_perf("loops_per_sec", cpu_type)
        self.assertEqual(cpu_perf, 450)

    def test_cpu1(self):
        cpu_type = "Intel(R) Xeon(R) CPU E5-2650 0 @ 2.20GHz"
        cpu_perf = perf_cpu_tables.get_cpu_min_perf("loops_per_sec", cpu_type)
        self.assertEqual(cpu_perf, 420)

    def test_cpu2(self):
        cpu_type = "Intel(R) Xeon(R) CPU E5-2750 0 @ 2.20GHz"
        cpu_perf = perf_cpu_tables.get_cpu_min_perf("loops_per_sec", cpu_type)
        self.assertEqual(cpu_perf, 400)

    def test_cpu3(self):
        cpu_type = "Intel(R) Xeon(R) CPU E7-2750 0 @ 2.20GHz"
        cpu_perf = perf_cpu_tables.get_cpu_min_perf("loops_per_sec", cpu_type)
        self.assertEqual(cpu_perf, 300)

    def test_cpu4(self):
        cpu_type = "Intel(R) Leon(R) CPU E7-2750 0 @ 2.20GHz"
        cpu_perf = perf_cpu_tables.get_cpu_min_perf("loops_per_sec", cpu_type)
        self.assertEqual(cpu_perf, 0)
