CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic
PKGS = gtk+-3.0 libpulse libpulse-mainloop-glib

all: volume_slider.so

volume_slider.so: volume_slider.c waybar_cffi_module.h
	$(CC) $(CFLAGS) -fPIC -shared -o $@ volume_slider.c \
		$$(pkg-config --cflags --libs $(PKGS)) -lm

clean:
	rm -f volume_slider.so

.PHONY: all clean
