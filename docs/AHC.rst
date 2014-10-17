=======================================
Automatic Health Check (AHC) User Guide
=======================================

--------------------------------------
Benchmarking infrastructures made easy
--------------------------------------

.. contents:: Table of Contents

Introduction on the need of benchmarking infrastructures
========================================================
An infrastructure s made of physical servers, networking components and some software, 
and is made for delivering a service. Once the first step of racking, connecting everything is done,

it's time to ask yourself those questions : 

- "Are all my servers performing as expected ?" 
- "Is the level of performance the expected one ?”

If you bought those servers together, the usual answer is: 

- "Yes, they are supposed to be and perform the same"
  
Is it enough to get into production ? What would be the consequences of a mostly-failing component on the global infrastructure ?

To get a clear view of your infrastructure state, you have to benchmark it.


What AHC is made for ?
======================

AHC is made for answering this simple question:

- "Are my servers running almost normally ?"


The *almost* part of the sentence is very important. This tool does not try to benchmark everything in every possible configuration  but make a best-effort estimation of your server’s capabilities.
Having a quick overview of a system to insure the basic features are working well. It’s usually enough to track down weak systems.

AHC's concepts
==============

Reproducibility
---------------
Software configurations/changes is a big concern when performing performance tests. It’s mandatory to reduce any possible source of annoyance that could have a positive or negative impact on the performance (like a crontab, a change in the benchmark tool itself or patch on the Linux Kernel). As we try to setup a performance indicator to compare a set of servers, keeping the same OS over server and time is a key point to consider.

The main idea here is to create a custom operating system that embeds the less amount of possible software with the Linux distribution of your choice. Ideally, the result is a bootable disk image or a kernel and ramfs files that could be booted over PXE.

The main benefit of this approach is being able to boot anytime your servers in order to run a benchmark test series without making any change on your production environment.

As a result, the performance metrics will always be provided on the same software environment letting as a unique difference between tests and over-time the hardware you have. It’s so possible to perform some differential analysis between install time anytime later if some issues are occurring on this particular server. This also could be used to ensure that a new server at least as performing as the other servers of a given pool..

AHC is part of the eDeploy project as a role that performs the task of selecting the main packages required to perform all this benchmark series. The resulting Operating System is now strongly versioned, archivable and available at any time. Booting becomes very easy by using a USB key on standalone servers or via PXE on an already setup network. 

Be as close as possible to the hardware
---------------------------------------
Benchmarking an infrastructure means being able to define how every single component (cpu, ram, storage, network) performs. To understand every single defect, it's important to be as close as possible to the hardware. This does have an impact on the tool to select and the associated parameters.

What we don't want to benchmark :

- caching effects

  The memory is usually used on every system to speed-up the access time to a given ressource. Using memory turns milliseconds or even seconds to reach an information into {micro|nano}seconds.
  It will be so mandatory to ask tools to avoid explicit caching.
- software optimization to hide hardware defects

  To optimize the usuage of a ressource, operating systems are providing software layers to optimize the acces to the ressource by aggregating requests or rescheduling IOs.
  Filesystems are known to do this kind of work. As we want to measure the state of every single device of the infrastructure, testing it through a filesystem hides part of the reality of this device.
  Storage benchmarking will have so to test the block device directly instead.


Constant time benchmarking
--------------------------
It’s a common mistake to use tools that try to see how long it takes to process a given amount of data. Benchmark results are usually expressed in ‘unit per time‘ like MegaBytes per seconds, GigaBit per seconds. If time is not a fixed element, the benchmark aren’t really comparable : processing 1GB of data on a system that consumes them at 100MB/sec last 10 seconds while it will take 100 seconds on another that performs at 10MB/sec.

Comparing both results when comparing a 10sec run versus a 100sec run. This huge difference of running time can hide or reveal various unexpected events like a crontab running in background. Another annoyance is the unpredictability of the required time to run a particular test on a set of non-similar servers.

Fixing the time for a test answer the question "How much data can I process in this amount of time ?" instead of "How much time do I need to process this amount of data ?"

The benchmarking tools have to support time-based benchmarks.


Do no trust humans
------------------
Automation is a key element on the success of a good benchmark suite. Benchmark tools are usually offering various options and usage.
Selecting or missing a particular option could totally change the meaning of a test.

In some storage testing tools, if you forget to disable the use of the Linux cache, you have a great chance of testing more your memory than your disk.
If you are not aware of this behaviour or if you missed the setting, the interpretation of results could be very misleading.

Humans are weak machines, even if you read something wrong, your brain with make you read what you expected to read more than the mistake.

A great example of this effect is shown in the following images:

.. image:: images/find_the_8.jpg

.. image:: images/spelling-test.png

To avoid any human mistake, having a tool that runs automatically a set of defined commands is an important protection against any misuse of tools leading to wrong results.


Kill any source of doubts on software
-------------------------------------
Mastering your software configuration is required to get consistency over time and systems. Trying to estimate the performance of a given hardware requires the benchmark tool to be the sole one using a particular resource. The more processes will use this resource at the same time as the benchmark the less reliable will be the result. 

It’s pretty obvious that performing some rsync/logrotate/database IOs while trying to estimate disk’s performance isn’t a good way to get a coherent result. Those example are pretty obvious, but at the time you run your benchmark, it could be a pretty complicated being 100% sure that not a single non-expected task ran. On an infrastructure which is in production, this could turn into a complex task disabling all possible sources of annoyance.

The way to go is embedding all required tools and automation scripts into your own live operating system. The easiest way to get a clean operating system for a benchmark, is to generate one with the minimum dependencies. It’s almost like creating a minimal system (like debootstrap on debian), install the benchmarking tools you need, no graphic server and for sure, no crontab at all. Once this minimal system is setup, create a ramfs with it and boot on it with your favourite bootloader (pxelinux, extlinux, grub, …). This steps are done automatically by edeploy.

Having an under-control operating system that will be the same over servers and time remove any possible doubt of a background process running at the same time as your benchmark. It become possible running the benchmark in a controlled fashion on an already installed server. If you have any doubt of a particular hardware, reboot the server in this under-control operating system, perform the benchmark and voilà.


Results should not be stored without context
--------------------------------------------
Keeping the hardware description/configuration attached to your performance results is an efficient way to “remember” what was the context. It could be used to determine that a particular under-performance could be linked to a hardware change or configuration.

The more details about your hardware you have, the easier it will be to determine the link between a change and a performance issue/increase.


Tools used in AHC
=================

CPU & Memory Benchmarking
-------------------------
The Sysbench project offer a single interface to compute both CPU computing power and memory bandwidth. Its main advantages are a lightweight source code, a GPL licensing, a threading option and a time based mode.

This benchmark does not test all features and instructions the CPU have and this is not the objective to do it neither. Sysbench reports a number that represents a global level of performance. This number doesn’t really have a unit humanly understandable,it is much more like a relative performance indicator.

About the memory module of Sysbench, it performs IOs of a given block size to the main memory. It’s pretty straightforward to understand. The result of this benchmark is a memory bandwidth in MB/sec reported during a constant time.


Storage Benchmarking
--------------------
When thinking about storage benchmarking tools, fio comes immediately in mind. Mainly developed under the GPL license by Jens Axboe (Linux Kernel Maintainer of the Block Layer) , this tool is by far the most versatile tool I’m aware of. As we try to estimate the performance of the hardware by itself, removing the filesystem layer is mandatory.

Filesystems are complex beasts that have various optimization and behaviours that are useful for users but could hide some defects or introduced non desired latencies. The more software on the data path, the more complex is the analysis of the results. Making the same test on two different filesystems would lead to pretty different results. As we want to be as clause a possible to the hardware, it’s important to remove this source of possible annoyance.

Fio’s ability to perform IOs at the block level is a very interesting feature here. Fio can be scripted to perform the exact IO pattern you need while keeping under control the time you spend on your run and ensuring that it runs without any cache Layer from the Linux Kernel (O_DIRECT).


Network Benchmarking
--------------------
The Netperf project, under a BSD-like license, is clearly one of the most known and used tool over the Linux world. It provides a very simple command line, a port based pairing, TCP and UDP support and up to 20 different scenario. This tool is used to report the network bandwidth or latencies that a set of servers can generated simultaneously. The performance is expressed in Gbit/sec or messages per seconds.


Standalone benchmarking
=======================

Concept
-------
When delivering a new platform, you need to check every single server by its own with the minimum dependencies to start this task. The standalone mode of AHC is made for testing local components (storage, cpu, memory) of a given server. It will inspect them one by one to provide a detailed view of their sanity and the resulting performance.


Building AHC
------------
Building AHC requires using eDeploy and select a particular Linux distribution like Debian|Ubuntu or Redhat|Centos.

A simple command is enough to build it like :

* for debian :

::

 make health-img SERV=<ip_of_http_server>

* for Redhat : 

::

 make health-img SERV=<ip_of_http_server> DVER=RH7.0 DIST=redhat ISO_PATH=<path_to_rhel-server-7.0-x86_64-dvd.iso> RHN_USERNAME='rhn_user@domain.com' RHN_PASSWORD='rhn_password'

This build process generates a bootable disk image like *health-RH7.0-1.6.0.img* but also a kernel and a ramfs named *health.pxe*. It is so possible to boot AHC by using an USB key or PXE.

The SERV= option allow you to define on which server the benchmark results will be uploaded.

Using AHC with an USB key
-------------------------
The USB key is featuring a VFAT partition to save results. After the benchmarking, plugging the USB key back to your computer will expose the files from the VFAT partition.

Using AHC with a PXE booting
----------------------------
When using pxelinux, adding a simple entry in your pxelinux configuration is enough to make your server booting on AHC.

A typical configuration file looks like :

::

 LABEL health
 KERNEL vmlinuz-3.10.0-123.el7.x86_64
 APPEND initrd=health.pxe SERV=192.168.1.1 IP=all:dhcp SESSION=install ONSUCCESS=halt ONFAILURE=reboot


Boot options
------------

===================  ============================================================
Variable Name                         Role
===================  ============================================================
SERV                 IP address of the eDeploy server URL
HTTP_PATH            Path to access the upload.py (HTTP_PATH/upload.py)
HTTP_PORT            HTTP Port to contact the eDeploy server
ONSUCCESS            Action to take upon successful installation (kexec\|reboot\|halt\|console)
ONFAILURE            Action to take upon failed installation (console\|halt)
UPLOAD_LOG           Boolean. Upload log file on eDeploy server
VERBOSE              Boolean. Enable the verbose mode
DEBUG                Boolean. Enable debug mode (start a ssh_server for further access)
IP                   A list of network device configuration (see below for details)
SESSION              Define a session name to name subdirectories when uploading results
===================  ============================================================

**Note**: The IP= option is composed of a coma separated list of interfaces and
their configuration like <netdev>:<config>,<othernetdev>:<config>.
The netdev represent the network device from the linux point of view like eth0.
Two special values exists :
- other : to match all interfaces not listed in this list
- all : to match all interfaces

The config options are:
- none (no IP configurtion at all)
- dhcp
- <CIDR address>

The address is under the CIDR notation like 192.168.0.1/24.
Some typical IP invocations could be:
- IP=eth0:dhcp,other=none
- IP=eth1:192.168.1.1/24,other:none
- IP=all:none

By default, all intefaces make DHCP requests with 'IP=all:dhcp'


Distributed benchmarking
========================

Concept
-------
Testing network performance requires cooperation from multiple hosts to gain a simultaneous load on the network interconnect. Measuring the impact of the CPU load from virtual machines on hypervisors requires the same kind of cooperation. The distributed mode of AHC (DAHC) can describe and orchestrate such benchmarks.

Building DAHC
-------------
Building AHC requires using eDeploy and select a particular Linux distribution like Debian|Ubuntu or Redhat|Centos.

A simple command is enough to build it like :

* for debian :

::

 make health-img CMDLINE="console=ttyS0,115200" RBENCH=<ip_of_benchmark_server>

* for Redhat :

::

 make health-img DVER=RH7.0 DIST=redhat ISO_PATH=<path_to_rhel-server-7.0-x86_64-dvd.iso> RHN_USERNAME='rhn_user@domain.com' RHN_PASSWORD='rhn_password' CMDLINE="console=ttyS0,115200" RBENCH=<ip_of_benchmark_server>

In addition of a standalone AHC, you can define the IP address of the host running the health-server.py script. If you intend to run DAHC in virtual machines, it could be useful to put the Linux console on the serial line to ease the log reporting at boot time.

This build process generates a bootable disk image like *health-RH7.0-1.6.0.img* but also a kernel and a ramfs named *health.pxe*. It is so possible to boot AHC by using an disk image or PXE.

Using DAHC with the disk image
------------------------------
The disk image is usually used with virtual machines. The default file format is RAW but could be easily converted in QCOW2 if required.


Using DAHC with a PXE booting
-----------------------------
When using pxelinux, adding a simple entry in your pxelinux configuration is enough to make your server booting on AHC.

A typical configuration file looks like :

::

 LABEL health
 KERNEL vmlinuz-3.10.0-123.el7.x86_64
 APPEND initrd=health.pxe SERV=192.168.1.1 IP=all:dhcp SESSION=install ONSUCCESS=halt ONFAILURE=reboot RBENCH=<ip_of_benchmark_server>


Boot options
------------

The following options in addition on the standalone mode :

===================  ============================================================
Variable Name                         Role
===================  ============================================================
RBENCH               IP of the server running health-server.py
===================  ============================================================


**Note**: The RBENCH= option can be overloaded by using cloud-init. If the host is running under an hypervisor, the boot process will try to find a cloud-init configuration.
To consider the user-data as valid, it shall have the **#EDEPLOYMAGIC** keyword followed by a set of bash variables and their values.

A typical configuration looks like:

::
 
      #EDEPLOYMAGIC
      RBENCH=<ip_of_bench_server>

