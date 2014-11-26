#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
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

'Set of functions to manage IPMI'

from commands import getstatusoutput as cmd
import re
import sys


def setup_user(channel, username, password):
    'Setup an IPMI user.'
    sys.stderr.write('Info: ipmi_setup_user: Setting user="%s", '
                     'password="%s" on channel %s\n' %
                     (username, password, channel))
    cmd('ipmitool user set name 1 %s' % username)
    cmd('ipmitool user set password 1 %s' % password)
    cmd('ipmitool user priv 1 4 %s' % channel)
    cmd('ipmitool user enable')
    state, _ = cmd('ipmitool user test 1 16 %s' % password)
    if state == 0:
        sys.stderr.write('Info: ipmi_setup_user: Setting user successful !\n')
    else:
        sys.stderr.write('Err: ipmi_setup_user: Setting user failed !\n')
        return False


def restart_bmc():
    'Restart a BMC card.'
    sys.stderr.write('Info: Restarting IPMI BMC\n')
    cmd('ipmitool bmc reset cold')


def setup_network(channel, ipv4, netmask, gateway, vlan_id=-1):
    'Define the network of an IPMI interface.'
    sys.stderr.write('Info: ipmi_setup_network: Setting network ip="%s", '
                     'netmask="%s", gateway="%s", vland_id="%d" on '
                     'channel %s\n' %
                     (ipv4,
                      netmask,
                      gateway,
                      vlan_id,
                      channel))
    # NOTE (leseb): assuming you're missing an argument
    # and this already happened
    # ipmitool always returns 0 and prompt the valid values...
    cmd('ipmitool lan set %s ipsrc static' % channel)
    cmd('ipmitool lan set %s ipaddr %s' % (channel, ipv4))
    cmd('ipmitool lan set %s netmask %s' % (channel, netmask))
    cmd('ipmitool lan set %s defgw ipaddr %s' % (channel, gateway))
    cmd('ipmitool lan set %s arp respond on' % channel)

    if vlan_id >= 0:
        cmd('ipmitool lan set %s vlan id %d' % (channel, vlan_id))
    else:
        cmd('ipmitool lan set %s vlan id off' % channel)

    # We need to restart the bmc to insure the setup is properly done
    restart_bmc()

LINE_REGEXP = re.compile(r'^([^:]+[^ ])\s*:\s*(.*[^ ])\s*$')


def parse_lan_info(output, lst):
    'Parse the output of ipmi lan info and turns add it to the hw list.'
    for line in output.split('\n'):
        res = LINE_REGEXP.search(line)
        if res:
            lst.append(('ipmi', 'lan',
                        '-'.join([s.lower() for s in res.group(1).split(' ')]),
                        res.group(2)))
    return lst
