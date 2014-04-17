#!/usr/bin/env python
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

'''Main entry point for hardware and system detection routines in eDeploy.'''

import platform
import pprint
import re
import subprocess
import sys
import health_libs as HL
import os
import psutil

RAMP_TIME = 5
DEBUG = 0
available_memory = 0


def is_included(dict1, dict2):
    'Test if dict1 is included in dict2.'
    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True


def get_disks_name(hw__, without_bootable=False):
    disks = []
    for entry in hw__:
        if (entry[0] == 'disk' and entry[2] == 'size'):
            if without_bootable and is_booted_storage_device(entry[1]):
                sys.stderr.write("Skipping disk %s in destructive mode, "
                                 "this is the booted device !\n" % entry[1])
            elif 'I:' in entry[1]:
                if DEBUG:
                    sys.stderr.write("Ignoring HP hidden disk %s\n" % entry[1])
            else:
                disks.append(entry[1])
    return disks


def get_mac(hw_, level1, level2):
    for entry in hw_:
        if (level1 == entry[0] and level2 == entry[2]):
            return entry[3]
    return None


def search_cpuinfo(cpu_nb, item):
    cpuinfo = open('/proc/cpuinfo', 'r')
    found = False
    for line in cpuinfo:
        if line.strip():
            name, value = line.rstrip('\n').split(':')
            if "processor" in name and int(value) == cpu_nb:
                found = True
            if (item in name) and (found is True):
                return value.replace(' ', '')
    cpuinfo.close()
    return None


def get_bogomips(hw_, cpu_nb):
#    print "Getting Bogomips for CPU %d" % cpu_nb
    bogo = search_cpuinfo(cpu_nb, "bogomips")
    if bogo is not None:
        hw_.append(('cpu', 'logical_%d' % cpu_nb, 'bogomips', bogo))


def get_cache_size(hw_, cpu_nb):
#    print "Getting CacheSize for CPU %d" % cpu_nb
    cache_size = search_cpuinfo(cpu_nb, "cache size")
    if cache_size is not None:
        hw_.append(('cpu', 'logical_%d' % cpu_nb, 'cache_size', cache_size))


def cpu_perf(hw_, testing_time=10, burn_test=False):
    ' Detect the cpu speed'
    result = HL.get_value(hw_, 'cpu', 'logical', 'number')
    physical = HL.get_value(hw_, 'cpu', 'physical', 'number')

    # Individual Test aren't useful for burn_test
    if burn_test is False:
        if physical is not None:
            sys.stderr.write('CPU Performance: %d logical '
                             'CPU to test (ETA: %d seconds)\n'
                             % (int(physical), (int(physical) + 1) * testing_time))
            for cpu_nb in get_one_cpu_per_socket(hw_):
                get_bogomips(hw_, cpu_nb)
                get_cache_size(hw_, cpu_nb)
                HL.run_sysbench(hw_, testing_time, 1, cpu_nb)
    else:
        sys.stderr.write('CPU Burn: %d logical'
                         ' CPU to test (ETA: %d seconds)\n' % (
                             int(result), testing_time))

    HL.run_sysbench(hw_, testing_time, int(result))


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
    if (size_in_bytes > available_memory):
        return False

    return True


def run_memtest(hw_, max_time, block_size, cpu_count, processor_num=-1):
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

    _cmd = '%s sysbench --max-time=%d --max-requests=1000000 ' \
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


def run_forked_memtest(hw_, max_time, block_size, cpu_count):
    'Running forked memtest on a processor'
    if check_mem_size(block_size, cpu_count) is False:
        cmd = 'Avoid benchmarking memory @%s from all CPUs (%d processes), not enough memory\n'
        sys.stderr.write(cmd % (block_size, cpu_count))
        return
    sys.stderr.write('Benchmarking memory @%s from all CPUs'
                     ' for %d seconds (%d processes)\n'
                     % (block_size, max_time, cpu_count))
    sysbench_cmd = '('
    for cpu in range(cpu_count):
        _cmd = 'sysbench --max-time=%d --max-requests=1000000 ' \
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


def get_ddr_timing(hw_):
    'Report the DDR timings'
    sys.stderr.write('Reporting DDR Timings\n')
    found = False
    cmd = subprocess.Popen('ddr-timings-%s' % platform.machine(),
                           shell=True, stdout=subprocess.PIPE)
# DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B
# 0 |  11    15    15    31     7   511    11    31    15    63    31

    for line in cmd.stdout:
        if 'is a Triple' in line:
            hw_.append(('memory', 'DDR', 'type', '3'))
            continue

        if 'is a Dual' in line:
            hw_.append(('memory', 'DDR', 'type', '2'))
            continue

        if 'is a Single' in line:
            hw_.append(('memory', 'DDR', 'type', '1'))
            continue

        if 'is a Zero' in line:
            hw_.append(('memory', 'DDR', 'type', '0'))
            continue

        if "DDR" in line:
            found = True
            continue

        if (found is True):
            (ddr_channel, tCL, tRCD, tRP, tRAS,
             tRRD, tRFC, tWR, tWTPr,
             tRTPr, tFAW, B2B) = line.rstrip('\n').replace('|', ' ').split()
            ddr_channel = ddr_channel.replace('#', '')
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tCL', tCL))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRCD', tRCD))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRP', tRP))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRAS', tRAS))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRRD', tRRD))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRFC', tRFC))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tWR', tWR))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tWTPr', tWTPr))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRTPr', tRTPr))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tFAW', tFAW))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'B2B', B2B))


def mem_perf_burn(hw_, testing_time=10):
    'Report the memory performance'
    result = HL.get_value(hw_, 'cpu', 'logical', 'number')
    if result is not None:
        sys.stderr.write('Memory Burn: %d logical CPU'
                         ' to test (ETA: %d seconds)\n' % (
                             int(result), testing_time))
        run_memtest(hw_, testing_time, '128M', int(result))


def get_one_cpu_per_socket(hw):
    logical = get_value(hw, 'cpu', 'logical', 'number')
    current_phys_package_id = -1
    cpu_list = []
    for cpu_nb in range(int(logical)):
        cmdline = "cat /sys/devices/system/cpu/cpu%d/topology/physical_package_id" % int(cpu_nb)
        phys_cmd = subprocess.Popen(cmdline,
                                shell=True, stdout=subprocess.PIPE)
        for phys_str in phys_cmd.stdout:
            phys_id = int(phys_str.strip())
            if phys_id > current_phys_package_id:
                current_phys_package_id = phys_id
                cpu_list.append(current_phys_package_id)

    return cpu_list

def mem_perf(hw_, testing_time=5):
    'Report the memory performance'
    all_cpu_testing_time = 5
    block_size_list = ['1K', '4K', '1M', '16M', '128M', '1G', '2G']
    result = HL.get_value(hw_, 'cpu', 'logical', 'number')
    physical = HL.get_value(hw_, 'cpu', 'physical', 'number')
    if physical is not None:
        eta = int(physical) * len(block_size_list) * testing_time
        eta += 2 * (all_cpu_testing_time * len(block_size_list))
        sys.stderr.write('Memory Performance: %d logical CPU'
                         ' to test (ETA: %d seconds)\n'
                         % (int(physical), int(eta)))
        for cpu_nb in get_one_cpu_per_socket(hw_):
            for block_size in block_size_list:
                run_memtest(hw_, testing_time, block_size, 1, cpu_nb)

        # There is not need to test fork vs thread
        #  if only a single logical cpu is present
        if (int(result) > 1):
            for block_size in block_size_list:
                run_memtest(hw_, all_cpu_testing_time, block_size, int(result))

            for block_size in block_size_list:
                run_forked_memtest(hw_, all_cpu_testing_time,
                                   block_size, int(result))

    get_ddr_timing(hw_)


def run_fio(hw_, disks_list, mode, io_size, time):
    filelist = [f for f in os.listdir(".") if f.endswith(".fio")]
    for myfile in filelist:
        os.remove(myfile)
    fio = "fio --ioengine=libaio --invalidate=1 --ramp_time=%d --iodepth=32 " \
          "--runtime=%d --time_based --direct=1 " \
          "--bs=%s --rw=%s" % (RAMP_TIME, time, io_size, mode)

    global_disk_list = ''
    for disk in disks_list:
        if '/dev/' not in disk:
            disk = '/dev/%s' % disk
        # Flusing Disk's cache prior benchmark
        os.system("hdparm -f %s >/dev/null 2>&1" % disk)
        short_disk = disk.replace('/dev/', '')
        fio = "%s --name=MYJOB-%s --filename='%s'" % (fio, short_disk, disk)
        global_disk_list += '%s,' % short_disk
    global_disk_list = global_disk_list.rstrip(',')
    sys.stderr.write(
        'Benchmarking storage %s for %s seconds in '
        '%s mode with blocksize=%s\n' %
        (global_disk_list, time, mode, io_size))
    fio_cmd = subprocess.Popen(fio,
                               shell=True, stdout=subprocess.PIPE)
    current_disk = ''
    for line in fio_cmd.stdout:
        if ('MYJOB-' in line) and ('pid=' in line):
            # MYJOB-sda: (groupid=0, jobs=1): err= 0: pid=23652: Mon Sep  9
            # 16:21:42 2013
            current_disk = re.search('MYJOB-(.*): \(groupid', line).group(1)
            continue
        if ("read : io=" in line) or ("write: io=" in line):
             # read : io=169756KB, bw=16947KB/s, iops=4230, runt= 10017msec
            if (len(disks_list) > 1):
                mode_str = "simultaneous_%s_%s" % (mode, io_size)
            else:
                mode_str = "standalone_%s_%s" % (mode, io_size)

            try:
                perf = re.search('bw=(.*?B/s),', line).group(1)
            except Exception:
                sys.stderr.write('Failed at detecting '
                                 'bwps pattern with %s\n' % line)
            else:
                multiply = 1
                divide = 1
                if "MB/s" in perf:
                    multiply = 1024
                elif "KB/s" in perf:
                    multiply = 1
                elif "B/s" in perf:
                    divide = 1024
                try:
                    iperf = perf.replace(
                        'KB/s', '').replace('MB/s', '').replace('B/s', '')
                except Exception:
                    True
                hw_.append(('disk', current_disk, mode_str + '_KBps',
                            str(int(float(float(iperf) * multiply / divide)))))

            try:
                hw_.append(('disk', current_disk, mode_str + '_IOps',
                            re.search('iops=(.*),', line).group(1).strip(' ')))
            except Exception:
                sys.stderr.write('Failed at detecting iops '
                                 'pattern with %s\n' % line)


def get_output_filename(hw_):
    sysname = ''

    sysprodname = HL.get_value(hw_, 'system', 'product', 'name')
    if sysprodname:
        sysname = re.sub(r'\W+', '', sysprodname) + '-'

    sysprodvendor = HL.get_value(hw_, 'system', 'product', 'vendor')
    if sysprodvendor:
        sysname += re.sub(r'\W+', '', sysprodvendor) + '-'

    sysprodserial = HL.get_value(hw_, 'system', 'product', 'serial')
    if sysprodserial:
        sysname += re.sub(r'\W+', '', sysprodserial)

    mac = get_mac(hw_, 'network', 'serial')
    if mac:
        sysname += mac.replace(':', '-')

    return sysname + ".hw_"


def is_booted_storage_device(disk):
    cmdline = "grep -w /ahcexport /proc/mounts | cut -d ' ' -f 1 "
    "| sed -e 's/[0-9]*//g'"
    if '/dev/' not in disk:
        disk = '/dev/%s' % disk
    grep_cmd = subprocess.Popen(cmdline,
                                shell=True, stdout=subprocess.PIPE)
    for booted_disk in grep_cmd.stdout:
        booted_disk = booted_disk.rstrip('\n').strip()
        if booted_disk == disk:
            return True
    return False


def storage_perf_burn(hw_, allow_destructive, running_time=10):
    mode = "non destructive"
    if allow_destructive:
        mode = 'destructive'
        running_time = running_time / 2
    disks = get_disks_name(hw_)
    sys.stderr.write('Running storage burn on %d disks in'
                     ' %s mode for %d seconds\n' % (
                         len(disks), mode, 2 * running_time))
    if allow_destructive:
        run_fio(hw_, get_disks_name(hw_, True), "write", "1M", running_time)
        run_fio(hw_, get_disks_name(hw_, True),
                "randwrite", "4k", running_time)

    run_fio(hw_, disks, "read", "1M", running_time)
    run_fio(hw_, disks, "randread", "4k", running_time)


def storage_perf(hw_, allow_destructive, running_time=10):
    'Reporting disk performance'
    mode = "non destructive"
    # Let's count the number of runs in safe mode
    total_runtime = len(get_disks_name(hw_)) * (running_time + RAMP_TIME) * 2
    disks = get_disks_name(hw_)
    if (len(disks) > 1):
        total_runtime += 2 * (running_time + RAMP_TIME)

    if allow_destructive:
        total_runtime = total_runtime * 2
        mode = 'destructive'

    sys.stderr.write('Running storage bench on %d disks in'
                     ' %s mode for %d seconds\n' % (
                         len(disks), mode, total_runtime))
    for disk in disks:
        is_booted_storage_device(disk)
        if allow_destructive:
            if is_booted_storage_device(disk):
                sys.stderr.write("Skipping disk %s in destructive mode,"
                                 " this is the booted device !" % disk)
            else:
                run_fio(hw_, ['%s' % disk], "write", "1M", running_time)
                run_fio(hw_, ['%s' % disk], "randwrite", "4k", running_time)

        run_fio(hw_, ['%s' % disk], "read", "1M", running_time)
        run_fio(hw_, ['%s' % disk], "randread", "4k", running_time)

    if (len(disks) > 1):
        if allow_destructive:
            run_fio(hw_, get_disks_name(hw_, True), "write", "1M",
                    running_time)
            run_fio(hw_, get_disks_name(hw_, True), "randwrite", "4k",
                    running_time)
        run_fio(hw_, disks, "read", "1M", running_time)
        run_fio(hw_, disks, "randread", "4k", running_time)


def _main():
    global available_memory
    'Command line entry point.'
    allow_destructive = False
    try:
        if os.environ['DESTRUCTIVE_MODE']:
            allow_destructive = True
    except Exception:
        True

    hrdw = eval(open(sys.argv[1]).read(-1))

    available_memory = psutil.virtual_memory().total
    sys.stderr.write("Available memory before run = %s\n" % available_memory)

    mode = 'cpu,memory,storage'
    try:
        mode = sys.argv[2]
    except Exception:
        True

    if 'cpu-burn' in mode:
        cpu_perf(hrdw, 60, True)
    elif 'cpu' in mode:
        cpu_perf(hrdw)

    if 'memory-burn' in mode:
        mem_perf_burn(hrdw, 60)
    elif 'memory' in mode:
        mem_perf(hrdw)

    if 'storage-burn' in mode:
        storage_perf_burn(hrdw, allow_destructive, 30)
    elif 'storage' in mode:
        storage_perf(hrdw, allow_destructive)

    # Saving result to stdout but also to a filename based on the hw properties
    output_filename = get_output_filename(hrdw)
    sys.stderr.write("Saving results in %s\n" % output_filename)
    with open(output_filename, 'w') as state_file:
        pprint.pprint(hrdw, stream=state_file)
    pprint.pprint(hrdw)

if __name__ == "__main__":
    _main()
