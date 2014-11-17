#!/bin/bash
#
# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
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

do_fatal_error() {
    echo "$@" 1>&2
    exit 1
}

setup_network() {
if [ "$NETWORK_CONFIG" = "auto" ]; then
    # Fix network to start eth0 in DHCP
    if [ -f "$MDIR/etc/network/interfaces" ]; then
        if [ -r "$MDIR"/etc/network/interfaces ]; then
            cat > "$MDIR"/etc/network/interfaces <<EOF
# interfaces(5) file used by ifup(8) and ifdown(8)
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF
        fi
    else
        cat > "$MDIR"/etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
DEVICE=eth0
BOOTPROTO=dhcp
ONBOOT=yes
EOF
        echo "NETWORKING=yes" >> "$MDIR"/etc/sysconfig/network
    fi
fi
}

clean_temporary() {
    rm -rf "$MDIR/"dev/*
    umount "$MDIR/"proc
    umount "$MDIR"

    losetup -d $DEV
    TRY=5
    while [ $TRY -gt 0 ] && ! kpartx -d "$DISK"; do
	sleep 1
	TRY=$(($TRY - 1))
    done
    losetup -d $DISK
    rmdir "$MDIR"
}

do_cleanup() {
    ret=$?
    echo "#################"
    echo "# Entering TRAP #"
    echo "#################"
    clear_trap

    set +e

    clean_temporary

    if [ -f $IMG ]; then
       rm -f $IMG
    fi

    echo "###############"
    echo "# End of TRAP #"
    echo "###############"
    exit $ret
}

usage() {
    echo "<top directory> directory of the eDeploy role"
    echo "<name> name of the image"
    echo " -V optional: enable the Vagrant support"
    echo " -R allow to replace file"
    do_fatal_error "Usage: $0 [-R] [-V (libvirt|kvm)] <top directory> <name>"
}

while getopts :V:R FLAG; do
    case "${FLAG}" in
        V)
            if [ -z "${OPTARG}" ] || [ ! `echo "${OPTARG}" | egrep '^(libvirt|kvm)$'` ]; then
                echo "Error: argument \"${OPTARG}\" is not a supported Vagrant provider. It should be the Vagrant provider: either libvirt or kvm." >&2
                exit 2
            fi

            echo "Enabling Vagrant support"
            VAGRANT_PROVIDER=${OPTARG}
            VAGRANT=1
            ;;
        R)
            REPLACE=1
            ;;
        *)
            usage
    esac
done
shift $(( OPTIND - 1 ));

dir="$1"

. $ORIG/common

DIR="$1"
IMG="$2"
CFG="$3"

if [ -n "$CFG" ] && [  -f "$CFG" ]; then
    echo "Sourcing $CFG"
    . $CFG
fi

if [ -z "$DIR" ] || [ -z "$IMG" ]; then
    usage
fi

# QCOW2 as default image format
IMAGE_FORMAT=${IMAGE_FORMAT:-qcow2}
COMPRESSED=${COMPRESSED:-no}
ROOT_FS_SIZE=${ROOT_FS_SIZE:-auto}
NETWORK_CONFIG=${NETWORK_CONFIG:-auto}

if [ "$COMPRESSED" = "yes" ]; then
    if [ "$IMAGE_FORMAT" != "qcow2" ]; then
        do_fatal_error "Error: The compressed option is only available for qcow2 format"
    fi
    COMP_OPT="-c"
else
    COMP_OPT=""
fi

if [ "$REPLACE" != 1 -a -f "$IMG" ]; then
    do_fatal_error "Error: $IMG already exists"
fi

if [ ! -d "$DIR" -a ! -r "$DIR" ] ;then
    do_fatal_error "Error: directory or edeploy role $DIR doesn't exist"
fi

rm -f "$IMG"

modprobe loop
check_binary dd
check_binary parted
check_binary chroot
check_binary kpartx
check_binary qemu-img
check_binary losetup
check_binary mkfs.ext4
check_binary rsync
check_binary gunzip
check_binary tail

set -e
set -x

# Compute the size of the directory or the role
if [ -d "$DIR" ]; then
    SIZE=$(du -s -BM "$DIR" | cut -f1 | sed -s 's/.$//')
else
    SIZE=$(($(gunzip -l $DIR|tail -1|sed -e 's/ *[0-9]* *//' -e 's/  *.*//') / 1024 / 1024))
fi

# Did the root fs size got user defined ?
if [ "$ROOT_FS_SIZE" != "auto" ]; then
    # Does the enforced size is big enough ?
    if [ $ROOT_FS_SIZE -lt $SIZE ]; then
        do_fatal_error "Destination root filesystem size ($ROOT_FS_SIZE) is smaller than the operating system itself ($SIZE)"
    fi

    # The destination size is now set to the user defined value
    SIZE=$ROOT_FS_SIZE
else
    # add 30% to be sure that metadata from the filesystem fit
    SIZE=$(($SIZE * 130 / 100))
fi

# Create the image file
fallocate -l $(($SIZE * 1024 * 1024)) $IMG || dd if=/dev/zero of=$IMG count=$SIZE bs=1M

# Create one partition

DISK=$(losetup --show --find "$IMG")
parted -s "$DISK" mklabel msdos
parted -s "$DISK" mkpart primary ext2 32k '100%'
parted "$DISK" set 1 boot on

# Format the partition as ext4

PART=/dev/mapper/$(kpartx -av $DISK|cut -f3 -d' ')
TRY=5
while [ $TRY -gt 0 -a ! -b $PART ]; do
    sleep 1
    TRY=$(($TRY - 1))
done

mkfs.ext4 "$PART"
MDIR=$(mktemp -d)
DEV=$(losetup --show --find "$PART")
mount "$DEV" "$MDIR"

trap do_cleanup 0

# Copy the data

if [ -d "$DIR" ]; then
    rsync -a "$DIR/" "$MDIR/"
else
    tar xf "$DIR" -C "$MDIR"
fi

if [ -n "$VAGRANT" ]; then
  chroot "$MDIR" useradd -s /bin/bash -m vagrant

  # Set the hostname to vagrant
  echo vagrant > "$MDIR/etc/hostname"
  sed -i "1i127.0.1.1 vagrant" "$MDIR/etc/hosts"
  sed -i "3iresize2fs /dev/vda1" "$MDIR/etc/rc.local"

  # Vagrant password for root and vagrant
  sed -i -E 's,^(root|vagrant):.*,\1:$6$noowoT8z$b4ncy.PlVqQPzULCy1/pb5RDUbKCq02JgfCQGMQ1.mSmGItYRWFSJeLJemPcWjiaStJRa7HlXLt2gDh.aPAFa0:16118:0:99999:7:::,' "$MDIR/etc/shadow"
  echo nameserver 8.8.4.4 > "$MDIR/etc/resolv.conf"
  chroot "$MDIR"  apt-get.moved install -y nfs-common cloud-initramfs-growroot

  # SSH setup
  # Add Vagrant ssh key for root and vagrant accouts.
  sed -i 's/.*UseDNS.*/UseDNS no/' "$MDIR/etc/ssh/sshd_config"
  echo 'vagrant ALL=NOPASSWD: ALL' > "$MDIR/etc/sudoers.d/vagrant"

  for sshdir in "/root/.ssh" "/home/vagrant/.ssh"; do
      [ -d "${MDIR}${sshdir}" ] || mkdir "${MDIR}${sshdir}"
      chmod 700 "${MDIR}${sshdir}"
      cat > "${MDIR}${sshdir}/authorized_keys" << EOF
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key
EOF
      chmod 600 "${MDIR}${sshdir}/authorized_keys"
  done
  chroot "$MDIR" chown -R root:root /root/.ssh
  chroot "$MDIR" chown -R vagrant:vagrant /home/vagrant/.ssh
fi

# Let's create a copy of the current /dev
mkdir -p "${MDIR}/"/dev/pts
rsync -a --delete-before --exclude=shm /dev/ ${MDIR}/dev/

# Mount /proc
mount -t proc none "$MDIR/"proc

# Configure Grub

UUID=$(blkid -s UUID -o value "$PART")
export GRUB_DEVICE_UUID=$UUID
echo $GRUB_DEVICE_UUID

if [ -x ${MDIR}/usr/sbin/grub-mkconfig -o -x ${MDIR}/usr/sbin/grub2-mkconfig ]; then
    if [ -x ${MDIR}/usr/sbin/grub2-mkconfig ]; then
        V=2
    else
        V=
        # Install grub1
        cat > "$MDIR"/boot/grub/device.map <<EOF
(hd0) $DISK
(hd0,1) $PART
EOF
    fi

    # Display console on serial line
    if [ -r $MDIR/etc/default/grub ]; then
        sed -i -E 's/GRUB_CMDLINE_LINUX_DEFAULT="?([^"]*)"?/GRUB_CMDLINE_LINUX_DEFAULT="\1 console=ttyS0"/' $MDIR/etc/default/grub
    else
        echo "GRUB_CMDLINE_LINUX_DEFAULT=\"console=ttyS0\"" > $MDIR/etc/default/grub
    fi

    do_chroot "$MDIR" grub$V-install --modules="ext2 part_msdos" --no-floppy "$DISK"

    do_chroot "$MDIR" grub$V-mkconfig -o /boot/grub$V/grub.cfg || :

    # Fix generated grub.cfg
    sed -i -e 's/\t*loopback.*//' -e 's/\t*set root=.*//' -e "s/\(--set=root \|UUID=\)[^ ]?+/\1$UUID/" $MDIR/boot/grub$V/grub.cfg
    sed -i -e 's/msdos5/msdos1/g' $MDIR/boot/grub$V/grub.cfg

    # add / to fstab
    echo "UUID=$UUID / ext4 errors=remount-ro 0 1" >> $MDIR/etc/fstab
else
    # Grub1 doesn't have /usr/sbin/grub-mkconfig, failback on extlinux for booting
    if [ ! -x extlinux/extlinux ] || [ ! -f extlinux/menu.c32 ] || [ ! -f extlinux/libutil.c32 ]; then
        rm -rf extlinux
        mkdir -p extlinux
        # Installing extlinux & mbr from source
        SYSLINUX_VER=5.10
        wget --no-verbose https://kernel.org/pub/linux/utils/boot/syslinux/${TESTING_SYSLINUX}/syslinux-${SYSLINUX_VER}.tar.xz
        tar -xf syslinux-${SYSLINUX_VER}.tar.xz
        cp syslinux-${SYSLINUX_VER}/extlinux/extlinux extlinux/
        cp syslinux-${SYSLINUX_VER}/mbr/mbr.bin extlinux/
        cp syslinux-${SYSLINUX_VER}/com32/menu/menu.c32 extlinux/
        cp syslinux-${SYSLINUX_VER}/com32/libutil/libutil.c32 extlinux/
        rm -rf syslinux-${SYSLINUX_VER}*
    fi
    for kernel in ${MDIR}/boot/vmlinuz-*; do
        kversion=`echo $kernel | awk -F'vmlinuz-' '{print $NF}'`;
        KERNEL="/boot/vmlinuz-${kversion}"
        INITRD="/boot/initramfs-${kversion}.img"
        echo "default Linux" >  ${MDIR}/boot/extlinux.conf
        echo "label Linux" >>  ${MDIR}/boot/extlinux.conf
        echo "  kernel $KERNEL" >> ${MDIR}/boot/extlinux.conf
        echo "  append initrd=$INITRD root=UUID=$UUID nomodeset rw $BOOT_ARG" >> ${MDIR}/boot/extlinux.conf
        extlinux --install ${MDIR}/boot
    done
    # install mbr
    dd if=extlinux/mbr.bin of=$IMG conv=notrunc
fi

sync

# Fixes according to
# http://docs.openstack.org/image-guide/content/ch_openstack_images.html

setup_network

# Cleanup everything
clear_trap
clean_temporary


if [ -n "$VAGRANT" ]; then
   qemu-img convert -O $IMAGE_FORMAT "$IMG" box.img
   cat > metadata.json <<EOF
{
  "provider": "${VAGRANT_PROVIDER}",
  "format": "qcow2",
  "virtual_size": 10
}
EOF
    tar cvzf ${IMG}.box metadata.json box.img
    rm box.img "$IMG"
    echo "Your Vagrant box is ready, you can import it using the following command:
 vagrant box add ${IMG} ${IMG}.box --provider=${VAGRANT_PROVIDER}"
else
    if [ -n "$IMAGE_FORMAT" -a "$IMAGE_FORMAT" != raw ]; then
        qemu-img convert $COMP_OPT -O $IMAGE_FORMAT "$IMG" "$IMG".$IMAGE_FORMAT
    fi
fi

