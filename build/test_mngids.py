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

import unittest

import mngids


class TestMngids(unittest.TestCase):

    def test_parse(self):
        content = 'root:x:0:0:root:/root:/bin/bash'
        arr = {}
        mngids.parse(content, arr)
        self.assertEquals(arr['root'], ('0', '0'))

    def test_parse_group(self):
        arr = {}
        mngids.parse(GROUP, arr, True)
        self.assertEquals(arr['root'], ('0', ''))

    def test_duplicate(self):
        content = 'root:x:0:0:root:/root:/bin/bash'
        content2 = 'root:x:1:0:root:/root:/bin/bash'
        arr = {}
        mngids.parse(content, arr)
        with self.assertRaises(KeyError):
            mngids.parse(content2, arr)

    def test_comment(self):
        content = '#root:x:0:0:root:/root:/bin/bash'
        arr = {}
        mngids.parse(content, arr)
        self.assertEquals(arr, {})

    def test_parsecmdline(self):
        cmd = 'adduser root'.split(' ')
        content = 'root:x:0:0:root:/root:/bin/bash'
        uids = {}
        mngids.parse(content, uids)
        orig = mngids.call_addgroup
        mngids.call_addgroup = lambda x: x
        mngids.parse_cmdline(cmd, uids, {})
        mngids.call_addgroup = orig
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '0')

    def test_parsecmdline_group(self):
        cmd = 'adduser --gid nogroup root'.split(' ')
        passwd = 'root:x:0:1:root:/root:/bin/bash'
        group = 'nogroup:x:65534:'
        uids = {}
        gids = {}
        mngids.parse(passwd, uids)
        mngids.parse(group, gids, True)
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '0')
        self.assertEquals(cmd[3], '--gid')
        self.assertEquals(cmd[4], '65534')

    def test_parsecmdline_addgroup(self):
        cmd = 'addgroup root'.split(' ')
        content = 'root:x:1:'
        gids = {}
        mngids.parse(content, gids)
        mngids.parse_cmdline(cmd, {}, gids)
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1')

    def test_parsecmdline_addgroup_path(self):
        cmd = './addgroup root'.split(' ')
        content = 'root:x:1:'
        gids = {}
        mngids.parse(content, gids, True)
        mngids.parse_cmdline(cmd, {}, gids)
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1')

    def test_parsecmdline_addgroup_noaction(self):
        cmd = 'addgroup --gid 2 root'.split(' ')
        content = 'root:x:1:'
        gids = {}
        mngids.parse(content, gids, True)
        l = len(cmd)
        mngids.parse_cmdline(cmd, {}, gids)
        self.assertEquals(len(cmd), l)
        self.assertEquals(cmd[2], '1')

    def test_parsecmdline_noaction(self):
        cmd = 'adduser --gid root root'.split(' ')
        l = len(cmd)
        passwd = 'root:x:0:1:root:/root:/bin/bash'
        group = 'root:x:1:'
        uids = {}
        gids = {}
        mngids.parse(passwd, uids)
        mngids.parse(group, gids, True)
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '0')
        self.assertEquals(cmd[4], '1')
        self.assertEquals(len(cmd), l + 2)

    def test_parsecmdline_noaction1(self):
        cmd = 'adduser --uid 2 root'.split(' ')
        l = len(cmd)
        content = 'root:x:0:1:root:/root:/bin/bash'
        uids = {}
        mngids.parse(content, uids)
        orig = mngids.call_addgroup
        mngids.call_addgroup = lambda x: x
        mngids.parse_cmdline(cmd, uids, {})
        mngids.call_addgroup = orig
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1')
        self.assertEquals(cmd[4], '0')
        self.assertEquals(len(cmd), l + 2)

    def test_parsecmdline_addgroup_non_exist(self):
        cmd = 'addgroup root'.split(' ')
        content = 'user:x:1000:'
        gids = {}
        mngids.parse(content, gids)
        with self.assertRaises(KeyError):
            mngids.parse_cmdline(cmd, {}, gids)

    def test_parsecmdline_addgroup_without_name(self):
        cmd = 'addgroup -g 1000 -b /root'.split(' ')
        content = 'root:x:1:'
        gids = {}
        mngids.parse(content, gids)
        with self.assertRaises(KeyError):
            mngids.parse_cmdline(cmd, {}, gids)

    def test_parsecmdline_addgroup_with_missing_arg_value(self):
        cmd = 'groupadd --gid root'.split(' ')
        content = 'root:x:1:'
        gids = {}
        mngids.parse(content, gids)
        with self.assertRaises(KeyError):
            mngids.parse_cmdline(cmd, {}, gids)

    def test_parsecmdline_find_gu_name(self):
        # Be sure parse_cmdline is able to find username or groupname
        passwd = 'jenkins:x:1000:1000::/home/jenkins:/bin/bash'
        group = 'cloud-users:x:1000:'
        uids = {}
        gids = {}
        mngids.parse(passwd, uids)
        mngids.parse(group, gids, True)

        cmd = ['useradd', 'jenkins', '--shell', '/bin/bash',
               '--gid', 'cloud-users',
               '--comment', 'eNovance Jenkins User', '-m']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '1000')
        self.assertEquals(cmd[7], '1000')

        cmd = ['useradd', '--shell', '/bin/bash',
               '--gid', 'cloud-users',
               '--comment', 'eNovance Jenkins User', '-m', 'jenkins']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '1000')
        self.assertEquals(cmd[6], '1000')

        cmd = ['useradd', '--shell', '/bin/bash',
               '--gid', 'cloud-users', 'jenkins',
               '--comment', 'eNovance Jenkins User', '-m']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '1000')
        self.assertEquals(cmd[6], '1000')

        cmd = ['groupadd', 'cloud-users']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1000')

        # 1010 is replaced by what we have in gids (usually provided in ids.tables
        cmd = ['groupadd', '--gid', '1010', 'cloud-users', '-o']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1000')

        cmd = ['groupadd', '--gid', '1010', '-f', 'cloud-users', '-o']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1000')

        cmd = ['useradd', '--shell', '/bin/bash',
               '--gid', 'cloud-users', '-f', '10', 'jenkins',
               '--comment', 'eNovance Jenkins User', '-m']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '1000')
        self.assertEquals(cmd[6], '1000')

    def test_calls(self):
        passwd = 'jenkins:x:1000:1000::/home/jenkins:/bin/bash'
        group = 'jenkins:x:1000:'
        uids = {'john': ('1001', '1001')}
        gids = {'john': ('1001', '')}
        mngids.parse(passwd, uids)
        mngids.parse(group, gids, True)

        cmd = ['useradd', 'john']
        orig = mngids.call_addgroup
        mngids.call_addgroup = lambda x: x
        mngids.parse_cmdline(cmd, uids, gids)
        mngids.call_addgroup = orig
        self.assertEquals(cmd[1], '--uid')
        self.assertEquals(cmd[2], '1001')

        cmd = ['useradd', 'john', '-u', '1001']
        orig = mngids.call_addgroup
        mngids.call_addgroup = lambda x: x
        mngids.parse_cmdline(cmd, uids, gids)
        mngids.call_addgroup = orig
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1001')
        self.assertEquals(cmd[4], '-u')
        self.assertEquals(cmd[5], '1001')

        cmd = ['useradd', 'john', '-u', '1001', '-g', '1001']
        mngids.parse_cmdline(cmd, uids, gids)
        self.assertEquals(cmd[2], '-u')
        self.assertEquals(cmd[3], '1001')
        self.assertEquals(cmd[4], '-g')
        self.assertEquals(cmd[5], '1001')

        cmd = ['useradd', 'john', '-u', '1001', '-g', '1002']
        with self.assertRaises(KeyError):
            # KeyError: "mngids.py: 1002 not found (--gid) in [('1000', ''), ('1001', '')]"
            mngids.parse_cmdline(cmd, uids, gids)

        uids = {'john': ('1001', '1002')}
        gids = {'john': ('1002', '')}
        mngids.parse(passwd, uids)
        mngids.parse(group, gids, True)
        cmd = ['useradd', 'john', '-u', '1001']
        orig = mngids.call_addgroup
        mngids.call_addgroup = lambda x: x
        mngids.parse_cmdline(cmd, uids, gids)
        mngids.call_addgroup = orig
        self.assertEquals(cmd[1], '--gid')
        self.assertEquals(cmd[2], '1002')
        self.assertEquals(cmd[4], '-u')
        self.assertEquals(cmd[5], '1001')


GROUP = '''root:x:0:
daemon:x:1:
bin:x:2:
sys:x:3:
adm:x:4:ubuntu,syslog
tty:x:5:
disk:x:6:
lp:x:7:
mail:x:8:
news:x:9:
uucp:x:10:
man:x:12:
proxy:x:13:
kmem:x:15:
dialout:x:20:ubuntu
fax:x:21:
voice:x:22:
cdrom:x:24:ubuntu
floppy:x:25:ubuntu
tape:x:26:
sudo:x:27:ubuntu
audio:x:29:pulse,ubuntu
dip:x:30:ubuntu
www-data:x:33:
backup:x:34:
operator:x:37:
list:x:38:
irc:x:39:
src:x:40:
gnats:x:41:
shadow:x:42:
utmp:x:43:
video:x:44:ubuntu
sasl:x:45:
plugdev:x:46:ubuntu
staff:x:50:
games:x:60:
users:x:100:
nogroup:x:65534:
libuuid:x:101:
crontab:x:102:
syslog:x:103:
fuse:x:104:
messagebus:x:105:
avahi-autoipd:x:106:
ssl-cert:x:107:
lpadmin:x:108:
netdev:x:109:ubuntu
whoopsie:x:110:
mlocate:x:111:
ssh:x:112:
utempter:x:113:
rtkit:x:114:
bluetooth:x:115:
lightdm:x:116:
nopasswdlogin:x:117:
avahi:x:118:
scanner:x:119:saned
colord:x:120:
pulse:x:121:
pulse-access:x:122:
saned:x:123:
fred:x:1000:
sambashare:x:124:
kvm:x:125:
redis:x:126:
lxc-dnsmasq:x:127:
puppet:x:128:
vboxusers:x:129:
mongodb:x:130:mongodb
stapdev:x:131:
stapusr:x:132:
stapsys:x:133:
libvirtd:x:134:ubuntu
uml-net:x:135:
ubuntu:x:1001:
'''

if __name__ == "__main__":
    unittest.main()

# test_mngids.py ends here
