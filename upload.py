#!/usr/bin/env python

'''CGI script part of the eDeploy system.

It receives on its file form a file containing a Python dictionnary
with the hardware detected on the remote host. In return, it sends
a Python configuration script corresponding to the matched config.

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
        except OSError as xcpt:
            if xcpt.errno != errno.EEXIST:
                raise
            time.sleep(1)
    return lock_fd


def unlock(lock_fd, filename):
    '''Called after the lock function to release a lock.'''
    if lock_fd:
        os.close(lock_fd)
        os.unlink(filename)


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

    # Handle CMDB settings if present
    cmdb_filename = cfg_dir + name + '.cmdb'
    try:
        cmdb = eval(open(cmdb_filename).read(-1))
        idx = 0
        for entry in cmdb:
            if not 'used' in entry:
                var.update(entry)
                var['used'] = 1
                cmdb[idx] = var
                pprint.pprint(cmdb, stream=open(cmdb_filename, 'w'))
                break
            idx += 1
        else:
            sys.stderr.write("eDeploy: No more entry in the CMDB, aborting.\n")
            sys.exit(1)
    except IOError:
        cmdb = None

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
