"""Acceptance must derive coverage and provenance, not trust summary labels."""
from pathlib import Path
import copy
import json
import math
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'animation_rig'))
import verify_blend_acceptance as acceptance
from test_animation_blend_numeric import BlendCoverage


class BlendAcceptance(unittest.TestCase):
    def fixture(self):
        shard=BlendCoverage().fixture();stems={'clip'+str(i) for i in range(13)}
        report=dict(shard,status='actual-lua-snapshot-blend-and-skin-passed',clip_count=13,
            pose_samples=3276,ordinary_transition_pose_samples=1638,interrupted_transition_pose_samples=1638,
            bone_comparisons=452088,weighted_vertex_samples=115675560,pure_authored_zero_write_checks=234,
            authored_helper_no_legacy_bone_write_checks=1638,maxima={key:0. for key in
                ('max_head_error_m','max_axis_error_m','max_local_matrix_error','max_weighted_skin_error_m')},
            weighted_skin_rms_m=0.,clips=[],interruptions=[])
        for stem in sorted(stems):
            clip=copy.deepcopy(shard['clips'][0]);clip['clip']=stem;report['clips'].append(clip)
            report['interruptions'].extend(dict(row,clip=stem) for row in copy.deepcopy(shard['interruptions']))
        return report,stems

    def test_exact_complete_rows_pass(self):
        report,stems=self.fixture();self.assertEqual(set(acceptance.numerical_rows(report,stems)),stems)

    def test_thirteen_repeated_clips_cannot_fake_complete_coverage(self):
        report,stems=self.fixture();report['clips']=[copy.deepcopy(report['clips'][0]) for _ in range(13)]
        with self.assertRaises(ValueError):acceptance.numerical_rows(report,stems)

    def test_extra_interruption_cannot_hide_behind_count_label(self):
        report,stems=self.fixture();report['interruptions'].append(copy.deepcopy(report['interruptions'][0]))
        with self.assertRaises(ValueError):acceptance.numerical_rows(report,stems)

    def test_summary_maximum_must_equal_rows(self):
        report,stems=self.fixture();report['clips'][0]['samples'][0]['max_weighted_skin_error_m']=.001
        with self.assertRaises(ValueError):acceptance.numerical_rows(report,stems)

    def test_rms_summary_must_equal_rows(self):
        report,stems=self.fixture();report['weighted_skin_rms_m']=.001
        with self.assertRaises(ValueError):acceptance.numerical_rows(report,stems)

    def test_unknown_legacy_clip_rejected(self):
        rows=[{'clip':'clip'+str(i)+'.fbx'} for i in range(13)];rows[-1]['clip']='new_unknown.fbx'
        with self.assertRaises(ValueError):acceptance.complete_by_stem(rows,{'clip'+str(i) for i in range(13)})

    def test_missing_required_provenance_rejected(self):
        with self.assertRaises(ValueError):acceptance.require_frozen({'frozen_input_sha256':{}},{'actual.py'})

    def test_current_hash_drift_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'frozen.py';path.write_bytes(b'initial source')
            report={'frozen_input_sha256':{str(path):acceptance.v.digest(path)}}
            path.write_bytes(b'changed source')
            with self.assertRaises(ValueError):acceptance.require_frozen(report,{str(path)})

    def test_validated_recorded_shard_sha_is_retained(self):
        proof={'frozen_input_sha256':{'source.py':'source SHA'},
               'shard_reports':{'executed.blend.json':'validated shard SHA'}}
        frozen={'source.py':'source SHA','executed.blend.json':'validated shard SHA'}
        acceptance.merge_recorded_numerical_pins(frozen,proof)
        self.assertEqual(frozen['executed.blend.json'],proof['shard_reports']['executed.blend.json'])

    def test_all_twenty_six_late_shard_changes_cannot_be_rebound(self):
        with tempfile.TemporaryDirectory() as folder:
            for suffix in ('.blend.json','.equivalence.json'):
                for index in range(13):
                    with self.subTest(suffix=suffix,index=index):
                        path=(Path(folder)/(str(index)+suffix)).resolve()
                        path.write_bytes(b'validated executed rows')
                        proof={'frozen_input_sha256':{},'shard_reports':{str(path):acceptance.v.digest(path)}}
                        path.write_bytes(b'changed after row validation')
                        frozen={str(path):acceptance.v.digest(path)}
                        with self.assertRaises(ValueError):acceptance.merge_recorded_numerical_pins(frozen,proof)

    def test_lifetime_only_executed_prefix_is_compared(self):
        first="HARNESS='executed prefix\\nQuaternion={old unused stub}'"
        second="HARNESS='executed prefix\\nQuaternion={new unused stub}'"
        self.assertEqual(acceptance.harness_prefix(first),acceptance.harness_prefix(second))
        changed="HARNESS='changed executable prefix\\nQuaternion={new unused stub}'"
        self.assertNotEqual(acceptance.harness_prefix(first),acceptance.harness_prefix(changed))

    def test_invalid_harness_boundary_rejected(self):
        with self.assertRaises(ValueError):acceptance.harness_prefix("HARNESS='no fixed boundary'")


class NumericalHelperIdentity(unittest.TestCase):
    PREFIX=b'import struct\nfrom local_decoder import bounded_read\nLIMIT=138\ndef compiled_bones(data):\n return bounded_read(data,LIMIT)\n\n'
    OLD=PREFIX+b'HARNESS="unused old Lua"\nclass RuntimeTests:\n def test_original(self):pass\n'
    CURRENT=PREFIX+b'HARNESS="unused new Lua"\nclass RuntimeTests:\n def test_original(self):pass\n def test_added(self):pass\n'

    def pins(self,current=None,old=None):
        return dict(acceptance.AIM_TEST_ONLY_UPDATE,
            current_sha256=acceptance.digest_bytes(self.CURRENT if current is None else current),
            historical_sha256=acceptance.digest_bytes(self.OLD if old is None else old),
            executed_prefix_sha256=acceptance.digest_bytes(self.PREFIX))

    def test_unchanged_helper_needs_no_exception(self):
        for relative in acceptance.HELPERS:
            identity=acceptance.numerical_helper_identity(relative,b'unchanged',b'unchanged')
            self.assertTrue(identity['whole_file_byte_identical'])
            self.assertNotIn('identity_policy',identity)

    def test_reviewed_pair_records_prefix_and_freezes_complete_current_file(self):
        with mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins()):
            identity=acceptance.numerical_helper_identity(acceptance.AIM_HELPER,self.CURRENT,self.OLD)
        self.assertFalse(identity['whole_file_byte_identical'])
        self.assertTrue(identity['executed_prefix_byte_identical'])
        self.assertEqual(identity['current_sha256'],acceptance.digest_bytes(self.CURRENT))
        self.assertEqual(identity['historical_sha256'],acceptance.digest_bytes(self.OLD))
        self.assertEqual(identity['executed_prefix_sha256'],acceptance.digest_bytes(self.PREFIX))
        self.assertEqual(identity['identity_policy'],'finite-reviewed-aim-test-only-update-v1')
        self.assertIn('no native playback acceptance',identity['scope'])

    def test_finite_policy_matches_current_reviewed_source(self):
        raw=(acceptance.v.ROOT/acceptance.AIM_HELPER).read_bytes()
        self.assertEqual(acceptance.digest_bytes(raw),acceptance.AIM_TEST_ONLY_UPDATE['current_sha256'])
        self.assertEqual(acceptance.digest_bytes(acceptance.aim_decoder_prefix(raw)),
                         acceptance.AIM_TEST_ONLY_UPDATE['executed_prefix_sha256'])

    def test_other_helpers_cannot_use_aim_exception(self):
        with mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins()):
            for relative in acceptance.HELPERS:
                if relative==acceptance.AIM_HELPER:continue
                with self.subTest(relative=relative),self.assertRaises(ValueError):
                    acceptance.numerical_helper_identity(relative,self.CURRENT,self.OLD)

    def test_unknown_base_current_or_reversed_pair_rejected(self):
        with mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins()):
            for current,old in ((self.CURRENT,self.OLD+b'\n'),(self.CURRENT+b'\n',self.OLD),
                                (self.OLD,self.CURRENT),(self.CURRENT,self.OLD.replace(b'old',b'unknown'))):
                with self.subTest(current=current,old=old),self.assertRaises(ValueError):
                    acceptance.numerical_helper_identity(acceptance.AIM_HELPER,current,old)

    def test_decoder_import_dependency_or_constant_drift_fails_even_with_new_full_file_pin(self):
        changes=((b'return bounded_read(data,LIMIT)',b'return ()'),(b'import struct',b'import json'),
                 (b'from local_decoder import bounded_read',b'from foreign_decoder import bounded_read'),
                 (b'LIMIT=138',b'LIMIT=137'))
        for before,after in changes:
            current=self.CURRENT.replace(before,after)
            with self.subTest(change=after),mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins(current)):
                with self.assertRaises(ValueError):
                    acceptance.numerical_helper_identity(acceptance.AIM_HELPER,current,self.OLD)

    def test_arbitrary_test_tail_and_import_time_rebindings_are_not_ignored(self):
        tails=(b'\ncompiled_bones=lambda data:()\n',b'\nimport foreign_decoder\n',
               b'\n@replace_decoder\nclass NewTests:pass\n',
               b'\ndef test_new(value=replace_decoder()):pass\n',
               b'\nclass NewTests:\n compiled_bones=replace_decoder()\n',
               b'\nclass NewTests:\n def test_harmless(self):pass\n')
        with mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins()):
            for tail in tails:
                with self.subTest(tail=tail),self.assertRaises(ValueError):
                    acceptance.numerical_helper_identity(acceptance.AIM_HELPER,self.CURRENT+tail,self.OLD)

    def test_missing_duplicate_computed_or_annotated_boundary_rejected_even_when_pinned(self):
        boundaries=(b'',b'HARNESS="one"\nHARNESS="two"\n',b'HARNESS=str("computed")\n',
                    b'HARNESS: str="annotated"\n',b'HARNESS=OTHER="shared"\n',
                    b'HARNESS="one"\nHARNESS+="two"\n')
        for boundary in boundaries:
            current=self.PREFIX+boundary
            with self.subTest(boundary=boundary),mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins(current)):
                with self.assertRaises(ValueError):
                    acceptance.numerical_helper_identity(acceptance.AIM_HELPER,current,self.OLD)

    def test_equal_but_different_prefix_is_not_a_new_reviewed_decoder(self):
        old=self.OLD.replace(b'LIMIT=138',b'LIMIT=137')
        current=self.CURRENT.replace(b'LIMIT=138',b'LIMIT=137')
        with mock.patch.object(acceptance,'AIM_TEST_ONLY_UPDATE',self.pins(current,old)):
            with self.assertRaises(ValueError):
                acceptance.numerical_helper_identity(acceptance.AIM_HELPER,current,old)


if __name__=='__main__':unittest.main()
