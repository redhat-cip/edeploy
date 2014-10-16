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

import unittest

import diskinfo


class TestDiskinfo(unittest.TestCase):

    def test_sizeingb(self):
        return self.assertEqual(diskinfo.sizeingb(977105060), 500L)

    def test_parse_hdparm_output(self):
        return self.assertEqual(
            diskinfo.parse_hdparm_output(
                '\n/dev/sda:\n Timing buffered disk reads: 1436 MB in  3.00 seconds = 478.22 MB/sec'),
            478.22)

    def test_parse_hdparm_output2(self):
        return self.assertEqual(
            diskinfo.parse_hdparm_output(
                '\n/dev/sdc:\n Timing buffered disk reads:  30 MB in  3.01 seconds =   9.97 MB/sec\n'),
            9.97)

if __name__ == "__main__":
    unittest.main()
