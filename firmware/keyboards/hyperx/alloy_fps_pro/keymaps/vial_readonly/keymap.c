// SPDX-License-Identifier: GPL-2.0-or-later
#include "../custom42_fn/keymap.c"
#include "raw_hid.h"
#include "protocol.h"

_Static_assert(MATRIX_ROWS == ALLOY_VIAL_ROWS && MATRIX_COLS == ALLOY_VIAL_COLS, "matrix mismatch");
_Static_assert(sizeof(keymaps) == ALLOY_VIAL_KEYMAP_BYTES, "compiled map dimensions changed");
// These codes are shared by the pinned SonixQMK and Vial keycode definitions.
_Static_assert(MO(1) == 0x5221 && LT(3, KC_ESC) == 0x4329 && S(KC_1) == 0x021e,
               "Vial keycode encoding changed; audit before advertising protocol");

uint16_t alloy_vial_keycode(uint8_t layer, uint8_t row, uint8_t col) {
    if (layer >= ALLOY_VIAL_LAYERS || row >= MATRIX_ROWS || col >= MATRIX_COLS) {
        return KC_NO;
    }
    return pgm_read_word(&keymaps[layer][row][col]);
}

void raw_hid_receive(uint8_t *data, uint8_t length) {
    if (alloy_vial_readonly(data, length)) {
        raw_hid_send(data, length);
    }
}
