#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

import ipmi


class TestIpmi(unittest.TestCase):

    def test_parse_lan_info(self):
        res = []
        ipmi.parse_lan_info(IPMI_LAN_INFO_OUTPUT, res)
        self.assertEquals(len(res), 19)

IPMI_LAN_INFO_OUTPUT = '''Set in Progress         : Set Complete
Auth Type Support       : MD2 MD5 OEM 
Auth Type Enable        : Callback : MD2 MD5 OEM 
                        : User     : MD2 MD5 OEM 
                        : Operator : MD2 MD5 OEM 
                        : Admin    : MD2 MD5 OEM 
                        : OEM      : 
IP Address Source       : Static Address
IP Address              : 10.151.68.13
Subnet Mask             : 255.255.255.0
MAC Address             : 00:30:48:f4:4d:83
SNMP Community String   : AMI
IP Header               : TTL=0x00 Flags=0x00 Precedence=0x00 TOS=0x00
BMC ARP Control         : ARP Responses Enabled, Gratuitous ARP Disabled
Gratituous ARP Intrvl   : 0.0 seconds
Default Gateway IP      : 10.151.68.3
Default Gateway MAC     : 00:00:00:00:00:00
Backup Gateway IP       : 0.0.0.0
Backup Gateway MAC      : 00:00:00:00:00:00
802.1q VLAN ID          : Disabled
802.1q VLAN Priority    : 0
RMCP+ Cipher Suites     : 1,2,3,6,7,8,11,12,0
Cipher Suite Priv Max   : aaaaXXaaaXXaaXX
                        :     X=Cipher Suite Unused
                        :     c=CALLBACK
                        :     u=USER
                        :     o=OPERATOR
                        :     a=ADMIN
                        :     O=OEM
'''
if __name__ == "__main__":
    unittest.main()

# test_ipmi.py ends here
