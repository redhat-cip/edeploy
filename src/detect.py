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

import commands
import pprint
import sys
import xml.etree.ElementTree as ET

import diskinfo
import hpacucli
import os

def size_in_gb(s):
    'Return the size in GB without the unit.'
    r = s.replace(' ', '')
    if r[-2:] == 'GB':
        return r[:-2]
    elif r[-2:] == 'TB':
        return r[:-2] + '000'

def detect_hpa(l):
    try:
        cli = hpacucli.Cli(debug=False)
        if not cli.launch():
            return False
        controllers = cli.ctrl_all_show()
        if len(controllers) == 0:
            return False

        for controller in controllers:
            slot = 'slot=%d' % controller[0]
            for name, disks in cli.ctrl_pd_all_show(slot):
                for disk in disks:
                    l.append(('disk', disk[0], 'type', disk[1]))
                    l.append(('disk', disk[0], 'slot', str(controller[0])))
                    l.append(('disk', disk[0], 'size', size_in_gb(disk[2])))
        return True
    except hpacucli.Error as e:
        import sys
	sys.stderr.write('Info: detect_hpa : %s\n' % e.value)
        return False

def detect_disks(l):
    names = diskinfo.disknames()
    sizes = diskinfo.disksizes(names)
    for name in [name for name, size in sizes.items() if size > 0]:
        l.append(('disk', name, 'size', str(sizes[name])))

def modprobe(module):
    status, output = commands.getstatusoutput('modprobe %s' % module)
    if status == 0:
	sys.stderr.write('Info: Probing %s failed\n' % module)

def detect_ipmi(l):
    modprobe("ipmi_smb")
    modprobe("ipmi_si")
    modprobe("ipmi_devintf")
    if os.path.exists('/dev/ipmi0') or os.path.exists('/dev/ipmi/0') or os.path.exists('/dev/ipmidev/0'):
    	for channel in range(0,16):
        	status, output = commands.getstatusoutput('ipmitool channel info %d 2>&1 | grep -sq Volatile' % channel)
		if status == 0:
	    		l.append(('system', 'ipmi', 'channel', channel))
			break;
    else:
	# Are we running under an hypervisor ?
	status, output = commands.getstatusoutput('grep -qi hypervisor /proc/cpuinfo')
	if status == 0:
		# Yes ! So let's create a fake ipmi device for testing purpose
	   	l.append(('system', 'ipmi-fake', 'channel', 0))
		sys.stderr.write('Info: Added fake IPMI device\n')
		return True
	else:
		sys.stderr.write('Info: No IPMI device found\n')
		return False

def detect_system(l, output=None):
    if output:
        status = 0
    else:
        status, output = commands.getstatusoutput('lshw -xml')
    if status == 0:
        xml = ET.fromstring(output)
        e = xml.findall("./node/serial")
        if len(e) >= 1:
            l.append(('system', 'product', 'serial', e[0].text))
        e = xml.findall("./node/product")
        if len(e) >= 1:
            l.append(('system', 'product', 'name', e[0].text))
        e = xml.findall("./node/vendor")
        if len(e) >= 1:
            l.append(('system', 'product', 'vendor', e[0].text))
        e = xml.findall("./node/version")
        if len(e) >= 1:
            l.append(('system', 'product', 'version', e[0].text))
        e = xml.findall(".//node[@id='memory']/size")
        if len(e) >= 1:
            l.append(('system', 'memory', 'size', e[0].text))
        for e in xml.findall(".//node[@class='network']"):
            name = e.find('logicalname')
            if name is not None:
                serial = e.find('serial')
                if serial is not None:
                    l.append(('network', name.text, 'serial', serial.text))
		vendor = e.find('vendor')
                if vendor is not None:
                    l.append(('network', name.text, 'vendor', vendor.text))
		product = e.find('product')
		if product is not None:
                    l.append(('network', name.text, 'product', product.text))
                size = e.find('size')
                if size is not None:
                    l.append(('network', name.text, 'size', size.text))
                ip = e.find("configuration/setting[@id='ip']")
                if ip is not None:
                    l.append(('network', name.text, 'ipv4', ip.attrib['value']))
                link = e.find("configuration/setting[@id='link']")
                if link is not None:
                    l.append(('network', name.text, 'link', link.attrib['value']))
		driver = e.find("configuration/setting[@id='driver']")
                if driver is not None:
                    l.append(('network', name.text, 'driver', driver.attrib['value']))

    else:
        sys.stderr.write("Unable to run lshw: %s\n" % output)

    status, output = commands.getstatusoutput('nproc')
    if status == 0:
        l.append(('system', 'cpu', 'number', output))

if __name__ == "__main__":
    l = []

    detect_hpa(l)
    detect_disks(l)
    detect_system(l)
    detect_ipmi(l)
    pprint.pprint(l)
