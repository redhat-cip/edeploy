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

import megacli


class TestMegacliTest(unittest.TestCase):

    def setUp(self):
        def my_run(*args, **arr):
            return self.output
        self.run = megacli.run_megacli
        megacli.run_megacli = my_run

    def tearDown(self):
        megacli.run = self.run

    def test_parse_output_empty(self):
        self.assertEqual(megacli.parse_output(''), {})

    def test_parse_output_simple(self):
        self.assertEqual(megacli.parse_output(' a : b'), {'A': 'b'})

    def test_parse_output_adpcount(self):
        self.assertEqual(megacli.parse_output(''' 
Controller Count: 1.
 
Exit Code: 0x01'''), {'ControllerCount': 1,
                      'ExitCode': '0x01'})

    def test_adp_count(self):
        self.output = ''' 
Controller Count: 1.
 
Exit Code: 0x01'''
        self.assertEqual(megacli.adp_count(), 1)

    def test_adp_all_info(self):
        self.output = '''megacli -adpallinfo -aALL
 
Adapter #0
 
==============================================================================
                    Versions
                ================
Product Name    : PERC H710 Mini
Serial No       : 29F026R
FW Package Build: 21.1.0-0007

                Device Present
                ================
Virtual Drives    : 1 
  Degraded        : 0 
  Offline         : 0 
Physical Devices  : 7 
  Disks           : 6 
  Critical Disks  : 0 
  Failed Disks    : 0 '''
        self.assertEqual(megacli.adp_all_info(0),
                         {'CriticalDisks': 0,
                          'Degraded': 0,
                          'Disks': 6,
                          'FwPackageBuild': '21.1.0-0007',
                          'FailedDisks': 0,
                          'Offline': 0,
                          'PhysicalDevices': 7,
                          'ProductName': 'PERC H710 Mini',
                          'SerialNo': '29F026R',
                          'VirtualDrives': 1})

    def test_pd_get_num(self):
        self.output = '''
 Number of Physical Drives on Adapter 0: 6'''
        self.assertEqual(megacli.pd_get_num(0), 6)

    def test_split_parts(self):
        self.assertEqual(len(megacli.split_parts(' +Enclosure [0-9]+:',
                                                 ENC_OUTPUT)),
                         2)

    def test_enc_info(self):
        self.output = '''
    Number of enclosures on adapter 0 -- 1

    Enclosure 0:
    Device ID                     : 32
    Number of Slots               : 8'''
        self.assertEqual(megacli.enc_info(0),
                         [{'Enclosure': 0,
                          'DeviceId': 32,
                          'NumberOfSlots': 8}])

    def test_enc_info2(self):
        self.output = ENC_OUTPUT
        info = megacli.enc_info(0)
        self.assertEqual(len(info), 2)
        self.assertEqual(info[0]['Enclosure'], 0)
        self.assertEqual(info[1]['Enclosure'], 1)

    def test_pdinfo(self):
        self.output = '''
Enclosure Device ID: 32
Slot Number: 5
Enclosure position: 1
Device Id: 5
WWN: 5000C50054C07E80
Sequence Number: 1
Media Error Count: 0
Other Error Count: 0
Predictive Failure Count: 0
Last Predictive Failure Event Seq Number: 0
PD Type: SAS'''
        self.assertEqual(megacli.pdinfo(0, 32, 5),
                         {'DeviceId': 5,
                          'EnclosureDeviceId': 32,
                          'EnclosurePosition': 1,
                          'LastPredictiveFailureEventSeqNumber': 0,
                          'MediaErrorCount': 0,
                          'OtherErrorCount': 0,
                          'PdType': 'SAS',
                          'PredictiveFailureCount': 0,
                          'SequenceNumber': 1,
                          'SlotNumber': 5,
                          'Wwn': '5000C50054C07E80'}
                         )

    def test_ld_get_num(self):
        self.output = '''
 Number of Virtual Drives Configured on Adapter 0: 1'''
        self.assertEqual(megacli.ld_get_num(0), 1)

    def test_ld_get_info(self):
        self.output = '''
Adapter 0 -- Virtual Drive Information:
Virtual Drive: 0 (Target Id: 0)
Name                :
RAID Level          : Primary-1, Secondary-0, RAID Level Qualifier-0
Size                : 465.25 GB
Sector Size         : 512
Mirror Data         : 465.25 GB
State               : Optimal
Strip Size          : 64 KB
Number Of Drives    : 2
Span Depth          : 1
Default Cache Policy: WriteBack, ReadAdaptive, Direct, No Write Cache if Bad BBU
Current Cache Policy: WriteBack, ReadAdaptive, Direct, No Write Cache if Bad BBU
Default Access Policy: Read/Write
Current Access Policy: Read/Write
Disk Cache Policy   : Disk's Default
Encryption Type     : None
Default Power Savings Policy: Controller Defined
Current Power Savings Policy: None
Can spin up in 1 minute: Yes
LD has drives that support T10 power conditions: No
LD's IO profile supports MAX power savings with cached writes: No
Bad Blocks Exist: No
Is VD Cached: Yes
Cache Cade Type : Read Only'''
        self.assertEqual(megacli.ld_get_info(0, 0),
                         {'Adapter0--VirtualDriveInformation': '',
                          'BadBlocksExist': 'No',
                          'CacheCadeType': 'Read Only',
                          'CanSpinUpIn1Minute': 'Yes',
                          'CurrentAccessPolicy': 'Read/Write',
                          'CurrentCachePolicy': 'WriteBack, ReadAdaptive, Direct, No Write Cache if Bad BBU',
                          'CurrentPowerSavingsPolicy': 'None',
                          'DefaultAccessPolicy': 'Read/Write',
                          'DefaultCachePolicy': 'WriteBack, ReadAdaptive, Direct, No Write Cache if Bad BBU',
                          'DefaultPowerSavingsPolicy': 'Controller Defined',
                          'DiskCachePolicy': "Disk's Default",
                          'EncryptionType': 'None',
                          'IsVdCached': 'Yes',
                          "Ld'SIoProfileSupportsMaxPowerSavingsWithCachedWrites": 'No',
                          'LdHasDrivesThatSupportT10PowerConditions': 'No',
                          'MirrorData': '465.25 GB',
                          'Name': '',
                          'NumberOfDrives': 2,
                          'RaidLevel': 'Primary-1, Secondary-0, RAID Level Qualifier-0',
                          'SectorSize': 512,
                          'Size': '465.25 GB',
                          'SpanDepth': 1,
                          'State': 'Optimal',
                          'StripSize': '64 KB'})

ENC_OUTPUT = '''
                                     
    Number of enclosures on adapter 0 -- 2

    Enclosure 0:
    Device ID                     : 6
    Number of Slots               : 12
    Number of Power Supplies      : 2
    Number of Fans                : 3
    Number of Temperature Sensors : 1
    Number of Alarms              : 1
    Number of SIM Modules         : 0
    Number of Physical Drives     : 2
    Status                        : Normal
    Position                      : 1
    Connector Name                : Port 0 - 3
    Enclosure type                : SES
    FRU Part Number               : N/A
    Enclosure Serial Number       : N/A 
    ESM Serial Number             : N/A 
    Enclosure Zoning Mode         : N/A 
    Partner Device Id             : 65535

    Inquiry data                  :
        Vendor Identification     : LSI CORP
        Product Identification    : SAS2X28         
        Product Revision Level    : 0717
        Vendor Specific           : x36-55.7.23.0       

Number of Voltage Sensors         :2

Voltage Sensor                    :0
Voltage Sensor Status             :OK
Voltage Value                     :5070 milli volts

Voltage Sensor                    :1
Voltage Sensor Status             :OK
Voltage Value                     :11910 milli volts

Number of Power Supplies     : 2 

Power Supply                 : 0 
Power Supply Status          : Not Installed

Power Supply                 : 1 
Power Supply Status          : Not Installed

Number of Fans               : 3 

Fan                          : 0 
Fan Status                   : OK

Fan                          : 1 
Fan Speed              :Medium Speed
Fan Status                   : OK

Fan                          : 2 
Fan Speed              :Medium Speed
Fan Status                   : OK

Number of Temperature Sensors : 1 

Temp Sensor                  : 0 
Temperature                  : 25 
Temperature Sensor Status    : OK

Number of Chassis             : 1 

Chassis                      : 0 
Chassis Status               : OK

    Enclosure 1:
    Device ID                     : 252
    Number of Slots               : 8
    Number of Power Supplies      : 0
    Number of Fans                : 0
    Number of Temperature Sensors : 0
    Number of Alarms              : 0
    Number of SIM Modules         : 1
    Number of Physical Drives     : 0
    Status                        : Normal
    Position                      : 1
    Connector Name                : Unavailable
    Enclosure type                : SGPIO
    FRU Part Number               : N/A
    Enclosure Serial Number       : N/A 
    ESM Serial Number             : N/A 
    Enclosure Zoning Mode         : N/A 
    Partner Device Id             : Unavailable

    Inquiry data                  :
        Vendor Identification     : LSI     
        Product Identification    : SGPIO           
        Product Revision Level    : N/A 
        Vendor Specific           :                     


Exit Code: 0x00
'''

if __name__ == "__main__":
    unittest.main()

# test_megacli.py ends here
