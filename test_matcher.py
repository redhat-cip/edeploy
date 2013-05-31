import unittest

import matcher

class TestMatcher(unittest.TestCase):
    
    def test_equal(self):
        line = ('system', 'board', 'serial', 'CZJ31402CD')
        specs = [('system', 'board', 'serial', 'CZJ31402CD'),
                 ]
        arr = {}
        self.assert_(matcher.match_line(line, specs, arr))
        self.assertEqual(specs, [])

    def test_not_equal(self):
        line = ('system', 'board', 'serial', 'CZJ31402CD')
        specs = [('system', 'board', 'serial', 'CZJ31402CE'),
                 ]
        arr = {}
        self.assert_(not matcher.match_line(line, specs, arr))

    def test_var(self):
        line = ('disk', '1I:1:1', 'size', '1000GB')
        specs = [('disk', '$disk8', 'size', '1000GB'),
                 ]
        arr = {}
        self.assert_(matcher.match_line(line, specs, arr))
        self.assertEqual(arr, {'disk8': '1I:1:1'})
        self.assertEqual(specs, [])

    def test_vars(self):
        lines = [
            ('system', 'board', 'serial', 'CZJ31402CD'),
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
            ('net', 'eth0', 'mac', '2c:76:8a:5a:e4:10'),
            ('net', 'eth0', 'type', '1Gb'),
            ('net', 'eth1', 'mac', '2c:76:8a:5a:e4:11'),
            ('net', 'eth1', 'type', '1Gb'),
            ('net', 'eth2', 'mac', 'b4:b5:2f:63:d4:2c'),
            ('net', 'eth2', 'type', '1Gb'),
            ('net', 'eth2', 'ipv4', '10.142.18.195'),
            ('net', 'eth3', 'mac', 'b4:b5:2f:63:d4:2d'),
            ('net', 'eth3', 'type', '1Gb'),
            ('net', 'eth3', 'ipv4', '10.66.6.218'),
            ]
        specs = [('system', 'board', 'serial', 'CZJ31402CD'),
                 ('disk', '$disk1', 'size', '100GB'),
                 ('disk', '$disk2', 'size', '100GB'),
                 ('disk', '$disk3', 'size', '1000GB'),
                 ('disk', '$disk4', 'size', '1000GB'),
                 ('disk', '$disk5', 'size', '1000GB'),
                 ('disk', '$disk6', 'size', '1000GB'),
                 ('disk', '$disk7', 'size', '1000GB'),
                 ('disk', '$disk8', 'size', '1000GB')]
        arr = {}
        self.assert_(matcher.match_all(lines, specs, arr))
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
            ('disk', '$disk1', 'control', 'hpa'),
            ('disk', '$disk1', 'size', '100GB'),
            ('disk', '$disk2', 'size', '1000GB'),
            ]
        arr = {}
        self.assert_(matcher.match_all(lines, specs, arr))
        self.assertEqual(arr,
                         {'disk1': '1I:1:2',
                          'disk2': '1I:1:1',
                          })

