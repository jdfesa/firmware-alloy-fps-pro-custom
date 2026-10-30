/* SPDX-License-Identifier: GPL-2.0-or-later */
ENTRY(_start)
MEMORY { FLASH (rx) : ORIGIN = 0, LENGTH = 512 }
SECTIONS {
    .text : { KEEP(*(.vectors)) *(.text*) *(.rodata*) } > FLASH
    .data : { *(.data*) } > FLASH
    .bss (NOLOAD) : { *(.bss*) *(COMMON) } > FLASH
    /DISCARD/ : { *(.comment) *(.ARM.exidx*) *(.ARM.extab*) *(.eh_frame*) }
}
ASSERT(SIZEOF(.text) <= 512, "jumploader overlaps application")
ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "startup has no data/bss initialization")
