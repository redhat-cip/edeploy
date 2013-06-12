#!/usr/bin/env python

import commands
import pprint
import sys
import xml.etree.ElementTree as ET

import diskinfo
import hpacucli
import matcher


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
        sys.stderr.write('Error: %s\n' % e.value)
        return False

def detect_disks(l):
    names = diskinfo.disknames()
    sizes = diskinfo.disksizes(names)
    for name in [name for name, size in sizes.items() if size > 0]:
        l.append(('disk', name, 'size', str(sizes[name])))

def detect_system(l):
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
        for e in xml.findall(".//node[@class='network']"):
            name = e.find('logicalname')
            if name is not None:
                serial = e.find('serial')
                if serial is not None:
                    l.append(('network', name.text, 'serial', serial.text))
                size = e.find('size')
                if size is not None:
                    l.append(('network', name.text, 'size', size.text))
                ip = e.find("configuration/setting[@id='ip']")
                if ip is not None:
                    l.append(('network', name.text, 'ipv4', ip.attrib['value']))
    
    status, output = commands.getstatusoutput('nproc')
    if status == 0:
        l.append(('system', 'cpu', 'number', output))

if __name__ == "__main__":
    l = []
    
    detect_hpa(l)
    detect_disks(l)
    detect_system(l)
    
    pprint.pprint(l)
