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

import sys


def generate(g):
    return ()

key = sys.argv[1]
val = sys.argv[2]
cmdb = eval(open(sys.argv[3]).read(-1))

for entry in cmdb:
    try:
        if entry[key] == val and entry['used'] == 1:
            sys.exit(0)
    except KeyError:
        pass

sys.exit(1)

# verify-cmdb.py ends here
