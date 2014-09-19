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

from health_messages import Health_Message as HM
import health_protocol as HP
import ipaddr
import psutil
import sys
import subprocess
import os
import matcher
import re
import time


def is_in_network(left, right):
    'Helper for match_spec.'
    return ipaddr.IPv4Address(left) in ipaddr.IPv4Network(right)


def get_multiple_values(hw, level1, level2, level3):
    result = []
    temp_level2 = level2
    for entry in hw:
        if level2 == '*':
            temp_level2 = entry[1]
        if (level1 == entry[0] and temp_level2 == entry[1] and level3 == entry[2]):
            result.append(entry[3])
    return result


def get_value(hw_, level1, level2, level3):
    for entry in hw_:
        if (level1 == entry[0] and level2 == entry[1] and level3 == entry[2]):
            return entry[3]
    return None


def fatal_error(error):
    '''Report a shell script with the error message and log
       the message on stderr.'''
    HP.logger.error('%s\n' % error)
    sys.exit(1)


def run_sysbench_cpu(hw_, max_time, cpu_count, processor_num=-1):
    'Running sysbench cpu stress of a give amount of logical cpu'
    taskset = ''
    if (processor_num < 0):
        sys.stderr.write('Benchmarking all CPUs for '
                         '%d seconds (%d threads)\n' % (max_time, cpu_count))
    else:
        sys.stderr.write('Benchmarking CPU %d for %d seconds (%d threads)\n' %
                         (processor_num, max_time, cpu_count))
        taskset = 'taskset %s' % hex(1 << processor_num)

    cmds = '%s sysbench --max-time=%d --max-requests=10000000' \
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


def get_available_memory():
    try:
        return psutil.virtual_memory().total
    except Exception:
        return psutil.avail_phymem()


def check_mem_size(block_size, cpu_count):
    dsplit = re.compile(r'\d+')
    ssplit = re.compile(r'[A-Z]+')
    unit = ssplit.findall(block_size)
    unit_in_bytes = 1
    if unit[0] == 'K':
        unit_in_bytes = 1024
    elif unit[0] == 'M':
        unit_in_bytes = 1024 * 1024
    elif unit[0] == 'G':
        unit_in_bytes = 1024 * 1024 * 1024

    size_in_bytes = unit_in_bytes * \
        int(dsplit.findall(block_size)[0]) * cpu_count
    if (size_in_bytes > get_available_memory()):
        return False

    return True


def stop_netservers(message):
    sys.stderr.write('Stopping netservers\n')
    os.system("pkill -9 netperf")


def run_network_bench(message):
    run_netperf(message)


def run_netperf(message):
    sys.stderr.write('Benchmarking %s @%s for %d seconds\n' % (message.network_test, message.block_size, message.running_time))
    time.sleep(message.running_time)


def run_sysbench_memory(message):
    if message.parallel_mode == HM.FORKED:
        run_sysbench_memory_forked(message.hw, message.running_time, message.block_size, message.cpu_instances)
    else:
        run_sysbench_memory_threaded(message.hw, message.running_time, message.block_size, message.cpu_instances)


def run_sysbench_memory_threaded(hw_, max_time, block_size, cpu_count, processor_num=-1):
    'Running memtest on a processor'
    check_mem = check_mem_size(block_size, cpu_count)
    taskset = ''
    if (processor_num < 0):
        if check_mem is False:
            msg = ("Avoid Benchmarking memory @%s "
                   "from all CPUs, not enough memory\n")
            sys.stderr.write(msg % block_size)
            return
        sys.stderr.write('Benchmarking memory @%s from all CPUs '
                         'for %d seconds (%d threads)\n'
                         % (block_size, max_time, cpu_count))
    else:
        if check_mem is False:
            msg = ("Avoid Benchmarking memory @%s "
                   "from CPU %d, not enough memory\n")
            sys.stderr.write(msg % (block_size, processor_num))
            return

        sys.stderr.write('Benchmarking memory @%s from CPU %d'
                         ' for %d seconds (%d threads)\n'
                         % (block_size, processor_num, max_time, cpu_count))
        taskset = 'taskset %s' % hex(1 << processor_num)

    _cmd = '%s sysbench --max-time=%d --max-requests=100000000 ' \
           '--num-threads=%d --test=memory --memory-block-size=%s run'
    sysbench_cmd = subprocess.Popen(_cmd % (taskset, max_time,
                                            cpu_count, block_size),
                                    shell=True, stdout=subprocess.PIPE)

    for line in sysbench_cmd.stdout:
        if "transferred" in line:
            title, right = line.rstrip('\n').replace(' ', '').split('(')
            perf, useless = right.split('.')
            if processor_num == -1:
                hw_.append(('cpu', 'logical', 'threaded_bandwidth_%s'
                            % block_size, perf))
            else:
                hw_.append(('cpu', 'logical_%d' % processor_num, 'bandwidth_%s'
                            % block_size, perf))


def run_sysbench_memory_forked(hw_, max_time, block_size, cpu_count):
    'Running forked memtest on a processor'
    if check_mem_size(block_size, cpu_count) is False:
        cmd = 'Avoid benchmarking memory @%s from all' \
              ' CPUs (%d forked processes), not enough memory\n'
        sys.stderr.write(cmd % (block_size, cpu_count))
        return
    sys.stderr.write('Benchmarking memory @%s from all CPUs'
                     ' for %d seconds (%d forked processes)\n'
                     % (block_size, max_time, cpu_count))
    sysbench_cmd = '('
    for cpu in range(cpu_count):
        _cmd = 'sysbench --max-time=%d --max-requests=100000000 ' \
               '--num-threads=1 --test=memory --memory-block-size=%s run &'
        sysbench_cmd += _cmd % (max_time, block_size)

    sysbench_cmd.rstrip('&')
    sysbench_cmd += ')'

    global_perf = 0
    process = subprocess.Popen(
        sysbench_cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        if "transferred" in line:
            title, right = line.rstrip('\n').replace(' ', '').split('(')
            perf, useless = right.split('.')
            global_perf += int(perf)

    hw_.append(('cpu', 'logical', 'forked_bandwidth_%s' %
               (block_size), str(global_perf)))


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
