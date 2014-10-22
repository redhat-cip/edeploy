#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
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

import detect_utils


class TestParsing(unittest.TestCase):

    def test_parse_lldp_tin(self):
        return self.assertEqual(
            detect_utils.parse_lldtool([], "eth0", LLDPTOOL_TIN.split('\n')),
            LLDPTOOL_TIN_RESULTS)


##############################################################################
# Output from real commands and expected results below
##############################################################################

LLDPTOOL_TIN = '''Chassis ID TLV
	MAC: f8:b1:56:15:e6:c6
Port ID TLV
	Ifname: gi1/1
Time to Live TLV
	120
MAC/PHY Configuration Status TLV
	Auto-negotiation supported and enabled
	PMD auto-negotiation capabilities: 0x6c01
	MAU type: 1000 BaseTFD
Port Description TLV
	gigabitethernet1/1
System Name TLV
	Switch POD
System Description TLV
	R1-2401 VRTX 1Gb Switch Module
System Capabilities TLV
	System capabilities:  Bridge
	Enabled capabilities: Bridge
End of LLDPDU TLV
'''

LLDPTOOL_TIN_RESULTS = [('lldp', 'eth0', 'Chassis ID/MAC', 'f8:b1:56:15:e6:c6'), ('lldp', 'eth0', 'Port ID/Ifname', 'gi1_1'), ('lldp', 'eth0', 'Time to Live', '120'), ('lldp', 'eth0', 'MAC_PHY Configuration Status', 'Auto-negotiation supported and enabled'), ('lldp', 'eth0', 'MAC_PHY Configuration Status/PMD auto-negotiation capabilities', '0x6c01'), ('lldp', 'eth0', 'MAC_PHY Configuration Status/PMD auto-negotiation capabilities/MAU type', '1000 BaseTFD'), ('lldp', 'eth0', 'Port Description', 'gigabitethernet1_1'), ('lldp', 'eth0', 'System Name', 'Switch POD'), ('lldp', 'eth0', 'System Description', 'R1-2401 VRTX 1Gb Switch Module'), ('lldp', 'eth0', 'System Capabilities/System capabilities', ' Bridge'), ('lldp', 'eth0', 'System Capabilities/System capabilities/Enabled capabilities', 'Bridge')]

if __name__ == "__main__":
    unittest.main()
