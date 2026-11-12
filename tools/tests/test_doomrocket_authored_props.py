"""Execute opt-in independent loaded-rocket following and native restoration.

The real Lua module runs against the existing independent scene-graph oracle.
These checks do not establish native engine or rendered acceptance.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_doomrocket_authored_weapon as weapon
import test_doomrocket_animation_blend as blend
import test_stage_integration as integration

stage = integration.stage


def runtime():
    lua = weapon.runtime()
    lua.execute(r'''
      -- The older oracle used normalized matrices as stand-in quaternions for
      -- its legacy path. New prop preparation exercises both paths together,
      -- so give Matrix4x4.rotation its native quaternion return convention.
      Matrix4x4.rotation=pose_quaternion
      local old_set_rotation=Unit.set_local_rotation
      Unit.set_local_rotation=function(u,node,q)
        if q.w~=nil then q=Matrix4x4.from_quaternion_position(q,Vector3(0,0,0)) end
        return old_set_rotation(u,node,q)
      end
      outfit.nodes.j_leftweaponcomponent2=17;outfit.parents[17]=outfit.nodes.j_lefthand
      outfit.locals[17]=keep(Matrix4x4.identity(1,.004,-.003,.002))
      weapon.nodes.pRocketLauncher=4;weapon.nodes.pRocket=5
      weapon.parents[4]=1;weapon.locals[4]=keep(Matrix4x4.identity(1,.001,.002,.003))
      weapon.parents[5]=4;weapon.locals[5]=keep(Matrix4x4.identity(1,.004,.005,.006))
      rocket_rest=keep(weapon.locals[5]);rocket_parent=4
      prop_links={}
      for i,link in ipairs(semantic_links) do prop_links[i]=link end
      prop_links[4]={target='pRocket',source='j_leftweaponcomponent2',world_scale={100,100,100}}
      prop_profile={weapon_links=prop_links,weapon_control_policy='independent-props-v1'}
      mod._warlock_animation_ownership=function()
        return {upper_body=mode,weapon=mode,profile=prop_profile}
      end
      function prop_gap()
        local actual=Unit.world_pose(weapon,5)
        local node=outfit.nodes.j_leftweaponcomponent2
        local expected=Matrix4x4.from_quaternion_position(Quaternion.normalize(Unit.world_rotation(outfit,node)),
          Unit.world_position(outfit,node))
        for _,axis in ipairs({'x','y','z'}) do
          local v=Matrix4x4[axis](expected)
          Matrix4x4['set_'..axis](expected,Vector3(v.x*100,v.y*100,v.z*100))
        end
        local worst=0
        for r=1,4 do for c=1,4 do worst=math.max(worst,math.abs(actual[r][c]-expected[r][c])) end end
        return worst
      end
      function restored_prop()
        assert(weapon.parents[5]==rocket_parent)
        for r=1,4 do for c=1,4 do assert(math.abs(weapon.locals[5][r][c]-rocket_rest[r][c])<1e-8) end end
        assert(#weapon.data.scene_graph_data==2)
      end
      World.update_unit(world,outfit);World.update_unit(world,weapon)
    ''')
    return lua


class AuthoredPropTests(unittest.TestCase):
    def test_legacy_helper_prop_endpoint_matches_native_frames_without_mutating_authored_pose(self):
        lua = runtime()
        lua.execute('''
          helper=make_unit(outfit.name)
          for name,node in pairs(outfit.nodes) do helper.nodes[name]=node end
          for node,parent in pairs(outfit.parents) do helper.parents[node]=parent end
          for node,pose in pairs(outfit.locals) do helper.locals[node]=keep(pose) end
          World.update_unit(world,helper)
          token={}
          mod._warlock_transition_helper_valid=function(u,h,p,t)
            return u==owner and h==helper and t==token
          end
          -- Capture the expected native loaded-mesh frame before custom following.
          local relative=keep(Matrix4x4.multiply(Unit.world_pose(weapon,5),Matrix4x4.inverse(Unit.world_pose(weapon,0))))
          tick();local authored=keep(Unit.world_pose(outfit,17))
          local body_writes,weapon_writes=calls.writes,calls.weapon_writes
          local grip=assert(mod._prepare_warlock_legacy_grip_pose(owner,helper,token))
          local props,why=mod._prepare_warlock_legacy_prop_pose(owner,helper,prop_profile,grip,token)
          assert(props and #props==3,why)
          assert(calls.writes==body_writes and calls.weapon_writes==weapon_writes)
          -- Builders are read-only; independently compose their candidate locals.
          for _,group in ipairs({grip,props}) do for _,record in ipairs(group) do
            helper.locals[record.node]=keep(record.pose)
          end end
          World.update_unit(world,helper)
          local expected=Matrix4x4.multiply(relative,
            Matrix4x4.from_quaternion_position(Quaternion.normalize(Unit.world_rotation(owner,owner.nodes.j_leftweaponattach)),
              Unit.world_position(owner,owner.nodes.j_leftweaponattach)))
          local actual=Unit.world_pose(helper,helper.nodes.j_leftweaponcomponent2)
          local ar=Quaternion.normalize(Unit.world_rotation(helper,helper.nodes.j_leftweaponcomponent2))
          local er=Quaternion.normalize(pose_quaternion(expected))
          assert(Vector3.distance(Matrix4x4.translation(actual),Matrix4x4.translation(expected))<1e-8)
          local dot=ar.x*er.x+ar.y*er.y+ar.z*er.z+ar.w*er.w
          assert(math.abs(math.abs(dot)-1)<1e-8)
          for r=1,4 do for c=1,4 do assert(math.abs(Unit.world_pose(outfit,17)[r][c]-authored[r][c])<1e-8) end end
        ''')

    def test_independent_rocket_uses_existing_channel_and_actual_parent_graph(self):
        lua = runtime()
        lua.execute('''
          tick();assert(not mod.last_error,mod.last_error)
          assert(mod._warlock_grip_alignment_status(owner)=='authored')
          assert(prop_gap()<1e-8 and weapon_gap()<1e-8 and calls.writes==0)
          assert(weapon.parents[5]==4 and weapon.parents[4]==1)
          assert(#weapon.data.scene_graph_data==2)
          local node=outfit.nodes.j_leftweaponcomponent2
          outfit.locals[node][1][4]=outfit.locals[node][1][4]+.015
          tick();assert(prop_gap()<1e-8 and weapon_gap()<1e-8)
        ''')

    def test_repeated_frames_restore_original_pose_before_new_world_to_local_solution(self):
        lua = runtime()
        lua.execute('''
          for i=1,24 do
            outfit.locals[17][1][4]=.004+i*.0001
            tick();assert(not mod.last_error,mod.last_error)
            assert(prop_gap()<1e-8 and weapon_gap()<1e-8 and calls.writes==0)
          end
          mode='legacy';tick();restored_prop()
        ''')

    def test_rotated_scale100_stretch_and_shear_do_not_scale_the_rocket(self):
        lua = runtime()
        lua.execute('''
          local p=Matrix4x4.identity(100,2,-3,1)
          p[1][1]=0;p[1][2]=-100;p[2][1]=100;p[2][2]=0;outfit.locals[1]=keep(p)
          local hand=outfit.nodes.j_lefthand
          outfit.locals[hand][1][1]=1.6;outfit.locals[hand][2][2]=.7
          outfit.locals[hand][1][2]=.3
          tick();assert(not mod.last_error,mod.last_error)
          assert(prop_gap()<1e-8 and weapon_gap()<1e-8)
          local p=Unit.world_pose(weapon,5)
          assert(math.abs(Vector3.length(Matrix4x4.x(p))-100)<1e-8)
          assert(math.abs(Vector3.length(Matrix4x4.y(p))-100)<1e-8)
        ''')

    def test_native_rewield_then_authored_reconciles_without_recapturing_generated_rest(self):
        lua = runtime()
        lua.execute('''
          tick();native_wield();tick()
          assert(not mod.last_error,mod.last_error)
          assert(prop_gap()<1e-8 and weapon_gap()<1e-8)
          mode='legacy';tick();restored_prop()
          mode='authored';tick();assert(prop_gap()<1e-8)
          mode='legacy';tick();restored_prop()
        ''')

    def test_missing_unknown_unmarked_duplicate_or_wrong_links_fail_before_any_write(self):
        for expression in (
            "prop_profile.weapon_control_policy=nil",
            "prop_profile.weapon_control_policy='unverified'",
            "prop_links[4]=nil",
            "prop_links[4].source='j_lefthand'",
            "prop_links[4].target='pRocketLauncher'",
            "prop_links[4].world_scale={1,1,1}",
            "prop_links[4].offset={0,0,0}",
            "prop_links[5]=prop_links[4]",
            "outfit.nodes.j_leftweaponcomponent2=nil",
            "weapon.nodes.pRocket=nil",
            "weapon.parents[5]=0",
        ):
            with self.subTest(expression=expression):
                lua = runtime()
                lua.execute(expression + '''
                  local links,writes,unlinks=calls.links,calls.weapon_writes,calls.unlinks
                  tick();assert(not mod.last_error,mod.last_error)
                  assert(calls.links==links and calls.weapon_writes==writes and calls.unlinks==unlinks)
                  assert(calls.writes==0)
                ''')

    def test_release_paths_restore_native_rocket_parent_and_local_pose(self):
        for expression in (
            "mode='legacy';tick()",
            "mod._stop_warlock_grip_alignment_item(owner,weapon)",
            "mod._stop_warlock_grip_alignment(owner)",
            "mod._reset_warlock_grip_alignment()",
            "HEALTH_ALIVE[owner]=nil;mod._reset_warlock_grip_alignment()",
            "mod._release_warlock_grip_alignment_world(world)",
            "item_extension.dropped=true;tick()",
        ):
            with self.subTest(expression=expression):
                lua = runtime()
                lua.execute('tick();assert(prop_gap()<1e-8);' + expression + ';restored_prop()')

    def test_switching_to_old_authored_profile_restores_loaded_mesh(self):
        lua = runtime()
        lua.execute('''
          tick();assert(prop_gap()<1e-8)
          prop_profile={weapon_links=semantic_links}
          tick();assert(not mod.last_error,mod.last_error)
          assert(weapon_gap()<1e-8);restored_prop()
        ''')


def capability():
    return {'schema': 1, 'weapon_control_policy': stage.PROP_POLICY,
            'game_bindings': dict(stage.PROP_BINDINGS), 'verified_control_to_game': True,
            'export_transform_policy': 'native-local-trs-v1',
            'maximum_position_error_m': 1e-6, 'maximum_axis_error_m_at_0_1m': 1e-6,
            'minimum_game_response_m': .02, 'binding_manifest_sha256': 'a'*64}


class PropCapabilityTests(unittest.TestCase):
    def receipt(self):
        return {'authoring_capabilities': capability(), 'export_script_sha256': 'b'*64}

    def test_old_receipt_keeps_exact_three_link_policy(self):
        profile = {'weapon_links': [1, 2, 3]}
        stage.configure_prop_policy(profile, {'old': {'data': {}}})
        self.assertEqual(profile, {'weapon_links': [1, 2, 3]})

    def test_only_reviewed_exporter_with_measured_exact_bindings_can_opt_in(self):
        receipt = self.receipt()
        with self.assertRaises(ValueError):
            stage.validated_prop_policy(receipt)
        with patch.object(stage, 'INDEPENDENT_PROP_EXPORTERS', {'b'*64}):
            self.assertEqual(stage.validated_prop_policy(receipt), stage.PROP_POLICY)
            profile = {'weapon_links': [1, 2, 3]}
            stage.configure_prop_policy(profile, {'new': {'data': receipt}})
            self.assertEqual(profile['weapon_control_policy'], stage.PROP_POLICY)
            self.assertEqual(profile['weapon_links'][3], {'target': 'pRocket',
                'source': 'j_leftweaponcomponent2', 'world_scale': [100, 100, 100]})

    def test_mixed_old_and_new_authored_clips_are_rejected(self):
        with patch.object(stage, 'INDEPENDENT_PROP_EXPORTERS', {'b'*64}):
            with self.assertRaisesRegex(ValueError, 'Do not mix'):
                stage.configure_prop_policy({'weapon_links': []}, {
                    'old': {'data': {}}, 'new': {'data': self.receipt()}})

    def test_unverified_schema_bindings_and_measurements_are_rejected(self):
        mutations = (
            ('schema', True), ('schema', 2), ('weapon_control_policy', 'unknown'),
            ('game_bindings', {'CTRL-rocket': 'j_lefthand'}), ('verified_control_to_game', False),
            ('verified_control_to_game', 1), ('maximum_position_error_m', float('nan')),
            ('maximum_position_error_m', float('inf')), ('maximum_position_error_m', -.001),
            ('maximum_position_error_m', .000051), ('maximum_axis_error_m_at_0_1m', .000051),
            ('minimum_game_response_m', 0), ('minimum_game_response_m', True),
            ('binding_manifest_sha256', 'not-a-sha'),
        )
        with patch.object(stage, 'INDEPENDENT_PROP_EXPORTERS', {'b'*64}):
            for field, value in mutations:
                with self.subTest(field=field, value=value):
                    receipt = self.receipt()
                    receipt['authoring_capabilities'][field] = value
                    with self.assertRaises(ValueError):
                        stage.validated_prop_policy(receipt)
            receipt = self.receipt()
            receipt['authoring_capabilities']['unexpected'] = True
            with self.assertRaises(ValueError):
                stage.validated_prop_policy(receipt)

    def test_complete_stager_emits_four_link_profile_without_modifying_sources(self):
        # Placeholder FBX bytes exercise receipt/staging policy only; actual
        # Blender/SDK fidelity is covered by the separately generated proof.
        with tempfile.TemporaryDirectory(prefix='warlock-prop-stage-') as directory:
            fixture = integration.Fixture(Path(directory))
            for clip in ('walk', 'shoot'):
                fixture.mutate_receipt(clip, lambda receipt: receipt.update(
                    export_script_sha256='b'*64, authoring_capabilities=capability()))
            fixture.save()
            before = fixture.snapshot()
            with patch.object(stage, 'APPROVED_EXPORTERS', stage.APPROVED_EXPORTERS | {'b'*64}), \
                 patch.object(stage, 'INDEPENDENT_PROP_EXPORTERS', {'b'*64}):
                receipt = fixture.run()
            self.assertEqual(before, fixture.snapshot())
            payload = json.loads((fixture.output / 'integration_manifest.json').read_text())
            profile = payload['profiles'][receipt['profile_id']]
            self.assertEqual(profile['weapon_control_policy'], stage.PROP_POLICY)
            self.assertEqual(len(profile['weapon_links']), 4)
            self.assertEqual(profile['weapon_links'][3], {'target': 'pRocket',
                'source': 'j_leftweaponcomponent2', 'world_scale': [100, 100, 100]})
            self.assertEqual(receipt['shipping_clips_and_sidecars_preserved'], 26)
            self.assertTrue(receipt['legacy_sources_unchanged'])


class PropBlendTests(unittest.TestCase):
    def runtime(self):
        lua = blend.runtime()
        lua.execute('''
          profile.weapon_control_policy='independent-props-v1'
          calls.props=0
          function mod._prepare_warlock_legacy_prop_pose(u,h,p,grip,token)
            calls.props=calls.props+1
            assert(p==profile and #grip==12)
            assert(mod._warlock_transition_helper_valid(u,h,p,token))
            if bad_props then return nil,'bad_props' end
            local result={}
            for node=20,22 do result[#result+1]={node=node,position=vec(500+node,2,3),rotation=q(.6)} end
            if duplicate_prop then result[3].node=1 end
            return result
          end
        ''')
        return lua

    def test_legacy_endpoint_adds_only_three_preflighted_channels(self):
        lua = self.runtime()
        lua.execute('''
          begin();change('authored');frame(.25);change('idle')
          assert(frame(.125))
          assert(calls.props==1 and calls.helper_bones==22*2)
          assert(math.abs(outfit.locals[20].p.x-(.2+520)/2)<1e-10)
          assert(math.abs(outfit.locals[23].p.x-(.23+10.23)/2)<1e-10)
        ''')

    def test_interruption_uses_displayed_snapshot_and_never_writes_incoming_authored_pose(self):
        lua = self.runtime()
        lua.execute('''
          begin();change('authored');frame(.25);change('idle');assert(frame(.1))
          local shown=outfit.locals[20].p.x
          local writes,props=calls.helper_bones,calls.props
          change('authored');assert(frame(0))
          assert(outfit.locals[20].p.x==shown and calls.helper_bones==writes and calls.props==props)
          assert(frame(.1))
          assert(calls.helper_bones==writes and calls.props==props and calls.warnings==0)
        ''')

    def test_prop_failure_duplicate_or_missing_builder_cannot_partially_write_helper(self):
        for mutation in ('bad_props=true', 'duplicate_prop=true',
                         'mod._prepare_warlock_legacy_prop_pose=nil'):
            with self.subTest(mutation=mutation):
                lua = self.runtime()
                lua.execute('''
                  begin();change('authored');frame(.25);change('idle')
                ''' + mutation + '''
                  assert(not frame(.1))
                  assert(calls.helper_bones==0 and calls.visible==0)
                ''')


if __name__ == '__main__':
    unittest.main()
