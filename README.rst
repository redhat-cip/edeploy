eDeploy
=======

eDeploy is a work in progress to experiment with a new way to
provision/update systems (physical or virtual) using trees of files
instead of packages or VM images.

Installation is done using these steps:

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
 	INITRD initrd.pxe SERV=10.0.2.2 RSERV=10.0.2.2 console=tty0 console=ttyS0,115200 DEBUG=1 VERBOSE=1 RSERV_PORT=1515 HTTP_PORT=9000
 
 LABEL local
 	LOCALBOOT 0

The ``DEBUG`` variable if set to ``1`` on the kernel command line, it
enables more debugging, the start of an ssh server on the configured
system and the launch of an interactive shell at the end of the
installation.

The ``VERBOSE`` variable if set to ``1`` on the kernel command line, it turns on
the -x of bash to ease the understanding of faulty commands

Please note that RSERV_PORT and HTTP_PORT are given here as an example to override the default settings 831 & 80 respectively.
Unless you run the rsync server or the http server on a very particular setup, don't use this variables.

CGI script
++++++++++

The address and port of the http server are defined on the kernel
command line in the ``SERV`` and ``HTTP_PORT`` variables.

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
(``state``). All those files must be readable by the user running the
http server.

``LOCKFILE`` points to a file used to lock the ``CONFIGDIR`` files
that are read and written like ``*.cmdb`` and ``state``. These files
(``LOCKFILE``, ``*.cmdb`` and ``state``) must be readable and writable
by the user running the http server.

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
the hardware profile detected on the system to install.

If an element ends with ``)`` a function is used to match the
value. Available functions are ``gt`` (greater than), ``ge`` (greater
or equal), ``lt`` (lesser than), ``le`` (lesser or equal), and ``network``
(match an IPv4 network).

If en element starts with a ``$``, it's a variable that will take the
value of the detected system config. These variables will be passed to
the configure script that will use them. For example the
``vm.configure`` is a Python script like that::

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

A CMDB file manages a set of settings to use (i.e. IPv4 addresses or
host names), it can be like that::

 [
  {'ip': '192.168.122.3', 'hostname': 'host3'},
  {'ip': '192.168.122.4', 'hostname': 'host4'},
  {'ip': '192.168.122.5', 'hostname': 'host5'},
  {'ip': '192.168.122.6', 'hostname': 'host6'},
  {'ip': '192.168.122.7', 'hostname': 'host7'}
 ]

Once an entry has been used, the CMDB file will be like that::

 [
  {'disk': 'vda',
   'eth': 'eth0',
   'hostname': 'host3',
   'ip': '192.168.122.3',
   'mac': '52:54:00:88:17:3c',
   'used': 1},
  {'ip': '192.168.122.4', 'hostname': 'host4'},
  {'ip': '192.168.122.5', 'hostname': 'host5'},
  {'ip': '192.168.122.6', 'hostname': 'host6'},
  {'ip': '192.168.122.7', 'hostname': 'host7'}
 ]

There is also an helper function that can be used like that to avoid
to create long list of entries::

 generate({'ip': '192.168.122.3-7', 'hostname': 'host3-7'})

The first time the ``upload.py`` script reads it, it expands the list
and stores it in the regular form.

Rsync server
++++++++++++

The address and port of the rsync server are defined on the kernel
command line in the ``RSERV`` and ``RSERV_PORT`` variables. Change the
address before testing. The rsync server must be started as root right
now and configured to serve an install target like this in the
/etc/rsyncd.conf::

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
display available update version::

 edeploy list

To update to the new version of mysql::

 edeploy upgrade D7-F.1.0.1

And then you can test the kernel update process::

 edeploy upgrade D7-F.1.0.2

You can also verify what has been changed from the initial install or
upgrade by running::

 edeploy verify

Update process
++++++++++++++

The different trees must be available under the ``[install]`` rsync
server setting like that::

 <version>/<role>/

For example::

 D7-F.1.0.0/mysql/

To allow updates from on version of a profile to another version,
special files must be available under the ``[metadata]`` rsync server
setting like that::

 <from version>/<role>/<to version>/

For example to allow an update from ``D7-F.1.0.0`` to ``D7-F.1.0.1``
for the ``mysql`` role, you must have this::

 D7-F.1.0.0/mysql/D7-F.1.0.1/

This directory must contain an ``exclude`` file which defines the list
of files to exclude from the synchonization. These files are the
changing files like data or generated files. You can use ``edeploy
verify`` to help defining these files.

This directory could also contain 2 scripts ``pre`` and ``post`` which
will be run if present before synchronizing the files to stop services
and after the synchro for example to restart stopped services. The
``post`` script can report that a reboot is needed by exiting with a
return code of 100.
