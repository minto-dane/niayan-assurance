# SPDX-License-Identifier: BSD-3-Clause
"""Kernel-control readback validation; fixtures do not change live cgroups."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('limited_exec', ROOT / 'dev/limited-exec.py')
limited = importlib.util.module_from_spec(spec)
spec.loader.exec_module(limited)


class ScopeReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='nia-scope-readback-')
        self.directory = Path(self.temporary.name)
        for name, value in {'memory.max': '3221225472', 'memory.swap.max': '0',
                            'cpu.max': '100000 100000', 'pids.max': '128'}.items():
            (self.directory / name).write_text(value + '\n')

    def tearDown(self):
        self.temporary.cleanup()

    def test_exact_and_stricter_limits(self):
        self.assertEqual(limited.check_limits(self.directory)['memory.swap.max'], '0')
        (self.directory / 'memory.max').write_text('1073741824')
        (self.directory / 'cpu.max').write_text('50000 100000')
        self.assertEqual(limited.check_limits(self.directory)['memory.max'], '1073741824')

    def test_weaker_or_unlimited_controls_are_refused(self):
        for name, value in [('memory.max', '4294967296'), ('memory.max', 'max'),
                            ('memory.swap.max', '1'), ('cpu.max', '200000 100000'),
                            ('cpu.max', 'max 100000'), ('pids.max', '129')]:
            with self.subTest(name=name, value=value):
                path = self.directory / name
                before = path.read_text()
                try:
                    path.write_text(value)
                    with self.assertRaises(ValueError): limited.check_limits(self.directory)
                finally:
                    path.write_text(before)

    def test_missing_control_is_refused(self):
        (self.directory / 'memory.swap.max').unlink()
        with self.assertRaises(OSError): limited.check_limits(self.directory)


if __name__ == '__main__':
    unittest.main()
