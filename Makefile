SRC=base
DST=pxe
IMG=initrd.pxe

$(IMG): base.done init
	./pxe.install $(SRC) $(DST) $(IMG)

base.done: base.install
	./base.install base
	touch base.done

dist:
	tar zcvf ../edeploy.tgz Makefile init README.rst base.install

clean:
	-rm -rf $(DST) $(IMG) *~ *.done

distclean: clean
	-rm -rf $(DST) $(IMG) *~ *.done
