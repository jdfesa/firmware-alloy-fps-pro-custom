import ctypes
import json
import lzma
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from test_firmware import ROOT,generator

PORT=ROOT/"firmware/keyboards/hyperx/alloy_fps_pro/keymaps/vial_editable"

@unittest.skipUnless(shutil.which("cc"),"C compiler required")
class EditableTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);d=Path(cls.tmp.name)
  codes={name:value for value,name in generator.HID.items() if name.startswith("KC_")};codes["KC_TRNS"]=1
  (d/"qmk_mock.h").write_text("#include <stdint.h>\n#include <stdbool.h>\n#define MATRIX_ROWS 14\n#define MATRIX_COLS 8\n#define PROGMEM\n"+
    "enum {"+",".join(f"{k}={v}" for k,v in codes.items())+"};\n"+
    "#define S(k) (0x0200u|(k))\n#define MO(l) (0x5220u|(l))\n#define LT(l,k) (0x4000u|((l)<<8)|(k))\n#define pgm_read_word(p) (*(const uint16_t*)(p))\n"+
    "typedef struct {uint8_t row,col;} keypos_t;typedef struct {uint8_t unused;} keyrecord_t;\nvoid clear_keyboard(void);uint16_t timer_read(void);uint16_t timer_elapsed(uint16_t);bool matrix_is_on(uint8_t,uint8_t);\n")
  (d/"raw_hid.h").write_text("#include <stdint.h>\nvoid raw_hid_send(uint8_t*,uint8_t);\n")
  cls.flags=["-std=c11","-Wall","-Wextra","-Werror","-O1","-I",str(d),"-I",str(PORT),'-DQMK_KEYBOARD_H="qmk_mock.h"']
  cls.sources=[str(PORT/x) for x in ("page_store.c","protocol.c","keymap.c")]+[str(ROOT/"tests/page_store_harness.c")]
  so=d/"edit.so";subprocess.run(["cc",*cls.flags,"-shared","-fPIC",*cls.sources,"-o",str(so)],check=True,capture_output=True)
  cls.lib=ctypes.CDLL(str(so));cls.lib.alloy_vial_keycode.restype=ctypes.c_uint16;cls.lib.fault_sweep.restype=ctypes.c_uint
  cls.lib.alloy_vial_protocol.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t]
  cls.lib.alloy_vial_protocol.restype=ctypes.c_bool
 def setUp(self):
  self.lib.reset_medium();self.exchange([0xfe,8])
 def exchange(self,p):
  p=bytes(p);buf=(ctypes.c_uint8*32).from_buffer_copy(p+bytes(32-len(p)))
  self.assertTrue(self.lib.alloy_vial_protocol(buf,32));return bytes(buf)
 def unlock(self):
  self.exchange([0xfe,6])
  for _ in range(20):self.lib.advance(101,True);last=self.exchange([0xfe,7])
  self.assertEqual(last[:3],bytes([1,0,0]))
 def test_full_base_enter_backspace_and_broken_keys(self):
  self.assertEqual(self.lib.alloy_vial_keycode(0,9,5),0x28)
  self.assertEqual(self.lib.alloy_vial_keycode(0,7,6),0x2a)
  for col in range(5):self.assertEqual(self.lib.alloy_vial_keycode(0,7,col),0)
  v=json.loads((PORT/"vial.json").read_text());coords=[k for row in v["layouts"]["keymap"] for k in row if isinstance(k,str)]
  self.assertEqual(len(coords),87);self.assertIn("9,5",coords);self.assertIn("7,6",coords)
 def test_visible_failed_keys_remain_disabled_in_all_layers(self):
  coords={k for row in json.loads((PORT/"vial.json").read_text())["layouts"]["keymap"] for k in row if isinstance(k,str)}
  for layer in range(4):
   for col in range(5):
    self.assertIn(f"7,{col}",coords)
    self.assertEqual(self.lib.alloy_vial_keycode(layer,7,col),0)
    self.unlock()
    self.assertEqual(self.exchange([5,layer,7,col,0,4])[0],255)
  self.assertEqual(self.lib.mutation_count(),0)
 def test_locked_writes_rejected_and_physical_unlock_required(self):
  self.assertEqual(self.exchange([5,0,2,1,0,0x1d])[0],255)
  self.assertEqual(self.lib.mutation_count(),0)
  self.exchange([0xfe,6])
  for _ in range(30):self.lib.advance(101,False);self.exchange([0xfe,7])
  self.assertEqual(self.exchange([0xfe,5])[0],0)
  self.unlock();self.assertEqual(self.exchange([0xfe,5])[:6],bytes([1,0,2,0,3,0]))
 def test_edit_read_scan_and_remount(self):
  self.unlock();self.assertEqual(self.exchange([5,0,2,1,0,0x1d])[0],5)
  self.assertEqual(self.lib.mutation_count(),17)
  self.assertEqual(self.exchange([4,0,2,1])[4:6],bytes([0,0x1d]))
  self.lib.reboot_store();self.assertEqual(self.lib.alloy_vial_keycode(0,2,1),0x1d)
  self.assertEqual(self.exchange([5,0,2,1,0,0x1d])[0],5);self.assertEqual(self.lib.mutation_count(),17)
 def test_reject_dangerous_keycodes_and_bad_boundaries(self):
  self.unlock()
  for code in (0x7c00,0x7c01,0x4404,0x5224,0xffff):
   self.assertEqual(self.exchange([5,0,2,1,code>>8,code&255])[0],255);self.unlock()
  for packet in ([5,4,0,0,0,4],[5,0,14,0,0,4],[5,0,0,8,0,4],[5,0,7,0,0,4],[0x13,3,128,1,0],[0x13,0,0,29]):
   self.assertEqual(self.exchange(packet)[0],255)
  self.assertEqual(self.lib.mutation_count(),0)
 def test_powercuts_default_and_both_banks(self):
  total=self.lib.fault_sweep();self.lib.mutate_key(5)
  total+=self.lib.fault_sweep();self.lib.mutate_key(6);total+=self.lib.fault_sweep()
  self.assertEqual(total,52275)
 def test_odd_bulk_edits_and_definition(self):
  self.unlock();self.assertEqual(self.exchange([0x13,0,35,1,0x1d])[0],0x13)
  self.assertEqual(self.lib.alloy_vial_keycode(0,2,1),0x1d)
  size=int.from_bytes(self.exchange([0xfe,1])[:4],"little")
  packed=b"".join(self.exchange([0xfe,2,i,0]) for i in range((size+31)//32))[:size]
  self.assertEqual(json.loads(lzma.decompress(packed)),json.loads((PORT/"vial.json").read_text()))
 def test_physical_bounds_are_bounded_and_linker_guard_exists(self):
  s=(PORT/"flash_backend.c").read_text();self.assertIn("#define START 0x7000u",s);self.assertIn("#define END 0x7800u",s)
  self.assertIn("page>=PS_PAGES",s);self.assertIn("__flash0_free__ <= 0x7000",(PORT/"map_reserve.ld").read_text())

 def test_sanitized_page_cuts_and_command_lengths(self):
  d=Path(self.tmp.name);main=d/"sanitize_main.c"
  main.write_text("""#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include "protocol.h"
void reset_medium(void);unsigned fault_sweep(void);
int main(void){reset_medium();assert(fault_sweep()==17425);
 for(unsigned n=0;n<256;n++){uint8_t p[32]={0};if(n!=32)assert(!alloy_vial_protocol(p,n));}
 for(unsigned a=0;a<256;a++)for(unsigned b=0;b<256;b++){uint8_t p[32]={a,b};alloy_vial_protocol(p,32);}
 return 0;}
""")
  exe=d/"sanitize"
  subprocess.run(["cc",*self.flags,"-fsanitize=address,undefined","-fno-omit-frame-pointer",*self.sources,str(main),"-o",str(exe)],check=True,capture_output=True)
  subprocess.run([str(exe)],check=True,capture_output=True)
