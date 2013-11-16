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

if [ $# != 2 ]; then
    echo "Usage: $0 <top directory> <image file to create>" 1>&2
    exit 1
fi

DIR="$1"
IMG="$2"

if [ -f "$IMG" ]; then
    echo "Error: $IMG already exists" 1>&2
    exit 1
fi

if [ ! -d "$DIR" ] ;then
    echo "Error: directory $DIR doesn't exist" 1>&2
    exit 1
fi

set -e
set -x

# Compute the size of the directory

SIZE=$(du -s -BM "$DIR" | cut -f1 | sed -s 's/.$//')

# add 20% to be sure that metadata from the filesystem fit

SIZE=$(($SIZE * 120 / 100))

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
(hd0,1) $DEV
EOF

chroot "$MDIR" grub-install --no-floppy "$DISK"

# Configure Grub

if [ ! -r "$MDIR"/boot/grub/grub.cfg ]; then
    chroot "$MDIR" grub-mkconfig -o /boot/grub/grub.cfg || :
fi

eval $(blkid -o export "$DEV")
sed -i -e "s/\(--set=root \|UUID=\)[^ ]*/\1$UUID/p" $MDIR/boot/grub/grub.cfg
sync

# Fixes according to
# http://docs.openstack.org/image-guide/content/ch_openstack_images.html

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

# Cleanup everything

umount "$MDIR/"dev
umount "$MDIR/"proc
umount "$MDIR"

losetup -d $DEV
kpartx -d "$IMG"
rmdir "$MDIR"

#qemu-img convert -O qcow2 "$IMG" "$IMG".qcow2
#mv -f "$IMG".qcow2 "$IMG"
