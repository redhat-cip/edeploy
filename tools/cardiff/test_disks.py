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

import utils
import check
import compare_sets


def load_samples(bench_values):
    for health in utils.find_file('tools/cardiff/sample', '*.hw_'):
        bench_values.append(eval(open(health).read()))


class TestDetect(unittest.TestCase):

    def test_firmware(self):
        l = []
        load_samples(l)
        result = compare_sets.compare(check.search_item(utils.find_sub_element(l, 'firmware'), "firmware", "(.*)"))
        self.assertEqual(
            result,
            {"set([('firmware', 'bios', 'date', '09/18/2013'), \
('firmware', 'bios', 'version', 'I31'), \
('firmware', 'bios', 'vendor', 'HP')])": ['CZ3404YWP4', 'CZ3404YWNW', 'CZ3404YWP6', 'CZ3404YWNR', 'CZ3404YWP2', 'CZ3404YWPS', 'CZ3404YWP8', 'CZ3404YWPX', 'CZ3404YWNT', 'CZ3404YWR0', 'CZ3404YWPE', 'CZ3404YWPA', 'CZ3404YWPP', 'CZ3404YWPC', 'CZ3404YWNN', 'CZ3404YWPM', 'CZ3404YWPV', 'CZ3404YWPH', 'CZ3404YWPK']})

    def test_systems(self):
        l = []
        load_samples(l)
        result = compare_sets.compare(check.search_item(utils.find_sub_element(l, 'system'), "system", "(.*)", ['serial']))
        self.assertEqual(
            result,
            {"set([('system', 'ipmi', 'channel', '2'), \
('system', 'product', 'name', 'ProLiant BL460c Gen8 (641016-B21)'), \
('system', 'product', 'vendor', 'HP')])": ['CZ3404YWP4', 'CZ3404YWNW', 'CZ3404YWP6', 'CZ3404YWNR', 'CZ3404YWP2', 'CZ3404YWPS', 'CZ3404YWP8', 'CZ3404YWPX', 'CZ3404YWNT', 'CZ3404YWR0', 'CZ3404YWPE', 'CZ3404YWPA', 'CZ3404YWPP', 'CZ3404YWPC', 'CZ3404YWNN', 'CZ3404YWPM', 'CZ3404YWPV', 'CZ3404YWPH', 'CZ3404YWPK']} )

    def test_logical_disks(self):
        l = []
        load_samples(l)
        result = compare_sets.compare(check.search_item(utils.find_sub_element(l, 'disk'), "disk", "sd(\S+)", ['simultaneous', 'standalone']))
        self.assertEqual(
            result,
            {"set([('disk', 'sdb', 'Write Cache Enable', '0'), \
('disk', 'sdb', 'model', 'LOGICAL VOLUME'), \
('disk', 'sdb', 'rev', '4.68'), \
('disk', 'sdb', 'size', '299'), \
('disk', 'sda', 'Write Cache Enable', '0'), \
('disk', 'sdb', 'vendor', 'HP'), \
('disk', 'sda', 'rev', '4.68'), \
('disk', 'sda', 'Read Cache Disable', '0'), \
('disk', 'sdb', 'Read Cache Disable', '0'), \
('disk', 'sda', 'vendor', 'HP'), \
('disk', 'sda', 'model', 'LOGICAL VOLUME'), \
('disk', 'sda', 'size', '299')])": ['CZ3404YWP4', 'CZ3404YWNW', 'CZ3404YWP6', 'CZ3404YWNR', 'CZ3404YWP2', 'CZ3404YWPS', 'CZ3404YWP8', 'CZ3404YWPX', 'CZ3404YWNT', 'CZ3404YWR0', 'CZ3404YWPE', 'CZ3404YWPA', 'CZ3404YWPP', 'CZ3404YWPC', 'CZ3404YWNN', 'CZ3404YWPM', 'CZ3404YWPV', 'CZ3404YWPH', 'CZ3404YWPK']})

    def test_hp_physical_disks(self):
        l = []
        load_samples(l)
        result = compare_sets.compare(check.search_item(utils.find_sub_element(l, 'disk'), "disk", "(\d+)I:(\d+):(\d+)"))
        self.assertEqual(
            result,
            {"set([('disk', '1I:1:3', 'size', '1000'), \
('disk', '1I:1:7', 'slot', '3'), \
('disk', '1I:1:2', 'type', 'SATA'), \
('disk', '1I:1:8', 'type', 'SATA'), \
('disk', '1I:1:4', 'size', '1000'), \
('disk', '1I:1:3', 'slot', '3'), \
('disk', '1I:1:2', 'size', '300'), \
('disk', '1I:1:1', 'type', 'SATA'), \
('disk', '1I:1:4', 'type', 'SATA'), \
('disk', '1I:1:6', 'slot', '3'), \
('disk', '1I:1:5', 'slot', '3'), \
('disk', '1I:1:5', 'size', '1000'), \
('disk', '1I:1:5', 'type', 'SATA'), \
('disk', '1I:1:3', 'type', 'SATA'), \
('disk', '1I:1:2', 'type', 'SAS'), \
('disk', '1I:1:6', 'type', 'SATA'), \
('disk', '1I:1:1', 'size', '1000'), \
('disk', '1I:1:1', 'size', '300'), \
('disk', '1I:1:6', 'size', '1000'), \
('disk', '1I:1:4', 'slot', '3'), \
('disk', '1I:1:8', 'size', '1000'), \
('disk', '1I:1:1', 'slot', '0'), \
('disk', '1I:1:2', 'slot', '3'), \
('disk', '1I:1:1', 'slot', '3'), \
('disk', '1I:1:2', 'size', '1000'), \
('disk', '1I:1:2', 'slot', '0'), \
('disk', '1I:1:7', 'size', '1000'), \
('disk', '1I:1:7', 'type', 'SATA'), \
('disk', '1I:1:8', 'slot', '3'), \
('disk', '1I:1:1', 'type', 'SAS')])": ['CZ3404YWNW'], \
            "set([('disk', '1I:1:2', 'type', 'SAS'), \
('disk', '1I:1:1', 'slot', '0'), \
('disk', '1I:1:2', 'size', '300'), \
('disk', '1I:1:2', 'slot', '0'), \
('disk', '1I:1:1', 'size', '300'), \
('disk', '1I:1:1', 'type', 'SAS')])": ['CZ3404YWP4', 'CZ3404YWP6', 'CZ3404YWNR', 'CZ3404YWP2', 'CZ3404YWPS', 'CZ3404YWP8', 'CZ3404YWPX', 'CZ3404YWNT', 'CZ3404YWR0', 'CZ3404YWPE', 'CZ3404YWPA', 'CZ3404YWPP', 'CZ3404YWPC', 'CZ3404YWNN', 'CZ3404YWPM', 'CZ3404YWPV', 'CZ3404YWPH', 'CZ3404YWPK']})
