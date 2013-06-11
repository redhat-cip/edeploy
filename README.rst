eDeploy
=======

eDeploy is a work in progress to experiment with a new way to
provision/update systems (physical or virtual) using trees of files
instead of packages or VM images.

Installation is done in 4 steps simulating a PXE boot:

- detect PCI hardware and setup network.
- send the detected hardware config to the server
- the server sends back a configuration script.
- run the configuration script to setup IPMI, RAID, partitions and network.
- according to the defined role, rsync the tree on the newly created partitions.
- configure the grub2 boot loader and reboot the system.

Then the system will boot on the provisioned harddrive directly.

How to start
------------

Issue ``make`` to build the base directory with a minimal Debian
wheezy tree, then strip it down to a pxe directory that will lead to
the creation of an initrd.pxe. Take this initrd.pxe file and the
base/boot/vmlinuz* kernel to boot from PXE.

Configure the PXE boot like that::

 prompt 0
 timeout 0
 default eDeploy
 serial 0
 
 LABEL eDeploy
 	KERNEL vmlinuz
 	INITRD initrd.pxe SERV=10.0.2.2 RSERV=10.0.2.2 console=tty0 console=ttyS0,115200 DEBUG=1 RSERV_PORT=1515 HTTP_PORT=9000
 
 LABEL local
 	LOCALBOOT 0

CGI script
++++++++++

On the web server, you need to setup the ``upload.py`` CGI
script. This CGI script is a python script which needs the
``python-ipaddr`` dependency optionnaly.

The CGI script is configured with ``/etc/edeploy.conf``::

 [SERVER]
 
 CONFIGDIR=/root/edeploy/config
 LOCKFILE=/var/tmp/edeploy.lock

``CONFIGDIR`` points to a directory which contains specifications
(``*.specs``), configurations (``*.configure``) and CMDB (``*.cmdb``)
per hardware profile, a description of the hardware profile priorities
(``state``).

``LOCKFILE`` points to a file used to lock the ``CONFIGDIR`` files
that are read and written like ``*.cmdb`` and ``state``.

``state`` contains an ordered list of profiles and the number of times
they must be installed for your deployment. Example::

 [('hp', 4), ('vm', '*')]

which means, the ``hp`` profile must only be installed 4 times and the
``vm`` profile can be installed without limit.

Each profile must have a ``.specs`` and ``.configure`` files. For
example, the ``vm.specs`` is a python list in this form::

 [
     ('disk', '$disk', 'size', 'gt(4)'),
     ('network', '$eth', 'ipv4', 'network(192.168.122.0/24)'),
     ('network', '$eth', 'serial', '$mac'),
 ]

Each entry of the list is tuple of 4 entries that must be matched on
the hardware profile detected on the system to install. If en element
starts with a ``$``, it's a variable that will take the value of
detected system config. These variables will be passed to the
configure script that will use them. For example the ``vm.configure``
is a Python script like that::

 disk1 = '/dev/' + var['disk']
 
 for disk, path in ((disk1, '/chroot'), ):
     run('parted -s %s mklabel msdos' % disk)
     run('parted -s %s mkpart primary ext2 0%% 100%%' % disk)
     run('mkfs.ext4 %s1' % disk)
     run('mkdir -p %s; mount %s1 %s' % (path, disk, path))
 
 open('/interfaces', 'w').write('''
 auto lo
 iface lo inet loopback
 
 auto %(eth)s
 allow-hotplug %(eth)s
 iface %(eth)s inet static
      address %(ip)s
      netmask %(netmask)s
      gateway %(gateway)s
      hwaddress %(mac)s
 ''' % var)
 
 set_role('mysql', 'D7-F.1.0.0', disk1)

The variables are stored in the ``var`` dictionary. 2 functions are
defined to be used in these configure scripts: ``run`` to execute
commands and abort on error, ``set_role`` to define the software
profile and version to install in the next step.

CMDB files are optional and used to add extra information to the
``var`` dictionary before configuration. To associate a CMDB entry,
the ``upload.py`` script tries to find a matching entry for the
matched spec. If nothing is found then the script tries to find an
unused entry (with no ``'used': 1`` part). This selected entry is
merged into ``var`` and then stored back in the CMDB file.

A CMDB file to manage a set of IPv4 addesses or settings to use, it
can be like that::

 [
  {'ip': '192.168.122.3'},
  {'ip': '192.168.122.4'},
  {'ip': '192.168.122.5'},
  {'ip': '192.168.122.6'},
  {'ip': '192.168.122.7'}
 ]

Once an entry has been used, the CMDB file will be like that::

 [
  {'disk': 'vda',
   'eth': 'eth0',
   'gateway': '192.168.122.2',
   'ip': '192.168.122.2',
   'mac': '52:54:00:88:17:3c',
   'netmask': '255.255.255.0',
   'used': 1},
  {'ip': '192.168.122.4'},
  {'ip': '192.168.122.5'},
  {'ip': '192.168.122.6'},
  {'ip': '192.168.122.7'}
 ]

There is also an helper function that can be used like that to avoid
to create long list of entries::

 generate({'ip': '192.168.122.3-7'})

The first time the ``upload.py`` script reads it, it expands the list
and stores it in the regular form.

Rsync server
++++++++++++

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

Image management
----------------

To build and test the install procedure under kvm::

 ./update-scenario.sh
 cd /var/lib/debootstrap/install/D7-F.1.0.0
 qemu-img create disk 10G
 kvm -initrd initrd.pxe -kernel base/boot/vmlinuz-3.2.0-4-amd64 -hda disk
 kvm -hda disk

Log into the root account and then launch the following command to
update to the new version of mysql::

 edeploy upgrade D7-F.1.0.1

And then you can test the kernel update process::

 edeploy upgrade D7-F.1.0.2
