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

    def test_parse_lldp_tin2(self):
        return self.assertEqual(
            detect_utils.parse_lldtool([], "eth0", LLDPTOOL_TIN2.split('\n')),
            LLDPTOOL_TIN2_RESULTS)



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

LLDPTOOL_TIN2='''Chassis ID TLV
	MAC: 58:f3:9c:81:ad:95
Port ID TLV
	Ifname: Ethernet1/14
Time to Live TLV
	120
Port Description TLV
	SRV-51D4-14
System Name TLV
	AC3K-51D4-05.local.odcnoord.nl
System Description TLV
	Cisco Nexus Operating System (NX-OS) Software 6.0(2)U2(5)
TAC support: http://www.cisco.com/tac
Copyright (c) 2002-2014, Cisco Systems, Inc. All rights reserved.
System Capabilities TLV
	System capabilities:  Bridge, Router
	Enabled capabilities: Bridge, Router
Management Address TLV
	IPv4: 10.100.5.24
	Ifindex: 83886080
CEE DCBX TLV
	Control TLV:
	  SeqNo: 1, AckNo: 1
	Priority Groups TLV:
	  Enabled, Not Willing, No Error
	  PGID Priorities:  0:[0,1,2,3,4,5,6,7]
	  PGID Percentages: 0:100% 1:0% 2:0% 3:0% 4:0% 5:0% 6:0% 7:0%
	  Number of TC's supported: 1
Cisco 4-wire Power-via-MDI TLV
	4-Pair PoE supported
	Spare pair Detection/Classification not required
	PD Spare pair Desired State: Disabled
	PSE Spare pair Operational State: Disabled
Unidentified Org Specific TLV
	OUI: 0x000142, Subtype: 2, Info: 23282328232823282328232823282328
Port VLAN ID TLV
	PVID: 100
End of LLDPDU TLV
'''

LLDPTOOL_TIN_RESULTS = [('lldp', 'eth0', 'Chassis ID/MAC', 'f8:b1:56:15:e6:c6'), ('lldp', 'eth0', 'Port ID/Ifname', 'gi1_1'), ('lldp', 'eth0', 'Time to Live', '120'), ('lldp', 'eth0', 'MAC_PHY Configuration Status', 'Auto-negotiation supported and enabled'), ('lldp', 'eth0', 'MAC_PHY Configuration Status/PMD auto-negotiation capabilities', '0x6c01'), ('lldp', 'eth0', 'MAC_PHY Configuration Status/PMD auto-negotiation capabilities/MAU type', '1000 BaseTFD'), ('lldp', 'eth0', 'Port Description', 'gigabitethernet1_1'), ('lldp', 'eth0', 'System Name', 'Switch POD'), ('lldp', 'eth0', 'System Description', 'R1-2401 VRTX 1Gb Switch Module'), ('lldp', 'eth0', 'System Capabilities/System capabilities', 'Bridge'), ('lldp', 'eth0', 'System Capabilities/System capabilities/Enabled capabilities', 'Bridge')]

LLDPTOOL_TIN2_RESULTS = [('lldp', 'eth0', 'Chassis ID/MAC', '58:f3:9c:81:ad:95'), ('lldp', 'eth0', 'Port ID/Ifname', 'Ethernet1_14'), ('lldp', 'eth0', 'Time to Live', '120'), ('lldp', 'eth0', 'Port Description', 'SRV-51D4-14'), ('lldp', 'eth0', 'System Name', 'AC3K-51D4-05.local.odcnoord.nl'), ('lldp', 'eth0', 'System Description', 'Cisco Nexus Operating System (NX-OS) Software 6.0(2)U2(5)'), ('lldp', 'eth0', 'System Capabilities/System capabilities', 'Bridge, Router'), ('lldp', 'eth0', 'System Capabilities/System capabilities/Enabled capabilities', 'Bridge, Router'), ('lldp', 'eth0', 'Management Address/IPv4', '10.100.5.24'), ('lldp', 'eth0', 'Management Address/IPv4/Ifindex', '83886080'), ('lldp', 'eth0', 'CEE DCBX/Control TLV/SeqNo', '1, AckNo: 1'), ('lldp', 'eth0', 'CEE DCBX/Control TLV/SeqNo/Priority Groups TLV', 'Enabled, Not Willing, No Error'), ('lldp', 'eth0', 'CEE DCBX/Control TLV/SeqNo/Priority Groups TLV/PGID Priorities', '0:[0,1,2,3,4,5,6,7]'), ('lldp', 'eth0', 'CEE DCBX/Control TLV/SeqNo/Priority Groups TLV/PGID Priorities/PGID Percentages', '0:100% 1:0% 2:0% 3:0% 4:0% 5:0% 6:0% 7:0%'), ('lldp', 'eth0', "CEE DCBX/Control TLV/SeqNo/Priority Groups TLV/PGID Priorities/PGID Percentages/Number of TC's supported", '1'), ('lldp', 'eth0', 'Cisco 4-wire Power-via-MDI', '4-Pair PoE supported'), ('lldp', 'eth0', 'Cisco 4-wire Power-via-MDI', 'Spare pair Detection_Classification not required'), ('lldp', 'eth0', 'Cisco 4-wire Power-via-MDI/PD Spare pair Desired State', 'Disabled'), ('lldp', 'eth0', 'Cisco 4-wire Power-via-MDI/PD Spare pair Desired State/PSE Spare pair Operational State', 'Disabled'), ('lldp', 'eth0', 'Unidentified Org Specific/OUI', '0x000142, Subtype: 2, Info: 23282328232823282328232823282328'), ('lldp', 'eth0', 'Port VLAN ID/PVID', '100')]

if __name__ == "__main__":
    unittest.main()
