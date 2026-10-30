// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
#include <stdbool.h>
enum { PS_PAGE=64, PS_BANK=1024, PS_BYTES=896, PS_KEYS=448, PS_PAGES=32 };
typedef struct { uint32_t generation; int8_t bank; bool mounted; } ps_store;
// Relative offsets ONLY; physical mapping belongs to flash_backend.c.
bool ps_read32(uint16_t offset, uint32_t *word);
// Replace exactly one page, including erase; a failure may damage that page.
// The caller never replaces any page in the currently active bank.
bool ps_replace(uint8_t page, const uint32_t words[16]);
uint16_t ps_default(uint16_t index);
bool ps_allowed(uint16_t index, uint16_t code);
bool ps_mount(ps_store *s);
uint16_t ps_get(const ps_store *s, uint16_t index);
bool ps_patch(ps_store *s, uint16_t offset, const uint8_t *data, uint8_t length);
