#!/usr/bin/env python3
"""Issue #33 balance contracts, executed from the production bootstrap in Lua 5.1.

Covers the explosion knockback (no catapult, distance-scaled push) and the 0.6x
rocket damage against AI. The knockback, explosion and hook blocks are executed
as written in doomrocket.lua with engine calls stubbed. Not an in-game test.
"""

from pathlib import Path
import re
import unittest

from lupa.lua51 import LuaRuntime


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = (ROOT / "scripts/mods/doomrocket/doomrocket.lua").read_text(encoding="utf-8")


def block(pattern):
    match = re.search(pattern, BOOTSTRAP, re.M | re.S)
    if not match:
        raise AssertionError(f"production block missing: {pattern}")
    return match.group()


KNOCKBACK = block(r"^local KNOCKBACK_NEAR_SPEED = .*?^end$")
EXPLOSION = block(r'^ExplosionTemplates\["doomrocket_explosion"\] = \{.*?^\}')
DAMAGE_HOOK = block(r"^local DOOMROCKET_DAMAGE_SOURCE = .*?^end\)")


def runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
        mod = { hooks = {} }
        function mod._doomrocket_select_impact_event() return 'impact' end
        function mod:hook(object, method, handler)
            assert(not self.hooks[method], 'duplicate hook ' .. method)
            self.hooks[method] = { object = object, handler = handler }
        end
        ExplosionTemplates = {}
        DamageUtils = { calculate_damage = function() error('call through the hook') end }
        units = {
            clan_rat = { breed = { name = 'skaven_clan_rat' } },
            warlock = { breed = { name = 'skaven_doomrocket' } },
            hero = { breed = { name = 'hero_es_mercenary', is_player = true } },
            barrel = {},
            corpse = { breed = { name = 'skaven_slave' }, dead = true },
        }
        Unit = {
            alive = function(unit) return unit ~= nil and not unit.dead end,
            get_data = function(unit, key) assert(key == 'breed'); return unit.breed end,
        }
        native_calls = 0
        function native(...)
            native_calls = native_calls + 1
            native_args = { ... }
            return 10, 'second'
        end
        local V = {}
        V.__index = V
        local function vec(x, y, z) return setmetatable({ x = x, y = y, z = z }, V) end
        V.__add = function(a, b) return vec(a.x + b.x, a.y + b.y, a.z + b.z) end
        V.__sub = function(a, b) return vec(a.x - b.x, a.y - b.y, a.z - b.z) end
        V.__mul = function(a, b)
            if type(a) == 'number' then a, b = b, a end
            return vec(a.x * b, a.y * b, a.z * b)
        end
        Vector3 = setmetatable({
            zero = function() return vec(0, 0, 0) end,
            flat = function(v) return vec(v.x, v.y, 0) end,
            direction_length = function(v)
                local length = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
                if length == 0 then return vec(0, 0, 0), 0 end
                return v * (1 / length), length
            end,
        }, { __call = function(_, x, y, z) return vec(x, y, z) end })
        Vector3.normalize = function(v) return (Vector3.direction_length(v)) end
        function math.clamp(value, min, max)
            if max < value then return max elseif value < min then return min end
            return value
        end
        pushes = {}
        local function player(x, y, disabled)
            local unit = { player = true }
            unit.status = { is_disabled = function() return disabled end }
            unit.locomotion = { add_external_velocity = function(_, velocity, upper)
                pushes[#pushes + 1] = { unit = unit, velocity = velocity, upper = upper }
            end }
            unit.position = vec(x, y, 0)
            return unit
        end
        DamageUtils.is_player_unit = function(unit) return unit.player == true end
        ScriptUnit = { has_extension = function(unit, system)
            return system == 'status_system' and unit.status or system == 'locomotion_system' and unit.locomotion or nil
        end }
        POSITION_LOOKUP = setmetatable({}, { __index = function(_, unit) return unit.position end })
        make_player = player
        function knock(unit, impact, attacker)
            local data = ExplosionTemplates.doomrocket_explosion.explosion
            data.server_hit_func(unit, 'skaven_doomrocket', attacker or { position = vec(-10, 0, 0) }, impact or vec(0, 0, 0), data)
            return pushes[#pushes]
        end
        function hooked(target, source)
            return mod.hooks.calculate_damage.handler(native, 'output', target, 'attacker',
                'torso', 800, nil, 0, false, 'profile', 1, 1, source, 'extra')
        end
    """)
    lua.execute(KNOCKBACK)
    lua.execute(EXPLOSION)
    lua.execute(DAMAGE_HOOK)
    return lua


class BalanceContractTests(unittest.TestCase):
    def test_explosion_no_longer_catapults_players(self):
        explosion = runtime().eval('ExplosionTemplates.doomrocket_explosion.explosion')
        self.assertFalse(explosion["catapult_players"])
        self.assertIsNone(explosion["catapult_force"])
        # Vanilla's push falloff clamps to 1 m/s whenever player_push_speed > 1.
        self.assertIsNone(explosion["player_push_speed"])
        self.assertEqual((explosion["max_damage_radius"], explosion["radius"]), (1.5, 6))

    def test_knockback_falls_off_linearly_with_lift(self):
        lua = runtime()
        for distance, speed in ((0.5, 10), (1.5, 10), (3.75, 6), (6, 2), (9, 2)):
            with self.subTest(distance=distance):
                lua.execute(f"""
                    local push = knock(make_player({distance}, 0, false))
                    local v = push.velocity
                    assert(math.abs(v.x - {speed}) < 1e-9 and math.abs(v.y) < 1e-9, v.x)
                    assert(math.abs(v.z - {speed} * 0.4) < 1e-9, v.z)
                    assert(push.upper == nil)
                """)

    def test_knockback_points_away_from_the_impact_in_the_horizontal_plane(self):
        runtime().execute("""
            local push = knock(make_player(3, 4, false), Vector3(0, 0, 2))
            local v = push.velocity
            -- 5 m away: speed 10 - 8 * (3.5 / 4.5); direction (0.6, 0.8).
            local speed = 10 - 8 * (3.5 / 4.5)
            assert(math.abs(v.x - 0.6 * speed) < 1e-9 and math.abs(v.y - 0.8 * speed) < 1e-9)
            assert(math.abs(v.z - 0.4 * speed) < 1e-9)
        """)

    def test_knockback_skips_disabled_players_and_ai(self):
        runtime().execute("""
            knock(make_player(1, 0, true))
            local data = ExplosionTemplates.doomrocket_explosion.explosion
            data.server_hit_func({ position = Vector3(1, 0, 0) }, 'skaven_doomrocket', {}, Vector3(0, 0, 0), data)
            assert(#pushes == 0)
        """)

    def test_direct_hit_pushes_away_from_the_shooter(self):
        runtime().execute("""
            local push = knock(make_player(2, 0, false), Vector3(2, 0, 0), { position = Vector3(-8, 0, 0) })
            assert(math.abs(push.velocity.x - 10) < 1e-9 and push.velocity.y == 0)
        """)

    def test_rocket_damage_to_ai_is_sixty_percent(self):
        lua = runtime()
        lua.execute("""
            assert(mod.hooks.calculate_damage.object == DamageUtils)
            for _, name in ipairs({ 'clan_rat', 'warlock' }) do
                local damage, second = hooked(units[name], 'skaven_doomrocket')
                assert(damage == 6 and second == 'second', name)
            end
            assert(native_args[12] == 'skaven_doomrocket' and native_args[13] == 'extra')
        """)

    def test_players_props_and_other_sources_are_unchanged(self):
        lua = runtime()
        lua.execute("""
            local cases = {
                { units.hero, 'skaven_doomrocket' },
                { units.barrel, 'skaven_doomrocket' },
                { units.corpse, 'skaven_doomrocket' },
                { nil, 'skaven_doomrocket' },
                { units.clan_rat, 'warpfire_thrower' },
                { units.clan_rat, nil },
            }
            for i, case in ipairs(cases) do
                local damage, second = hooked(case[1], case[2])
                assert(damage == 10 and second == 'second', i)
            end
            assert(native_calls == #cases)
        """)

    def test_invincible_targets_stay_at_zero(self):
        lua = runtime()
        lua.execute("""
            local result = { mod.hooks.calculate_damage.handler(function() return 0, true end,
                'output', units.clan_rat, 'attacker', 'torso', 800, nil, 0, false, 'profile', 1, 1,
                'skaven_doomrocket') }
            assert(result[1] == 0 and result[2] == true)
        """)


if __name__ == "__main__":
    unittest.main(verbosity=2)
