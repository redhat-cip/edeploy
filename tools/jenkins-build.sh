#!/bin/bash

SRC=$(cd $(dirname $0)/..; pwd)

if [ $# -lt 2 ]; then
    echo "$0 <build dir> <archive dir> [<make params>...]" 1>&2
    exit 1
fi

set -e

DIR="$1"
shift
ARCH="$1"
shift

cleanup() {
    if [ -d "$DIR" ]; then
	sudo rm -rf "$DIR"/install/
    fi
}

trap cleanup 0

if [ -z "$ROLES" ]; then
    ROLES="base pxe openstack-common openstack-full puppet-master"
fi

set -x

cd $SRC/build
cleanup
sudo mkdir -p "$DIR"/install
RC=0
for role in $ROLES; do
    if sudo make TOP="$DIR" "$@" $role; then
	if [ -d "$ARCH" ]; then
	    VERS=$(sudo make TOP="$DIR" "$@" version)
	    mkdir -p "$ARCH"/$VERS/
	    rsync -a "$DIR"/install/$VERS/*.* "$ARCH"/$VERS/
	    git rev-parse HEAD > "$ARCH"/$VERS/$role.rev
	fi
    else
	RC=1
    fi
done

exit $RC
