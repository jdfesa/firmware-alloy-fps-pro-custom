// SPDX-License-Identifier: GPL-2.0-or-later
#include "base_keymap.c"
#include "raw_hid.h"
#include "protocol.h"
#include "page_store.h"
#include <string.h>
static ps_store store;
static bool unlocked,pending;
static uint8_t remaining;
static uint16_t unlock_time;
_Static_assert(sizeof(keymaps)==PS_BYTES,"map size changed");
_Static_assert(MO(1)==0x5221 && LT(3,KC_ESC)==0x4329,"audit Vial keycodes");
uint16_t ps_default(uint16_t index) {
    if(index>=PS_KEYS) return 0;
    return pgm_read_word(&keymaps[index/112][(index/8)%14][index%8]);
}
static bool basic(uint16_t c) { return c<=1||(c>=4&&c<=0x73)||(c>=0xe0&&c<=0xe7); }
bool ps_allowed(uint16_t index,uint16_t c) {
    if(index>=PS_KEYS) return false;
    if(!ps_default(index%112)) return c==0; // keep unused/dead positions disabled
    if(basic(c)) return true;
    if(c>=0x100&&c<=0x3fff) return basic(c&255); // mods / mod-tap
    if(c>=0x4000&&c<=0x43ff) return basic(c&255); // LT only existing layers
    return (c>=0x5200&&c<=0x5203)||(c>=0x5220&&c<=0x5223)||
           (c>=0x5260&&c<=0x5263); // TO/MO/TG; no boot/reset/macros
}
uint16_t alloy_vial_keycode(uint8_t layer,uint8_t row,uint8_t col) {
    if(layer>=4||row>=14||col>=8) return 0;
    return ps_get(&store,(uint16_t)((layer*14+row)*8+col));
}
uint16_t keymap_key_to_keycode(uint8_t layer,keypos_t key) {
    return alloy_vial_keycode(layer,key.row,key.col);
}
void keyboard_post_init_user(void) { ps_mount(&store); }
bool alloy_vial_write(uint16_t offset,const uint8_t *bytes,uint8_t length) {
    if(!unlocked||pending) return false;
    bool ok=ps_patch(&store,offset,bytes,length);
    if(!ok) { unlocked=false;ps_mount(&store); }
    return ok;
}
void alloy_vial_lock_command(uint8_t *p) {
    uint8_t cmd=p[1];
    if(cmd==6) { clear_keyboard();unlocked=false;pending=true;remaining=20;unlock_time=timer_read(); }
    if(cmd==7 && pending) {
        if(!matrix_is_on(2,0)||!matrix_is_on(3,0)) { remaining=20;unlock_time=timer_read(); }
        else if(timer_elapsed(unlock_time)>=100) {
            unlock_time=timer_read();
            if(--remaining==0) { pending=false;unlocked=true; }
        }
    }
    if(cmd==8) { unlocked=false;pending=false; }
    memset(p,cmd==5?0xff:0,32);p[0]=unlocked;p[1]=pending;
    if(cmd==5) { p[2]=2;p[3]=0;p[4]=3;p[5]=0; } // physical Tab + Caps
    if(cmd==7) p[2]=remaining;
}
bool process_record_user(uint16_t keycode,keyrecord_t *record) {
    (void)keycode;(void)record;
    return !pending;
}
void raw_hid_receive(uint8_t *data,uint8_t length) {
    if(alloy_vial_protocol(data,length)) raw_hid_send(data,length);
}
