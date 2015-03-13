#!/usr/bin/env python
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
#
# Authors: Frederic Lepied <frederic.lepied@enovance.com>
#          Emilien Macchi <emilien.macchi@enovance.com>
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

""" Generate pre/post scripts after having build a role.
Usage:
    generate_metadatas.py <chrootdir>

This will generate 'pre' and 'post' files.
"""


import subprocess
import sys


def filter_file(name):
    if name.startswith('var/lib/yum') or \
       name.startswith('var/log') or \
       name.startswith('usr/share/man'):
        return True
    else:
        return False


def rpmqa(dir_):
    print(['sudo', 'chroot', dir_, 'rpm', '-qa'])
    output = chroot(dir_, 'rpm -qa')
    list_ = output.split('\n')
    return list_


def chroot(dir_, cmd):
    return subprocess.check_output(['sudo', 'chroot', dir_] + cmd.split(' '))


def has_scriptlet(pkg, dir_):
    return chroot(dir_, 'rpm -q --scripts ' + pkg) != ''


def gen_scriptlet(comment, cmd):
    scriptlet_format = '''# %s
(
# put the scriptlet in upgrade mode by passing 2 (package count is 2
# during upgrades) as the first argument.
set 2

%s
)

'''
    return scriptlet_format % (comment, cmd)


def gen_scripts(pkgs, dir_):
    header = '''#!/bin/sh

# abort on error
set -e

# echo commands
set -x

'''
    ldconfig_header = '''# for installed libraries

/sbin/ldconfig

'''
    post = pre = ''
    ldconfig = False
    for pkg in pkgs:
        if pkg:
            preinst_prog = chroot(dir_, 'rpm -q --qf %{PREINPROG} ' + pkg)
            preinst = chroot(dir_, 'rpm -q --qf %{PREIN} ' + pkg)
            postinst_prog = chroot(dir_, 'rpm -q --qf %{POSTINPROG} ' + pkg)
            postinst = chroot(dir_, 'rpm -q --qf %{POSTIN} ' + pkg)
            if preinst_prog == '/bin/sh':
                pre = pre + gen_scriptlet(pkg, preinst)
            elif preinst_prog != '(none)':
                print('PREPROG', pkg, preinst_prog)
                print('PRE', pkg, preinst)
            if postinst_prog == '/bin/sh':
                post = post + gen_scriptlet(pkg, postinst)
            elif postinst_prog != '(none)':
                if postinst_prog == '/sbin/ldconfig' and postinst == '(none)':
                    ldconfig = True
                elif (postinst_prog != '/sbin/ldconfig' and
                      postinst == '(none)'):
                    post = post + gen_scriptlet(pkg, postinst_prog)
                else:
                    print('POSTPROG', pkg, postinst_prog)
                    print('POST', pkg, postinst)
    if ldconfig:
        post = ldconfig_header + post
    return header + pre, header + post


def main():
    res = rpmqa(sys.argv[1])
    pre, post = gen_scripts(res, sys.argv[1])
    open('pre', 'w').write(pre)
    open('post', 'w').write(post)

main()

# generate_metadatas.py ends here
