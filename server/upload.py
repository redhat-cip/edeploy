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

'''CGI script part of the eDeploy system.

It receives on its file form a file containing a Python dictionnary
with the hardware detected on the remote host. In return, it sends
a Python configuration script corresponding to the matched config.

If nothing matches, nothing is returned. So the system can abort
its configuration.

On the to be configured host, it is usally called like that:

$ curl -i -F name=test -F file=@/tmp/hw.lst http://localhost/cgi-bin/upload.py
'''

import atexit
import ConfigParser
import cgi
import cgitb
import commands
import errno
import os
import pprint
import re
import sys
import time

import matcher

_RANGE_REGEXP = re.compile('^(.*?)([0-9]+-[0-9]+(:([0-9]+-[0-9]+))*)(.*)$')


def _generate_range(num_range):
    'Generate number for range specified like 10-12:20-30.'
    for rang in num_range.split(':'):
        boundaries = rang.split('-')
        if len(boundaries) == 2:
            for res in range(int(boundaries[0]), int(boundaries[1]) + 1):
                yield str(res)
        else:
            yield num_range


def _generate_values(pattern):
    '''Create a generator for range of IPv4 or names with ranges
defined like 10-12:15-18 or from a list of entries.'''
    if isinstance(pattern, list) or isinstance(pattern, tuple):
        for elt in pattern:
            yield elt
    else:
        parts = pattern.split('.')
        if len(parts) == 4 and (pattern.find(':') != -1 or
                                pattern.find('-') != -1):
            gens = [_generate_range(part) for part in parts]
            for part0 in gens[0]:
                for part1 in gens[1]:
                    for part2 in gens[2]:
                        for part3 in gens[3]:
                            yield '.'.join((part0, part1, part2, part3))
                        gens[3] = _generate_range(parts[3])
                    gens[2] = _generate_range(parts[2])
                gens[1] = _generate_range(parts[1])
        else:
            res = _RANGE_REGEXP.search(pattern)
            if res:
                head = res.group(1)
                foot = res.group(res.lastindex)
                for num in _generate_range(res.group(2)):
                    yield head + num + foot
            else:
                for _ in xrange(16387064):
                    yield pattern

STRING_TYPE = type('')


def generate(model):
    '''Generate a list of dict according to a model. Ipv4 ranges are
handled by _generate_ip.'''
    # Safe guard for models without ranges
    for value in model.values():
        if type(value) != STRING_TYPE:
            break
        elif _RANGE_REGEXP.search(value):
            break
    else:
        return [model]
    # The model has a range starting from here
    result = []
    copy = {}
    copy.update(model)
    for key, value in copy.items():
        copy[key] = _generate_values(value)
    while True:
        try:
            entry = {}
            for key in copy:
                entry[key] = copy[key].next()
            result.append(entry)
        except StopIteration:
            break
    return result


def lock(filename):
    '''Lock a file and return a file descriptor. Need to call unlock to release
the lock.'''
    count = 0
    while True:
        try:
            lock_fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except OSError, xcpt:
            if xcpt.errno != errno.EEXIST:
                raise
            if count % 30 == 0:
                log('waiting for lock %s' % filename)
            time.sleep(1)
            count += 1
    return lock_fd


def unlock(lock_fd, filename):
    'Called after the lock function to release a lock.'
    if lock_fd:
        os.close(lock_fd)
        os.unlink(filename)


def log(msg):
    'Error Logging.'
    sys.stderr.write('eDeploy: ' + msg + '\n')


def is_included(dict1, dict2):
    'Test if dict1 is included in dict2.'
    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True


def cmdb_filename(cfg_dir, name):
    'Return the cmdb filename.'
    return cfg_dir + name + '.cmdb'


def load_cmdb(cfg_dir, name):
    'Load the cmdb.'
    filename = cmdb_filename(cfg_dir, name)
    try:
        return eval(open(filename).read(-1))
    except IOError, xcpt:
        if xcpt.errno != errno.ENOENT:
            log("exception while processing CMDB %s" % str(xcpt))
        return None


def save_cmdb(cfg_dir, name, cmdb):
    'Save the cmdb.'
    filename = cmdb_filename(cfg_dir, name)
    try:
        pprint.pprint(cmdb, stream=open(filename, 'w'))
    except IOError, xcpt:
        log("exception while processing CMDB %s" % str(xcpt))


def update_cmdb(cmdb, var, pref, forced_find):
    '''Handle CMDB settings if present. CMDB is updated with var.
var is also augmented with the cmdb entry found.'''

    def update_entry(entry, cmdb, idx):
        'Update var using a cmdb entry and save the full cmdb on disk.'
        var.update(entry)
        var['used'] = 1
        cmdb[idx] = var

    #sys.stderr.write(str(cmdb))
    # First pass to lookup if the var is already in the database
    # and if this is the case, reuse the entry.
    idx = 0
    for entry in cmdb:
        if is_included(pref, entry):
            update_entry(entry, cmdb, idx)
            break
        idx += 1
    else:
        # not looking for $$ type matches
        if not forced_find:
            # Second pass, find a not used entry.
            idx = 0
            for entry in cmdb:
                if not 'used' in entry:
                    update_entry(entry, cmdb, idx)
                    break
                idx += 1
            else:
                log("No more entry in the CMDB, aborting.")
                return False
        else:
            log("No entry matched in the CMDB, aborting.")
            return False
    return True


def save_hw(items, name, hwdir):
    'Save hw items for inspection on the server.'
    try:
        filename = os.path.join(hwdir, name + '.hw')
        pprint.pprint(items, stream=open(filename, 'w'))
    except Exception, xcpt:
        log("exception while saving hw file: %s" % str(xcpt))


def register_pxemngr(sysvars):
    'Register the system in pxemngr.'
    macs = ' '.join(sysvars['serial'])
    cmd = 'pxemngr addsystem %s %s' % (sysvars['sysname'],
                                       macs)
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        log('%s -> %d / %s' % (cmd, status, output))
    else:
        log('added %s under pxemngr for MAC addresses %s'
            % (sysvars['sysname'], macs))


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
        sysvars['sysname'] += re.sub(r'\W+', '', sysvars['sysserial'])
    else:
        if matcher.match_multiple(hw_items,
                                  ('network', '$eth', 'serial', '$serial'),
                                  sysvars):
            sysvars['sysname'] += sysvars['serial'][0].replace(':', '-')
        else:
            log('unable to detect network macs')

    return sysvars


def main():
    '''CGI entry point.'''

    config = ConfigParser.ConfigParser()
    config.read('/etc/edeploy.conf')

    cfg_dir = config.get('SERVER', 'CONFIGDIR') + '/'

    # parse hw file given in argument or passed to cgi script
    if len(sys.argv) == 3 and sys.argv[1] == '-f':
        hw_file = open(sys.argv[2])
    else:
        cgitb.enable()

        form = cgi.FieldStorage()

        fileitem = form["file"]
        hw_file = fileitem.file

        print "Content-Type: text/x-python"     # HTML is following
        print                                   # blank line, end of headers

    hw_items = eval(hw_file.read(-1))

    # avoid concurrent accesses
    lock_filename = config.get('SERVER', 'LOCKFILE')
    lockfd = lock(lock_filename)

    def cleanup():
        'Remove lock.'
        unlock(lockfd, lock_filename)

    atexit.register(cleanup)

    filename_and_macs = generate_filename_and_macs(hw_items)
    save_hw(hw_items, filename_and_macs['sysname'], cfg_dir)

    def config_get(section, name, default):
        'Secured config getter.'
        try:
            return config.get(section, name)
        except ConfigParser.NoOptionError:
            return default

    use_pxemngr = (config_get('SERVER', 'USEPXEMNGR', False) == 'True')
    pxemngr_url = config_get('SERVER', 'PXEMNGRURL', None)
    metadata_url = config_get('SERVER', 'METADATAURL', None)

    if use_pxemngr:
        register_pxemngr(filename_and_macs)

    state_filename = cfg_dir + 'state'
    names = eval(open(state_filename).read(-1))

    idx = 0
    times = '*'
    name = None
    for name, times in names:
        if times == '*' or times > 0:
            specs = eval(open(cfg_dir + name + '.specs', 'r').read(-1))
            var = {}
            var2 = {}
            if matcher.match_all(hw_items, specs, var, var2):
                break
        idx += 1
    else:
        log('Unable to match requirements')
        log('Specs: %s' % repr(specs))
        log('Lines: %s' % repr(hw_items))
        sys.exit(1)

    forced = (var2 != {})

    if var2 == {}:
        var2 = var

    if times != '*':
        names[idx] = (name, times - 1)

    cmdb = load_cmdb(cfg_dir, name)
    if cmdb:
        if not update_cmdb(cmdb, var, var2, forced):
            sys.exit(1)
        save_cmdb(cfg_dir, name, cmdb)

    cfg = open(cfg_dir + name + '.configure').read(-1)

    sys.stdout.write('''#!/usr/bin/env python

import commands
import sys

import hpacucli
import ipmi
import time

def run(cmd):
    print '+ ' + cmd
    status, output = commands.getstatusoutput(cmd)
    print output
    if status != 0:
        print "Command '%s' failed" % cmd
        print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        print "!!! Configure script exited prematurely !!!"
        print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        sys.exit(status)

def set_role(role, version, disk):
    with open('/vars', 'w') as f:
        f.write("ROLE=%s\\nVERS=%s\\nDISK=%s\\n" % (role,
                                                    version,
                                                    disk))

var = ''')

    pprint.pprint(var)

    sys.stdout.write(cfg)

    if use_pxemngr:
        print '''
run('curl -s %slocalboot/')
''' % pxemngr_url

    if metadata_url:
        print '''
run('echo "METADATA_URL=%s" >> /vars')
''' % metadata_url

    pprint.pprint(names, stream=open(state_filename, 'w'))

if __name__ == "__main__":
    main()
