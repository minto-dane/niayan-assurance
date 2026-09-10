# SPDX-License-Identifier: BSD-3-Clause
"""Tests of developer orchestration only; never writes source fixtures here."""
import importlib.util
from pathlib import Path
import unittest
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'assurance/ci'))
s=importlib.util.spec_from_file_location('nia_rebind',ROOT/'assurance/ci/rebind-development.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class RebindTests(unittest.TestCase):
    def test_plan_is_fixed_and_local(self):
        p=r.checked_plan(ROOT)
        self.assertEqual(len(p),17)
        for step in p:
            self.assertNotIn('shell',step);self.assertFalse(any('https://' in x for x in step['argv']))
    def test_dependency_order(self):
        names=[x['name'] for x in r.plan()]
        self.assertLess(names.index('shared-contract'),names.index('resolver-profile'))
        self.assertLess(names.index('manager-profile'),names.index('public-manager-fixtures'))
        self.assertLess(names.index('public-manager-fixtures'),names.index('source-inventory'))
    def test_no_write_default(self):r.authorize_write(False,False,False,0)
    def test_two_explicit_acknowledgements(self):
        for a,b in [(False,False),(True,False),(False,True)]:
            with self.assertRaises(ValueError):r.authorize_write(True,a,b,1000)
    def test_write_refuses_root(self):
        with self.assertRaises(ValueError):r.authorize_write(True,True,True,0)
        r.authorize_write(True,True,True,1000)
    def test_ack_without_write_is_invalid(self):
        with self.assertRaises(ValueError):r.authorize_write(False,True,True,1000)
if __name__=='__main__':unittest.main()
