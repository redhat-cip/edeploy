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

SDIR=/root/edeploy
TOP=/var/lib/debootstrap
VERS=D7-F.1.0.0
DIST=wheezy

SRC=base
DST=pxe
IMG=initrd.pxe
ARCH=amd64
export PATH := /sbin:/bin::$(PATH)
SERV:=10.66.6.10
PYDIR=../src
PYSERVERDIR=../server

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

all: $(INST)/$(IMG) $(INST)/mysql.done

pxe $(INST)/$(IMG): $(INST)/base.done init pxe.install $(PYDIR)/detect.py $(PYDIR)/hpacucli.py $(PYSERVERDIR)/matcher.py $(PYDIR)/diskinfo.py $(PYDIR)/ipmi.py
	./pxe.install $(INST)/base $(INST)/pxe $(IMG) $(VERS)

img: pxe
	./img.install $(INST)/base $(IMG) $(VERS) $(INST) $(SERV)

base $(INST)/base.done: base.install policy-rc.d edeploy
	ARCH=$(ARCH) ./base.install $(INST)/base $(DIST) $(VERS)
	cp -p policy-rc.d edeploy $(INST)/base/usr/sbin/
	touch $(INST)/base.done

cloud $(INST)/cloud.done: cloud.install $(INST)/base.done
	./cloud.install $(INST)/base $(INST)/cloud $(VERS)
	touch $(INST)/cloud.done

devstack $(INST)/devstack.done: devstack.install $(INST)/cloud.done
	./devstack.install $(INST)/cloud $(INST)/devstack $(DIST) $(VERS)
	touch $(INST)/devstack.done

openstack $(INST)/openstack.done: openstack.install $(INST)/base.done
	./openstack.install $(INST)/base $(INST)/openstack $(VERS)
	touch $(INST)/openstack.done

openstack-controller $(INST)/openstack-controller.done: openstack-controller.install $(INST)/base.done
	./openstack-controller.install $(INST)/base $(INST)/openstack-controller $(VERS)
	touch $(INST)/openstack-controller.done

openstack-compute $(INST)/openstack-compute.done: openstack-compute.install $(INST)/base.done
	./openstack-compute.install $(INST)/base $(INST)/openstack-compute $(VERS)
	touch $(INST)/openstack-compute.done

openstack-swift-proxy $(INST)/openstack-swift-proxy.done: openstack-swift-proxy.install $(INST)/base.done
	./openstack-swift-proxy.install $(INST)/base $(INST)/openstack-swift-proxy $(VERS)
	touch $(INST)/openstack-swift-proxy.done

openstack-swift-storage $(INST)/openstack-swift-storage.done: openstack-swift-storage.install $(INST)/base.done
	./openstack-swift-storage.install $(INST)/base $(INST)/openstack-swift-storage $(VERS)
	touch $(INST)/openstack-swift-storage.done

mysql $(INST)/mysql.done: mysql.install $(INST)/base.done
	./mysql.install $(INST)/base $(INST)/mysql $(VERS)
	touch $(INST)/mysql.done

galera $(INST)/galera.done: galera.install $(INST)/base.done
	./galera.install $(INST)/base $(INST)/galera $(VERS)
	touch $(INST)/galera.done

haproxy $(INST)/haproxy.done: haproxy.install $(INST)/base.done
	./haproxy.install $(INST)/base $(INST)/haproxy $(VERS)
	touch $(INST)/haproxy.done

ceph $(INST)/ceph.done: ceph.install $(INST)/base.done
	./ceph.install $(INST)/base $(INST)/ceph $(VERS)
	touch $(INST)/ceph.done

test: $(INST)/$(IMG)
	cd ../tests/tftpboot/; ln -sf $(INST)/base/boot/vmlinuz* vmlinuz; ln -sf $(INST)/initrd.pxe initrd;
	cd ../tests; ./run_kvm.sh $(TOP)

dist:
	tar zcvf ../edeploy.tgz Makefile init README.rst *.install edeploy update-scenario.sh *.py

clean:
	-rm -f *~ $(INST)/*.done

distclean: clean
	-rm -rf $(INST)/*
