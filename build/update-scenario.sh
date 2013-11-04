#!/bin/bash
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

set -x

make DIST=wheezy VERS=D7-F.1.0.0 pxe mysql
./upgrade-from mysql D7-F.1.0.0 D7-F.1.0.1 /var/lib/debootstrap
./upgrade-from mysql D7-F.1.0.1 D7-F.1.0.2 /var/lib/debootstrap

make DIST=precise VERS=U12.04-F.1.0.0 pxe mysql
./upgrade-from mysql U12.04-F.1.0.0 U12.04-F.1.0.1 /var/lib/debootstrap
