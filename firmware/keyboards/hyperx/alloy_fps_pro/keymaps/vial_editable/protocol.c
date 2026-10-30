// SPDX-License-Identifier: GPL-2.0-or-later
// Editable subset of the Vial 6 / VIA 9 wire protocols, NOT full Vial firmware.
// References and intentional exclusions: docs/vial-editable.md.
#include "protocol.h"
#include "definition.h"

#include <string.h>

// Experimental design identifier, not an MCU serial or a registered USB ID.
static const uint8_t keyboard_uid[8] = {0xa7, 0x14, 0xf0, 0x8d, 0x9b, 0x31, 0x62, 0xe6};

_Static_assert(sizeof(alloy_vial_definition) <= 65535u, "definition too large");

static void reject(uint8_t *p) {
    memset(p, 0, ALLOY_VIAL_PACKET_SIZE);
    p[0] = 0xff;
}

static void put_u32_le(uint8_t *p, uint32_t value) {
    for (uint8_t i = 0; i < 4; ++i) {
        p[i] = (uint8_t)(value >> (8u * i));
    }
}

static void vial_read(uint8_t *p) {
    const uint8_t command = p[1];
    switch (command) {
        case 0x00: // keyboard ID / protocol, little endian
            memset(p, 0, ALLOY_VIAL_PACKET_SIZE);
            put_u32_le(p, 6);
            memcpy(p + 4, keyboard_uid, sizeof(keyboard_uid));
            return;
        case 0x01: // compressed definition size
            memset(p, 0, ALLOY_VIAL_PACKET_SIZE);
            put_u32_le(p, sizeof(alloy_vial_definition));
            return;
        case 0x02: { // definition page; firmware protocol uses a 16-bit page ID
            const uint32_t start = ((uint32_t)p[2] | ((uint32_t)p[3] << 8)) * ALLOY_VIAL_PACKET_SIZE;
            // GUI encodes a 32-bit page. Do not silently truncate its high word.
            if (p[4] || p[5] || start >= sizeof(alloy_vial_definition)) {
                reject(p);
                return;
            }
            size_t count = sizeof(alloy_vial_definition) - start;
            if (count > ALLOY_VIAL_PACKET_SIZE) {
                count = ALLOY_VIAL_PACKET_SIZE;
            }
            memset(p, 0, ALLOY_VIAL_PACKET_SIZE);
            memcpy(p, alloy_vial_definition + start, count);
            return;
        }
        case 0x05:
        case 0x06:
        case 0x07:
        case 0x08:
            alloy_vial_lock_command(p);
            return;
        case 0x09: // no QMK settings; 0xffff terminates the GUI query
            memset(p, 0xff, ALLOY_VIAL_PACKET_SIZE);
            return;
        case 0x0d: // optional dynamic feature counts
            if (p[2] == 0) {
                memset(p, 0, ALLOY_VIAL_PACKET_SIZE);
                return;
            }
            break;
        default:
            break;
    }
    // Includes unsupported encoder/settings writes and unknown ops.
    reject(p);
}

bool alloy_vial_protocol(uint8_t *p, size_t length) {
    if (p == NULL || length != ALLOY_VIAL_PACKET_SIZE) {
        return false;
    }
    switch (p[0]) {
        case 0x01: // VIA protocol version, big endian
            memset(p + 1, 0, ALLOY_VIAL_PACKET_SIZE - 1);
            p[2] = 9;
            break;
        case 0x02: // only fixed layout options; no matrix-state/keystroke queries
            if (p[1] != 0x02) {
                reject(p);
                break;
            }
            memset(p + 2, 0, ALLOY_VIAL_PACKET_SIZE - 2);
            break;
        case 0x04: { // one compiled keycode, big endian
            if (p[1] >= ALLOY_VIAL_LAYERS || p[2] >= ALLOY_VIAL_ROWS || p[3] >= ALLOY_VIAL_COLS) {
                reject(p);
                break;
            }
            const uint16_t code = alloy_vial_keycode(p[1], p[2], p[3]);
            memset(p + 4, 0, ALLOY_VIAL_PACKET_SIZE - 4);
            p[4] = (uint8_t)(code >> 8);
            p[5] = (uint8_t)code;
            break;
        }
        case 0x05: { // SET_KEYCODE; never mutate before physical unlock
            if (p[1] >= ALLOY_VIAL_LAYERS || p[2] >= ALLOY_VIAL_ROWS || p[3] >= ALLOY_VIAL_COLS ||
                !alloy_vial_write((uint16_t)(((p[1]*ALLOY_VIAL_ROWS+p[2])*ALLOY_VIAL_COLS+p[3])*2),p+4,2)) reject(p);
            break;
        }
        case 0x13: { // SET_BUFFER, at most28 bytes; atomic per packet, not whole GUI upload
            const uint16_t offset=((uint16_t)p[1]<<8)|p[2];
            if(p[3]>28 || !alloy_vial_write(offset,p+4,p[3])) reject(p);
            break;
        }
        case 0x0c: // no macros
        case 0x0d: // no macro storage
            memset(p + 1, 0, ALLOY_VIAL_PACKET_SIZE - 1);
            break;
        case 0x11:
            memset(p + 1, 0, ALLOY_VIAL_PACKET_SIZE - 1);
            p[1] = ALLOY_VIAL_LAYERS;
            break;
        case 0x12: { // keymap bytes, including odd offsets, in VIA wire order
            const uint16_t offset = ((uint16_t)p[1] << 8) | p[2];
            const uint8_t count = p[3];
            if (count > ALLOY_VIAL_PACKET_SIZE - 4 || offset > ALLOY_VIAL_KEYMAP_BYTES ||
                count > ALLOY_VIAL_KEYMAP_BYTES - offset) {
                reject(p);
                break;
            }
            memset(p + 4, 0, ALLOY_VIAL_PACKET_SIZE - 4);
            for (uint8_t i = 0; i < count; ++i) {
                const uint16_t byte = offset + i;
                const uint16_t index = byte / 2;
                const uint16_t code = alloy_vial_keycode(index / (ALLOY_VIAL_ROWS * ALLOY_VIAL_COLS),
                                                       (index / ALLOY_VIAL_COLS) % ALLOY_VIAL_ROWS,
                                                       index % ALLOY_VIAL_COLS);
                p[4 + i] = (uint8_t)((byte & 1u) ? code : (code >> 8));
            }
            break;
        }
        case 0xfe:
            vial_read(p);
            break;
        default:
            // Includes reset/erase and ISP jump.
            reject(p);
            break;
    }
    return true;
}
