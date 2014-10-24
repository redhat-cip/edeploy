#!/bin/bash

# Script used by Jenkins jobs to build roles and archive them if the
# target directory exists

if [ $# -lt 3 ]; then
    echo "$0 <src dir> <build dir> <archive dir> [<make params>...]" 1>&2
    exit 1
fi

set -e

SRC="$1"
shift
DIR="$1"
shift
ARCH="$1"
shift

if [ -f $HOME/froze-builds ]; then
    exit 0
fi

if [ -z "$ROLES" ]; then
    ROLES="base pxe health-check deploy"
fi

set -x

cd $SRC
sudo mkdir -p "$DIR"/install
RC=0
BROKEN=

for role in $ROLES; do
    if sudo env VIRTUALIZED=$VIRTUALIZED make TOP="$DIR" ARCHIVE="$ARCH" "$@" $role; then
	if [ -d "$ARCH" ]; then
	    VERS=$(sudo make TOP="$DIR" "$@" version)
	    mkdir -p "$ARCH"/$VERS/
	    rsync -a "$DIR"/install/$VERS/*.* "$ARCH"/$VERS/
            if [ -d "$DIR"/install/$VERS/base/boot ]; then
                rsync -a "$DIR"/install/$VERS/base/boot/vmlinuz* "$ARCH"/$VERS/vmlinuz
                (cd "$ARCH"/$VERS; md5sum vmlinuz > vmlinuz.md5)
            fi
	    git rev-parse HEAD > "$ARCH"/$VERS/$role.rev
	fi
    else
	BROKEN="$BROKEN $role"
	RC=1
    fi
done

set +x

if [ -n "$BROKEN" ]; then
    echo "BROKEN ROLES:$BROKEN"
fi

exit $RC
