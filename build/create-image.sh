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

ORIG=$(cd $(dirname $0); pwd)

. $ORIG/common

do_fatal_error() {
    echo "$@" 1>&2
    exit 1
}

setup_network() {
if [ "$NETWORK_CONFIG" = "auto" ]; then
    # Fix network to start eth0 in DHCP

    if [ -r "$MDIR"/etc/network/interfaces ]; then
    cat > "$MDIR"/etc/network/interfaces <<EOF
# interfaces(5) file used by ifup(8) and ifdown(8)
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF
    fi
fi
}

clean_temporary() {
    umount "$MDIR/"dev
    umount "$MDIR/"proc
    umount "$MDIR"

    losetup -d $DEV
    kpartx -d "$IMG"
    rmdir "$MDIR"
}

do_cleanup() {
    ret=$?
    echo "#################"
    echo "# Entering TRAP #"
    echo "#################"
    clear_trap

    clean_temporary

    if [ -f $IMG ]; then
       rm -f $IMG
    fi

    echo "###############"
    echo "# End of TRAP #"
    echo "###############"
    exit $ret
}

if [ $# != 3 ]; then
    do_fatal_error "Usage: $0 <top directory> <image file to create> <configuration_file>"
fi

DIR="$1"
IMG="$2"
CONFIG="$3"

. $CONFIG

# QCOW2 as default image format
IMAGE_FORMAT=${IMAGE_FORMAT:-qcow2}
ROOT_FS_SIZE=${ROOT_FS_SIZE:-auto}
NETWORK_CONFIG=${NETWORK_CONFIG:-auto}

if [ -f "$IMG" ]; then
    do_fatal_error "Error: $IMG already exists"
fi

if [ ! -d "$DIR" ] ;then
    do_fatal_error "Error: directory $DIR doesn't exist"
fi

check_binary dd
check_binary parted
check_binary chroot
check_binary kpartx
check_binary qemu-img
check_binary losetup
check_binary mkfs.ext3
check_binary rsync

set -e
set -x

# Compute the size of the directory
SIZE=$(du -s -BM "$DIR" | cut -f1 | sed -s 's/.$//')

# Did the root fs size got user defined ?
if [ "$ROOT_FS_SIZE" != "auto" ]; then
    # Does the enforced size is big enough ?
    if [ $ROOT_FS_SIZE -lt $SIZE ]; then
        do_fatal_error "Destination root filesystem size ($ROOT_FS_SIZE) is smaller than the operating system itself ($SIZE)"
    fi

    # The destination size is now set to the user defined value
    SIZE=$ROOT_FS_SIZE
else
    # add 20% to be sure that metadata from the filesystem fit
    SIZE=$(($SIZE * 120 / 100))
fi

trap do_cleanup 0

# Create the image file
dd if=/dev/zero of=$IMG count=$SIZE bs=1M

# Create one partition

DISK=$(losetup --show --find "$IMG")
parted -s "$DISK" mklabel msdos
parted -s "$DISK" mkpart primary ext2 32k '100%'
parted "$DISK" set 1 boot on

# Format the partition as ext3

PART=/dev/mapper/$(kpartx -av $DISK|cut -f3 -d' ')
mkfs.ext3 "$PART"
MDIR=$(mktemp -d)
DEV=$(losetup --show --find "$PART")
mount "$DEV" "$MDIR"

# Copy the data

rsync -a "$DIR/" "$MDIR/"

# Install Grub on the boot sector

mount -obind /dev "$MDIR/"dev
mount -t proc none "$MDIR/"proc

cat > "$MDIR"/boot/grub/device.map <<EOF
(hd0) $DISK
(hd0,1) $PART
EOF

do_chroot "$MDIR" grub-install --modules=\"ext2 part_msdos\" --no-floppy "$DISK"

# Configure Grub

UUID=$(blkid -s UUID -o value "$PART")
export GRUB_DEVICE_UUID=$UUID
echo $GRUB_DEVICE_UUID

if [ ! -r "$MDIR"/boot/grub/grub.cfg ]; then
    do_chroot "$MDIR" grub-mkconfig -o /boot/grub/grub.cfg || :
fi

# Fix generated grub.cfg
# As we run on primary partition, let's fix the numbering
sed -i -e 's/msdos5/msdos1/g' $MDIR/boot/grub/grub.cfg
sed -i -e 's/\t*loopback.*//' -e 's/\t*set root=.*//' -e "s/\(--set=root \|UUID=\)[^ ]*/\1$UUID/p" $MDIR/boot/grub/grub.cfg

sync

# Fixes according to
# http://docs.openstack.org/image-guide/content/ch_openstack_images.html

setup_network

# Cleanup everything
clean_temporary

qemu-img convert -O $IMAGE_FORMAT "$IMG" "$IMG".$IMAGE_FORMAT

clear_trap
