// SPDX-License-Identifier: GPL-2.0-or-later
// Page-granular snapshots. No assumptions about erase polarity or word writes.
#include "page_store.h"
#include <string.h>
#define MAGIC 0x32505641u // AVP2, distinct from the earlier virtual word store
#define SCHEMA 0x02040e08u
#define COMMIT 0x54494d43u
_Static_assert(sizeof(ps_store)<=8, "no RAM shadow of map");
static uint32_t crcword(uint32_t crc,uint32_t w) {
    for(unsigned i=0;i<4;i++,w>>=8) {
        crc^=(uint8_t)w;
        for(unsigned b=0;b<8;b++) crc=(crc>>1)^((crc&1)?0xedb88320u:0);
    }
    return crc;
}
static uint16_t code(uint32_t w,unsigned half) {
    w>>=16*half;
    return (uint16_t)(((w&255)<<8)|((w>>8)&255));
}
static bool readbank(unsigned bank,unsigned off,uint32_t *w) {
    return ps_read32((uint16_t)(bank*PS_BANK+off),w);
}
static bool valid(unsigned bank,bool committed,uint32_t *generation) {
    uint32_t w,crc=0xffffffffu,saved;
    for(unsigned i=0;i<3;i++) {
        if(!readbank(bank,i*4,&w)) return false;
        if((i==0 && w!=MAGIC)||(i==1 && w!=SCHEMA)) return false;
        if(i==2) *generation=w;
        crc=crcword(crc,w);
    }
    if(!readbank(bank,12,&saved)) return false;
    for(unsigned i=16;i<64;i+=4) {
        if(!readbank(bank,i,&w)||w!=0) return false;
    }
    for(unsigned i=0;i<PS_BYTES;i+=4) {
        if(!readbank(bank,64+i,&w)||!ps_allowed(i/2,code(w,0))||!ps_allowed(i/2+1,code(w,1))) return false;
        crc=crcword(crc,w);
    }
    if((crc^0xffffffffu)!=saved) return false;
    if(committed) {
        if(!readbank(bank,960,&w)||w!=COMMIT) return false;
        if(!readbank(bank,964,&w)||w!=*generation) return false;
        if(!readbank(bank,968,&w)||w!=saved) return false;
        for(unsigned i=972;i<1024;i+=4) if(!readbank(bank,i,&w)||w!=0) return false;
    }
    return true;
}
bool ps_mount(ps_store *s) {
    uint32_t a=0,b=0;
    bool va=valid(0,true,&a),vb=valid(1,true,&b);
    s->mounted=false;s->bank=-1;s->generation=0;
    if(va&&vb) {
        if((uint32_t)(a-b)==1) s->bank=0;
        else if((uint32_t)(b-a)==1) s->bank=1;
        else return false;
    } else if(va) s->bank=0;
    else if(vb) s->bank=1;
    if(s->bank>=0) s->generation=s->bank==0?a:b;
    s->mounted=true;
    return true;
}
static bool current(const ps_store *s,unsigned off,uint32_t *w) {
    if(s->bank>=0) return readbank((unsigned)s->bank,64+off,w);
    uint16_t a=ps_default(off/2),b=ps_default(off/2+1);
    *w=(a>>8)|((uint32_t)(a&255)<<8)|((uint32_t)(b>>8)<<16)|((uint32_t)(b&255)<<24);
    return true;
}
uint16_t ps_get(const ps_store *s,uint16_t index) {
    if(index>=PS_KEYS) return 0;
    if(!s->mounted) return ps_default(index);
    uint32_t w;
    if(!current(s,(index/2)*4,&w)) return 0;
    return code(w,index&1);
}
static uint32_t patchword(uint32_t w,unsigned at,unsigned off,const uint8_t *p,unsigned n) {
    for(unsigned i=0;i<4;i++) if(at+i>=off && at+i-off<n) {
        unsigned shift=8*i;
        w=(w&~(255u<<shift))|((uint32_t)p[at+i-off]<<shift);
    }
    return w;
}
static bool failure(ps_store *s) { s->mounted=false;return false; }
bool ps_patch(ps_store *s,uint16_t off,const uint8_t *p,uint8_t n) {
    if(!s->mounted||s->bank < -1||s->bank>1||n>28||off>PS_BYTES||n>PS_BYTES-off||(!p&&n)) return false;
    bool changed=false;
    for(unsigned i=0;i<PS_BYTES;i+=4) {
        uint32_t w;
        if(!current(s,i,&w)) return failure(s);
        uint32_t next=patchword(w,i,off,p,n);
        if(!ps_allowed(i/2,code(next,0))||!ps_allowed(i/2+1,code(next,1))) return false;
        changed|=next!=w;
    }
    if(!changed) return true;
    unsigned bank=s->bank==0?1:0;
    uint32_t generation=s->generation+1;
    uint32_t page[16]={0};
    // Invalidate the destination commit FIRST, including on reuse after failure.
    if(!ps_replace((uint8_t)(bank*16+15),page)) return failure(s);
    uint32_t check;
    if(!readbank(bank,960,&check)||check==COMMIT) return failure(s);
    uint32_t crc=crcword(crcword(crcword(0xffffffffu,MAGIC),SCHEMA),generation);
    for(unsigned pg=0;pg<14;pg++) {
        for(unsigned i=0;i<16;i++) {
            unsigned at=pg*64+i*4;
            if(!current(s,at,&page[i])) return failure(s);
            page[i]=patchword(page[i],at,off,p,n);
            crc=crcword(crc,page[i]);
        }
        if(!ps_replace((uint8_t)(bank*16+1+pg),page)) return failure(s);
    }
    crc^=0xffffffffu;
    memset(page,0,sizeof page);
    page[0]=MAGIC;page[1]=SCHEMA;page[2]=generation;page[3]=crc;
    if(!ps_replace((uint8_t)(bank*16),page)||!valid(bank,false,&check)||check!=generation) return failure(s);
    memset(page,0,sizeof page);page[0]=COMMIT;page[1]=generation;page[2]=crc;
    if(!ps_replace((uint8_t)(bank*16+15),page)||!valid(bank,true,&check)||check!=generation) return failure(s);
    s->bank=(int8_t)bank;s->generation=generation;
    return true;
}
