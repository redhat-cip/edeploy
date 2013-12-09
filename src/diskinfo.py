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

from commands import getoutput as cmd
import os


def sizeingb(size):
    return (size * 512) / (1000 * 1000 * 1000)


def disksize(name):
    size = open('/sys/block/' + name + '/size').read(-1)
    return sizeingb(long(size))


def disknames():
    return [name for name in os.listdir('/sys/block')
            if name[1] == 'd' and name[0] in 'shv']


def parse_hdparm_output(output):
    res = output.split(' = ')
    if len(res) != 2:
        return 0.0
    try:
        mbsec = res[1].split(' ')[-2]
        return float(mbsec)
    except (ValueError, KeyError):
        return 0.0


def diskperfs(names):
    return dict((name, parse_hdparm_output(cmd('hdparm -t /dev/%s' % name)))
                for name in names)


def disksizes(names):
    return dict((name, disksize(name)) for name in names)


def _main():
    names = disknames()
    sizes = disksizes(names)
    names = [name for name, size in sizes.items() if size > 0]
    perfs = diskperfs(names)
    for name in names:
        print '%s %d GB (%.2f MB/s)' % (name, sizes[name], perfs[name])

if __name__ == "__main__":
    _main()
