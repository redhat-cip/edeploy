eDeploy
=======

eDeploy is a work in progress to experiment with a new way to
provision/update systems (physical or virtual) using trees of files
instead of packages.

Installation is done in 4 steps simulating a PXE boot:

- detect PCI hardware and setup network.
- create an ext4 partition on the harddrive detected.
- rsync the tree on the newly created partition.
- configure the grub2 boot loader and stop the system.

Then you can boot the system with the provisioned harddrive directly.

How to start
------------

Issue make to build the base directory with a minimal Debian wheezy
tree, then strip it down to a pxe directory that will lead to the
creation of an initrd.pxe.

Right now the address of the rsync server is hardcoded in the init
file. Change the adress before testing. The rsync server must be
started as root right now and configured to serve an install target
like this in the /etc/rsyncd.conf::

 uid = root
 gid = root
 
 [install]
         path = /var/lib/debootstrap/install
         comment = eDeploy install trees
 
 [metadata]
         path = /var/lib/debootstrap/metadata
         comment = eDeploy metadata
  uid = root
  gid = root

To test the install procedure under kvm::

 make
 cd /var/lib/debootstrap/install/D7-F.1.0.0
 qemu-img create disk 10G
 kvm -initrd initrd.pxe -kernel base/boot/vmlinuz-3.2.0-4-amd64 -hda disk
 kvm -hda disk

To test the update procedure under kvm::

 ./update-scenario.sh
 cd /var/lib/debootstrap/install/D6-F.1.0.0
 qemu-img create disk 10G
 kvm -initrd initrd.pxe -kernel base/boot/vmlinuz-3.2.0-4-amd64 -hda disk
 kvm -hda disk

Log into the root account and then launch the following command to
update to the new version of mysql::

 edeploy

