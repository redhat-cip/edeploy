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

'''Wrapper functions around the megacli command.'''

import re
from subprocess import Popen, PIPE

SEP_REGEXP = re.compile(r'\s*:\s*')


def parse_output(output):
    'Parse the output of the megacli command into an associative array.'
    res = {}
    for line in output.split('\n'):
        lis = re.split(SEP_REGEXP, line.strip())
        if len(lis) == 2:
            if len(lis[1]) > 1 and lis[1][-1] == '.':
                lis[1] = lis[1][:-1]
            try:
                res[lis[0].title().replace(' ', '')] = int(lis[1])
            except ValueError:
                res[lis[0].title().replace(' ', '')] = lis[1]
    return res


def run_megacli(*args):
    'Run the megacli command in a subprocess and return the output.'
    cmd = 'megacli -' + ' '.join(args)
    return Popen(cmd, shell=True, stdout=PIPE).stdout.read(-1)


def run_and_parse(*args):
    '''Run the megacli command in a subprocess and return the output
as an associative array.'''
    res = run_megacli(*args)
    return parse_output(res)


def adp_count():
    'Get the numberof adaptaters.'
    arr = run_and_parse('adpCount')
    if 'ControllerCount' in arr:
        return int(arr['ControllerCount'])
    else:
        return 0


def adp_all_info(ctrl):
    'Get adaptater info.'
    arr = run_and_parse('adpallinfo -a%d' % ctrl)
    for key in ('RaidLevelSupported', 'SupportedDrives'):
        if key in arr:
            arr[key] = arr[key].split(', ')
    return arr


def pd_get_num(ctrl):
    'Get the number of physical drives on a controller.'
    try:
        key = 'NumberOfPhysicalDrivesOnAdapter%d' % ctrl
        return run_and_parse('PDGetNum -a%d' % ctrl)[key]
    except KeyError:
        return 0


def enc_info(ctrl):
    'Get enclosing info on a controller.'
    return run_and_parse('EncInfo -a%d' % ctrl)


def pdinfo(ctrl, encl, disk):
    'Get info about a physical drive on an enclosure and a controller.'
    return run_and_parse('pdinfo -PhysDrv[%d:%d] -a%d' % (encl, disk, ctrl))


def ld_get_num(ctrl):
    'Get the number of logical drives on a controller.'
    try:
        key = 'NumberOfVirtualDrivesConfiguredOnAdapter%d' % ctrl
        return run_and_parse('LDGetNum -a%d' % ctrl)[key]
    except KeyError:
        return 0


def ld_get_info(ctrl, ldrv):
    'Get info about a logical drive on a controller.'
    return run_and_parse('megacli -LDInfo -L%d -a%d' % (ldrv, ctrl))


if __name__ == "__main__":
    import pprint

    for ctrl_num in range(adp_count()):
        print 'Controler', ctrl_num
        pprint.pprint(adp_all_info(ctrl_num))

        enc = enc_info(ctrl_num)

        print

        print 'Enclosing:'
        pprint.pprint(enc)

        for disk_num in range(pd_get_num(ctrl_num)):
            print
            print 'Physical disk', disk_num
            pprint.pprint(pdinfo(ctrl_num, enc['DeviceId'], disk_num))

        for ld_num in range(ld_get_num(ctrl_num)):
            print
            print 'Logical disk', ld_num
            pprint.pprint(ld_get_info(ctrl_num, ld_num))

# megacli.py ends here
