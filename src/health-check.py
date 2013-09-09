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

from commands import getstatusoutput as cmd
import pprint
import sys
import xml.etree.ElementTree as ET
import subprocess
import platform

import diskinfo
import hpacucli
import os


def is_included(dict1, dict2):
    'Test if dict1 is included in dict2.'
    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True


def get_value(hw, level1, level2, level3):
    for entry in hw:
        if (level1==entry[0] and level2==entry[1] and level3==entry[2]):
            return entry[3]
    return None

def search_cpuinfo(cpu_nb, item):
    f=open('/proc/cpuinfo','r')
    found=False
    for line in f:
        if line.strip():
            name,value= line.rstrip('\n').split(':')
            if "processor" in name  and int(value)==cpu_nb:
                found=True
            if item in name and found==True:
                return value.replace(' ', '')
    f.close()
    return None

def get_bogomips(hw,cpu_nb):
#    print "Getting Bogomips for CPU %d" % cpu_nb
    bogo=search_cpuinfo(cpu_nb, "bogomips")
    if bogo is not None:
           hw.append(('cpu', 'logical_%d'%cpu_nb, 'bogomips', bogo))

def get_cache_size(hw,cpu_nb):
#    print "Getting CacheSize for CPU %d" % cpu_nb
    cache_size=search_cpuinfo(cpu_nb, "cache size")
    if cache_size is not None:
           hw.append(('cpu', 'logical_%d'%cpu_nb, 'cache_size', cache_size))

def run_sysbench(hw, max_time, cpu_count, processor_num=-1):
    'Running sysbench cpu stress of a give amount of logical cpu'
    taskset=''
    if (processor_num < 0):
        sys.stderr.write('Benchmarking all CPUs for %d seconds (%d threads)\n' % (max_time,cpu_count))
    else:
        sys.stderr.write('Benchmarking CPU %d for %d seconds (%d threads)\n' % (processor_num,max_time,cpu_count))
        taskset='taskset %s' % hex(1 << processor_num)

    cmd = subprocess.Popen('%s sysbench --max-time=%d --max-requests=1000000 --num-threads=%d --test=cpu --cpu-max-prime=15000 run' %(taskset, max_time,cpu_count),
             shell=True, stdout=subprocess.PIPE)
    for line in cmd.stdout:
             if "total number of events" in line:
                 title,perf = line.rstrip('\n').replace(' ','').split(':')
                 if processor_num==-1:
                     hw.append(('cpu', 'logical', 'loops_per_sec', int(perf)/max_time))
                 else:
                     hw.append(('cpu', 'logical_%d'%processor_num, 'loops_per_sec', int(perf)/max_time))

def cpu_perf(hw):
    ' Detect the cpu speed'
    result=get_value(hw,'cpu','logical','number')
    if result is not None:
        for cpu_nb in range(int(result)):
            get_bogomips(hw,cpu_nb)
            get_cache_size(hw,cpu_nb)
            run_sysbench(hw,5, 1, cpu_nb)
    run_sysbench(hw,5, int(result))

def run_memtest(hw, max_time, block_size, cpu_count, processor_num=-1):
    'Running memtest on a processor'
    taskset=''
    if (processor_num < 0):
        sys.stderr.write('Benchmarking memory @%s from all CPUs for %d seconds (%d threads)\n' % (block_size, max_time,cpu_count))
    else:
        sys.stderr.write('Benchmarking memory @%s from CPU %d for %d seconds (%d threads)\n' % (block_size, processor_num,max_time,cpu_count))
        taskset='taskset %s' % hex(1 << processor_num)

    cmd = subprocess.Popen('%s sysbench --max-time=%d --max-requests=1000000 --num-threads=1 --test=memory --memory-block-size=%s run' %(taskset, max_time,block_size),
             shell=True, stdout=subprocess.PIPE)
    for line in cmd.stdout:
             if "transferred" in line:
                 title,right = line.rstrip('\n').replace(' ','').split('(')
                 perf,useless = right.split('.')
                 if processor_num==-1:
                     hw.append(('cpu', 'logical', 'bandwidth_%s'%block_size, perf))
                 else:
                     hw.append(('cpu', 'logical_%d'%processor_num, 'bandwidth_%s'%block_size, perf))

def get_ddr_timing(hw):
    'Report the DDR timings'
    sys.stderr.write('Reporting DDR Timings\n')
    found=False
    cmd = subprocess.Popen('ddr-timings-%s'% platform.machine(),
                         shell=True, stdout=subprocess.PIPE)
#DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B
# #0 |  11    15    15    31     7   511    11    31    15    63    31

    for line in cmd.stdout:
             if "DDR" in line:
                found=True
                continue;
             if (found):
                ddr_channel,tCL,tRCD,tRP,tRAS,tRRD,tRFC,tWR,tWTPr,tRTPr,tFAW,B2B = line.rstrip('\n').replace('|',' ').split()
                ddr_channel=ddr_channel.replace('#','')
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tCL', tCL))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tRCD', tRCD))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tRP', tRP))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tRAS', tRAS))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tRRD', tRRD))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tRFC', tRFC))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tWR', tWR))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tWTPr', tWTPr))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tRTPr', tRTPr))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'tFAW', tFAW))
                hw.append(('memory', 'DDR_%s'%ddr_channel, 'B2B', B2B))


def mem_perf(hw):
    'Report the memory performance'
    block_size_list=['1K', '4K', '1M', '16M', '128M', '1G']
    result=get_value(hw,'cpu','logical','number')
    if result is not None:
        for cpu_nb in range(int(result)):
            for block_size in block_size_list:
                run_memtest(hw, 3, block_size, 1, cpu_nb)

    for block_size in block_size_list:
        run_memtest(hw, 3, block_size, int(result))

    get_ddr_timing(hw)

def _main():
    'Command line entry point.'
    hrdw = eval(open(sys.argv[1]).read(-1))

    cpu_perf(hrdw)
    mem_perf(hrdw)
    pprint.pprint(hrdw)

if __name__ == "__main__":
    _main()
