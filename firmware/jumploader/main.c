// SPDX-License-Identifier: GPL-2.0-or-later
// Experimental SN32F26x startup, not validated on the connected PCB.
// Register layout: SONiX SN32F260; exception forwarding: SonixQMK architecture.
#include <stdint.h>
#define REG(a) (*(volatile uint32_t *)(a))
#define APP 0x200u
#define APP_END 0x7800u
#define RAM_START 0x20000000u
#define RAM_END 0x20000800u
#define MAGIC_ADDR (RAM_END - 4)
#define MAGIC 0xDEADBEEFu // Matches the pinned QMK sn32_dfu.c, NOT old bldr magic.
#define GPIO_A 0x40044000u
#define GPIO_C 0x40048000u

extern void exception_proxy(void);
extern void jump_application(void);

static void settle(void) {
    for (unsigned i = 0; i < 400; ++i) __asm__ volatile ("nop");
}

static int escape_held(void) {
    // Inferred Escape [0,0]: C0 drives low, A0 input pull-up. No D5/BOOT0 use.
    uint32_t mode_a = REG(GPIO_A + 4), cfg_a = REG(GPIO_A + 8);
    uint32_t mode_c = REG(GPIO_C + 4), data_c = REG(GPIO_C);
    REG(GPIO_A + 4) = mode_a & ~1u;
    REG(GPIO_A + 8) = cfg_a & ~3u;
    REG(GPIO_C) = data_c & ~1u;
    REG(GPIO_C + 4) = mode_c | 1u;
    settle();
    uint32_t first = REG(GPIO_A);
    settle();
    uint32_t second = REG(GPIO_A);
    REG(GPIO_C + 4) = mode_c;
    REG(GPIO_C) = data_c;
    REG(GPIO_A + 8) = cfg_a;
    REG(GPIO_A + 4) = mode_a;
    return !(first & second & 1u);
}

__attribute__((noreturn)) void _start(void) {
    const uint32_t sp = REG(APP), pc = REG(APP + 4);
    const int requested = REG(MAGIC_ADDR) == MAGIC;
    if (requested) REG(MAGIC_ADDR) = 0;
    if (requested || sp <= RAM_START || sp > RAM_END || (sp & 7u) ||
        !(pc & 1u) || pc < APP + 0xc0 || pc >= APP_END || escape_held()) {
        ((void (*)(void))0x1FFF0009u)();
        for (;;) {}
    }
    jump_application();
    __builtin_unreachable();
}

__attribute__((used, section(".vectors")))
const void *const vectors[48] = {
    // Keep stack below QMK reset magic at 0x200007fc while checking it.
    [0] = (void *)0x20000780u,
    [1] = _start,
    [2 ... 47] = exception_proxy,
};
