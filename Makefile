SDIR=/root/edeploy
TOP=/var/lib/debootstrap
VERS=D7-F.1.0.0
DIST=wheezy

SRC=base
DST=pxe
IMG=initrd.pxe

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

all: $(INST)/$(IMG) mysql.done

$(INST)/$(IMG): base.done init
	./pxe.install $(INST)/base $(INST)/pxe $(IMG)

base.done: base.install policy-rc.d edeploy
	./base.install $(INST)/base $(DIST)
	cp policy-rc.d edeploy $(INST)/base/usr/sbin/
	touch base.done

openstack.done: openstack.install base.done
	./openstack.install $(INST)/base $(INST)/openstack
	touch openstack.done

mysql.done: mysql.install base.done
	./mysql.install $(INST)/base $(INST)/mysql
	touch mysql.done

dist:
	tar zcvf ../edeploy.tgz Makefile init README.rst *.install

clean:
	-rm -rf *~ *.done
