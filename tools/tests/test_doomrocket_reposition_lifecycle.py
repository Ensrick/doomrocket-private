#!/usr/bin/env python3
"""Execute production reposition actions with prescribed native nav outcomes.

The game navmesh, locomotion, animation and replication are NOT simulated.
Tests exercise real Lua lifecycle/selector decisions and bounded engine calls;
matching host/client visual playtests are still required.
"""

import unittest

from test_doomrocket_reload_lifecycle import create_runtime


class DoomrocketRepositionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.lua = create_runtime()

    def test_completed_kick_starts_navigation_without_reloading(self):
        self.lua.execute("""
            blackboard.reloaded_rocket = true
            request_reposition()
            assert(blackboard.doomrocket_reposition_request_target == target)
            assert(selected_close_combat_child() == 'reposition')
            reposition:enter(unit, blackboard, 1.3)
            assert(reposition:run(unit, blackboard, 1.3, 0) == 'running')
            assert(#events.nav_goals == 1 and events.nav_goals[1].y < 0)
            assert(blackboard.navigation_extension.enabled)
            assert(blackboard.reloaded_rocket and weapon.rocket_visible)
            assert(count_event('animations', 'wind_up_start') == 0)
            assert(#events.rpcs == 0 and events.spawns == 0)
        """)

    def test_initial_round_can_retreat_without_reload_initialization(self):
        self.lua.execute("""
            assert(blackboard.reloaded_rocket == nil)
            request_reposition()
            assert(selected_close_combat_child() == 'reposition')
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            assert(#events.nav_goals == 1)
            assert(blackboard.reloaded_rocket == nil)
        """)

    def test_retreat_is_sticky_past_shove_range_then_returns_to_ranged(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            place_unit(0, -1, 0)
            assert(blackboard.target_dist == 2)
            assert(selected_close_combat_child() == 'reposition')
            assert(reposition:run(unit, blackboard, 1.8, 0.5) == 'running')
            place_unit(0, -2.6, 0)
            assert(reposition:run(unit, blackboard, 2.3, 0.5) == 'done')
            reposition:leave(unit, blackboard, 2.3, 'done')
            assert(not blackboard.doomrocket_reposition_active)
            assert(blackboard.navigation_extension.goal == nil)
            assert(selected_close_combat_child() == 'attack_pattern')
            enter_reload(2.3)
            assert(run_reload(2.3, 0, false) == 'done')
            assert(count_event('animations', 'wind_up_start') == 0)
        """)

    def test_push_already_beyond_shove_range_still_creates_clearance(self):
        self.lua.execute("""
            request_reposition()
            blackboard.target_dist = 2.5
            target.position = Vector3(0, 2.5, 0)
            POSITION_LOOKUP[target] = target.position
            assert(selected_close_combat_child() == 'reposition')
        """)

    def test_kick_can_preempt_active_retreat_when_cooldown_is_ready(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            blackboard.utility_actions.push_attack.time_since_last = 7.49
            assert(selected_close_combat_child() == 'reposition')
            blackboard.utility_actions.push_attack.time_since_last = 7.5
            assert(selected_close_combat_child() == 'push_attack')
            reposition:leave(unit, blackboard, 7.5, 'aborted')
            assert(not blackboard.doomrocket_reposition_active)
            assert(blackboard.navigation_extension.goal == nil)
        """)

    def test_empty_reload_completes_before_retreat_and_does_not_get_free_ammo(self):
        self.lua.execute("""
            blackboard.reloaded_rocket = false
            weapon.rocket_visible = false
            request_reposition()
            assert(selected_close_combat_child() == 'attack_pattern')
            enter_reload(1.3)
            for step = 1, 3 do
                assert(run_reload(1.3 + step, 1, true) == 'running')
                assert(selected_close_combat_child() == 'attack_pattern')
                assert(not blackboard.reloaded_rocket)
            end
            assert(run_reload(5.4, 1.1, true) == 'done')
            reload:leave(unit, blackboard, 5.4, 'done')
            assert(selected_close_combat_child() == 'reposition')
            reposition:enter(unit, blackboard, 5.4)
            reposition:run(unit, blackboard, 5.4, 0)
            place_unit(0, -2.6, 0)
            assert(reposition:run(unit, blackboard, 6.8, 1.4) == 'done')
            reposition:leave(unit, blackboard, 6.8, 'done')
            enter_reload(6.8)
            assert(run_reload(6.8, 0, false) == 'done')
            assert(count_event('rpcs', 'rpc_reload_rocket') == 1)
            assert(count_event('animations', 'wind_up_start') == 1)
        """)

    def test_wall_behind_uses_valid_diagonal(self):
        self.lua.execute("""
            nav_policy = function(origin, goal)
                return math.abs(goal.x) > 0.1, origin, goal
            end
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            assert(#events.nav_goals == 1)
            assert(math.abs(events.nav_goals[1].x) > 0.1)
            assert(events.nav_goals[1].y < 0)
            assert(events.nav_queries <= 5)
        """)

    def test_no_route_is_bounded_and_does_not_retry_every_frame(self):
        self.lua.execute("""
            nav_policy = function() return false end
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            local result = reposition:run(unit, blackboard, 1.3, 0)
            if result == 'running' then result = reposition:run(unit, blackboard, 4, 2.7) end
            assert(result == 'done' or result == 'failed')
            reposition:leave(unit, blackboard, 4, result)
            assert(#events.nav_goals == 0 and events.nav_queries <= 10)
            local queries = events.nav_queries
            for frame = 1, 600 do
                assert(selected_close_combat_child() == 'wait_at_close_range')
            end
            assert(events.nav_queries == queries)
            blackboard.utility_actions.push_attack.time_since_last = 7.5
            assert(selected_close_combat_child() == 'push_attack')
            assert(events.spawns == 0)
        """)

    def test_projection_cannot_select_another_floor(self):
        self.lua.execute("""
            nav_policy = function(origin, goal)
                return true, origin, Vector3(goal.x, goal.y, 8)
            end
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            assert(#events.nav_goals == 0)
        """)

    def test_stationary_or_failed_path_times_out_without_per_frame_move_requests(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            local result
            for frame = 0, 160 do
                result = reposition:run(unit, blackboard, 1.3 + frame / 60, 1/60)
                if result ~= 'running' then break end
            end
            assert(result == 'done' or result == 'failed')
            assert(#events.nav_goals <= 2 and events.nav_queries <= 10)
            reposition:leave(unit, blackboard, 4, result)
            assert(selected_close_combat_child() == 'wait_at_close_range')
        """)

    def test_target_change_cancels_without_touching_deleted_target(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            target.alive = false
            blackboard.target_unit = {alive=true, position=Vector3(4,0,0)}
            assert(reposition:run(unit, blackboard, 1.4, 0.1) == 'done')
            reposition:leave(unit, blackboard, 1.4, 'done')
            assert(not blackboard.doomrocket_reposition_active)
            assert(not blackboard.doomrocket_reposition_request_target)
        """)

    def test_pending_target_loss_or_clearance_does_not_trigger_retreat_later(self):
        self.lua.execute("""
            request_reposition()
            blackboard.target_dist = 5
            assert(selected_close_combat_child() == 'attack_pattern')
            assert(not blackboard.doomrocket_reposition_request_target)
            become_close()
            assert(selected_close_combat_child() == 'wait_at_close_range')
            blackboard.doomrocket_reposition_request_target = target
            target.alive = false
            assert(selected_close_combat_child() == 'attack_pattern')
            assert(not blackboard.doomrocket_reposition_request_target)
        """)

    def test_stagger_abort_cleans_movement_without_overriding_animation(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            local animations = #events.animations
            reposition:leave(unit, blackboard, 1.5, 'aborted')
            assert(#events.animations == animations)
            assert(not blackboard.doomrocket_reposition_active)
            assert(not blackboard.doomrocket_reposition_data)
            assert(blackboard.navigation_extension.goal == nil)
            assert(blackboard.navigation_extension.max_speed == 1)
        """)

    def test_released_navbot_never_receives_native_cleanup_calls(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            local nav = blackboard.navigation_extension
            nav.traverse_logic = function() return nil end
            nav.stop = function() error('stop with released navbot') end
            nav.set_max_speed = function() error('speed with released navbot') end
            nav.set_enabled = function() error('enable with released navbot') end
            unit.alive = false
            HEALTH_ALIVE[unit] = false
            reposition:leave(unit, blackboard, 1.5, 'aborted')
            assert(not blackboard.doomrocket_reposition_active)
            assert(not blackboard.doomrocket_reposition_data)
        """)

    def test_aborted_or_early_ended_shove_does_not_request_retreat(self):
        for reason in ("aborted", "done"):
            with self.subTest(reason=reason):
                self.setUp()
                self.lua.globals().reason = reason
                self.lua.execute("""
                    become_close()
                    shove:enter(unit, blackboard, 0)
                    shove:leave(unit, blackboard, 0.1, reason)
                    assert(not blackboard.doomrocket_reposition_request_target)
                """)

    def test_ammo_and_attack_data_are_unchanged_during_reposition(self):
        self.lua.execute("""
            blackboard.reloaded_rocket = true
            blackboard.attack_pattern_data = {marker='preserve'}
            local original = blackboard.attack_pattern_data
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            reposition:leave(unit, blackboard, 1.8, 'aborted')
            assert(blackboard.attack_pattern_data == original)
            assert(blackboard.reloaded_rocket and weapon.rocket_visible)
            assert(#events.rpcs == 0 and events.spawns == 0)
        """)

    def test_crossing_behind_cancels_the_now_unsafe_segment(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            reposition:run(unit, blackboard, 1.3, 0)
            target.position = Vector3(0, -1, 0)
            POSITION_LOOKUP[target] = target.position
            assert(reposition:run(unit, blackboard, 1.4, 0.1) == 'done')
            assert(blackboard.doomrocket_reposition_data.outcome == 'target_crossed_route')
            reposition:leave(unit, blackboard, 1.4, 'done')
            assert(blackboard.navigation_extension.goal == nil)
            assert(#events.nav_goals == 1 and events.spawns == 0)
        """)

    def test_stale_path_failure_does_not_abort_a_new_viable_route(self):
        self.lua.execute("""
            request_reposition()
            blackboard.no_path_found = true
            blackboard.navigation_extension.failed_attempts = 5
            reposition:enter(unit, blackboard, 1.3)
            assert(blackboard.navigation_extension.failed_attempts == 0)
            place_unit(0, -0.8, 0)
            assert(reposition:run(unit, blackboard, 2.1, 0.8) == 'running')
            assert(#events.nav_goals == 1)
        """)

    def test_current_path_failures_use_only_one_replan(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            place_unit(0, -0.3, 0)
            blackboard.navigation_extension.failed_attempts = 1
            assert(reposition:run(unit, blackboard, 2.1, 0.8) == 'running')
            assert(#events.nav_goals == 2)
            place_unit(0, -0.6, 0)
            blackboard.navigation_extension.failed_attempts = 1
            assert(reposition:run(unit, blackboard, 2.9, 0.8) == 'done')
            assert(#events.nav_goals == 2)
        """)

    def test_coincident_target_positions_produce_finite_away_goal(self):
        self.lua.execute("""
            request_reposition()
            target.position = Vector3(0, 0, 0)
            POSITION_LOOKUP[target] = target.position
            blackboard.target_dist = 0
            reposition:enter(unit, blackboard, 1.3)
            assert(#events.nav_goals == 1)
            local goal = events.nav_goals[1]
            assert(goal.x == goal.x and goal.y == goal.y and goal.z == goal.z)
            assert(Vector3.length(goal) > 0 and Vector3.length(goal) < 5)
        """)

    def test_live_frozen_navbot_cancels_without_unsafe_engine_calls(self):
        self.lua.execute("""
            request_reposition()
            reposition:enter(unit, blackboard, 1.3)
            local nav = blackboard.navigation_extension
            nav.traverse_logic = function() return nil end
            nav.stop = function() error('stop with frozen navbot') end
            nav.set_max_speed = function() error('speed with frozen navbot') end
            assert(reposition:run(unit, blackboard, 1.4, 0.1) == 'done')
            reposition:leave(unit, blackboard, 1.4, 'done')
            assert(not blackboard.doomrocket_reposition_active)
        """)

    def test_repeated_completed_kicks_each_allow_one_new_retreat_not_new_ammo(self):
        self.lua.execute("""
            blackboard.reloaded_rocket = true
            for cycle = 1, 3 do
                place_unit(0, 0, 0)
                request_reposition(cycle * 10)
                assert(selected_close_combat_child() == 'reposition')
                reposition:enter(unit, blackboard, cycle * 10 + 1.3)
                place_unit(0, -2.6, 0)
                assert(reposition:run(unit, blackboard, cycle * 10 + 2.5, 1.2) == 'done')
                reposition:leave(unit, blackboard, cycle * 10 + 2.5, 'done')
                assert(not blackboard.doomrocket_reposition_request_target)
                assert(blackboard.reloaded_rocket)
            end
            assert(#events.nav_goals == 3 and #events.rpcs == 0)
        """)


if __name__ == '__main__':
    unittest.main(verbosity=2)
