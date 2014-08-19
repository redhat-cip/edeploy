#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

import sys
import subprocess
import matcher
import re


def get_value(hw_, level1, level2, level3):
    for entry in hw_:
        if (level1 == entry[0] and level2 == entry[1] and level3 == entry[2]):
            return entry[3]
    return None


def fatal_error(error):
    '''Report a shell script with the error message and log
       the message on stderr.
    '''
    HP.logger.error('%s\n' % error)
    sys.exit(1)


def run_sysbench(hw_, max_time, cpu_count, processor_num=-1):
    'Running sysbench cpu stress of a give amount of logical cpu'
    taskset = ''
    if (processor_num < 0):
        sys.stderr.write('Benchmarking all CPUs for '
                         '%d seconds (%d threads)\n' % (max_time, cpu_count))
    else:
        sys.stderr.write('Benchmarking CPU %d for %d seconds (%d threads)\n' %
                         (processor_num, max_time, cpu_count))
        taskset = 'taskset %s' % hex(1 << processor_num)

    cmds = '%s sysbench --max-time=%d --max-requests=1000000' \
            ' --num-threads=%d --test=cpu --cpu-max-prime=15000 run' \
            % (taskset, max_time, cpu_count)
    sysbench_cmd = subprocess.Popen(cmds, shell=True, stdout=subprocess.PIPE)

    for line in sysbench_cmd.stdout:
        if "total number of events" in line.decode():
            title, perf = line.decode().rstrip('\n').replace(' ', '').split(':')
            if processor_num == -1:
                hw_.append(('cpu', 'logical', 'loops_per_sec',
                            str(int(perf) / max_time)))
            else:
                hw_.append(('cpu', 'logical_%d' % processor_num,
                            'loops_per_sec', str(int(perf) / max_time)))


def generate_filename_and_macs(items):
    '''Generate a file name for a hardware using DMI information
    (product name and version) then if the DMI serial number is
    available we use it unless we lookup the first mac address.
    As a result, we do have a filename like :

    <dmi_product_name>-<dmi_product_version>-{dmi_serial_num|mac_address}'''

    # Duplicate items as it will be modified by match_* functions
    hw_items = list(items)
    sysvars = {}
    sysvars['sysname'] = ''

    matcher.match_spec(('system', 'product', 'name', '$sysprodname'),
                       hw_items, sysvars)
    if 'sysprodname' in sysvars:
        sysvars['sysname'] = re.sub(r'\W+', '', sysvars['sysprodname']) + '-'

    matcher.match_spec(('system', 'product', 'vendor', '$sysprodvendor'),
                       hw_items, sysvars)
    if 'sysprodvendor' in sysvars:
        sysvars['sysname'] += re.sub(r'\W+', '', sysvars['sysprodvendor']) + \
            '-'

    matcher.match_spec(('system', 'product', 'serial', '$sysserial'),
                       hw_items, sysvars)
    # Let's use any existing DMI serial number or take the first mac address
    if 'sysserial' in sysvars:
        sysvars['sysname'] += re.sub(r'\W+', '', sysvars['sysserial']) + '-'

    # we always need to have the mac addresses for pxemngr
    if matcher.match_multiple(hw_items,
                              ('network', '$eth', 'serial', '$serial'),
                              sysvars):
        sysvars['sysname'] += sysvars['serial'][0].replace(':', '-')
    else:
        HP.logger.error('unable to detect network macs')

    return sysvars
