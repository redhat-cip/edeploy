#!/usr/bin/env python

#curl -i -F name=test -F file=@/tmp/hw.lst http://localhost/cgi-bin/upload.py

import cgi
import cgitb
import errno
import os
import pprint
import sys
import time
import ConfigParser

import matcher

def lock(filename):
    while True:
        try:
            fd = os.open(filename, os.O_CREAT|os.O_EXCL|os.O_RDWR)
            break;
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise 
            time.sleep(1)
    return fd

def unlock(fd, filename):
    if fd:
        os.close(fd)
        os.unlink(filename)

config = ConfigParser.ConfigParser()
config.read('/etc/edeploy.conf')

DIR = config.get('SERVER', 'CONFIGDIR') + '/'

cgitb.enable()

print "Content-Type: text/x-python"     # HTML is following
print                                   # blank line, end of headers

form = cgi.FieldStorage()

fileitem = form["file"]
l = eval(fileitem.file.read(-1))

lock_filename = config.get('SERVER', 'LOCKFILE')
lockfd = lock(lock_filename)

state_filename = DIR + 'state'
names = eval(open(state_filename).read(-1))

idx = 0
for name, times in names:
    if times == '*' or times > 0:
        specs = eval(open(DIR + name + '.specs', 'r').read(-1))
        var = {}
        if matcher.match_all(l, specs, var):
            break
    idx += 1
else:
    sys.stderr.write('eDeploy: Unable to match requirements\n')
    sys.stderr.write('eDeploy: Specs: %s\n' % repr(specs))
    sys.stderr.write('eDeploy: Lines: %s\n' % repr(l))
    sys.exit(1)

if times != '*':
    names[idx] = (name, times - 1)

# Handle CMDB settings if present
cmdb_filename = DIR + name + '.cmdb'
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

cfg = open(DIR + name + '.configure').read(-1)

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
    open('/role', 'w').write("ROLE=%s\\nVERS=%s\\nDISK=%s\\n" % (role, version, disk))

var = ''')

pprint.pprint(var)

sys.stdout.write(cfg)

pprint.pprint(names, stream=open(state_filename, 'w'))

unlock(lockfd, lock_filename)
