SDIR=/root/edeploy
TOP=/var/lib/debootstrap
VERS=D7-F.1.0.0

SRC=base
DST=pxe
IMG=initrd.pxe
ROLES=swift_storage

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

all: $(INST)/$(IMG) openstack.done

$(INST)/$(IMG): base.done init
	./pxe.install $(INST)/base $(INST)/pxe $(IMG)

base.done: base.install
	./base.install $(INST)/base
	touch base.done

openstack.done: openstack.install base.done
	./openstack.install $(INST)/base $(INST)/openstack
	touch openstack.done

dist:
	tar zcvf ../edeploy.tgz Makefile init README.rst *.install

clean:
	-rm -rf *~ *.done
