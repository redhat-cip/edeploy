#!/bin/bash
#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Erwan Velu <erwan.velu@enovance.com>
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

KVM=
DISK=kvm_storage.img
DISK_SIZE=2000 # in MB
HTTP_PORT=9000
INST=$1
SSH_PORT=2222
PYTHON_PID=0
RSYNC_PID=0
LOCKFILE=edeploy.lock
SYSLINUX_VER=5.10

fatal_error() {
        echo $1;
        exit 1
}

check_binary() {
        type -p $1 || fatal_error "$1 is missing"
}

detect_kvm() {
	KVM=$(which kvm 2>/dev/null)
	if [ $? -ne 0 ]; then
		KVM=$(which qemu-kvm 2>/dev/null)
		if [ $? -ne 0 ]; then
			fatal_error "Please Install KVM first"
		fi
	fi
}

prepare_disk() {
	if [ ! -f $DISK ]; then
		echo "Preparing system disk, please wait a short"
		qemu-img create -f qcow2 $DISK ${DISK_SIZE}M
	fi
}

run_kvm() {
	BOOT_DEVICE="n"
	[ "$1" = "local" ] && BOOT_DEVICE="c"

	$KVM --enable-kvm -m 512\
		-netdev user,id=net0,net=10.0.2.0/24,tftp=tftpboot,bootfile=/pxelinux.0,hostfwd=tcp::$SSH_PORT-:22 \
		-netdev user,id=net1,net=10.0.3.0/24 \
		-netdev user,id=net2,net=1.2.3.0/24 \
		-device virtio-net,netdev=net0,mac=52:54:12:34:00:01 \
		-device virtio-net,netdev=net1,mac=52:54:12:34:00:02 \
		-device virtio-net,netdev=net2,mac=52:54:12:34:00:03 \
		-drive file=$DISK,if=virtio,id=drive-virtio-disk0,format=qcow2,cache=none,media=disk,index=0 \
		-boot $BOOT_DEVICE \
		-serial stdio \
		-smbios type=1,manufacturer=kvm,product=edeploy_test_vm
}


start_rsyncd() {
	cat > rsync-kvm.conf << EOF
use chroot = no
syslog facility = local5
pid file = rsyncd-edeploy.pid

[install]
	uid=root
	gid=root
	path=$INST/install

[metadata]
	uid=root
	gid=root
	path=$INST/metadata
EOF

	# Rsync shall die with the current test
	rsync --daemon --config rsync-kvm.conf --port 1515 --no-detach &
	RSYNC_PID=$!
}

start_httpd() {
	rm -f cgi-bin
	ln -sf ../server cgi-bin &>/dev/null
	python -m CGIHTTPServer $HTTP_PORT &
	HTTP_PID=$!
}

stop_httpd() {
	kill -9 $HTTP_PID &>/dev/null
	rm -f $LOCKFILE
}

stop_rsyncd() {
	kill -9 $RSYNC_PID &>/dev/null
	rm -f rsyncd-edeploy.pid &>/dev/null
}

setup_pxe() {
	if [ ! -f tftpboot/pxelinux.0 -o ! -f tftpboot/ldlinux.c32 ]; then
		mkdir -p tftpboot
	        # Installing extlinux & mbr from source
		wget ftp://ftp.kernel.org/pub/linux/utils/boot/syslinux/syslinux-${SYSLINUX_VER}.tar.xz
		tar -xf syslinux-${SYSLINUX_VER}.tar.xz
		cp syslinux-${SYSLINUX_VER}/core/pxelinux.0 tftpboot/
		cp syslinux-${SYSLINUX_VER}/com32/elflink/ldlinux/ldlinux.c32 tftpboot/
		rm -rf syslinux-${SYSLINUX_VER}*
	fi
}

create_edeploy_conf() {
	cat > edeploy.conf << EOF
[SERVER]

CONFIGDIR=$PWD/../config
LOCKFILE=$LOCKFILE
USEPXEMNGR=False
PXEMNGRURL=http://192.168.122.1:8000/
EOF

# Insure upload.py can create its lock file locally
chmod a+rw .
chmod a+rw $PWD/../config/state
chmod a+rw $PWD/../config/kvm-test.cmdb

ln -sf $PWD/edeploy.conf /etc/
}

############## MAIN
check_binary rsync
check_binary qemu-img
check_binary python

setup_pxe
start_rsyncd
start_httpd
create_edeploy_conf
detect_kvm
prepare_disk
run_kvm
stop_httpd
stop_rsyncd
run_kvm local
