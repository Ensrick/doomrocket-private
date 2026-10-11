"""Acceptance must derive coverage and provenance, not trust summary labels."""
from pathlib import Path
import copy
import json
import math
import sys
import tempfile
import unittest

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


if __name__=='__main__':unittest.main()
