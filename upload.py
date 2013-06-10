#!/usr/bin/env python

'''CGI script part of the eDeploy system.

It receives on its file form a file containing a Python dictionnary
with the hardware detected on the remote host. In return, it sends
a Python configuration script corresponding to the matched config.

If nothing matches, nothing is returned. So the system can abort
its configuration.

On the to be configured host, it is usally called like that:

$ curl -i -F name=test -F file=@/tmp/hw.lst http://localhost/cgi-bin/upload.py
'''

import ConfigParser
import cgi
import cgitb
import errno
import os
import pprint
import sys
import time

import matcher


def lock(filename):
    '''Lock a file and return a file descriptor. Need to call unlock to release
the lock.'''
    while True:
        try:
            lock_fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except OSError, xcpt:
            if xcpt.errno != errno.EEXIST:
                raise
            time.sleep(1)
    return lock_fd


def unlock(lock_fd, filename):
    '''Called after the lock function to release a lock.'''
    if lock_fd:
        os.close(lock_fd)
        os.unlink(filename)


def is_included(dict1, dict2):
    'Test if dict1 is included in dict2.'
    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True


def update_cmdb(name, cfg_dir, var):
    '''Handle CMDB settings if present. CMDB is updated with var.
var is also augmented with the cmdb entry found.'''
    cmdb_filename = cfg_dir + name + '.cmdb'

    def update_entry(entry, cmdb, idx):
        'Update var using a cmdb entry and save the full cmdb on disk.'
        var.update(entry)
        var['used'] = 1
        cmdb[idx] = var
        pprint.pprint(cmdb, stream=open(cmdb_filename, 'w'))

    try:
        cmdb = eval(open(cmdb_filename).read(-1))
        # First pass to lookup if the var is already in the database
        # and if this is the case, reuse the entry.
        idx = 0
        for entry in cmdb:
            if is_included(var, entry):
                update_entry(entry, cmdb, idx)
                break
            idx += 1
        else:
            # Second pass, find a not used entry.
            idx = 0
            for entry in cmdb:
                if not 'used' in entry:
                    update_entry(entry, cmdb, idx)
                    break
                idx += 1
            else:
                sys.stderr.write("eDeploy: No more entry in the CMDB,"
                                 " aborting.\n")
                sys.exit(1)
    except IOError:
        pass


def main():
    '''CGI entry point.'''

    config = ConfigParser.ConfigParser()
    config.read('/etc/edeploy.conf')

    cfg_dir = config.get('SERVER', 'CONFIGDIR') + '/'

    cgitb.enable()

    print "Content-Type: text/x-python"     # HTML is following
    print                                   # blank line, end of headers

    form = cgi.FieldStorage()

    fileitem = form["file"]
    hw_items = eval(fileitem.file.read(-1))

    lock_filename = config.get('SERVER', 'LOCKFILE')
    lockfd = lock(lock_filename)

    state_filename = cfg_dir + 'state'
    names = eval(open(state_filename).read(-1))

    idx = 0
    times = '*'
    name = None
    for name, times in names:
        if times == '*' or times > 0:
            specs = eval(open(cfg_dir + name + '.specs', 'r').read(-1))
            var = {}
            if matcher.match_all(hw_items, specs, var):
                break
        idx += 1
    else:
        sys.stderr.write('eDeploy: Unable to match requirements\n')
        sys.stderr.write('eDeploy: Specs: %s\n' % repr(specs))
        sys.stderr.write('eDeploy: Lines: %s\n' % repr(hw_items))
        sys.exit(1)

    if times != '*':
        names[idx] = (name, times - 1)

    update_cmdb(name, cfg_dir, var)

    cfg = open(cfg_dir + name + '.configure').read(-1)

    sys.stdout.write('''#!/usr/bin/env python

import sys
import commands

def run(cmd):
    print '+ ' + cmd
    status, output = commands.getstatusoutput(cmd)
    print output
    if status != 0:
        sys.exit(status)

def set_role(role, version, disk):
    open('/role', 'w').write("ROLE=%s\\nVERS=%s\\nDISK=%s\\n" % (role,
                                                                 version,
                                                                 disk))

var = ''')

    pprint.pprint(var)

    sys.stdout.write(cfg)

    pprint.pprint(names, stream=open(state_filename, 'w'))

    unlock(lockfd, lock_filename)

if __name__ == "__main__":
    main()
