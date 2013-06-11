#!/bin/bash
KVM=
DISK=kvm_storage.img
DISK_SIZE=2000 # in MB
HTTP_PORT=9000
INST=$1
SSH_PORT=2222
PYTHON_PID=0

detect_kvm() {
	VM=$(which kvm 2>/dev/null)
	if [ $? -ne 0 ]; then
		KVM=$(which qemu-kvm 2>/dev/null)
		if [ $? -ne 0 ]; then
			echo "Please Install KVM first"
			echo "Exiting !"
			exit 1
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
	$KVM --enable-kvm -m 512  -net nic -net nic,model=virtio -net user,tftp=tftpboot,bootfile=/pxelinux.510,hostfwd=tcp::$SSH_PORT-:22 -drive file=$DISK,if=none,id=drive-virtio-disk0,format=qcow2,cache=none -boot n -serial stdio
}


start_rsyncd() {
	cat > rsync-kvm.conf << EOF
use chroot = no
syslog facility = local5
pid file = /var/run/rsyncd.pid

[install]
	uid=root
	gid=root
	path=$INST

EOF

	# Rsync shall die with the current test
	rsync --daemon --config rsync-kvm.conf --port 1515 --no-detach & 
}

start_httpd() {
	ln -sf ../ cgi-bin &>/dev/null
	python -m CGIHTTPServer $HTTP_PORT &
	HTTP_PID=$!
}

stop_httpd() {
	kill -9 $HTTP_PID
}

create_edeploy_conf() {
	cat > edeploy.conf << EOF
[SERVER]

CONFIGDIR=$PWD/../config
LOCKFILE=edeploy.lock
EOF

# Insure upload.py can create its lock file locally
chmod a+rw .

ln -sf $PWD/edeploy.conf /etc/
}

############## MAIN
start_rsyncd
start_httpd
create_edeploy_conf
detect_kvm
prepare_disk
run_kvm
stop_httpd
