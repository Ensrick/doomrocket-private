#!/usr/bin/env python3
"""Issue #15: one persistent warpfire flame linked to the launcher crystal.

Executes the production controller in Lua 5.1 against strict engine lifetime
doubles (the backpack smoke suite's boundary): handle and package ownership,
start/stop/drop/death/world-release ordering. A deleted launcher recycles its
old particle ID to catch unsafe cleanup. The anchor is checked against the
measured fixture and, when bundleV2 exists, regenerated from the compiled
launcher node. None of this proves how the flame looks in game.
"""

import json
import math
from pathlib import Path
import re
import subprocess
import sys
import unittest

from lupa.lua51 import LuaRuntime


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/mods/doomrocket/extensions/doomrocket_crystal_flame.lua"
ANCHOR = ROOT / "scripts/mods/doomrocket/utils/doomrocket_crystal_anchor.lua"
FIXTURE = json.loads((ROOT / "tools/fixtures/warlock_crystal_anchor.json").read_text(encoding="utf-8"))
BOOTSTRAP = ROOT / "scripts/mods/doomrocket/doomrocket.lua"
HOOKS = ROOT / "scripts/mods/doomrocket/utils/hooks.lua"
BUNDLE_ROOT = ROOT / "bundleV2"

HARNESS = r"""
events={created=0,linked=0,destroyed=0,queried=0,loads=0,unloads=0,nodes=0}
function printf() end
local function v(x,y,z) return {x=x,y=y,z=z} end
Vector3=v
Matrix4x4={
 identity=function() return {x=v(1,0,0),y=v(0,1,0),z=v(0,0,1),p=v(0,0,0)} end,
 set_x=function(m,x) m.x=x end,set_y=function(m,x) m.y=x end,
 set_z=function(m,x) m.z=x end,set_translation=function(m,x) m.p=x end,
}
world={alive=true}
weapon_name='units/rocket/pRocketLauncher'
function new_owner() return {alive=true,world=world} end
function new_weapon() return {alive=true,world=world,name=weapon_name,has_node=true,item={dropped=false}} end
owner=new_owner(); weapon=new_weapon()
function new_inventory(o,w) return {unit=o or owner,inventory_item_units={{alive=true,world=world,name='units/bombadier/Backpack'},w or weapon}} end
inventory=new_inventory()
Unit={
 alive=function(u) return u and u.alive end,
 world=function(u) assert(u and u.alive,'dead Unit.world'); return u.world end,
 get_data=function(u,key) assert(u and u.alive and key=='unit_name'); return u.name end,
 has_node=function(u,node) assert(u.alive and node=='pRocketLauncher'); return u.has_node end,
 node=function(u,node)
  assert(u.alive and u.has_node and node=='pRocketLauncher','unsafe node lookup')
  events.nodes=events.nodes+1; return 7
 end,
}
ScriptUnit={has_extension=function(u,system)
 assert(system=='ai_inventory_item_system'); return u.item
end}
wm={_worlds={level_world=world},_disabled_worlds={}}
function wm:has_world(name) return self._worlds[name] ~= nil end
function wm:world(name) assert(self._worlds[name]); return self._worlds[name] end
package_name='resource_packages/breeds/skaven_warpfire_thrower'
package_reference='doomrocket_crystal_flame'
effect_name='fx/wpnfx_warp_fire_nozzle'
package_available=true; particles_available=true; loaded=true
refs={global=3}
pm={}
function pm:has_loaded(name,reference)
 assert(name==package_name)
 return loaded and (not reference or refs[reference] ~= nil)
end
function pm:load(name,reference,callback,asynchronous)
 assert(name==package_name and reference==package_reference)
 assert(callback==nil and asynchronous==nil,'must load synchronously')
 refs[reference]=(refs[reference] or 0)+1; loaded=true; events.loads=events.loads+1
end
function pm:unload(name,reference)
 assert(name==package_name and reference==package_reference)
 assert(refs[reference] and refs[reference] > 0,'unowned package decrement')
 refs[reference]=refs[reference]-1
 if refs[reference]==0 then refs[reference]=nil end
 events.unloads=events.unloads+1
end
Managers={world=wm,package=pm}
Application={can_get=function(kind,name)
 if kind=='package' then assert(name==package_name); return package_available end
 assert(kind=='particles' and name==effect_name)
 assert(refs[package_reference],'residency queried before own package load')
 return particles_available
end}
effects={}; next_id=1
local function check_world(w) assert(w and w.alive,'released world touched') end
World={
 create_particles=function(w,name)
  check_world(w); assert(name==effect_name)
  local id=next_id; next_id=id+1
  effects[id]={world=w}; events.created=events.created+1
  return id
 end,
 link_particles=function(w,id,u,node,pose,policy)
  check_world(w); assert(effects[id] and u.alive and u.world==w)
  assert(node==7 and policy=='destroy')
  effects[id].weapon=u; effects[id].pose=pose
  events.linked=events.linked+1; events.last_pose=pose
 end,
 are_particles_playing=function(w,id)
  check_world(w); events.queried=events.queried+1
  assert(effects[id] and effects[id].world==w,'stale particle queried')
  return true
 end,
 destroy_particles=function(w,id)
  check_world(w); assert(effects[id] and effects[id].world==w,'stale particle destroyed')
  assert(not effects[id].foreign,'recycled foreign particle destroyed')
  effects[id]=nil; events.destroyed=events.destroyed+1
 end,
}
ScriptWorld={create_particles_linked=function(w,name,u,node,policy,pose)
 local id=World.create_particles(w,name)
 World.link_particles(w,id,u,node,pose or Matrix4x4.identity(),policy)
 return id
end}
mod={}
function get_mod(name) assert(name=='doomrocket'); return mod end
function delete_weapon(w)
 w=w or weapon
 -- The engine destroys a linked emitter with its unit; its ID may be reused.
 for id,e in pairs(effects) do
  if e.weapon==w then effects[id]={world=e.world,foreign=true} end
 end
 w.alive=false
end
function count() local n=0; for _ in pairs(effects) do n=n+1 end; return n end
function start(o,inv) return mod._start_warlock_crystal_flame(o or owner,inv or inventory) end
"""


def runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(HARNESS)
    lua.execute("mod._doomrocket_crystal_anchor = (function()\n"
                + ANCHOR.read_text(encoding="utf-8") + "\nend)()")
    lua.execute(MODULE.read_text(encoding="utf-8"))
    return lua


class CrystalFlameLifecycleTests(unittest.TestCase):
    def test_start_links_one_flame_at_the_anchor_and_is_idempotent(self):
        lua = runtime()
        lua.execute("""
            assert(start()); assert(start())
            assert(events.created==1 and events.linked==1 and events.loads==1)
            local a, p = mod._doomrocket_crystal_anchor, events.last_pose
            assert(p.x.x==a.x_axis[1] and p.y.y==a.y_axis[2] and p.z.z==a.z_axis[3])
            assert(p.p.x==a.position[1] and p.p.y==a.position[2] and p.p.z==a.position[3])
        """)

    def test_stop_destroys_its_own_flame_and_releases_the_package_on_reset(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            assert(mod._stop_warlock_crystal_flame(owner,'test'))
            assert(not mod._stop_warlock_crystal_flame(owner,'again'))
            assert(events.destroyed==1 and count()==0)
            mod._reset_warlock_crystal_flame('test')
            assert(events.unloads==1 and refs[package_reference]==nil and refs.global==3)
        """)

    def test_dropping_or_disabling_the_launcher_stops_only_that_flame(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            assert(not mod._stop_warlock_crystal_flame_item(owner,{alive=true},'other_item'))
            assert(count()==1)
            assert(mod._stop_warlock_crystal_flame_item(owner,weapon,'inventory_drop'))
            assert(events.destroyed==1 and count()==0)
        """)

    def test_deleted_launcher_is_forgotten_without_touching_a_recycled_id(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            delete_weapon()
            mod._update_warlock_crystal_flame()
            assert(events.destroyed==0 and events.queried==0)
            assert(not mod._stop_warlock_crystal_flame(owner,'late'))
        """)

    def test_world_release_forgets_without_particle_calls(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            mod._release_warlock_crystal_flame_world(world)
            assert(events.destroyed==0 and events.queried==0)
            assert(not start(), 'no new flame while the old world is releasing')
            world.alive=false; wm._worlds.level_world=nil
            world={alive=true}; wm._worlds.level_world=world
            owner=new_owner(); weapon=new_weapon(); inventory=new_inventory(owner,weapon)
            assert(start())
        """)

    def test_no_flame_without_a_carried_launcher_or_on_dedicated_servers(self):
        lua = runtime()
        lua.execute("""
            weapon.item.dropped=true
            assert(not start())
            weapon.item.dropped=false
            assert(not start(owner,{unit=new_owner(),inventory_item_units={weapon}}))
            weapon.has_node=false
            assert(not start())
            weapon.has_node=true
            particles_available=false
            assert(not start())
            particles_available=true
            DEDICATED_SERVER=true
            assert(not start())
            DEDICATED_SERVER=nil
            assert(start() and events.created==1)
        """)

    def test_replaced_launcher_moves_the_flame(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            local replacement=new_weapon()
            assert(start(owner,new_inventory(owner,replacement)))
            assert(events.created==2 and events.destroyed==1 and count()==1)
        """)


class CrystalFlameWiringTests(unittest.TestCase):
    def test_bootstrap_loads_anchor_then_controller_and_drives_update_and_reset(self):
        source = BOOTSTRAP.read_text(encoding="utf-8")
        anchor = source.index('mod._doomrocket_crystal_anchor = mod:dofile("scripts/mods/doomrocket/utils/doomrocket_crystal_anchor")')
        controller = source.index('mod:dofile("scripts/mods/doomrocket/extensions/doomrocket_crystal_flame")')
        self.assertLess(anchor, controller)
        self.assertIn("mod._update_warlock_crystal_flame()", source)
        self.assertIn('mod._reset_warlock_crystal_flame(reason or "runtime_reset")', source)

    def test_every_smoke_lifecycle_boundary_also_ends_the_flame(self):
        hooks = HOOKS.read_text(encoding="utf-8")
        for call in (
            "mod._start_warlock_crystal_flame(unit, self)",
            'mod._stop_warlock_crystal_flame(self.unit, "inventory_destroy")',
            'mod._stop_warlock_crystal_flame(self.unit, "inventory_freeze")',
            'mod._stop_warlock_crystal_flame_item(self.unit, item_unit, "inventory_drop")',
            'mod._stop_warlock_crystal_flame_item(self.unit, item_unit, "inventory_disable_item")',
            "mod._release_warlock_crystal_flame_world(world)",
            'mod._stop_warlock_crystal_flame(owner_unit, "death_" .. tostring(source))',
        ):
            with self.subTest(call=call):
                self.assertEqual(hooks.count(call), 1)


class CrystalAnchorTests(unittest.TestCase):
    def anchor(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        table = lua.execute(ANCHOR.read_text(encoding="utf-8"))
        return {key: list(table[key].values()) if key != "node" else table[key]
                for key in ("node", "x_axis", "y_axis", "z_axis", "position")}

    def test_anchor_is_the_measured_tip_frame_in_node_units(self):
        # The compiled node is a scale-100 frame at the root with a rotation of
        # about 1.6e-5 rad, so the node-local frame is 0.01 x the root frame.
        anchor = self.anchor()
        self.assertEqual(anchor["node"], FIXTURE["target_node"])
        for key, source in (("x_axis", "frame_x_axis"), ("y_axis", "frame_y_axis"),
                            ("z_axis", "frame_z_axis"), ("position", "tip_engine_m")):
            for actual, expected in zip(anchor[key], FIXTURE[source]):
                self.assertAlmostEqual(actual, expected * 0.01, delta=2e-8, msg=key)
        x, y, z = anchor["x_axis"], anchor["y_axis"], anchor["z_axis"]
        cross = (x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0])
        self.assertGreater(sum(c * w for c, w in zip(cross, z)), 0, "anchor frame must stay right-handed")
        self.assertAlmostEqual(math.sqrt(sum(c * c for c in x)), 0.01, delta=1e-9)

    @unittest.skipUnless(BUNDLE_ROOT.is_dir() and any(BUNDLE_ROOT.glob("*.mod_bundle")), "compiled bundleV2 is not present")
    def test_anchor_regenerates_from_the_compiled_launcher_node(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/build_crystal_anchor.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
