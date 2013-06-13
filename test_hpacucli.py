import unittest
import mock

import hpacucli

class TestParsing(unittest.TestCase):

    def test_parse_ctrl_all_show(self):
        # => ctrl all show
        return self.assertEqual(
            hpacucli.parse_ctrl_all_show(CTRL_ALL_SHOW_OUTPUT),
            CTRL_ALL_SHOW_RESULT)

    def test_parse_ctrl_pd_all_show(self):
        # => ctrl slot=2 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_all_show(CTRL_PD_ALL_SHOW_OUTPUT),
            CTRL_PD_ALL_SHOW_RESULT)

    def test_parse_ctrl_pd_all_show_unassigned(self):
        # => ctrl slot=2 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_all_show(CTRL_PD_ALL_SHOW_UNASSIGNED_OUTPUT),
            [('unassigned',
                 [('1I:1:1', 'SATA', '1 TB', 'OK'),
                  ('1I:1:2', 'SATA', '1 TB', 'OK'),
                  ('1I:1:3', 'SATA', '1 TB', 'OK'),
                  ('1I:1:4', 'SATA', '1 TB', 'OK'),
                  ('2I:1:5', 'SATA', '1 TB', 'OK'),
                  ('2I:1:6', 'SATA', '1 TB', 'OK'),
                  ('2I:1:7', 'Solid State SATA', '100 GB', 'OK'),
                  ('2I:1:8', 'Solid State SATA', '100 GB', 'OK')])])

    def test_parse_ctrl_ld_all_show(self):
        # => ctrl slot=2 ld all show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_all_show(CTRL_LD_ALL_SHOW_OUTPUT),
            CTRL_LD_ALL_SHOW_RESULT)

    def test_error(self):
        # => ctrl slot=2 delete force
        return self.assertRaisesRegexp(hpacucli.Error,
                                       '^\'Syntax error at "force"\'$',
                                       hpacucli.parse_error,
                                       '''
Error: Syntax error at "force"

''')

    def test_parse_ctrl_ld_show(self):
        # => ctrl slot=2 ld 1 show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_show(CTRL_LD_SHOW_OUTPUT),
            CTRL_LD_SHOW_RESULT
            )

    def test_parse_ctrl_ld_show2(self):
        # => ctrl slot=2 ld 2 show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_show(CTRL_LD_SHOW_OUTPUT2),
            CTRL_LD_SHOW_RESULT2
            )

class TestController(unittest.TestCase):
    def setUp(self):
        self.cli = hpacucli.Cli()
        self.cli.process = mock.MagicMock()

    def test_ctrl_all_show(self):
        self.cli.process.before = 'ctrl all show' + CTRL_ALL_SHOW_OUTPUT
        return self.assertEqual(self.cli.ctrl_all_show(),
                                CTRL_ALL_SHOW_RESULT
                                )

    def test_ctrl_pd_all_show(self):
        self.cli.process.before = 'ctrl slot=2 pd all show' + CTRL_PD_ALL_SHOW_OUTPUT
        return self.assertEqual(self.cli.ctrl_pd_all_show('slot=2'),
                                CTRL_PD_ALL_SHOW_RESULT
                                )

    def test_ctrl_ld_all_show(self):
        self.cli.process.before = 'ctrl slot=2 ld all show' + CTRL_LD_ALL_SHOW_OUTPUT
        return self.assertEqual(self.cli.ctrl_ld_all_show('slot=2'),
                                CTRL_LD_ALL_SHOW_RESULT
                                )

    def test_ctrl_ld_show(self):
        self.cli.process.before = 'ctrl slot=2 ld 2 show' + CTRL_LD_SHOW_OUTPUT
        return self.assertEqual(
            self.cli.ctrl_ld_show('slot=2', '2'),
            CTRL_LD_SHOW_RESULT
            )

    @unittest.skip("WIP")
    def test_ctrl_create_ld(self):
        self.cli.process.before = 'ctrl slot=2 ld 2 show' + CTRL_LD_ALL_SHOW_OUTPUT + CTRL_LD_SHOW_OUTPUT
        return self.assertEqual(
            self.cli.ctrl_create_ld('slot=2', ('2I:1:7' ,'2I:1:8'), '1'),
            '/dev/sda'
            )


##############################################################################
# Output from real commands and expected results below
##############################################################################

CTRL_ALL_SHOW_OUTPUT = '''
Smart Array P420 in Slot 2                (sn: PDKRH0ARH4F1R6)

'''

CTRL_ALL_SHOW_RESULT = [(2, 'Smart Array P420', 'PDKRH0ARH4F1R6')]

CTRL_PD_ALL_SHOW_OUTPUT = '''
Smart Array P420 in Slot 2

   array A

      physicaldrive 2I:1:7 (port 2I:box 1:bay 7, Solid State SATA, 100 GB, OK)
      physicaldrive 2I:1:8 (port 2I:box 1:bay 8, Solid State SATA, 100 GB, OK)

   array B

      physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SATA, 1 TB, OK)

   array C

      physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 1 TB, OK)

   array D

      physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SATA, 1 TB, OK)

   array E

      physicaldrive 1I:1:4 (port 1I:box 1:bay 4, SATA, 1 TB, OK)

   array F

      physicaldrive 2I:1:5 (port 2I:box 1:bay 5, SATA, 1 TB, OK)

   array G

      physicaldrive 2I:1:6 (port 2I:box 1:bay 6, SATA, 1 TB, OK)

'''

CTRL_PD_ALL_SHOW_RESULT = [
    ('array A', [('2I:1:7', 'Solid State SATA', '100 GB', 'OK'),
                ('2I:1:8', 'Solid State SATA', '100 GB', 'OK')]),
    ('array B', [('1I:1:1', 'SATA', '1 TB', 'OK')]),
    ('array C', [('1I:1:2', 'SATA', '1 TB', 'OK')]),
    ('array D', [('1I:1:3', 'SATA', '1 TB', 'OK')]),
    ('array E', [('1I:1:4', 'SATA', '1 TB', 'OK')]),
    ('array F', [('2I:1:5', 'SATA', '1 TB', 'OK')]),
    ('array G', [('2I:1:6', 'SATA', '1 TB', 'OK')]),
    ]

CTRL_PD_ALL_SHOW_UNASSIGNED_OUTPUT = '''

Smart Array P420 in Slot 2

   unassigned

      physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SATA, 1 TB, OK)
      physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 1 TB, OK)
      physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SATA, 1 TB, OK)
      physicaldrive 1I:1:4 (port 1I:box 1:bay 4, SATA, 1 TB, OK)
      physicaldrive 2I:1:5 (port 2I:box 1:bay 5, SATA, 1 TB, OK)
      physicaldrive 2I:1:6 (port 2I:box 1:bay 6, SATA, 1 TB, OK)
      physicaldrive 2I:1:7 (port 2I:box 1:bay 7, Solid State SATA, 100 GB, OK)
      physicaldrive 2I:1:8 (port 2I:box 1:bay 8, Solid State SATA, 100 GB, OK)

'''

CTRL_LD_ALL_SHOW_OUTPUT = '''
Smart Array P420 in Slot 2

   array A

      logicaldrive 1 (93.1 GB, RAID 1, OK)

   array B

      logicaldrive 2 (931.5 GB, RAID 0, OK)

   array C

      logicaldrive 3 (931.5 GB, RAID 0, OK)

   array D

      logicaldrive 4 (931.5 GB, RAID 0, OK)

   array E

      logicaldrive 5 (931.5 GB, RAID 0, OK)

   array F

      logicaldrive 6 (931.5 GB, RAID 0, OK)

   array G

      logicaldrive 7 (931.5 GB, RAID 0, OK)

'''

CTRL_LD_ALL_SHOW_RESULT = [
    ('array A', [('1', '93.1 GB', 'RAID 1', 'OK')]),
    ('array B', [('2', '931.5 GB', 'RAID 0', 'OK')]),
    ('array C', [('3', '931.5 GB', 'RAID 0', 'OK')]),
    ('array D', [('4', '931.5 GB', 'RAID 0', 'OK')]),
    ('array E', [('5', '931.5 GB', 'RAID 0', 'OK')]),
    ('array F', [('6', '931.5 GB', 'RAID 0', 'OK')]),
    ('array G', [('7', '931.5 GB', 'RAID 0', 'OK')]),
    ]

#=> ctrl slot=2 pd 2I:1:8 show
CTRL_PD_SHOW_OUTPUT = '''

Smart Array P420 in Slot 2

   array A

      physicaldrive 2I:1:8
         Port: 2I
         Box: 1
         Bay: 8
         Status: OK
         Drive Type: Data Drive
         Interface Type: Solid State SATA
         Size: 100 GB
         Firmware Revision: 5DV1HPG0
         Serial Number: BTTV305001NZ100FGN  
         Model: ATA     MK0100GCTYU     
         SATA NCQ Capable: True
         SATA NCQ Enabled: True
         Current Temperature (C): 11
         Maximum Temperature (C): 22
         Usage remaining: 100.00%
         Power On Hours: 43
         SSD Smart Trip Wearout: False
         PHY Count: 1
         PHY Transfer Rate: 6.0Gbps
         Drive Authentication Status: OK
         Carrier Application Version: 11
         Carrier Bootloader Version: 6

'''

# => ctrl slot=2 ld 1 show
CTRL_LD_SHOW_OUTPUT = '''

Smart Array P420 in Slot 2

   array A

      Logical Drive: 1
         Size: 93.1 GB
         Fault Tolerance: 1
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 23934
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001CE81A48ACAE0E3331C2F6
         Disk Name: /dev/sda
         Mount Points: None
         Logical Drive Label: A299BBB1PDKRH0ARH4F1R6D4B9
         Mirror Group 0:
            physicaldrive 2I:1:7 (port 2I:box 1:bay 7, Solid State SATA, 100 GB, OK)
         Mirror Group 1:
            physicaldrive 2I:1:8 (port 2I:box 1:bay 8, Solid State SATA, 100 GB, OK)
         Drive Type: Data
         Caching Association: None

'''

CTRL_LD_SHOW_RESULT = {
    'Caching': 'Enabled',
    'Caching Association': 'None',
    'Cylinders': '23934',
    'Disk Name': '/dev/sda',
    'Drive Type': 'Data',
    'Fault Tolerance': '1',
    'Full Stripe Size': '256 KB',
    'Heads': '255',
    'Logical Drive': '1',
    'Logical Drive Label': 'A299BBB1PDKRH0ARH4F1R6D4B9',
    'Mirror Group 0': '2I:1:7',
    'Mirror Group 1': '2I:1:8',
    'Mount Points': 'None',
    'Sectors Per Track': '32',
    'Size': '93.1 GB',
    'Status': 'OK',
    'Strip Size': '256 KB',
    'Unique Identifier': '600508B1001CE81A48ACAE0E3331C2F6'}

#=> ctrl slot=2 ld 2 show

CTRL_LD_SHOW_OUTPUT2 = '''

Smart Array P420 in Slot 2

   array B

      Logical Drive: 2
         Size: 931.5 GB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001C87603833075ECAC289A6
         Disk Name: /dev/sdb
         Mount Points: None
         Logical Drive Label: A29A9DA2PDKRH0ARH4F1R63C33
         Drive Type: Data
         Caching Association: None

'''

CTRL_LD_SHOW_RESULT2 = {
    'Status': 'OK',
    'Mount Points': 'None',
    'Sectors Per Track': '32',
    'Caching Association': 'None',
    'Cylinders': '65535',
    'Full Stripe Size': '256 KB',
    'Drive Type': 'Data',
    'Logical Drive Label': 'A29A9DA2PDKRH0ARH4F1R63C33',
    'Strip Size': '256 KB',
    'Disk Name': '/dev/sdb',
    'Caching': 'Enabled',
    'Heads': '255',
    'Unique Identifier': '600508B1001C87603833075ECAC289A6',
    'Logical Drive': '2',
    'Fault Tolerance': '0',
    'Size': '931.5 GB'}

if __name__ == "__main__":
    unittest.main()
