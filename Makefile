BINDIR ?= /usr/bin
DESKTOPDIR ?= /usr/share/applications

install:
	mkdir -p $(DESTDIR)$(BINDIR)
	install -m0755 yamp.py $(DESTDIR)$(BINDIR)/yamp
	install -m 0644 yamp.desktop $(DESTDIR)$(DESKTOPDIR)
