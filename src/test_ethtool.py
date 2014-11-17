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

    def test_parse_ethtool_a(self):
        return self.assertEqual(
            detect_utils.parse_ethtool([], "enp0s25", ETHTOOL_A.split('\n')),
            ETHTOOL_A_RESULTS)

    def test_parse_ethtool_k(self):
        return self.assertEqual(
            detect_utils.parse_ethtool([], "enp0s25", ETHTOOL_K.split('\n')),
            ETHTOOL_K_RESULTS)


##############################################################################
# Output from real commands and expected results below
##############################################################################

ETHTOOL_A = '''Pause parameters for enp0s25:
Autonegotiate:	on
RX:		on
TX:		on
'''

ETHTOOL_K = '''Features for enp0s25:
rx-checksumming: on
tx-checksumming: on
	tx-checksum-ipv4: off [fixed]
	tx-checksum-ip-generic: on
	tx-checksum-ipv6: off [fixed]
	tx-checksum-fcoe-crc: off [fixed]
	tx-checksum-sctp: off [fixed]
scatter-gather: on
	tx-scatter-gather: on
	tx-scatter-gather-fraglist: off [fixed]
tcp-segmentation-offload: on
	tx-tcp-segmentation: on
	tx-tcp-ecn-segmentation: off [fixed]
	tx-tcp6-segmentation: on
udp-fragmentation-offload: off [fixed]
generic-segmentation-offload: on
generic-receive-offload: on
large-receive-offload: off [fixed]
rx-vlan-offload: on
tx-vlan-offload: on
ntuple-filters: off [fixed]
receive-hashing: on
highdma: on [fixed]
rx-vlan-filter: off [fixed]
vlan-challenged: off [fixed]
tx-lockless: off [fixed]
netns-local: off [fixed]
tx-gso-robust: off [fixed]
tx-fcoe-segmentation: off [fixed]
tx-gre-segmentation: off [fixed]
tx-ipip-segmentation: off [fixed]
tx-sit-segmentation: off [fixed]
tx-udp_tnl-segmentation: off [fixed]
tx-mpls-segmentation: off [fixed]
fcoe-mtu: off [fixed]
tx-nocache-copy: off
loopback: off [fixed]
rx-fcs: off
rx-all: off
tx-vlan-stag-hw-insert: off [fixed]
rx-vlan-stag-hw-parse: off [fixed]
rx-vlan-stag-filter: off [fixed]
l2-fwd-offload: off [fixed]
'''

ETHTOOL_A_RESULTS = [('network', 'enp0s25', 'Autonegotiate', 'on'), ('network', 'enp0s25', 'RX', 'on'), ('network', 'enp0s25', 'TX', 'on')]

ETHTOOL_K_RESULTS = [('network', 'enp0s25', 'rx-checksumming', 'on'), ('network', 'enp0s25', 'tx-checksumming', 'on'), ('network', 'enp0s25', 'tx-checksumming/tx-checksum-ipv4', 'off [fixed]'), ('network', 'enp0s25', 'tx-checksumming/tx-checksum-ip-generic', 'on'), ('network', 'enp0s25', 'tx-checksumming/tx-checksum-ipv6', 'off [fixed]'), ('network', 'enp0s25', 'tx-checksumming/tx-checksum-fcoe-crc', 'off [fixed]'), ('network', 'enp0s25', 'tx-checksumming/tx-checksum-sctp', 'off [fixed]'), ('network', 'enp0s25', 'scatter-gather', 'on'), ('network', 'enp0s25', 'scatter-gather/tx-scatter-gather', 'on'), ('network', 'enp0s25', 'scatter-gather/tx-scatter-gather-fraglist', 'off [fixed]'), ('network', 'enp0s25', 'tcp-segmentation-offload', 'on'), ('network', 'enp0s25', 'tcp-segmentation-offload/tx-tcp-segmentation', 'on'), ('network', 'enp0s25', 'tcp-segmentation-offload/tx-tcp-ecn-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'tcp-segmentation-offload/tx-tcp6-segmentation', 'on'), ('network', 'enp0s25', 'udp-fragmentation-offload', 'off [fixed]'), ('network', 'enp0s25', 'generic-segmentation-offload', 'on'), ('network', 'enp0s25', 'generic-receive-offload', 'on'), ('network', 'enp0s25', 'large-receive-offload', 'off [fixed]'), ('network', 'enp0s25', 'rx-vlan-offload', 'on'), ('network', 'enp0s25', 'tx-vlan-offload', 'on'), ('network', 'enp0s25', 'ntuple-filters', 'off [fixed]'), ('network', 'enp0s25', 'receive-hashing', 'on'), ('network', 'enp0s25', 'highdma', 'on [fixed]'), ('network', 'enp0s25', 'rx-vlan-filter', 'off [fixed]'), ('network', 'enp0s25', 'vlan-challenged', 'off [fixed]'), ('network', 'enp0s25', 'tx-lockless', 'off [fixed]'), ('network', 'enp0s25', 'netns-local', 'off [fixed]'), ('network', 'enp0s25', 'tx-gso-robust', 'off [fixed]'), ('network', 'enp0s25', 'tx-fcoe-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'tx-gre-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'tx-ipip-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'tx-sit-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'tx-udp_tnl-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'tx-mpls-segmentation', 'off [fixed]'), ('network', 'enp0s25', 'fcoe-mtu', 'off [fixed]'), ('network', 'enp0s25', 'tx-nocache-copy', 'off'), ('network', 'enp0s25', 'loopback', 'off [fixed]'), ('network', 'enp0s25', 'rx-fcs', 'off'), ('network', 'enp0s25', 'rx-all', 'off'), ('network', 'enp0s25', 'tx-vlan-stag-hw-insert', 'off [fixed]'), ('network', 'enp0s25', 'rx-vlan-stag-hw-parse', 'off [fixed]'), ('network', 'enp0s25', 'rx-vlan-stag-filter', 'off [fixed]'), ('network', 'enp0s25', 'l2-fwd-offload', 'off [fixed]')]


if __name__ == "__main__":
    unittest.main()
