import unittest

import matcher

class TestMatcher(unittest.TestCase):
    
    def test_equal(self):
        lines = [('system', 'board', 'serial', 'CZJ31402CD')]
        spec = ('system', 'board', 'serial', 'CZJ31402CD')
        arr = {}
        self.assert_(matcher.match_spec(spec, lines, arr))

    def test_not_equal(self):
        lines = [('system', 'board', 'serial', 'CZJ31402CD')]
        spec = ('system', 'board', 'serial', 'CZJ31402CE')
        arr = {}
        self.assert_(not matcher.match_spec(spec, lines, arr))

    def test_var(self):
        lines = [('disk', '1I:1:1', 'size', '1000GB')]
        spec = ('disk', '$disk8', 'size', '1000GB')
        arr = {}
        self.assert_(matcher.match_spec(spec, lines, arr))
        self.assertEqual(arr, {'disk8': '1I:1:1'})

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
            ('disk', '$disk1', 'size', '100GB'),
            ('disk', '$disk1', 'control', 'hpa'),
            ('disk', '$disk2', 'size', '1000GB'),
            ]
        arr = {}
        self.assert_(matcher.match_all(lines, specs, arr))
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
        self.assert_(matcher.match_all(lines, specs, arr))

    def test_2vars(self):
        specs = [
            ('disk', '$disk', 'size', '$size'),
            ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ]
        arr = {}
        self.assert_(matcher.match_all(lines, specs, arr))
        self.assertEqual(arr,
                         {'size': '8',
                          'disk': 'vda',
                          })

    def test_multiple(self):
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
        self.assert_(not matcher.match_all(lines, specs, arr))
        self.assert_(matcher.match_all(lines, specs2, arr), lines)

if __name__ == "__main__":
    unittest.main()
