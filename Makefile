SDIR=/root/edeploy
TOP=/var/lib/debootstrap
VERS=D7-F.1.0.0

SRC=base
DST=pxe
IMG=initrd.pxe
ROLES=swift_storage

INST=$(TOP)/install/$(VERS)
META=$(TOP)/metadata/$(VERS)

$(IMG): base.done init
	./pxe.install $(INST)/base $(INST)/pxe $(IMG)

base.done: base.install
	./base.install $(INST)/base
	touch base.done

dist:
	tar zcvf ../edeploy.tgz Makefile init README.rst base.install

clean:
	-rm -rf *~ *.done
