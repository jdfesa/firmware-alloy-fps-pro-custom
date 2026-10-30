// SPDX-License-Identifier: GPL-2.0-or-later
// SONiX SN32F260 manual v1.9 sections 11.4,11.8,11.11. See docs/vial-editable.md.
#include "page_store.h"
#define START 0x7000u
#define END 0x7800u
#define REG(off) (*(volatile uint32_t *)(0x40062000u+(off)))
_Static_assert(END-START==2*PS_BANK, "reserved map range mismatch");
static bool wait_ready(void) {
    for(unsigned n=0;n<3000000;n++) if(!(REG(4)&1)) return !(REG(4)&4);
    return false;
}
bool ps_read32(uint16_t off,uint32_t *w) {
    if(!w || off&3 || off>END-START-4) return false;
    *w=*(volatile const uint32_t *)(START+off);return true;
}
bool ps_replace(uint8_t page,const uint32_t words[16]) {
    if(page>=PS_PAGES||!words) return false;
    uint32_t addr=START+(uint32_t)page*PS_PAGE;
    if(addr<START||addr+PS_PAGE>END) return false;
    uint32_t mask;
    __asm__ volatile("mrs %0, primask\ncpsid i":"=r"(mask)::"memory");
    bool ok=wait_ready();
    if(ok) {
        REG(4)=0;REG(8)=2;REG(16)=addr; // PER, selected page only. No MER/security.
        ok=wait_ready();
        if(ok) { REG(8)|=64;ok=wait_ready(); }
    }
    if(ok) {
        REG(4)=0;REG(8)=1;REG(16)=addr; // PG then address, per manual.
        ok=wait_ready();
        for(unsigned i=0;ok&&i<16;i++) { REG(12)=words[i];ok=wait_ready(); }
        if(ok) { REG(8)|=64;ok=wait_ready(); }
    }
    REG(8)=0;
    __asm__ volatile("msr primask, %0"::"r"(mask):"memory");
    for(unsigned i=0;ok&&i<16;i++) if(*(volatile const uint32_t *)(addr+i*4)!=words[i]) ok=false;
    return ok;
}
