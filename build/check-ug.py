#!/usr/bin/env python

# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
#
# Author: Fabien Boucher <fabien.boucher@enovance.com>
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

""" eDeploy used to pre-define uid and gid for all users and groups
on a image built by eDeploy. This is done by the ids.tables mechanism.

In order to do that useradd/adduser/groupadd are wrapped by a python script
provided by eDeploy.

Most of the rpm pre-inst scripts adds users and groups but does not
trigger or even raise an error if useradd/adduser/groupadd fails. This
can lead in case of an error in the wrapper to some unexpected behaviors.

In order to improve and keep safe that process (wrapping) this script
is intended to be run at the end of an image creation to verify
that all users and groups expected by all rpm packages are really created
and that uid/gid are according to the ids.tables.
"""

import os
import grp
import pwd
import copy
import shlex
import subprocess

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

IDS = '/etc/ids.tables'
try:
    exec(open(IDS).read())
except IOError:
    pass


def log(msg, level='info'):
    if 'CHECK_UG_DEBUG' in os.environ:
        if level == 'debug':
            print("%s: %s" % (level.upper(), msg))
    if level != 'debug':
        print("%s: %s" % (level.upper(), msg))


def detect_commands(pkg, content):
    commands = []
    cont = False
    buff = ""
    for line in content.split('\n'):
        if (line.strip().startswith('useradd') or
           line.strip().startswith('adduser') or
           line.strip().startswith('groupadd')) and not cont:
            buff += line.strip()
        for cmd in ('useradd', 'adduser', 'groupadd'):
            if line.strip().find(cmd) > 0 and not cont:
                buff += line.strip()[line.strip().find(cmd):]
        if cont:
            buff += line.strip()
        if buff and line.strip().endswith('\\'):
            cont = True
            buff = buff[0:-1]
        else:
            cont = False
            if buff:
                for ma in ('||', '&>', '2>', '>/dev/null', '> /dev/null'):
                    if buff.find(ma) > 0:
                        buff = buff[:buff.find(ma)].strip()
                commands.append(buff)
            buff = ""
    if commands:
        log("Detected commands for package %s: %s" % (pkg, commands),
            level='debug')
    return commands


def parse_command(pkg, command):
    def get_index(array, key):
        try:
            return array.index(key)
        except ValueError:
            return None
    ret = {'typ': None, 'uid': None, 'gid': None, 'name': None}
    if command.startswith('useradd') or command.startswith('adduser'):
        ret['typ'] = 'useradd'
    if command.startswith('groupadd'):
        ret['typ'] = 'groupadd'
    args = shlex.split(command)
    args_opts = copy.deepcopy(ARGS_OPTS)
    if ret['typ'] == 'groupadd':
        # Unfortunatly the -f option is not consistent between
        # useradd and groupadd
        args_opts.remove('-f')
    name = None
    for ai in range(1, len(args)):
        if args[ai][0] != '-' and \
           (args[ai-1] not in args_opts or args[ai-1] == args[0]):
            name = args[ai]
            break
    if not name:
        raise KeyError('Unable to find the fullname user or group in %s' %
                       str(args))
    ret['name'] = name
    g_idx = get_index(args, '-g') or get_index(args, '--gid')
    u_idx = get_index(args, '-u') or get_index(args, '--uid')
    if g_idx:
        ret['gid'] = args[g_idx + 1]
    if u_idx:
        ret['uid'] = args[u_idx + 1]
    log("Expected by the package %s: %s" % (pkg, str(ret)), level='debug')
    return ret


def get_rpm_list():
    ret = subprocess.check_output('rpm -qa 2> /dev/null',
                                  shell=True).split('\n')
    if not ret[-1]:
        del ret[-1]
    return ret


def get_rpm_scripts(pkg):
    return subprocess.check_output('rpm -q --scripts %s 2> /dev/null' % pkg,
                                   shell=True)


def query_ids_table(desc):
    ret = {'typ': None, 'uid': None, 'gid': None, 'name': None}
    ret['typ'] = desc['typ']
    ret['name'] = desc['name']
    if desc['typ'] == 'useradd':
        try:
            ret['uid'] = uids[desc['name']][0]  # noqa
            ret['gid'] = uids[desc['name']][1]  # noqa
        except KeyError:
            log('Unable to find uid/gid in ids.tables for user %s' %
                desc['name'], level='warning')
    if desc['typ'] == 'groupadd':
        try:
            ret['gid'] = gids[desc['name']][0]  # noqa
        except KeyError:
            log('Unable to find gid in ids.tables for group %s' %
                desc['name'], level='warning')
    log("According to ids.tables: %s" % str(ret), level='debug')
    return ret


def validate_etc_passwd(real):
    ret = 0
    if real['typ'] == 'useradd':
        try:
            pwd.getpwnam(real['name'])
        except KeyError:
            log("Unable to find user %s in /etc/passwd" % real['name'],
                level='warning')
            return 1
        if str(pwd.getpwnam(real['name']).pw_uid) != str(real['uid']):
            log("UID for user %s (%s) does not correspond to the one in "
                "ids.tables (%s)" % (real['name'],
                                     pwd.getpwnam(real['name']).pw_uid,
                                     real['uid']), level='warning')
            ret = 1
        if str(pwd.getpwnam(real['name']).pw_gid) != str(real['gid']):
            log("GID for user %s (%s) does not correspond to the one in "
                "ids.tables (%s)" % (real['name'],
                                     pwd.getpwnam(real['name']).pw_gid,
                                     real['gid']), level='warning')
            ret = 1
    return ret


def validate_etc_group(real):
    ret = 0
    if real['typ'] == 'groupadd':
        try:
            grp.getgrnam(real['name'])
        except KeyError:
            log("Unable to find group %s in /etc/group" % real['name'],
                level='warning')
            return 1
        if str(grp.getgrnam(real['name']).gr_gid) != str(real['gid']):
            log("GID for group %s (%s) does not correspond to the one in "
                "ids.tables (%s)" % (real['name'],
                                     grp.getgrnam(real['name']).gr_gid,
                                     real['gid']), level='warning')
            ret = 1
    return ret


if __name__ == "__main__":
    import sys

    ret = 0
    log("Start check-ug ...")
    rpms = get_rpm_list()
    log("Found %s RPMs" % len(rpms))
    for rpm in rpms:
        content = get_rpm_scripts(rpm)
        commands = detect_commands(rpm, content)
        for command in commands:
            desc = parse_command(rpm, command)
            real = query_ids_table(desc)
            ret += validate_etc_passwd(real)
            ret += validate_etc_group(real)
    if ret != 0:
        sys.exit(1)
