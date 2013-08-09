#!/usr/bin/env python
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

'''Main entry point for hardware and system detection routines in eDeploy.'''

import commands
import pprint
import sys
import xml.etree.ElementTree as ET

import diskinfo
import hpacucli
import os


def size_in_gb(size):
    'Return the size in GB without the unit.'
    ret = size.replace(' ', '')
    if ret[-2:] == 'GB':
        return ret[:-2]
    elif ret[-2:] == 'TB':
        return ret[:-2] + '000'
    else:
        return ret


def detect_hpa(hw_lst):
    'Detect HP RAID controller configuration.'
    try:
        cli = hpacucli.Cli(debug=False)
        if not cli.launch():
            return False
        controllers = cli.ctrl_all_show()
        if len(controllers) == 0:
            sys.stderr.write("Info: No hpa controller found\n")
            return False

        for controller in controllers:
            slot = 'slot=%d' % controller[0]
            for _, disks in cli.ctrl_pd_all_show(slot):
                for disk in disks:
                    hw_lst.append(('disk', disk[0], 'type', disk[1]))
                    hw_lst.append(('disk', disk[0], 'slot', str(controller[0])))
                    hw_lst.append(('disk', disk[0], 'size', size_in_gb(disk[2])))
        return True
    except hpacucli.Error as expt:
        sys.stderr.write('Info: detect_hpa : %s\n' % expt.value)
        return False


def detect_disks(hw_lst):
    'Detect disks.'
    names = diskinfo.disknames()
    sizes = diskinfo.disksizes(names)
    for name in [name for name, size in sizes.items() if size > 0]:
        hw_lst.append(('disk', name, 'size', str(sizes[name])))


def modprobe(module):
    'Load a kernel module using modprobe.'
    status, _ = commands.getstatusoutput('modprobe %s' % module)
    if status == 0:
        sys.stderr.write('Info: Probing %s failed\n' % module)


def detect_ipmi(hw_lst):
    'Detect IPMI interfaces.'
    modprobe("ipmi_smb")
    modprobe("ipmi_si")
    modprobe("ipmi_devintf")
    if os.path.exists('/dev/ipmi0') or os.path.exists('/dev/ipmi/0') \
            or os.path.exists('/dev/ipmidev/0'):
        for channel in range(0, 16):
            status, _ = commands.getstatusoutput('ipmitool channel info %d 2>&1 | grep -sq Volatile' % channel)
            if status == 0:
                hw_lst.append(('system', 'ipmi', 'channel', channel))
                break
    else:
        # Are we running under an hypervisor ?
        status, _ = commands.getstatusoutput('grep -qi hypervisor /proc/cpuinfo')
        if status == 0:
            # Yes ! So let's create a fake ipmi device for testing purpose
            hw_lst.append(('system', 'ipmi-fake', 'channel', 0))
            sys.stderr.write('Info: Added fake IPMI device\n')
            return True
        else:
            sys.stderr.write('Info: No IPMI device found\n')
            return False


def detect_system(hw_lst, output=None):
    'Detect system characteristics from the output of lshw.'
    if output:
        status = 0
    else:
        status, output = commands.getstatusoutput('lshw -xml')
    if status == 0:
        xml = ET.fromstring(output)
        elt = xml.findall("./node/serial")
        if len(elt) >= 1:
            hw_lst.append(('system', 'product', 'serial', elt[0].text))
        elt = xml.findall("./node/product")
        if len(elt) >= 1:
            hw_lst.append(('system', 'product', 'name', elt[0].text))
        elt = xml.findall("./node/vendor")
        if len(elt) >= 1:
            hw_lst.append(('system', 'product', 'vendor', elt[0].text))
        elt = xml.findall("./node/version")
        if len(elt) >= 1:
            hw_lst.append(('system', 'product', 'version', elt[0].text))
        elt = xml.findall(".//node[@id='memory']/size")
        if len(elt) >= 1:
            hw_lst.append(('system', 'memory', 'size', elt[0].text))
        for elt in xml.findall(".//node[@class='network']"):
            name = elt.find('logicalname')
            if name is not None:
                serial = elt.find('serial')
                if serial is not None:
                    hw_lst.append(('network', name.text, 'serial',
                                   serial.text))
                vendor = elt.find('vendor')
                if vendor is not None:
                    hw_lst.append(('network', name.text, 'vendor',
                                   vendor.text))
                product = elt.find('product')
                if product is not None:
                    hw_lst.append(('network', name.text, 'product',
                                   product.text))
                size = elt.find('size')
                if size is not None:
                    hw_lst.append(('network', name.text, 'size', size.text))
                ipv4 = elt.find("configuration/setting[@id='ip']")
                if ipv4 is not None:
                    hw_lst.append(('network', name.text, 'ipv4',
                                   ipv4.attrib['value']))
                link = elt.find("configuration/setting[@id='link']")
                if link is not None:
                    hw_lst.append(('network', name.text, 'link',
                                   link.attrib['value']))
                driver = elt.find("configuration/setting[@id='driver']")
                if driver is not None:
                    hw_lst.append(('network', name.text, 'driver',
                                   driver.attrib['value']))

    else:
        sys.stderr.write("Unable to run lshw: %s\n" % output)

    status, output = commands.getstatusoutput('nproc')
    if status == 0:
        hw_lst.append(('system', 'cpu', 'number', output))

if __name__ == "__main__":
    l = []

    detect_hpa(l)
    detect_disks(l)
    detect_system(l)
    detect_ipmi(l)
    pprint.pprint(l)
