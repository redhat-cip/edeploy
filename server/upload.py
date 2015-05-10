#!/usr/bin/env python
#
# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
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

On the to be configured host, it is usually called like that:

$ curl -i -F name=test -F file=@/hw.lst http://localhost/cgi-bin/upload.py
'''

import atexit
import ConfigParser
import cgi
import cgitb
import commands
from datetime import datetime
import errno
import json
import os
import pprint
import sys
import time
import traceback

from hardware import matcher
from hardware import state


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


def log(msg, prefix='eDeploy', module='upload.py'):
    'Error Logging.'
    timestamp = datetime.strftime(datetime.now(), '%a %b %d %H:%M:%S.%f %Y')
    sys.stderr.write('[%s] [%s] %s(%d): %s\n' % (timestamp,
                                                 prefix,
                                                 module,
                                                 os.getpid(),
                                                 msg))


def save_hw(items, name, hwdir):
    'Save hw items for inspection on the server.'
    try:
        filename = os.path.join(hwdir, name + '.hw')
        pprint.pprint(items, stream=open(filename, 'w'))
    except Exception, xcpt:
        log("exception while saving hw file: %s" % str(xcpt))


def register_pxemngr(sysvars):
    'Register the system in pxemngr.'
    # only use Ethernet mac addresses with pxemngr
    macs = ' '.join(filter(lambda x: len(x) == 17, sysvars['serial']))
    cmd = 'pxemngr addsystem %s %s' % (sysvars['sysname'],
                                       macs)
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        log('%s -> %d / %s' % (cmd, status, output))
    else:
        log('added %s under pxemngr for MAC addresses %s'
            % (sysvars['sysname'], macs))


def warning_error(error):
    '''Report a shell script with the error message and log
    the message on stderr.'''
    print('''#!/bin/sh

cat <<EOF
%s
EOF

exit 1
''' % error)
    log('Aborting: ' + error)
    if sys.exc_info()[0] is not None:
        traceback.print_exc(file=sys.stderr)


def fatal_error(error):
    '''Report a shell script with the error message and log
    the message on stderr.'''
    warning_error(error)
    sys.exit(1)


def main():
    '''CGI entry point.'''

    config = ConfigParser.ConfigParser()
    config.read('/etc/edeploy.conf')

    def config_get(section, name, default):
        'Secured config getter.'
        try:
            return config.get(section, name)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            return default

    failure_role = None
    section = 'SERVER'

    # parse hw file given in argument or passed to cgi script
    if len(sys.argv) >= 3 and sys.argv[1] == '-f':
        hw_file = open(sys.argv[2])
        if len(sys.argv) >= 5 and sys.argv[3] == '-F':
            failure_role = sys.argv[4]

        cfg_dir = os.path.normpath(config_get(
            'SERVER', 'CONFIGDIR',
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         '..',
                         'config'))) + '/'

        hw_dir = os.path.normpath(config_get(
            'SERVER', 'HWDIR', cfg_dir)) + '/'

    else:
        cgitb.enable()

        form = cgi.FieldStorage()

        log('Called from %s' % os.getenv('REMOTE_ADDR', '<no address>'))

        print "Content-Type: text/x-python"     # HTML is following
        print                                   # blank line, end of headers

        # Log form fields
        for key in form:
            if key == 'file':
                log('form[%s]: %d bytes' % (key, len(form.getvalue(key))))
            else:
                log('form[%s]: "%s"' % (key, form.getvalue(key)))

        section = form.getvalue('section', 'SERVER')

        cfg_dir = os.path.normpath(config_get(
            section, 'CONFIGDIR',
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         '..',
                         'config'))) + '/'

        # If the filename ends with a .log, we need to process it as a log file
        if ('file' in form) and (form['file'].filename.endswith('.log.gz')):
            logitem = form['file']
            logfile = logitem.file
            try:
                # Let's save the file in LOGDIR directory
                log_dir = os.path.normpath(config_get(section,
                                                      'LOGDIR',
                                                      cfg_dir)) + '/'
                filename = os.path.join(log_dir,
                                        os.path.basename(logitem.filename))
                if os.path.exists(filename):
                    backupname = '%s.%s.log.gz' % \
                                 (filename[:-7],
                                  time.strftime('%Y%m%d%H%M%S',
                                                time.gmtime(
                                                    os.path.getmtime(
                                                        filename))))
                    log('Renaming log file %s to %s' % (filename, backupname))
                    os.rename(filename, backupname)
                output_file = open(filename, 'w')
                output_file.write(logfile.read(-1))
                output_file.close()
            except Exception, xcpt:
                # If we fails at saving, let's exit
                fatal_error("exception while saving log file: %s" % str(xcpt))
                sys.exit(1)
            # If the succeed at saving log file, let's also exit
            # In fact we have nothing more to do once its saved.
            log('Log file %s saved' % logitem.filename)
            sys.exit(0)

        if 'file' not in form:
            fatal_error('No file passed to the CGI')

        fileitem = form['file']
        hw_file = fileitem.file

        if form.getvalue('failure'):
            failure_role = form.getvalue('failure')

        hw_dir = os.path.normpath(config_get(
            section, 'HWDIR', cfg_dir)) + '/'

    try:
        json_hw_items = json.loads(hw_file.read(-1))
    except Exception as excpt:
        fatal_error("'Invalid hardware file: %s'" % str(excpt))

    def encode(elt):
        'Encode unicode strings as strings else return the object'
        try:
            return elt.encode('ascii', 'ignore')
        except AttributeError:
            return elt

    hw_items = []
    for info in json_hw_items:
        hw_items.append(tuple(map(encode, info)))

    # avoid concurrent accesses
    lock_filename = config_get(section, 'LOCKFILE',
                               '/var/run/httpd/edeploy.lock')
    state_obj = state.State(lockname=lock_filename)
    state_obj.load(cfg_dir)

    def cleanup():
        'Remove lock.'
        state_obj.unlock()

    atexit.register(cleanup)

    filename_and_macs = matcher.generate_filename_and_macs(hw_items)
    save_hw(hw_items, filename_and_macs['sysname'], hw_dir)

    use_pxemngr = (config_get(section, 'USEPXEMNGR', False) == 'True')
    pxemngr_url = config_get(section, 'PXEMNGRURL', None)
    metadata_url = config_get(section, 'METADATAURL', None)

    if use_pxemngr:
        register_pxemngr(filename_and_macs)

    if failure_role:
        if state_obj.failed_profile(failure_role):
            state_obj.save()
            sys.exit(0)

    try:
        name, var = state_obj.find_match(hw_items)
        var['edeploy-profile'] = name
    except Exception as excpt:
        fatal_error(str(excpt))

    sys.stdout.write('''#!/usr/bin/env python
#EDEPLOY_PROFILE = %s
''' % name)

    cfg = open(cfg_dir + name + '.configure').read(-1)

    sys.stdout.write('''
import commands
import os
import sys
import time

from hardware import hpacucli
from hardware import ipmi

def run(cmd):
    sys.stderr.write('+ ' + cmd + '\\n')
    status, output = commands.getstatusoutput(cmd + ' </dev/null')
    sys.stderr.write(output + '\\n')
    if status != 0:
        sys.stderr.write("Command '%s' failed\\n" % cmd)
        sys.stderr.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\\n")
        sys.stderr.write("!!! Configure script exited prematurely !!!\\n")
        sys.stderr.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\\n")
        sys.exit(status)

def set_role(role, version, disk):
    with open('/vars', 'a') as f:
        f.write("ROLE=%s\\nVERS=%s\\nDISK=%s\\n" % (role,
                                                    version,
                                                    disk))
        f.write("PROFILE=%s\\n" % var['edeploy-profile'])

def config(name, mode='w', basedir='/post_rsync', fmod=0644, uid=0, gid=0):
    path = basedir + name
    dir_ = '/'.join(path.split('/')[:-1])
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    f = open(path, mode)
    os.fchmod(f.fileno(), fmod)
    os.fchown(f.fileno(), uid, gid)
    return f

def inject_facts(vars, basedir='/post_rsync', prefix='hw_'):
    dir_ = os.path.join(basedir, 'etc', 'facter', 'facts.d')
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    with open(os.path.join(dir_, 'edeploy.yaml'), 'w') as f:
        f.write('---\\n')
        for key in vars:
            f.write('%s%s: %s\\n' % (prefix, key, vars[key]))

var = ''')

    pprint.pprint(var)

    sys.stdout.write(cfg)

    if use_pxemngr and pxemngr_url:
        log("Adding pxemngr url to configure script: %s" % pxemngr_url)
        print '''
run('echo "PXEMNGR_URL=%s" >> /vars')
''' % pxemngr_url

    if metadata_url:
        log("Adding metadata url to configure script: %s" % metadata_url)
        print '''
run('echo "METADATA_URL=%s" >> /vars')
''' % metadata_url

    log('Sending configure script')
    state_obj.save()

if __name__ == "__main__":
    try:
        main()
    except Exception, err:
        fatal_error(str(err))
