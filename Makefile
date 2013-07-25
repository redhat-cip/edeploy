DESTDIR=
PROG_NAME=edeploy
SERVER_DIR=server
CONFIG_DIR=config
BUILD_DIR=build

WWW_DIR=$(DESTDIR)/usr/lib/cgi-bin/
WWW_CONFIG_DIR=$(WWW_DIR)/config
ETC_DIR=$(DESTDIR)/etc/
SHARE_BUILD_DIR=$(DESTDIR)/usr/share/$(PROG_NAME)/$(BUILD_DIR)

install-www:
	mkdir -p $(WWW_DIR) && 	chmod 755 $(WWW_DIR)
	mkdir -p $(WWW_CONFIG_DIR) && chmod 755 $(WWW_CONFIG_DIR)
	mkdir -p $(ETC_DIR) && chmod 755 $(ETC_DIR)
	install -m 644 $(SERVER_DIR)/edeploy.conf $(ETC_DIR)/
	install -m 755 $(SERVER_DIR)/upload.py $(SERVER_DIR)/matcher.py $(WWW_DIR)/
	install -m 644 $(CONFIG_DIR)/* $(WWW_CONFIG_DIR)/
	chmod a+rw $(WWW_CONFIG_DIR)/state
	sed -i -e "s/^CONFIGDIR=.*/CONFIGDIR=$(WWW_CONFIG_DIR)/" $(ETC_DIR)/edeploy.conf

install-build:
	mkdir -p $(SHARE_BUILD_DIR) && chmod 755 $(SHARE_BUILD_DIR)
	cp -a $(BUILD_DIR)/* $(SHARE_BUILD_DIR)/
