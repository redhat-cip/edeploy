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

if [ -z "$COMPRESSED_ROLES" ]; then
    COMPRESSED_ROLES="base cloud openstack-full install-server install-server-vm mysql slave softwarefactory"
fi

set -x

cd $SRC
sudo mkdir -p "$DIR"/install
RC=0
BROKEN=

for role in $ROLES; do
    NO_COMPRESSED_FILE=1
    for compr in $COMPRESSED_ROLES; do
        if [ "$role" = "$compr" ]; then
            NO_COMPRESSED_FILE=
            break
        fi
    done
    if sudo env NO_COMPRESSED_FILE=$NO_COMPRESSED_FILE VIRTUALIZED=$VIRTUALIZED make TOP="$DIR" ARCHIVE="$ARCH" "$@" $role; then
	if [ -d "$ARCH" ]; then
	    BVERS=$(sudo make TOP="$DIR" "$@" bversion || :)
	    VERS=$(sudo make TOP="$DIR" "$@" version)

	    mkdir -p "$ARCH"/$VERS/
	    rsync -a "$DIR"/install/$VERS/*.* "$ARCH"/$VERS/

            if [ -n "$BVERS" ]; then
                for f in vmlinuz health.pxe initrd.pxe; do
                    case $f in
                        vmlinuz)
                            dirname=base
                            ;;
                        health.pxe)
                            dirname=health
                            ;;
                        initrd.pxe)
                            dirname=pxe
                            ;;
                    esac
                    # Only copy the file when there is no support in the current
                    # version (could happen in upgrades)
                    if [ ! -d "$DIR"/install/$VERS/$dirname -a -r "$ARCH"/$BVERS/${f} ]; then
                        cp "$ARCH"/$BVERS/${f}* "$ARCH"/$VERS/
                    fi
                done
            else
                if [ -d "$DIR"/install/$VERS/base/boot ]; then
                    rsync -a "$DIR"/install/$VERS/base/boot/vmlinuz* "$ARCH"/$VERS/vmlinuz
                    (cd "$ARCH"/$VERS; md5sum vmlinuz > vmlinuz.md5)
                fi
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
