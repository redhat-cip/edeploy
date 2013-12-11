#!/bin/bash

SRC=$(cd $(dirname $0)/..; pwd)

if [ $# -eq 0 ]; then
    echo "$0 <dirname> [<make params>...]" 1>&2
    exit 1
fi


if [ -z "$JOB_NAME" ]; then
    echo "JOB_NAME env variable must be set" 1>&2
    exit 1
fi

set -e

DIR="$1"
shift

cleanup() {
    if [ -d "$DIR" ]; then
	sudo rm -rf "$DIR"
    fi
}

trap cleanup 0

if [ -z "$ROLES" ]; then
    ROLES="pxe openstack-controller openstack-swift-proxy openstack-swift-storage galera haproxy ceph puppet-master"
fi
set -x

cd $SRC/build
sudo rm -rf "$DIR"
sudo mkdir -p "$DIR"/tmp
for role in $ROLES; do
    sudo make TOP="$DIR" VERS=$JOB_NAME NO_COMPRESSED_FILE=1 "$@" $role || exit 1
    sudo rm -rf "$DIR"/install/$JOB_NAME/$role*
done
