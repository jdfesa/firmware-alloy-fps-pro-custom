// SPDX-License-Identifier: GPL-2.0-or-later
// Simulated storage only. Never linked into a keyboard firmware target.
#include "map_store.h"
#include "qmk_mock.h"
#include "test_keymap.h"
#include <assert.h>
#include <string.h>

uint8_t medium[ALLOY_MAP_BANKS * ALLOY_MAP_BANK_BYTES];
alloy_map_store store;
unsigned mutations, reads;
int fail_mutation = -1, fail_read = -1, torn = 0;
int lie_mutation = -1;
bool powered = true;

static void fault_reset(void) {
    mutations = reads = 0;
    fail_mutation = fail_read = lie_mutation = -1;
    powered = true;
}

void reset_medium(void) {
    memset(medium, 0xff, sizeof medium);
    memset(&store, 0, sizeof store);
    fault_reset();
}

bool alloy_map_io_read(uint16_t offset, uint32_t *word) {
    assert(offset % 4 == 0 && offset <= sizeof medium - 4 && word);
    if (!powered) return false;
    if ((int)reads++ == fail_read) { powered = false; return false; }
    *word = (uint32_t)medium[offset] | ((uint32_t)medium[offset + 1] << 8) |
            ((uint32_t)medium[offset + 2] << 16) | ((uint32_t)medium[offset + 3] << 24);
    return true;
}

bool alloy_map_io_program(uint16_t offset, uint32_t word) {
    assert(offset % 4 == 0 && offset <= sizeof medium - 4);
    if (!powered) return false;
    const int operation = (int)mutations++;
    const bool fail = operation == fail_mutation;
    if (operation == lie_mutation) return true;
    for (int bit = 0; bit < 32; ++bit) {
        const uint8_t mask = (uint8_t)(1u << (bit % 8));
        assert(!(word & (UINT32_C(1) << bit)) || (medium[offset + bit / 8] & mask));
        if ((!fail || bit < torn) && !(word & (UINT32_C(1) << bit))) medium[offset + bit / 8] &= (uint8_t)~mask;
    }
    if (fail) powered = false;
    return !fail;
}

bool alloy_map_io_erase(uint8_t bank) {
    assert(bank < ALLOY_MAP_BANKS);
    if (!powered) return false;
    const int operation = (int)mutations++;
    const bool fail = operation == fail_mutation;
    if (operation == lie_mutation) return true;
    const unsigned count = fail ? (unsigned)torn : ALLOY_MAP_BANK_BYTES;
    assert(count <= ALLOY_MAP_BANK_BYTES);
    memset(medium + bank * ALLOY_MAP_BANK_BYTES, 0xff, count);
    if (fail) powered = false;
    return !fail;
}

uint16_t alloy_map_default_keycode(uint16_t index) {
    assert(index < ALLOY_MAP_KEYS);
    return keymaps[index / 112][(index / 8) % 14][index % 8];
}

// Test policy, NOT a certified SonixQMK/Vial keycode translation layer.
// Base-map disabled positions cannot be enabled, including the five dead keys.
static bool basic(uint16_t code) {
    return code <= 0x73 || (code >= 0xe0 && code <= 0xe7);
}

bool alloy_map_keycode_allowed(uint16_t index, uint16_t code) {
    assert(index < ALLOY_MAP_KEYS);
    if (!alloy_map_default_keycode(index % 112)) return code == 0;
    if (basic(code)) return true;
    if (code >= 0x0100 && code <= 0x1fff) return basic(code & 0xffu);
    if (code >= 0x4000 && code <= 0x43ff) return basic(code & 0xffu);
    return code >= 0x5220 && code <= 0x5223;
}

int mount_map(void) { return alloy_map_mount(&store); }
int patch_map(uint16_t offset, const uint8_t *bytes, uint8_t length) {
    return alloy_map_patch(&store, offset, bytes, length);
}

void dump_map(uint8_t *out) {
    for (uint16_t index = 0; index < ALLOY_MAP_KEYS; ++index) {
        uint16_t code;
        assert(alloy_map_get(&store, index, &code) == ALLOY_MAP_OK);
        out[index * 2] = code >> 8;
        out[index * 2 + 1] = (uint8_t)code;
    }
}

// Native loops keep exhaustive cut tests fast and also run under ASan/UBSan.
// A fault affects only the selected word/bank, with no later operations until
// reboot. Tests cover every prefix bit of every program, every prefix byte of
// erase, every read failure, and a lost ACK after the complete commit word.
unsigned exercise_powercuts(void) {
    uint8_t initial[sizeof medium], old[ALLOY_MAP_BYTES], next[ALLOY_MAP_BYTES];
    const uint8_t edit[] = {0x00, 0x1d}; // change a used key to Z
    memcpy(initial, medium, sizeof initial);
    assert(mount_map() == ALLOY_MAP_OK);
    const int old_bank = store.bank;
    dump_map(old);
    fault_reset();
    assert(patch_map(34, edit, sizeof edit) == ALLOY_MAP_OK);
    const unsigned total_mutations = mutations, total_reads = reads;
    dump_map(next);
    assert(memcmp(old, next, sizeof old));
    unsigned cases = 0;
    for (unsigned operation = 0; operation < total_mutations + total_reads; ++operation) {
        const bool read_fault = operation >= total_mutations;
        const int variants = read_fault ? 1 : operation == 0 ? ALLOY_MAP_BANK_BYTES + 1 : 33;
        for (int progress = 0; progress < variants; ++progress) {
            memcpy(medium, initial, sizeof initial);
            fault_reset();
            assert(mount_map() == ALLOY_MAP_OK);
            fault_reset();
            if (read_fault) fail_read = (int)(operation - total_mutations);
            else fail_mutation = (int)operation;
            torn = progress;
            assert(patch_map(34, edit, sizeof edit) == ALLOY_MAP_IO_ERROR);
            assert(!store.mounted);
            if (old_bank >= 0) assert(!memcmp(medium + old_bank * ALLOY_MAP_BANK_BYTES,
                                               initial + old_bank * ALLOY_MAP_BANK_BYTES, ALLOY_MAP_BANK_BYTES));
            fault_reset();
            assert(mount_map() == ALLOY_MAP_OK);
            uint8_t observed[ALLOY_MAP_BYTES];
            dump_map(observed);
            assert(!memcmp(observed, old, sizeof old) || !memcmp(observed, next, sizeof next));
            ++cases;
        }
    }
    memcpy(medium, initial, sizeof initial);
    fault_reset();
    assert(mount_map() == ALLOY_MAP_OK);
    return cases;
}

int main(void) {
    reset_medium();
    exercise_powercuts();
    const uint8_t edit[] = {0, 0x05};
    assert(patch_map(34, edit, sizeof edit) == ALLOY_MAP_OK);
    exercise_powercuts();
    const uint8_t edit2[] = {0, 0x06};
    assert(patch_map(34, edit2, sizeof edit2) == ALLOY_MAP_OK);
    exercise_powercuts();
    return 0;
}
