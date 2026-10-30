// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    ALLOY_VIAL_PACKET_SIZE = 32,
    ALLOY_VIAL_ROWS = 14,
    ALLOY_VIAL_COLS = 8,
    ALLOY_VIAL_LAYERS = 4,
    ALLOY_VIAL_KEYMAP_BYTES = ALLOY_VIAL_LAYERS * ALLOY_VIAL_ROWS * ALLOY_VIAL_COLS * 2,
};

// Adapter reads the compiled map, not live switch state or another keyboard.
uint16_t alloy_vial_keycode(uint8_t layer, uint8_t row, uint8_t col);

// In-place response; false for invalid packet framing (no response, no mutation).
// Unsupported requests receive 0xff + zero padding. No write/unlock/ISP API.
bool alloy_vial_readonly(uint8_t *packet, size_t length);
