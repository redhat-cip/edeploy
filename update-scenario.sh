#!/bin/bash

set -x

make
./upgrade-from mysql D7-F.1.0.0 D7-F.1.0.1 /var/lib/debootstrap
./upgrade-from mysql D7-F.1.0.1 D7-F.1.0.2 /var/lib/debootstrap

make DIST=precise VERS=U12.04-F.1.0.0
./upgrade-from mysql U12.04-F.1.0.0 U12.04-F.1.0.1 /var/lib/debootstrap
