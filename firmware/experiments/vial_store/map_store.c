// SPDX-License-Identifier: GPL-2.0-or-later
#include "map_store.h"

#define MAGIC UINT32_C(0x314d5641) // bytes "AVM1"
#define SCHEMA UINT32_C(0x01040e08) // format 1, layers 4, rows 14, cols 8
#define COMMIT UINT32_C(0x54494d43) // bytes "CMIT", programmed last
#define ERASED UINT32_C(0xffffffff)

_Static_assert(sizeof(alloy_map_store) <= 8, "store must not shadow the map");
_Static_assert(ALLOY_MAP_HEADER_BYTES + ALLOY_MAP_BYTES <= ALLOY_MAP_BANK_BYTES, "bank too small");

static bool read_word(uint8_t bank, uint16_t offset, uint32_t *word) {
    return alloy_map_io_read((uint16_t)(bank * ALLOY_MAP_BANK_BYTES + offset), word);
}

static bool program_word(uint8_t bank, uint16_t offset, uint32_t word) {
    return alloy_map_io_program((uint16_t)(bank * ALLOY_MAP_BANK_BYTES + offset), word);
}

// Reflected CRC-32/ISO-HDLC, bytes in stored order, initial/final xor ffffffff.
// Integrity check, not authentication or proof against arbitrary corruption.
static uint32_t crc_word(uint32_t crc, uint32_t word) {
    for (uint8_t byte = 0; byte < 4; ++byte) {
        crc ^= (uint8_t)word;
        word >>= 8;
        for (uint8_t bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ ((crc & 1u) ? UINT32_C(0xedb88320) : 0);
        }
    }
    return crc;
}

static uint16_t keycode(uint32_t word, uint8_t half) {
    word >>= half * 16u;
    return (uint16_t)(((word & 0xffu) << 8) | ((word >> 8) & 0xffu));
}

static bool allowed_word(uint16_t offset, uint32_t word) {
    return alloy_map_keycode_allowed(offset / 2, keycode(word, 0)) &&
           alloy_map_keycode_allowed(offset / 2 + 1, keycode(word, 1));
}

static alloy_map_result check_bank(uint8_t bank, uint32_t marker, uint32_t *generation) {
    uint32_t word, crc = ERASED, stored_crc;
    if (!read_word(bank, 28, &word)) return ALLOY_MAP_IO_ERROR;
    if (word != marker) return ALLOY_MAP_INVALID;
    for (uint16_t offset = 0; offset < 12; offset += 4) {
        if (!read_word(bank, offset, &word)) return ALLOY_MAP_IO_ERROR;
        if ((offset == 0 && word != MAGIC) || (offset == 4 && word != SCHEMA)) return ALLOY_MAP_INVALID;
        if (offset == 8) *generation = word;
        crc = crc_word(crc, word);
    }
    if (!read_word(bank, 12, &stored_crc)) return ALLOY_MAP_IO_ERROR;
    for (uint16_t offset = 16; offset < 28; offset += 4) {
        if (!read_word(bank, offset, &word)) return ALLOY_MAP_IO_ERROR;
        if (word != ERASED) return ALLOY_MAP_INVALID;
    }
    for (uint16_t offset = 0; offset < ALLOY_MAP_BYTES; offset += 4) {
        if (!read_word(bank, ALLOY_MAP_HEADER_BYTES + offset, &word)) return ALLOY_MAP_IO_ERROR;
        if (!allowed_word(offset, word)) return ALLOY_MAP_INVALID;
        crc = crc_word(crc, word);
    }
    return (crc ^ ERASED) == stored_crc ? ALLOY_MAP_OK : ALLOY_MAP_INVALID;
}

static alloy_map_result io_failure(alloy_map_store *store) {
    store->mounted = false;
    return ALLOY_MAP_IO_ERROR;
}

static bool ready(const alloy_map_store *store) {
    return store && store->mounted && store->bank >= -1 && store->bank < ALLOY_MAP_BANKS;
}

alloy_map_result alloy_map_mount(alloy_map_store *store) {
    if (!store) return ALLOY_MAP_INVALID;
    store->mounted = false;
    store->bank = -1;
    store->generation = 0;
    uint32_t a = 0, b = 0;
    const alloy_map_result ra = check_bank(0, COMMIT, &a);
    const alloy_map_result rb = check_bank(1, COMMIT, &b);
    if (ra == ALLOY_MAP_IO_ERROR || rb == ALLOY_MAP_IO_ERROR) return ALLOY_MAP_IO_ERROR;
    if (ra == ALLOY_MAP_OK && rb == ALLOY_MAP_OK) {
        // Each successful transaction alternates banks and increments by one.
        // Reject equal/nonadjacent generations rather than guess on corruption.
        if ((uint32_t)(a - b) == 1u) store->bank = 0;
        else if ((uint32_t)(b - a) == 1u) store->bank = 1;
        else return ALLOY_MAP_AMBIGUOUS;
    } else if (ra == ALLOY_MAP_OK) store->bank = 0;
    else if (rb == ALLOY_MAP_OK) store->bank = 1;
    if (store->bank >= 0) store->generation = store->bank == 0 ? a : b;
    store->mounted = true;
    return ALLOY_MAP_OK;
}

static bool map_word(const alloy_map_store *store, uint16_t offset, uint32_t *word) {
    if (store->bank >= 0) return read_word((uint8_t)store->bank, ALLOY_MAP_HEADER_BYTES + offset, word);
    const uint16_t a = alloy_map_default_keycode(offset / 2);
    const uint16_t b = alloy_map_default_keycode(offset / 2 + 1);
    *word = ((uint32_t)(a >> 8)) | ((uint32_t)(a & 0xffu) << 8) |
            ((uint32_t)(b >> 8) << 16) | ((uint32_t)(b & 0xffu) << 24);
    return true;
}

alloy_map_result alloy_map_get(alloy_map_store *store, uint16_t index, uint16_t *code) {
    if (!code || index >= ALLOY_MAP_KEYS) return ALLOY_MAP_INVALID;
    if (!ready(store)) return ALLOY_MAP_NOT_MOUNTED;
    uint32_t word;
    if (!map_word(store, (uint16_t)((index / 2) * 4), &word)) return io_failure(store);
    *code = keycode(word, index & 1u);
    return ALLOY_MAP_OK;
}

static uint32_t patched(uint32_t word, uint16_t at, uint16_t offset, const uint8_t *bytes, uint8_t length) {
    for (uint8_t i = 0; i < 4; ++i) {
        if (at + i >= offset && at + i - offset < length) {
            const uint32_t shift = 8u * i;
            word = (word & ~(UINT32_C(0xff) << shift)) | ((uint32_t)bytes[at + i - offset] << shift);
        }
    }
    return word;
}

alloy_map_result alloy_map_patch(alloy_map_store *store, uint16_t offset,
                                 const uint8_t *bytes, uint8_t length) {
    if (offset > ALLOY_MAP_BYTES || length > ALLOY_MAP_MAX_PATCH || length > ALLOY_MAP_BYTES - offset ||
        (length && !bytes)) return ALLOY_MAP_INVALID;
    if (!ready(store)) return ALLOY_MAP_NOT_MOUNTED;
    if (!length) return ALLOY_MAP_OK;
    if (store->bank >= 0) {
        uint32_t generation;
        if (check_bank((uint8_t)store->bank, COMMIT, &generation) != ALLOY_MAP_OK ||
            generation != store->generation) return io_failure(store);
    }
    bool changed = false;
    // Validate the entire candidate before erasing anything. Disabled positions
    // and unsupported keycodes are the adapter's responsibility, never bypassed.
    for (uint16_t at = 0; at < ALLOY_MAP_BYTES; at += 4) {
        uint32_t old;
        if (!map_word(store, at, &old)) return io_failure(store);
        const uint32_t word = patched(old, at, offset, bytes, length);
        if (!allowed_word(at, word)) return ALLOY_MAP_INVALID;
        changed |= word != old;
    }
    if (!changed) return ALLOY_MAP_OK; // no wear for a no-op
    const uint8_t target = store->bank == 0 ? 1 : 0;
    const uint32_t next = store->generation + 1u;
    if (!alloy_map_io_erase(target)) return io_failure(store);
    for (uint16_t at = 0; at < ALLOY_MAP_BANK_BYTES; at += 4) {
        uint32_t word;
        if (!read_word(target, at, &word) || word != ERASED) return io_failure(store);
    }
    if (!program_word(target, 0, MAGIC) || !program_word(target, 4, SCHEMA) ||
        !program_word(target, 8, next)) return io_failure(store);
    uint32_t crc = crc_word(crc_word(crc_word(ERASED, MAGIC), SCHEMA), next);
    for (uint16_t at = 0; at < ALLOY_MAP_BYTES; at += 4) {
        uint32_t word;
        if (!map_word(store, at, &word)) return io_failure(store);
        word = patched(word, at, offset, bytes, length);
        crc = crc_word(crc, word);
        if (!program_word(target, ALLOY_MAP_HEADER_BYTES + at, word)) return io_failure(store);
    }
    if (!program_word(target, 12, crc ^ ERASED)) return io_failure(store);
    uint32_t observed;
    // Readback before committing; marker is still erased. Never erase the old
    // bank after success: it remains the fallback until the next transaction.
    if (check_bank(target, ERASED, &observed) != ALLOY_MAP_OK || observed != next ||
        !program_word(target, 28, COMMIT) ||
        check_bank(target, COMMIT, &observed) != ALLOY_MAP_OK || observed != next) return io_failure(store);
    store->bank = (int8_t)target;
    store->generation = next;
    return ALLOY_MAP_OK;
}
