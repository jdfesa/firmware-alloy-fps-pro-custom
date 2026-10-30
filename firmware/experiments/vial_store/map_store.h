// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <stdbool.h>
#include <stdint.h>

// HOST-TESTED EXPERIMENT ONLY. These are virtual offsets, NOT SN32F26x geometry
// or approved addresses. No physical backend or QMK target is provided.
enum {
    ALLOY_MAP_BYTES = 896,
    ALLOY_MAP_KEYS = ALLOY_MAP_BYTES / 2,
    ALLOY_MAP_BANK_BYTES = 1024,
    ALLOY_MAP_BANKS = 2,
    ALLOY_MAP_HEADER_BYTES = 32,
    ALLOY_MAP_MAX_PATCH = 28,
};

typedef enum {
    ALLOY_MAP_OK,
    ALLOY_MAP_INVALID,
    ALLOY_MAP_IO_ERROR,
    ALLOY_MAP_NOT_MOUNTED,
    ALLOY_MAP_AMBIGUOUS,
} alloy_map_result;

typedef struct {
    uint32_t generation;
    int8_t bank; // -1: compiled defaults; otherwise 0 or 1
    bool mounted;
} alloy_map_store;

// Backend contract: exclusive, synchronous, no reentry; read words are LE.
// Program changes only 1->0 in one aligned word; erase affects only one bank.
// Any failure may have partially modified that word/bank. Reads must report
// failures, not fabricate erased bytes. See docs/vial-map-store.md for limits.
// Only the test harness implements these functions, using simulated storage.
bool alloy_map_io_read(uint16_t offset, uint32_t *word);
bool alloy_map_io_program(uint16_t offset, uint32_t word);
bool alloy_map_io_erase(uint8_t bank);
uint16_t alloy_map_default_keycode(uint16_t index);
bool alloy_map_keycode_allowed(uint16_t index, uint16_t keycode);

alloy_map_result alloy_map_mount(alloy_map_store *store);
alloy_map_result alloy_map_get(alloy_map_store *store, uint16_t index, uint16_t *code);
// VIA byte order (big-endian keycodes), including odd byte offsets. A single
// call is atomic in the simulated fault model, NOT a multi-packet GUI upload.
// After an I/O failure, remount before further reads/writes; commit may have
// reached storage even if its acknowledgement was lost.
alloy_map_result alloy_map_patch(alloy_map_store *store, uint16_t offset,
                                 const uint8_t *bytes, uint8_t length);
