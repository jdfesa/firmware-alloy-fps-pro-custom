#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "page_store.h"
static uint8_t medium[2048];
static int fail_at=-1,cut_bits;
static unsigned operations;
static uint16_t now;
static bool held;
uint8_t response[32];
unsigned sends;
void raw_hid_send(uint8_t *p,uint8_t n){assert(n==32);memcpy(response,p,32);sends++;}
void clear_keyboard(void){}
uint16_t timer_read(void){return now;}
uint16_t timer_elapsed(uint16_t t){return (uint16_t)(now-t);}
bool matrix_is_on(uint8_t row,uint8_t col){return held&&col==0&&(row==2||row==3);}
void advance(unsigned ms,bool holding){now+=(uint16_t)ms;held=holding;}
bool ps_read32(uint16_t off,uint32_t *w){assert(off%4==0&&off<=2044);memcpy(w,medium+off,4);return true;}
bool ps_replace(uint8_t pg,const uint32_t words[16]){
 assert(pg<32);uint8_t *dst=medium+pg*64;const uint8_t *src=(const uint8_t*)words;
 if((int)operations++==fail_at){
  // Prefix cuts during erase-to-zero then program, including lost success ACK.
  for(int bit=0;bit<cut_bits&&bit<512;bit++) dst[bit/8]&=(uint8_t)~(1u<<(bit%8));
  if(cut_bits>=512){memset(dst,0,64);for(int bit=0;bit<cut_bits-512&&bit<512;bit++) dst[bit/8]|=src[bit/8]&(1u<<(bit%8));}
  return false;
 }
 memset(dst,0,64);memcpy(dst,src,64);return true;
}
void keyboard_post_init_user(void);
void reset_medium(void){memset(medium,0xff,sizeof medium);fail_at=-1;operations=0;keyboard_post_init_user();}
unsigned mutation_count(void){return operations;}
void reboot_store(void){keyboard_post_init_user();}
static void dump(ps_store*s,uint8_t*out){for(unsigned i=0;i<PS_KEYS;i++){uint16_t c=ps_get(s,i);out[2*i]=c>>8;out[2*i+1]=c;}}
unsigned fault_sweep(void){
 uint8_t initial[2048],old[PS_BYTES],next[PS_BYTES];ps_store s;
 const uint8_t edit[2]={0,0x1d}; // physical Q -> Z
 memcpy(initial,medium,2048);assert(ps_mount(&s));int bank=s.bank;dump(&s,old);
 fail_at=-1;operations=0;assert(ps_patch(&s,34,edit,2));unsigned total=operations;dump(&s,next);
 assert(memcmp(old,next,PS_BYTES)!=0);assert(total==17);
 unsigned cases=0;
 for(unsigned op=0;op<total;op++)for(int cut=0;cut<=1024;cut++){
  memcpy(medium,initial,2048);assert(ps_mount(&s));operations=0;fail_at=op;cut_bits=cut;
  assert(!ps_patch(&s,34,edit,2));fail_at=-1;
  if(bank>=0)assert(memcmp(medium+bank*1024,initial+bank*1024,1024)==0);
  assert(ps_mount(&s));uint8_t got[PS_BYTES];dump(&s,got);
  assert(!memcmp(got,old,PS_BYTES)||!memcmp(got,next,PS_BYTES));cases++;
 }
 memcpy(medium,initial,2048);fail_at=-1;return cases;
}
void mutate_key(uint16_t value){ps_store s;assert(ps_mount(&s));uint8_t p[2]={value>>8,value};fail_at=-1;assert(ps_patch(&s,34,p,2));}
void corrupt(unsigned off,uint8_t xor){assert(off<2048);medium[off]^=xor;}
