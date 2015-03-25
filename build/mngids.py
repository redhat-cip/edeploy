#!/usr/bin/env python
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

'''
'''
from __future__ import print_function

import os
import copy
import pprint
import subprocess
import sys

_DEBUG = os.getenv('MNGIDS_DEBUG', None) is not None

# adduser and addgroup option taking an argument
ARGS_OPTS = ['-g', '--gid',
             '-K', '--key',
             '-p', '--password',
             '-R', '--root',
             '-b', '--base-dir',
             '-c', '--comment',
             '-d', '--home-dir',
             '-e', '--expiredate',
             '-f', '--inactive',
             '-G', '--groups',
             '-k', '--skel',
             '-s', '--shell',
             '-u', '--uid',
             '-Z', '--selinux-user']

def debug(output):
    if _DEBUG:
        sys.stderr.write(output + '\n')


def parse(content, assoc, is_group=False):
    for line in content.split('\n'):
        line = line.split('#', 1)[0]
        fields = line.strip().split(':')
        if len(fields) >= 4:
            if is_group:
                val = (fields[2], '')
            else:
                val = (fields[2], fields[3])
            if fields[0] in assoc:
                if assoc[fields[0]] != val:
                    raise KeyError('%s already exist with %s instead of %s' %
                                   (fields[0], assoc[fields[0]], val))
            assoc[fields[0]] = val
    return assoc


def get_index(array, key, default=None):
    try:
        return array.index(key)
    except ValueError:
        return default

def call_addgroup(name):
    subprocess.call(['groupadd', name])


def parse_cmdline(args, uids, gids, first=100, last=999, last_user=29999):
    args0 = args[0].split('/')[-1]

    def insert(ids, key, idx, opt):
        index = get_index(args, opt) or get_index(args, '-' + opt[2])

        # to match a group/user name
        if key in ids:
            val = ids[key][idx]
        # to match a group/user ID
        elif key in [x for v in ids.values() for x in v]:
            val = key
        else:
            # we try to create a user/group not in ids.tables, we fail.
            raise KeyError('mngids.py: %s not found (%s) in %s' %
                           (key, opt, str(ids.values())))

        debug('mngids.py: found %s at %s for val[%s]=%s' %
              (opt, str(index), key, val))

        if index:
            args[index + 1] = val
        else:
            args.insert(1, val)
            args.insert(1, opt)

    # support to have the user or group name at all position
    args_opts = copy.deepcopy(ARGS_OPTS)
    if args0 == 'groupadd':
        # Unfortunatly the -f option is not consistent between useradd and groupadd
        args_opts.remove('-f')
    arg1 = None
    for ai in range(1, len(args)):
        if args[ai][0] != '-' and (args[ai-1] not in args_opts or args[ai-1] == args[0]):
            arg1 = args[ai]
            break
    if not arg1:
        raise KeyError('Unable to find the fullname user or group in %s' % str(args))
    if args0 == 'adduser' or args0 == 'useradd':
        # lookup group argument
        idx = get_index(args, '-g') or get_index(args, '--gid')

        if idx:
            insert(gids, args[idx + 1], 0, '--gid')
        else:
            # useradd can be called without a -g or --gid argument and in
            # that case a group is created with the same name as the username by the
            # useradd command. So if we want to specify a specific gid (according to
            # ids.tables) we need to create the group here. Plus this mimic
            # the useradd command.
            call_addgroup(arg1)
            insert(uids, arg1, 1, '--gid')
        insert(uids, arg1, 0, '--uid')
    elif args0 == 'addgroup' or args0 == 'groupadd':
        insert(gids, arg1, 0, '--gid')

    args[0] = args[0] + '.real'

    return args


def main():
    uids = {}
    gids = {}

    debug('ORIG %s' % str(sys.argv))

    IDS = '/etc/ids.tables'

    try:
        exec(open(IDS).read())
    except IOError:
        pass
    parse(open('/etc/passwd').read(), uids)
    parse(open('/etc/group').read(), gids, True)
    parse_cmdline(sys.argv, uids, gids)
    #
    debug('REWRITTEN %s' % str(sys.argv))
    ret = subprocess.call(sys.argv)
    if ret != 0:
        sys.exit(ret)
    #
    parse(open('/etc/passwd').read(), uids)
    parse(open('/etc/group').read(), gids, True)
    #
    out = open(IDS, 'w')
    print('uids = ', file=out, end='')
    pprint.pprint(uids, out)
    print('gids = ', file=out, end='')
    pprint.pprint(gids, out)
    out.close()

if __name__ == "__main__":
    if sys.argv[0].split('/')[-1] == 'mngids.py':
        uids = {}
        gids = {}

        try:
            exec(open(sys.argv[3]).read())
        except IOError:
            pass
        parse(open(sys.argv[1]).read(), uids)
        parse(open(sys.argv[2]).read(), gids, True)

        out = open(sys.argv[3], 'w')
        print('uids = ', file=out, end='')
        pprint.pprint(uids, out)
        print('gids = ', file=out, end='')
        pprint.pprint(gids, out)
        out.close()
    else:
        main()

# mngids.py ends here
