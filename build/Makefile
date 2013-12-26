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

# Exporting ALL variables to other childs
.EXPORT_ALL_VARIABLES:

MAKEFILE_DIR=$(shell pwd)
SDIR=/root/edeploy
TOP=/var/lib/debootstrap
DVER=D7
PVER=H
REL=1.0.0
VERSION:=$(PVER).$(REL)
VERS=$(DVER)-$(VERSION)
DIST=wheezy

SRC=base
DST=pxe
IMG=initrd.pxe
HEALTH_IMG=health.pxe
ARCH=amd64
export PATH := /sbin:/bin::$(PATH)
SERV:=10.66.6.10
HSERV:=10.66.6.10
DEBUG=1
UPLOAD_LOG:=0
PYDIR=../src
PYSERVERDIR=../server

LOAD=5
HTTP=
MAKEFILE_TARGET=$(MAKECMDGOALS)
CURRENT_TARGET=$@
export MAKEFILE_TARGET
export CURRENT_TARGET

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

TEST_ROLE:=mysql

DEPS = $(PYDIR)/detect.py $(PYDIR)/hpacucli.py $(PYDIR)/megacli.py $(PYSERVERDIR)/matcher.py $(PYDIR)/diskinfo.py $(PYDIR)/ipmi.py $(PYDIR)/infiniband.py

all: $(INST)/$(IMG) $(INST)/mysql.done

health-check: $(INST)/base.done init.health init.common health-check.install $(DEPS)
	ENABLE_IB=y ENABLE_MELLANOX=n ./health-check.install $(INST)/base $(INST)/health-check $(HEALTH_IMG) $(VERS) $(DEBUG)

health-img: health-check
	./img.install $(INST)/base $(HEALTH_IMG) $(VERS) $(INST) $(SERV) $(HSERV) $(DEBUG) health

pxe $(INST)/$(IMG): $(INST)/base.done init init.common pxe.install $(DEPS)
	ENABLE_IB=y ENABLE_MELLANOX=n ./pxe.install $(INST)/base $(INST)/pxe $(IMG) $(VERS) $(DEBUG)

img: $(INST)/$(IMG)
	./img.install $(INST)/base $(IMG) $(VERS) $(INST) $(SERV) $(HSERV) $(DEBUG)

base: $(INST)/base.done
$(INST)/base.done: base.install policy-rc.d edeploy
	./base.install $(INST)/base $(DIST) $(VERS)
	touch $(INST)/base.done

deploy: $(INST)/deploy.done
$(INST)/deploy.done: deploy.install $(INST)/base.done
	./deploy.install $(INST)/base $(INST)/deploy $(VERS)
	touch $(INST)/deploy.done

#sample: $(INST)/sample.done
#$(INST)/sample.done: sample.install $(INST)/base.done
#	./sample.install $(INST)/base $(INST)/sample $(VERS)
#	touch $(INST)/sample.done

cloud: $(INST)/cloud.done
$(INST)/cloud.done: cloud.install $(INST)/base.done
	./cloud.install $(INST)/base $(INST)/cloud $(VERS)
	touch $(INST)/cloud.done

devstack: $(INST)/devstack.done
$(INST)/devstack.done: devstack.install $(INST)/cloud.done
	./devstack.install $(INST)/cloud $(INST)/devstack $(DIST) $(VERS)
	touch $(INST)/devstack.done

openstack-common: $(INST)/openstack-common.done
$(INST)/openstack-common.done: openstack-common.install $(INST)/base.done
	./openstack-common.install $(INST)/base $(INST)/openstack-common $(VERS)
	touch $(INST)/openstack-common.done

openstack-full: $(INST)/openstack-full.done
$(INST)/openstack-full.done: openstack-full.install $(INST)/openstack-common.done
	./openstack-full.install $(INST)/openstack-common $(INST)/openstack-full $(VERS)
	touch $(INST)/openstack-full.done

openstack-swift-proxy: $(INST)/openstack-swift-proxy.done
$(INST)/openstack-swift-proxy.done: openstack-swift-proxy.install $(INST)/openstack-common.done
	./openstack-swift-proxy.install $(INST)/openstack-common $(INST)/openstack-swift-proxy $(VERS)
	touch $(INST)/openstack-swift-proxy.done

openstack-swift-storage: $(INST)/openstack-swift-storage.done
$(INST)/openstack-swift-storage.done: openstack-swift-storage.install $(INST)/openstack-common.done
	./openstack-swift-storage.install $(INST)/openstack-common $(INST)/openstack-swift-storage $(VERS)
	touch $(INST)/openstack-swift-storage.done

mysql: $(INST)/mysql.done
$(INST)/mysql.done: mysql.install $(INST)/base.done
	./mysql.install $(INST)/base $(INST)/mysql $(VERS)
	touch $(INST)/mysql.done

ceph: $(INST)/ceph.done
$(INST)/ceph.done: ceph.install $(INST)/base.done
	./ceph.install $(INST)/base $(INST)/ceph $(VERS)
	touch $(INST)/ceph.done

docker: $(INST)/docker.done
$(INST)/docker.done: docker.install $(INST)/base.done
	./docker.install $(INST)/base $(INST)/docker $(VERS)
	touch $(INST)/docker.done

puppet-master: $(INST)/puppet-master.done
$(INST)/puppet-master.done: puppet-master.install $(INST)/base.done
	./puppet-master.install $(INST)/base $(INST)/puppet-master $(VERS)
	touch $(INST)/puppet-master.done

server: $(INST)/chef-server.done
$(INST)/chef-server.done: chef-server.install $(INST)/base.done
	./chef-server.install $(INST)/base $(INST)/chef-server $(VERS)
	touch $(INST)/chef-server.done

health-test: health-check
	cd ../tests/tftpboot/; ln -sf $(INST)/base/boot/vmlinuz* vmlinuz; ln -sf $(INST)/health.pxe initrd;
	cd ../tests; ./run_kvm.sh $(TOP) health

test: $(INST)/$(IMG) $(TEST_ROLE)
	cd ../tests/tftpboot/; ln -sf $(INST)/base/boot/vmlinuz* vmlinuz; ln -sf $(INST)/initrd.pxe initrd;
	cd ../tests; ./run_kvm.sh $(TOP)

stress-http:
	cd ../tests; ./run_kvm.sh $(TOP) stress-http $(LOAD) $(HTTP)

benchmark $(INST)/benchmark.done: benchmark.install $(INST)/base.done
	ENABLE_IB=y ./benchmark.install $(INST)/base $(INST)/benchmark $(VERS)
	touch $(INST)/benchmark.done

dist:
	tar zcvf ../edeploy.tgz Makefile init init.common README.rst *.install edeploy update-scenario.sh *.py

clean:
	-rm -f *~ $(INST)/*.done

distclean: clean
	-rm -rf $(INST)/*

version:
	@echo "$(VERS)"

.PHONY: base img base cloud devstack openstack-common openstack-full mysql ceph docker puppet-master\
	server test stress-http benchmark dist clean distclean version
