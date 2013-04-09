#!/bin/bash

set -x

make VERS=D6-F.1.0.0 DIST=squeeze clean
make VERS=D6-F.1.0.0 DIST=squeeze

rsync -a --delete --exclude disk /var/lib/debootstrap/install/D6-F.1.0.0/ /var/lib/debootstrap/install/D6-F.1.0.1/

make VERS=D6-F.1.0.1 DIST=squeeze clean
make VERS=D6-F.1.0.1 DIST=squeeze
