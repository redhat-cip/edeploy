import unittest

import diskinfo

class TestDiskinfo(unittest.TestCase):
    
    def test_sizeingb(self):
        return self.assertEqual(diskinfo.sizeingb(977105060), 500L)
    
    def test_parse_hdparm_output(self):
        return self.assertEqual(
            diskinfo.parse_hdparm_output(
                '\n/dev/sda:\n Timing buffered disk reads: 1436 MB in  3.00 seconds = 478.22 MB/sec'),
            478.22)

    def test_parse_hdparm_output2(self):
        return self.assertEqual(
            diskinfo.parse_hdparm_output(
                '\n/dev/sdc:\n Timing buffered disk reads:  30 MB in  3.01 seconds =   9.97 MB/sec\n'),
            9.97)

if __name__ == "__main__":
    unittest.main()
