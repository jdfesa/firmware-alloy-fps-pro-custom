# SPDX-License-Identifier: GPL-2.0-or-later
RAW_ENABLE = yes
# The jumploader owns cold Escape recovery; disable the app's duplicate route.
BOOTMAGIC_ENABLE = no
SRC += $(KEYMAP_PATH)/protocol.c $(KEYMAP_PATH)/page_store.c $(KEYMAP_PATH)/flash_backend.c
LDFLAGS += -Wl,-T,$(KEYMAP_PATH)/map_reserve.ld
