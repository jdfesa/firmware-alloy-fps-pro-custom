# SPDX-License-Identifier: GPL-2.0-or-later
# Local experiment: no persistent flash writes, RGB, console or dynamic configurator.
EEPROM_DRIVER = transient
BACKLIGHT_ENABLE = no
RGBLIGHT_ENABLE = no
RGB_MATRIX_ENABLE = no
LED_MATRIX_ENABLE = no
CONSOLE_ENABLE = no
COMMAND_ENABLE = no
VIA_ENABLE = no
# This is SonixQMK, not Vial-QMK. VIAL_ENABLE is not a valid option here.
# Size reference: SonixQMK handwired/onekey/sn32f260, not measured for this port.
USE_PROCESS_STACKSIZE = 0x1E0
USE_EXCEPTIONS_STACKSIZE = 0xE0
