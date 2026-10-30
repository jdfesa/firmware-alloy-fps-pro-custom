import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import generate_vial_editable as generator


class PhysicalLayoutTests(unittest.TestCase):
    def test_generated_definition_is_current(self):
        generator.generate(check=True)

    def test_tkl_geometry_and_electrical_identity(self):
        matrix = json.loads((ROOT/'hardware/matrix-inference.json').read_text())
        data = generator.definition(matrix)
        self.assertEqual(data['matrix'], {'rows': 14, 'cols': 8})
        self.assertEqual(len(data['layouts']['keymap']), 6)
        # Decode KLE spacing, including next-key-only width and persistent x.
        positions = {}
        y = 0
        for row in data['layouts']['keymap']:
            x, w = 0, 1
            for item in row:
                if isinstance(item, dict):
                    x += item.get('x', 0)
                    y += item.get('y', 0)
                    w = item.get('w', w)
                else:
                    self.assertNotIn(item, positions)
                    positions[item] = (x, y, w)
                    x += w
                    w = 1
            y += 1
        expected = {','.join(map(str,e['matrix'])) for e in matrix['entries']
                    if e['usage']}
        self.assertEqual(set(positions), expected)
        self.assertEqual(len(positions), 87)
        failed = {','.join(map(str,e['matrix'])) for e in matrix['entries']
                  if e['usage'] in generator.BROKEN}
        self.assertEqual(len(failed), 5)
        self.assertTrue(failed <= set(positions))
        self.assertEqual(positions['0,0'], (0, 0, 1))  # Escape
        self.assertEqual(positions['6,6'], (14, 0, 1))  # F12, same top row
        self.assertEqual(positions['7,6'], (13, 1.5, 2))  # Backspace
        self.assertEqual(positions['9,5'], (12.75, 3.5, 2.25))  # Enter
        self.assertEqual(positions['5,6'], (3.75, 5.5, 6.25))  # Space
        self.assertEqual(positions['13,0'], (16.25, 4.5, 1))  # Up above Down
        self.assertEqual(positions['13,2'], (16.25, 5.5, 1))
        self.assertEqual(max(y for x,y,w in positions.values()), 5.5)

    def test_build_checks_editable_generated_data(self):
        text = (ROOT/'scripts/build_compact_raw.py').read_text()
        self.assertIn('from generate_vial_editable import generate', text)

    def test_private_instructions_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path/'.gitignore').write_text((ROOT/'.gitignore').read_text())
            subprocess.run(['git','init','--quiet',folder],check=True,capture_output=True)
            run = subprocess.run(['git','check-ignore','tmp/private-instructions.docx'],
                                 cwd=folder,capture_output=True,text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
