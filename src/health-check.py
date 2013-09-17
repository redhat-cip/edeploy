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
import re

import diskinfo
import hpacucli
import os

ramp_time=5
DEBUG=0

def is_included(dict1, dict2):
    'Test if dict1 is included in dict2.'
    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True

def get_disks_name(hw,without_bootable=False):
    disks=[]
    for entry in hw:
        if (entry[0]=='disk' and entry[2]=='size'):
            if without_bootable and is_booted_storage_device(entry[1]):
                sys.stderr.write("Skipping disk %s in destructive mode, this is the booted device !\n"%entry[1])
            elif 'I:' in entry[1]:
                if DEBUG:
                    sys.stderr.write("Ignoring HP hidden disk %s\n"%entry[1])
            else:
                disks.append(entry[1])
    return disks

def get_value(hw, level1, level2, level3):
    for entry in hw:
        if (level1==entry[0] and level2==entry[1] and level3==entry[2]):
            return entry[3]
    return None

def get_mac(hw, level1, level2):
    for entry in hw:
        if (level1==entry[0] and level2==entry[2]):
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

def cpu_perf(hw,testing_time=5,burn_test=False):
    ' Detect the cpu speed'
    result=get_value(hw,'cpu','logical','number')

    # Individual Test aren't useful for burn_test
    if burn_test==False:
        if result is not None:
            sys.stderr.write('CPU Performance: %d logical CPU to test (ETA: %d seconds)\n'%(int(result),(int(result)+1)*testing_time))
            for cpu_nb in range(int(result)):
                get_bogomips(hw,cpu_nb)
                get_cache_size(hw,cpu_nb)
                run_sysbench(hw,testing_time, 1, cpu_nb)
    else:
        sys.stderr.write('CPU Burn: %d logical CPU to test (ETA: %d seconds)\n'%(int(result),testing_time))

    run_sysbench(hw, testing_time, int(result))

def run_memtest(hw, max_time, block_size, cpu_count, processor_num=-1):
    'Running memtest on a processor'
    taskset=''
    if (processor_num < 0):
        sys.stderr.write('Benchmarking memory @%s from all CPUs for %d seconds (%d threads)\n' % (block_size, max_time,cpu_count))
    else:
        sys.stderr.write('Benchmarking memory @%s from CPU %d for %d seconds (%d threads)\n' % (block_size, processor_num,max_time,cpu_count))
        taskset='taskset %s' % hex(1 << processor_num)

    cmd = subprocess.Popen('%s sysbench --max-time=%d --max-requests=1000000 --num-threads=%d --test=memory --memory-block-size=%s run' %(taskset, max_time,cpu_count, block_size),
             shell=True, stdout=subprocess.PIPE)
    for line in cmd.stdout:
             if "transferred" in line:
                 title,right = line.rstrip('\n').replace(' ','').split('(')
                 perf,useless = right.split('.')
                 if processor_num==-1:
                     hw.append(('cpu', 'logical', 'threaded_bandwidth_%s'%block_size, perf))
                 else:
                     hw.append(('cpu', 'logical_%d'%processor_num, 'bandwidth_%s'%block_size, perf))

def run_forked_memtest(hw, max_time, block_size, cpu_count):
    'Running forked memtest on a processor'
    sys.stderr.write('Benchmarking memory @%s from all CPUs for %d seconds (%d processes)\n' % (block_size, max_time,cpu_count))
    cmd='('
    for cpu in range(cpu_count):
        cmd +='sysbench --max-time=%d --max-requests=1000000 --num-threads=1 --test=memory --memory-block-size=%s run &' %(max_time, block_size)

    cmd.rstrip('&')
    cmd+=')'

    global_perf=0
    process=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
             if "transferred" in line:
                 title,right = line.rstrip('\n').replace(' ','').split('(')
                 perf,useless = right.split('.')
                 global_perf+=int(perf)

    hw.append(('cpu', 'logical', 'forked_bandwidth_%s'%block_size, global_perf))

def get_ddr_timing(hw):
    'Report the DDR timings'
    sys.stderr.write('Reporting DDR Timings\n')
    found=False
    cmd = subprocess.Popen('ddr-timings-%s'% platform.machine(),
                         shell=True, stdout=subprocess.PIPE)
#DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B
# #0 |  11    15    15    31     7   511    11    31    15    63    31

    for line in cmd.stdout:
             if 'is a Triple' in line:
                hw.append(('memory', 'DDR', 'type', '3'))
                continue

             if 'is a Dual' in line:
                hw.append(('memory', 'DDR', 'type', '2'))
                continue

             if 'is a Single' in line:
                hw.append(('memory', 'DDR', 'type', '1'))
                continue

             if 'is a Zero' in line:
                hw.append(('memory', 'DDR', 'type', '0'))
                continue

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

def mem_perf_burn(hw, testing_time=10):
    'Report the memory performance'
    result=get_value(hw,'cpu','logical','number')
    if result is not None:
        sys.stderr.write('Memory Burn: %d logical CPU to test (ETA: %d seconds)\n'%(int(result),testing_time))
        run_memtest(hw, testing_time, '128M', int(result))

def mem_perf(hw, testing_time=1):
    'Report the memory performance'
    all_cpu_testing_time=5
    block_size_list=['1K', '4K', '1M', '16M', '128M', '1G', '2G']
    result=get_value(hw,'cpu','logical','number')
    if result is not None:
        sys.stderr.write('Memory Performance: %d logical CPU to test (ETA: %d seconds)\n'%(int(result),(int(result))*len(block_size_list)*testing_time+2*all_cpu_testing_time*len(block_size_list)))
        for cpu_nb in range(int(result)):
            for block_size in block_size_list:
                run_memtest(hw, testing_time, block_size, 1, cpu_nb)

        for block_size in block_size_list:
            run_memtest(hw, all_cpu_testing_time, block_size, int(result))

        for block_size in block_size_list:
            run_forked_memtest(hw, all_cpu_testing_time, block_size, int(result))

    get_ddr_timing(hw)

def run_fio(hw,disks_list,mode,io_size,time):
    filelist = [ f for f in os.listdir(".") if f.endswith(".fio") ]
    for f in filelist:
        os.remove(f)
    fio="fio --ioengine=libaio --invalidate=1 --ramp_time=%d --iodepth=32 --runtime=%d --time_based --direct=1 --bs=%s --rw=%s"%(ramp_time, time,io_size,mode)
    global_disk_list=''
    for disk in disks_list:
        if not '/dev/' in disk:
            disk='/dev/%s'%disk
        short_disk=disk.replace('/dev/','')
        fio="%s --name=MYJOB-%s --filename='%s'" %(fio,short_disk,disk)
        global_disk_list+='%s,'%short_disk
    global_disk_list=global_disk_list.rstrip(',')
    sys.stderr.write('Benchmarking storage %s for %s seconds in %s mode with blocksize=%s\n'%(global_disk_list,time,mode,io_size))
    cmd = subprocess.Popen(fio,
                        shell=True, stdout=subprocess.PIPE)
    current_disk=''
    for line in cmd.stdout:
        if ('MYJOB-' in line) and ('pid=' in line):
            #MYJOB-sda: (groupid=0, jobs=1): err= 0: pid=23652: Mon Sep  9 16:21:42 2013
            current_disk = re.search('MYJOB-(.*): \(groupid',line).group(1)
            continue
        if ("read : io=" in line) or ("write: io=" in line):
             #read : io=169756KB, bw=16947KB/s, iops=4230, runt= 10017msec
             if (len(disks_list)>1):
                 mode_str="simultaneous_%s_%s"%(mode,io_size)
             else:
                 mode_str="standalone_%s_%s"%(mode,io_size)

             try:
                 perf=re.search('bw=(.*?B/s),',line).group(1)
             except:
                sys.stderr.write('Failed at detecting bwps pattern with %s\n'%line)
             else:
                 multiply=1
                 divide=1
                 if "MB/s" in perf:
                    multiply=1024
                 elif "KB/s" in perf:
                    multiply=1
                 elif "B/s" in perf:
                    divide=1024
                 try:
                    iperf=perf.replace('KB/s','').replace('B/s','').replace('MB/s','')
                 except:
                     True
                 hw.append(('disk',current_disk,mode_str+'_KBps', int(float(float(iperf)*multiply/divide))))

             try:
                 hw.append(('disk',current_disk,mode_str+'_IOps', re.search('iops=(.*),',line).group(1)))
             except:
                sys.stderr.write('Failed at detecting iops pattern with %s\n'%line)

def get_output_filename(hw):
    sysname=''

    sysprodname=get_value(hw,'system', 'product', 'name')
    if sysprodname:
        sysname=re.sub(r'\W+', '', sysprodname) + '-'

    sysprodvendor=get_value(hw,'system', 'product', 'vendor')
    if sysprodvendor:
        sysname += re.sub(r'\W+', '', sysprodvendor) + '-'

    sysprodserial=get_value(hw,'system', 'product', 'serial')
    if sysprodserial:
        sysname += re.sub(r'\W+', '', sysprodserial)

    mac=get_mac(hw,'network', 'serial')
    if mac:
        sysname += mac.replace(':', '-')

    return sysname+".hw"

def is_booted_storage_device(disk):
    cmdline="grep -w /ahcexport /proc/mounts | cut -d ' ' -f 1 | sed -e 's/[0-9]*//g'"
    if not '/dev/' in disk:
            disk='/dev/%s'%disk
    cmd = subprocess.Popen(cmdline,
            shell=True, stdout=subprocess.PIPE)
    for booted_disk in cmd.stdout:
        booted_disk=booted_disk.rstrip('\n').strip()
        if booted_disk == disk:
            return True
    return False

def storage_perf_burn(hw,allow_destructive,running_time=10):
    mode="non destructive"
    if allow_destructive:
        mode='destructive'
        running_time=running_time / 2
    disks=get_disks_name(hw)
    sys.stderr.write('Running storage burn on %d disks in %s mode for %d seconds\n'%(len(disks),mode,2*running_time))

    run_fio(hw,disks,"randread","4k",running_time)
    run_fio(hw,disks,"read","1M",running_time)
    if allow_destructive:
        run_fio(hw, get_disks_name(hw, True),"randwrite","4k",running_time)
        run_fio(hw, get_disks_name(hw, True),"write","1M",running_time)

def storage_perf(hw,allow_destructive,running_time=10):
    'Reporting disk performance'
    mode="non destructive"
    # Let's count the number of runs in safe mode
    total_runtime=len(get_disks_name(hw))*(running_time+ramp_time)*2
    disks=get_disks_name(hw)
    if (len(disks)>1):
        total_runtime+=2*(running_time+ramp_time)

    if allow_destructive:
        total_runtime=total_runtime*2
        mode='destructive'

    sys.stderr.write('Running storage bench on %d disks in %s mode for %d seconds\n'%(len(disks),mode,total_runtime))
    for disk in disks:
        is_booted_storage_device(disk)
        run_fio(hw, ['%s'%disk],"randread","4k",running_time)
        run_fio(hw, ['%s'%disk],"read","1M",running_time)
        if allow_destructive:
            if is_booted_storage_device(disk):
                sys.stderr.write("Skipping disk %s in destructive mode, this is the booted device !"%disk)
            else:
                run_fio(hw, ['%s'%disk],"randwrite","4k",running_time)
                run_fio(hw, ['%s'%disk],"write","1M",running_time)

    if (len(disks)>1):
        run_fio(hw,disks,"randread","4k",running_time)
        run_fio(hw,disks,"read","1M",running_time)
        if allow_destructive:
            run_fio(hw, get_disks_name(hw, True),"randwrite","4k",running_time)
            run_fio(hw, get_disks_name(hw, True),"write","1M",running_time)

def _main():
    'Command line entry point.'
    allow_destructive=False
    try:
        if os.environ['DESTRUCTIVE_MODE']:
            allow_destructive=True
    except:
        True

    hrdw = eval(open(sys.argv[1]).read(-1))

    mode='cpu,memory,storage'
    try:
        mode=sys.argv[2]
    except:
        True

    if 'cpu-burn' in mode:
        cpu_perf(hrdw,60,True)
    elif 'cpu' in mode:
        cpu_perf(hrdw)

    if 'memory-burn' in mode:
        mem_perf_burn(hrdw,60)
    elif 'memory' in mode:
        mem_perf(hrdw)

    if 'storage-burn' in mode:
        storage_perf_burn(hrdw,allow_destructive,30)
    elif 'storage' in mode:
        storage_perf(hrdw,allow_destructive)

    # Saving result to stdout but also to a filename based on the hw properties
    output_filename=get_output_filename(hrdw)
    sys.stderr.write("Saving results in %s\n"%output_filename)
    with open(output_filename, 'w') as state_file:
                pprint.pprint(hrdw, stream=state_file)
    pprint.pprint(hrdw)

if __name__ == "__main__":
    _main()
