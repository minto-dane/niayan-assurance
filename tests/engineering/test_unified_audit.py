# SPDX-License-Identifier: MIT
"""Tests of documentation/capability/lineage tooling, NOT Ada execution."""
import copy, importlib.util, json, shutil, tempfile, unittest, sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'assurance/ci'))
spec=importlib.util.spec_from_file_location('unified_audit',ROOT/'assurance/ci/unified-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
class CapabilityAuditTests(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'assurance/engineering/capabilities.json').read_text())
    def run_value(self,data):
        original=audit.eng.load_json
        def load(p):return data if p.name=='capabilities.json' else original(p)
        with patch.object(audit.eng,'load_json',side_effect=load):return audit.capabilities(ROOT)
    def test_baseline(self):self.assertGreaterEqual(len(self.run_value(self.data)['capabilities']),20)
    def test_no_production_claim(self):
        self.data['production_qualified']=True
        with self.assertRaises(audit.eng.Invalid):self.run_value(self.data)
    def test_no_proof_by_naming(self):
        self.data['capabilities'][0]['level']='formally-proven-production'
        with self.assertRaises(audit.eng.Invalid):self.run_value(self.data)
    def test_required_residuals(self):
        self.data['capabilities'][0]['remaining']=''
        with self.assertRaises(audit.eng.Invalid):self.run_value(self.data)
    def test_missing_code(self):
        self.data['capabilities'][0]['code']=[]
        with self.assertRaises(audit.eng.Invalid):self.run_value(self.data)
    def test_unknown_code(self):
        self.data['capabilities'][0]['code']=['controlcore/src/absent.adb']
        with self.assertRaises(OSError):self.run_value(self.data)
    def test_duplicate_capability(self):
        self.data['capabilities'].append(self.data['capabilities'][0])
        with self.assertRaises(audit.eng.Invalid):self.run_value(self.data)
    def test_additional_schema_field(self):
        self.data['capabilities'][0]['approved']=True
        with self.assertRaises(audit.eng.Invalid):self.run_value(self.data)
    def test_lineage_exact_restoration(self):
        result=audit.lineage(ROOT);self.assertEqual(result['restored_canonical_ada'],95);self.assertEqual(result['restored_files'],98)
    def test_packaging_covers_built_tools_without_auto_hooks(self):
        result=audit.packaging(ROOT)
        self.assertEqual(len(result['covered_application_mains']),18)
        self.assertIn('resolvercore/resolverctl',result['covered_application_mains'])
        self.assertFalse(result['package_build_executed'])
        self.assertFalse(result['legacy_rpm_recipes_active'])
        self.assertIn('controlcore/nia',result['covered_application_mains'])
    def test_all_local_links(self):self.assertEqual(audit.documentation(ROOT)['failed_links'],[])
    def test_seven_independent_build_roots(self):
        self.assertEqual(set(audit.eng.REPOS),{'assurance','pkgcore','statecore','controlcore','configcore','resolvercore','capsulecore'})
        for repo in audit.eng.REPOS:self.assertTrue((ROOT/repo/(repo+'.gpr')).is_file())
class LineageAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'assurance/engineering/lineage-amendments.json').read_text())
    def run_value(self):
        original=audit.eng.load_json
        def load(p):return self.data if p.name=='lineage-amendments.json' else original(p)
        with patch.object(audit.eng,'load_json',side_effect=load):return audit.lineage(ROOT)
    def test_exact_source_successors(self):
        history=json.loads((ROOT/'assurance/engineering/lineage-merge.json').read_text())
        import hashlib
        changed=sum(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256'] for r in history['restored'])
        self.assertGreaterEqual(changed,2)
        self.assertEqual(self.run_value()['amended_restored_files'],changed)
    def test_missing_amendments_reject_changed_files(self):
        self.data['amendments']=[]
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_original_digest_must_match_history(self):
        self.data['amendments'][0]['from_sha256']='0'*64
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_successor_digest_must_match_file(self):
        self.data['amendments'][0]['to_sha256']='0'*64
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_unknown_file_cannot_be_amended(self):
        self.data['amendments'][0]['path']='statecore/src/state_xfs_health.adb'
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_duplicate_amendments_rejected(self):
        self.data['amendments'].append(copy.deepcopy(self.data['amendments'][0]))
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_no_invented_independent_approval(self):
        self.data['independent_review']='approved'
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_exact_schema_required(self):
        self.data['amendments'][0]['skip_hash']=True
        with self.assertRaises(audit.eng.Invalid):self.run_value()
    def test_adr_must_exist(self):
        self.data['amendments'][0]['adr']='assurance/docs/engineering/adr/ADR-9999.ja.md'
        with self.assertRaises((audit.eng.Invalid,OSError)):self.run_value()

if __name__=='__main__':unittest.main()
