# This is free software, licensed under the Apache License, Version 2.0
#
# Copyright (C) 2024 Maizil <maizilpc7@gmail.com>

include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI Support for Telebot-Radius.
LUCI_DEPENDS:=+luci +python3 +python3-pip
LUCI_DESCRIPTION:=Telegram Bot for monitoring RADIUS server.
LUCI_MAINTAINER:=Maizil <maizilpc7@gmail.com>

PKG_MAINTAINER:=Maizil <maizilpc7@gmail.com>
PKG_VERSION:=2.3
PKG_RELEASE:=beta
PKG_LICENSE:=Apache-2.0
PKG_ARCH:=all

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature