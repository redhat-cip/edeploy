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

import fnmatch
import os
import subprocess
import unittest


def filter_output(output):
    res = '\n'
    lines = output.split('\n')
    for idx in range(len(lines) // 2):
        desc = lines[2 * idx]
        file_part = lines[2 * idx + 1][2:].replace(' L', '')
        res = res + '%s: %s\n' % (file_part, desc)
    return res


class TestBash8(unittest.TestCase):

    def check(self, fname):
        try:
            subprocess.check_output(('bash8', fname))
            self.assertTrue(True)
        except subprocess.CalledProcessError as e:
            self.assertTrue(False, filter_output(e.output))

for fname in fnmatch.filter(os.listdir('.'), '*.install') + \
        ['common', 'distributions', 'functions', 'packages', 'repositories']:
    def ch(fname, mname):
        def test_aux(self):
            return self.check(fname)
        test_aux.__name__ = mname
        return test_aux
    mname = "test_%s" % fname.replace('.', '_')
    setattr(TestBash8, mname, ch(fname, mname))

if __name__ == "__main__":
    unittest.main()

# test_bash8.py ends here
