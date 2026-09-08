# SPDX-License-Identifier: MIT
"""A required native fixture must not turn into a successful skipped suite."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[2] / 'ci/run-engineering-checks.py'


class NativeDependencyTests(unittest.TestCase):
    def test_absent_fixture_tools_fail_before_any_suite_runs(self):
        with tempfile.TemporaryDirectory(prefix='nia-missing-native-tools-') as d:
            root = Path(d)
            (root / 'assurance').mkdir()
            result = subprocess.run([sys.executable, '-B', str(RUNNER), '--mode', 'source',
                                     '--root', str(root)], capture_output=True, text=True,
                                    env=os.environ | {'PATH': '/nonexistent-nia-test-tools'}, timeout=10)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            reports = list((root / 'assurance/evidence').glob('engineering-*/report.json'))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text())
            self.assertEqual(report['result'], 'fail')
            self.assertIn('required native fixture tools unavailable', report['error'])
            self.assertIn('gpg', report['error'])
            self.assertEqual(report['checks'], [])
            self.assertEqual(report['ada_execution'], 'not-run')
            self.assertEqual(report['formal_proof'], 'not-run')


if __name__ == '__main__':
    unittest.main()
