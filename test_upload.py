import unittest

import upload

class TestUpload(unittest.TestCase):
    
    def test_is_included_same(self):
        a = {'a': 1}
        self.assert_(upload.is_included(a, a))

    def test_is_included_different(self):
        a = {'a': 1}
        b = {'a': 2}
        self.assert_(not upload.is_included(a, b))

    def test_is_included_different(self):
        a = {'a': 1, 'b': 2}
        b = {'a': 1, 'b': 2, 'c': 3}
        self.assert_(upload.is_included(a, b))

    def test_generate(self):
        model = {'a': '192.168.1.1',
                 'ip': '192.168.1.10-12'}
        self.assertEqual(upload.generate(model), 
                         [{'a': '192.168.1.1', 'ip': '192.168.1.10'},
                          {'a': '192.168.1.1', 'ip': '192.168.1.11'},
                          {'a': '192.168.1.1', 'ip': '192.168.1.12'}])

    def test_generate_ip(self):
        model = '192.168.1.10-12'
        self.assertEqual(list(upload._generate_ip(model)),
                         ['192.168.1.10',
                          '192.168.1.11',
                          '192.168.1.12'])

    def test_generate_range(self):
        self.assertEqual(list(upload._generate_range('10-12')),
                         ['10', '11', '12'])

    def test_generate_range_colon(self):
        self.assertEqual(list(upload._generate_range('1-3:10-12')),
                         ['1', '2', '3', '10', '11', '12'])

if __name__ == "__main__":
    unittest.main()
