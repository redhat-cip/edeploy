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

import pprint
import subprocess
import sys


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


def parse_cmdline(args, uids, gids):
    args0 = args[0].split('/')[-1]

    def insert(ids, key, idx, opt):
        if not key in ids:
            print('%s not found in %s' % (key, ids))
            return

        try:
            index = args.index(opt)
        except ValueError:
            try:
                index = args.index('-' + opt[2])
            except ValueError:
                index = None
        if index:
            args[index + 1] = ids[key][idx]
        else:
            if opt not in args and '-' + opt[2] not in args:
                try:
                    args.insert(1, ids[key][idx])
                    args.insert(1, opt)
                except KeyError:
                    pass

    if args0 == 'adduser' or args0 == 'useradd':
        insert(uids, args[-1], 1, '--gid')
        insert(uids, args[-1], 0, '--uid')
    elif args0 == 'addgroup' or args0 == 'groupadd':
        insert(gids, args[-1], 0, '--gid')
    args[0] = args[0] + '.real'
    return args


def main():
    uids = {}
    gids = {}

    print('ORIG', sys.argv)

    IDS = '/root/ids.tables'

    try:
        exec(open(IDS).read())
    except IOError:
        pass
    parse(open('/etc/passwd').read(), uids)
    parse(open('/etc/group').read(), gids, True)
    parse_cmdline(sys.argv, uids, gids)
    #
    print(sys.argv)
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
