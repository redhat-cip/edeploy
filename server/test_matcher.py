#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
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

import matcher


class TestMatcher(unittest.TestCase):

    def test_equal(self):
        lines = [('system', 'product', 'serial', 'CZJ31402CD')]
        spec = ('system', 'product', 'serial', 'CZJ31402CD')
        arr = {}
        self.assertTrue(matcher.match_spec(spec, lines, arr))

    def test_not_equal(self):
        lines = [('system', 'product', 'serial', 'CZJ31402CD')]
        spec = ('system', 'product', 'serial', 'CZJ31402CE')
        arr = {}
        self.assertFalse(matcher.match_spec(spec, lines, arr))

    def test_var(self):
        lines = [('disk', '1I:1:1', 'size', '1000GB')]
        spec = ('disk', '$disk8', 'size', '1000GB')
        arr = {}
        self.assertTrue(matcher.match_spec(spec, lines, arr))
        self.assertEqual(arr, {'disk8': '1I:1:1'})

    def test_vars(self):
        lines = [
            ('system', 'product', 'serial', 'CZJ31402CD'),
            ('disk', '1I:1:1', 'size', '1000GB'),
            ('disk', '1I:1:1', 'type', 'SATA'),
            ('disk', '1I:1:1', 'control', 'hpa'),
            ('disk', '1I:1:2', 'size', '1000GB'),
            ('disk', '1I:1:2', 'type', 'SATA'),
            ('disk', '1I:1:2', 'control', 'hpa'),
            ('disk', '1I:1:3', 'size', '1000GB'),
            ('disk', '1I:1:3', 'type', 'SATA'),
            ('disk', '1I:1:3', 'control', 'hpa'),
            ('disk', '1I:1:4', 'size', '1000GB'),
            ('disk', '1I:1:4', 'type', 'SATA'),
            ('disk', '1I:1:4', 'control', 'hpa'),
            ('disk', '2I:1:5', 'size', '1000GB'),
            ('disk', '2I:1:5', 'type', 'SATA'),
            ('disk', '2I:1:5', 'control', 'hpa'),
            ('disk', '2I:1:6', 'size', '1000GB'),
            ('disk', '2I:1:6', 'type', 'SATA'),
            ('disk', '2I:1:6', 'control', 'hpa'),
            ('disk', '2I:1:7', 'size', '100GB'),
            ('disk', '2I:1:7', 'type', 'SSDSATA'),
            ('disk', '2I:1:7', 'control', 'hpa'),
            ('disk', '2I:1:8', 'size', '100GB'),
            ('disk', '2I:1:8', 'type', 'SSDSATA'),
            ('disk', '2I:1:8', 'control', 'hpa'),
            ]
        specs = [('system', 'product', 'serial', 'CZJ31402CD'),
                 ('disk', '$disk1', 'size', '100GB'),
                 ('disk', '$disk2', 'size', '100GB'),
                 ('disk', '$disk3', 'size', '1000GB'),
                 ('disk', '$disk4', 'size', '1000GB'),
                 ('disk', '$disk5', 'size', '1000GB'),
                 ('disk', '$disk6', 'size', '1000GB'),
                 ('disk', '$disk7', 'size', '1000GB'),
                 ('disk', '$disk8', 'size', '1000GB')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr,
                         {'disk1': '2I:1:7',
                          'disk2': '2I:1:8',
                          'disk3': '1I:1:1',
                          'disk4': '1I:1:2',
                          'disk5': '1I:1:3',
                          'disk6': '1I:1:4',
                          'disk7': '2I:1:5',
                          'disk8': '2I:1:6',
                          }
                         )

    def test_already_bound(self):
        lines = [
            ('disk', '1I:1:2', 'size', '100GB'),
            ('disk', '1I:1:1', 'size', '1000GB'),
            ('disk', '1I:1:1', 'control', 'hpa'),
            ('disk', '1I:1:2', 'control', 'hpa'),
            ]
        specs = [
            ('disk', '$disk1', 'size', '100GB'),
            ('disk', '$disk1', 'control', 'hpa'),
            ('disk', '$disk2', 'size', '1000GB'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr,
                         {'disk1': '1I:1:2',
                          'disk2': '1I:1:1',
                          })

    def test_order(self):
        specs = [
            ('disk', '$disk1', 'size', '100'),
            ('disk', '$disk1', 'slot', '$slot1'),
            ('disk', '$disk2', 'size', '1000'),
            ('disk', '$disk2', 'slot', '$slot2'),
            ]
        lines = [
            ('disk', '1I:1:1', 'size', '1000'),
            ('disk', '1I:1:1', 'control', 'hpa'),
            ('disk', '1I:1:1', 'slot', '2'),
            ('disk', '2I:1:8', 'size', '100'),
            ('disk', '2I:1:8', 'control', 'hpa'),
            ('disk', '2I:1:8', 'slot', '2'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))

    def test_2vars(self):
        specs = [
            ('disk', '$disk', 'size', '$size'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr,
                         {'size': '8',
                          'disk': 'vda',
                          })

    def test_2dollars(self):
        specs = [
            ('disk', '$$disk', 'size', '$size'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ]
        arr = {}
        arr2 = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, arr2))
        self.assertEqual(arr,
                         {'size': '8',
                          'disk': 'vda',
                          })
        self.assertEqual(arr2,
                         {'disk': 'vda',
                          })

    def test_multiple_vars(self):
        specs = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '16'),
            ]
        specs2 = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '8'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '8'),
            ]
        arr = {}
        self.assertFalse(matcher.match_all(lines, specs, arr, {}))
        self.assertTrue(matcher.match_all(lines, specs2, arr, {}), lines)

    def test_multiple(self):
        spec = ('disk', '$disk', 'size', '8')
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '8'),
            ]
        arr = {}
        self.assertTrue(matcher.match_multiple(lines, spec, arr))
        self.assertEqual(arr['disk'], ['vda', 'vdb'])

    def test_gt(self):
        specs = [('disk', '$disk', 'size', 'gt(10)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_ge(self):
        specs = [('disk', '$disk', 'size', 'ge(10)')]
        lines = [
            ('disk', 'vda', 'size', '10'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_lt(self):
        specs = [('disk', '$disk', 'size', 'lt(30)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_le(self):
        specs = [('disk', '$disk', 'size', 'le(20)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_network(self):
        specs = [('network', '$eth', 'ipv4', 'network(192.168.2.0/24)')]
        lines = [
            ('network', 'eth0', 'ipv4', '192.168.2.2'),
            ]
        arr = {}
        if matcher._HAS_IPADDR:
            self.assertTrue(matcher.match_all(lines, specs, arr, {}))
            self.assertEqual(arr['eth'], 'eth0')

    def test_le_var(self):
        specs = [('disk', '$disk', 'size', '$size=le(20)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')
        self.assertEqual(arr['size'], '20')

    def test_in(self):
        specs = [('disk', '$disk', 'size', 'in(10, 20, 30)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_in2(self):
        specs = [('disk', '$disk=in("vda", "vdb")', 'size', '20')]
        lines = [
            ('disk', 'vda', 'size', '20'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_backtrack(self):
        specs = [
            ('disk', '$disk', 'size', '8'),
            ('disk', '$disk', 'type', 'b'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vda', 'type', 'a'),
            ('disk', 'vdb', 'size', '8'),
            ('disk', 'vdb', 'type', 'b'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vdb', arr)

    def test_backtrack2(self):
        specs = [
            ('disk', '$disk', 'size', '8'),
            ('disk', '$disk', 'type', 'b'),
            ('disk', '$disk2', 'size', '8'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vda', 'type', 'a'),
            ('disk', 'vdb', 'size', '8'),
            ('disk', 'vdb', 'type', 'b'),
            ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk2'], 'vda', arr)
        self.assertEqual(arr['disk'], 'vdb', arr)

    def test_backtrack3(self):
        specs = [
            ('disk', '$disk', 'size', '8'),
            ('disk', '$disk', 'type', 'c'),
            ('disk', '$disk2', 'size', '8'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vda', 'type', 'a'),
            ('disk', 'vdb', 'size', '8'),
            ('disk', 'vdb', 'type', 'b'),
            ]
        arr = {}
        self.assertFalse(matcher.match_all(lines, specs, arr, {}))

if __name__ == "__main__":
    unittest.main()
