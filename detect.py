#!/usr/bin/env python

import pprint
import sys

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

l = []

detect_hpa(l)
detect_disks(l)

pprint.pprint(l)
